#!/usr/bin/env python3
"""Read-only checks IN THE DATABASE of what an integration created: a batch counter proves nothing.

    python3 -I db_check.py <database> <expectations.json> [step]

expectations.json: {"<step>": [check, ...]} or a plain list. A check is
    {"name": "leave of 9001 validated", "sql": "SELECT ...", "expect": [["3", "2026-10-19"]]}
    {"name": "no orphan line", "sql": "SELECT ...", "expect_count": 0}
    {"name": "employee exists", "sql": "SELECT ...", "expect_min": 1}
Values are compared as the strings psql prints (-At, "|" separator, NULL = empty string).

Only SELECT / WITH statements are run, in a read-only transaction. Connection: the standard libpq settings
($PGHOST, $PGPORT, $PGUSER, $PGPASSWORD or ~/.pgpass); nothing is assumed, and psql never prompts (-w), so an
unreachable or unauthenticated database stops with psql's own message. Prints one OK/KO line per check;
exit code 1 on any KO.
"""
import json
import os
import subprocess
import sys


def run(db, query):
    q = query.strip().rstrip(";")
    if not q.lower().startswith(("select", "with")):
        raise SystemExit(f"refused (read only): {q[:60]}")
    cmd = ["psql", "-w", "-d", db, "-At", "-F", "|", "-v", "ON_ERROR_STOP=1", "-c", q]
    env = dict(os.environ, PGOPTIONS="-c default_transaction_read_only=on")
    out = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if out.returncode:
        raise RuntimeError(out.stderr.strip())
    return [line.split("|") for line in out.stdout.splitlines() if line]


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    db, spec = sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8"))
    checks = spec if isinstance(spec, list) else spec[sys.argv[3]] if len(sys.argv) > 3 else \
        [c for step in spec.values() for c in step]
    ko = 0
    for c in checks:
        try:
            rows = run(db, c["sql"])
        except RuntimeError as e:
            ko += 1
            print(f"KO {c['name']}: SQL error {e}")
            continue
        if "expect" in c:
            want = [[str(v) if v is not None else "" for v in r] for r in c["expect"]]
            good = rows == want
            detail = f"expected {want} got {rows}"
        elif "expect_count" in c:
            good, detail = len(rows) == c["expect_count"], f"expected {c['expect_count']} rows got {len(rows)}"
        else:
            good, detail = len(rows) >= c.get("expect_min", 1), f"expected >= {c.get('expect_min', 1)} rows got {len(rows)}"
        ko += not good
        print(f"{'OK' if good else 'KO'} {c['name']}" + ("" if good else f": {detail}"))
    print(f"{len(checks) - ko}/{len(checks)} OK")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
