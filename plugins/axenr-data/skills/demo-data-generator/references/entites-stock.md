# Entités — stock (mouvement, ligne d'emplacement, réception, chaîne moteur)

> **Couche UI-critical uniquement.** Ce que ni le schéma (`scripts/shape-fiche.sh`, `introspect.sh`)
> ni un enregistrement modèle ne donnent. Les NOT NULL, les FK et les taux de remplissage ne sont
> PAS ici : ils s'introspectent au moment de produire (règle 1).
>
> **Établie empiriquement le 2026-09-07** sur `<base>` — AOS 9.1.6. Protocole :
> lecture d'un dossier d'hypothèses
> (10 items, produit en lecture seule sans écran), réfutation/confirmation de chacun contre la base
> réelle, décompilation à la volée (CFR) des classes `PurchaseOrderStockServiceImpl` et
> `StockLocationLineServiceImpl` (`axelor-supplychain`/`axelor-stock` 9.1.6) pour localiser le
> mécanisme exact, création d'une commande fournisseur jetable + exécution réelle de la chaîne
> moteur (`/ws/action`) jusqu'à réalisation, test destructif d'un mouvement inséré en SQL brut
> (créé puis supprimé), et vérification REST du domaine servi par le menu « Supplier arrivals ».
>
> **Marquage** : `[prouvé REST/moteur]` = appel HTTP authentifié réellement exécuté, effet observé
> en base ET/OU via l'endpoint que le front consomme ; `[prouvé source]` = lu dans le bytecode
> décompilé du service réellement déployé sur cette base (pas une doc, le `.class` chargé) ;
> `[SCHEMA]` = compté en SQL ; `[SUPPOSE]` = ni l'un ni l'autre. **Aucun item ne porte
> `[prouvé écran]`** — navigateur indisponible (extension déconnectée, profil Playwright
> verrouillé), constaté deux fois ce jour, cf. « Ce que ce protocole n'a PAS couvert ».

**Pièges déjà existants que cette fiche concerne** (numéros inchangés) :

- 12. Le SQL pose un état, ne simule pas une transition — confirmé ici de la manière la plus
  stricte possible : `stock_stock_location_line.current_qty` est un **cache dérivé** que le moteur
  recalcule à chaque mouvement réalisé, et le moteur lui-même **refuse d'avancer** si ce cache est
  déjà dans un état incohérent (voir §0, nouveau cas concret).
- 73. Consommer la séquence après insertion — vérifié ici sur **deux** horloges distinctes en
  parallèle : la séquence PK Postgres (`stock_stock_move_seq`) et la séquence métier Axelor
  (`stock_move_seq`, format `DO0001`/`RO0001`/`ISM0001` par famille `type_select`).
- 10. Aucun nom au hasard — le fournisseur et le produit choisis pour le test de chaîne
  (SASAKI Components / Imprimante Jet d'encre) sont repris du catalogue fournisseur existant
  (`purchase_supplier_catalog`), pas inventés.

---

## 0. Ce que le protocole a établi de transverse

| Constat | Preuve |
|---|---|
| **`current_qty` n'est PAS universellement fiable comme « somme des mouvements réalisés »** — le dossier d'hypothèses l'affirmait vérifié sur 8 couples produit/emplacement ; élargi à **tous** les couples de la base (63), **5 lignes divergent** (produits 18, 20, 36, aux emplacements Entrepôt et Client). Le mécanisme reste correct pour tout produit ayant reçu un inventaire initial cohérent (H1 tient à 58/63) — mais la base porte une **anomalie pré-existante, non introduite par cette mission**, sur 3 produits jamais couverts par l'inventaire ISM0001. | `[SCHEMA, prouvé par requête]` produit 20 : `current_qty`(Entrepôt)=-1 vs somme réalisée calculée=-3 (écart +2) ; `current_qty`(Client)=0 vs +3 attendu (écart -3). Requête de falsification exécutée sur les 65 lignes, pas sur un échantillon de 8. |
| **Cette anomalie pré-existante N'EST PAS cosmétique : le moteur lui-même la détecte et refuse d'empiler un nouveau mouvement sur un produit dans cet état.** Tenter une réception moteur sur le produit 20 (déjà à `current_qty=-1`, donc négatif sur un emplacement réel) échoue avec un message métier trompeur (« stocks insuffisants pour réaliser la **livraison** », alors qu'il s'agit d'une réception) — **la même action, sur un produit sain (id=19), réussit immédiatement.** Cause localisée dans le bytecode déployé : `StockLocationLineServiceImpl.checkStockMin()` lève dès que `current_qty < 0` sur un emplacement `type_select != 3` (non virtuel), **quel que soit le sens du mouvement** — le texte du message (« livraison ») est un faux ami, la condition est générique. | `[prouvé source + REST]` `StockLocationLineServiceImpl.class` décompilé (CFR), méthode `checkStockMin` l.161 ; `POST /ws/action/action-purchase-order-create-stock-move` sur ma commande ACH0019 (produit 20) → `{"info":{"message":"...insuffisants pour réaliser la livraison"}}`, **0 mouvement créé** (vérifié en base) ; même appel sur ma commande ACH0020 (produit 19, sain) → succès, vue `StockMove` id=23 retournée. |
| **La chaîne moteur complète « commande fournisseur → mouvement → quantité » fonctionne de bout en bout et a été exécutée intégralement sur un enregistrement créé pour cette mission.** Étapes et effets observés, dans l'ordre : (1) commande fournisseur posée en SQL, statut Validated ; (2) `action-purchase-order-create-stock-move` → crée le mouvement **Planifié**, `stock_move_seq='RO0007'` déjà posé (séquence consommée **à la création**, pas à la réalisation), `name` déjà au format `<seq> - <code partenaire> - <nom partenaire>` ; (3) `action-stock-move-method-realize` → `status_select` 2→3, `real_date` posé au jour du jour, `current_qty` de l'emplacement réel **+5** (285→290, exactement la quantité reçue), `avg_price` recalculé (0→27.83, coût moyen pondéré), une ligne `stock_stock_location_line_history` créée automatiquement, **une nouvelle ligne d'emplacement créée à la volée** pour le couple (produit, emplacement virtuel Fournisseur) qui n'existait pas avant (current_qty=-5, miroir exact de la réception), jonction M2M `stock_stock_move_purchase_order_set` peuplée automatiquement. | `[prouvé REST + SQL]` séquence complète exécutée sur commande id=21 (ACH0020) → mouvement id=23 (RO0007) → `GET`/recherche REST confirmant `current_qty` avant (285.0000000000) / après (290.0000000000) sur `stock_stock_location_line` id=2 ; requêtes SQL avant/après jointes en annexe §2. |
| **Un mouvement inséré directement en SQL (contournement du moteur) N'EST PAS invisible à l'écran — contrairement à l'attente initiale (H3) calquée sur le piège `full_name` de `SaleOrder`/`Address` — il reste SERVI par la recherche du domaine exact du menu « Supplier arrivals », mais avec `name`/`stockMoveSeq` à `null`.** Nuance importante par rapport au piège 71 (dénormalisation composée qui rend NULL = invisible) : `StockMove.name` n'est pas une concaténation recalculée en `SELECT`, c'est un champ simple posé par le service au moment de la création — sa colonne NULL ne fait donc pas planter un index de recherche ni disparaître la ligne, elle produit une **ligne fantôme sans numéro de pièce** dans le grid (même famille de piège que les 85 tâches à `full_name` NULL du 2026-09-03, mais avec un symptôme différent : dégradé, pas invisible). | `[prouvé REST]` test destructif exécuté et nettoyé : `INSERT` d'un mouvement id=24 (`status_select=1`, aucune séquence), recherche REST avec le domaine exact du menu `stock.root.internal` (`self.typeSelect = :_typeSelect`) → `total:1`, la ligne revient avec `"name": null, "stockMoveSeq": null` — servie, pas absente. Enregistrement supprimé après observation (`DELETE FROM stock_stock_move WHERE id=24`), aucun effet sur le stock réel (jamais planifié ni réalisé). |
| **Les 6 emplacements sont bien un singleton de configuration société, un-à-un avec les champs nommés de `stock_stock_config`** — H4 était `SUPPOSE`, désormais `SCHEMA` (confirmé par jointure directe, pas par ressemblance de nom). | `[SCHEMA]` `stock_stock_config` id=1 : `supplier_virtual_stock_location=3`, `customer_virtual_stock_location=2`, `inventory_virtual_stock_location=4`, `production_virtual_stock_location=5`, `waste_stock_location=6`, et **4 champs distincts** (`receipt_default`, `component_default`, `finished_products_default`, `pickup_default`, `quality_control_default`) qui pointent tous vers le même id=1 (Entrepôt principal). |
| **Le mouvement `ISM0001` est bien la matérialisation directe de l'inventaire id=1, par une FK explicite** — H9 était `INFERE`, désormais `SCHEMA`. | `[SCHEMA]` `stock_stock_move.inventory = 1` sur le mouvement `ISM0001` (id=1) — colonne trouvée sur `StockMove`, pas sur `Inventory` (le sens de la FK va du mouvement vers l'inventaire, pas l'inverse). |

---

## 1. `stock_stock_move` / `stock_stock_move_line`

**Point d'entrée moteur, chaîne complète, nommé et testé**

| Étape | Point d'entrée REST | Effet observé |
|---|---|---|
| 1. Créer le(s) mouvement(s) depuis une commande fournisseur validée | `POST /ws/action/action-purchase-order-create-stock-move`, contexte `{"_model":"...PurchaseOrder","id":<id>}` | Crée un `StockMove` **Planifié** (`status_select=2`), `stock_move_seq` et `name` déjà posés (voir §0). Si la config qualité est active (`quality_control_default_stock_location`), peut créer un **second** mouvement de contrôle qualité — non observé ici (config pointe vers le même entrepôt, pas de split). `[prouvé REST]` |
| 2. Réaliser le mouvement | `POST /ws/action/action-stock-move-method-realize`, contexte `{"_model":"...StockMove","id":<id>}` | `status_select` 2→3, `real_date` posé, `current_qty`/`future_qty`/`avg_price` des lignes d'emplacement concernées recalculés, historique créé. **Aucun appel `plan` séparé nécessaire** : `createStockMoveFromPurchaseOrder` appelle déjà `stockMoveService.plan()` en interne à l'étape 1. `[prouvé REST]` |
| Côté vente (non exécuté cette mission, localisé par analogie de nommage confirmée dans le dossier d'hypothèses) | `action-supplychain-sale-order-create-stock-move` | Même patron attendu (création + plan), non testé — `[SUPPOSE]` par transposition, à vérifier avant usage. |

**Casse à NULL / dégradation UI (pas invisibilité)**

- `stock_move_seq` / `name` — posés par le service **à la création**, jamais recalculés à la volée
  (contrairement à `full_name` sur `Partner`/`SaleOrder`). Un `INSERT` SQL direct les laisse `NULL` :
  la ligne reste **servie** par toute recherche de menu (testé sur le domaine exact de « Supplier
  arrivals » et « Internal Stock Moves »), mais s'affiche sans numéro de pièce — dégradation visible,
  pas suppression. `[prouvé REST]`
- `origin` — résolu vers le numéro de pièce commerciale (`purchase_order_seq`/`sale_order_seq`) ou
  vers `inventory_seq` pour un mouvement d'inventaire, jamais vers un id technique. `[SCHEMA,
  confirmé sur 18 mouvements dont le mien]`
- `conformity_select` — la valeur `1` de la sélection `stock.move.line.conformity.select` n'a pas de
  libellé en base (`meta_select_item` sans `title` pour cette valeur) — non retesté à l'écran cette
  mission (hérité de l'hypothèse H5 du dossier d'hypothèses, `[SUPPOSE]`, cf. limites).

**Domaine filtrant qui exclut le NULL/false**

| Menu / dashlet | Prédicat | Conséquence |
|---|---|---|
| `stock.root.suparrivals` (Supplier arrivals) | `self.typeSelect = 3 AND self.isReversion = FALSE` | Aucun filtre sur `status_select` dans le domaine lui-même — un mouvement Draft/Annulé apparaît aussi dans la recherche brute ; le filtrage par statut vient du `search-filters` (`supplier-arrivals-filters`, non ouvert cette mission). `[prouvé REST]` pour la partie domaine. |
| `stock.root.internal` (Internal Stock Moves) | `self.typeSelect = 1` | Idem, aucun filtre de statut dans le domaine. Testé avec mon mouvement Draft sans séquence : servi. `[prouvé REST]` |
| `purchase.root.purchase.orders.without.stock.move` | `self.statusSelect = 3 AND self IN (... p.receiptState != 3 ...) AND self.id NOT IN (SELECT po.id FROM StockMove s JOIN s.purchaseOrderSet AS po WHERE s.statusSelect = 2)` | C'est le menu qui aurait montré mes 2 commandes de test **avant** que je ne génère leur mouvement — confirme le terrain de la source 5 de la mission (11 SO / 1 PO sans mouvement) est bien exposé nativement, pas une déduction. `[SCHEMA, lu en source `meta_action`]` |

## 2. `stock_stock_location_line` — MOTEUR, avec une réserve mesurée

**Verdict inchangé sur le fond** (MOTEUR, jamais de `UPDATE` direct — hypothèse H1 / règle 12),
**mais la garantie n'est pas absolue sur cette base** : 5 lignes sur 65 portent déjà un `current_qty`
qui ne correspond à aucune reconstruction possible depuis les mouvements réalisés existants (§0).
Conséquence pratique pour la suite du skill : **avant de générer un mouvement moteur sur un
produit existant, vérifier que ses lignes d'emplacement ne portent pas déjà cette anomalie** —
sinon le moteur refusera silencieusement (message « livraison » trompeur pour une réception) et il
faudra changer de produit-cible, pas insister.

Requête de vérification à rejouer avant toute génération sur un produit déjà en stock :

```sql
WITH mv AS (
  SELECT sml.product, sml.to_stock_location AS loc, sum(sml.real_qty) AS q
  FROM stock_stock_move_line sml JOIN stock_stock_move sm ON sm.id = sml.stock_move
  WHERE sm.status_select = 3 GROUP BY 1,2
), mv_out AS (
  SELECT sml.product, sml.from_stock_location AS loc, -sum(sml.real_qty) AS q
  FROM stock_stock_move_line sml JOIN stock_stock_move sm ON sm.id = sml.stock_move
  WHERE sm.status_select = 3 GROUP BY 1,2
), net AS (
  SELECT product, loc, sum(q) AS q FROM (SELECT * FROM mv UNION ALL SELECT * FROM mv_out) x GROUP BY 1,2
)
SELECT sll.product, sll.stock_location, sll.current_qty, net.q AS net_calc
FROM stock_stock_location_line sll JOIN net ON net.product = sll.product AND net.loc = sll.stock_location
WHERE sll.current_qty <> net.q;
```

- **Une ligne d'emplacement est créée à la volée par le moteur** au premier mouvement touchant un
  couple (produit, emplacement) qui n'en avait pas encore — pas besoin de la pré-créer en SQL.
  `[prouvé REST/SQL]` (ligne id=69, produit 19 × emplacement Fournisseur, apparue après ma
  réception).
- `avg_price` — recalculé par le moteur à la réalisation, jamais posé en SQL (règle 12 confirmée
  une fois de plus, avec un exemple chiffré : 0 → 27.83 après une seule réception).

## 3. `purchase_purchase_order` — chaîne stock (complément à `entites-achats.md`)

- Le champ `stock_location` du header (pas de la ligne) détermine la destination de la réception
  quand `is_manage_stock_location_on_stock_move_line` est désactivé — c'est le cas observé ici
  (toutes mes lignes ont hérité de `stock_location=1` du header sans le poser explicitement sur la
  ligne). `[prouvé source]` (`getPurchaseOrderLineMap`, `PurchaseOrderStockServiceImpl.class`).
- `receipt_state` du header et des lignes, et `received_qty` des lignes, **sont mis à jour à la
  réalisation du mouvement** quand l'app Supply chain est active — pas à sa génération
  (`StockMoveServiceSupplychainImpl.realizeStockMove` l.179-181 et l.206-223 ;
  `PurchaseOrderReceiptStateServiceImpl` l.96-140 : `received_qty` = somme des lignes de mouvement
  réalisées ; `[prouvé source 9.1.3]`). *Corrigé le 2026-09-24 : cette fiche affirmait le contraire.
  Relu en base sur la commande de test elle-même (ACH0020, `<base>`, 9.1.6) :
  `receipt_state` 3, `received_qty` 5, écrits dans la même seconde que la réalisation de RO0007.*
  Non retesté après un retour fournisseur.

## 4. Couche UI-critical — établie par test, verdicts affinés

| Colonne | Effet réel constaté | Preuve |
|---|---|---|
| `stock_stock_move.stock_move_seq` / `name` NULL | **Servi, dégradé** (ligne fantôme sans numéro), **pas invisible** — infirme l'hypothèse par analogie H3/H10 du dossier d'hypothèses qui anticipait une invisibilité façon `full_name` | `[prouvé REST]` §0 |
| `stock_stock_location_line.current_qty` négatif sur un emplacement réel (`type_select≠3`) | **Bloque le moteur** pour tout nouveau mouvement touchant ce couple produit/emplacement, avec un message qui ne nomme pas la vraie cause | `[prouvé source + REST]` §0 |
| `stock_stock_location_line.current_qty`/`future_qty` sur un couple produit/emplacement jamais mouvementé | La ligne **n'existe simplement pas** avant le premier mouvement — pas de ligne à `0`, absence pure. Un panneau qui listerait « tous les emplacements » pour un produit neuf serait donc plus court que les 6 emplacements de configuration, pas rempli de zéros. | `[prouvé REST/SQL]` (ligne id=69 apparue seulement après le premier mouvement touchant ce couple) |
| `stock_stock_move.status_select` dans le domaine des menus « Supplier arrivals »/« Internal Stock Moves » | **Non filtrant au niveau du domaine lui-même** — un mouvement Draft ou Annulé resterait dans la liste brute ; le filtrage par statut, s'il existe à l'écran, vient d'un `search-filters` non ouvert cette mission | `[prouvé REST]` pour la partie domaine, `[NON TESTABLE ICI]` pour le rendu des onglets de filtre |
| `stock_stock_move_line.conformity_select=1` sans libellé | Non retesté par cette mission (hérité du dossier d'hypothèses) | `[SUPPOSE]`, cf. limites |

## 4 bis. Pièce « reçue », « livrée » ou OF « démarré » sans mouvement — mesures du 2026-09-23

### 143. Un historique qui marque des pièces reçues, livrées ou fabriquées SANS mouvement de stock se voit au premier clic

`[prouvé 9.1.3 / AOP 8.2.2, 2026-09-23, démo industrielle]` Historique de 10 affaires machines posé en SQL
(pour tenir des coûts exacts) : **27 commandes fournisseur « reçues » ou « partiellement reçues »**
(558 lignes à quantité reçue), **25 OF démarrés ou terminés**, **7 commandes clients « livrées » ou
« partiellement livrées »** — et **0 mouvement de stock**. Sur la même base, les pièces natives en ont
toutes : 6/6 commandes reçues, 135/135 OF démarrés, 7/7 commandes livrées. L'utilisateur l'a trouvé en
naviguant : « partiellement reçue, des quantités reçues, mais aucun mouvement rattaché ». Un OF
**planifié** par le moteur a déjà les siens : 115 des 117 OF planifiés hors historique (archivés
compris ; les 2 autres ont été posés en SQL, sans composant ni opération), 0 sur les 15 OF planifiés
de l'historique (mesuré le 2026-09-24).

**Pourquoi c'est un piège.** `receipt_state` / `received_qty` et `delivery_state` sont les
**conséquences** d'un mouvement réalisé par le moteur (réception, livraison : app Supply chain active,
`StockMoveServiceSupplychainImpl.realizeStockMove` l.179-223, 9.1.3 ; §3). Un OF, lui, porte ses
mouvements **dès la planification** : consommation et production créées et planifiées
(`ManufOrderPlanServiceImpl.updateStatusToPlan` puis `planStockMoves`, l.186-223, 9.1.3). La
consommation est réalisée au démarrage si la gamme porte `stock_move_realize_order_select` = 0,
sinon à la fin (`ManufOrderWorkflowServiceImpl.start` l.140-146 et `finishManufOrder` l.235). Le
défaut à la création est 1, « à la fin » (`ProdProcess.xml` l.46), mais **une gamme à NULL se lit 0,
« au démarrage »** (getter `getStockMoveRealizeOrderSelect`, `ProdProcess.java` l.609-610, classe
servie identique) : sur `<base>`, 241 gammes sur 247 à NULL, et 32 des 33 OF natifs en cours sur
ces gammes ont leur consommation réalisée. Écrire ces états en SQL simule la transition
(règle 12). Tout ce qui lit les mouvements se
contredit alors : bon de réception et BL introuvables, onglets « mouvements » des OF vides, stocks des
composants jamais entrés ni sortis, « Réceptions attendues » et « Expéditions à préparer » muettes.

**À faire, dans cet ordre :**
1. jouer la chaîne par le moteur — réception : `action-purchase-order-create-stock-move` puis
   `action-stock-move-method-realize` (§0) ; OF : démarrer puis terminer (pièges 125 et 126) ;
   livraison : générer puis réaliser le BL (`action-supplychain-sale-order-create-stock-move`,
   **non testé** : §1 et §5) ;
1 bis. pour un OF **terminé** seulement, et seulement si l'écran à montrer est le journal de
   consommation ou la traçabilité des lots, pas les niveaux de stock : construire la chaîne en SQL selon
   le piège 15 — mouvements IN et OUT réalisés (`status_select` 3) avec séquence et `name`, lignes
   `consumed_manuf_order` / `produced_manuf_order`, FK `in_manuf_order` / `out_manuf_order` /
   `manuf_order` (piège 27). Ce que cette voie ne fait pas : les lignes d'emplacement (`current_qty`,
   `avg_price`, historique) ne bougent pas — la requête du §2 le montre — et aucune feuille de coût n'est
   produite : à livrer comme une limite (étape 3) ;
2. à défaut, ne pas poser l'état : commande validée **non** reçue ; OF **brouillon**, ou planifié
   **par le moteur** (planifié en SQL, il n'a pas les mouvements que la planification crée) ;
3. si le raccourci est assumé faute de temps, c'est une **limite visible** : la livrer dans le message
   de fin avec les écrans à ne pas ouvrir et la phrase à dire (piège 149), pas seulement dans un rapport.

**Leçon du 24/09** (retex démo, pièges 143 et 149) : une limite « annoncée si on la demande » devient
une limite découverte dès que le client ouvre un écran au hasard. Un historique qui porte des statuts
de flux physique se joue donc par le moteur (étape 1, ou 1 bis dans ses conditions), ou ses objets sont
exclus des écrans de la démo — et la limite s'annonce d'office AVANT la séance, pas sur demande.

Voir aussi le piège 15 (`entites-production-btp.md`) : chaîne de stock d'un OF terminé construite en
SQL.

**Garde :** dimension 13 de `scripts/audit-completeness.sql`, invariants G4 (achat reçu ou partiel sans
mouvement), G5 (vente livrée ou partielle sans mouvement), G6 (OF planifié, démarré ou terminé sans
ligne de consommation, portée par l'OF ou par l'opération). Mesurés 27 / 7 / 42 sur `<base>`
(G6 : les 40 OF du lot et les 2 OF posés en SQL), 0 sur les pièces natives. Garde **à cliquet** : le
premier passage prend les compteurs comme référence, défauts compris, et une hausse n'émet qu'une
ligne `ERROR` (psql sort à 0) — lancer l'audit une fois avant la première écriture (SKILL.md, Phase 4,
dimension 13).

## 5. Ce que ce protocole n'a PAS couvert

- **Aucun écran ouvert au navigateur** — extension de navigateur déconnectée, profil Playwright
  verrouillé par un processus concurrent, les deux essayés, aucun n'a abouti (contrainte connue,
  signalée dans `entites-achats.md` §7 pour le même jour). Tout ce qui est marqué `[prouvé REST]`
  est un appel HTTP authentifié réel contre l'endpoint que le front-end React appelle
  (`/ws/action`, `/ws/rest`), réponse JSON observée — preuve du mécanisme serveur et du domaine
  servi, **pas** du rendu pixel (disposition, couleur, tri, onglets de `search-filters`).
- **Le mécanisme de mouvement de contrôle qualité** (`qualityStockMove`, second mouvement créé en
  parallèle si `controlOnReceipt` est actif sur le produit) n'a été ni déclenché ni observé — les
  2 produits testés (19 et 20) ont `control_on_receipt=false`. Lu en source uniquement.
  `[prouvé source]` pour l'existence du mécanisme, `[NON TESTABLE ICI]` pour son effet réel.
- **Le chemin symétrique côté vente** (`action-supplychain-sale-order-create-stock-move`, livraison
  client) n'a pas été exécuté — seule la réception fournisseur l'a été. Le nom de l'action est
  confirmé présent (`meta_action`), son comportement exact non testé.
- **`stock_stock_move_line.conformity_select`, `stock_partner_stock_settings`,
  `stock_stock_rules`, `stock_tracking_number`** : hors périmètre d'exécution de cette mission
  (0 ligne ou satellites non touchés par la chaîne testée) — verdicts hérités du
  dossier d'hypothèses sans reformulation.
- **`receipt_state` après un retour fournisseur ou un cycle complet réception→facturation** —
  non testé (§3, corrigé le 2026-09-24 : la réalisation met bien l'état à jour), recoupe le domaine
  achats/compta hors mandat strict de cette mission.
- **Le comportement exact des `search-filters` par statut** sur les 2 menus testés — seul le
  `<domain>` de l'`action-view` a été vérifié par REST, pas les onglets de filtre additionnels
  qu'un client React construit par-dessus.
