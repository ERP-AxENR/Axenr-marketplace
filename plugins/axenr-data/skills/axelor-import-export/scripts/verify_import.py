#!/usr/bin/env python3
"""Vérifie, valeur par valeur et en LECTURE seule, qu'un classeur importé a bien écrit ce qu'il porte.

  verify_import.py CLASSEUR.xlsx [--cred F] [-o ecarts.csv]

Onglet principal (nom = modèle) : chaque ligne est relue par sa clé d'import via l'API REST, avec les
colonnes du fichier comme champs (un lien simple se relit en notation pointée, ex. unit.importId ; un lien
écrit par clé fabriquée `unit-40` est comparé à l'id). Onglet de liaison « Modele.collection » (colonnes
importId + collection.<clé>) : ensemble attendu comparé à la collection en base.
Écarts : ABSENTE, VIDE (valeur attendue, rien en base : lien non résolu, colonne ignorée), DIFFERENTE,
MEMBRE MANQUANT ; MEMBRE EN PLUS est listé sans compter comme échec (membres déjà présents avant l'import).
Les colonnes de mot de passe ne sont jamais relues par l'API : elles ne doivent pas être dans un gabarit.
"""
import argparse, csv, os, re, sys
from decimal import Decimal, InvalidOperation
import openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ee_api import connect, fqn, dasherize  # noqa: E402

def norm(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v).strip()
    if s.lower() in ("true", "false"):
        return s.lower()
    try:
        return str(Decimal(s).normalize())
    except InvalidOperation:
        return s[:10] if len(s) >= 19 and s[4] == "-" and s[10] in "T " else s

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file"); p.add_argument("--cred"); p.add_argument("-o", "--out", default="ecarts.csv")
    a = p.parse_args()
    c = connect(a)
    wb = openpyxl.load_workbook(a.file, read_only=True, data_only=True)
    ecarts, checked = [], 0
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows or "importId" not in (rows[0] or ()):
            print(f"-- {ws.title} : ignoré (pas de colonne importId)")
            continue
        hdr = [str(h) for h in rows[0]]
        data = [dict(zip(hdr, r)) for r in rows[1:] if any(v not in (None, "") for v in r)]
        model, _, coll = ws.title.partition(".")
        try:
            meta = {f["name"]: f for f in c.meta(model)["fields"]}
            if not coll:
                cols = [h for h in hdr if h not in ("importId", "password", "transientPassword")]
                ask = set(cols)
                for col in cols:                       # lien par clé fabriquée : relire aussi l'id
                    head, _, sub = col.partition(".")
                    if sub == "importId":
                        ask.add(f"{head}.id")
                for i in range(0, len(data), 200):
                    part = data[i:i + 200]
                    keys = [str(d["importId"]) for d in part]
                    got, _ = c.search(model, ["importId"] + sorted(ask), domain="self.importId in (:k)",
                                      ctx={"k": keys}, limit=len(keys))
                    by = {g.get("importId"): g for g in got}
                    for d in part:
                        k = str(d["importId"]); g = by.get(k)
                        if g is None:
                            ecarts.append([ws.title, k, "", "", "", "ABSENTE"]); continue
                        for col in cols:
                            exp = norm(d.get(col))
                            if exp is None:
                                continue
                            checked += 1
                            head, _, sub = col.partition(".")
                            tgt = (meta.get(head) or {}).get("target", "").split(".")[-1]
                            if sub == "importId" and tgt and re.fullmatch(re.escape(dasherize(tgt)) + r"-(\d+)", exp):
                                exp_id = exp.rsplit("-", 1)[1]
                                val = norm(g.get(f"{head}.id"))
                                if val != exp_id:
                                    ecarts.append([ws.title, k, col, exp, f"id {val}" if val else "", "VIDE" if val is None else "DIFFERENTE"])
                                continue
                            val = norm(g.get(col))
                            if val is None:
                                ecarts.append([ws.title, k, col, exp, "", "VIDE"])
                            elif exp != val:
                                ecarts.append([ws.title, k, col, exp, val, "DIFFERENTE"])
            else:
                keycol = next(h for h in hdr if h.startswith(coll + "."))
                sub = keycol.split(".", 1)[1]
                exp = {}
                for d in data:
                    exp.setdefault(str(d["importId"]), set()).add(norm(d.get(keycol)))
                parents, _ = c.search(model, ["importId", coll], domain="self.importId in (:k)",
                                      ctx={"k": list(exp)}, limit=len(exp))
                tgt_model = meta[coll]["target"]
                for par in parents:
                    ids = [x["id"] for x in par.get(coll) or []]
                    vals = set()
                    if ids:
                        t, _ = c.search(tgt_model, [sub], domain="self.id in (:i)", ctx={"i": ids}, limit=len(ids))
                        vals = {norm(x.get(sub)) for x in t}
                    k = par["importId"]; want = exp.get(k, set()); checked += len(want)
                    if want - vals:
                        ecarts.append([ws.title, k, keycol, "|".join(sorted(map(str, want - vals))), "|".join(sorted(map(str, vals))), "MEMBRE MANQUANT"])
                    if vals - want:
                        ecarts.append([ws.title, k, keycol, "", "|".join(sorted(map(str, vals - want))), "MEMBRE EN PLUS"])
                for k in set(exp) - {p_["importId"] for p_ in parents}:
                    ecarts.append([ws.title, k, "", "", "", "PARENT ABSENT"])
        except Exception as e:  # un onglet illisible ne doit pas masquer les autres
            ecarts.append([ws.title, "", "", "", str(e)[:200], "ERREUR DE VERIFICATION"])
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["onglet", "cle", "colonne", "attendu", "en_base", "ecart"]); w.writerows(ecarts)
    for e in ecarts[:60]:
        print(" | ".join(map(str, e)))
    bad = [e for e in ecarts if e[5] != "MEMBRE EN PLUS"]
    print(f"{checked} valeurs attendues contrôlées, {len(bad)} écart(s), {len(ecarts) - len(bad)} membre(s) en plus → {a.out}")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
