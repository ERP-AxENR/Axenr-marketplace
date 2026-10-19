#!/usr/bin/env python3
"""Shape structurelle des tables du compartiment B : quelles colonnes une demo reelle a
renseignees, a quel taux, et lesquelles sont restees vides.

AUCUNE VALEUR METIER n'est extraite - seulement la structure. Extraire des exemples de
contenu reintroduirait le biais sectoriel de la base d'origine, ce que la carte doit eviter.
"""
import json
import os
import re
import subprocess
import sys

if len(sys.argv) < 4:
    sys.exit("usage : socle-b-shape.py <base-vierge> <base-travaillee> <dossier-sortie> "
             "(appelé par baseline-map.sh, qui produit d'abord les fichiers counts-<base>.txt)")
vierge, travail, out = sys.argv[1], sys.argv[2], sys.argv[3]
for _var in ("PGHOST", "PGUSER"):
    if not os.environ.get(_var):
        sys.exit(f"variable d'environnement {_var} absente : l'hote et l'utilisateur PostgreSQL "
                 "ne sont jamais supposes (mot de passe : PGPASSWORD)")
ENV = dict(os.environ)
TECH = ("id", "version", "archived", "created_on", "updated_on", "created_by",
        "updated_by", "import_id", "import_origin", "process_instance_id", "attrs")
NOISE = ('meta_', 'mail_', 'base_trace_back', 'base_batch', 'base_sequence_version',
         'base_reserved_sequence', 'studio_', 'auth_permission', 'ical_', 'dms_',
         'base_app', 'audit_log')


def q(db, sql):
    r = subprocess.run(["psql", "-d", db, "-At", "-F", "|", "-c", sql],
                       env=ENV, capture_output=True, text=True)
    return [] if r.returncode else r.stdout.strip().splitlines()


def path(db):
    return os.path.join(out, "counts-%s.txt" % re.sub(r'[^a-zA-Z0-9]', '_', db))


def load(f):
    d = {}
    for l in open(f):
        l = l.strip()
        if '|' in l:
            t, c = l.rsplit('|', 1)
            try:
                d[t] = int(c)
            except ValueError:
                pass
    return d


aos, esn = load(path(vierge)), load(path(travail))
B = sorted((t for t in esn
            if t in aos and aos[t] == 0 and esn[t] > 0 and not t.startswith(NOISE)),
           key=lambda t: -esn[t])

# Un seul aller-retour pour toutes les colonnes des tables du compartiment B.
inlist = ",".join("'%s'" % t for t in B)
meta = {}
for line in q(travail, f"""
    select table_name, column_name, is_nullable, data_type
    from information_schema.columns
    where table_schema='public' and table_name in ({inlist})
    order by table_name, ordinal_position"""):
    t, c, nullable, typ = line.split("|")
    if c in TECH:
        continue
    meta.setdefault(t, []).append((c, nullable == "NO", typ))

shape = {}
for t in B:
    cols = meta.get(t, [])
    if not cols:
        continue
    n = esn[t]
    exprs = ",".join('count("%s")' % c for c, _, _ in cols)
    vals = q(travail, f"select {exprs} from {t}")
    if not vals:
        continue
    counts = [int(v) for v in vals[0].split("|")]
    remplies, partielles, vides = [], [], []
    for (c, notnull, typ), k in zip(cols, counts):
        if k == 0:
            vides.append(c)
        elif k == n:
            remplies.append(c + ("*" if notnull else ""))
        else:
            partielles.append(f"{c} ({round(100*k/n)}%)")
    shape[t] = {"lignes": n, "total_col": len(cols), "remplies": remplies,
                "partielles": partielles, "vides": vides}

json.dump(shape, open(os.path.join(out, "shape-B.json"), "w"), indent=1, ensure_ascii=False)

with open(os.path.join(out, "shape-B.md"), "w") as fh:
    fh.write("| Table | Lignes | Colonnes renseignées |\n|---|---:|---:|\n")
    for t, d in shape.items():
        k = len(d["remplies"]) + len(d["partielles"])
        fh.write(f"| `{t}` | {d['lignes']} | {k}/{d['total_col']} |\n")
    fh.write("\n---\n")
    for t, d in shape.items():
        k = len(d["remplies"]) + len(d["partielles"])
        fh.write(f"\n**`{t}`** — {d['lignes']} lignes, "
                 f"**{k}/{d['total_col']}** colonnes renseignées\n\n")
        if d["remplies"]:
            fh.write("- pleines : " + " · ".join(f"`{c}`" for c in d["remplies"]) + "\n")
        if d["partielles"]:
            fh.write("- partielles : " + " · ".join(f"`{c}`" for c in d["partielles"]) + "\n")
        if d["vides"]:
            fh.write("- **restées vides** : " + " · ".join(f"`{c}`" for c in d["vides"]) + "\n")

tot = sum(len(d["remplies"]) + len(d["partielles"]) for d in shape.values())
totv = sum(len(d["vides"]) for d in shape.values())
print(f"  {len(shape)} tables, {tot} colonnes renseignées, {totv} restées vides")
print(f"  -> {out}/shape-B.md ({os.path.getsize(os.path.join(out,'shape-B.md'))} octets)")
