# Bareme Pricing Catalog

> Knowledge base versionnee pour l'agent `axenr-bareme-expert`. Issue d'une integration reelle de bout en bout : BPU de maintenance photovoltaique Emeraude Solaire, 22 articles, 26 baremes, 178 lignes de grille, 181 cas de recette conformes.

---

## 1. LE MOTEUR PRICING - ARCHITECTURE REELLE

Trois entites, dans `axelor-base` :

| Entite | Role |
|---|---|
| `Pricing` | Le bareme. Porte le scope (societe, modele, dates, type) et la formule de ciblage |
| `PricingRule` | Une regle, reutilisable par plusieurs baremes. Classification ou resultat |
| `PricingLine` | Une ligne de la grille. Porte les valeurs de classification et les resultats |

### 1.1 Comment le moteur choisit un bareme

Verifie dans `PricingServiceImpl.pricingFetchFilter()`. Le filtre SQL est **exclusivement** :

```
startDate <= aujourd'hui
AND (endDate > aujourd'hui OR endDate IS NULL)
AND company        = <societe du document>
AND concernedModel = <modele, ex SaleOrderLine>
AND typeSelect     = <type, ex 'Pricing'>
AND (archived = false OR archived IS NULL)
```

Puis `appendFormulaFilter()` evalue le champ `formula` en Groovy sur le contexte du modele.

**Le champ `product` du bareme n'est PAS un critere de selection.** Il n'est lu que par
`PricingGroupServiceImpl.computeFormulaField()`, un assistant IHM qui *genere* la formule :

```groovy
product?.id == <id> || product?.parentProduct?.id == <id>
// + " || product?.productCategory?.id == <id>" si une categorie est choisie
```

Consequence pratique : en script SQL, il faut ecrire la formule soi-meme avec l'id reel
de l'article dans la base cible. Renseigner `product` sans formule ne cible rien.

**Champ `formula` vide = bareme jamais selectionne**, sans erreur. C'est la premiere chose a
verifier quand un bareme cree a la main (copie d'un autre, saisie directe en base) ne
s'applique pas : le log de calcul (`pricingScaleLogs`, voir 11.1) indique alors qu'aucun bareme
n'a ete trouve, et non que les classifications ne matchent pas.

### 1.2 Ordre d'evaluation

1. Selection des baremes candidats (filtre ci-dessus + formule)
2. Pour chaque bareme : filtrage des `PricingLine` par les classifications 1 a 4, dans l'ordre
3. La premiere ligne survivante alimente les regles de resultat
4. Chaque regle de resultat ecrit dans son `fieldToPopulate`

---

## 2. CONTRAINTES DURES

A connaitre avant de concevoir. Toutes verifiees dans le code AOS 8.5.

| Contrainte | Detail | Impact conception |
|---|---|---|
| **4 classifications max** | `class1PricingRule` a `class4PricingRule` | Au-dela, il faut splitter en plusieurs baremes ou porter un axe par l'article |
| **4 resultats max** | `result1PricingRule` a `result4PricingRule` | Suffisant en pratique (prix, libelle, quantite, remise) |
| **Operateurs `<` `=` `>`** | `OPERATOR_LESS_THAN=-1`, `EQUAL=0`, `GREATER_THAN=1` | **Pas de `<=` ni `>=`**. Voir 2.1 |
| **`resultParam1..4` decimaux** | `precision 20, scale 10` | Une valeur texte ne peut pas venir de la ligne. Voir 2.2 |
| **`classificationParam1..4`** | texte | Plus `classificationIntParam` et `classificationDecParam`, un jeu par position |
| **`Pricing.company`** | mono-societe | Des tarifs par entite = autant de baremes |
| **`startDate` / `endDate`** | + `historizedBy`, `currentPricing` | Versionnement tarifaire natif : ne jamais ecraser une grille, en ouvrir une nouvelle |

### 2.1 Semantique des bornes numeriques - LE point a maitriser

Verifie dans `PricingComputer.checkRuleOperator()` et `sortPricingLineOnField()` :

```java
// operateur "<"
((BigDecimal) param).compareTo((BigDecimal) value) < 0
// param = valeur de la LIGNE, value = resultat de la FORMULE
// et les lignes sont triees en ordre DECROISSANT
```

Donc, avec l'operateur `<` : **la premiere ligne dont la borne est strictement inferieure
a la valeur calculee l'emporte**. Chaque ligne porte la **borne inferieure exclue** de son palier :

```
palier = ] borne ; borne suivante ]
```

Exemple pour une grille "0 a 9 / 10 a 18 / 19 a 36 kWc" :

| Ligne a saisir | Palier couvert | Verification |
|---|---|---|
| `0` | ]0 ; 9] | 9 kWc -> ligne 0 (car 9 < 9 est faux) |
| `9` | ]9 ; 18] | 9,5 kWc -> ligne 9 |
| `18` | ]18 ; 36] | 20 kWc -> ligne 18 |

**Une valeur exactement egale a une borne tombe dans le palier inferieur.** C'est coherent,
mais cela doit etre valide avec le client quand la grille est exprimee en entiers.

Deux consequences a verifier systematiquement :
- **valeur nulle ou zero** : aucune ligne ne matche si la plus petite borne vaut 0. Le bareme
  reste muet. C'est souvent le comportement voulu, mais il faut le decider.
- **debordement haut** : au-dela de la derniere borne, la derniere ligne s'applique
  **silencieusement**. Prevoir une ligne de garde ou assumer le plafond.

### 2.2 Une regle de resultat peut ecrire du TEXTE

Verifie dans `PricingComputer.computeResultFormulaAndApply()` :

```java
Object result = scriptHelper.eval(resultPricingRule.getFormula());
if (typeName.equals("BigDecimal")) { result = setScale(result, scale); }
Mapper.of(...).set(model, fieldToPopulate.getName(), result);
```

Le resultat est applique **tel quel**, le `setScale` ne s'appliquant qu'aux champs `BigDecimal`.
Une regle de resultat peut donc cibler un champ `String` (`productName`, `description`) a condition
que **la valeur vienne de la formule Groovy**, jamais de `pricingLine.resultParamN` qui est decimal.

C'est le mecanisme du pattern "libelle ecrit par le bareme" (voir 4.5).

---

## 3. LA REGLE DE DECISION : ARTICLE OU BAREME ?

La question qui revient a chaque projet : faut-il N articles, ou un article et un axe de bareme ?

> **On ne cree jamais d'article sur un axe qui decrit le CLIENT ou son CONTRAT.
> On peut en creer un sur un axe qui decrit l'ACTE.**

- Formule contractuelle, segment de clientele, categorie de tiers -> **jamais de split**
- Puissance, distance, surface, hauteur d'acces, technique employee, unite de vente -> **split recevable**

**Exception unique et fondee** : quand la prestation *est* le contrat. Un forfait d'abonnement
n'est pas un acte tarife par la formule, il **est** la formule - c'est l'objet meme du choix
commercial. La, N articles se justifient, et ils coexistent legitimement sur un devis comparatif.

### 3.1 Les trois tests, dans l'ordre

1. **Objet contractuel** - le client achete-t-il cette ligne *pour souscrire*, ou la
   consomme-t-il *parce qu'il a souscrit* ? Souscription -> N articles. Consommation -> article unique.
2. **Coexistence sur une meme piece** - deux variantes peuvent-elles apparaitre legitimement
   sur le meme devis ? Si non, la duplication est de la redondance.
3. **Unite de vente et ressource** - unites differentes (forfait / m2 / heure) ou moyens
   reellement differents (nacelle 12 m vs 21 m : autre engin, autre CACES, autre cout) -> articles distincts.

### 3.2 Ce que ce critere evite

Sur un BPU de 36 prestations croisant 3 formules et 2 segments, le croisement integral donne
**216 articles**. Le critere ci-dessus en produit **22**. Un article est une ligne de catalogue
que le commercial vend et que le client reconnait ; un bareme est une grille de prix. Dupliquer
un article sans creer une nouvelle chose vendable, c'est du tarif deguise en catalogue - et a la
premiere revision tarifaire, il faut rouvrir N fiches article au lieu d'une ligne de grille.

### 3.3 Le faux dilemme "devis autonome vs devis depuis contrat"

Objection classique : un article unique pilote par le contrat sert le cas "devis genere depuis
une intervention", mais empeche de presenter plusieurs formules au choix dans un devis autonome.

C'est un faux dilemme. Un client ne compare pas les formules **ligne par ligne** : il compare des
**forfaits**, et la grille des actes hors forfait est une **annexe**, pas des lignes de devis.
La solution est un **champ "formule applicable" sur l'entete du document**, alimente en cascade :

1. contrat rattache -> formule du contrat
2. sinon -> saisie de l'utilisateur
3. sinon -> tarif par defaut, **avec signalement visible**

Le bareme lit ce champ unique. Basculer le champ retarife tout le document ; la comparaison se
fait en dupliquant le **document**, pas les **articles**.

---

## 4. PATTERNS DE PARAMETRAGE

### 4.1 Prix par segment de clientele

Le plus simple. Une classification texte, une ligne par valeur.

```groovy
// Regle CLASSIFICATION, type texte, operateur =
saleOrder?.clientPartner?.partnerCategory?.code
```

Lignes : `classification_param1 = 'AGRI'` / `'ICT'`, `result_param1 = <prix>`.

### 4.2 Palier numerique (puissance, surface, nombre d'equipements)

```groovy
// Regle CLASSIFICATION, type DECIMAL, operateur <
// IMPERATIF : retourner un BigDecimal, jamais "?: 0" (voir piege 5.2)
def v = saleOrder?.estimatedPower
return v != null ? new BigDecimal(v.toString()) : BigDecimal.ZERO
```

Lignes : `classification_dec_param1 = <borne inferieure exclue>`.

### 4.3 Formule contractuelle en cascade

Le pattern central des grilles "sous contrat / hors contrat".

```groovy
import groovy.json.JsonSlurper
// 1) champ saisi sur l'entete du document (prioritaire)
def f = null
def raw = saleOrder?.attrs
if (raw) {
  try { f = new JsonSlurper().parseText(raw.toString())?.formuleTarifaire } catch (e) { f = null }
}
if (f == 'EXPERT')    return 'EXP'
if (f == 'ESSENTIEL') return 'ESS'
if (f == 'PONCTUEL')  return 'HC'

// 2) repli : contrat rattache
def c = saleOrder?.contract
if (c != null) {
  def n = (c.name ?: '').toUpperCase()
  if (n.contains('EXPERT'))    return 'EXP'
  if (n.contains('ESSENTIEL')) return 'ESS'
}

// 3) defaut
return 'HC'
```

**Regle partagee** : une seule regle lue par tous les baremes. Le jour ou un champ dedie apparait
sur `Contract`, une seule formule est a modifier et tous les baremes suivent.

**Point de vigilance a signaler au client** : deduire la formule d'un libelle est fragile - un
renommage casse la tarification en silence. C'est acceptable en transitoire, jamais en cible.

### 4.4 Prix forfaitaire calcule

Quand le BPU exprime un tarif unitaire (au m2, au module) mais que la ligne doit porter une
quantite de 1 et un montant total.

```groovy
import groovy.json.JsonSlurper
def lire = { o ->
  if (!o) return null
  try { return new JsonSlurper().parseText(o.toString())?.surfaceModulesM2 } catch (e) { return null }
}
def s = lire(saleOrder?.attrs)
if (s == null) s = lire(saleOrder?.opportunity?.attrs)   // cascade amont
if (s == null) s = 0
def tarif = pricingLine?.resultParam1 ?: 0
return new BigDecimal(tarif.toString()) * new BigDecimal(s.toString())
```

La ligne de bareme stocke le **tarif unitaire**, la regle produit le **montant**.

**A dire au client** : le prix unitaire affiche n'est plus le tarif au m2 mais le montant total.
Le detail unitaire doit alors vivre dans le libelle (pattern suivant), sinon il disparait du devis.

### 4.5 Libelle ecrit par le bareme, et temoin d'execution

```groovy
def surf  = new BigDecimal(s.toString()).setScale(0, java.math.RoundingMode.HALF_UP)
def tarif = new BigDecimal((pricingLine?.resultParam1 ?: 0).toString())
              .setScale(2, java.math.RoundingMode.HALF_UP)
return (product?.name ?: 'Prestation') + ' - Surface : ' + surf + ' m2 x ' + tarif + ' EUR/m2'
```

Cible : `fieldToPopulate` = `SaleOrderLine.productName`, `fieldTypeSelect` = texte (0).

Usage detourne mais tres efficace : **faire toujours reecrire le libelle par le bareme**, meme
quand ce n'est pas necessaire. Le libelle devient le temoin d'execution - s'il n'a pas ete
reecrit, le bareme n'a pas tourne, et un controleur le voit sans ouvrir les logs.

### 4.6 Valeur "incluse au contrat"

Le BPU indique "Inclus" : la prestation est consommee sans etre facturee.

- **Enregistrer 0** dans `result_param1` (les `resultParam` sont decimaux, "Inclus" n'est pas stockable)
- **Conserver le cout de revient sur la ligne**, sinon l'analyse de marge est detruite : la
  prestation offerte disparait des couts alors qu'elle en genere
- **Faire ecrire un libelle explicite** ("... - inclus au contrat Expert") pour que le client
  percoive la valeur de ce qu'il consomme sans payer
- Piloter la rentabilite **au niveau du contrat**, pas de la ligne : en maintenance, on gagne ou
  on perd de l'argent sur un contrat annuel, pas sur un deplacement

### 4.7 Valeur "sur devis"

Le BPU indique "SUR DEVIS" : le montant doit etre chiffre manuellement.

**Ne creer aucune ligne de bareme pour ce cas.** Le bareme ne matche pas, le prix reste a la
valeur catalogue (0 si l'article est bien configure) et force la saisie.

A ne pas faire : enregistrer 0 comme un prix. Une ligne a 0 EUR passe la validation et part en
facture - typiquement sur une intervention d'urgence, ou le montant est le plus eleve et
l'urgence pousse a valider vite.

### 4.8 Chainer des baremes avec `linkedPricing`

`linkedPricing` sert uniquement a **chainer** des baremes : le bareme lie s'execute apres le
premier, sur le meme enregistrement. Usage type : une chaine "cout de revient avec alea ->
prix unitaire -> marge", ou chaque maillon lit le resultat du precedent sur la ligne.

- Un maillon doit lire le champ ecrit par le maillon precedent, jamais recalculer sa source :
  sinon les deux calculs divergent au premier changement de formule.
- Un bareme lie n'est pas un critere de selection : il ne s'execute que si le premier bareme
  a ete selectionne (formule, societe, modele, type).

### 4.9 Courbe de prix continue plutot que paliers

Quand le prix suit une grandeur continue (surface, longueur, puissance) avec un plancher,
preferer une formule a une grille de paliers :

```groovy
// Regle RESULTAT, champ price
def PRIX_PLANCHER = new BigDecimal('450')
def COEF_M2       = new BigDecimal('3.20')
def s = new BigDecimal((attrs?.surfaceM2 ?: 0).toString())
[PRIX_PLANCHER, s * COEF_M2].max()
```

Une grille de paliers cree des sauts de prix que le client ne comprend pas (1 m2 de plus =
+200 EUR). Ne garder les paliers que si **le metier veut une discontinuite** (changement
d'engin, de categorie d'habilitation, de forfait).

### 4.10 Garde de forcage par un booleen Studio

Quand l'utilisateur doit pouvoir **imposer** une quantite ou un prix que le bareme calculerait
sinon, poser un booleen Studio sur la ligne (ex. "Forcer la quantite", "Forcer le prix") et le
tester dans **chaque** regle de resultat concernee :

```groovy
// Regle RESULTAT, champ qty
if (attrs?.forcerQuantite == true) return qty   // valeur saisie conservee
// ... calcul normal
```

- La garde doit etre presente dans **toutes** les regles qui ecrivent le champ, y compris celles
  de baremes lies : une seule regle sans garde ecrase la saisie au recalcul suivant.
- Rendre le champ editable dans la vue quand le booleen est coche, et seulement dans ce cas.
- Auditer periodiquement : lister les regles de resultat qui ecrivent `qty` ou `price` et
  verifier la presence de la garde dans chacune.

### 4.11 Cout de revient pilote par bareme : `costPrice = 0` au niveau societe

Probleme : le calcul standard (`fillCostPrice`) reecrit `subTotalCostPrice` a partir du
`costPrice` de l'article, et ecrase la valeur posee par le bareme.

Technique constatee : mettre `costPrice = 0` sur la configuration **societe** de l'article
(`ProductCompany`). Le calcul standard ne reecrit plus le cout quand il vaut 0, et le bareme
garde la main sur `subTotalCostPrice`.

- **Reserve** aux articles sans cout d'achat ni cout de stock reel (prestations, forfaits
  calcules). Pour un article achete ou stocke, utiliser un champ Studio dedie au cout calcule.
- Verifier que le bareme se **redeclenche au changement de quantite** : sinon le cout reste
  celui de la quantite initiale.
- **Anti-pattern** : recopier le cout dans `costPrice` a chaque devis. Le cout de l'article
  devient celui du dernier devis saisi, pour tous les documents suivants.

---

## 5. PIEGES DOCUMENTES

Chacun a ete rencontre en conditions reelles. Le symptome est ce qui permet de le reconnaitre.

### 5.1 `typeSelect` a 'Default' - le bareme est ignore en silence

**Symptome** : aucun prix, et le log de ligne indique "Pas de bareme utilise pour cet enregistrement".

Le module Ventes appelle `PricingRepository.PRICING_TYPE_SELECT_SALE_PRICING`, dont la valeur
est **`'Pricing'`**, pas `'Default'`. Un bareme cree en `'Default'` n'est jamais selectionne
par le calcul de devis, sans aucune erreur.

Verification : `SELECT type_select FROM base_pricing;` -> doit valoir `Pricing` pour les ventes.

### 5.2 `ClassCastException: Integer cannot be cast to BigDecimal`

**Symptome** : `PricingComputer.computeClassificationFormula` leve une exception des que le champ
source est vide. Passe inapercu tant qu'on teste avec des valeurs renseignees.

Cause : une regle de classification **decimale** dont la formule se termine par `?: 0`. Le
litteral `0` est un `Integer`, et `checkRuleOperator` caste en `BigDecimal`.

Correctif : toujours retourner explicitement un `BigDecimal` (voir 4.2).

### 5.3 Prix catalogue non nul - le prix fantome

Quand aucune ligne ne matche, le moteur ne remplace pas le prix : celui du catalogue reste.
Si l'article porte un `salePrice` non nul, **ce prix part en facture** sans que rien ne le signale.

Regle : tout article pilote par bareme doit avoir `salePrice = 0` et `costPrice = 0`,
**y compris sur ses `ProductCompany`**.

### 5.4 `autoUpdateSalePrice` ecrase le prix du bareme

Si l'article a `autoUpdateSalePrice = true`, le calcul standard recalcule le prix de vente
depuis le cout et le coefficient, apres le bareme. Verifier ce flag sur l'article **et** sur
ses `ProductCompany`.

### 5.5 `ProductCompany` est en heritage single-table

`base_product` porte une colonne `dtype` : `'Product'` pour les articles, `'ProductCompany'`
pour les configurations par societe. Il **n'existe pas** de table `base_product_company`.

Consequence : un `SELECT count(*) FROM base_product` compte les deux. Toujours filtrer
`WHERE dtype = 'Product'`, sinon les inventaires sont faux.

### 5.6 `attrs` de la ligne vs `attrs` de l'entete

Dans un bareme dont le `concernedModel` est `SaleOrderLine`, la variable `attrs` designe les
champs personnalises **de la ligne**. Pour lire un champ Studio porte par l'entete, il faut
passer par la relation : `saleOrder.attrs`.

### 5.7 "Ce bareme devrait etre applique mais n'a pas pu l'etre"

**Symptome** : message d'information a la selection du produit.

Ce message est une **bonne nouvelle sur le parametrage** : il ne se declenche que si un bareme a
ete **trouve** (`defaultPricing.isPresent()`). Ce sont donc les **classifications** qui ne matchent
pas. Verifier dans l'ordre : segment du client, valeur numerique source, formule tarifaire,
existence d'une ligne pour cette combinaison.

### 5.8 Debordement du dernier palier

Au-dela de la derniere borne, la derniere ligne s'applique sans alerte. Une installation hors
grille est facturee au tarif du dernier palier. Prevoir une ligne de garde ou faire acter le plafond.

### 5.9 Erreurs de classloader en Tomcat embarque

**Symptome** : `Type specified for TypedQuery [...] is incompatible with the query return type
of the same name` a chaque enregistrement d'entite.

Cause : `GlobalEntityListener` (workflows Studio) s'execute sur un thread separe ou le context
classloader n'est pas positionne. En `gradlew run`, les classes vivent a la fois sur le classpath
systeme et dans le webapp classloader.

Non bloquant (l'exception est catchee) mais bruyant. **Disparait en Tomcat externe**, ou il n'y a
qu'un seul classloader. Aucun interrupteur cote configuration Studio.

### 5.10 `sum { it.champ }` sans garde : NPE silencieuse, resultat a 0

**Symptome** : la regle renvoie 0 ou rien alors que les donnees existent. Aucun message visible.

Cause : un seul element de la collection a le champ nul, et `sum` leve une NPE que le moteur
avale. Le `?: 0` place **apres** le `sum` ne couvre que l'absence de collection, pas un element nul.

```groovy
// FAUX : le ?: 0 externe ne protege pas des elements nuls
def total = lignes?.sum { it.longueur } ?: 0

// CORRECT : garde dans la closure, liste vide geree, cast explicite
def total = (lignes ?: []).sum { it?.longueur ?: 0 } ?: 0
return new BigDecimal(total.toString())
```

Regle : `?.` sur toute la chaine d'acces, `?: []` avant `sum`, `?: 0` **dans** la closure,
cast `as BigDecimal` ou `new BigDecimal(...)` en sortie.

### 5.11 `return` de haut niveau : il fonctionne

Une conclusion a circule selon laquelle un `return` en tete de formule serait ignore par le
moteur. Elle est **fausse** : le `return` de haut niveau fonctionne. Le symptome qui l'avait
fait croire etait en realite le piege 5.10. Avant d'accuser la syntaxe, chercher une NPE.

### 5.12 `saleOrder.opportunity` dans un bareme de ligne de devis

Sur un bareme `SaleOrderLine`, ne pas passer par `saleOrder.opportunity` par defaut : le devis
n'a pas toujours d'opportunite, et la grandeur lue la peut avoir diverge de celle du devis.
Lire d'abord le champ sur la ligne (directement ou via `__this__`), puis sur `saleOrder`, et
ne descendre vers l'opportunite qu'en repli explicite et documente (cascade du pattern 4.4).

Inversement, sur un bareme dont l'objet est `Opportunity`, les champs se lisent **directement**
(`estimatedPower`), jamais `opportunity.estimatedPower`.

---

## 6. METHODE DE BOUT EN BOUT

### Etape 1 - Comprendre la grille avant de parametrer

Lire le document tarifaire ligne a ligne et repondre a ces questions :

- Quels sont les **axes reels** ? Attention aux matrices trompeuses : une grille "3 formules x
  2 segments" peut cacher quatre natures de lignes differentes (prestations a valeur ajoutee,
  prestations reglementaires a prix invariant, refacturations de moyens, modificateurs de prix).
- Quelles lignes ont un **prix identique sur toutes les colonnes** ? L'axe y est neutre.
- Quelles lignes ne sont **pas des prix** ? Coefficients, remises, mentions "inclus" ou "sur devis"
  sont des **regles**, pas des prix. Ne jamais les loger dans une grille de prix unitaires.
- Y a-t-il des **chevauchements ou des trous** dans les bornes ? Les faire corriger par le client,
  ne jamais parametrer une ambiguite.

### Etape 2 - Inventorier la base cible

Requetes en section 7. Il faut savoir, avant de proposer quoi que ce soit :
- quels articles existent deja et lequel servira de **source de duplication**
- quelles categories de tiers sont peuplees, et **combien de clients en sont depourvus**
- quels champs portent deja les grandeurs necessaires, et **s'ils sont alimentes**
- si le moteur est deja actif et si des baremes existent

### Etape 3 - Decider articles vs baremes

Appliquer la regle de la section 3, famille par famille, et **produire le tableau de decision**
avec le nombre d'articles et la justification. C'est ce tableau qui se discute avec le client,
pas le detail technique.

### Etape 4 - Concevoir les axes

Pour chaque famille : quelles classifications, dans quel ordre, quels resultats. Verifier la
limite de 4. Reutiliser au maximum les **regles partagees** : une regle "segment client" doit
servir tous les baremes.

### Etape 5 - Produire les scripts

Modele en section 8. Trois exigences non negociables :
- **aucun identifiant technique en dur** - les id different d'une base a l'autre
- **idempotence** - rejouer la serie ne doit rien dupliquer
- **garde-fou de prerequis** - le script s'arrete si l'environnement cible ne convient pas

### Etape 6 - Recette

Ne jamais valider par une simulation SQL. Appeler l'**action reelle** de l'application :

```
POST /ws/action
{"model":"com.axelor.apps.sale.db.SaleOrderLine",
 "action":"action-sale-order-line-method-compute-pricing-scale",
 "data":{"context":{"_model":"com.axelor.apps.sale.db.SaleOrderLine",
   "product":{"id":<id>},"qty":1,
   "_parent":{"_model":"com.axelor.apps.sale.db.SaleOrder","company":{"id":<id>},
              "clientPartner":{"id":<id>}, ...}}}}
```

Couvrir : toutes les combinaisons de la grille, **les bornes exactes** (n et n+1), les champs
vides, les segments non couverts, et les cas "sur devis" qui doivent ne rien renvoyer.

### Etape 7 - Livrer

Scripts numerotes dans `src/main/scripts/V<version>/`, dans l'ordre de dependance :

```
00  verification des prerequis
01  unites de mesure
02  articles + ProductCompany
03  champs personnalises
04  regles de bareme
05  baremes            (depend de 02 et 04)
06  lignes de bareme   (depend de 05)
07  activation du moteur
08  modele de document (en dernier)
```

Valider la serie sur une **restauration vierge du dump**, avec les sequences volontairement
decalees, puis comparer les empreintes md5 du resultat a l'environnement de reference.

---

## 7. REQUETES D'INVENTAIRE

```sql
-- Moteur actif ?
SELECT enable_pricing_scale, is_pricing_computing_order FROM studio_app_base;

-- Baremes existants (precedents reutilisables)
SELECT p.id, p.name, p.type_select, c.code AS societe, p.start_date,
       (SELECT count(*) FROM base_pricing_line l WHERE l.pricing = p.id) AS lignes
FROM base_pricing p LEFT JOIN base_company c ON c.id = p.company ORDER BY p.id;

-- Regles existantes et leurs formules
SELECT r.id, r.name,
       CASE r.type_select WHEN 1 THEN 'CLASSIF' WHEN 2 THEN 'RESULT' END AS type,
       CASE r.field_type_select WHEN -1 THEN 'int' WHEN 0 THEN 'texte' WHEN 1 THEN 'dec' END AS champ,
       CASE r.operator_select WHEN -1 THEN '<' WHEN 0 THEN '=' WHEN 1 THEN '>' END AS oper,
       (SELECT m.name||'.'||f.name FROM meta_field f JOIN meta_model m ON m.id = f.meta_model
         WHERE f.id = r.field_to_populate) AS cible
FROM base_pricing_rule r ORDER BY r.id;

-- Categories de tiers ET leur peuplement reel (mesurer le trou de couverture)
SELECT coalesce(pc.code,'(sans categorie)') AS categorie, count(*) AS clients
FROM base_partner p LEFT JOIN base_partner_category pc ON pc.id = p.partner_category
WHERE p.is_customer = true GROUP BY pc.code ORDER BY 2 DESC;

-- Articles : ne compter que les vrais articles (voir piege 5.5)
SELECT count(*) FROM base_product WHERE dtype = 'Product';

-- Article candidat a la duplication : sa configuration complete
SELECT p.code, p.name, p.product_type_select, p.sale_price, p.cost_price,
       p.auto_update_sale_price, f.name AS famille, c.name AS categorie, u.name AS unite
FROM base_product p
LEFT JOIN base_product_family f   ON f.id = p.product_family
LEFT JOIN base_product_category c ON c.id = p.product_category
LEFT JOIN base_unit u             ON u.id = p.unit
WHERE p.code = '<code>' AND p.dtype = 'Product';

-- La comptabilite est-elle portee par l'article ou par la famille ?
SELECT count(*) FILTER (WHERE product IS NOT NULL)        AS par_article,
       count(*) FILTER (WHERE product_family IS NOT NULL) AS par_famille
FROM account_account_management;

-- Champs candidats a porter une grandeur, et leur PEUPLEMENT reel
SELECT count(*) AS total,
       count(*) FILTER (WHERE estimated_power IS NOT NULL AND estimated_power <> 0) AS renseigne
FROM sale_sale_order;

-- Champs personnalises deja presents sur un modele
SELECT id, name, type_name, title, context_field, context_field_value
FROM meta_json_field WHERE model_name = 'com.axelor.apps.sale.db.SaleOrder' ORDER BY sequence;
```

**Un champ declare n'est pas un champ alimente.** Toujours mesurer le peuplement : un axe de
bareme bati sur un champ vide ne produira jamais aucun prix.

---

## 8. MODELE DE SCRIPTS LIVRABLES

### 8.1 Garde-fou de prerequis (script 00)

```sql
BEGIN;
DO $$
DECLARE manquants text := '';
BEGIN
  IF NOT EXISTS (SELECT 1 FROM base_product WHERE code = '<code source>' AND dtype = 'Product') THEN
    manquants := manquants || E'\n  - article source <code source>';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_partner_category WHERE code = 'AGRI') THEN
    manquants := manquants || E'\n  - categorie de tiers AGRI';
  END IF;
  -- ... un bloc par prerequis
  IF manquants <> '' THEN
    RAISE EXCEPTION E'Integration IMPOSSIBLE, prerequis manquant(s) :%', manquants;
  END IF;
  RAISE NOTICE 'Tous les prerequis sont presents.';
END $$;
COMMIT;
```

### 8.2 Resolution par code metier, jamais par id

```sql
-- INTERDIT                          -- CORRECT
concerned_model = 408                (SELECT id FROM meta_model WHERE name = 'SaleOrderLine')
company = 1                          (SELECT id FROM base_company WHERE code = '101')
field_to_populate = 9591             (SELECT f.id FROM meta_field f
                                        JOIN meta_model m ON m.id = f.meta_model
                                       WHERE m.name = 'SaleOrderLine' AND f.name = 'price')
WHERE id = 129                       WHERE code = '100011' AND dtype = 'Product'
unit = 12                            (SELECT id FROM base_unit WHERE name = 'Heure')
```

### 8.3 Creation d'article par copie integrale

Herite famille, categorie, type, comptes, sans rien inventer :

```sql
CREATE TEMP TABLE tmp_art ON COMMIT DROP AS SELECT * FROM base_product WHERE id = v_src;
UPDATE tmp_art SET
  id = v_new, code = r.code, name = r.libelle,
  full_name = '[' || r.code || '] ' || r.libelle,
  unit = v_unit, version = 0, import_id = NULL, serial_number = NULL,
  sale_price = 0, cost_price = 0, created_on = now(), updated_on = now();
INSERT INTO base_product SELECT * FROM tmp_art;
-- puis idem pour les ProductCompany (dtype = 'ProductCompany', product = v_src)
```

### 8.4 Bareme avec formule generee

```sql
INSERT INTO base_pricing
 (id, version, created_on, updated_on, name, company, concerned_model, type_select,
  start_date, product, class1pricing_rule, result1pricing_rule, formula)
VALUES (nextval('base_pricing_seq'), 0, now(), now(), r.nom, v_comp, v_mod, 'Pricing',
  r.debut, v_prod,
  (SELECT id FROM base_pricing_rule WHERE name = r.cl1),
  (SELECT id FROM base_pricing_rule WHERE name = r.res1),
  'product?.id == ' || v_prod || ' || product?.parentProduct?.id == ' || v_prod);
```

### 8.5 Idempotence

```sql
CONTINUE WHEN EXISTS (SELECT 1 FROM base_product WHERE code = r.code AND dtype = 'Product');
-- ou, pour les lignes de bareme, tester la combinaison complete de classifications
```

---

## 9. CHECKLIST AVANT LIVRAISON

**Parametrage**
- [ ] `typeSelect` = `'Pricing'` sur tous les baremes de vente
- [ ] Toute classification decimale retourne un `BigDecimal`
- [ ] `salePrice` et `costPrice` a 0 sur les articles **et** leurs `ProductCompany`
- [ ] `autoUpdateSalePrice` a `false`
- [ ] Regles partagees reutilisees, pas dupliquees
- [ ] Comportement decide pour : valeur nulle, debordement haut, segment non couvert
- [ ] Champ `formula` renseigne sur chaque bareme
- [ ] Aucun `sum` sans garde dans la closure
- [ ] Garde de forcage presente dans toutes les regles qui ecrivent un champ forcable
- [ ] Cout pilote par bareme : `costPrice = 0` sur la `ProductCompany`, recalcul au changement de quantite verifie

**Scripts**
- [ ] Aucun identifiant technique en dur (`grep` de controle)
- [ ] Aucune donnee de demonstration ou de production
- [ ] Garde-fou de prerequis en tete de serie
- [ ] Idempotents, verifies par un second passage
- [ ] Ordre de dependance respecte, documente dans les en-tetes
- [ ] Retour arriere decrit dans chaque en-tete

**Recette**
- [ ] Toutes les combinaisons de la grille testees via l'action reelle
- [ ] Bornes exactes verifiees (n et n+1)
- [ ] Cas negatifs : champs vides, segment absent, "sur devis"
- [ ] Serie rejouee sur une restauration vierge avec sequences decalees
- [ ] Empreintes md5 comparees a l'environnement de reference

**A dire au client**
- [ ] Champs sources non alimentes -> les axes concernes ne produiront aucun prix
- [ ] Part de clients hors segments couverts, chiffree
- [ ] Mecanismes transitoires assumes et leur date de revision
- [ ] Plafonds et comportements par defaut actes

---

## 10. ECRIRE UNE FORMULE GROOVY LISIBLE

| Regle | Pourquoi |
|---|---|
| Constantes nommees (`PRIX_PLANCHER`, `SEUIL_M2`, `COEF_M2`) en tete | La revision tarifaire se fait sans relire l'algorithme |
| Terminer par une **expression finale nue** (ou un `return` explicite) | La valeur retournee est evidente a la relecture |
| `?.` sur chaque acces relationnel, `?:` sur chaque valeur lue | Un champ vide ne doit jamais lever d'exception (5.2, 5.10) |
| Sortie decimale toujours en `BigDecimal` | Evite `ClassCastException` (5.2) |
| Commentaire = **intention**, pas paraphrase du code | `// plancher contractuel` aide ; `// prend le max` n'aide pas |
| Aucune justification metier inventee en commentaire | Une fausse justification est pire que pas de commentaire : elle sera crue |

Acces aux donnees :
- `attrs` = champs Studio de l'objet du bareme ; ceux de l'entete via `saleOrder.attrs` (5.6).
- Dans le JSON `attrs`, un champ personnalise peut apparaitre sous une cle technique
  `<type><id>` (ex. `integer2287`, `decimal110`) : relever la cle reelle en base
  (`meta_json_field`) avant d'ecrire la formule, et convertir les decimaux avec
  `new BigDecimal(valeur.toString())`.
- Resultat lu depuis la ligne de grille : `pricingLine.resultParam1` a `resultParam4`,
  aucune autre variante.
- Pour un prix decimal saisi en champ Studio, le type "Chaine de caracteres" est le pattern
  historique AxENR : convertir explicitement en `BigDecimal` dans la formule.

---

## 11. DIAGNOSTIQUER UN BAREME QUI NE S'APPLIQUE PAS

### 11.1 Lire le log de calcul

Sur la ligne de devis, lancer **"Recalcul des prix"**, puis lire le champ `pricingScaleLogs` de
la ligne. Il dit lequel des trois cas s'applique :

| Log | Signification | Ou chercher |
|---|---|---|
| Aucun bareme utilise | Le bareme n'a pas ete selectionne | Formule vide (1.1), `typeSelect` (5.1), societe, dates, modele, archive |
| "devrait etre applique mais n'a pas pu l'etre" | Bareme trouve, classifications sans correspondance | 5.7, sens de l'operateur (2.1), ordre des lignes |
| Bareme applique, resultat inattendu | Regle de resultat fautive | NPE avalee (5.10), cast (5.2), garde de forcage (4.10) |

### 11.2 Comparer a un bareme qui marche

Quand le log ne suffit pas, comparer **champ par champ** le bareme en echec a un bareme
fonctionnel de la meme instance (fetch REST en lecture ou requete SQL sur `base_pricing`) :
formule, `typeSelect`, societe, modele concerne, dates, regles de classification et de resultat,
`linkedPricing`. L'ecart saute aux yeux plus vite qu'un raisonnement sur le code.

### 11.3 Isoler la formule fautive, du plus simple au plus reel

1. Remplacer la formule par une **valeur fixe** : si rien ne s'affiche, le probleme est en amont.
2. Lire un **champ connu et renseigne** de l'objet : valide l'acces au contexte.
3. Verifier la donnee en **SQL** : le champ est-il vraiment alimente sur cet enregistrement ?
4. Verifier le **nom technique** dans `meta_field` / `meta_json_field` (nom de propriete,
   pas de colonne : `length_overallm` en base peut etre `lengthOverallM` en Groovy).
5. En dernier recours, tester l'acces en **JPQL**.

Debug "aucun resultat" sur une grille : formule non nulle -> sens de l'operateur -> ordre des
lignes -> desactiver les autres classifications -> toutes les classifications renseignees.

### 11.4 Generateur d'indicateurs (requetes depuis l'interface)

Pratique pour verifier une donnee sans acces base, avec trois limites : **pas de JSONB**
(les `attrs` ne sont pas lisibles), **pas de cast**, **pas de `;` final**.

---

## 12. PARAMETRER DEPUIS L'INTERFACE

| Situation | Constat | Parade |
|---|---|---|
| Champ Formule du bareme en lecture seule | C'est un editeur Monaco verrouille | Console du navigateur : `monaco.editor.getEditors()[0].updateOptions({readOnly:false})`, puis `executeEdits` pour injecter le texte, puis enregistrer |
| Ecriture REST directe refusee | Les ecritures d'agent sur une ressource partagee peuvent etre bloquees | Creer et modifier par l'interface |
| Ajout de ligne dans une grille O2M | Le "+" n'agit pas | Passer la grille en mode edition avant "+" |
| Editeur riche | `ctrl+a` selectionne la page | Cliquer dans le champ avant `ctrl+a` |
| Creer une variante | | "Dupliquer" fonctionne pour l'article et pour le bareme |
| Menu des baremes | Son libelle varie selon l'instance ("Ventes > Bareme", "Tarification") | Le chercher par la recherche de menu |

Le contournement Monaco est un expedient de consultant : il ne remplace pas une correction
des droits ou de la vue si un utilisateur metier doit modifier les formules en autonomie.

---

## 13. EXPLOITER UN EXPORT DE BAREMES (XLSX)

Un export Axelor des regles de bareme se lit avec pandas, onglet `PricingRule` :

```python
import pandas as pd
df = pd.read_excel("export.xlsx", sheet_name="PricingRule")
df.columns = [c.strip() for c in df.columns]   # noms de colonnes avec espaces finaux
for _, r in df.iterrows():
    print(r.iloc[0], "|", r["Formule"])          # la formule est dans la colonne "Formule"
```

Usage : audit en masse (gardes de forcage presentes, `?: 0` en fin de classification decimale,
`sum` sans garde), avant toute correction dans l'interface.

