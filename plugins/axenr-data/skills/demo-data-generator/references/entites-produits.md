# Entités — produits

**Pièges couverts par cette fiche :**

- 1. Un produit créé avec `product_family` / `sale_currency` / `purchase_currency` / `cost_type_select` à NULL casse silencieusement l'interface
- 2. `is_activity` n'est PAS « toujours false »
- 5. Les unités produit doivent être alignées (stock / vente / achat)
- 10. `type_select = NULL` rend une nomenclature (BoM) / gamme (ProdProcess) invisible dans les domaines de liste standard
- 11. Produits : `product_family` est OBLIGATOIRE pour la comptabilité (prolonge les pièges 1 et 5)
- 11.bis. « Le produit est créé » ne veut pas dire « le produit est vendable » : sans FAMILLE **et** CATÉGORIE, l'ajout à une commande échoue
- 25. Selects de valorisation de production du produit

Piège 2 rattaché ici : fait produit pur (is_activity), voisin direct de 1, 5, 10, 11.

### base_product_category

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| name | OUI | Nom de la catégorie |
| code | Recommandé | Code unique (vérifier : recherche par code à l'import) |
| import_id | Recommandé | Utiliser la plage 200000+ |
| version | OUI | Mettre à 0 |

### base_product

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| dtype | OUI (NOT NULL) | Toujours 'Product' |
| name | Recommandé | Nom du produit |
| code | Recommandé | Code produit unique |
| product_type_select | Recommandé | 'storable' ou 'service' |
| unit | Recommandé | Unité de stock. FK vers base_unit (voir les IDs d'unité ci-dessous) |
| sales_unit | **CRITIQUE (souple)** | FK vers base_unit. Aligner sur `unit` pour les données de démo (pas de conversion multi-unité). Laisser à NULL fait retomber les écrans de prix de vente sur `unit`, mais certains flux lèvent une erreur. |
| purchases_unit | **CRITIQUE (souple)** | FK vers base_unit. Aligner sur `unit` pour les données de démo. Même raison que sales_unit. |
| product_category | Recommandé | FK vers base_product_category |
| product_family | **CRITIQUE (souple)** | FK vers base_product_family. NOT NULL au niveau base, mais les regroupements/filtres de l'interface AOS s'appuient dessus — laisser à NULL casse la grille produit, la fiche de coût, et les tableaux de bord par famille. Voir les IDs de famille ci-dessous. |
| sale_price | Recommandé | BigDecimal, 10 décimales |
| purchase_price | Recommandé | BigDecimal, 10 décimales |
| cost_price | Recommandé | BigDecimal, 10 décimales |
| sale_currency | **CRITIQUE (souple)** | FK vers base_currency. EUR = 46. Nullable en base mais chaque écran vente/facture le déréférence → NPE dans l'interface. TOUJOURS le renseigner. |
| purchase_currency | **CRITIQUE (souple)** | FK vers base_currency. EUR = 46. Même raison que sale_currency. TOUJOURS le renseigner. |
| cost_type_select | **CRITIQUE (souple)** | Mode entier de fiche de coût. Valeur standard = 1 (coût standard). Nullable en base mais le calcul de fiche de coût lève une NPE si absent. |
| sellable | **CRITIQUE** | Doit être `true` — NULL masque le produit des sélections |
| purchasable | **CRITIQUE** | Doit être `true` — NULL masque le produit des sélections |
| is_shipping_costs_product | **CRITIQUE** | Doit être `false` — NULL masque le produit des formulaires |
| is_model | **CRITIQUE** | Doit être `false` |
| is_prototype | **CRITIQUE** | Doit être `false` |
| is_activity | **CRITIQUE** | `false` pour les matières premières / produits achetés en sous-traitance. `true` pour les **produits internes de main-d'œuvre/MO** suivis via feuille de temps (ex. études, pose atelier, assemblage). Règle empirique : product_type_select='service' ET procurement_method_select='produce' → is_activity=true. |
| stock_managed | Recommandé | `true` pour storable, `false` pour service |
| in_ati | Recommandé | Booléen, false par défaut |
| import_id | Recommandé | Utiliser la plage 200000+ |
| version | OUI | Mettre à 0 |

### 1. Un produit créé avec `product_family` / `sale_currency` / `purchase_currency` / `cost_type_select` à NULL casse silencieusement l'interface

**Symptôme :** `NullPointerException` ou écrans vides sur le formulaire produit, la fiche de coût, ou tout écran vente/achat qui déréférence la devise. Aucune erreur au moment de l'INSERT (colonnes nullables en base).

**Correctif :** Toujours renseigner ces 4 champs à l'INSERT. Pour les démos BTP françaises :
- `product_family` : 15 (matière) / 16 (MO interne) / 17 (matériel) / 18 (SST) — exemple sur base BTP
- `sale_currency = purchase_currency = 46` (EUR)
- `cost_type_select = 1`

**SQL de rattrapage** (si déjà inséré sans ces valeurs) :
```sql
UPDATE base_product
SET product_family = <id>, sale_currency = 46, purchase_currency = 46, cost_type_select = 1, updated_on = NOW()
WHERE code IN (...) AND (product_family IS NULL OR sale_currency IS NULL OR purchase_currency IS NULL OR cost_type_select IS NULL);
```

### 2. `is_activity` n'est PAS « toujours false »

Une consigne antérieure disait « is_activity doit être false ». C'est faux pour les **produits internes de main-d'œuvre/MO** :
- Les produits avec `product_type_select='service'` ET `procurement_method_select='produce'` représentent des activités suivies en feuille de temps → `is_activity = true`
- La sous-traitance pure achetée (`service` / `buy`) → `is_activity = false`
- Les matières stockables → `is_activity = false`

Se tromper sur ce point masque les produits de MO des sélecteurs d'activité/feuille de temps dans AOS.

### 5. Les unités produit doivent être alignées (stock / vente / achat)

`base_product` expose trois FK d'unité : `unit` (stock), `sales_unit`, `purchases_unit`. AOS gère la conversion multi-unité via `base_unit_conversion`, mais les jeux de données de démo doivent garder les trois alignées, sauf si la conversion est explicitement dans le périmètre.

**Symptôme en cas de désalignement ou de NULL :** prix affiché dans une unité, quantité attendue dans une autre → l'utilisateur voit des totaux incohérents ; certains flux vente/achat lèvent une erreur en déréférençant un `sales_unit` / `purchases_unit` NULL.

**Règle :** toujours poser `sales_unit = purchases_unit = unit` dans les inserts de démo. Rattrapage :

```sql
UPDATE base_product SET sales_unit = unit, purchases_unit = unit, updated_on = NOW()
WHERE code LIKE 'DEMO-PREFIX-%' AND (sales_unit IS NULL OR purchases_unit IS NULL);
```

### 10. `type_select = NULL` rend une nomenclature (BoM) / gamme (ProdProcess) invisible dans les domaines de liste standard

**Symptôme :** une `production_bill_of_material` / `production_prod_process` créée existe en base mais n'apparaît jamais dans les vues liste standard. Aucune erreur.

**Cause :** les action-views de grille standard filtrent avec un domaine qui exclut NULL :
- Liste BoM : `self.defineSubBillOfMaterial = true AND self.personalized = false AND self.typeSelect != 3` — et **`NULL != 3` s'évalue à NULL (pas TRUE) en SQL**, donc la ligne est exclue.
- Liste ProdProcess : `self.isPersonalized = false AND self.typeSelect = 1` — `NULL = 1` vaut NULL → exclu.

**Correctif :** toujours poser `type_select = 1` (normal) sur les BoM et ProdProcess insérés, plus `personalized = false` (BoM) / `is_personalized = false` (ProdProcess). Poser `define_sub_bill_of_material = true` seul n'est PAS suffisant — le prédicat `typeSelect` élimine silencieusement les lignes NULL. Confirmé sur AOS 9.0.8.

### 11. Produits : `product_family` est OBLIGATOIRE pour la comptabilité (prolonge les pièges 1 et 5)

`product_family` à NULL n'est pas qu'un confort d'interface — c'est le point d'accroche de la **configuration comptable** (la famille porte/dérive les comptes de produits/charges par défaut). Un produit avec une famille à NULL lève une erreur ou bloque à la génération d'écriture/facture. Toujours le positionner sur une famille déjà utilisée par d'autres produits fonctionnels (pour que sa config comptable soit présente), ex. `2 Equipement / 3 Composants / 4 Consommables` sur une base de démo AOS standard. Poser aussi, dans la même passe : `product_sub_type_select` (`1 Fini / 2 Semi-fini / 3 Composant` — `product.sub.type.product.select`), `sale_supply_select` (`product.sale.supply.select` : `2 Achat / 3 Production`), et `sales_unit = purchases_unit = unit`. Un produit fini fabriqué → subType 1 + saleSupply 3 ; un composant/consommable acheté → subType 3 + saleSupply 2.

### 11.bis. « Le produit est créé » ne veut pas dire « le produit est vendable » : sans FAMILLE **et** CATÉGORIE, l'ajout à une commande échoue

Prolonge le piège 11, et le durcit : la famille seule ne suffit pas. Un produit créé sans `product_family` NI `product_category` passe la création sans un mot, puis l'ajout à une commande de vente échoue sur « La configuration comptable est manquante pour le produit : X (société : Y) ». La configuration comptable ne se porte pas sur le produit, elle s'**hérite** de la famille et de la catégorie — un produit qui n'en a pas n'a rien à hériter.

Constaté sur des produits issus d'un configurateur, mais la cause n'a rien de spécifique au configurateur : c'est vrai de tout produit inséré ou généré sans ces deux relations. Le piège est que la génération, elle, réussit : « le produit existe » et « le produit se vend » sont deux assertions différentes, et un audit qui compte les produits ne voit que la première.

**Correctif de seed** : poser les deux relations dès l'insertion, et VÉRIFIER par l'usage (ajouter une ligne de commande sur un échantillon), pas par la présence des colonnes.

### 25. Selects de valorisation de production du produit

Pour les produits utilisés en production, renseigner `real_or_estimated_price_select`, `bom_comp_valu_method_select`, `manuf_order_comp_valu_method_select` (NULL = vide sur l'onglet production / ambiguïté de fiche de coût). Reproduire un produit manufacturé fonctionnel (démo AOS standard : `1` / `2` / `1`).

## Mapping familles produit (référence BTP)

**Règle empirique de mapping (jeux de données de démo BTP) :**

| Type de produit | procurement_method | product_family par défaut | is_activity |
|---|---|---|---|
| Matière première (stockable) | buy | 15 — Fourniture chantier | false |
| Main d'œuvre interne (service) | produce | 16 — Main d'Oeuvre chantier | **true** |
| Matériel possédé (service) | produce | 17 — Matériel chantier | false |
| Sous-traitance (service) | buy | 18 — Prestation et Sous-traitance | false |
| Ligne d'ouvrage synthétique | — | 19 — Ouvrage | false |
