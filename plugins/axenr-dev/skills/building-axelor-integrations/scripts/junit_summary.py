#!/usr/bin/env python3
"""Summary of JUnit reports (build/test-results/test/*.xml): per class, then the failing tests.

    python3 -I junit_summary.py <module>/build/test-results/test

Exit code 1 when a test fails or no report is found (a green build with 0 test proves nothing).
"""
import glob
import os
import sys
import xml.etree.ElementTree as ET

d = sys.argv[1] if len(sys.argv) > 1 else "build/test-results/test"
tot = [0, 0, 0, 0]
failed = []
for f in sorted(glob.glob(os.path.join(d, "TEST-*.xml"))):
    r = ET.parse(f).getroot()
    n, fl, er, sk = (int(r.get(k, 0)) for k in ("tests", "failures", "errors", "skipped"))
    tot = [a + b for a, b in zip(tot, (n, fl, er, sk))]
    print(f"{r.get('name').split('.')[-1]:45s} tests={n:3d} failures={fl:2d} errors={er:2d} skipped={sk}")
    for tc in r.findall("testcase"):
        pb = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        if pb is not None:
            msg = (pb.get("message") or "").splitlines()[0][:150] if pb.get("message") else pb.get("type")
            failed.append(f"  - {tc.get('classname').split('.')[-1]}.{tc.get('name')} : {msg}")
print(f"TOTAL tests={tot[0]} failures={tot[1]} errors={tot[2]} skipped={tot[3]}")
if failed:
    print("Failing:")
    print("\n".join(failed))
sys.exit(1 if failed or tot[0] == 0 else 0)
