# Entités — achats (commande fournisseur, ligne, tarif fournisseur, rattachement affaire)

> **Couche UI-critical uniquement.** Ce que ni le schéma (`scripts/shape-fiche.sh`, `introspect.sh`)
> ni un enregistrement modèle ne donnent. Les NOT NULL, les FK et les taux de remplissage ne sont
> PAS ici : ils s'introspectent au moment de produire (règle 1).
>
> **Établie empiriquement le 2026-09-07** sur `<base>` — AOS 9.1.6 / module local
> `axelor-construction` 9.1.0-SNAPSHOT. Protocole : lecture d'un dossier
> d'hypothèses (10 items, produit en lecture seule sans écran), réfutation de chacun contre la base réelle, lecture directe des sources Java
> (`PurchaseOrderController`, `ConstructionRafComputeServiceImpl`) et des dashlets SQL
> (`ConstructionDashboard.xml`) pour localiser le mécanisme de calcul du déboursé achat, création
> de 10 commandes fournisseur BTP + tests via REST authentifié (`/ws/action`, `/ws/rest`,
> `/ws/meta/custom/{name}`).
>
> **Marquage de chaque item** : `[prouvé REST]` = appel HTTP authentifié réellement exécuté sur le
> serveur, réponse observée (recherche, action-method, dataset de dashlet) ; `[prouvé écran]` =
> ouverture navigateur, capture — **aucun item de cette fiche ne porte ce marquage**, le navigateur
> n'était pas disponible dans cette session (voir « Ce que ce protocole n'a PAS couvert ») ;
> `[SCHEMA]` = compté en SQL ou lu dans un domaine de menu ; `[INFERE]` = lu en source Java, non
> exécuté ; `[SUPPOSE]` = ni l'un ni l'autre.

**Pièges déjà existants que cette fiche concerne** (numéros inchangés) :

- 4. Aucune sélection inventée : `0` est souvent invalide — confirmé ici sur
  `construction_market_type_select` (H-ACH-02), non corrigé sur les 9 commandes pré-existantes
  (règle de sûreté : je ne touche pas un enregistrement que je n'ai pas créé), posé à `1` (Private)
  sur les 10 commandes neuves après vérification du client réel de chaque affaire.
- 2 / 88. Une mesure sans son unité est pire qu'un champ vide — `purchase_purchase_order_line.unit`
  posé depuis `base_product.unit` (jamais `purchases_unit`, vide sur tout le catalogue produit,
  y compris les 391 articles du socle — pas une lacune propre aux achats).
- 10. Aucun nom au hasard — 2 fournisseurs BTP créés (`NORMATER Négoce BTP`, `ELEXA Fluides &
  Réseaux`), aucun des 21 fournisseurs existants n'étant compatible avec un achat de matériaux de
  construction (tous IT/ESN du socle AOS).
- 73 / 12. Consommer la séquence après insertion, jamais avant — `purchase_purchase_order_seq`,
  `_line_seq`, `_line_tax_seq`, `base_partner_seq` avancés par `setval(..., max(id))` en fin de
  script, jamais en tête.
- 90. `meta_action`/`meta_view` peuvent porter des doublons — non revérifié ici, hors périmètre.
- 131 / 132. Un `POST /ws/rest` ne déclenche aucun `onChange` ; une action de calcul appelée avec
  `{id}` rend un succès vide — **les deux valent à l'identique pour les achats**, avec les actions
  préfixées `purchase`. Écrits une seule fois, dans `entites-ventes.md`.

---

## 0. Ce que le protocole a établi de transverse

| Constat | Preuve |
|---|---|
| **Le déboursé achat d'une affaire se lit sur DEUX dashlets distincts du formulaire `Project`, onglet « Pilotage »**, et ils ne lisent PAS la même granularité. D6 « Expense budget » et D8 « Supplier purchase flow » lisent `purchase_purchase_order.project` **directement** (`po.project = :_id AND po.status_select >= 3 AND po.status_select != 5`) — aucun moteur à appeler, la donnée remonte dès l'`UPDATE`/`INSERT` du champ `project`. D12 « Expenditure Synthesis » (le tableau ventilé par ouvrage/lot, prévision vs réalisation) lit `purchase_purchase_order_line.project_task` **via une jointure sur `project_project_task.sale_order_line`** — une correspondance ligne-de-commande → tâche → ligne de DPGF que ce protocole n'établit PAS (voir §7). | `[prouvé REST]` `ConstructionDashboard.xml:562-628` (D6), `:738-812` (D8), `:1161-1293` (D12) lus en source ; `/ws/meta/custom/construction-dash-expense-budget` et `.../construction-dash-purchase-flow` avec `{"id":950003,"_id":950003}` → `purchase_committed:"54620.000"` sur les deux, exactement la somme des 3 commandes que j'ai rattachées à ce projet ; `.../construction-dash-expenditure-synthesis` sur le même projet → `realisation:"0"` sur toutes les lignes (attendu, `project_task` non posé). |
| **Ces deux dashlets sont câblés sur le formulaire `Project`, showIf `constructionIsConstructionProject && id != null`, onglet Pilotage**, D5 « Time budget » et D6 « Expense budget » **côte à côte** (`colSpan="6"` chacun) — c'est littéralement l'écran que la mission demandait de vérifier (« le déboursé achat à côté du déboursé main-d'œuvre »). | `[SCHEMA]` `Project.xml:216-264` (panel `constructionFinancialTab`, dashlets `constructionTimeBudgetDashlet`/`constructionExpenseBudgetDashlet` en colSpan 6/6). |
| **Le bouton de validation / finalisation d'une commande fournisseur est scriptable, localisé et exécuté avec succès.** `action-purchase-order-method-validate` (Draft/Requested → Validated, `PurchaseOrderController.validate()`) et `action-purchase-order-method-finish-purchase-order` (→ Finished, `.finishPurchaseOrder()`) — le dossier d'hypothèses initial ne les avait pas trouvés faute de budget. | `[prouvé REST]` `POST /ws/action/action-purchase-order-method-finish-purchase-order` sur ma commande 16 (`{"id":16}`) → `status:0`, `{"reload":true}` ; en base, `status_select` 3→4 confirmé après l'appel. |
| **Le moteur de finalisation NE réécrit PAS un `purchase_order_seq`/`full_name` déjà posés correctement en SQL, et NE force PAS `receipt_state` à Received.** Conséquence directe pour H-ACH-04 et H-ACH-08 (§2). | `[prouvé REST]` même appel : `purchase_order_seq` reste `'ACH0015'`, `full_name` reste `'ACH0015-ELEXA Fluides & Réseaux'`, `receipt_state` reste `1` après le passage à Finished. |
| **Le menu Data Capture → Commandes fournisseur est mort**, même famille de piège que `SaleOrder`/`Invoice` dans `entites-ventes.md` §0 : `purchase_purchase_order` ne porte aucune colonne `data_capture_template`. | `[prouvé REST]` `POST /ws/rest/.../PurchaseOrder/search` avec `_domain:"self.dataCaptureTemplate IS NOT NULL"` → `status:-1`, `IllegalArgumentException: No such field 'dataCaptureTemplate' in object 'com.axelor.apps.purchase.db.PurchaseOrder'`. |
| **Aucun des 21 fournisseurs existants ni des 26 lignes de `purchase_supplier_catalog` ne porte un article de construction.** Tout est IT/ESN/fourniture de bureau (disques durs, cartouches, ramettes, imprimantes). Un rattachement direct des 9 commandes existantes à une affaire BTP est donc **non défendable** — cf. H-ACH-01. | `[SCHEMA]` `SELECT product, count(*) ... JOIN base_product` sur les 26 lignes des 9 commandes + les 26 lignes de `purchase_supplier_catalog` : 100 % `product_type_select='storable'` de nature bureautique. |
| **Le catalogue produit BTP existe déjà en base** (`base_product` id 200-400 : béton, acier, ciment, sable, bordures, tuyaux PVC, bardage, carrelage, peinture, câbles électriques, CVC…), avec prix et **`unit` correctement posé** (m³, kg, m, m², forfait, unité, ensemble) — jamais utilisé jusqu'ici par aucune commande fournisseur ni tarif fournisseur. C'est le socle sur lequel les 10 commandes créées sont bâties. | `[SCHEMA]` comptage direct, aucun produit id 200-400 référencé ni par `purchase_purchase_order_line` ni par `purchase_supplier_catalog` avant cette mission. |
| **Les 10 projets BTP portent des noms évocateurs (« Groupe scolaire », « EHPAD », « Centre de santé ») mais leurs `client_partner` réels sont les partenaires génériques du socle AOS** (123 Services, GERARD Solutions, MASSON SA…), **tous des sociétés privées**. Aucun signal de maître d'ouvrage public. Décide `construction_market_type_select=1` (Private) pour toute pièce achats nouvellement créée sur ces affaires, quel que soit ce que suggère le nom du chantier. | `[SCHEMA]` `sale_sale_order.client_partner` des 10 projets, tous `is_customer=true`, aucun nom à consonance publique (mairie, département, collège public…). |
| Attention : **Fait vérifié qui corrige la source de mission** : la base ne porte que **10 affaires BTP** (`project_project.code LIKE 'CH-%'`), pas 13. Les 3 lignes restantes de `project_project` (id 1-3) sont des projets génériques du socle AOS (123Service Project, SASAKI, GERARD), sans rapport BTP. Le plan de rattachement porte donc sur 10 affaires. | `[SCHEMA]` `SELECT count(*) FROM project_project` = 13 total, dont `code LIKE 'CH-%'` = 10 ; les 3 autres confirmées non-BTP par lecture directe. |

---

## 1. `purchase_purchase_order`

**Casse à NULL / valeur hors sélection**

- `construction_market_type_select` — nullable, mais **hors sélection à `0`** (la sélection réelle
  ne porte que `1=Private | 2=Public`, vérifiée `meta_select_item`). Les 9 commandes du socle
  portent `0` sur 9/9 — **non corrigé** (règle de sûreté, enregistrement pré-existant). Les 10
  commandes créées pour cette mission posent `1`, jamais `0`. `[SCHEMA]`
- `status_select` — répartit strictement entre 3 menus par égalité/inégalité stricte (`< 3` Devis
  fournisseur, `= 3` Commandes, aucun domaine = Historique). Confirmé structurellement inchangé
  après ajout de 10 lignes : `status_select=3` passe de 1 à 4 occurrences, cohérent avec le
  domaine `IN(3)`. `[SCHEMA]`

**Domaine filtrant qui exclut le NULL/false**

| Menu / dashlet | Prédicat | Conséquence |
|---|---|---|
| `sc.root.purchase.orders` / `...quotations` / `...historical` | `statusSelect IN(3)` / `< 3` / aucun | H-ACH-09, confirmé structurellement. |
| `construction-purchase-subcontracting` + 5 dashlets ST | `constructionIsSubcontracting = true` | 0/19 commandes (existantes + créées) — menu vide, légitime, la mission ne portait pas sur la sous-traitance. `[SCHEMA]` |
| **D6 « Expense budget », D8 « Supplier purchase flow »** (formulaire `Project`, onglet Pilotage) | `po.project = :_id AND po.status_select >= 3 AND po.status_select != 5` | **C'est le mécanisme du rattachement demandé par la mission.** Poser `project` + un statut Validated/Finished suffit — aucun moteur à déclencher, la requête SQL du dashlet est vive. `[prouvé REST]` |
| **D12 « Expenditure Synthesis »** (même onglet) | jointure sur `purchase_purchase_order_line.project_task` → `project_project_task.sale_order_line` | **Ne lit PAS `purchase_purchase_order.project`.** Une commande rattachée par `project` seul reste à `realisation:0` sur ce dashlet précis — cf. §7, boundary assumée. `[prouvé REST]` |
| `manufacturing-root-outsourcing-purchase-orders` | `outsourcingOrder = true` | 0/19 — concept distinct de la sous-traitance BTP (module `production`), non confondu. `[SCHEMA]` |
| `data-capture-root-objects-purchase-orders` | `self.dataCaptureTemplate IS NOT NULL` | Menu mort, colonne absente de la table. `[prouvé REST]` |

**namecolumn — `full_name`, format `<purchase_order_seq>-<supplier_partner.name>`**

Getter CDATA de `PurchaseOrder.xml` (`purchaseOrderSeq + '-' + supplierPartner.getName()`),
vérifié conforme sur les 9 commandes du socle ET reproduit à l'identique sur les 10 commandes
créées. **Un appel moteur (`finish-purchase-order`) sur une commande dont `full_name` a été posé
correctement en SQL NE l'écrase PAS** — testé en réel sur la commande 16. `[prouvé REST]`

**`purchase_order_seq` — au format `ACH000N` (Requested et au-delà), jamais `#<id>` sauf Draft pur**

Consommé par `PurchaseOrderManagementRepository.save()` à chaque enregistrement moteur —
mais **un `purchase_order_seq` déjà posé en SQL au bon format n'est pas régénéré/écrasé** par un
appel moteur ultérieur (testé sur la commande 16 : reste `'ACH0015'` après passage Validated→
Finished). `[prouvé REST]` pour ce point précis, `[INFERE]` pour le mécanisme général de
consommation au premier save (non testé sur une commande neuve jamais sauvée par le moteur).

**Boutons moteur, localisés et testés**

| Action | Point d'entrée REST | Effet observé |
|---|---|---|
| Valider (Draft/Requested → Validated) | `action-purchase-order-method-validate` (`PurchaseOrderController.validate()`) | Non exécuté cette mission (aurait modifié un statut) — localisé uniquement. `[INFERE]` |
| Finaliser (→ Finished) | `action-purchase-order-method-finish-purchase-order` (`.finishPurchaseOrder()`) | **Exécuté** sur ma commande 16 : `status_select` 3→4, `reload:true`, aucune erreur. `receipt_state` et `purchase_order_seq`/`full_name` inchangés (voir ci-dessus). `[prouvé REST]` |
| Réception (mouvement de stock) | Non relocalisé cette mission (hors périmètre stock) | — |

**À laisser au moteur** : la validation/réception d'une commande (ci-dessus). Le SQL de cette
mission pose des commandes déjà Validated/Finished (règle 12 : le SQL pose un ÉTAT), jamais une
transition simulée.

## 2. `purchase_purchase_order_line`

**Casse à NULL / dénormalisation**

- `product_name` — NOT NULL, snapshot du libellé produit à la sélection (comme
  `sale_sale_order_line.product_name`), jamais recalculé. `[SCHEMA]`
- `unit` — nullable, mais une ligne sans unité affiche un prix sans dire s'il s'applique au m³, au
  kg ou au forfait (piège 88). Posé sur les 28 lignes créées depuis `base_product.unit` (jamais
  `purchases_unit`, vide sur tout le catalogue produit — pas une lacune spécifique aux achats).
  `[SCHEMA]`
- `receipt_state` — porte la même sélection que le header (`purchase.order.receipt.state`,
  1/2/3) mais n'est **pas automatiquement synchronisé** par le moteur de finalisation (testé :
  finaliser une commande ne fait pas passer ses lignes de 1 à 3). `[prouvé REST]`

**Le champ qui décide de la remontée du réalisé dans le bilan d'affaire ventilé (D12) :
`project_task`, PAS `project`**

`ConstructionRafComputeServiceImpl` (calcul du RAF par tâche) ET le dashlet D12 filtrent tous les
deux sur `purchase_purchase_order_line.project_task` (rejoint à `project_project_task`), jamais
sur `purchase_purchase_order_line.project`. Une ligne de commande rattachée uniquement par
`project` (comme les 28 créées ici) est invisible à ces deux mécanismes — voir §7. `[INFERE]`
(source lue : `ConstructionRafComputeServiceImpl.java:74-99`, commentaire du code lui-même
signale la divergence entre l'ancien chemin (header) et le nouveau (ligne, aligné sur D13/D12).

**namecolumn** : `full_name`, format `<purchase_order_seq>-<product_name>`, même patron que
`SaleOrderLine.fullName` (non résolu dans `entites-ventes.md` §7 — même incertitude transposée
ici, non retestée : une ligne créée directement avec la valeur posée en SQL n'a pas eu besoin
d'être corrigée après coup, donc le cas "colonne périmée après renommage du parent" ne s'est
simplement pas produit dans ce protocole).

## 3. `purchase_supplier_catalog`

Table satellite pure, aucun menu dédié (confirmé, inchangé) — consultée seulement via le panneau
`supplierCatalogList` de la fiche `Partner`/`Product`.

- `unit` — NULL sur les 26 lignes existantes (non touchées cette mission). Le champ pertinent pour
  le poser serait `base_product.unit` (rempli sur le catalogue BTP), pas `purchases_unit` (vide
  partout, socle IT compris — pas une lacune propre à ces 26 lignes). **Non corrigé** : ces 26
  lignes appartiennent au jeu socle IT/ESN, hors du périmètre de rattachement BTP de cette
  mission. `[SCHEMA]`
- Aucune des 3 FK optionnelles qui pourraient la consommer
  (`construction_construction_ouvrage.supplier_catalog`, `..._detail_line.supplier_catalog`,
  `sale_sale_order_line.construction_supplier_catalog`) n'est utilisée : toujours 0/0/0 après
  cette mission (non touché, hors périmètre production-BTP). `[SCHEMA]`
- Cette mission n'a **pas créé** de nouvelles lignes de `purchase_supplier_catalog` pour les 2
  fournisseurs BTP créés : hors mandat (rattacher des commandes aux affaires), aurait été du
  gold-plating.

## 4. Fournisseurs créés pour cette mission — `base_partner`

Deux fournisseurs, aucun des 21 existants n'étant compatible nature-produit avec un achat de
matériaux de construction (règle 10 : créer la valeur plutôt que piocher au hasard) :

| id | Nom | Rôle |
|---|---|---|
| 10225 | NORMATER Négoce BTP | Matériaux généraux : gros œuvre, VRD, second œuvre, bardage. 9 commandes. |
| 10226 | ELEXA Fluides & Réseaux | Lot technique : électricité, CVC. 1 commande (950002). |

Shape reprise de `MASSON SA` (id=8, fournisseur socle **français, EUR**) plutôt que de `TOP
Components` (currency=USD 148, société chinoise — non représentative d'un négoce français) :
`partner_type_select=1`, `currency=46` (EUR), `localization=2` (France), `in_payment_mode=6`,
`out_payment_mode=14`, `payment_condition=2`, `partner_category=3` (PME). Tous les autres
booléens posés explicitement à `false` (règle 3). `full_name = name` (pas de `partner_seq`
inventé — les 10 208 lignes de test de masse montrent que `partner_seq` NULL est le cas normal
hors du socle `T0001`-`T0079`, mais `full_name` est TOUJOURS posé, piège 71).

**Non fait, volontairement** : aucune adresse (`main_address`) créée — non requise pour la
visibilité dans les menus Fournisseurs (`self.isContact=false AND self.isSupplier=true`, sans
condition d'adresse) ni pour la commande fournisseur. Un fournisseur sans adresse reste correct
fonctionnellement mais afficherait un onglet « Adresses » vide si ouvert — signalé en §7.

## 5. Rattachement aux affaires — ce qui a été écrit

10 commandes fournisseur créées (ids 10-19, séquences ACH0009-ACH0018), 28 lignes (ids 27-54),
10 lignes de taxe (ids 35-44), sur 7 des 10 affaires BTP réelles :

| Affaire | Budget prévisionnel | Commandes | Committed (D6/D8) | % du budget |
|---|---|---|---|---|
| 950003 Résidence Terrasses du Chêne (héros) | 1 035 004,13 € | 3 (ACH0009/10/11) | 54 620,00 € | 5,3 % |
| 950004 Plateforme Val-de-Reuil (héros) | 700 651,37 € | 2 (ACH0012/13) | 69 210,00 € | 9,9 % |
| 950001 Réhabilitation Cardan | 292 334,62 € | 1 (ACH0014) | 13 740,00 € | 4,7 % |
| 950002 Centre technique Nord | 205 163,66 € | 1 (ACH0015) | 5 895,00 € | 2,9 % |
| 950007 Groupe scolaire Rostand | 82 269,56 € | 1 (ACH0016) | 6 000,00 € | 7,3 % |
| 950008 Siège DE KIMPE | 90 978,37 € | 1 (ACH0017) | 4 700,00 € | 5,2 % |
| 950009 Atelier SILVER | 72 735,84 € | 1 (ACH0018) | 6 450,00 € | 8,9 % |
| 950005 Centre de santé Beauregard | 0 (n'a pas démarré) | 0 | — | légitime |
| 950006 EHPAD Les Glycines | 0 (n'a pas démarré) | 0 | — | légitime |
| 950010 AZ Inno (abandonné) | 0 | 0 | — | légitime, anti-faux-positif connu |

Distribution volontairement non uniforme : 2 héros (3 et 2 commandes), 5 affaires à 1 commande,
3 affaires à 0 — jamais « toutes à N commandes ». Statuts : Finished pour les projets déjà
terminés au 2026-09-07 ou bien avancés, Validated pour les commandes plus récentes — jamais
Draft/Requested (n'apparaîtraient pas dans le committed des dashlets, `status_select < 3`).

**Vérifié à l'appel réel du dashlet** (`/ws/meta/custom/construction-dash-expense-budget`,
`/ws/meta/custom/construction-dash-purchase-flow`) : les montants « Committed »/« Order »
remontés par le serveur correspondent exactement à la somme des `ex_tax_total` des commandes
rattachées, sur chacun des 7 projets. `[prouvé REST]`

## 6. Opportunité `958004` — correction du défaut nommé

`crm_opportunity.opportunity_status` : `4` (Négociation) → `5` (Fermée gagnée), valeur vérifiée
dans `crm_opportunity_status` avant écriture (règle 4). `expected_close_date` repositionnée de
`2026-10-09` (postérieure à aujourd'hui 2026-09-07 — incohérent avec un statut déjà gagné, règle
11) à `2026-09-05` (antérieure à aujourd'hui ET au démarrage du projet 950006, 2026-10-12).

**Non touché, volontairement** (hors du mandat explicite de la mission — statut + date
seulement) : `probability` reste à `75` (un « Won » réel serait à 100, incohérence résiduelle
assumée, pas corrigée) ; `description` mentionne toujours « Négociation en cours sur le
phasage » — texte libre non harmonisé avec le nouveau statut.

`[prouvé REST]` `GET /ws/rest/.../Opportunity/958004` après écriture :
`opportunityStatus.name = "Fermée gagnée"`, `$closedWonId = 5` — la condition de hilite
`$get('opportunityStatus.id') == $closedWonId` de `Opportunity.xml` sera donc vraie, la ligne
s'affichera en vert dans les vues kanban/liste (mécanisme lu en source, valeur confirmée par
REST, rendu visuel non vu à l'écran — voir §7).

Attention : **Piège attrapé par l'audit, pas en amont : `order_by_state` désynchronisé.** Le premier
`UPDATE` ne touchait que `opportunity_status` ; `order_by_state` (dénormalisation de
`opportunity_status.sequence`, pilote l'ordre kanban) restait à `4` (Négociation) alors que le
nouveau statut porte `sequence=5`. Détecté par `audit-completeness.sql` dimension 7c
(`crm_opportunity.order_by_state ≠ statut.sequence`, 1 anomalie sur la première passe). Corrigé
dans le même mouvement que le champ que je venais de changer (pas une harmonisation d'une AUTRE
opportunité, donc dans le mandat), en 2e bloc du même script. Nouveau cas
concret du piège 70/92 (dénormalisation qui ne suit pas un changement de statut), sur un champ
différent de celui déjà documenté pour `Partner`/`SaleOrder`.

Attention : **Second piège attrapé par l'audit : le compteur métier de la séquence `purchaseOrder` restait
à 9.** `base_sequence_version.next_num` (code `purchaseOrder`, préfixe `ACH`) n'avance qu'à
chaque save moteur — mes 10 commandes posent `purchase_order_seq` directement en SQL (`ACH0009` à
`ACH0018`) sans jamais consommer ce compteur (règle 12 : le SQL pose un état). Un prochain clic
« Valider » sur une commande brouillon depuis l'écran aurait donc régénéré `'ACH0009'`, en
collision avec la commande id=10 déjà nommée ainsi. Détecté par `audit-completeness.sql`
dimension 7d (compteur métier, distinct des séquences PK Postgres de la dimension 7e). Avancé à
19 (au-delà du max réellement occupé, 18), par un script dédié.
**Documenté dans `references/methode-ecriture-sql.md` (piège 118)** : le piège 73 déjà connu
couvre les séquences PK Postgres ; les compteurs `base_sequence`/`base_sequence_version` des
séquences MÉTIER Axelor (numérotation `ACH000N`, `SO000N`…) sont une deuxième horloge, distincte,
qui doit être avancée séparément après tout INSERT SQL posant directement un numéro de pièce.

## 7. Ce que ce protocole n'a PAS couvert

- **Aucun écran ouvert au navigateur.** L'extension de navigateur n'était pas connectée et le
  profil du navigateur automatisé (Playwright) était verrouillé par un autre processus concurrent
  (plusieurs sessions peuvent partager le même profil) — les deux ont été essayés, aucun n'a abouti. Tout ce qui est marqué
  `[prouvé REST]` est un appel HTTP authentifié réel contre le même endpoint que le front-end React
  appelle (`/ws/action`, `/ws/rest`, `/ws/meta/custom/{name}`), avec la réponse JSON observée — une
  preuve solide du mécanisme serveur, mais **pas** une preuve du rendu pixel (couleur du hilite,
  disposition des deux dashlets côte à côte, absence d'erreur console).
- **`purchase_purchase_order_line.project_task` n'a été posé sur aucune des 28 lignes créées.**
  Conséquence assumée : le dashlet D12 « Expenditure Synthesis » (réalisé ventilé par ouvrage/lot)
  reste à `realisation:0` sur les 7 projets concernés, **alors que D6 et D8 remontent
  correctement**. Poser ce champ suppose de choisir, pour chaque ligne de commande, une tâche
  `project_project_task` déjà reliée à la bonne `sale_sale_order_line` de niveau ouvrage (20) de la
  DPGF du projet — une correspondance produit-à-ouvrage que cette mission n'a pas établie
  (dépasserait le rattachement achats demandé, empièterait sur le domaine production-BTP/DPGF déjà
  couvert par `entites-production-btp.md`).
- **`purchase_purchase_order_line.project` a été posé** (miroir du header) mais **aucun dashlet
  du périmètre ne le lit** — vérifié par grep sur `ConstructionDashboard.xml` : posé par prudence
  (règle 2), pas parce qu'un mécanisme identifié en dépend.
- **La validation (`action-purchase-order-method-validate`) n'a pas été testée en réel** — seule
  la finalisation (`finish-purchase-order`) l'a été, sur une seule commande (la mienne, id=16).
  Le point d'entrée de la validation est localisé (§1) mais non exécuté, pour ne pas modifier
  inutilement l'état d'une commande au-delà de ce que la mission demandait.
- **Aucune adresse créée pour les 2 fournisseurs BTP** (§4) — un onglet « Adresses » vide serait
  visible si un présentateur ouvrait la fiche fournisseur en démo.
- **Le rattachement `budget_budget` ↔ `project_project`** (H-ACH-05) reste non résolu : la table
  `budget_budget` ne porte aucune colonne `project`, donc aucune FK directe à tester depuis le
  domaine achats — potentiellement du ressort d'un autre chaînage (niveau de budget, distribution),
  hors périmètre de cette mission.
- **`purchase_purchase_order_line_tax`** : structure et cohérence 1:1 avec les commandes
  reproduites à l'identique du motif majoritaire du socle (tax_line=24, 0 %), jamais vérifiées
  ligne à ligne au-delà de ce qui était nécessaire pour les 10 commandes créées.
- **La cohérence produit-à-produit entre `purchase_supplier_catalog` et
  `purchase_purchase_order_line`** sur les 9 commandes du socle (26=26, coïncidence relevée dans
  le dossier d'hypothèses) n'a pas été vérifiée en détail — hors périmètre, ces lignes ne sont pas
  concernées par le rattachement.
---

## Piloter les achats par l'API — mesures du 2026-09-22

9.1.7, 27/09 — achat intragroupe créé par l'API : poser `"interco": true`, sinon aucune commande miroir (piège 193). Règlement
fournisseur par l'API : répartir le montant sur les échéances de la facture, sinon ni écriture ni lettrage, et
NullPointerException en virement (piège 194).

> `[prouvé REST 9.1.3 / AOP 8.2.2]` sur une passe de **100 commandes d'achat**. Prérequis de lecture :
> pièges 131 et 132 (`entites-ventes.md`), qui valent tels quels ici. Les quatre pièges ci-dessous
> sont ce que les achats ont **en propre**, et qui diverge de la vente.

### 133. Le calcul d'en-tête d'achat ne fait que SOMMER : sans calcul par ligne, il somme des zéros

Divergence nette avec la vente : `action-sale-order-method-compute` recalcule aussi les totaux de
ligne, `action-purchase-order-method-compute` **non**. Il se contente d'agréger ce que les lignes
portent déjà.

Séquence correcte, dans cet ordre :

1. `action-purchase-order-line-method-get-product-information` **une fois par article** (piège 131) ;
2. `action-purchase-order-line-method-compute` **par ligne** ;
3. `action-purchase-order-method-compute` sur l'en-tête, avec l'enregistrement entier (piège 132).

Sauter l'étape 2 rend un en-tête à 0,00 € sur des lignes qui portent pourtant un prix à l'écran — et
aucun des trois appels ne renvoie d'erreur.

### 134. Le prix d'une ligne d'achat vient de `purchase_price`, jamais de `cost_price`

La ligne d'achat lit `base_product.purchase_price`, ou une ligne de catalogue fournisseur
(`purchase_supplier_catalog`, §3) — **jamais `base_product.cost_price`**. Un article dont le prix de
revient est renseigné et le prix d'achat vide produit une ligne à **0,00 €**, sans avertissement.

C'est contre-intuitif parce que le prix de revient est le champ qu'on remplit pour la production et la
marge : il ne sert à rien ici. Contrôle à passer avant la vague achats, sur le périmètre d'articles
visé : `SELECT count(*) FROM base_product WHERE COALESCE(purchase_price,0) = 0` — et attention au
piège 130, `> 0` sauterait les NULL.

### 135. Le moteur refuse d'écrire sur une commande d'achat validée, en répondant `status: 0`

Sur une commande au **statut 3**, les actions de calcul répondent `status: 0` et **n'écrivent rien**.
Le refus n'est pas un message : c'est un succès sans effet.

À distinguer du fait déjà établi en §1 : les **transitions** restent jouables sur une commande validée
(`action-purchase-order-method-finish-purchase-order` a bien fait passer la commande 16 de 3 à 4).
Ce qui est refusé, c'est la **réécriture des montants**.

Conséquence d'ordonnancement : les totaux d'une commande destinée au statut 3 se calculent **avant**
la validation. Sur une commande déjà validée qu'on ne peut plus remettre en arrière, ils se posent en
SQL — suivi d'un **redémarrage** avant toute lecture ou tout nouvel appel moteur (règle 12, piège 125).

*Non mesuré* : si le refus est une garde explicite du service ou un effet de bord, et s'il s'applique
aux statuts au-delà de 3. Formulé au statut 3 seulement, parce que c'est là qu'il a été constaté.

### 136. Supprimer une commande d'achat en SQL heurte trois tables filles aux noms non devinables

Une suppression SQL doit descendre dans cet ordre :

1. `purchase_purchase_order_line_tax_line_set`
2. `purchase_purchase_order_line_tax`
3. `purchase_purchase_order_line`
4. `purchase_purchase_order`

Attention : **Les colonnes de jointure ne se devinent pas** : elles s'appellent `purchase_purchase_order_line`,
pas `purchase_order_line`. Écrire le nom « logique » donne une erreur de colonne inconnue, et le
réflexe est alors de croire que la table n'est pas concernée.

**Plus court et plus sûr** : `POST /ws/rest/<modèle>/<id>/remove` fait la descente proprement, y
compris les tables de jonction. À préférer systématiquement pour défaire une passe ratée — sous
réserve de la règle de sûreté de SKILL.md : on ne supprime que ce qu'on a créé soi-même.
