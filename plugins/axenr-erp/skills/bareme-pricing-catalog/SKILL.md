---
name: bareme-pricing-catalog
description: Catalogue de reference pour axenr-bareme-expert - moteur Pricing Axelor (Pricing / PricingRule / PricingLine), contraintes dures verifiees dans le code AOS 8.5, regle de decision article vs bareme, 7 patterns de parametrage, 9 pieges documentes avec leur symptome, methode de bout en bout du besoin client aux scripts SQL livrables, requetes d'inventaire et modele de scripts idempotents sans identifiant en dur.
---

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
