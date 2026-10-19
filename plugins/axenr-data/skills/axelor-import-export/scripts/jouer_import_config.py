#!/usr/bin/env python3
"""ENV DE PREUVE SEULEMENT (écrit en base) : joue une liaison + un zip de CSV par une configuration
d'import (Administration > Configurations d'import), comme le ferait un utilisateur à l'écran.

  jouer_import_config.py --cred C.json --bind input-config.xml --data data.zip --nom <libellé> \
                         --confirm-write <URL exacte>
Affiche l'historique d'import (compteurs) et écrit le journal d'import renvoyé par l'instance.
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # ee_api.py livré à côté
import ee_api  # noqa: E402

ap = argparse.ArgumentParser()
for a in ("--cred", "--bind", "--data", "--nom", "--confirm-write"):
    ap.add_argument(a, required=True)
ap.add_argument("--out", default=".")
a = ap.parse_args()
c = json.load(open(a.cred))
if a.confirm_write != c["url"]:
    sys.exit(f"--confirm-write ({a.confirm_write}) différent de l'URL du fichier d'accès ({c['url']}) : refus")
if "localhost" not in c["url"]:
    sys.exit("refus : ce script n'écrit que sur un env de preuve local")
cl = ee_api.Client(c["url"], c["username"], c["password"])
bind_id, data_id = cl.upload(a.bind), cl.upload(a.data)
moi = cl.search("com.axelor.auth.db.User", ["id"], domain="self.code = :c", ctx={"c": c["username"]})[0][0]["id"]
r = cl.post("/ws/rest/com.axelor.apps.base.db.ImportConfiguration", json={"data": {
    "name": a.nom, "typeSelect": "csv", "user": {"id": moi}, "bindMetaFile": {"id": bind_id}, "dataMetaFile": {"id": data_id}}}).json()
if r.get("status") != 0:
    sys.exit(f"création refusée : {json.dumps(r)[:600]}")
ic = r["data"][0]
full = cl.get(f"/ws/rest/com.axelor.apps.base.db.ImportConfiguration/{ic['id']}").json()["data"][0]
full["_model"] = "com.axelor.apps.base.db.ImportConfiguration"
t0 = time.time()
r = cl.post("/ws/action", json={"action": "action-import-configuration-method-run",
                                "model": "com.axelor.apps.base.db.ImportConfiguration",
                                "data": {"context": full}}).json()
print(f"action run : status {r.get('status')} en {time.time() - t0:.0f} s  {json.dumps(r)[:400]}")
h = cl.post("/ws/rest/com.axelor.apps.base.db.ImportHistory/search", json={
    "fields": ["log", "logMetaFile", "createdOn"], "sortBy": ["-id"], "limit": 1,
    "data": {"_domain": "self.importConfiguration.id = :i", "_domainContext": {"i": ic["id"]}}}).json()
for x in h.get("data") or []:
    print("historique :", x.get("log"))
    lf = x.get("logMetaFile")
    if lf:
        rr = cl.get(f"/ws/rest/com.axelor.meta.db.MetaFile/{lf['id']}/content/download")
        p = os.path.join(a.out, f"journal-import-{ic['id']}.log")
        open(p, "wb").write(rr.content)
        print("journal :", p)
