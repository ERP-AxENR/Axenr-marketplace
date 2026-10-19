#!/usr/bin/env python3
"""Fermeture FK transitive d'un jeu de tables de depart.

Complete `introspect.sh`, qui donne les FK d'UNE table : ici on suit les FK de proche
en proche jusqu'a saturation, et on indique pour chaque colonne FK combien de lignes la
renseignent reellement. Sert a decider, avant d'ecrire, s'il faut elargir le perimetre a
une table de plus ou s'il est acceptable de laisser une FK hors perimetre a NULL.

Attention : une FK peu ou pas renseignee dans la base de reference ne signifie pas
qu'elle est optionnelle a l'ecran. Croiser avec le compartiment B de
references/socle-aos-baseline.md avant de conclure.

Usage :
  ./fk-closure.py <base> <table> [table ...]
  ./fk-closure.py <base> hr_employee project_project

Env : PGHOST et PGUSER (obligatoires) ; PGPASSWORD (ou le fichier de mots de passe de psql) ; PGPORT si besoin
Sortie : JSON sur stdout.
"""
import json
import os
import subprocess
import sys

if len(sys.argv) < 3:
    sys.exit(__doc__)

DB = sys.argv[1]
SEED = sys.argv[2:]
for _var in ("PGHOST", "PGUSER"):
    if not os.environ.get(_var):
        sys.exit(f"variable d'environnement {_var} absente : l'hote et l'utilisateur PostgreSQL "
                 "ne sont jamais supposes (mot de passe : PGPASSWORD)")
ENV = {k: v for k, v in os.environ.items() if k.startswith("PG") or k in ("PATH", "HOME")}


def psql(sql):
    r = subprocess.run(["psql", "-d", DB, "-tA", "-c", sql],
                       env=ENV, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def table_exists(table):
    return psql(f"SELECT to_regclass('{table}');").strip() != ""


def get_fks(table):
    # array_length(conkey,1)=1 : on ignore les FK composites, absentes du modele AOP.
    out = psql(f"""
        SELECT a.attname, confrelid::regclass::text
        FROM pg_constraint c
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
        WHERE c.conrelid = '{table}'::regclass
          AND c.contype = 'f' AND array_length(c.conkey, 1) = 1
        ORDER BY 1;""")
    fks = []
    for line in out.splitlines():
        if line.strip():
            col, target = line.split("|")
            fks.append((col, target))
    return fks


def nonnull_count(table, col):
    try:
        return int(psql(f'SELECT count("{col}") FROM {table};'))
    except Exception as exc:
        return f"ERR:{exc}"


seen, frontier, report = set(), set(SEED), {}
while frontier:
    t = frontier.pop()
    if t in seen:
        continue
    seen.add(t)
    if not table_exists(t):
        report[t] = {"error": "table absente de la base"}
        continue
    total = int(psql(f"SELECT count(*) FROM {t};"))
    cols = []
    for col, target in get_fks(t):
        cols.append({"col": col, "target": target,
                     "renseignee": nonnull_count(t, col), "lignes": total})
        frontier.add(target)
    report[t] = cols

print(json.dumps(report, indent=2, ensure_ascii=False))
