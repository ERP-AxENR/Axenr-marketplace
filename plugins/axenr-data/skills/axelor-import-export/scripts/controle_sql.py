#!/usr/bin/env python3
"""ENV DE PREUVE (accès PostgreSQL direct, lecture seule) : cases à cocher NULL sur les fiches du périmètre,
et, avec --empreinte, empreinte ligne à ligne (md5 de la ligne entière, version et dates comprises) pour
prouver qu'une opération (rejeu, démarrage sur base existante) n'a RIEN écrit.

  controle_sql.py --perimetre perimetre.json --base <base>                 # booléens NULL (code 1 si > 0)
  controle_sql.py --perimetre perimetre.json --base <base> --empreinte > avant.txt ; … ; diff avant.txt apres.txt
Tables et filtres : « table » / « filtre_sql » de chaque modèle, « tables_liaison » du périmètre.

Connexion PostgreSQL : options --hote / --port / --utilisateur, sinon variables PGHOST / PGPORT / PGUSER ;
mot de passe par PGPASSWORD (ou ~/.pgpass), jamais en argument. Sans rien, ce sont les défauts de libpq
(socket local, utilisateur du système). Prérequis : le client `psql` dans le PATH.
"""
import argparse, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perimetre as P  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--perimetre", required=True)
ap.add_argument("--base", required=True, help="nom de la base PostgreSQL de l'env de preuve")
ap.add_argument("--hote", default=os.environ.get("PGHOST"), help="hôte PostgreSQL (défaut : PGHOST)")
ap.add_argument("--port", default=os.environ.get("PGPORT"), help="port PostgreSQL (défaut : PGPORT)")
ap.add_argument("--utilisateur", default=os.environ.get("PGUSER"), help="utilisateur PostgreSQL (défaut : PGUSER)")
ap.add_argument("--empreinte", action="store_true")
a = ap.parse_args()
per = P.charger(a.perimetre)


def q(sql):
    cmd = ["psql"]
    for opt, val in (("-h", a.hote), ("-p", a.port), ("-U", a.utilisateur)):
        if val:
            cmd += [opt, str(val)]
    cmd += ["-d", a.base, "-AtF", "|", "-c", sql]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("psql introuvable : installer le client PostgreSQL (il doit être dans le PATH)")
    if r.returncode:
        sys.exit(r.stderr)
    return [l.split("|") for l in r.stdout.strip().splitlines() if l]


if a.empreinte:
    for j in per.get("tables_liaison", []):
        print(f"## {j} " + q(f"SELECT count(*) || ' md5=' || md5(string_agg(x::text, ',' ORDER BY x::text)) FROM {j} x")[0][0])
    for m in per["modeles"]:
        t, w = m["table"], m["filtre_sql"]
        print(f"## {t} total={q(f'SELECT count(*) FROM {t}')[0][0]}")
        for i, h in q(f"SELECT id, md5(x::text) FROM {t} x WHERE {w} ORDER BY id"):
            print(i, h)
    app = per["application"]
    print("## meta_module", q(f"SELECT count(*) FROM meta_module WHERE name = '{app}'")[0][0])
    sys.exit(0)

total = 0
for m in per["modeles"]:
    t, w = m["table"], m["filtre_sql"]
    cols = [c for (c,) in q(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}' AND data_type = 'boolean'")]
    n = q(f"SELECT count(*) FROM {t} WHERE {w}")[0][0]
    nulls = {c: k for c in cols if (k := int(q(f"SELECT count(*) FROM {t} WHERE ({w}) AND {c} IS NULL")[0][0]))}
    total += sum(nulls.values())
    print(f"{t:28} fiches {n:>6}  booléens {len(cols):3}  cases NULL {sum(nulls.values()):5} {nulls or ''}")
print("comptes non bloqués (tous) :", q("SELECT count(*) FROM auth_user WHERE blocked IS NOT TRUE")[0][0])
print(f"TOTAL cases à cocher NULL : {total}")
sys.exit(1 if total else 0)
