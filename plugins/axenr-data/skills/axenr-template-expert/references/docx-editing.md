# Edition des .docx de template

> A charger avant de modifier un .docx de template par script ou a la main.

## 1. Regle d'or

Ne jamais ouvrir un .docx genere dans Word ou LibreOffice avant de l'importer dans Axelor. Word double le
`tblGrid`, supprime le texte `vanish`, passe `hRule="exact"` en `atLeast` et fragmente les expressions.
Verifier en dezippant le fichier, ou sur une copie convertie en PDF.

## 2. Une expression par run

Chaque expression `{...}` doit tenir dans un seul run XML (`<w:r><w:t>`). Word fragmente une balise lors d'une
correction d'orthographe ou d'une saisie en plusieurs fois.

Detection des fragments :

```python
import re
texts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', xml, re.S)
broken = [t for t in texts if t.count('{') != t.count('}')]
```

## 3. Chaine d'edition

```bash
mkdir work && cd work && unzip -q ../template.docx
# edition de word/document.xml avec lxml (ElementTree corrompt les namespaces)
rm -f ../template_v2.docx
zip -X ../template_v2.docx '[Content_Types].xml'
zip -Xrq ../template_v2.docx . -x '[Content_Types].xml'
```

- `[Content_Types].xml` en premier dans l'archive.
- Eviter les scripts de fusion de runs (`merge_runs.py`) qui introduisent des violations de preservation des
  espaces.
- Reutiliser les elements existants (cloner un paragraphe de titre, une ligne fusionnee, un dessin) plutot que
  d'en creer de toutes pieces.

## 4. Boucles imbriquees et numerotation

- Les boucles imbriquees dependent de la numerotation d'origine du document (`numId`). Une reconstruction
  complete (docx-js) ne rend que la derniere iteration : conserver la section de detail octet pour octet et ne
  modifier que le necessaire.
- En reordonnant des colonnes qui contiennent un ouvreur de boucle `{#var=...}`, ne permuter que les jetons de
  valeur : l'ouvreur reste avant toute reference a la variable.

## 5. Erreur « Cannot store template : InvalidPart »

Ce n'est pas une erreur de syntaxe de champ : Apache POI rejette l'integrite du paquet OPC/ZIP (part manquante,
type de contenu absent, archive mal reconstituee). Reprendre la chaine du paragraphe 3 sur le dernier .docx sain.

## 6. Validation avant livraison

Sur une copie, jamais sur le livrable :

```bash
soffice --headless --convert-to pdf --outdir /tmp/check copie.docx
pdftoppm -png -r 80 /tmp/check/copie.pdf /tmp/check/page
```

Controler le rendu des pages, puis livrer le .docx d'origine (non ouvert).
