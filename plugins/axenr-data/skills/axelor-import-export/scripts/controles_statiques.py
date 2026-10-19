#!/usr/bin/env python3
"""Contrôles statiques du paquet data-init, avant tout démarrage. Code de sortie 1 au premier bloquant.

  controles_statiques.py --perimetre perimetre.json --oracle etat/ --xsd data-import.xsd data-init/

Prérequis : `xmllint` (libxml2-utils) dans le PATH, et le `data-import.xsd` de la plateforme cible (présent dans
le jar ou les sources d'axelor-core), passé par --xsd ou par la variable AOS_DATA_IMPORT_XSD.
"""
import csv, json, os, re, shutil, subprocess, sys
import xml.etree.ElementTree as ET

import argparse
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import perimetre as P  # noqa: E402
ap = argparse.ArgumentParser()
ap.add_argument("--perimetre", required=True)
ap.add_argument("--oracle", required=True)
ap.add_argument("--xsd", default=os.environ.get("AOS_DATA_IMPORT_XSD"),
                help="data-import.xsd de la plateforme cible (jar ou sources d'axelor-core) ; "
                     "à défaut, variable d'environnement AOS_DATA_IMPORT_XSD")
ap.add_argument("paquet")
A = ap.parse_args()
if not A.xsd or not os.path.isfile(A.xsd):
    sys.exit("data-import.xsd introuvable : le passer par --xsd <fichier> ou par la variable AOS_DATA_IMPORT_XSD "
             "(fichier présent dans le jar ou les sources d'axelor-core de la plateforme cible)")
if not shutil.which("xmllint"):
    sys.exit("xmllint introuvable : installer libxml2-utils (il doit être dans le PATH)")
PER = P.charger(A.perimetre)
PAQUET, XSD = A.paquet, A.xsd
NS = {"d": "http://axelor.com/xml/ns/data-import"}

# Valeurs de lien présentes sur une base NEUVE avant le data-init de l'application (data-init des modules
# standard), déclarées dans le périmètre (« base_neuve ») après vérification sur une vraie base neuve.
BASE_NEUVE = {tuple(k.split("|")): set(v) for k, v in PER.get("base_neuve", {}).items()}
MOTS_DE_PASSE = {"password", "transientpassword", "forcepasswordchange", "passwordupdatedon"}

bloquants, notes = [], []
def ko(msg): bloquants.append(msg)

cfg = os.path.join(PAQUET, "input-config.xml")
r = subprocess.run(["xmllint", "--noout", "--schema", XSD, cfg], capture_output=True, text=True)
(notes if r.returncode == 0 else bloquants).append(f"XSD : {(r.stdout + r.stderr).strip()}")
brut = open(cfg, encoding="utf-8").read()
for motif, msg in [(r"\scall=\"", "call= présent"), (r"self\.id\s*=", "identifiant technique en dur (self.id =)"),
                   (r"<input[^>]*update=\"true\"", "update=\"true\" sur un input")]:
    if re.search(motif, brut):
        ko(msg)

connus = {}  # (type, champ) -> valeurs créées par les inputs précédents
racine = ET.parse(cfg).getroot()
for inp in racine.findall("d:input", NS):
    f, typ, search = inp.get("file"), inp.get("type"), inp.get("search")
    chemin = os.path.join(PAQUET, "input", f)
    octets = open(chemin, "rb").read()
    if octets.startswith(b"\xef\xbb\xbf"):
        ko(f"{f} : BOM UTF-8")
    try:
        octets.decode("utf-8")
    except UnicodeDecodeError:
        ko(f"{f} : pas en UTF-8")
    rows = list(csv.DictReader(open(chemin, encoding="utf-8", newline=""), delimiter=";"))
    cols = list(rows[0].keys()) if rows else []
    for c in cols:
        if c.lower() in MOTS_DE_PASSE:
            ko(f"{f} : colonne de mot de passe « {c} »")
    m = re.match(r"self\.(\w+) = :(\w+)$", search or "")
    if not m:
        ko(f"{f} : recherche d'input non conforme « {search} »")
        continue
    champ, col = m.groups()
    vals = [x[col] for x in rows]
    if len(vals) != len(set(vals)) or "" in vals:
        ko(f"{f} : clé « {col} » vide ou répétée")
    connus.setdefault((typ, champ), set()).update(vals)
    for c in cols:  # toute colonne écrite est une valeur de la fiche créée
        connus.setdefault((typ, c), set()).update(x[c] for x in rows)
    for b in inp.findall("d:bind", NS):
        c, ev, s = b.get("column"), b.get("eval"), b.get("search")
        if c and c not in cols:
            ko(f"{f} : colonne liée « {c} » absente du CSV")
        if ev and "== 'true'" in ev:
            bad = [x[c] for x in rows if x[c] not in ("true", "false")]
            if bad:
                ko(f"{f}.{c} : {len(bad)} booléen(s) ni true ni false")
        if s and c:
            tgt_field = re.match(r"self\.(\w+) = ", s).group(1)
            notes.append(f"{f}.{c} → {s}")
    for c in cols:
        for x in rows:
            v = x[c]
            if re.fullmatch(r"-?\d+,\d+", v):
                ko(f"{f}.{c} : décimal à virgule « {v} »")
                break

# Résolution des liens : chaque valeur est créée par le paquet ou présente sur une base neuve.
meta_dir = os.path.join(A.oracle, "_meta")
type_de = {}
for nomf in os.listdir(meta_dir):
    d = json.load(open(os.path.join(meta_dir, nomf), encoding="utf-8"))
    type_de[d["model"]] = d["fields"]
avant = {}
for inp in racine.findall("d:input", NS):
    f, typ = inp.get("file"), inp.get("type")
    rows = list(csv.DictReader(open(os.path.join(PAQUET, "input", f), encoding="utf-8"), delimiter=";"))
    for b in inp.findall("d:bind", NS):
        c, s, to = b.get("column"), b.get("search"), b.get("to")
        if not s:
            continue
        tgt = type_de[typ][to]["target"]
        champ = re.match(r"self\.(\w+) = ", s).group(1)
        const = re.match(r"self\.\w+ = '(.*)'$", s)
        attendues = {const.group(1)} if const else {m for x in rows for m in x[c].split("|") if m}
        # seules comptent les fiches créées par un input PRÉCÉDENT (un input ne voit ni les suivants, ni
        # les lignes qu'il crée lui-même) et celles d'une base neuve
        dispo = avant.get((tgt, champ), set()) | BASE_NEUVE.get((tgt, champ), set())
        manque = attendues - dispo
        if manque:
            plus_loin = manque & connus.get((tgt, champ), set())
            ko(f"{f}.{c} → {tgt}.{champ} : {len(manque)} valeur(s) introuvable(s) à ce stade, ex. {sorted(manque)[:3]}"
               + (" — créée(s) par un input SUIVANT : revoir l'ordre" if plus_loin else ""))
    for c in rows[0].keys() if rows else []:
        avant.setdefault((typ, c), set()).update(x[c] for x in rows)
    for champ_s in re.findall(r"self\.(\w+) = :(\w+)", inp.get("search") or ""):
        avant.setdefault((typ, champ_s[0]), set()).update(x[champ_s[1]] for x in rows)

print("\n".join("  ok  " + n for n in notes[:3]))
print(f"{len(notes)} contrôle(s) passés, {len(bloquants)} bloquant(s)")
for b in bloquants:
    print("  BLOQUANT", b)
sys.exit(1 if bloquants else 0)
