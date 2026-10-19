#!/usr/bin/env bash
# Squelette de fiche entite : tout ce qui se lit dans le schema et dans un enregistrement
# modele, pour une table Axelor donnee.
#
# Pourquoi ce script existe : l'ancien "Entity Reference Guide" etait ce contenu ecrit a la
# main, 16 fois, fige a une date et sur une base — il a divergent. La regle 0/1 du skill
# exige d'introspecter au moment de produire : ce script REMPLACE l'ecriture manuelle par une
# introspection executee a chaque appel. Rien de ce qu'il affirme ne doit venir d'ailleurs que
# du catalogue systeme et d'un enregistrement reel de LA base interrogee.
#
# Ce qu'il NE fait PAS : il ne decide pas ce qui est "UI-critical" (casse a NULL, domaine
# filtrant, denormalisation non resynchronisee...) — cette couche ne se lit ni dans le schema
# ni dans un record, elle est l'objet du stress-test qui consomme ce squelette. La section
# correspondante est emise VIDE, avec un gabarit a remplir.
#
# Usage : ./shape-fiche.sh <base> <table> [id-modele]
#   ./shape-fiche.sh <base> sale_sale_order
#   ./shape-fiche.sh <base> sale_sale_order 42
#
# Sortie : markdown sur stdout.
# Variables d'environnement : PGHOST et PGUSER (obligatoires), PGPASSWORD (ou le fichier de mots de passe de psql)
# Prerequis : psql, jq, awk
#
# Composition avec les scripts existants du skill :
#   - introspect.sh    : NON invoque ici. Sa sortie est un rendu psql en tables unicode destine
#                        a la lecture humaine (bannieres \echo, \pset linestyle unicode), pas a
#                        la fusion machine dans un tableau markdown unique colonne/FK/selection/
#                        taux/valeur-modele. La LOGIQUE de ses sections 2 a 6 (colonnes, FK,
#                        selections, enfants O2M, jonctions M2M) est reprise a l'identique ici,
#                        executee en mode non aligne (-A) pour rester parseable.
#   - socle-b-shape.py : NON invoque. Son contrat est une comparaison DELTA entre une base
#                        vierge et une base de travail (fichiers "counts-<db>.txt" prealables
#                        via baseline-map.sh) pour reperer les 155 tables du compartiment B —
#                        pas le taux de remplissage colonne par colonne d'UNE table sur UNE
#                        base, qui est le besoin ici. Le motif SQL qu'il utilise (un seul
#                        aggregat count(col) par colonne, une passe) est repris directement.
#   - fk-closure.py    : NON invoque. Il calcule la fermeture des FK SORTANTES d'un jeu de
#                        tables de depart (utile pour delimiter un perimetre de peuplement),
#                        pas les enfants O2M ENTRANTS ni les jonctions M2M d'une seule table —
#                        ce que la section "Satellites" demande. Information redondante avec
#                        le taux de remplissage generique calcule ici (qui couvre aussi les
#                        colonnes FK) : pas de valeur ajoutee a l'appeler pour ce livrable.

set -euo pipefail

DB="${1:?usage: shape-fiche.sh <base> <table> [id-modele]}"
TABLE="${2:?usage: shape-fiche.sh <base> <table> [id-modele]}"
MODEL_ID="${3:-}"

: "${PGHOST:?definir PGHOST (hote PostgreSQL de la base cible)}"
: "${PGUSER:?definir PGUSER (utilisateur PostgreSQL)}"
export PGHOST PGUSER

# Delimiteur "unit separator" : ne collisionne jamais avec du texte metier (titres, noms...).
US=$'\x1f'
PSQL=(psql -h "$PGHOST" -U "$PGUSER" -d "$DB" -X -q -v ON_ERROR_STOP=1 -At -F "$US")

q() {
  # Execute le SQL recu sur stdin, une ligne par resultat, colonnes separees par $US.
  "${PSQL[@]}"
}

qval() {
  # Variante 1 valeur / 1 ligne, sans le delimiteur (evite tout parasite si UNE colonne).
  psql -h "$PGHOST" -U "$PGUSER" -d "$DB" -X -q -v ON_ERROR_STOP=1 -tA
}

# ─── 0. La table existe-t-elle ? ────────────────────────────────────────────────────────────
EXISTS=$(echo "SELECT to_regclass('${TABLE}') IS NOT NULL;" | qval)
if [ "$EXISTS" != "t" ]; then
  echo "ERREUR : la table '${TABLE}' n'existe pas dans la base '${DB}'." >&2
  exit 1
fi

TOTAL=$(echo "SELECT count(*) FROM \"${TABLE}\";" | qval)

# ─── En-tete : modele AOS, version AOS / plateforme, date ───────────────────────────────────
META_MODEL=$(echo "SELECT name FROM meta_model WHERE lower(table_name)=lower('${TABLE}') LIMIT 1;" | qval || true)
AOS_VERSION=$(echo "SELECT module_version FROM meta_module WHERE name='axelor-base' LIMIT 1;" | qval || true)
PLATFORM_VERSION=$(echo "SELECT module_version FROM meta_module WHERE name='axelor-core' LIMIT 1;" | qval || true)
CONSTRUCTION_VERSION=$(echo "SELECT module_version FROM meta_module WHERE name='axelor-construction' LIMIT 1;" | qval || true)
TODAY=$(date +%Y-%m-%d)

echo "# Fiche shape — \`${TABLE}\`"
echo
echo "| | |"
echo "|---|---|"
echo "| Base | \`${DB}\` |"
echo "| Table | \`${TABLE}\` |"
echo "| Modele AOS (\`meta_model\`) | ${META_MODEL:-non trouve (table sans meta_model — table technique/jonction)} |"
echo "| Version AOS (axelor-base) | ${AOS_VERSION:-inconnue} |"
echo "| Version plateforme (axelor-core) | ${PLATFORM_VERSION:-inconnue} |"
echo "| Version axelor-construction | ${CONSTRUCTION_VERSION:-non installe} |"
echo "| Lignes actuelles | ${TOTAL} |"
echo "| Genere le | ${TODAY} |"
echo "| Genere par | \`shape-fiche.sh ${DB} ${TABLE}${MODEL_ID:+ $MODEL_ID}\` |"
echo
echo "> Tout ce qui suit vient de l'introspection de \`${DB}\` au moment de la generation."
echo "> Rien n'est invente ; une absence est ecrite explicitement comme telle."
echo

# ─── 1. Colonnes techniques (identifiees, non detaillees en table) ──────────────────────────
TECH_COLS_RAW=$(cat <<SQL | q
SELECT column_name FROM information_schema.columns
WHERE table_schema='public' AND table_name='${TABLE}'
  AND column_name IN ('id','version','archived','import_id','import_origin',
                       'process_instance_id','created_on','updated_on','created_by','updated_by',
                       'is_data_capture_created','is_data_capture_updated')
ORDER BY ordinal_position;
SQL
)
TECH_COLS=$(echo "$TECH_COLS_RAW" | paste -sd, - | sed 's/,/, /g')

# ─── 2-4. Colonnes metier + FK + selections, fusionnees ─────────────────────────────────────
# Une seule requete par facette pour eviter les allers-retours, jointes en bash par nom de colonne.

COLS_RAW=$(cat <<SQL | q
SELECT c.column_name, c.data_type ||
       COALESCE('(' || c.character_maximum_length || ')', ''),
       CASE WHEN c.is_nullable='NO' THEN 'NOT NULL' ELSE '' END,
       COALESCE(c.column_default,'')
FROM information_schema.columns c
WHERE c.table_schema='public' AND c.table_name='${TABLE}'
  AND c.column_name NOT IN ('id','version','archived','import_id','import_origin',
                       'process_instance_id','created_on','updated_on','created_by','updated_by',
                       'is_data_capture_created','is_data_capture_updated')
ORDER BY c.ordinal_position;
SQL
)

declare -A FK_TARGET FK_NOTNULL
while IFS="$US" read -r col target notnull; do
  [ -z "$col" ] && continue
  FK_TARGET["$col"]="$target"
  FK_NOTNULL["$col"]="$notnull"
done < <(cat <<SQL | q
SELECT a.attname, cf.confrelid::regclass::text, a.attnotnull
FROM pg_constraint cf
JOIN pg_attribute a ON a.attrelid=cf.conrelid AND a.attnum=ANY(cf.conkey)
WHERE cf.contype='f' AND cf.conrelid='${TABLE}'::regclass
  AND array_length(cf.conkey,1)=1;
SQL
)

# Resolution des selections : convention "<modele-en-points>.<champ-en-points>.select" (core
# AOS) OU "<champ-en-points>.select" (champs d'extension/module, cf. piege verifie sur
# construction*Select) OU, a defaut, correspondance approchee unique. meta_field ne porte NI
# "selection" NI "name_column" en AOP 8.2 (piege 31 du skill) : on passe par meta_select /
# meta_select_item et le nom conventionnel, jamais par une colonne meta_field qui n'existe pas.
declare -A SEL_NAME SEL_VALUES SEL_STATUS
if [ -n "${META_MODEL}" ]; then
  while IFS="$US" read -r snake_col cand1 cand2; do
    [ -z "$snake_col" ] && continue
    field="$snake_col"
    exact=$(cat <<SQL | qval
SELECT string_agg(name, ',') FROM meta_select WHERE name IN ('${cand1}', '${cand2}');
SQL
)
    resolved=""
    status=""
    if [ -n "$exact" ] && [ "$(echo "$exact" | tr ',' '\n' | wc -l)" -eq 1 ]; then
      resolved="$exact"; status="exact"
    else
      fuzzy=$(cat <<SQL | q
SELECT name FROM meta_select WHERE name LIKE '%.${cand1}';
SQL
)
      nfuzzy=$(echo "$fuzzy" | grep -c . || true)
      if [ "$nfuzzy" -eq 1 ]; then
        resolved="$fuzzy"; status="approche"
      elif [ "$nfuzzy" -gt 1 ]; then
        resolved=$(echo "$fuzzy" | paste -sd, -); status="ambigu"
      else
        status="non_resolue"
      fi
    fi
    SEL_STATUS["$field"]="$status"
    if [ -n "$resolved" ] && [ "$status" != "ambigu" ]; then
      values=$(cat <<SQL | qval
SELECT string_agg(i.value || '=' || COALESCE(i.title,''), ' | ' ORDER BY i.order_seq)
FROM meta_select s JOIN meta_select_item i ON i.select_id=s.id
WHERE s.name='${resolved}';
SQL
)
      SEL_NAME["$field"]="$resolved"
      SEL_VALUES["$field"]="$values"
    elif [ "$status" = "ambigu" ]; then
      SEL_NAME["$field"]="$resolved"
    fi
  done < <(cat <<SQL | q
SELECT lower(regexp_replace(f.name,'([a-z0-9])([A-Z])','\1_\2','g')) AS snake_col,
       lower(regexp_replace(regexp_replace(f.name,'Select\$',''),'([a-z0-9])([A-Z])','\1.\2','g')) || '.select',
       lower(regexp_replace('${META_MODEL}','([a-z0-9])([A-Z])','\1.\2','g')) || '.' ||
       lower(regexp_replace(regexp_replace(f.name,'Select\$',''),'([a-z0-9])([A-Z])','\1.\2','g')) || '.select'
FROM meta_field f JOIN meta_model mm ON f.meta_model=mm.id
WHERE mm.name='${META_MODEL}' AND f.name ILIKE '%Select';
SQL
)
fi

# Taux de remplissage : un seul aggregat, une passe, quel que soit le nom des colonnes
# (via to_jsonb + jsonb_each_text, pas de reconstruction manuelle d'identifiants).
declare -A FILL_COUNT
if [ "$TOTAL" -gt 0 ]; then
  while IFS="$US" read -r col cnt; do
    [ -z "$col" ] && continue
    FILL_COUNT["$col"]="$cnt"
  done < <(cat <<SQL | q
DO \$\$
DECLARE cols text;
BEGIN
  SELECT string_agg(format('count(%I) AS %I', column_name, column_name), ', ')
    INTO cols FROM information_schema.columns
    WHERE table_schema='public' AND table_name='${TABLE}';
  EXECUTE format('CREATE TEMP TABLE _fillrates AS SELECT %s FROM %I', cols, '${TABLE}');
END \$\$;
SELECT kv.key, kv.value FROM _fillrates f, LATERAL jsonb_each_text(to_jsonb(f)) AS kv(key,value);
SQL
)
fi

# ─── Enregistrement modele : celui donne, sinon celui au plus de colonnes non NULL ──────────
MODEL_JSON=""
MODEL_LABEL="aucun (table vide)"
if [ "$TOTAL" -gt 0 ]; then
  if [ -n "$MODEL_ID" ]; then
    FOUND=$(echo "SELECT count(*) FROM \"${TABLE}\" WHERE id=${MODEL_ID};" | qval)
    if [ "$FOUND" = "0" ]; then
      echo "ERREUR : id-modele ${MODEL_ID} introuvable dans ${TABLE}." >&2
      exit 1
    fi
    CHOSEN_ID="$MODEL_ID"
    MODEL_LABEL="id ${CHOSEN_ID} (impose)"
  else
    CHOSEN_ID=$(cat <<SQL | qval
SELECT id FROM (
  SELECT id, (SELECT count(*) FROM jsonb_each_text(to_jsonb(t)) WHERE value IS NOT NULL) AS filled
  FROM "${TABLE}" t
) x ORDER BY filled DESC, id ASC LIMIT 1;
SQL
)
    MODEL_LABEL="id ${CHOSEN_ID} (auto — le plus de colonnes non NULL)"
  fi
  MODEL_JSON=$(echo "SELECT to_jsonb(t) FROM \"${TABLE}\" t WHERE id=${CHOSEN_ID};" | qval)
fi

# ─── Emission : section Colonnes ────────────────────────────────────────────────────────────
echo "## Colonnes"
echo
echo "### Colonnes techniques (non detaillees)"
echo
if [ -n "$TECH_COLS" ]; then
  echo "\`${TECH_COLS}\`"
else
  echo "(aucune)"
fi
echo
echo "### Colonnes metier"
echo
echo "| Colonne | Type | Obligatoire | Defaut | FK -> cible | Selection -> valeurs valides | Taux de remplissage | Valeur (record modele) |"
echo "|---|---|---|---|---|---|---|---|"
while IFS="$US" read -r col type notnull default; do
  [ -z "$col" ] && continue

  fk="-"
  if [ -n "${FK_TARGET[$col]+x}" ]; then
    fk="→ \`${FK_TARGET[$col]}\`"
  fi

  sel="-"
  case "${SEL_STATUS[$col]:-}" in
    exact) sel="\`${SEL_NAME[$col]}\` : ${SEL_VALUES[$col]}" ;;
    approche) sel="\`${SEL_NAME[$col]}\` (correspondance approchee) : ${SEL_VALUES[$col]}" ;;
    ambigu) sel="**ambigu** — candidats : \`${SEL_NAME[$col]}\` — a verifier manuellement" ;;
    non_resolue) sel="**selection non resolue** (aucun \`meta_select\` correspondant trouve — verifier le XML de domaine)" ;;
  esac

  fill="-"
  if [ "$TOTAL" -gt 0 ]; then
    cnt="${FILL_COUNT[$col]:-0}"
    pct=$(awk -v c="$cnt" -v t="$TOTAL" 'BEGIN{printf "%.0f", (t>0)?100.0*c/t:0}')
    fill="${cnt}/${TOTAL} (${pct}%)"
  else
    fill="n/a (table vide)"
  fi

  val="-"
  if [ -n "$MODEL_JSON" ]; then
    raw=$(echo "$MODEL_JSON" | jq -r --arg k "$col" '.[$k]')
    if [ "$raw" = "null" ] || [ -z "$raw" ]; then
      val="_NULL_"
    else
      val=$(echo "$raw" | cut -c1-60 | sed 's/|/\\|/g')
      if [ "${#raw}" -gt 60 ]; then val="${val}…"; fi
    fi
  fi

  # echapper les pipes dans les champs texte pour ne pas casser le tableau markdown
  type_e=$(echo "$type" | sed 's/|/\\|/g')
  echo "| \`${col}\` | ${type_e} | ${notnull:--} | ${default:--} | ${fk} | ${sel} | ${fill} | ${val} |"
done <<< "$COLS_RAW"
echo

# ─── Satellites ──────────────────────────────────────────────────────────────────────────────
echo "## Satellites"
echo
echo "### Enfants O2M (tables portant une FK vers \`${TABLE}\`)"
echo
echo "| Table enfant | Colonne -> moi | Obligatoire | Lignes |"
echo "|---|---|---|---|"
CHILDREN_RAW=$(cat <<SQL | q
SELECT cf.conrelid::regclass::text, a.attname, a.attnotnull,
       (xpath('/row/c/text()', query_to_xml('SELECT count(*) c FROM '||cf.conrelid::regclass, false, true, '')))[1]::text::bigint
FROM pg_constraint cf
JOIN pg_attribute a ON a.attrelid=cf.conrelid AND a.attnum=ANY(cf.conkey)
WHERE cf.contype='f' AND cf.confrelid='${TABLE}'::regclass
  AND array_length(cf.conkey,1)=1
ORDER BY 1;
SQL
)
if [ -n "$(echo "$CHILDREN_RAW" | grep -c . || true)" ] && [ -n "$(echo "$CHILDREN_RAW" | tr -d '[:space:]')" ]; then
  while IFS="$US" read -r ctable ccol cnotnull crows; do
    [ -z "$ctable" ] && continue
    echo "| \`${ctable}\` | \`${ccol}\` | ${cnotnull} | ${crows} |"
  done <<< "$CHILDREN_RAW"
else
  echo "| (aucun) | | | |"
fi
echo
echo "### Jonctions M2M (detection structurelle : table sans \`id\`, 2 colonnes, dont une FK vers \`${TABLE}\` — insensible a la troncature des noms a 63 caracteres, piege 33)"
echo
echo "| Table de jonction | Autre cote | Lignes |"
echo "|---|---|---|"
M2M_RAW=$(cat <<SQL | q
SELECT t.table_name,
       (SELECT confrelid::regclass::text FROM pg_constraint cf
          WHERE cf.contype='f' AND cf.conrelid=t.table_name::regclass
            AND confrelid <> '${TABLE}'::regclass LIMIT 1),
       (xpath('/row/c/text()', query_to_xml('SELECT count(*) c FROM '||quote_ident(t.table_name), false, true, '')))[1]::text::bigint
FROM information_schema.tables t
WHERE t.table_schema='public'
  AND NOT EXISTS (SELECT 1 FROM information_schema.columns c WHERE c.table_name=t.table_name AND c.column_name='id')
  AND (SELECT count(*) FROM information_schema.columns c WHERE c.table_name=t.table_name) = 2
  AND EXISTS (SELECT 1 FROM pg_constraint cf WHERE cf.contype='f' AND cf.conrelid=t.table_name::regclass AND cf.confrelid='${TABLE}'::regclass)
ORDER BY 1;
SQL
)
if [ -n "$(echo "$M2M_RAW" | tr -d '[:space:]')" ]; then
  while IFS="$US" read -r jtable other jrows; do
    [ -z "$jtable" ] && continue
    echo "| \`${jtable}\` | \`${other:-?}\` | ${jrows} |"
  done <<< "$M2M_RAW"
else
  echo "| (aucune) | | |"
fi
echo

# ─── Record modele ───────────────────────────────────────────────────────────────────────────
echo "## Record modele"
echo
echo "- **Choix** : ${MODEL_LABEL}"
if [ -n "$MODEL_JSON" ]; then
  name_val=$(echo "$MODEL_JSON" | jq -r 'if has("name") then .name elif has("fullName") then .fullName elif has("full_name") then .full_name else "(pas de colonne name/fullName)" end')
  id_val=$(echo "$MODEL_JSON" | jq -r '.id')
  echo "- **id** : ${id_val}"
  echo "- **nom** : ${name_val}"
else
  echo "- Table vide : pas de record modele disponible."
fi
echo

# ─── Couche UI-critical : vide par construction ─────────────────────────────────────────────
cat <<'GABARIT'
## Couche UI-critical

**Section volontairement VIDE.** Ni le schema ni un enregistrement modele ne la donnent — elle
est l'objet du stress-test qui consomme cette fiche (voir `references/socle-b-shape.md` et les
fiches `entites-*.md`). Gabarit a remplir, une ligne par constat, chacune avec sa preuve :

| Type de constat | Colonne / relation concernee | Ce qui casse / ce qui est exclu | Preuve (test, requete, capture) |
|---|---|---|---|
| Casse a NULL | | | |
| Domaine filtrant qui exclut le NULL | | | |
| Denormalisation non resynchronisee | | | |
| namecolumn / full_name et sa cascade | | | |
| A laisser au moteur (ne pas peupler en SQL) | | | |

**Version verifiee : ** _(AOS ___ / plateforme ___ — a completer par le stress-test)_
GABARIT
