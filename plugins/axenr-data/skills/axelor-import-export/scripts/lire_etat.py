#!/usr/bin/env python3
"""Relit, en LECTURE SEULE, les fiches d'un périmètre sur une instance Axelor et les écrit en CSV (oracle, ou
contrôle de la base recréée). Aucune écriture : /callback, /ws/meta/fields, /ws/rest/<modèle>/search.

  lire_etat.py --cred acces.json --perimetre perimetre.json --out etat/ [--meta]

Règles (identiques à comparer_etat.py) : clé de ligne = champ « cle » du modèle ; hors comparaison : id,
version, dates et auteurs, champs calculés (virtual), un-à-plusieurs, mots de passe ; fichier (MetaFile) :
présence seule ; plusieurs-à-un : clé métier de la cible (« cles_cibles ») ; plusieurs-à-plusieurs : clés
triées « a|b » ; booléen vide en base : NULL ; décimal normalisé. --meta écrit aussi etat/_meta/<Modèle>.json
(types des champs), dont generer_paquet.py a besoin.
"""
import argparse, csv, json, os, sys
from decimal import Decimal

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import ee_api  # noqa: E402
import perimetre as P  # noqa: E402

EXCLUS = {"id", "version", "createdOn", "createdBy", "updatedOn", "updatedBy",
          "password", "passwordUpdatedOn", "forcePasswordChange", "transientPassword"}
CLE_DEFAUT = ["importId", "code", "name"]
CLE_CIBLE = {}


class Lecteur:
    def __init__(self, cl):
        self.cl, self.meta_cache, self.cles = cl, {}, {}

    def meta(self, model):
        if model not in self.meta_cache:
            self.meta_cache[model] = {f["name"]: f for f in self.cl.meta(model)["fields"]}
        return self.meta_cache[model]

    def search_all(self, model, fields, domain, ctx):
        rows, off = [], 0
        while True:
            body = {"fields": fields, "limit": 500, "offset": off, "sortBy": ["id"],
                    "data": {"_domain": domain, "_domainContext": ctx, "_archived": True}}
            r = self.cl.post(f"/ws/rest/{model}/search", json=body).json()
            if r.get("status") != 0:
                raise RuntimeError(f"{model} : {json.dumps(r)[:400]}")
            part = r.get("data") or []
            rows += part
            off += 500
            if not part or off >= r.get("total", 0):
                return rows

    def resoudre(self, target, ids):
        cache = self.cles.setdefault(target, {})
        manque = sorted(set(ids) - set(cache))
        if not manque or target == "com.axelor.meta.db.MetaFile":
            return
        champs = [c for c in ([CLE_CIBLE[target]] if target in CLE_CIBLE else CLE_DEFAUT) if c in self.meta(target)]
        for i in range(0, len(manque), 400):
            lot = manque[i:i + 400]
            for r in self.search_all(target, champs or ["id"], "self.id IN (:ids)", {"ids": lot}):
                val = next((str(r[c]) for c in champs if r.get(c) not in (None, "")), "")
                cache[r["id"]] = val or f"id:{r['id']}"

    def cle(self, target, ident):
        if target == "com.axelor.meta.db.MetaFile":
            return "oui"
        return self.cles.get(target, {}).get(ident, f"id:{ident}")

    def valeur(self, f, v):
        t = f["type"]
        if t in ("MANY_TO_ONE", "ONE_TO_ONE"):
            return "" if not v else self.cle(f["target"], v["id"])
        if t == "MANY_TO_MANY":
            return "|".join(sorted(self.cle(f["target"], x["id"]) for x in (v or [])))
        if t == "BOOLEAN":
            return "NULL" if v is None else ("true" if v else "false")
        if v is None:
            return ""
        if t == "DECIMAL":
            return format(Decimal(str(v)).normalize(), "f")
        return str(v)

    def lire(self, model, domain, ctx):
        meta = self.meta(model)
        champs = sorted(n for n, f in meta.items()
                        if n not in EXCLUS and not f.get("virtual") and not f.get("json")
                        and f["type"] not in ("ONE_TO_MANY", "BINARY"))
        rows = self.search_all(model, champs, domain, ctx)
        refs = {}
        for r in rows:
            for c in champs:
                f, v = meta[c], r.get(c)
                if f["type"] in ("MANY_TO_ONE", "ONE_TO_ONE") and v:
                    refs.setdefault(f["target"], []).append(v["id"])
                elif f["type"] == "MANY_TO_MANY" and v:
                    refs.setdefault(f["target"], []).extend(x["id"] for x in v)
        for target, ids in refs.items():
            self.resoudre(target, ids)
        return champs, [{c: self.valeur(meta[c], r.get(c)) for c in champs} for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cred", required=not os.environ.get("AOS_COOKIE_JAR"),
                    help="fichier d'accès (instance locale jetable) ; ignoré si AOS_COOKIE_JAR est défini (session hébergée)")
    ap.add_argument("--perimetre", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--meta", action="store_true")
    a = ap.parse_args()
    per = P.charger(a.perimetre)
    CLE_CIBLE.update(per["cles_cibles"])
    if os.environ.get("AOS_COOKIE_JAR"):  # session hébergée ouverte par l'utilisateur (curl) : ni fichier d'accès ni mot de passe
        cli = ee_api.connect(a)
        url = cli.base
    else:
        c = json.load(open(a.cred))
        cli = ee_api.Client(c["url"], c["username"], c["password"])
        url = c["url"]
    lec = Lecteur(cli)
    ctx = P.contexte(per)
    os.makedirs(a.out, exist_ok=True)
    comptes = {}
    for m in per["modeles"]:
        nom, model, cle = m["nom"], m["type"], m["cle"]
        champs, rows = lec.lire(model, m["domaine"], ctx)
        rows.sort(key=lambda r: r[cle])
        champs = [cle] + [x for x in champs if x != cle]
        with open(os.path.join(a.out, f"{nom}.csv"), "w", encoding="utf-8", newline="") as h:
            w = csv.DictWriter(h, fieldnames=champs, delimiter=";")
            w.writeheader()
            w.writerows(rows)
        if a.meta:
            os.makedirs(os.path.join(a.out, "_meta"), exist_ok=True)
            f = lec.meta(model)
            json.dump({"model": model, "fields": {n: {k: x.get(k) for k in ("type", "target", "required", "unique",
                       "virtual", "defaultValue", "selection")} for n, x in f.items()}},
                      open(os.path.join(a.out, "_meta", f"{nom}.json"), "w"), indent=0, ensure_ascii=False)
        comptes[nom] = len(rows)
        print(f"{nom:18} {len(rows):5}", flush=True)
    json.dump({"url": url, "comptes": comptes}, open(os.path.join(a.out, "_comptes.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
