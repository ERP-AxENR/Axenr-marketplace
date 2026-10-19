# Carbone.io dans Axelor / AxENR

> A charger des que le moteur identifie est Carbone (voir SKILL.md, regle n°1).
> Les constats ci-dessous ont ete observes sur des instances client reelles. Le comportement de Carbone
> depend de sa version et de l'instance : verifier chaque regle par un rendu avant de la generaliser.

## 1. Identifier le moteur avant d'ecrire une expression

Le log de previsualisation d'Axelor donne le moteur reel :

```
Preview successfully generated in Xms = Carbone (Yms) + conversion (Zms)
```

- Mention `Carbone (...)` : moteur Carbone.io, appliquer ce fichier.
- Pas de mention Carbone : moteur XDocReport, appliquer le catalogue (`catalog.md`).

Erreur la plus couteuse deja vecue : six versions d'un template construites en supposant XDocReport alors que
l'instance rendait sous Carbone. Une documentation interne intitulee « Pattern XDocReport » peut decrire en
realite du Carbone : se fier au log, pas au titre.

Ne jamais transposer une regle d'une instance a une autre sans verification : deux clients peuvent avoir des
moteurs, des versions de Carbone et des parametrages differents.

## 2. Syntaxe Carbone utile

| Besoin | Syntaxe |
|---|---|
| Champ | `{d.champ}` |
| Contexte | `{c.now}` |
| Boucle | `{d.liste[i].champ}` sur la ligne modele, `{d.liste[i+1].champ}` sur la ligne suivante |
| Boucle triee | `{d.liste[rangeSeq, i].champ}` / `{d.liste[rangeSeq+1, i+1].champ}` |
| Filtre de boucle | `{d.liste[i, statut=1].champ}` (meme filtre sur toutes les cellules de la ligne) |
| Alias | `{#nom = d.liste[i]}` puis `{$nom.champ}` (noms d'alias totalement distincts) |
| Boucles imbriquees | alias nommes par niveau : `#question` / `#question2`, `#nc` / `#nc2` |
| Condition d'affichage | `{d.flag:ifEQ(true):showBegin}` ... `{d.flag:showEnd}` |
| Masquer si vide | `{d.champ:ifEM:hideBegin}` ... `{d.champ:hideEnd}` |
| Retours a la ligne | `{d.champ:convCRLF()}` |
| Tronquer | `{d.champ:substr(0,45)}` |

La documentation officielle carbone.io decrit la derniere version (v5). La version embarquee dans Axelor est
souvent plus ancienne : un formateur documente peut etre absent.

## 3. Formateurs : etat observe

| Formateur | Constat | Consigne |
|---|---|---|
| `:convCRLF()` | Fonctionne | Multi-lignes dans une cellule |
| `:ifEM:hideBegin/hideEnd` | Fonctionne sur certaines instances, inoperant sur d'autres | Tester ; sinon champ Groovy booleen + showBegin |
| `:ifEQ(true):showBegin/showEnd` sur un booleen Groovy | Fonctionne | Patron recommande |
| Plusieurs paires showBegin dans un document | Plusieurs paires validees sur une instance ; seconde paire neutralisee sur une autre | Limiter le nombre de paires ; deporter la logique en Groovy |
| Filtres multi-conditions `[a=x, b=y, i]` | Erratiques sur certaines instances | Un seul booleen Groovy combine (`?: false`) |
| `:drop(row)` | Supprime toutes les lignes | Ne pas utiliser |
| `bindColor` | Absent avant Carbone v4 | Ne pas utiliser sans verifier la version |

Principe : chaque paire showBegin retiree du Word est un risque en moins. Calculer en Groovy dans
TemplateSettingsLine (voir `groovy-template-settings.md`), afficher dans le Word.

## 4. Images dynamiques

1. Ne jamais fabriquer un `<w:drawing>` par script : Carbone l'ignore sans erreur. Toujours cloner un dessin
   insere par Word, idealement depuis un template qui fonctionne deja.
2. Structure du dessin :
   - balise placee uniquement dans `wp:docPr/@descr` (texte alternatif) ;
   - `pic:cNvPr` : `descr` et `title` vides ;
   - ancrage `wp:inline` (une image flottante ne se repete pas dans une boucle) ;
   - `noChangeAspect="1"` ;
   - media JPEG coherent avec son extension, pas de `a:srcRect` (recadrage) ;
   - plusieurs dessins peuvent partager le meme rId.
3. Jamais d'alias dans une balise d'image : `{$photo.x}` est une substitution de texte qui n'atteint pas les
   attributs XML. Utiliser le chemin complet `{d.liste[i].champ}`.
4. La valeur doit etre une data URI produite en Groovy : `__tools__.toBase64Uri(champMetaFile)`.
5. Afficher une base64 brute en texte fait tomber le rendu (timeout passerelle `SyntaxError ... upstream`).
   Pour diagnostiquer, tronquer : `{d.champ:substr(0,45)}`.

## 5. Geometrie des tableaux et des boucles

- Une boucle fige la geometrie de la ligne repetee. showBegin/hideBegin suppriment du texte, jamais une
  cellule ni un `gridSpan`.
- `[i]` et `[i+1]` sur des lignes differentes, sinon l'iteration se fait au niveau de la cellule.
- Sous-ligne fusionnee : deux lignes par iteration entre `[i]` et `[i+1]` (ligne A en 3 colonnes, ligne B
  avec une cellule `gridSpan`, bordure haute nulle, retrait).
- Ne pas repartir des sous-donnees paralleles dans des colonnes distinctes (desalignement) : regrouper libelle,
  valeur et commentaire dans une seule cellule (`join('\n')` + `:convCRLF()`).
- Tableau dedie par sous-ensemble : en-tete + ligne modele + ligne marker `[i+1]` invisible :
  `gridSpan` sur toute la largeur, `w:trHeight w:val="1" w:hRule="exact"`, texte en `w:vanish`, police 1 pt.
- Repeter un filtre `[filtre, i]` different sur chaque cellule fait iterer chaque cellule independamment :
  meme filtre partout.
- Alias a prefixes communs mal resolus : noms d'alias totalement distincts.

## 6. Generation des .docx Carbone complexes

- Generer le document par script (Node.js `docx` ou edition XML avec `lxml`), logos et images inseres par le
  script, jamais ajoutes dans Word apres coup.
- Ne jamais ouvrir le .docx genere dans Word ou LibreOffice avant import : Word double le `tblGrid`, supprime
  le texte `vanish`, passe `hRule="exact"` en `atLeast` et fragmente les expressions.
- Detail de l'edition XML : `docx-editing.md`.

## 7. Rapport d'intervention : choix de conception valides

- Structure : page de garde, client et intervention, installations, detail par gamme avec sous-lignes
  conditionnelles, non-conformites, conclusion du technicien, annexe photo numerotee sur page dediee.
- Referentiels cites : NF EN 62446-1, IEC 60364-6, guide O&M SolarPower Europe.
- Rouge sur la valeur non conforme seulement ; colonne Reponse centree, Question et Commentaire a gauche.
- Photos en annexe ; numeroter les photos, pas les questions (compteur global en Groovy, voir
  `groovy-template-settings.md`).
