#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere le classeur de cadrage des droits a faire remplir par le client.

Le perimetre est passe en parametre : on ne demande jamais au client de remplir
une matrice sur tout l'ERP. Cadrer d'abord, produire la grille ensuite.

Usage
-----
    python3 generer_grille.py --client SYS --sortie ~/Downloads \
        --groupes "Direction,Logistique,Finances,Stock" \
        --roles "Achat User,Achat Manager,Stock User,Stock Manager,Facturation" \
        --objets objets.csv \
        --menus "Achats > Commandes fournisseurs,Stock > Mouvements de stock"

`objets.csv` : une ligne par objet du perimetre, format
    module;libelle;classe complete
Sans ce fichier, l'onglet Objets est cree vide avec ses seuls en-tetes.

Dependance : openpyxl.
"""
import argparse, csv, os, sys

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("openpyxl requis : python3 -m pip install openpyxl")

BLEU = PatternFill("solid", fgColor="1F3864")
SAISIE = PatternFill("solid", fgColor="FFF2CC")
GRIS = PatternFill("solid", fgColor="F2F2F2")
BLANC = Font(color="FFFFFF", bold=True)
T = Side(style="thin", color="BFBFBF")
BORD = Border(left=T, right=T, top=T, bottom=T)


def onglet(wb, nom, entetes, lignes, largeurs, saisie=(), retour=(), fige="A2"):
    ws = wb.create_sheet(nom)
    ws.append(entetes)
    for c in range(1, len(entetes) + 1):
        x = ws.cell(1, c)
        x.fill, x.font = BLEU, BLANC
        x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(c)].width = largeurs[c - 1]
    ws.row_dimensions[1].height = 34
    for i, ligne in enumerate(lignes, 2):
        ws.append(ligne)
        for c in range(1, len(entetes) + 1):
            x = ws.cell(i, c)
            x.border = BORD
            x.alignment = Alignment(vertical="top", wrap_text=(c in retour),
                                    horizontal="center" if c in saisie else "left")
            if c in saisie:
                x.fill = SAISIE
    ws.freeze_panes = fige
    return ws


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--client", required=True, help="Prefixe client, ex. SYS")
    p.add_argument("--sortie", default=".", help="Dossier de sortie")
    p.add_argument("--groupes", required=True, help="Postes separes par des virgules")
    p.add_argument("--roles", default="", help="Roles pressentis, separes par des virgules")
    p.add_argument("--objets", default="", help="CSV module;libelle;classe")
    p.add_argument("--menus", default="", help="Menus 'Module > Sous-menu', separes par des virgules")
    a = p.parse_args()

    groupes = [g.strip() for g in a.groupes.split(",") if g.strip()]
    roles = [r.strip() for r in a.roles.split(",") if r.strip()]
    menus = [m.strip() for m in a.menus.split(",") if m.strip()]
    objets = []
    if a.objets:
        with open(a.objets, encoding="utf-8") as f:
            objets = [l for l in csv.reader(f, delimiter=";") if l and l[0].strip()]

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # ---- 0. Mode d'emploi
    onglet(wb, "0. Mode d'emploi", ["Onglet", "A quoi il sert", "Ce que tu dois faire"], [
        ["1. Groupes", "Un groupe = un poste dans l'entreprise. Un utilisateur n'appartient qu'a UN seul groupe.",
         "Completer la description de chaque poste. Ajouter ou retirer des lignes si la liste ne correspond pas."],
        ["2. Roles", "Un role = la plus petite unite de droits reutilisable. Un meme role peut servir dans plusieurs groupes.",
         "Verifier la liste, la completer. Un role qui ne sert que dans un seul groupe est souvent un role de trop."],
        ["3. Groupes x Roles", "Quel poste recoit quel role.",
         "Poser un x a chaque intersection voulue. Remplir ligne par ligne, jamais par glissement de souris."],
        ["4. Droits objet", "Le coeur du sujet : qui peut faire quoi sur chaque donnee.",
         "Pour chaque objet et chaque role, ecrire les lettres du droit accorde. C'est l'onglet le plus important."],
        ["5. Menus", "Ce que chaque role voit dans la navigation.",
         "Poser un x. Attention : masquer un menu ne protege pas la donnee, cela ne remplace pas l'onglet 4."],
        ["", "", ""],
        ["CODIFICATION", "R = lire | W = modifier | C = creer | D = supprimer | E = exporter",
         "Exemple : RWC = lire, modifier, creer, sans supprimer ni exporter. Vide = aucun acces."],
        ["REGLE", "Un droit non accorde est un droit refuse.",
         "Un objet laisse vide pour un role sera inaccessible a ce role. Dans le doute, accorde la lecture."],
        ["A EVITER", "Donner la gestion des utilisateurs, des groupes, des roles ou des permissions a un profil metier.",
         "Reserve l'administration a un profil dedie."],
    ], [22, 62, 74], retour=(2, 3))

    # ---- 1. Groupes
    onglet(wb, "1. Groupes",
           [f"Code ({a.client}_...)", "Nom du poste", "Description", "Nb utilisateurs", "Commentaire"],
           [[f"{a.client.lower()}_{g.lower().replace(' ', '_')}", g, "", "", ""] for g in groupes],
           [24, 26, 56, 16, 40], saisie=(3, 4, 5), retour=(3, 5))

    # ---- 2. Roles
    onglet(wb, "2. Roles",
           ["Nom du role", "Perimetre fonctionnel", "Niveau (Lecture / Utilisateur / Manager)", "Commentaire"],
           [[r, "", "", ""] for r in roles] or [["", "", "", ""] for _ in range(10)],
           [30, 34, 34, 48], saisie=(2, 3, 4), retour=(4,))

    # ---- 3. Groupes x Roles
    ws = onglet(wb, "3. Groupes x Roles", ["Role"] + groupes + ["Commentaire"],
                [[r] + [""] * len(groupes) + [""] for r in roles] or
                [[""] + [""] * len(groupes) + [""] for _ in range(10)],
                [30] + [15] * len(groupes) + [48],
                saisie=tuple(range(2, len(groupes) + 2)), retour=(len(groupes) + 2,), fige="B2")
    ws.cell(len(ws["A"]) + 2, 1,
            "Un x a l'intersection. Un role peut etre partage entre plusieurs groupes : c'est le but.").font = Font(italic=True)

    # ---- 4. Droits objet
    entetes = ["Module", "Objet metier", "Nom technique"] + roles + ["Condition eventuelle"]
    lignes = [o[:3] + [""] * len(roles) + [""] for o in objets] or \
             [["", "", ""] + [""] * len(roles) + [""] for _ in range(15)]
    ws = onglet(wb, "4. Droits objet", entetes, lignes,
                [16, 30, 46] + [14] * len(roles) + [40],
                saisie=tuple(range(4, len(roles) + 4)), fige="D2")
    ws.cell(len(lignes) + 3, 1,
            "R lire | W modifier | C creer | D supprimer | E exporter. Vide = aucun acces, donc refus.").font = Font(italic=True)

    # ---- 5. Menus
    lignes = []
    for m in menus:
        if ">" in m:
            mod, sous = m.split(">", 1)
            lignes.append([mod.strip(), sous.strip()] + [""] * len(roles) + [""])
        else:
            lignes.append([m, ""] + [""] * len(roles) + [""])
    onglet(wb, "5. Menus", ["Module", "Sous-menu"] + roles + ["Commentaire"],
           lignes or [["", ""] + [""] * len(roles) + [""] for _ in range(15)],
           [18, 32] + [14] * len(roles) + [40],
           saisie=tuple(range(3, len(roles) + 3)), fige="C2")

    os.makedirs(a.sortie, exist_ok=True)
    chemin = os.path.join(a.sortie, f"grille_droits_{a.client}_a_remplir.xlsx")
    wb.save(chemin)
    print(f"Grille generee : {chemin}")
    print(f"  {len(groupes)} groupes, {len(roles)} roles, {len(objets)} objets, {len(menus)} menus")
    if not objets:
        print("  Onglet 4 vide : fournis --objets pour le pre-remplir. C'est l'onglet qui compte le plus.")


if __name__ == "__main__":
    main()
