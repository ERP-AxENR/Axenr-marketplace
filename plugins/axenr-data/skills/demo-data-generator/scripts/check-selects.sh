#!/usr/bin/env bash
# check-selects.sh — balaie TOUTES les valeurs de sélection écrites sous un tag et les confronte
# aux listes réelles de la base.
#
# Pourquoi ce script existe : la règle cardinale 4 dit « aucune sélection inventée ». Elle est
# facile à énoncer et facile à enfreindre — une valeur plausible s'écrit sans effort, l'insert
# passe, et le défaut ne se révèle qu'à l'écran, parfois devant quelqu'un. Une valeur de sélection
# fausse ne produit pas d'erreur : elle produit un champ vide, un enregistrement filtré hors d'une
# liste, ou une exception tardive dans un service qui branche sur elle.
#
# Le script ne remplace pas la lecture de la fiche `entites-*.md` du domaine — elle porte le SENS
# des valeurs, lui ne vérifie que leur EXISTENCE. Mais il attrape la classe entière d'erreurs même
# quand la fiche n'a pas été ouverte, ce qui est exactement le cas où elle mord.
#
# Usage :
#   ./check-selects.sh <base> <tag> [chemin/vers/.axelor]
#
#   base   nom de la base PostgreSQL
#   tag    la valeur d'import_origin posée sur les lignes créées
#   .axelor  racine des sources AOS/AOP de la version qui TOURNE (checkout git du tag, par exemple ;
#            défaut : ./.axelor dans le répertoire courant, à créer ou à lier).
#            Connexion à la base : variables PGHOST, PGUSER, PGPASSWORD comme pour psql.
#            Les sources servent à retrouver, pour chaque colonne `*_select`, le nom de la
#            sélection déclarée dans les domaines XML.
#
# Sortie : une ligne par valeur hors liste, avec les valeurs valides. 0 ligne = rien à corriger.
# Code de retour : 0 si rien à signaler, 1 sinon, 2 si les sources ou la base sont inaccessibles —
# utilisable comme garde dans un enchaînement.
#
# Faux positifs attendus, et pourquoi ils ne sont pas des défauts : plusieurs colonnes AOS portent
# `0` comme valeur NEUTRE sans que `0` figure dans la sélection (`size_select`,
# `charge_back_purchase_select`, `inventory_type_select`…). Avant de corriger une valeur signalée,
# comparer au SOCLE : si les lignes non taguées portent la même valeur, c'est la valeur neutre de
# l'application, pas une invention. Le script affiche cette comparaison pour chaque signalement.

set -uo pipefail

BASE="${1:?usage: check-selects.sh <base> <tag> [chemin/.axelor]}"
TAG="${2:?usage: check-selects.sh <base> <tag> [chemin/.axelor]}"
AXELOR="${3:-.axelor}"

if [ ! -d "$AXELOR" ]; then
  echo "Sources introuvables : $AXELOR" >&2
  echo "Monter les sources de la version qui TOURNE (pas celles d'une autre version)." >&2
  exit 2
fi

python3 - "$BASE" "$TAG" "$AXELOR" <<'PY'
import glob, re, subprocess, sys, collections

base, tag, axelor = sys.argv[1], sys.argv[2], sys.argv[3]


def q(sql):
    r = subprocess.run(['psql', '-d', base, '-tAX', '-c', sql],
                       capture_output=True, text=True)
    if r.returncode != 0:  # connexion ou requête en échec : jamais un faux « rien à signaler »
        print("psql en échec (vérifier PGHOST, PGUSER, mot de passe, nom de base) : " + r.stderr.strip()[:300],
              file=sys.stderr)
        sys.exit(2)
    return [x for x in r.stdout.split('\n') if x.strip()]


# 1. Les champs à sélection, lus dans les domaines XML des sources
sel = {}
for f in glob.glob(f'{axelor}/**/src/main/resources/domains/*.xml', recursive=True):
    txt = open(f, encoding='utf-8', errors='replace').read()
    for ent in re.finditer(r'<entity name="(\w+)"(.*?)</entity>', txt, re.S):
        for fld in re.finditer(r'<(integer|string)\s+name="(\w+)"([^>]*)/?>', ent.group(2)):
            m = re.search(r'selection="([^"]+)"', fld.group(3))
            if m:
                sel.setdefault(fld.group(2), set()).add(m.group(1))

if not sel:
    print("Aucun champ à sélection trouvé dans les sources : vérifier le chemin .axelor", file=sys.stderr)
    sys.exit(2)


def camel(col):
    p = col.split('_')
    return p[0] + ''.join(x.capitalize() for x in p[1:])


# 2. Les tables taguées, et leurs colonnes *_select
tables = q(f"""
  SELECT DISTINCT c.table_name FROM information_schema.columns c
   WHERE c.column_name = 'import_origin' AND c.table_schema = 'public'
""")

signale = 0
for t in tables:
    try:
        n = q(f"SELECT count(*) FROM {t} WHERE import_origin = '{tag}'")[0]
    except IndexError:
        continue
    if n == '0':
        continue
    cols = q(f"""SELECT column_name FROM information_schema.columns
                  WHERE table_name = '{t}' AND column_name LIKE '%!_select' ESCAPE '!'""")
    for col in cols:
        noms = sel.get(camel(col))
        if not noms or len(noms) != 1:
            continue          # ambigu entre plusieurs modules : on ne devine pas
        selname = next(iter(noms))
        valides = set(q(f"""SELECT i.value FROM meta_select s
                             JOIN meta_select_item i ON i.select_id = s.id
                            WHERE s.name = '{selname}'"""))
        if not valides:
            continue
        posees = q(f"""SELECT DISTINCT {col}::text FROM {t}
                        WHERE import_origin = '{tag}' AND {col} IS NOT NULL""")
        for v in posees:
            if v not in valides:
                socle = q(f"""SELECT count(*) FROM {t}
                               WHERE COALESCE(import_origin,'') <> '{tag}' AND {col}::text = '{v}'""")
                socle = socle[0] if socle else '0'
                verdict = (f"le socle porte la même valeur sur {socle} ligne(s) → probablement la "
                           f"valeur neutre de l'application, à confirmer"
                           if socle != '0' else "ABSENTE du socle → valeur très probablement inventée")
                print(f"{t}.{col} = {v}")
                print(f"    sélection : {selname}")
                print(f"    valides   : {', '.join(sorted(valides))}")
                print(f"    verdict   : {verdict}")
                signale += 1

if signale == 0:
    print(f"Aucune valeur de sélection hors liste sous le tag {tag}.")
sys.exit(1 if signale else 0)
PY
