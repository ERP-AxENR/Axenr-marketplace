#!/usr/bin/env bash
# Introspection complète d'une table Axelor avant de la peupler.
#
# Pourquoi ce script existe : les erreurs les plus coûteuses en peuplement de démo viennent
# de suppositions (« cette colonne est un entier », « cette sélection accepte 0 », « le
# rattachement se fait par bill_of_material »). Une introspection systématique coûte 5 secondes
# et supprime cette classe entière d'erreurs. Il liste AUSSI toutes les colonnes facultatives,
# ce qui rend concrète la règle « remplir un maximum de champs utiles, pas seulement le requis ».
#
# Usage : ./introspect.sh <base> <table> [<table2> ...]
#   ./introspect.sh <base> base_partner
#   ./introspect.sh <base> talent_job_application talent_education
#
# Variables d'environnement : PGHOST et PGUSER (obligatoires), PGPASSWORD (ou le fichier de mots de passe de psql),
# AOS_SRC (facultative : racine des sources AOS, citée dans le rappel de la section 4)

set -euo pipefail
DB="${1:?usage: introspect.sh <base> <table> [table2...]}"; shift
: "${PGHOST:?définir PGHOST (hôte PostgreSQL de la base cible)}"
: "${PGUSER:?définir PGUSER (utilisateur PostgreSQL)}"
export PGHOST PGUSER
PSQL="psql -h $PGHOST -U $PGUSER -d $DB -X -q"

for T in "$@"; do
cat <<SQL | $PSQL
\pset pager off
\pset linestyle unicode

\echo ''
\echo '════════════════════════════════════════════════════════════════════'
\echo '  TABLE : $T'
\echo '════════════════════════════════════════════════════════════════════'

\echo ''
\echo '── 1. VOLUMÉTRIE ACTUELLE ─────────────────────────────────────────'
SELECT count(*) AS lignes_existantes FROM $T;

\echo ''
\echo '── 2. COLONNES (type · NOT NULL · défaut) ──────────────────────────'
\echo '   Remplir un MAXIMUM de ces colonnes, pas seulement les NOT NULL.'
SELECT c.column_name AS colonne,
       c.data_type || COALESCE('(' || c.character_maximum_length || ')','') AS type,
       CASE WHEN c.is_nullable='NO' THEN 'NOT NULL' ELSE '' END AS obligatoire,
       COALESCE(c.column_default,'') AS defaut
FROM information_schema.columns c
WHERE c.table_name='$T'
  AND c.column_name NOT IN ('id','version','archived','import_id','process_instance_id',
                            'created_on','updated_on','created_by','updated_by')
ORDER BY (c.is_nullable='NO') DESC, c.ordinal_position;

\echo ''
\echo '── 3. CLÉS ÉTRANGÈRES → table cible ───────────────────────────────'
\echo '   Résoudre chaque FK par une SOUS-REQUÊTE sur un code/nom, jamais par un id en dur.'
SELECT a.attname AS colonne, cf.confrelid::regclass::text AS cible, a.attnotnull AS obligatoire,
       (SELECT count(*) FROM pg_class pc WHERE pc.oid=cf.confrelid) AS cible_existe
FROM pg_constraint cf
JOIN pg_attribute a ON a.attrelid=cf.conrelid AND a.attnum=ANY(cf.conkey)
WHERE cf.contype='f' AND cf.conrelid='$T'::regclass
  AND a.attname NOT IN ('created_by','updated_by')
ORDER BY a.attnotnull DESC, a.attname;

\echo ''
\echo '── 4. SÉLECTIONS et leurs VALEURS VALIDES ─────────────────────────'
\echo '   Ne jamais inventer une valeur : 0 est souvent INVALIDE (donc invisible en UI).'
WITH champs AS (
  SELECT f.name AS field, mm.name AS model
  FROM meta_field f JOIN meta_model mm ON f.meta_model=mm.id
  WHERE lower(mm.table_name)='$T'
)
SELECT ch.field AS champ, s.name AS selection,
       string_agg(i.value || '=' || COALESCE(i.title,''), ' | ' ORDER BY i.order_seq) AS valeurs
FROM champs ch
JOIN meta_select s ON s.name ILIKE '%' || lower(regexp_replace(ch.field,'([a-z0-9])([A-Z])','\1.\2','g')) || '%'
JOIN meta_select_item i ON i.select_id=s.id
WHERE ch.field LIKE '%Select' OR ch.field LIKE '%select'
GROUP BY ch.field, s.name ORDER BY ch.field;

\echo ''
\echo '   (si vide : chercher la selection dans le domaine XML du module)'
\echo '   grep -rn "name=\\"<champ>\\"" \$AOS_SRC/*/src/main/resources/domains/*.xml'

\echo ''
\echo '── 5. ENFANTS O2M (un header sans lignes est inutilisable) ─────────'
SELECT cf.conrelid::regclass::text AS table_enfant, a.attname AS colonne_vers_moi, a.attnotnull AS obligatoire,
       (xpath('/row/c/text()', query_to_xml('SELECT count(*) c FROM '||cf.conrelid::regclass, false, true, '')))[1]::text::bigint AS lignes
FROM pg_constraint cf
JOIN pg_attribute a ON a.attrelid=cf.conrelid AND a.attnum=ANY(cf.conkey)
WHERE cf.contype='f' AND cf.confrelid='$T'::regclass
ORDER BY 1;

\echo ''
\echo '── 6. JONCTIONS M2M (Attention : PostgreSQL tronque les noms à 63 car.) ─────'
SELECT t.table_name AS jonction,
       (xpath('/row/c/text()', query_to_xml('SELECT count(*) c FROM '||quote_ident(t.table_name), false, true, '')))[1]::text::bigint AS lignes
FROM information_schema.tables t
WHERE t.table_schema='public' AND t.table_name LIKE '$T\_%'
  AND (SELECT count(*) FROM information_schema.columns c WHERE c.table_name=t.table_name) <= 3
ORDER BY 1;

\echo ''
\echo '── 7. MODÈLE DE SHAPE : une ligne EXISTANTE bien remplie ──────────'
\echo '   Le meilleur guide de remplissage est un enregistrement du clone.'
\echo '   Inspecter :  SELECT * FROM $T ORDER BY id LIMIT 1;'
SQL
done

cat <<'EOF'

────────────────────────────────────────────────────────────────────
RAPPELS avant d'écrire l'INSERT
────────────────────────────────────────────────────────────────────
 1. Aucun booléen NULL      → true/false explicite (NULL est exclu des grids et des pickers)
 2. Aucun xxxSelect NULL    → une valeur de la liste ci-dessus (section 4)
 3. name / fullName         → posés à la main : AOS ne les calcule pas en SQL
 4. FK par sous-requête     → (SELECT id FROM ref WHERE code='X'), et un AND EXISTS(...) en garde :
                              une sous-requête sans résultat insère NULL EN SILENCE
 5. Satellites              → remplir les enfants O2M et les jonctions M2M (sections 5 et 6)
 6. Dates étalées           → offset dérivé de l'entité liée, jamais un offset constant
 7. Vérifier les VALEURS    → count() compte les 0 et les '' comme « rempli »
EOF
