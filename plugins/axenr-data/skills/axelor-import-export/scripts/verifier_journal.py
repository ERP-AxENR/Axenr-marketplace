#!/usr/bin/env python3
"""Recherche dans le journal du premier démarrage les erreurs d'import du paquet data-init.

  verifier_journal.py <journal> --config data-init/input-config.xml --application <nom du module application>

Verdict OK seulement si : l'application a été installée pendant ce démarrage (« Installing package <nom> »),
chacun des fichiers du paquet a été lu une fois (« Importing <modèle> from <fichier> »), et aucune ligne
d'erreur n'apparaît pendant leur lecture (ERROR, « Unable to import », « Error while importing »,
exception, violation de contrainte). Les erreurs des autres modules sont listées à part, pour
information : elles ne viennent pas du paquet.
"""
import re, sys, os
import xml.etree.ElementTree as ET

ICI = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    sys.exit(__doc__)
for _opt in ("--config", "--application"):
    if _opt not in sys.argv or sys.argv.index(_opt) + 1 >= len(sys.argv):
        sys.exit(f"paramètre manquant : {_opt} <valeur>\n{__doc__}")
log = sys.argv[1]
cfg = sys.argv[sys.argv.index("--config") + 1]
APP = sys.argv[sys.argv.index("--application") + 1]
NS = {"d": "http://axelor.com/xml/ns/data-import"}
fichiers = [i.get("file") for i in ET.parse(cfg).getroot().findall("d:input", NS)]
ERR = re.compile(r"( ERROR |Unable to import|Error while importing|Error while accessing|Exception|Constraint violation)")
IMP = re.compile(r"Importing (\S+) from (\S+)$")
courant, vus, erreurs_paquet, autres, installe = None, {}, [], 0, False
for n, l in enumerate(open(log, encoding="utf-8", errors="replace"), 1):
    l = l.rstrip("\n")
    if f"Installing package {APP}..." in l:
        installe = True
    m = IMP.search(l)
    if m:
        courant = m.group(2) if m.group(2) in fichiers else None
        if courant:
            vus[courant] = vus.get(courant, 0) + 1
        continue
    horo = re.match(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+\s+(\w+)\s+\d+ --- \[[^\]]*\]\s+(\S+)", l)
    if re.search(r"Installing package |Loading package |Ready to serve", l) or \
            (horo and not re.search(r"(^|\.)(data|d)\.", horo.group(2))):
        courant = None  # une ligne d'un autre composant que le moteur d'import clôt la lecture du fichier
    if ERR.search(l):
        if courant or any(f in l for f in fichiers):
            erreurs_paquet.append(f"l.{n}: {l[:300]}")
        else:
            autres += 1
manquants = [f for f in fichiers if vus.get(f) != 1]
print(f"application {APP} installée pendant ce démarrage : {'oui' if installe else 'NON'}")
print(f"fichiers du paquet lus : {sum(1 for f in fichiers if vus.get(f) == 1)}/{len(fichiers)}"
      + (f"  (manquants ou répétés : {manquants})" if manquants else ""))
print(f"lignes d'erreur pendant la lecture du paquet : {len(erreurs_paquet)}")
for e in erreurs_paquet[:30]:
    print("   ", e)
print(f"(pour information) lignes d'erreur d'autres modules : {autres}")
ok = installe and not manquants and not erreurs_paquet
print("VERDICT :", "OK — 0 erreur d'import du paquet" if ok else "À TRAITER")
sys.exit(0 if ok else 1)
