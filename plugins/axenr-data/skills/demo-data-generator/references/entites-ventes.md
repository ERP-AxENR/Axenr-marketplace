# Entités — ventes (catégorie, produit, tiers, adresse, commande, facture)

> **Couche UI-critical uniquement.** Ce que ni le schéma (`scripts/shape-fiche.sh`, `introspect.sh`)
> ni un enregistrement modèle ne donnent. Les NOT NULL, les FK, les valeurs de sélection et les
> taux de remplissage ne sont PAS ici : ils s'introspectent au moment de produire (règle 1).
>
> **Établie empiriquement le 2026-09-03** sur `<base>` — **AOS 9.1.6 / plateforme
> EE 8.2.3** (+ module local `axelor-construction` 9.1.0-SNAPSHOT, 46 apps installées). Protocole :
> INSERT minimal (NOT NULL seuls, tous booléens à `false`, `name`/`full_name` posés, ids ≥ 900000
> tagués `import_origin='stress-c3'`), puis test de chaque domaine de menu au REST, ouverture de la
> fiche au navigateur, bissection colonne par colonne, nettoyage vérifié par comptage.
> Le journal et les captures citées (`c3-*.png`) ne sont pas livrés avec ce skill.
>
> **Marquage de chaque item** : `[prouvé]` = reproduit sur cette version, la preuve est citée ;
> `[statique]` = repris de l'analyse des sources par un autre agent, **non reproduit à l'écran** ;
> `[non résolu]` = la bissection n'a pas tranché, l'état atteint est écrit.

**Pièges déjà existants que cette fiche concerne** (numéros inchangés, ils restent dans leur fichier) :

- 1. Produit à `product_family` / `cost_type_select` NULL → interface cassée en silence — `entites-produits.md`
- 3. Séquences à relever au-dessus de la plage d'ID de démo — `methode-ecriture-sql.md`
- 4. Aucune sélection inventée : `0` est souvent invalide — `methode-ecriture-sql.md`
- 6 / 8 / 9 / 13 / 23 / 24. Forme du tiers, panneaux vides, situation comptable — `entites-tiers-contacts.md`
- 52. Cache Hibernate L2 : un UPDATE SQL n'apparaît pas en UI — `methode-audit.md` (**étendu par le 96 ci-dessous**)
- 54. Méta morte d'un module retiré → 500 à l'ouverture d'un écran — `methode-audit.md`
- 62 / 76. Un booléen NULL est exclu des grids et des pickers ; `= false` **exclut les NULL** — `methode-audit.md`
- 70 / 71 / 72 / 92. `full_name` périmé, `full_name` NULL = invisible, et la cascade à N niveaux — `entites-tiers-contacts.md`, `methode-audit.md`
- 73 / 74. Consommer la séquence, recopier les dénormalisations — `methode-ecriture-sql.md`
- 90. `meta_action` / `meta_view` peuvent porter des DOUBLONS de nom — `methode-audit.md`
- 91. Lire le panneau ACTIF, pas `document.body` — `methode-audit.md`
- 94. Omettre la clé `data` au REST désactive le filtre `archived` — `methode-audit.md`
- 113. Popup « Configurer Supply Chain » sur le devis même app `supplychain` inactive — garde `isApp()` manquante dans AOS

**Deux filtres transverses, valables sur les 9 tables, cités une seule fois ici :** tous les menus
héritent du filtre `archived` (piège 79/94) et les écrans multi-sociétés sont bornés par
`:__user__.activeCompany`. Ne pas les redire table par table.

---

## 0. Ce que le protocole a établi de transverse aux 9 tables

| Constat | Preuve |
|---|---|
| **Aucune des 9 fiches ne casse à l'ouverture sur un enregistrement minimal.** Les groupes `onLoad` effectifs (vue fusionnée, priorité 21) rendent `status:0` sur les 9 modèles ; les 9 fiches s'ouvrent au navigateur sans erreur console. **Une seule exception : `InvoiceLine`** (voir §9). | `[prouvé]` `/ws/action` sur les groupes onLoad, `status:0` + 0 erreur console ; captures `c3-*.png` |
| **`import_origin` est AFFICHÉ à l'écran sur la Commande client, et sur elle seule.** L'en-tête de `sale-order-form` rend `<Badge bg="primary">{importOrigin}</Badge>` et le panneau « Canal de ventes » affiche le champ en lecture seule. Un tag technique de démo devient donc visible du client. Balayage des 15 formulaires du périmètre : présent uniquement sur celui-là. | `[prouvé]` `/ws/meta/view` sur les 15 formulaires ; à l'écran l'en-tête affichait « Commande client **stress-c3** » (capture `c3-so-900006.png`). **Nouveau piège 98.** |
| **Deux menus du périmètre sont morts dans cette combinaison de modules** : `data-capture-root-objects-sale-orders` et `...-invoices` filtrent sur `self.dataCaptureTemplate`, champ **absent** de `SaleOrder` et `Invoice` (les tables ne portent que `is_data_capture_created` / `is_data_capture_updated`). Famille du piège 54. | `[prouvé]` REST → `status:-1`, `causeStack: java.lang.IllegalArgumentException: No such field 'dataCaptureTemplate' in object 'com.axelor.apps.sale.db.SaleOrder'` ; colonne absente d'`information_schema` |
| **Les champs `required` de la VUE ne sont pas ceux du domaine.** Les `required="true"` d'entité correspondent 1:1 aux NOT NULL de la base — donc toute exigence supplémentaire vient des **vues**, et elle est invisible au schéma. Liste ventes ci-dessous, par table. | `[prouvé]` balayage `required` de la vue fusionnée `/ws/meta/view` vs `information_schema.columns.is_nullable` |

---

## 1. `base_product_category`

Rien. Les deux colonnes qui comptent (`code`, `name` = namecolumn) sont NOT NULL, les deux menus
(liste et arbre) n'ont **aucun** `domain`, et la fiche s'ouvre nue sans erreur.

- **Casse à NULL** : néant. `[prouvé]` INSERT minimal → fiche ouverte, panneaux « Nom / Code /
  Catégorie parente / Remise maximale / Coefficient » tous rendus (capture `c3-prodcat-900001.png`).
- **Domaine filtrant** : néant — `referential.conf.product.category` et `...-tree` sans `<domain>`.
  `[prouvé]` la ligne minimale apparaît dans les deux (`total=1`).
- **Dénormalisation / namecolumn / moteur** : néant propre. `[statique]` `name` porte
  `namecolumn="true"` directement, pas de `computeFullName` séparé.
- Attention : Le dashlet « CA H.T. par catégorie par mois » de la fiche affiche **« Aucune donnée trouvée »**
  sur une catégorie neuve : c'est normal (il agrège des factures ventilées), ne pas chercher à le
  remplir en SQL. `[prouvé]` capture `c3-prodcat-900001.png`.

## 2. `base_product`

**Casse à NULL**

- `product_type_select` — nullable en base, mais **requis par la vue** (`product-form`) et testé par
  égalité stricte par les menus. `[prouvé]` menu « Articles » : `total=0` avec la colonne à NULL,
  `total=1` après `product_type_select='storable'`.
- `product_family` → dérivation des comptes comptables. `[statique]` (piège 1, déjà en fiche produits).

**Domaine filtrant qui exclut le NULL** — les 12 menus produits du périmètre, tous en égalité stricte :

| Prédicat présent dans les menus | Conséquence sur un NULL |
|---|---|
| `self.dtype = 'Product'` — sur **les 12** | Discriminant d'héritage mono-table. `ProductCompany` partage la table (92 lignes sur 391 dans cette base) : ces lignes ne sont dans **aucun** menu produit, et c'est voulu. Écrire un autre `dtype` rend la ligne invisible partout. `[prouvé]` `self.dtype='ProductCompany'` sur ma ligne → `total=0` |
| `self.isModel = false` / `= :_isModel` | NULL exclu (piège 76) |
| `self.sellable = true` (menus vente), `self.purchasable = true` (achat) | `[prouvé]` `total=0` à false, `total=1` après `sellable=true` |
| `self.isShippingCostsProduct = false`, `self.isPackaging = true`, `self.expense = true/false`, `self.isActivity = true` | NULL exclu dans les deux sens |

- Attention : **Le menu « Articles » ne porte pas le domaine qu'on lit dans `axelor-base`.** Deux
  `meta_action` s'appellent `product.root.product` (l'une de base, l'autre d'`axelor-human-resource`,
  qui ajoute `self.expense = false`) : c'est **celle d'HR qui est servie au runtime**. Un produit à
  `expense IS NULL` est donc absent du menu produits principal, et cette exigence n'existe dans
  aucun fichier de vues d'`axelor-base`. Famille du piège 90.
  `[prouvé]` `/ws/action` sur `product.root.product` retourne
  `domain: "self.isModel = :_isModel AND self.productTypeSelect = :_productTypeSelect AND self.expense = false AND self.dtype = 'Product'"`.

**Dénormalisation non resynchronisée** : néant sur `Product` lui-même ; les recopies sont en aval
(`sale_sale_order_line.product_name`, `account_invoice_line.product_name/product_code/unit`). `[statique]`

**namecolumn** : `full_name`, format fixe `[<code>] <name>` posé par `ProductBaseRepository`, jamais
par un trigger. Un INSERT SQL doit le poser dans ce format exact. `[statique]`

**À laisser au moteur** : `cost_type_select` a un `default="1"` d'entité — à reproduire
explicitement en SQL. `[statique]`

## 3. `base_partner`

**Casse à NULL**

- `main_address` → NPE dans la validation SIREN/TVA (`RegistrationNumberValidator`). `[statique]`
- `partner_type_select` NULL → ni le panneau « Société » ni le panneau « Particulier » ne s'affiche :
  la fiche paraît amputée de son bloc nom. `[statique]` (complète le piège 6)
- `full_name` NULL → enregistrement introuvable dans tout sélecteur m2o. `[statique]` (piège 71)

**Domaine filtrant qui exclut le NULL** — 17 menus, **aucun** n'est neutre. Sur les 17, un tiers
minimal (tous booléens à `false`) n'apparaît que dans **un seul** : `referential.root.partners`
(`self.isContact != true`). `[prouvé]` 17 recherches REST, 1 seul `total=1`.

| Menu | Prédicat | Ce qu'il faut poser |
|---|---|---|
| Clients (vente, CRM) | `self.isContact = false AND (self.isCustomer = true OR self.isProspect = true)` | `is_customer` ou `is_prospect` `[prouvé]` `total=1` après `is_customer=true` |
| Fournisseurs | `self.isContact = false AND self.isSupplier = true` | `is_supplier` |
| Contacts (référentiel) | `self.isContact = true` | `is_contact` |
| Contacts (CRM) | `self.isContact = true AND self.isEmployee = false` | Attention : **tension avec le piège 6.bis** : le `contact_partner` d'un employé DOIT porter `is_employee=true`, ce qui l'exclut délibérément du menu Contacts CRM. Ce n'est pas un défaut. `[prouvé]` `total=1` sur le contact `is_employee=false`, exclu dès qu'il passe à `true` |
| Contacts vente / achat | `self.isContact = true AND (self.mainPartner.isCustomer = true OR self.mainPartner.isProspect = true)` | Attention : **le filtre porte sur le PARENT** : un contact sans `main_partner`, ou rattaché à un tiers qui n'est ni client ni prospect, est invisible. `[prouvé]` `total=1` après `is_contact=true` + `main_partner` vers un tiers `is_customer=true` |
| Prospects (4 menus CRM) | `... self.isProspect = true` + `self.partnerStatus.isOpen = true/false` selon le menu | `is_prospect` **et** la FK `partner_status` : à NULL, le prospect est absent des menus « ouverts » ET « clos » |
| Affactureur / transporteur / sous-traitant | `self.isFactor` / `self.isCarrier` / `self.isSubcontractor = true` | le booléen dédié |

**Champ requis par la VUE et nullable en base** : `address` (dans l'éditeur d'adresses de
`partner-customer-form`). `[prouvé]` extraction `required` de la vue fusionnée.

**Dénormalisation non resynchronisée** : `simple_full_name`, recalculé par
`PartnerServiceImpl.computeSimpleFullName` à chaque save et **jamais** par SQL — un
`UPDATE ... SET name=` direct le laisse périmé. `[statique]` (niveau supplémentaire du piège 92)

**namecolumn** : `full_name`, calculé par `PartnerServiceImpl.computeFullName()`. `[statique]`

## 4. `base_address`

C'est la table la plus piégeuse du périmètre, et le piège n'est pas où l'analyse statique le plaçait.

**Casse à NULL — `city` (et `street_name`, `zip`) : l'adresse devient INSAUVEGARDABLE**

`AddressBaseRepository.save()` appelle `AddressTemplateServiceImpl.checkRequiredAddressFields()`,
qui **lève** dès qu'un champ marqué requis dans le `AddressTemplate` du **pays** est NULL. Toutes
ces colonnes sont nullables en base. Pour la FRANCE (template `DEFAULT`, `base_country.id=3`) les
requis sont **`city`, `street_name`, `zip`**.

```
[prouvé] save REST de l'adresse minimale (country=3 seul) -> status:-1
  causeStack: com.axelor.apps.base.AxelorException: Champ de l'adresse manquant : city
    at AddressTemplateServiceImpl.checkRequiredAddressFields(AddressTemplateServiceImpl.java:142)
    at com.axelor.apps.base.db.repo.AddressBaseRepository.save(AddressBaseRepository.java:40)
```

> Attention : **Ceci CORRIGE `entites-tiers-contacts.md`**, qui dit de `city` : « Peut ne pas exister pour
> tous les codes postaux — laisser NULL si absent ». Sur 9.1.6 cette consigne produit une adresse
> qu'aucun écran ne peut plus enregistrer, **et** qui fait échouer tout save d'un parent qui cascade
> dessus. S'il n'existe pas de `base_city` pour le code postal visé, **créer la ville** (règle 10),
> ne pas laisser la FK vide.
> La liste des requis est **par pays** : `SELECT f.name FROM base_address_template_line l JOIN
> meta_field f ON l.meta_field=f.id WHERE l.is_required AND l.address_template=(SELECT
> address_template FROM base_country WHERE id=<pays>)`. `[prouvé]` FRANCE → city, street_name, zip ;
> CANADA → + `country_sub_division`. Aucun pays sans template dans cette base (0 sur 246).

**namecolumn — `full_name` et toute la chaîne d'affichage sont dérivés au SAVE, jamais par SQL**

Avec les 3 requis renseignés, le save réussit et le moteur dérive **quatre** colonnes d'un coup :

```
[prouvé] save REST avec street_name + zip + city={id:1} -> status:0, puis en base :
  addressl4            = '12 RUE DU STRESS'
  addressl6            = '75001 NICE'
  full_name            = 'ALPES-MARITIMES 12 RUE DU STRESS 75001 NICE'
  formatted_full_name  = 'ALPES-MARITIMES\n12 RUE DU STRESS\n75001 NICE\nFRANCE'
```

Un INSERT SQL ne déclenche rien de tout ça : il doit poser lui-même `addressl4`, `addressl6`,
`full_name` **et** `formatted_full_name`, dans ce format (`<département> <l4> <l6>` pour `full_name`).

**Domaine filtrant** : néant — `referential.conf.address` n'a aucun `domain`. `[prouvé]` `total=1`.
Mais **la grille des adresses n'a qu'une seule colonne de données, `fullName`** : une adresse à
`full_name` NULL s'affiche comme une **ligne vide** dans la liste. `[prouvé]` `/ws/meta/view`
`address-grid` → `[('fullName','field'), ('mapBtn','button'), ('directionsBtn','button')]` ;
capture `c3-address-grid.png`.

**Dénormalisation non resynchronisée** : `formatted_full_name` est la source des colonnes
`*_address_str` recopiées ailleurs (`sale_sale_order.delivery_address_str`,
`account_invoice.address_str`) ; à NULL, les recopies le sont aussi. `[statique]`

**À laisser au moteur** : `latit` / `longit` (géocodage par API). `[statique]`

## 5. `base_partner_address`

Table satellite, **aucun menu** ne la cible : elle ne se consulte que par le panneau
`partnerAddressList` de la fiche tiers. Rien à tester en visibilité.

- **Casse à NULL** : `is_invoicing_addr` / `is_delivery_addr` laissés à NULL laissent le bandeau
  d'avertissement `invoiceAndDeliveryAddressText` affiché sur la fiche tiers (Groovy traite NULL
  comme faux). `[statique]` — application directe de la règle 3.
- **À laisser au moteur** : rien ; au contraire, `partner` est nullable et non `required` alors que
  c'est le côté propriétaire de `Partner.partnerAddressList` (mappedBy) — le laisser NULL crée une
  ligne orpheline invisible de la fiche tiers. `[statique]` (piège 85 : les DEUX côtés)
- `[prouvé]` l'INSERT minimal avec `address` + `partner` posés est bien lu au REST (`total=1`).

## 6. `sale_sale_order`

Trois pièges 9.1.7 qui se voient sur l'écran des ventes : la « date de commande » est celle de la 1re facture
(piège 195) ; les complémentaires d'un tiers s'ajoutent à chaque enregistrement du devis, une ligne saisie en
plus fait doublon (piège 199) ; un règlement créé par l'API sans ses échéances n'a ni écriture ni lettrage
(piège 194).

**Casse à NULL — `status_select` : la commande n'est dans AUCUN menu opérationnel**

Les deux menus principaux se partagent l'espace par exclusion mutuelle stricte —
`self.template = false and self.statusSelect < 3` (Devis) et `... = 3` (Commandes) — et un NULL ne
satisfait ni l'un ni l'autre.

```
[prouvé] status_select NULL      -> menu Devis : total=0 ; menu Commandes : total=0
         status_select = 1       -> menu Devis : total=1
```

Sur les 12 menus SaleOrder, la commande minimale n'apparaissait que dans **un seul**,
`sc.hist.sale.orders` (`self.template = false` seul). `[prouvé]`

**Champs requis par la VUE et nullables en base** : `client_partner`, `currency`,
`construction_order_type_select`. `[prouvé]` `required` de la vue fusionnée ; aucun des trois n'est
NOT NULL ni `required` d'entité. Une commande insérée en SQL sans eux s'ouvre (capture
`c3-so-900006.png`) mais affiche « Société Axelor / **Devise** / **Client** » vides et ne peut plus
être enregistrée depuis l'écran.

- `client_partner` NULL désactive en plus l'ajout et la suppression de lignes
  (`canNew`/`canRemove` de `saleOrderLineList`) : le devis n'est plus éditable normalement. `[statique]`

**Domaine filtrant — le volet chantier**

Les 4 menus du module construction filtrent `self.constructionIsConstructionOrder = true AND
self.constructionOrderTypeSelect = 1|2|3|4` (1 Devis initial, 2 Avenant, 3 Travaux supplémentaires,
4 Devis d'exécution).

> Attention : **`construction_order_type_select = 0` n'est pas une valeur de la sélection** — et c'est
> pourtant la valeur portée par les **14 commandes du socle** de cette base. Une commande à `0`,
> même avec `constructionIsConstructionOrder=true`, est absente des 4 menus chantier.
> Application directe de la règle 4.
> `[prouvé]` `is_co=true` + `type=1` → `total=1` ; `is_co=true` + `type=0` → `total=0` sur
> `... IN (1,2,3,4)`.

**namecolumn — `full_name` : posé par SQL, il SURVIT**

`SaleOrderManagementRepository` ne recalcule `full_name` que **si `client_partner` est renseigné**.
Conséquence pratique, contre-intuitive : sur une commande sans client, une valeur écrite par SQL
n'est jamais écrasée ; dès que le client est posé, elle l'est.

```
[prouvé] save REST avec fullName='ZZ SO TEMOIN FULLNAME', client_partner NULL
         -> status:0, et en base full_name = 'ZZ SO TEMOIN FULLNAME' (conservé)
```

Attention : `full_name` n'est **pas** ce que l'en-tête de la fiche affiche : l'en-tête rend `saleOrderSeq`
(vide sur un INSERT SQL) et le badge `importOrigin` (§0). `[prouvé]` même avec `full_name` posé,
l'en-tête affichait toujours « Commande client stress-c3 » (capture `c3-so-900006-fullname.png`).

**À laisser au moteur**

- `sale_order_seq` : la séquence n'est jamais consommée par un INSERT SQL — elle reste NULL, et
  l'en-tête de la fiche reste muet. `[prouvé]` après INSERT et après `action-sale-order-method-compute`,
  `sale_order_seq` est toujours NULL en base (piège 73).
- **Les totaux se calculent, ils ne s'écrivent pas.** `action-sale-order-method-compute` (le bouton
  standard, appelable en REST) renvoie `exTaxTotal`, `inTaxTotal`, `taxTotal`, `companyExTaxTotal`,
  `totalCostPrice`, `marginRate`, `markup`, `totalGrossMargin`… sur une commande dont la base ne
  portait aucun de ces champs. `[prouvé]` `status:0`, `values:` de 80+ clés.
  Attention : **Ce résultat suppose un contexte COMPLET, ce que la mesure ci-dessus ne disait pas.** Le même
  appel avec `{"context":{"id":N}}` rend `status: 0` et **zéro clé** — un succès vide (piège 132).
- Attention : **Mais l'appel de l'action SAUVEGARDE.** `action-sale-order-method-compute` a fait passer la
  **ligne** 900007 de `version=0` à `version=1` et rempli son `full_name` ; l'onLoad du projet a
  fait passer le projet de `version=0` à `version=2`. Un « bouton scriptable » (règle 12) n'est pas
  une lecture. `[prouvé]` **nouveau piège 97**.
- `version_number` : `default="1"`, `readonly` en vue — à poser à `1`. `[statique]`

### 98. Un tag technique peut être AFFICHÉ à l'écran : `import_origin` est rendu en badge dans l'en-tête de la Commande client

`[prouvé 9.1.6 / EE 8.2.3, 2026-09-03]` Le formulaire de `SaleOrder` porte, dans la vue fusionnée servie au
client, un champ `$importOrigin` rendu en badge dans l'en-tête
(`viewer.template = <Badge bg="primary">{importOrigin}</Badge>`) et un second `importOrigin` en lecture seule
dans le panneau « Canal de ventes ». Balayage des 15 formulaires du périmètre ventes et projet/temps :
**présent sur celui-là seulement**. Un tag de peuplement posé dans `import_origin` (« stress-c3 »,
« demo-c4 ») s'affiche donc en pleine démo sur chaque commande. Choisir pour ce champ une valeur qui peut être
vue (« Import », le nom du canal réel) ou tracer les lignes de démo par une autre colonne technique, et vérifier
sur toute nouvelle entité si le tag choisi est rendu par une vue.

### 113. Popup « Configurer Supply Chain » sur le devis même app `supplychain` inactive — garde `isApp()` manquante dans AOS

`[prouvé 9.1.6 / EE 8.2.3, 2026-09-08]` Ouvrir ou recharger un `SaleOrder` (même sur une base où
l'app `supplychain` n'est PAS activée) peut faire apparaître la popup « Veuillez configurer le
module Supply Chain pour la société … ». **Cause identifiée dans le code, pas une donnée
manquante au sens habituel** : `SaleOrderViewSupplychainServiceImpl.hideManagedLinesFields()`
(appelée par `getOnLoadAttrs`/`getOnNewAttrs`/`getCompanyAttrs`) invoque
`SupplyChainConfigServiceImpl.getSupplyChainConfig()` **sans jamais vérifier**
`appBaseService.isApp("supplychain")` — contrairement à la méthode voisine du même fichier,
`hideAvailabilityLabel()`, qui pose cette garde. Reproduit en direct par `POST /ws/action`
(`action-sale-order-method-onload` sur un `SaleOrder` existant) → `status:0, info: "Veuillez
configurer le module Supply Chain pour la société <X>"`. **C'est un défaut de garde livré par
AOS lui-même**, indépendant de l'activation de l'app — donc reproductible sur n'importe quelle
base où `supplychain_supply_chain_config` est vide, qu'elle ait ou non l'app installée.

**Ne pas confondre avec un vrai besoin Supply Chain.** `SupplyChainConfig` n'a aucune contrainte
NOT NULL hors `id`, et le bouton natif « Configurer Supply Chain »
(`action-supply-chain-config-record-default`) ne pose QUE la FK `company` avec les valeurs par
défaut du domain-model. Contournement minimal, sans activer l'app ni rien changer d'autre :

```sql
INSERT INTO supplychain_supply_chain_config (id, version, company, created_on, updated_on, created_by, updated_by)
SELECT nextval('supplychain_supply_chain_config_seq'), 0, c.id, NOW(), NOW(), 1, 1
FROM base_company c
WHERE NOT EXISTS (SELECT 1 FROM supplychain_supply_chain_config s WHERE s.company = c.id);
```

`out_sm_generation_select` reste à sa valeur par défaut (`1`, ≠ `4 = MANAGED_LINES`) : aucun champ
supplémentaire n'apparaît à l'écran, la popup disparaît et rien d'autre ne change visuellement.
À remonter à l'éditeur (comportement AOS constaté) : c'est un défaut de garde
corrigeable en amont, pas une limitation structurelle.

## 7. `sale_sale_order_line`

**Un seul menu la cible**, `sc.root.sale.order.lines.to.invoice`, et son domaine porte sur **deux**
enregistrements : `(self.invoicingState = 1 OR self.invoicingState = 2) AND self.saleOrder.statusSelect = 3`.

```
[prouvé] invoicing_state NULL                          -> total=0
         invoicing_state=1, saleOrder.statusSelect=1   -> total=0   (c'est le PARENT qui exclut)
         invoicing_state=1, saleOrder.statusSelect=3   -> total=1
```

Retenir la forme du piège : **une ligne peut être invisible à cause d'une colonne de son en-tête.**
Un audit qui ne regarde que la ligne conclut à tort.

**Champs requis par la vue et nullables en base** : `unit` (`requiredIf="typeSelect == 0"`).
`[statique]`

**Casse à NULL** : `product` — plusieurs services déréférencent `getProduct().getInAti()` /
`.getDescription()` sans garde au recalcul d'une ligne. `[statique]`

**Dénormalisation non resynchronisée**

- `product_name` (NOT NULL) est une recopie de `product.name` figée à la sélection : elle ne suit
  pas un renommage du produit. `[statique]`
- `main_sale_order` est **posé par le moteur au save**, pas par l'INSERT. `[prouvé]` mes deux lignes
  avaient `main_sale_order` NULL après INSERT et `= 900006` après le premier save moteur.
  Attention : Avec le module `axelor-construction`, cette FK n'est pas qu'une dénormalisation : le bilan
  d'affaire **agrège par elle**, et la laisser NULL donne un bilan à zéro, en silence. La poser dans
  l'INSERT, en même temps que `sale_order`. Décomposé DPGF à trois niveaux et formule du budget de
  temps : `entites-production-btp.md`, section « DPGF et bilan d'affaire ». *(2026-09-03)*

**namecolumn — `[non résolu]`**

`SaleOrderLine.fullName` a un corps CDATA `saleOrder.saleOrderSeq + '-' + productName`.
Ce que j'ai prouvé : **la colonne stockée part périmée et le reste jusqu'à un save de la ligne.**

```
[prouvé] INSERT SQL seul                       -> full_name NULL (ligne témoin 900018, version=0)
         UPDATE sale_sale_order SET sale_order_seq='ZZ-SO-900006'
                                                -> full_name reste '-ZZ Stress C3 Ligne' (périmé)
         save REST de la LIGNE                  -> full_name = 'ZZ-SO-900006-ZZ Stress C3 Ligne'
```

Ce que je **n'ai pas** tranché : l'analyse statique soutient que le *getter* recalcule à chaque
lecture, donc que l'écran afficherait toujours la valeur juste et que soigner la colonne serait
inutile. Mon protocole ne discrimine pas les deux hypothèses — entre les deux états ci-dessus je
n'ai pas relu la valeur *affichée*, et le cache L2 confond les deux lectures. **Position sûre en
attendant** : poser `full_name` en SQL au format `<sale_order_seq>-<product_name>` (coût nul, sans
risque) **et** ne pas compter sur un recalcul.

## 8. `account_invoice`

**Domaine filtrant** : `operation_type_select` est NOT NULL, donc pas de piège NULL — mais les 5
menus partitionnent par égalité exacte (3 = fact. client, 4 = avoir client, 1 = fact. fournisseur,
2 = avoir fournisseur, `operationSubTypeSelect = 6` = abonnement). Une valeur hors de ces cinq rend
la facture invisible partout.
`[prouvé]` la facture minimale (`operation_type_select=3`) apparaît dans `invoice.root.custinvoices`
(`total=1`) et dans aucun des 4 autres. **Aucun menu ne filtre `status_select`** : une facture
brouillon reste bien visible dans son menu. `[prouvé]` (le domaine ne mentionne pas `statusSelect`)

**Casse à NULL** : `payment_condition` / `payment_mode` — nullables, mais
`InvoiceServiceImpl.checkPreconditions()` lève à la ventilation : la facture reste bloquée à
« Validée », jamais « Ventilée ». `[statique]`

**namecolumn — `invoice_id`, pas `full_name`.** C'est `invoice_id` qui porte `namecolumn="true"` sur
`Invoice`. Il est `readonly` et nullable : posé comme numéro brouillon à la création, remplacé par
le numéro définitif à la ventilation. Un INSERT SQL sans lui rend la facture introuvable en m2o.
`[statique]` — `[prouvé]` que la colonne reste NULL sur un INSERT SQL et que la fiche s'ouvre quand
même, en-tête sans numéro (capture `c3-invoice-900008.png`). Le socle affiche `'#1'` sur une facture
et `'FC260001'` sur les suivantes : les deux formes coexistent en base, ne pas s'aligner sur la
première.

**Dénormalisation non resynchronisée** : `address_str`, `delivery_address_str` — recopies de
`Address.formattedFullName` jamais réconciliées. `[statique]`

**À laisser au moteur** : la ventilation (écritures comptables, numérotation définitive). Le SQL pose
un ÉTAT, pas la transition (règle 12).

## 9. `account_invoice_line`

**Aucun menu, et pas d'écran autonome — c'est le seul modèle du périmètre qui CASSE.**

Le groupe onLoad effectif descend dans `action-invoice-line-attrs-display-coefficient`, qui évalue
`__parent__.company` **sans garde de nullité**. Hors du formulaire Facture, `__parent__` est absent :

```
[prouvé] /ws/action sur l'onLoad, contexte = la ligne seule -> status:-1
  causeStack: java.lang.NullPointerException: Cannot get property 'company' on null object
    at ActionAttrs.evaluate(ActionAttrs.java:66)
  action fautive isolée par bissection sur les 12 sous-actions du groupe :
    action-invoice-line-attrs-display-coefficient
    <attribute name="hidden" expr="eval: !__repo__(AccountConfig).findByCompany(__parent__.company)?.isInvoiceCoefficientEnabled" for="coefficient"/>
  même appel avec _parent = la facture 900008 -> status:0, {"attrs":{"coefficient":{"hidden":true}}}
```

Conséquence pour la production de données : la ligne de facture ne se vérifie **que** par le panneau
`invoiceLineList` de sa facture. Ne pas budgéter de contrôle visuel autonome, et ne pas conclure à
une donnée fautive en voyant ce `status:-1`.

- **Champs requis par la vue et nullables en base** : `price`, `qty`, `in_tax_price`. `[prouvé]`
- **Casse à NULL** : `account` — posé sans exception à la génération, le blocage n'apparaît qu'à la
  génération de l'écriture comptable. `[statique]`
- **Dénormalisation non resynchronisée** : `product_name`, `product_code`, `unit`. `[statique]`
- **namecolumn** : sans objet, `InvoiceLine` n'a pas de `namecolumn`. `[statique]`
- **À laisser au moteur** : `coefficient` (`default="1"`, repli `BigDecimal.ONE`). `[statique]`

---

## Ce que ce protocole n'a PAS couvert

- Les **kanbans** et **cards** : je n'ai testé que les grilles et les formulaires. Un `columnBy`
  NULL retire l'enregistrement de toutes les colonnes du kanban — mécanisme réel mais **non
  reproduit ici**.
- Les **search-filters** (`view-param name="search-filters"`) : ce sont des filtres proposés à
  l'utilisateur, pas des filtres appliqués d'office. Non testés, sans effet sur la visibilité par
  défaut.
- Les **permissions** : tout a été mesuré en `admin`. Un profil métier peut retirer des écrans que
  ce protocole a vus pleins (voir `axelor-droits-expert`).
- `construction_construction_dgd` : table vide dans cette base, hors périmètre.

### 104. Créer une commande de vente par API : quatre champs seulement, dont `creation_date` que rien n'annonce

Pour monter une commande de travail par `POST /ws/rest` (jeu d'essai, fixture de recette, point de départ d'une chaîne), le minimum réellement exigé par les contraintes JPA est : `company`, `clientPartner`, `currency` et **`creation_date`**. Ce dernier est un `NotNull` que ni les exemples ni les écrans ne rendent visible — l'oubli rend une `ConstraintViolationException` sur `propertyPath=creationDate`, lisible mais déroutante puisqu'on n'a jamais saisi ce champ à la main.

Deux détours à ne pas prendre : `/ws/rest/<model>/<id>/copy` rend un payload que `/ws/rest` refuse ensuite (« invalid request »), et cloner une commande de démo traîne ses lignes et ses totaux. Créer nu, puis ajouter les lignes, est plus court et plus prévisible.

Enchaînement des transitions, chacune en `/ws/action` séparée : `action-sale-order-method-check-before-finalize`, `action-sale-order-method-finalize-quotation`, `action-sale-order-method-check-before-confirm`, `action-sale-order-method-confirm` — statut 1 → 2 → 3. Le contrôle avant confirmation rend une **alerte** (et non une erreur) quand le total vaut zéro : une commande de démo sans prix se confirme quand même, mais l'écran demande une confirmation que l'API doit ignorer sciemment.
**Et le même piège existe un cran plus bas, sur la LIGNE.** `[prouvé REST 9.1.3 / AOP 8.2.2, 2026-09-22]` `sale_sale_order_line` — comme `purchase_purchase_order_line` — n'a **qu'une seule colonne obligatoire au-delà de l'identifiant : `product_name`**. Un `POST /ws/rest` sans elle lève une `jakarta.validation.ConstraintViolationException` **au moment de la persistance**, et son message **ne nomme pas la colonne** — contrairement à celui de `creationDate` ci-dessus, qui porte son `propertyPath`. Le réflexe est de chercher du côté du produit ou du prix ; la cause est la recopie du libellé, décrite en §7 (« dénormalisation non resynchronisée »).

---

## Piloter les ventes par l'API — mesures du 2026-09-22

> `[prouvé REST 9.1.3 / AOP 8.2.2]` sur une passe de **120 commandes de vente**, 1 à 7 lignes chacune.
> Les deux pièges qui suivent valent **aussi pour les achats** (mêmes actions, préfixe `purchase`) ;
> `entites-achats.md` y renvoie plutôt que de les redire.

### 131. Un `POST /ws/rest` ne déclenche AUCUN `onChange` : la ligne sort sans prix ni taxe

Une ligne créée par REST est exactement ce qu'on a écrit — et rien de plus. Les `onChange` de la vue,
qui à l'écran remplissent le prix, la taxe, l'unité et le libellé dès qu'on choisit un article, **ne
tournent pas**. Résultat : des lignes à 0,00 €, sans `taxLineSet`, que le calcul d'en-tête somme
ensuite fidèlement à zéro.

**Remède** : appeler d'abord, **une fois par article**, l'action de remplissage de la ligne.

| Domaine | Action |
|---|---|
| Vente | `action-sale-order-line-method-get-product-information` |
| Achat | `action-purchase-order-line-method-get-product-information` |

Contexte à passer : `{product:{id}, qty, _parent:{…la commande…}}` — le `_parent` n'est pas décoratif,
la société, la devise et le régime de taxe s'y lisent. La réponse rend `price`, `inTaxPrice`,
`taxLineSet`, `unit`, `productName` et `companyCostPrice`.

**Le résultat se met en cache par article.** *Mesuré : sur 100 commandes de 1 à 7 lignes, **77 appels
au lieu de 400**.* Le cache est légitime parce que la réponse ne dépend que de l'article et du
contexte société/devise, constants sur une passe ; le recalculer par ligne est du temps de passe pur.
*Non mesuré* : le comportement quand une même passe traverse plusieurs sociétés ou plusieurs devises —
la clé de cache devrait alors les inclure.

Attention : Rappel du piège 97 : cet appel **écrit**. Il entre dans le périmètre de nettoyage.

### 132. Une action de calcul d'en-tête appelée avec `{id}` rend `status: 0` et zéro clé

`action-sale-order-method-compute` et `action-purchase-order-method-compute` appelées avec
`{"context":{"id":N}}` répondent **`status: 0`** — un succès — et rendent **zéro clé**. Aucun total.
Aucune erreur. Un script qui ne teste que le statut conclut que le calcul a eu lieu.

L'action lit ses données **dans le contexte**, pas en base : il lui faut l'enregistrement **entier**.

1. `POST /ws/rest/<modèle>/<id>/fetch` (corps `{}` ou `{"fields": [...]}` ; en GET : 405) ;
2. passer l'enregistrement complet retourné comme `context` de l'action ;
3. les totaux reviennent dans `values` — **à réenregistrer** par un `POST` portant `id` **et**
   `version` (sans la version, le save est rejeté en conflit optimiste).

C'est la nuance qui manquait à la puce « Les totaux se calculent » du §6 : elle mesurait le cas
favorable sans dire à quelle condition il l'était.
