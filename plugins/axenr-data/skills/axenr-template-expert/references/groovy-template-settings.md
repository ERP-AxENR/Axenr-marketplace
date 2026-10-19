# Groovy et parametrage TemplateSettingsLine

> A charger des qu'une ligne TemplateSettingsLine doit etre creee ou corrigee, ou qu'un champ ressort vide.
> Valable pour XDocReport et Carbone : le Groovy s'execute cote serveur avant le rendu.

## 1. Principe

Mise en page dans le Word, logique dans TemplateSettingsLine. Tout calcul, fallback, filtre ou conditionnel
complexe se fait en Groovy dans la colonne `field` ; le Word n'affiche que `{d.<nameInTemplate>}`.

Frontiere a cadrer par ecrit avec le client :

| Element | Responsable |
|---|---|
| Mise en page | Template Word |
| Champ calcule, filtre, conditionnel | TemplateSettingsLine (Groovy) |
| Existence et type d'une question | Gamme d'intervention (client) |
| Donnees de site | Saisie dans l'ERP (client) |

Un rapport ne peut pas afficher ce qui n'a jamais ete saisi.

## 2. Chaines de 3 relations ou plus

`{d.a.b.c.d}` echoue silencieusement au 3e niveau, meme avec un parametrage correct. Creer un champ au niveau
racine :

```
nameInTemplate      | field
clientCityFullName  | clientPartner?.mainAddress?.city?.fullName ?: ''
```

## 3. metaField (Sous-champ) et import Excel

- L'import Excel de TemplateSettingsLine laisse `metaField` vide sur les lignes relationnelles.
- Selon l'instance, c'est bloquant (echec silencieux a l'execution) ou anodin (des lignes sans metaField
  fonctionnent en production). Verifier sur l'instance concernee ; en cas d'echec, re-selectionner la relation
  via le Constructeur d'expression de l'UI.
- L'import Excel est additif pour les champs relationnels et les collections : il ne remplace pas les
  associations existantes.
- Un champ calcule (metaField vide) s'affiche en `{$var.field}` mais ne peut pas servir de filtre de liste
  `[field=valeur]`. Filtrer exige un vrai metaField, ou une sous-collection pre-filtree en Groovy avec un
  sous-modele lie via le Constructeur d'expression (pas par import Excel).

## 4. Collections construites en Groovy

- Une collection Groovy sert de source de boucle si le sous-modele (`templateSettingsToUse`) est renseigne.
- Preferer une collection d'entites. Une collection de `Map` peut fonctionner pour du texte sur certaines
  instances et ne pas materialiser ses sous-champs sur d'autres : tester.
- `*.` suivi de `.flatten()` renvoie une liste vide sans erreur (la boucle disparait). Utiliser :

```groovy
(liste ?: []).collectMany { r -> (r.sousListe ?: []).findAll { it.pictureAnswer != null } }
```

## 5. Garde-fous obligatoires

- Tests explicites : `findAll { it.pictureAnswer != null }`, jamais `findAll { it?.pictureAnswer }`
  (la verite Groovy d'un proxy Hibernate est trompeuse).
- `(liste ?: [])` avant toute iteration.
- `?: 0` dans les comparateurs de tri : `sort { it.orderSeq ?: 0 }`.
- `?: ''` sur toute concatenation ; points-virgules entre instructions.
- Expressions en `switch` : chaque branche null-safe, pas seulement l'appel de collection
  (`.collect{}.join()` expose `.join` a une NPE). Symptome : erreur d'impression sur certaines interventions
  seulement (echec dependant des donnees).

## 6. Statuts et selections

- Conformite : propriete ORM anglaise `nonConforming` (colonne `non_conforming`).

```groovy
// non conforme
listAnswer?.nonConforming == true
// conforme
listAnswer != null && listAnswer.nonConforming != true
```

- Jamais `nonConformite` (renvoie null et inverse la logique).
- Jamais de filtre par `contains` sur un libelle : « Non conforme » contient « Conforme », le statut est compte
  deux fois.
- Les libelles de selection sont stockes en anglais : `com.axelor.i18n.I18n.get(libelle)` pour le francais
  (idem pour `MetaSelectItem.title`).
- `partnerTypeSelect` stocke une cle numerique : `ifEQ('1')` / `ifNE('1')` (Societe / Particulier), jamais
  `ifEQ('Societe')`.

## 7. Transformations courantes

| Besoin | Groovy dans `field` |
|---|---|
| Fallback (SIRET sinon SIREN) | `clientPartner?.registrationCode ?: clientPartner?.siren ?: ''` |
| Nettoyer le HTML d'une description | `description?.replaceAll('<[^>]+>', ' ') ?: ''` |
| Image MetaFile | `__tools__.toBase64Uri(champMetaFile)` (data URI ou null) |
| Nombre formate | `new java.text.DecimalFormat('#,##0.00').format(montant ?: 0)` |
| Multi-lignes dans une cellule | `liste.collect { ... }.join('\n')` + `:convCRLF()` cote Word ; prefixer `'\n'` seulement si non vide |
| Libelle traduit | `com.axelor.i18n.I18n.get(champ ?: '')` |

- Images : `MetaFiles.getPath(...)` et `java.io.File(...)` sont rejetes par le sandbox Groovy ; ne pas declarer
  ces champs en M2O.
- Le fallback se met dans la colonne `field`, pas dans le Word.

## 8. Compteur global (photos numerotees)

`questionSeq` repart a zero a chaque gamme. Construire la numerotation en Groovy : aplatir la liste
(`collectMany`), puis `indexOf(id) + 1` pour chaque element.

## 9. Tri

Un tri sur un champ partage par plusieurs lignes (`sort { it.priority }`) est inefficace : trier sur une cle
discriminante (par exemple `sort { it.product?.name }`).

## 10. Mapping usuel d'un rapport d'intervention

`rangeName` -> `name`, `rangeSeq` / `questionSeq` -> `orderSeq`, `answer` = `switch` Groovy sur
`answerTypeSelect` (texte, case a cocher, liste, mesure + unite, date `dd/MM/yyyy`, suivi avance).
