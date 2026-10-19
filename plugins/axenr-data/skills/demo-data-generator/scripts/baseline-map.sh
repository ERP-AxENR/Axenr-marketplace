#!/usr/bin/env bash
# Regenere la carte de reference du socle AOS (references/socle-aos-baseline.md).
#
# Compare une base AOS VIERGE (socle livre par l'install) a une base TRAVAILLEE
# (demo reelle, reference empirique de credibilite) et produit :
#   - les 3 compartiments : A (AOS remplit) / B (AOS vide, il a fallu remplir) / C (vide partout)
#   - les taux de colonnes 100% NULL sur les tables metier
#   - le catalogue B en markdown
#
# Usage :
#   ./baseline-map.sh <base-vierge> <base-travaillee> [dossier-sortie]
#   ./baseline-map.sh <base-vierge> <base-travaillee> ./baseline-map
#
# Env : PGHOST et PGUSER (obligatoires) ; PGPASSWORD (ou le fichier de mots de passe de psql) ; PGPORT si besoin
#
# NE JAMAIS trier le socle via import_id / import_origin / created_on : verifie faux
# dans les deux sens (UPDATE conserve import_id ; le tag ne couvre qu'une fraction des
# lignes). La comparaison de comptages contre une base vierge est la seule methode fiable.

set -euo pipefail

VIERGE="${1:?base vierge de reference manquante (ex: <base-vierge>)}"
TRAVAIL="${2:?base travaillee manquante (ex: <base-travaillee>)}"
OUT="${3:-./baseline-map}"

: "${PGHOST:?definir PGHOST (hote PostgreSQL de la base cible)}"
: "${PGUSER:?definir PGUSER (utilisateur PostgreSQL)}"
# PGPASSWORD : variable d'environnement de la session (ou fichier de mots de passe de psql), jamais dans un fichier du skill ni dans une commande
export PGHOST PGUSER

mkdir -p "$OUT"

psql_q() { psql -d "$1" -At -F'|' -c "$2"; }

echo "== Contexte =="
for db in "$VIERGE" "$TRAVAIL"; do
  printf '  %-22s ' "$db"
  psql_q "$db" "select 'axelor-base='||coalesce((select module_version from meta_module where name='axelor-base'),'?')
    ||' modules='||(select count(*) from meta_module)
    ||' taille='||pg_size_pretty(pg_database_size(current_database()))" || true
done

echo "== Comptages exacts (query_to_xml, pas reltuples) =="
for db in "$VIERGE" "$TRAVAIL"; do
  # sanitisation identique cote python (re.sub) : printf, pas echo, sinon le \n
  # est lui aussi converti en '_' et les deux noms divergent.
  f="$OUT/counts-$(printf '%s' "$db" | tr -c 'a-zA-Z0-9' '_').txt"
  psql_q "$db" "
    select table_name, (xpath('/row/c/text()', x))[1]::text::bigint
    from (select table_name,
                 query_to_xml(format('select count(*) as c from public.%I', table_name),
                              false, true, '') as x
          from information_schema.tables
          where table_schema='public' and table_type='BASE TABLE') t
    order by 1" > "$f"
  echo "  $db -> $(wc -l < "$f") tables"
done

echo "== Taux de colonnes 100% NULL sur les tables metier =="
python3 - "$VIERGE" "$TRAVAIL" "$OUT" <<'PYFILL'
import subprocess, sys, json, os
vierge, travail, out = sys.argv[1], sys.argv[2], sys.argv[3]
# Tables ouvertes a l'ecran pendant une demo : c'est la que la largeur compte.
TABLES = ["base_partner","base_product","base_company","hr_employee","project_project",
 "project_project_task","sale_sale_order","sale_sale_order_line","purchase_purchase_order",
 "account_invoice","account_invoice_line","stock_stock_move","crm_lead","crm_opportunity",
 "base_address","base_bank_details","hr_timesheet","hr_timesheet_line","contract_contract",
 "production_manuf_order","base_product_category","account_account","helpdesk_ticket",
 "base_partner_category","account_move","project_project_planning_time"]
# Colonnes techniques AOP : jamais representatives du remplissage metier.
TECH = ("id","version","archived","created_on","updated_on","created_by","updated_by",
        "import_id","import_origin","process_instance_id")
def q(db, sql):
    r = subprocess.run(["psql","-d",db,"-At","-F","|","-c",sql],
                       capture_output=True, text=True)
    if r.returncode: return []
    return r.stdout.strip().splitlines()
res = {}
for db in (vierge, travail):
    res[db] = {}
    for t in TABLES:
        cols = q(db, "select column_name from information_schema.columns "
                     f"where table_schema='public' and table_name='{t}' "
                     f"and column_name not in {TECH} order by 1")
        if not cols: continue
        n = int((q(db, f"select count(*) from {t}") or ["0"])[0] or 0)
        if n == 0:
            res[db][t] = {"rows": 0}; continue
        exprs = ",".join(f'count("{c}")' for c in cols)
        vals = q(db, f"select {exprs} from {t}")[0].split("|")
        filled = {c: int(v) for c, v in zip(cols, vals)}
        vides = sorted(c for c, v in filled.items() if v == 0)
        res[db][t] = {"rows": n, "cols": len(cols), "vides": len(vides),
                      "pct": round(100*len(vides)/len(cols)),
                      "cols_vides": vides,
                      "partiel": {c: round(100*v/n) for c, v in filled.items() if 0 < v < n}}
json.dump(res, open(os.path.join(out, "fill-rates.json"), "w"), indent=1, ensure_ascii=False)
def fmt(d):
    if d is None: return "table absente"
    if d.get("rows", 0) == 0: return "0 ligne"
    return f"{d['rows']} l. / {d['pct']}% col. vides"
print(f"  {'table':<32}{'vierge':>26}{'travaillee':>26}")
for t in TABLES:
    a, b = res[vierge].get(t), res[travail].get(t)
    if not a and not b: continue
    print(f"  {t:<32}{fmt(a):>26}{fmt(b):>26}")
PYFILL

echo "== Compartiments A / B / C + catalogue B =="
python3 - "$VIERGE" "$TRAVAIL" "$OUT" <<'PYBUCKET'
import sys, os, re
vierge, travail, out = sys.argv[1], sys.argv[2], sys.argv[3]
def path(db): return os.path.join(out, "counts-%s.txt" % re.sub(r'[^a-zA-Z0-9]', '_', db))
def load(f):
    d = {}
    for l in open(f):
        l = l.strip()
        if '|' in l:
            t, c = l.rsplit('|', 1)
            try: d[t] = int(c)
            except ValueError: pass
    return d
aos, esn = load(path(vierge)), load(path(travail))
# Bruit technique : tracabilite, meta, sequences internes. Jamais de la donnee de demo.
NOISE = ('meta_','mail_','base_trace_back','base_batch','base_sequence_version',
         'base_reserved_sequence','studio_','auth_permission','ical_','dms_','base_app',
         'audit_log')
common = [t for t in esn if t in aos]
A = [t for t in common if aos[t] > 0]
B = [t for t in common if aos[t] == 0 and esn[t] > 0]
C = [t for t in common if aos[t] == 0 and esn[t] == 0]
Bu = sorted((t for t in B if not t.startswith(NOISE)), key=lambda t: -esn[t])
print(f"  tables communes : {len(common)}  ({vierge} {len(aos)} / {travail} {len(esn)})")
print(f"    A. AOS remplit deja                : {len(A)}")
print(f"    B. AOS vide, il a fallu remplir    : {len(B)}  ({len(Bu)} utiles)")
print(f"    C. vide dans les deux (angles morts): {len(C)}")
mod = {}
for t in Bu: mod.setdefault(t.split('_')[0], []).append(t)
with open(os.path.join(out, "catalogue-B.md"), "w") as fh:
    for m in sorted(mod, key=lambda m: -sum(esn[t] for t in mod[m])):
        ts = sorted(mod[m], key=lambda t: -esn[t])
        fh.write(f"\n**`{m}`** — {len(ts)} tables, {sum(esn[t] for t in ts)} lignes de référence\n\n")
        fh.write("| Table | Volumétrie de référence |\n|---|---:|\n")
        for t in ts: fh.write(f"| `{t}` | {esn[t]} |\n")
with open(os.path.join(out, "angles-morts-C.txt"), "w") as fh:
    for t in sorted(C): fh.write(t + "\n")
print(f"  -> {out}/catalogue-B.md, {out}/angles-morts-C.txt, {out}/fill-rates.json")
PYBUCKET

echo "== Shape du compartiment B (colonnes reellement renseignees) =="
python3 "$(dirname "$0")/socle-b-shape.py" "$VIERGE" "$TRAVAIL" "$OUT"

echo
echo "Reporter les chiffres dans references/socle-aos-baseline.md (§1 a §7)."
echo "Reassembler references/socle-b-shape.md : en-tete existant + $OUT/shape-B.md"
