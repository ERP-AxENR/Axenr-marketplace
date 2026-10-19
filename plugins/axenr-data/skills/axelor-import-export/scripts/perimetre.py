"""Lecture du fichier de périmètre (JSON) partagé par tous les scripts du skill."""
import csv, json, os


def charger(chemin):
    p = json.load(open(chemin, encoding="utf-8"))
    p["_dir"] = os.path.dirname(os.path.abspath(chemin))
    for m in p["modeles"]:
        m.setdefault("recherche", f"self.{m['cle']} = :{m['cle']}")
        m.setdefault("non_ecrits", [])
        m.setdefault("lignes_exclues", [])
    return p


def contexte(p):
    """Paramètres nommés des domaines (listes de clés lues dans un CSV), ex. :tiers."""
    ctx = {}
    for nom, src in (p.get("contexte") or {}).items():
        f = os.path.join(p["_dir"], src["csv"])
        with open(f, encoding="utf-8") as h:
            ctx[nom] = [r[src["colonne"]] for r in csv.DictReader(h, delimiter=";")]
    return ctx


def modele(p, nom):
    return next(m for m in p["modeles"] if m["nom"] == nom)
