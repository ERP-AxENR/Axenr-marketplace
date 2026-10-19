#!/usr/bin/env python3
"""Compare, valeur par valeur, l'état relu sur une base recréée à l'oracle de la recette.

  comparer_etat.py --oracle etat-recette/ --base etat-base/ --ecarts ecarts-attendus.json --out rapport/

Sortie : rapport/ecarts.csv (modèle ; clé ; champ ; recette ; base ; statut) et un résumé.
Statuts : ECART (bloquant), ATTENDU (décision documentée), MANQUANT / EN_TROP (ligne).
Règles : mêmes champs que lire_etat.py ; case vide de la recette (NULL) contre « false » = ATTENDU ;
case vide sur la base recréée = ECART ; champs non écrits par le paquet = ATTENDU.
Code de sortie 1 s'il reste un ECART, une ligne MANQUANT ou EN_TROP.
"""
import argparse, csv, json, os, sys


def lire(d, nom):
    p = os.path.join(d, f"{nom}.csv")
    if not os.path.exists(p):
        return None, []
    rows = list(csv.DictReader(open(p, encoding="utf-8"), delimiter=";"))
    return (list(rows[0].keys())[0] if rows else None), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oracle", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--ecarts", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    e = json.load(open(a.ecarts, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    lignes, resume, bloquant = [], [], False
    noms = sorted(f[:-4] for f in os.listdir(a.oracle) if f.endswith(".csv"))
    for nom in noms:
        cle, orows = lire(a.oracle, nom)
        _, brows = lire(a.base, nom)
        exclues = set(e["lignes_exclues"].get(nom, []))
        non_ecrits = set(e["non_ecrits"].get(nom, []))
        n2f = set(e["null_vers_false"].get(nom, {}))
        v2d = set(e.get("vide_vers_defaut", {}).get(nom, []))
        o = {r[cle]: r for r in orows}
        b = {r[cle]: r for r in brows} if brows else {}
        cpt = {"ECART": 0, "ATTENDU": 0, "valeurs": 0}
        for k in sorted(set(o) | set(b)):
            if k in exclues:
                lignes.append((nom, k, "*", "", "", "ATTENDU (ligne laissée à la plateforme)"))
                continue
            if k not in b:
                lignes.append((nom, k, "*", "présente", "absente", "MANQUANT")); bloquant = True; continue
            if k not in o:
                lignes.append((nom, k, "*", "absente", "présente", "EN_TROP")); bloquant = True; continue
            for c, vo in o[k].items():
                vb = b[k].get(c, "<colonne absente>")
                cpt["valeurs"] += 1
                if vb == "NULL":
                    lignes.append((nom, k, c, vo, vb, "ECART (case vide sur la base recréée)"))
                    cpt["ECART"] += 1; bloquant = True
                elif vo == vb:
                    continue
                elif c in non_ecrits:
                    lignes.append((nom, k, c, vo, vb, "ATTENDU (non écrit par le paquet)")); cpt["ATTENDU"] += 1
                elif c in v2d and vo == "" and vb == "0":
                    lignes.append((nom, k, c, vo, vb, "ATTENDU (vide sur la recette, valeur par défaut du modèle)"))
                    cpt["ATTENDU"] += 1
                elif c in n2f and vo == "NULL" and vb == "false":
                    cpt["ATTENDU"] += 1  # case vide de la recette, posée à false : attendu, non listé ligne à ligne
                else:
                    lignes.append((nom, k, c, vo, vb, "ECART")); cpt["ECART"] += 1; bloquant = True
        resume.append(f"{nom:18} recette {len(o):5}  base {len(b):5}  valeurs {cpt['valeurs']:6}  "
                      f"écarts {cpt['ECART']:4}  attendus {cpt['ATTENDU']:5}")
    with open(os.path.join(a.out, "ecarts.csv"), "w", encoding="utf-8", newline="") as h:
        w = csv.writer(h, delimiter=";")
        w.writerow(["modele", "cle", "champ", "recette", "base", "statut"])
        w.writerows(lignes)
    txt = "\n".join(resume) + f"\n\nVERDICT : {'ÉCARTS À TRAITER' if bloquant else '0 écart bloquant'}\n"
    open(os.path.join(a.out, "resume.txt"), "w", encoding="utf-8").write(txt)
    print(txt)
    sys.exit(1 if bloquant else 0)


if __name__ == "__main__":
    main()
