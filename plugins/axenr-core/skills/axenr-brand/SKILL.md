---
name: axenr-brand
description: >
  Identite visuelle officielle AxENR (charte mina studio, 01/2026) : logos
  fournis en SVG et PNG, palette de 5 couleurs, typographies Bruno Ace et
  Montserrat fournies, zone de protection et usages interdits du logo. A
  appliquer a tout support aux couleurs d'AxENR : presentation, deck,
  slides, PowerPoint, document client, proposition commerciale, page web,
  artifact, visuel, post, signature, en-tete. Declencheurs : « charte
  graphique », « aux couleurs d'AxENR », « logo AxENR », « couleurs AxENR »,
  « police AxENR », « fais une presentation », « fais un deck », « mets en
  forme ». PAS pour : les templates Word d'impression Axelor
  (axenr-template-expert), la charte d'un client (utiliser la sienne).
metadata:
  owner: axenr
  family: socle
---

# Charte graphique AxENR

Source : charte graphique AxENR par mina studio, 01/2026. Le detail complet
(couleurs en CMJN/HSB, zone de protection, interdits) est dans
`references/charte.md` : le lire avant de produire un support.

## Environnement d'execution

| Ou | Comportement |
|---|---|
| claude.ai et Cowork | Les fichiers du skill sont disponibles dans l'environnement d'execution : inserer les logos et polices depuis `assets/` dans le fichier produit (.pptx, .docx, .pdf, HTML). |
| Claude Code | Memes fichiers, sous le dossier du skill ; livrables ecrits dans `~/Downloads`. |
| Artifact web | Polices par Google Fonts (`Bruno Ace`, `Montserrat`) ; logo en SVG inline depuis `assets/logos/svg/`. |

## Fichiers fournis

| Fichier | Usage |
|---|---|
| `assets/logos/svg/logo-color-on-light.svg` | Logo principal sur fond clair (texte fonce, X en degrade vert) |
| `assets/logos/svg/logo-color-on-dark.svg` | Logo principal sur fond fonce (texte clair, X en degrade vert) |
| `assets/logos/svg/logo-mono-dark.svg` / `logo-mono-light.svg` | Logo monochrome, quand la couleur est impossible (impression N&B, filigrane) |
| `assets/logos/svg/icon-color.svg` | Icone (le X) : favicon, avatar, petit espace |
| `assets/logos/svg/icon-mono-dark.svg` / `icon-mono-light.svg` | Icone monochrome |
| `assets/logos/png/*@2x.png` | Memes declinaisons en PNG, pour les outils qui n'acceptent pas le SVG (PowerPoint, Word) |
| `assets/fonts/BrunoAce-Regular.ttf` | Titres et CTA |
| `assets/fonts/Montserrat-{Regular,Medium,SemiBold,Bold}.ttf` | Texte |

Ne jamais redessiner, vectoriser a nouveau ou recolorer un logo : toujours
utiliser un fichier de `assets/logos/`.

## L'essentiel a appliquer

### Couleurs

| Role | Hexa |
|---|---|
| Fond clair, texte sur fond fonce | `#F1F7F7` |
| Accent vif (le vert de l'energie) | `#01DF82` |
| Accent principal | `#2BC295` |
| Vert profond (fonds, bandeaux) | `#093226` |
| Quasi-noir (texte, fonds sombres) | `#041212` |

Aucune autre couleur sur un support AxENR, sauf les couleurs d'un graphique
de donnees (et dans ce cas, partir de ces 5 teintes).

### Typographies

- **Bruno Ace Regular** : titres principaux, CTA, elements a fort impact,
  **exclusivement en capitales**.
- **Montserrat** : baselines, corps de texte, citations, tout le reste.
- Si la police ne peut pas etre embarquee (outil sans police personnalisee) :
  Montserrat se remplace par une sans-serif neutre ; Bruno Ace ne se remplace
  pas, on met le titre en Montserrat Bold capitales et on le signale.

### Logo

- Logo principal des que l'espace le permet ; icone seule quand l'espace est
  tres limite.
- Zone de protection : aucun element a moins de **1/2 x** autour du logo,
  x etant la hauteur du X du logo.
- Choisir la version selon le fond : `color-on-light` sur `#F1F7F7` ou blanc,
  `color-on-dark` sur `#041212` ou `#093226`.

### Direction artistique

Green tech futuriste : formes geometriques nettes (lignes, grilles, segments,
blocs), degrades verts qui evoquent la circulation de l'energie et de la
donnee. Ecologie technologique et maitrisee, jamais d'imagerie ecologique
naive (feuilles, planetes, mains).

## Methode pour une presentation

1. Lire `references/charte.md`.
2. Choisir l'ambiance : sombre (fond `#041212` ou `#093226`, texte `#F1F7F7`)
   pour la couverture et les slides de rupture ; claire (fond `#F1F7F7`, texte
   `#041212`) pour les slides de contenu.
3. Couverture : logo principal, titre en Bruno Ace capitales, sous-titre en
   Montserrat.
4. Slides de contenu : titre en Bruno Ace capitales (court), texte en
   Montserrat, accents `#2BC295` / `#01DF82` pour les chiffres cles et les
   puces.
5. Icone ou logo discret en pied de slide, en respectant la zone de
   protection.
6. Avant de livrer, verifier la liste « Usages interdits » de
   `references/charte.md`.

## Regles

- Le nom s'ecrit **AxENR** dans le texte ; le logo, lui, est en minuscules
  (« axenr ») et ne se recopie jamais en texte.
- Les couleurs ne s'impriment pas fidelement (mention de la charte) : pour un
  support imprime, prevenir l'utilisateur et privilegier le logo monochrome
  si le rendu couleur compte.
- Un support pour un client reste aux couleurs d'AxENR ; le logo du client
  peut apparaitre, jamais a la place du logo AxENR ni en le recolorant.
