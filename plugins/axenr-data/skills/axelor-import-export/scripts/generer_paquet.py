#!/usr/bin/env python3
# Prudence droits : le générateur recopie des groupes et des comptes à l'état de l'oracle ; il ne conçoit
# aucun droit. Les rôles et menus ne sont écrits que si le périmètre ne les met pas dans « non_ecrits ».
"""Génère un paquet data-init (moteur classique csv-inputs) depuis l'oracle relu par lire_etat.py --meta.

  generer_paquet.py --perimetre perimetre.json --oracle etat/ --out data-init/ [--sonde]

Écrit data-init/input-config.xml, data-init/input/NN-<modèle>.csv et, hors sonde, ecarts-attendus.json à
côté du périmètre (lu par comparer_etat.py). Règles : aucun call= ; recherche par clé sur chaque input
(upsert, jamais update="true" sur un input) ; liens par clé métier de la cible avec update="true" (jamais de
fiche vide créée) et if= (cellule vide = pas de lien) ; booléens true/false explicites (NULL de l'oracle → false,
tracé) ; champ non booléen vide : non écrit ; UTF-8 sans BOM, « ; », décimal à point.
"""
import argparse, csv, json, os, sys
from xml.sax.saxutils import quoteattr

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import perimetre as P  # noqa: E402

CIBLES_IGNOREES = {"com.axelor.meta.db.MetaFile"}


def lire(oracle, nom):
    with open(os.path.join(oracle, f"{nom}.csv"), encoding="utf-8") as h:
        rows = list(csv.DictReader(h, delimiter=";"))
    meta = json.load(open(os.path.join(oracle, "_meta", f"{nom}.json"), encoding="utf-8"))
    return rows, meta


def fermeture_sonde(per, oracle):
    """Clés gardées par modèle : lignes choisies + tout ce qu'elles pointent (fermeture des liens) + enfants."""
    cles = per["cles_cibles"]
    sonde = per["sonde"]
    garder = {k: set(v) for k, v in sonde["garder"].items()}
    donnees = {m["nom"]: lire(oracle, m["nom"]) for m in per["modeles"]}
    par_type = {m["type"]: m for m in per["modeles"]}
    change = True
    while change:
        change = False
        for m in per["modeles"]:
            rows, meta = donnees[m["nom"]]
            g = garder.get(m["nom"], set())
            if "*" in g:
                continue
            for r in rows:
                if r[m["cle"]] not in g:
                    continue
                for c, v in r.items():
                    f = meta["fields"].get(c) or {}
                    tgt = f.get("target")
                    if not v or tgt not in par_type or c in m["non_ecrits"]:
                        continue
                    cible = par_type[tgt]
                    # la valeur de lien est la clé métier de la cible ; la retrouver dans la colonne clé ou autre
                    trows, _ = donnees[cible["nom"]]
                    champ = cles.get(tgt, "importId")
                    for membre in v.split("|"):
                        for tr in trows:
                            if tr.get(champ) == membre and tr[cible["cle"]] not in garder.setdefault(cible["nom"], set()):
                                garder[cible["nom"]].add(tr[cible["cle"]])
                                change = True
        for enfant, spec in (sonde.get("enfants") or {}).items():
            rows, _ = donnees[enfant]
            parents = garder.get(spec["parent"], set())
            for r in rows:
                if r[spec["champ"]] in parents and r[P.modele(per, enfant)["cle"]] not in garder.setdefault(enfant, set()):
                    garder[enfant].add(r[P.modele(per, enfant)["cle"]])
                    change = True
    return garder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perimetre", required=True)
    ap.add_argument("--oracle", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sonde", action="store_true")
    a = ap.parse_args()
    per = P.charger(a.perimetre)
    CLE = per["cles_cibles"]
    garder = fermeture_sonde(per, a.oracle) if a.sonde else None
    os.makedirs(os.path.join(a.out, "input"), exist_ok=True)
    for vieux in os.listdir(os.path.join(a.out, "input")):  # pas de fichier d'une génération précédente
        if vieux.endswith(".csv"):
            os.remove(os.path.join(a.out, "input", vieux))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<csv-inputs xmlns="http://axelor.com/xml/ns/data-import"',
           '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
           '  xsi:schemaLocation="http://axelor.com/xml/ns/data-import '
           'http://axelor.com/xml/ns/data-import/data-import_8.2.xsd">',
           '',
           f'  <!-- Paquet de recréation (application « {per["application"]} »). Généré par generer_paquet.py',
           '       depuis l\'oracle : ne pas modifier à la main, régénérer.',
           '       Aucun call= : la configuration de l\'app Base n\'existe pas encore au data-init. -->',
           '']
    ecarts = {"non_ecrits": {}, "lignes_exclues": {}, "null_vers_false": {}, "vide_vers_defaut": {}}
    ordre = per.get("ordre_paquet") or [m["nom"] for m in per["modeles"]]
    for i, nom in enumerate(ordre, 1):
        m = P.modele(per, nom)
        rows, meta = lire(a.oracle, nom)
        fields, model = meta["fields"], meta["model"]
        cle_ligne = m["cle"]
        ecarts["non_ecrits"][nom] = sorted(m["non_ecrits"])
        ecarts["lignes_exclues"][nom] = sorted(m["lignes_exclues"])
        rows = [r for r in rows if r[cle_ligne] not in set(m["lignes_exclues"])]
        if garder is not None and "*" not in garder.get(nom, set()):
            rows = [r for r in rows if r[cle_ligne] in garder.get(nom, set())]
        if not rows:
            print(f"{nom:18} 0 ligne : input omis")
            continue
        fichier = f"{i:02d}-{nom}.csv"
        colonnes, binds = [], []
        for c in rows[0].keys():
            if c in m["non_ecrits"]:
                continue
            f = fields[c]
            t = f["type"]
            vals = [r[c] for r in rows]
            if t == "BOOLEAN":
                nulls = sum(1 for v in vals if v == "NULL")
                if nulls:
                    ecarts["null_vers_false"].setdefault(nom, {})[c] = nulls
                colonnes.append((c, c, lambda v: "true" if v == "true" else "false"))
                binds.append(f'    <bind column="{c}" to="{c}" eval="{c} == \'true\'"/>')
                continue
            if t in ("INTEGER", "LONG", "DECIMAL") and any(v == "" for v in vals):
                ecarts["vide_vers_defaut"].setdefault(nom, []).append(c)
            if all(v == "" for v in vals):
                continue
            if t in ("MANY_TO_ONE", "ONE_TO_ONE"):
                tgt = f["target"]
                if tgt in CIBLES_IGNOREES:
                    continue
                if tgt not in CLE:
                    print(f"  ! {nom}.{c} → {tgt} : lien par importId (à vérifier sur base neuve)", file=sys.stderr)
                col = f"{c}_key"
                colonnes.append((col, c, lambda v: v))
                binds.append(f'    <bind column="{col}" to="{c}" search="self.{CLE.get(tgt, "importId")} = :{col}" '
                             f'update="true" if="{col}"/>')
            elif t == "MANY_TO_MANY":
                tgt = f["target"]
                if tgt not in CLE:
                    sys.exit(f"{nom}.{c} : cible {tgt} sans clé métier dans « cles_cibles » — à trancher")
                col = f"{c}_keys"
                membres = sorted({x for v in vals for x in v.split("|") if x})
                colonnes.append((col, c, lambda v: v))
                if max(len(v.split("|")) for v in vals if v) == 1:
                    binds.append(f'    <bind column="{col}" to="{c}" search="self.{CLE[tgt]} = :{col}" '
                                 f'update="true" if="{col}"/>')
                else:
                    # une recherche par membre : motif prouvé sur AOP 8.2 (une cellule délimitée liée
                    # directement à une collection lève une erreur de type)
                    if len(membres) > 10:
                        sys.exit(f"{nom}.{c} : {len(membres)} membres distincts — passe d'association dédiée à prévoir")
                    for mb in membres:
                        cond = f"{col} != null &amp;&amp; ('|' + {col} + '|').contains('|{mb}|')"
                        binds.append(f'    <bind column="{col}" to="{c}" search="self.{CLE[tgt]} = \'{mb}\'" '
                                     f'update="true" if="{cond}"/>')
            else:
                colonnes.append((c, c, lambda v: v))
                binds.append(f'    <bind column="{c}" to="{c}" if="{c}"/>')
        with open(os.path.join(a.out, "input", fichier), "w", encoding="utf-8", newline="") as h:
            w = csv.writer(h, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
            w.writerow([col for col, _, _ in colonnes])
            for r in rows:
                w.writerow([conv(r[src]) for col, src, conv in colonnes])
        xml += [f'  <!-- {nom} : {len(rows)} ligne(s) -->',
                f'  <input file="{fichier}" separator=";" type="{model}"',
                f'    search={quoteattr(m["recherche"])}>'] + binds + ['  </input>', '']
        print(f"{fichier:28} {len(rows):5} lignes {len(colonnes):4} colonnes")
    xml.append('</csv-inputs>')
    with open(os.path.join(a.out, "input-config.xml"), "w", encoding="utf-8", newline="\n") as h:
        h.write("\n".join(xml) + "\n")
    if not a.sonde:
        json.dump(ecarts, open(os.path.join(per["_dir"], "ecarts-attendus.json"), "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
    print("case vide → false :", ecarts["null_vers_false"])


if __name__ == "__main__":
    main()
