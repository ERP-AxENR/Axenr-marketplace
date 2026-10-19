# Entités — production & BTP

**Pièges couverts par cette fiche :**

- 14. Les champs de coût du poste de charge (WorkCenter) dépendent de `work_center_type_select`
- 15. Un ordre de fabrication TERMINÉ créé en SQL pur n'a AUCUNE chaîne de stock — la construire explicitement (les liens sont des FK, pas des M2M)
- 19. Lignes composant de nomenclature (BoM) : l'O2M `billOfMaterialLineList` se mappe par `bill_of_material_parent`, PAS par `bill_of_material`
- 20. La gamme (ProdProcess) doit être liée à un produit OU partagée
- 21. La ligne de gamme (ProdProcessLine) dénormalise les champs du poste de charge à la création — mettre à jour le poste de charge NE resynchronise PAS les lignes existantes
- 22. La machine a besoin de `machine_type` (FK) + `stock_location`
- 26. Ne pas rendre `real_*` identique à `planned_*` sur un OF/OperationOrder terminé
- 27. Mouvement de stock de production : renseigner aussi le `manuf_order` générique (pas seulement in_/out_manuf_order)
- 28. Numéro de lot (TrackingNumber) produit : renseigner les champs d'origine
- 29. La généalogie des lots (TN) se construit à partir des TN CONSOMMÉS — consommer le lot source, ne pas se contenter d'affirmer le M2M
- 99. Une nomenclature qui porte une gamme et AUCUNE ligne de composant échoue sur un NullPointerException
- 100. Une nomenclature SANS gamme rend un ordre de production VIDE : zéro OF, en succès, sans un message
- 101. Générer un OF depuis une commande exige `sale_supply_select` ∈ {3,4} sur le produit ET `qty_to_produce > 0` sur la ligne
- 102. Configurateur : une formule sans indicateur correspondant est ignorée EN SILENCE, et éditer une formule périme toutes les instances
- 103. Attributs de configurateur seedés par API : cinq colonnes `context_field*`, un `on_change`, et parfois un redémarrage
- 119. Nomenclature et gamme INVISIBLES dans le sélecteur d'un ordre de fabrication : `statusSelect = 3` ET atelier vide
- 120. Une gamme qui consomme depuis un emplacement SANS stock ne lève rien — l'OF affiche tous ses composants manquants
- 121. `producedProductStockLocation` décide où atterrit le produit fini, et les sous-ensembles doivent atterrir là où le parent consomme
- 122. Une quantité NÉGATIVE en nomenclature passe l'import sans un mot et bloque au lancement de l'OF
- 125. Démarrer puis Terminer un ordre par script rend un coût réel de ZÉRO — le correctif a trois temps
- 126. « Démarrer » ne touche que l'en-tête : les opérations restent Planifiées, sans date réelle
- 127. `compute-cost-price` AJOUTE une feuille de coût, il ne remplace pas la précédente
- 128. Les lignes filles d'une feuille de coût ne portent PAS la référence à la feuille — purge récursive
- 129. Une nomenclature auto-référencée rend un coût de zéro, sans erreur et sans feuille
- 148. Gamme à `operation_continuity` NULL : l'ordre de démarrage des opérations est IMPOSÉ, comme si la case était cochée
- 155. Un devis BTP créé par REST n'est BTP qu'avec son drapeau et son initialisation — et il naît hors sélection, en marché privé avec l'avance par défaut
- 156. « Créer le chantier » recopie l'en-tête du devis — tout poser AVANT, puis renommer chantier ET dépôt
- 157. « Planning du chantier » plante au premier clic — planning créé d'avance, APRÈS le renommage
- 158. Synthèse matière vide sans produit sur les sous-détails — réutiliser les produits BTP de la démo
- 159. La sauvegarde de l'arbre accepte tous les champs de complétude d'une ligne
- 160. Situation de travaux : quatre prérequis, un avancement en INCRÉMENT — et le marché-cadre ne rattache que le devis qui le crée
- 161. Les retenues du module pointent vers des produits vides — repointer par la retenue, par le code
- 162. Régler une facture de situation : hors retenue, et décider sur le reste dû
- 163. Paiement direct confirmé = journal DC4 obligatoire à la ventilation suivante
- 164. Circuit de sous-traitance : URSSAF « Valide » + Kbis sur la fiche du sous-traitant
- 165. Commande de sous-traitance repassée au prix d'achat du produit
- 166. Lots de pointage : salarié sans contrat ni utilisateur = feuille sans société = « Date invalide »
- 167. Devis perdu : envoyé, puis annulé avec un motif standard
- 168. Contrôler le montant d'avenant du chantier, pas le message de confirmation
- 176. Avancement posé par l'API : chaque enregistrement crée une ligne d'historique datée du jour simulé — le poser sur les ouvrages, une fois par date
- 177. Réceptionner un chantier ne pose pas sa fin réelle : retard et pénalité provisoire continuent de courir
- 178. L'onglet Pilotage calcule ET ENREGISTRE à son ouverture : après un peuplement par l'API, rejouer son action sur chaque chantier
- 179. Un instantané de reste à faire enregistre l'état du moment ; sa date n'est qu'une étiquette
- 180. Achats d'un chantier : trois rattachements lus par trois écrans — sans celui de l'en-tête, la déduction du paiement direct vaut 0 € en silence
- 181. Lots de pointage et paie du module : préremplir par le bouton dédié, zone sur chaque demi-journée, paie par le chemin de l'écran

Voir aussi, dans `entites-projet-temps.md` : 144 — un pointage d'atelier porte l'OF et l'opération,
pas l'affaire, et l'employé doit être « imputé sur OF ».

### production_bill_of_material

Module : `axelor-production`. Dépendances UI lourdes — un insert erroné casse silencieusement les sélecteurs m2o et le panneau « Nomenclatures » sur le Produit.

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| name | OUI | Nom de la nomenclature |
| product | OUI | FK vers base_product (l'article produit) |
| prod_process | Recommandé | FK vers production_prod_process |
| company | OUI | FK vers base_company (généralement 1) |
| status_select | Recommandé | 1=Brouillon, 2/3=Validé (à vérifier selon la base) |
| type_select | Recommandé | 1 = normal, 2 = personnalisé |
| version_number | OUI | Démarrer à 1 |
| qty, calculation_qty | Recommandé | 1.0 par défaut |
| unit | Recommandé | FK vers base_unit |
| workshop_stock_location | Recommandé | FK vers stock_stock_location |
| **full_name** | **CRITIQUE** | **DOIT être renseigné.** `namecolumn="true"`. Calculé par `BillOfMaterialComputeNameServiceImpl` : `<product.code> + " \| " + <bom.name> + (" - v" + version_number si > 1)`. NULL = libellé vide dans les sélecteurs m2o → les utilisateurs croient la nomenclature « manquante ». |
| **define_sub_bill_of_material** | **CRITIQUE** | **DOIT être `true`** pour que la nomenclature apparaisse sur le formulaire Produit. `action-product-view-show-bill-of-material` filtre par `self.product.id = :productId AND self.defineSubBillOfMaterial = true`. False = la nomenclature existe mais est invisible côté Produit. |

### production_prod_process

| code, name | Recommandé | Identifiant de la gamme |
| product | OUI | FK vers base_product |
| company | OUI | FK vers base_company |
| status_select | Recommandé | 3=validé typiquement |
| type_select, version_number, launch_qty | Recommandé | 1, 1, 1.0 |
| workshop_stock_location, stock_location, produced_product_stock_location | Recommandé | FK vers stock_stock_location |
| **full_name** | **CRITIQUE** | `namecolumn="true"`. Calculé par `ProdProcessManagementRepository.save()` : `<name> + (" - v" + version_number si > 1)`. NULL = libellé vide partout. |

### production_machine

| code, name | Recommandé | |
| stock_location | Recommandé | FK vers stock_stock_location |
| buying_currency | Recommandé | 46 EUR |
| **weekly_planning** | **CRITIQUE POUR LE PLANIFICATEUR** | FK vers base_weekly_planning. Sans lui, le planificateur de production / la vue `planning-per-machine` n'affichera aucun OperationOrder utilisant cette machine. Défaut : 1=Plein temps. Toujours le renseigner sur chaque machine de démo. |

### production_manuf_order

| manuf_order_seq | Recommandé | "MO-XXX-001" |
| status_select | Recommandé | 1=brouillon, 2=annulé, 3=planifié, 4=en cours, 5=en attente, 6=terminé, 7=fusionné |
| type_select, priority_select, qty, unit | Recommandé | |
| company, product, bill_of_material, prod_process | OUI | Les quatre sont requis pour un OF valide |
| sale_order_line | Recommandé (si business-production) | Relie OF→Commande client→marge Projet |
| client_partner | Recommandé (si business-production) | Accès direct au client final |
| workshop_stock_location | Recommandé | FK vers stock_stock_location |
| planned_start_datet, planned_end_datet | OUI si status >= 3 | |
| real_start_datet, real_end_datet | OUI si status = 4 ou 6 | |
| operation_order_max_priority | Recommandé | Entier (ex. 30) |
| outsourcing, plan_only_missing_quantities, is_cons_pro_on_operation, invoiced, is_to_invoice | Recommandé | `false` |

> **Un OF TERMINÉ créé en SQL pur n'a aucun effet de bord de consommation/stock.** Insérer `status_select=6` directement contourne le workflow Java `plan() → start() → finish()`. Résultat : aucune ligne `production_prod_product` (toConsume/consumed/produced), aucun `stock_stock_move`/`stock_stock_move_line` pour les matières consommées ou les articles produits, aucun M2M `consumed_stock_move_line_list`/`produced_stock_move_line_list`. Acceptable pour des démos centrées sur la planification, l'ordonnancement, la marge P&L. PAS acceptable pour la traçabilité de stock ou l'analytique de consommation : dérouler le workflow via l'interface ou l'API REST, moteur d'abord (piège 143, étape 1) ; pour un OF déjà terminé, la chaîne SQL du piège 15 reste une 3e voie, sous les conditions et limites du piège 143 (étape 1 bis) — jamais pour les niveaux de stock.

### production_operation_order

| name, operation_name, priority | Recommandé | |
| status_select | Recommandé | 1=brouillon, 3=planifié, 4=en cours, 6=terminé (aligné sur l'OF parent) |
| manuf_order, work_center, machine, prod_process_line | OUI | FK |
| planned_start_datet, planned_end_datet | OUI | |
| **planned_duration** | OUI | **secondes en bigint** (widget `duration x-seconds="true"`, jamais des minutes malgré l'indice du titre « (hhh:mm:ss) »). Formule : `qty * 3600 / cadence`. |
| **planned_human_duration, planned_machine_duration** | Recommandé | secondes en bigint. Poser à `planned_duration` pour les postes de charge mixtes ; l'un des deux à 0 pour un poste purement machine ou purement humain. NULL = affichage vide sur le formulaire. |
| real_start_datet, real_end_datet | OUI si status >= 4 | |
| **real_duration** | **CRITIQUE non-NULL** | secondes en bigint. **Poser à 0 (pas à NULL) sur les OO avec status < 4** — sinon le champ fantôme de l'ordre de fabrication `$totalRealDuration` (somme Groovy `operationOrderList.realDuration.sum()`) lève une NPE et affiche `false`/vide. La lecture du % de cadence est `(planned_duration / real_duration) * 100`. |
| **is_micro_planning_done** | **CRITIQUE POUR LE PLANIFICATEUR** | **Poser à `true` sur chaque OO avec `status_select IN (3, 4, 6)`** (planifié, en cours, terminé). Seul `status_select=1` (brouillon) garde `false`. La SPA `production-pro/planning-per-machine` place les OO avec `is_micro_planning_done=false` dans la **barre latérale** (comme s'ils étaient brouillon) au lieu de les placer dans la grille Gantt — OO terminés inclus, sinon le Gantt historique est vide. Confirmé sur AOS 9.0.2 production-pro. |
| is_pinned, is_to_invoice | Recommandé | `false` |
| employee | Recommandé | FK vers hr_employee. Pour que l'OO apparaisse sur `operation-order-employee-planned-calendar` (business-production), en assigner un. |
| outsourcing | Recommandé | `false` |

### btp_btp_ouvrage

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| name | OUI (NOT NULL) | Nom de l'ouvrage |
| code | Recommandé | Code d'ouvrage unique (motif : OUV-XXXX) |
| unit | Recommandé | FK vers base_unit |
| product | Recommandé | FK vers base_product (le produit représentant cet ouvrage) |
| product_category | NON | FK vers base_product_category |
| company | Recommandé | FK vers base_company. Généralement = 1 |
| total_material_cost | Calculé | Somme des lignes de détail type 1 |
| total_labor_cost | Calculé | Somme des lignes de détail type 2 |
| total_equipment_cost | Calculé | Somme des lignes de détail type 3 (location) |
| total_service_cost | Calculé | Somme des lignes de détail type 5 (prestation) |
| total_subcontracting_cost | Calculé | Somme des lignes de détail type 4 |
| total_cost | Calculé | Somme de tout ce qui précède |
| fg_percentage | Recommandé | Frais généraux % (typiquement 12.00) |
| fg_amount | Calculé | total_cost × fg_percentage / 100 |
| margin_percentage | Recommandé | Marge % (typiquement 15-20) |
| margin_amount | Calculé | (total_cost + fg_amount) × margin_percentage / 100 |
| selling_price | Calculé | total_cost + fg_amount + margin_amount |
| coefficient | Calculé | selling_price / total_cost (ou 0 si total_cost = 0) |
| realization_time | Calculé | Somme des realization_time des lignes de détail MO |
| is_active | Recommandé | Booléen, à true |
| is_subcontractable | Recommandé | Booléen, false par défaut |
| is_selling_price_manual | Recommandé | Booléen, false = calculé automatiquement |
| is_fixed | Recommandé | Booléen, false par défaut |
| version | OUI | Mettre à 0 |

### btp_btp_ouvrage_detail_line

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| btp_ouvrage | OUI (NOT NULL) | FK vers btp_btp_ouvrage |
| product_name | OUI (NOT NULL) | Nom de produit dénormalisé |
| btp_detail_type_select | OUI (NOT NULL) | 1=Matériel, 2=MO, 3=Location, 4=Sous-traitance, 5=Prestation |
| product | NON | FK vers base_product |
| qty | Recommandé | Quantité BigDecimal |
| unit | Recommandé | FK vers base_unit |
| unit_cost | Recommandé | Prix unitaire BigDecimal |
| total_cost | Recommandé | qty × unit_cost |
| realization_time | Pour les lignes MO | Heures. Pour MO : qty (si unit=heure). Pour un mode cadencé : qty/cadence |
| cadence | Pour les lignes MO | Unités par heure (ex. 1.0 = 1 unité/heure) |
| sequence | Recommandé | Ordre d'affichage (10, 20, 30...) |
| supplier_catalog | NON | FK vers une entrée de catalogue fournisseur |
| description | NON | Description en texte libre |
| version | OUI | Mettre à 0 |

## Règle de sûreté (ex-PROHIBITIONS)

- Ne jamais créer de ligne de détail d'ouvrage sans `btp_ouvrage` ni `product_name` : ce sont des colonnes NOT NULL, l'insert échoue sinon.

### 14. Les champs de coût du poste de charge (WorkCenter) dépendent de `work_center_type_select`

`production_work_center` porte DEUX volets de coût ; celui qui est lu dépend du type (`1 Humain / 2 Machine / 3 Les deux`). Les laisser à NULL affiche un coût vide sur le detailsPanel et met la fiche de coût à zéro :
- **Machine (2)** + **Les deux (3)** : renseigner `cost_type_select` (`iproduction.work.center.cost.type.select` : `1 Par heure / 2 Par cycle / 3 Par pièce`) et `cost_amount`.
- **Humain (1)** + **Les deux (3)** : renseigner `hr_cost_type_select`, `hr_cost_amount`, `hr_duration_per_cycle`.
- Tous : `min_capacity_per_cycle` / `max_capacity_per_cycle` doivent être `> 0` (NULL/0 casse la planification de capacité) et `duration_per_cycle` non nul.

**Et le type n'est pas qu'une affaire de coût : il bloque.** Poser `2 Machine` (ou `3`) sans
renseigner `machine` lève au calcul de la gamme :
« Merci de remplir la machine à utiliser dans le poste de charge X »
(`ProdProcessLineComputationServiceImpl` : le contrôle ne se déclenche que sur MACHINE ou BOTH).
Un atelier de **montage manuel** — la majorité des démos industrielles — est en `1 Humain`, et c'est
alors `human_duration` qui est retenue, pas `duration_per_cycle`. Vérifié sur AOS 9.1.4.

### 15. Un ordre de fabrication TERMINÉ créé en SQL pur n'a AUCUNE chaîne de stock — la construire explicitement (les liens sont des FK, pas des M2M)

Insérer `status_select=6` directement laisse `inStockMoveList` / `outStockMoveList` / `consumedStockMoveLineList` / `producedStockMoveLineList` vides et le TrackingNumber produit « lié à rien ». La liaison passe par des **colonnes FK sur le mouvement/la ligne — il n'y a AUCUNE table de jonction M2M** :
- `stock_stock_move.in_manuf_order` → ManufOrder.inStockMoveList ; `.out_manuf_order` → outStockMoveList.
- `stock_stock_move_line.consumed_manuf_order` → consumedStockMoveLineList ; `.produced_manuf_order` → producedStockMoveLineList ; `.tracking_number` → relie le lot produit.

**Troisième voie seulement, après le moteur (piège 143, étape 1) ; conditions et limites : piège 143, étape 1 bis.** Motif de référence (reproduire la chaîne d'un vrai OF terminé, ex. cloner les mouvements `ISM0002`/`ISM0003` de `MO0001`) :
- **Mouvement IN** (consommation) : `status_select=3 type_select=1`, `from_stock_location=<emplacement composant> to=<Production virtuel (type 3)>`, `in_manuf_order=<OF>` ; une `stock_move_line` par composant consommé avec `consumed_manuf_order=<OF>`, `qty=real_qty`, pas de tracking_number.
- **Mouvement OUT** (production) : `status_select=3 type_select=1`, `from=<Production virtuel> to=<emplacement produits finis>`, `out_manuf_order=<OF>` ; une ligne pour le produit fabriqué avec `produced_manuf_order=<OF>` et `tracking_number=<id du TN produit>`.

`stock_stock_move_line.product_name` est NOT NULL. La valorisation/généalogie/MRP fonctionnent SANS cette chaîne (via prod_product + TN.origin_manuf_order + parentTrackingNumberSet) ; ne construire la chaîne de stock que lorsque le journal de stock / la traçabilité de consommation doivent être démontrés.

Voir aussi le piège 143 (`entites-stock.md`) : statut de flux physique posé sans mouvement réalisé par
le moteur.

### 19. Lignes composant de nomenclature (BoM) : l'O2M `billOfMaterialLineList` se mappe par `bill_of_material_parent`, PAS par `bill_of_material`

**Symptôme :** des lignes `production_bill_of_material_line` existent (liées via `bill_of_material`) mais la grille des composants du formulaire de nomenclature (`billOfMaterialLineList`) est **vide**.

**Cause :** sur `production_bill_of_material_line`, il y a DEUX FK vers une nomenclature :
- **`bill_of_material_parent`** = la nomenclature propriétaire (c'est elle que lit l'O2M `billOfMaterialLineList`). **C'est celle-ci qu'il faut renseigner.**
- `bill_of_material` = la SOUS-nomenclature PROPRE au produit composant (pour une nomenclature multi-niveaux ; NULL pour un composant simple).
- `product` = le produit composant.

Renseigner `bill_of_material = <id parent>` (intuitif mais faux) place la ligne dans le slot de *sous-nomenclature* → invisible depuis le parent. **Toujours renseigner `bill_of_material_parent = <id de la nomenclature parent>`** et laisser `bill_of_material` à NULL pour les composants feuilles. Référence : les lignes du clone « Pack Performance » ont `bill_of_material_parent=32`, `bill_of_material` NULL (ou un id de sous-nomenclature pour un composant fabriqué). Rattrapage : `UPDATE ... SET bill_of_material_parent = bill_of_material, bill_of_material = NULL WHERE bill_of_material_parent IS NULL`.

### 20. La gamme (ProdProcess) doit être liée à un produit OU partagée

Une `production_prod_process` avec À LA FOIS `product IS NULL` ET `is_enabled_for_all_products = false` est orpheline (inutilisable/invisible pour aucun produit). **Règle générale : `product` est obligatoire.** Pour une gamme partagée entre de nombreux produits (ex. une gamme générique de stérilisation/finition), poser plutôt `is_enabled_for_all_products = true` et laisser product à NULL. Choisir explicitement l'un des deux par gamme.

### 21. La ligne de gamme (ProdProcessLine) dénormalise les champs du poste de charge à la création — mettre à jour le poste de charge NE resynchronise PAS les lignes existantes

`production_prod_process_line` copie le coût/la capacité/le type depuis son poste de charge à la création. Si les postes de charge sont corrigés APRÈS la création des lignes (piège 14), les lignes gardent leurs valeurs périmées/NULL et la gamme affiche des temps/coûts vides. Repropager explicitement :
```sql
UPDATE production_prod_process_line ppl SET
  min_capacity_per_cycle = COALESCE(NULLIF(wc.min_capacity_per_cycle,0),1),
  max_capacity_per_cycle = COALESCE(NULLIF(wc.max_capacity_per_cycle,0),1),
  cost_amount = wc.cost_amount, cost_type_select = wc.cost_type_select,
  hr_cost_amount = wc.hr_cost_amount, hr_cost_type_select = wc.hr_cost_type_select,
  work_center_type_select = wc.work_center_type_select,
  human_duration = COALESCE(NULLIF(ppl.human_duration,0), wc.hr_duration_per_cycle, ppl.duration_per_cycle)
FROM production_work_center wc WHERE ppl.work_center = wc.id AND ppl.prod_process IN (...);
```
Attention : Le nom de colonne diffère : WorkCenter a `hr_duration_per_cycle` ; **ProdProcessLine a `human_duration`** (pas de `hr_duration_per_cycle`). Sur les postes de charge machine, `cost_type_select` est renseigné / `hr_cost_type_select` est NULL, et inversement pour les postes de charge humains — ne pas supposer que les deux sont non-NULL simultanément.

### 22. La machine a besoin de `machine_type` (FK) + `stock_location`

Une `production_machine` de démo avec `machine_type` / `stock_location` à NULL paraît cassée sur le formulaire et n'est pas positionnable. `machine_type` est une FK vers `production_machine_type` (créer des types adaptés au domaine si ceux du seed ne conviennent pas). Positionner `stock_location` sur l'emplacement atelier. (`weekly_planning` déjà couvert pour le planificateur.)

### 26. Ne pas rendre `real_*` identique à `planned_*` sur un OF/OperationOrder terminé

Des ordres terminés créés en SQL pur avec `real_start_datet = planned_start_datet` et `real_end_datet = planned_end_datet` (et `real_duration = planned_duration`) paraissent artificiels. Ajouter des écarts petits et variés. Dériver `real_*` de `planned_*` (qui est stable) pour que l'UPDATE reste idempotent : ex. `real_start = planned_start + (priority*180)s`, `real_end = planned_end + (priority*120)s`, `real_duration = GREATEST(60, planned_duration + ((priority%3)-1)*120)`.

### 27. Mouvement de stock de production : renseigner aussi le `manuf_order` générique (pas seulement in_/out_manuf_order)

Un `stock_stock_move` de production porte `in_manuf_order` (consommation) / `out_manuf_order` (production) ET une FK `manuf_order` générique. Le clone renseigne tous les champs pertinents ; ne renseigner que in_/out_ laisse le champ « Ordre de fabrication » du mouvement vide sur le formulaire. Renseigner `manuf_order = <OF>` sur les deux mouvements.

### 28. Numéro de lot (TrackingNumber) produit : renseigner les champs d'origine

Un TN de lot produit doit reproduire la forme du TN produit cloné : `origin_move_type_select`, `origin_manuf_order = <OF>`, `origin_stock_move_line = <l'id de la stock_move_line produite>` (lien retour vers la ligne du mouvement OUT qui porte ce TN), et `nbr_of_pieces`. Sans cela, le panneau « Origine » du TN est vide même si généalogie/DLU sont renseignées.

Énumération `stock.tracking.number.origin.move.type.select` : **1 Manuel / 2 Inventaire / 3 Vente / 4 Achat / 5 Fabrication**.
- **Chaque lot produit a besoin d'un mouvement OUT** pour appuyer son `origin_stock_move_line` — même pour les cycles terminés « simples » pour lesquels la chaîne complète a été omise. Un TN produit avec `origin_manuf_order` renseigné mais sans `origin_stock_move_line` est à moitié configuré ; créer au moins un mouvement OUT minimal (Production → emplacement produits finis) portant le TN, puis poser `origin_move_type_select = 5`.
- **Les lots d'entrée / en circulation** (ex. un article sale entrant pour retraitement) n'ont AUCUNE origine de production : poser `origin_move_type_select = 1` (Manuel) et laisser `origin_stock_move_line` à NULL — c'est la forme cohérente pour un lot suivi manuellement, pas un bug.

### 29. La généalogie des lots (TN) se construit à partir des TN CONSOMMÉS — consommer le lot source, ne pas se contenter d'affirmer le M2M

`ManufOrderTrackingNumberServiceImpl.setParentTrackingNumbers(ManufOrder)` (bytecode vérifié, AOS 9.0.8) lit `getProducedStockMoveLineList()` et `getConsumedStockMoveLineList()`, et positionne le `parentTrackingNumberSet` de chaque TN produit = les TN trouvés sur les **lignes de mouvement de stock consommées**. Conséquence pour une généalogie construite en SQL pur : insérer à la main le M2M `stock_tracking_number_parent_tracking_number_set` fait *afficher* des parents dans le formulaire, mais c'est **incohérent** à moins que ces TN parents soient effectivement portés par une ligne consommée — et le service natif, s'il était exécuté, ne reproduirait PAS cet état. Pour être fidèle : le **mouvement de consommation (IN) doit consommer le lot SOURCE portant son TN** (`stock_move_line.tracking_number = <TN parent>`, `consumed_manuf_order = <OF>`). C'est un **motif de retraitement / reprise** — le MÊME produit apparaît à la fois consommé (lot d'entrée, ex. caisse sale `LOT-00041`) et produit (lot de sortie, ex. caisse stérile `LOT-00042`, nouvelle DLU), avec des TN différents ; la caisse d'entrée N'EST PAS un composant de nomenclature, elle est ajoutée directement au mouvement de consommation. Vérifier : chaque TN dans le `parentTrackingNumberSet` d'un lot produit devrait aussi apparaître comme `tracking_number` sur une ligne `consumed_manuf_order` du même OF.

---

### 99. Une nomenclature qui porte une gamme et AUCUNE ligne de composant échoue sur un NullPointerException

Bug d'AOS 9.1.6 (`axelor-production`), joignable depuis le formulaire de nomenclature standard, donc pas réservé au configurateur. `BillOfMaterialManagementRepository.save` appelle `refreshProdProcessHazardPhrases` ; sur une nomenclature NEUVE portant une gamme, `computeHazardPhrasesForProdProcess` fait `.flatMap(b -> b.getBillOfMaterialLineList().stream())` **sans garde de nullité**, alors que la méthode voisine de la MÊME classe garde le cas nul. La collection d'une entité neuve est nulle (Hibernate ne l'initialise qu'au chargement).

Falsifié sur quatre variantes : gamme + aucune ligne → `status:-1`, NPE, **rien de persisté** ; sans gamme → succès ; gamme + une ligne de composant → succès ; nomenclature EXISTANTE à laquelle on ajoute une gamme → succès. Par le configurateur l'erreur arrive en `status:0` + `error`, par `/ws/rest` en `status:-1` + `causeStack` : deux formes pour un même bug.

**Correctif de seed** : toute nomenclature qui porte une gamme reçoit au moins une ligne de composant dans le même lot. Aucune perte de données à craindre, la transaction est bien annulée — mais un seed qui crée les nomenclatures avant leurs lignes échouera sur celles-là.

### 100. Une nomenclature SANS gamme rend un ordre de production VIDE : zéro OF, en succès, sans un message

`ProductionOrderSaleOrderMOGenerationServiceImpl.generateManufOrders` commence par `if (billOfMaterial.getProdProcess() == null) { return null; }` — un `return` nu, sans exception et sans message. L'ordre de production, lui, est bien créé. Mesuré : trois ordres de production créés, **zéro ordre de fabrication**, réponse en succès, ni info ni alerte, **rien dans TraceBack**. Falsifié en attachant une gamme aux deux nomenclatures et en rejouant : les OF sont apparus.

À l'écran, un jeu de démo dans cet état montre des ordres de production vides et personne ne sait pourquoi. Contrôle avant livraison : `SELECT id FROM production_bill_of_material WHERE prod_process IS NULL;` sur les nomenclatures censées être fabriquées.

Attention à la combinaison avec le piège 99 : la gamme est **obligatoire** pour l'OF, et une ligne de composant est **obligatoire** pour que la nomenclature s'enregistre. Les deux, ou rien.

### 101. Générer un OF depuis une commande exige `sale_supply_select` ∈ {3,4} sur le produit ET `qty_to_produce > 0` sur la ligne

`isGenerationNeeded` combine trois conditions : `isLineHasCorrectSaleSupply` (la ligne doit être en 3 `SALE_SUPPLY_PRODUCE` ou 4 `FROM_STOCK_AND_PRODUCE`), `computeQuantityToProduceLeft(line) > 0` (qui lit `sale_order_line.qty_to_produce`), et l'absence de blocage de production. La commande doit par ailleurs être confirmée.

Le piège est le message : quand une seule de ces conditions manque, l'application répond « Il n'y a pas d'ordre de fabrication ou de production à générer pour une des lignes sélectionnées » — ce qui se lit comme un échec de la chaîne alors que c'est un filtre qui écarte la ligne. Trois de ces filtres ont dû être levés successivement avant qu'un bout en bout puisse être mesuré.

**Correctif de seed** : le produit fabriqué porte `sale_supply_select = 3`, et la ligne de commande porte `qty_to_produce` (le chemin configurateur le renseigne seul, une ligne créée en SQL ou par API non). Et l'action attend les lignes **sélectionnées dans le contexte** (`Model::isSelected`) : les passer avec `selected = true`, en dictionnaires MINIMAUX (`{id, selected}`) — renvoyer les lignes telles que `/ws/rest` les rend fait échouer `Context.asType` sur « Class SaleOrderLine$ByteBuddy$… is not an entity ».

### 102. Configurateur : une formule sans indicateur correspondant est ignorée EN SILENCE, et éditer une formule périme toutes les instances

Deux faits qui rendent un configurateur de démo faussement prêt.

**Formule sans indicateur.** Le produit généré est rempli depuis `jsonIndicators`, pas depuis les formules. Une formule ajoutée sans que les indicateurs soient régénérés est donc persistée, visible à l'écran, et **sans aucun effet** — la génération rend `status:0` et un produit incomplet. Les indicateurs se régénèrent par l'action d'activation du créateur (`action-configurator-creator-method-update-activate`) : après toute retouche de formule, la rejouer.

**Version.** `action-configurator-creator-record-desactivate` est câblée sur le `onChange` des panneaux de formules : modifier UNE formule désactive le créateur ET incrémente sa version, ce qui périme d'un coup toutes les instances déjà créées — leur régénération rend « La version du configurateur est différente de celle de son modèle » et aucun produit. C'est voulu, mais pour un jeu de démo cela signifie : figer les formules AVANT de créer les instances de démonstration.

Un produit généré n'est par ailleurs **pas vendable** sans famille ni catégorie de produit : voir piège 11.bis.

### 103. Attributs de configurateur seedés par API : cinq colonnes `context_field*`, un `on_change`, et parfois un redémarrage

Les attributs d'un `ConfiguratorCreator` sont des lignes `meta_json_field` **contextuelles**. Trois exigences, chacune silencieuse quand elle manque :

1. **Les cinq colonnes de contexte** — `context_field = 'configuratorCreator'`, `context_field_target`, `context_field_target_name`, `context_field_title`, `context_field_value = '<id du créateur>'`. Sans elles la ligne existe, le seed paraît réussi, et le formulaire n'affiche **aucun champ de saisie** : un attribut non contextualisé n'appartient à aucun créateur.
2. **`on_change = 'action-configurator-update-indicators'`** sur CHAQUE attribut. Sans lui l'écran ne recalcule jamais les indicateurs pendant la saisie, et la génération échoue sur « Veuillez configurer un script pour renseigner le code du produit créé ». Les créateurs du jeu de démo AOS le portent sur tous leurs attributs — c'est la référence à imiter. Un harnais qui appelle `update-indicators` lui-même masque complètement le défaut.
3. **Un redémarrage a été nécessaire** lors de ce seed (constat d'exécution, cause non établie). Ce n'est pas le cache des champs personnalisés : en 8.2.3, `MetaStore.findJsonFields` relit `meta_json_field` en base à chaque vue (piège 209). Avant de redémarrer, recharger la page du créateur de configurateur et vérifier les indicateurs ; ne redémarrer que s'ils restent absents, et noter ce qui a changé.

Et à la saisie : la colonne `attributes` d'un `Configurator` se poste en **CHAÎNE JSON**. Postée en objet, `/ws/rest` répond `status:0` et n'écrit rien, sans le moindre signalement. Une génération réussit quand même (les attributs sont lus dans le CONTEXTE), mais la colonne reste NULL — et toute duplication ultérieure repart de l'enregistrement, retombe sur les branches de repli `?:` des formules et rend un produit DIFFÉRENT en silence.

## DPGF et bilan d'affaire (module axelor-construction)

`[prouvé 9.1.6 / EE 8.2.3 / axelor-construction 9.1.0-SNAPSHOT, 2026-09-03]` — établi en produisant
2 affaires héros et leurs 2 bilans complets sur `<base>`. Ces faits sont **propres au
module `axelor-construction`** : ils ne valent pour aucune base AOS qui ne le porte pas.

### La DPGF a trois niveaux, et le bilan ne lit pas le même niveau pour chaque montant

Le décomposé d'un marché de travaux vit dans `sale_sale_order_line` (cf. `entites-ventes.md` §7),
hiérarchisé par `parent_sale_order_line` et typé par `construction_type_select` :

| `construction_type_select` | Niveau | Porte quoi |
|---|---|---|
| 10 | chapitre (titre de lot) | rien de chiffré ; `construction_detail_type_select` reste NULL (piège 89) |
| 20 | ouvrage | la quantité d'ouvrage et le prix de vente |
| 30 | sous-détail | le déboursé, les frais généraux et **le temps de main-d'œuvre** |

`construction_detail_type_select` sur les sous-détails : 1 fourniture, 2 main-d'œuvre, 3 matériel,
5 service.

Attention : **Un sous-détail ne porte aucun montant de vente.** Le recalcul AOS de l'en-tête somme *toutes*
les lignes : un prix posé au niveau 30 double le marché.

### Le budget de temps ne se calcule que sur les sous-détails de main-d'œuvre

`ConstructionTimeBudgetServiceImpl.hasRealizationTime()` ne retient que les sous-détails de
main-d'œuvre, et le budget vaut :

```
soldHours = construction_realization_time × ligne.qty × PARENT.qty
```

*Coût payé faute de le savoir* : DPGF construite à deux niveaux → budget **0 h**, consommé 3 022 h,
**restant −3 022 h** affiché sur l'écran du fil rouge, ce qui se lit comme une panne. Puis, en
corrigeant, second piège : oublier le facteur `PARENT.qty` donne le temps **unitaire**, trois ordres
de grandeur trop bas.

Corollaire — **ne pas recopier un référentiel d'ouvrage sans vérifier qu'il est cohérent avec cette
formule.** Dans `construction_construction_ouvrage_detail_line`, la ligne de main-d'œuvre du
catalogue porte tantôt `qty = 1` + `realization_time = heures`, tantôt `qty = heures` +
`realization_time = heures`. Recopiée telle quelle, la formule à trois facteurs **élève les heures
au carré** : 64 h au lieu de 8 sur `OUV-CVC-VMC` et `OUV-ELEC-TGBT2`, +35 % sur le budget du
chantier. Encoder la forme que le moteur attend, et asserter le budget reconstitué contre le temps
publié au niveau ouvrage.

### `main_sale_order` est la FK par laquelle le bilan agrège — la laisser NULL donne un bilan à zéro

`ConstructionSaleOrderHelperServiceImpl.getWorkLineListByMainSaleOrder()` filtre
`self.mainSaleOrder = :so AND self.constructionTypeSelect = :work`. `main_sale_order` n'est donc pas
qu'une dénormalisation posée au save (`entites-ventes.md` §7) : c'est le chemin d'agrégation du
déboursé et des frais généraux du bilan d'affaire. Un INSERT SQL doit la poser explicitement, dans
le même mouvement que `sale_order`.

*Coût payé* : c'est le défaut le plus coûteux du périmètre, et il est **silencieux** — vendu et
déboursé à **zéro** sur les 12 montants du bilan, sans erreur, sans log.

### Les tâches dérivées de la DPGF sortent du moteur incomplètes

`action-construction-project-method-regenerate-missing-tasks` crée les tâches depuis la DPGF avec
`type_select`, `is_private`, `assigned_to` et `task_date` posés, mais **`status` et `full_name` à
NULL** — les deux colonnes de visibilité et de lisibilité de `project_project_task`
(`entites-projet-temps.md` §2). *Coût payé* : 85 tâches en base, panneau « Phases et tâches » à
« 0 à 0 sur 0 » et « RAT incomplet — aucune tâche » sur la fiche héros. C'est le troisième cas de la
règle 12 : compléter en SQL après la génération, avant la passe moteur suivante.


### 119. Nomenclature et gamme INVISIBLES dans le sélecteur d'un ordre de fabrication : `statusSelect = 3` ET atelier vide

**Symptôme :** la nomenclature existe, se cherche dans sa propre liste, et **n'apparaît pas** dans
le sélecteur d'un OF. Aucune erreur, aucun log. Le piège 10 ne couvre PAS ce cas : il porte sur la
visibilité en liste (`type_select`), pas sur le sélecteur de l'OF, qui a son propre domaine.

Le champ `billOfMaterial` de la vue `ManufOrder` porte :

```
domain="self.defineSubBillOfMaterial = true AND self.statusSelect = 3
        AND ((:workshopStockLocation IS NULL AND self.workshopStockLocation IS NULL)
             OR self.workshopStockLocation = :workshopStockLocation)"
```

Deux conditions, et la seconde est contre-intuitive.

- **`statusSelect = 3` (Applicable).** Une nomenclature seedée à `1` (Brouillon) est exclue.
  Même sélection sur la gamme : `production.prod.process.status.select` = `1 Draft / 2 Validated /
  3 Applicable / 4 Obsolete`.
- **L'atelier doit être VIDE.** Sur un OF **neuf**, `workshopStockLocation` est NULL — il n'est
  renseigné qu'**après** le choix de la nomenclature, dont il est recopié
  (`ManufOrderServiceImpl` : `manufOrder.setWorkshopStockLocation(billOfMaterial.getWorkshopStockLocation())`).
  Une nomenclature qui porte un atelier n'est donc **jamais** proposée à la création. Le symptôme
  trompeur : la valider à la main ne change rien, ce qui fait chercher du côté du statut.

La gamme subit les deux mêmes conditions, dans l'action-attrs
`action-manuf-order-attrs-filter-prodProcess`.

**Correctif de seed.** Sur un site unique — le cas de la quasi-totalité des démos — laisser
`workshop_stock_location` à NULL sur la nomenclature ET sur la gamme, et poser `status_select = 3`.
Ne renseigner l'atelier que si la démo porte réellement plusieurs ateliers, et alors le poser aussi
sur les OF. Garde à écrire : rejouer le domaine tel quel et compter, plutôt que de vérifier
colonne par colonne.

Vérifié sur AOS 9.1.4.

### 120. Une gamme qui consomme depuis un emplacement SANS stock ne lève rien — l'OF affiche tous ses composants manquants

`ProdProcess.stockLocation` (« Production stock location ») est la **source depuis laquelle les
composants sont consommés**. Si le stock a été semé ailleurs — typiquement sur l'entrepôt principal
alors que la gamme pointe une zone d'atelier — l'OF planifie ses sorties depuis un emplacement
**vide** : tout ressort manquant, sans une erreur, et le calcul des besoins propose de tout acheter.

C'est d'autant plus facile à rater que les deux objets sont seedés par des lots différents : le
stock par le lot stock, la gamme par le lot production. Rien ne les confronte.

**Garde à écrire dans le lot production**, elle coûte trois lignes :

```sql
SELECT count(*) FROM production_prod_process pp
 WHERE pp.import_origin = :tag
   AND NOT EXISTS (SELECT 1 FROM stock_stock_location_line l
                   WHERE l.stock_location = pp.stock_location AND l.current_qty > 0);
-- doit rendre 0
```

Le fallback, quand `stockLocation` est NULL, est
`stockConfigService.getComponentDefaultStockLocation(manufOrder.getWorkshopStockLocation(), stockConfig)` :
utile à connaître, mais s'en remettre à lui rend l'emplacement de consommation implicite et
dépendant de la config société. Poser la valeur explicitement.

### 121. `producedProductStockLocation` décide où atterrit le produit fini, et les sous-ensembles doivent atterrir là où le parent consomme

`ProdProcess.producedProductStockLocation` est l'emplacement où l'OF **sort** son produit fini
(`ManufOrderStockMoveServiceImpl._getProducedProductStockLocation`). Le laisser sur la zone de
production fait apparaître les produits finis au milieu de l'atelier au lieu du magasin : sans
conséquence technique, mais visible et faux sur l'écran des stocks.

**Le point qui casse vraiment, sur une nomenclature à plusieurs niveaux :** si les OF de
sous-ensembles déposent ailleurs que là où l'OF parent consomme, **le parent ne les retrouve pas**.
Règle simple et suffisante : les sous-ensembles atterrissent à l'emplacement de consommation, les
produits finis vendables au stockage produits finis.

**Ce que le modèle ne fait PAS, et qu'on croit volontiers qu'il fait.** Il n'y a pas de chaînage
d'opérations d'un emplacement à l'autre — l'en-cours ne « voyage » pas de zone en zone :

- `ProdProcessLine.stockLocation` n'est pas l'endroit où l'opération dépose son en-cours. C'est
  **sa source de consommation**, et le code ne la lit **que si** `isConsProOnOperation = true`
  (`OperationOrderStockMoveServiceImpl`).
- Ce drapeau exige de déclarer les composants **opération par opération**, dans
  `ProdProcessLine.toConsumeProdProductList` — une liste **non dérivée de la nomenclature**
  (`OperationOrderServiceImpl.createToConsumeProdProductList`). Sans elle, les opérations n'ont
  rien à consommer.
- `OperationOrder` n'a **ni liste de produits à produire ni emplacement** : une opération ne dépose
  rien.

Conséquence de seed : ne pas promettre le chaînage par phases sur la foi des colonnes. Avant de
l'activer, vérifier dans les processus du client si son atelier sort réellement les pièces
opération par opération, ou une seule fois avant montage — le second cas est le plus courant, et il
se modélise au niveau de l'OF.

### 122. Une quantité NÉGATIVE en nomenclature passe l'import sans un mot et bloque au lancement de l'OF

**Symptôme, et il arrive tard :**

```
Validation failed for com.axelor.apps.stock.db.StockMoveLine
'doit être supérieur ou égal à 0' — propertyPath=qty, puis realQty
```

L'insertion de la ligne de nomenclature, elle, passe : la contrainte est portée par
`StockMoveLine`, pas par `BillOfMaterialLine`. Le défaut ne se révèle donc qu'au **lancement**,
souvent devant quelqu'un.

**Ça n'est presque jamais une faute de frappe.** Cas rencontré : le fichier de chiffrage du client
exprimait ses options **en écart par rapport à la configuration de base** — monter le frein central
*retire* 2 roulettes arrière, monter la poignée ergonomique *retire* la poignée standard et son
kit de câbles. Un tableur porte ça sans difficulté ; une nomenclature ERP non.

**Quoi en faire.** Retirer les lignes négatives — il n'y a pas d'alternative, le moteur les refuse —
mais ne pas les faire disparaître :

1. écrire la déduction **en note sur la nomenclature**, pour qu'elle reste lisible à l'écran ;
2. **chiffrer l'écart de déboursé** que le retrait produit, et vérifier s'il se propage aux
   nomenclatures parentes ;
3. le dire au client comme un **point d'architecture** : la logique de déduction est précisément ce
   qu'un configurateur modélise. C'est un argument, pas une excuse.

**Garde à écrire** : `SELECT count(*) FROM production_bill_of_material_line WHERE COALESCE(qty,0) <= 0`
doit rendre 0 avant de déclarer le lot production terminé. Le mettre dans le lot, pas dans l'audit
final : à ce stade l'OF a déjà échoué devant quelqu'un.

---

## Piloter le moteur de fabrication par l'API — mesures du 2026-09-22

> `[prouvé REST 9.1.3 / AOP 8.2.2]` sur une passe de **250 ordres de fabrication**. Les cinq pièges
> qui suivent ont chacun coûté un aller-retour complet. Ils se lisent ensemble : 125 donne l'ordre
> des passes, 126 la shape à écrire, 127 et 128 le nettoyage qu'elles imposent, 129 le cas où tout
> le reste est inutile parce que la nomenclature est fausse.

### 125. Démarrer puis Terminer un ordre par script rend un coût réel de ZÉRO — et le correctif a trois temps

`action-manuf-order-method-start` et `action-manuf-order-method-finish` écrivent **l'instant présent**,
sans condition (même mécanisme que le §6 de `pieges-runtime-aos-9-1-7.md` pour les mouvements de
stock). Enchaînées par un script, elles sont séparées de quelques millisecondes :
`production_operation_order.real_duration` vaut **0** sur toutes les opérations, et la feuille de coût
réelle sort à **0,00 €**. *Mesuré sur 30 ordres d'une première passe, puis 96 d'une seconde.*

Le résultat est un succès du point de vue du moteur : `status: 0`, une feuille créée, aucun message.
C'est une démo dont l'écran « coût réel » est vide sans que rien ne l'annonce.

**Correctif, en trois temps dont l'ordre n'est pas négociable :**

1. **SQL** — poser `real_start_datet`, `real_duration` et `real_end_datet` dérivés des dates
   **planifiées**, avec un écart déterministe tiré de l'identifiant, jamais constant (formule du
   piège 26, qui garde l'`UPDATE` idempotent et évite l'effet « trop parfait »).
2. **Redémarrer l'application.** Sans cela le cache de second niveau sert les anciennes durées
   (pièges 52 et 96) et l'étape 3 recalcule **le même zéro**.
3. **Rappeler `action-manuf-order-method-compute-cost-price`** sur chaque ordre — en tenant compte
   du piège 127 (il ajoute une feuille) et du piège 128 (la purge des périmées est récursive).

Attention : Cette séquence est l'exception cadrée à la garde de `socle-aos-baseline.md` §6 (« ne jamais
relancer un calcul de coût après un redatage »). La garde vaut quand le flux a produit des durées
**justes** qu'un redatage ne doit pas détruire. Ici le moteur a produit des durées **nulles** : il
n'y a rien à préserver, et le recalcul est le seul moyen d'obtenir une feuille non nulle. Distinguer
les deux cas avant d'appliquer l'une ou l'autre.

*Non mesuré* : si une invalidation ciblée du cache suffirait à la place du redémarrage complet, et
ce que coûte cette contrainte sur un environnement partagé où le redémarrage est interdit.

### 126. « Démarrer » ne touche que l'en-tête : les opérations restent Planifiées, sans date réelle

`action-manuf-order-method-start` fait passer l'ordre au **statut 4** et lui pose `real_start_datet`.
**Ses opérations restent au statut 3 (Planifié)**, sans aucune date réelle. Un ordre « en cours »
crédible — celui qu'on ouvre en démo — ne sort donc pas du moteur : il s'écrit en SQL, opération par
opération.

Shape à poser sur les opérations d'un ordre en cours :

| Opérations | `status_select` | Temps |
|---|---|---|
| les premières | **6** (terminé) | `real_start_datet` / `real_duration` / `real_end_datet` posés |
| **une** seule | **4** (en cours) | `real_start_datet` posé, `real_end_datet` NULL |
| les suivantes | **3** (planifié) | `real_duration = 0`, jamais NULL (tableau `production_operation_order` ci-dessus) |

**Effet de bord utile** : c'est la seule manière de fabriquer un ordre porteur d'une opération « En
cours » — le seul objet capable de faire lever le refus de replanification d'AOS, donc le seul qui
permette de démontrer ce refus.

### 127. `compute-cost-price` AJOUTE une feuille de coût, il ne remplace pas la précédente

Rappelé sur un ordre qui porte déjà une feuille, `action-manuf-order-method-compute-cost-price` en
crée une **seconde**. Rien ne le signale, et l'écran affiche la liste — le présentateur voit deux
feuilles pour un ordre. *Mesuré : 98 ordres recalculés → **89 feuilles périmées** à purger.*

C'est le mécanisme derrière l'observation de `socle-aos-baseline.md` §6 (« un flux laisse des feuilles
de coût parasites : 3 feuilles pour un seul ordre »), qui constatait le symptôme sans le nommer.

**À prévoir dès l'écriture de la passe** : ne garder que la **dernière feuille par ordre et par type
de calcul**, et faire de ce contrôle une garde du lot, pas une ligne d'audit final.

```sql
-- Feuilles à purger : tout sauf la plus récente par (ordre, type de calcul)
SELECT id FROM (
  SELECT cs.id,
         row_number() OVER (PARTITION BY cs.manuf_order, cs.calculation_type_select
                            ORDER BY cs.id DESC) AS rang
    FROM production_cost_sheet cs
) t WHERE rang > 1;
```

### 128. Les lignes filles d'une feuille de coût ne portent PAS la référence à la feuille — la purge est récursive ou elle échoue

`production_cost_sheet_line.cost_sheet` n'est renseigné que sur les lignes **racines** ; toutes les
descendantes ne portent que `parent_cost_sheet_line` (fait déjà noté en `socle-aos-baseline.md` §6 —
ici c'est sa conséquence en suppression qui est neuve).

Deux échecs symétriques, tous deux rencontrés :

- `DELETE FROM production_cost_sheet WHERE id IN (...)` **échoue sur une contrainte de clé
  étrangère** : les lignes racines pointent encore la feuille ;
- `DELETE FROM production_cost_sheet_line WHERE cost_sheet IN (...)` **passe** et laisse toutes les
  descendantes **orphelines** — invisibles à tout contrôle qui compte par `cost_sheet`.

Purge correcte : descente **récursive** par `parent_cost_sheet_line`, puis suppression des feuilles de
l'arbre **vers la racine**, en boucle jusqu'à épuisement.

```sql
WITH RECURSIVE arbre AS (
  SELECT id, parent_cost_sheet_line FROM production_cost_sheet_line
   WHERE cost_sheet IN (/* feuilles à purger */)
  UNION ALL
  SELECT l.id, l.parent_cost_sheet_line
    FROM production_cost_sheet_line l JOIN arbre a ON l.parent_cost_sheet_line = a.id
)
SELECT count(*) FROM arbre;   -- mesurer avant de supprimer
```

*Mesuré : 89 feuilles périmées = **561 lignes** réparties sur plusieurs niveaux.* Un `DELETE` à plat
en aurait laissé la majorité derrière lui.

### 129. Une nomenclature auto-référencée rend un coût de zéro, sans erreur et sans feuille

Dans le jeu de données client rencontré, chaque `production_bill_of_material_line.product` pointe vers
**le même article que l'en-tête de la nomenclature** : la nomenclature se contient elle-même.
`action-manuf-order-method-compute-cost-price` répond alors `status: 0` et **ne crée aucune feuille** —
silencieux, strictement indiscernable d'un succès pour un script qui ne lit que le statut.
*Mesuré : **9 ordres sur 250** concernés.*

C'est la même famille que les pièges 99 (nomenclature sans ligne → NPE) et 100 (nomenclature sans
gamme → zéro OF en succès) : une nomenclature fausse ne se signale jamais à l'endroit où elle casse.

**Détection, à passer AVANT la passe moteur** — sur les nomenclatures reçues comme sur celles qu'on
écrit :

```sql
SELECT bom.id, bom.name, count(*) AS lignes_auto_referencees
  FROM production_bill_of_material bom
  JOIN production_bill_of_material_line bl ON bl.bill_of_material_parent = bom.id
 WHERE bl.product = bom.product
 GROUP BY bom.id, bom.name;
```

Attendu : **0 ligne**. Un résultat non vide se remonte comme un défaut de la donnée d'entrée, pas
comme un incident de la passe.

## Gamme : continuité des opérations — lecture de code du 2026-09-24

### 148. Gamme à `operation_continuity` NULL : l'ordre de démarrage des opérations est IMPOSÉ, comme si la case était cochée

`[lu dans le code 9.1.3, non observé à l'exécution, 2026-09-24]`
`OperationOrderWorkflowServiceImpl.canStartOperationOrder` (l.459) ne laisse démarrer n'importe quelle
opération que si la valeur est explicitement `false` ; à `true` **ou NULL**, seule l'opération de
priorité courante démarre (`ManufOrderWorkflowServiceImpl.setOperationOrderMaxPriority`, l.644, ne sort
tôt que sur `false`). Le réglage d'application `operationContinuitySelect` (0 aucune, 1 optionnelle,
2 par défaut) n'agit que sur la vue gamme : case cachée à 0, cochée par défaut **à la création** à 2
(`ProdProcess.xml` l.208-211 et l.249-252) — jamais sur les gammes existantes. Démo industrielle : 238 gammes
sur 243 à NULL.

**À faire :** poser `operation_continuity` explicitement (règle 3) ; ne pas promettre qu'un changement
du réglage d'application modifie les gammes déjà créées. **Garde :** aucune dans
`scripts/audit-completeness.sql`.

## Peupler le module Construction par l'API — rejeu de la démo BTP de référence (25-26/09/2026)

`[prouvé AOS 9.1.7 / AOP EE 8.2.4-SNAPSHOT / axelor-construction 6c56275f, 25-26/09/2026, env local, répétition
locale, instance hébergée]` — établi en rejouant par l'API (REST + `/ws/action`) un jeu
complet : 16 devis, 14 chantiers, situations, factures, règlements, achats, pointages, paie (scripts
du **dossier de rejeu**, fourni par l'utilisateur et non livré avec ce skill). Les entrées 176 à 181 datent du 26/09,
avec des correctifs du module déployés en local. Chaque entrée porte en plus sa preuve. Propre au module
`axelor-construction`. Complète la section DPGF ci-dessus. Méthode du rejeu contrôlé : `methode-rejeu-controle.md`.

Trois pièges de transport, lus dans le bytecode déployé puis constatés à l'exécution (25/09/2026, AOP EE 8.2.4-SNAPSHOT) :

- `fetch` n'accepte que **POST** : `POST /ws/rest/<modèle>/<id>/fetch` (en GET : 405, bytecode `RestService.fetch`
  d'`axelor-web-enterprise` 8.2.4-SNAPSHOT) ; pour relire, `POST` avec `{}` ou `GET /ws/rest/<modèle>/<id>`. (Même route en
  POST en AOP 8.1.2 et 8.2.2, lu dans le code le 15/10/2026 : le piège 132 l'écrit ainsi.)
- Une reprise de groupe d'actions renvoie `pending = "<groupe>[n]"` : la poster dans le **corps** de `POST /ws/action`,
  jamais dans l'URL (Tomcat 10.1 refuse les crochets).
- Confirmer un devis exige le statut finalisé (2) : appeler d'abord `action-group-sale-order-finalize-quotation`
  (`SaleOrderConfirmServiceImpl.confirmProcess`).

### 155. Un devis BTP créé par REST n'est BTP qu'avec son drapeau et son initialisation — et il naît hors sélection, en marché privé avec l'avance par défaut

La création REST n'exécute aucun `onNew` (piège 131). Trois conséquences, toutes silencieuses :

- **Pas de devis BTP sans drapeau.** `constructionIsConstructionOrder` vaut faux par défaut, et
  `initConstructionSaleOrder` ne fait rien tant qu'il l'est (lu dans le code le 24/09,
  relecture adverse, point B4). Poser le drapeau dès la création, puis appeler
  `action-construction-sale-order-method-init-construction` avec l'enregistrement entier (piège 132) et
  **enregistrer** les valeurs qu'elle rend par `setValue` : le contrôleur ne persiste rien. `creationDate`, devise,
  condition et mode de paiement se posent aussi à la création. Les menus BTP filtrent sur ce drapeau et sur le type de
  devis (`entites-ventes.md` §6). À l'écran, même symptôme quand `axelor-portal` est
  installé : son `onNew` remplace celui du module et le devis naît sans « Mode chantier » (constaté le 26/09 sur un autre
  environnement).
- **Hors sélection.** `statusSelect` et `constructionTaskGranularitySelect` restent à **0**. La finalisation exige
  `statusSelect = 1` ; la granularité à 0 se recopie telle quelle sur le chantier
  (`constructionDashboardGranularitySelect`, `ConstructionProjectGenerationServiceImpl` : seule une valeur nulle
  déclenche le repli sur le réglage de l'app).
- **Marché privé avec l'avance par défaut.** L'initialisation BTP met tout devis en marché privé, avec l'avance par
  défaut de l'app (5 % dans la démo).

**À faire :** dès la création, le drapeau, `statusSelect = 1`, la granularité (1 chapitre, 2 ouvrage), le type de
marché (`constructionMarketTypeSelect` 1 privé, 2 public) et le taux d'avance. Ce taux est un choix métier : la démo
BTP de référence a retenu 0 % en marché privé, l'avance forfaitaire étant un mécanisme des marchés publics (arbitrage de
l'utilisateur du 25/09). *Constaté au premier jet du 25/09 ; appliqué par le script de rejeu aux 16 devis, jusqu'au rejeu hébergé du
26/09.*

### 156. « Créer le chantier » recopie l'en-tête du devis — tout poser AVANT, puis renommer chantier ET dépôt

Le bouton = `action-construction-method-enrich-project-post-generation` puis
`action-construction-method-recompute-market-time-budget`, après finalisation (2) et confirmation (3) ; jamais
« Projet automatique » (plante sur un devis BTP). Il **recopie** site, type de marché, lot, date de démarrage (début
contractuel), durée, délai de libération de la retenue, maître d'ouvrage et granularité
(`ConstructionProjectGenerationServiceImpl`, relu le 26/09) : un en-tête vide donne un chantier vide. Il nomme le
chantier « SO…-client_project » et crée le dépôt « Site - <nom> ».

**À faire :** en-tête complet avant la confirmation — adresses de facturation (+ `mainInvoicingAddressStr`) et de
livraison (adresse du chantier), un `base_site` par chantier (vide dans la démo : `code`, `name`, `company`,
`typeSelect` 2 et **`invoicingTypeSelect` 4** obligatoires, ce dernier ajouté par business-project), lot,
début = ordre de service, durée en jours, délai de retenue, commercial, équipe, dépôt, contact, fin de validité,
description. Après : renommer le chantier (le `fullName` se recalcule à l'enregistrement REST) et son dépôt, poser
MOE, BET, zone, membres ou partage aux salariés, responsable, contact, dates, date de notification, fin
contractuelle. Confirmer à la date d'**acceptation** (date de commande) ; l'ordre de service reste le début
contractuel. *Constaté au premier jet du 25/09 et relevé
par l'utilisateur sur les fiches.*

### 157. « Planning du chantier » plante au premier clic — planning créé d'avance, APRÈS le renommage

`ConstructionProjectPlanningController.openProjectPlanning` passe au service l'objet reconstitué depuis le contexte
(`asType`) sans le relire ; le service l'ajoute à un nouveau `ProjectPlanning` et enregistre → « Project … name ne
doit pas être nul », sur TOUT chantier sans planning (anomalie du module, constatée le 25/09).

**À faire :** créer par l'API un `com.axelor.apps.projectscheduler.db.ProjectPlanning` nommé « Planning - » +
`fullName` **exact** du chantier, `projectSet` = [chantier], `projectScopeSelect` 1, `horizon` 2, `employeeSet`
non vide. Le service le retrouve et n'enregistre rien. Le nom suit le `fullName` : le créer après le renommage du
piège 156 (fait ainsi sur les 14 chantiers du rejeu hébergé).

### 158. Synthèse matière vide sans produit sur les sous-détails — réutiliser les produits BTP de la démo

La synthèse matière du devis groupe les sous-détails par **famille puis catégorie de produit**
(`views/ConstructionMaterialSynthesis.xml`) : un sous-détail sans produit n'y groupe rien. La démo du module livre
207 produits : 162 `BTP-MAT-*`, 24 `BTP-MO-*`, 14 `BTP-ENG-*`, 7 `BTP-SVC-*` (familles Matériaux / Main d'œuvre /
Matériel BTP, catégories par corps d'état ; `apps/demo-data/fr/base_product.csv` du module, relu le 26/09) : les
réutiliser plutôt qu'en créer (règle zéro). Le produit n'altère pas le montant :
le serveur recalcule depuis `constructionPuDebourse` (0,00 € d'écart mesuré sur 16 devis le 25/09). Un produit
« approchant » (même catégorie, désignation de ligne conservée) vaut mieux que rien, mais se liste comme tel. Effet
de bord : piège 165.

### 159. La sauvegarde de l'arbre accepte tous les champs de complétude d'une ligne

`action-construction-tree-method-save-lines` (`ConstructionTreePayloadMapper`) lit sur chaque ligne neuve
`product`, `description`, `constructionCodeBpu`, `constructionOuvrage`, `constructionForecastDisbursementDate`, en
plus des montants. Les poser dans la charge utile coûte zéro appel de plus. **Le lien ouvrage se pose sur l'ouvrage
(type 20), JAMAIS sur un sous-détail** : la grille affiche alors le sous-détail en « Sous-Ouvrage »
(`axelor-react-btp/…/TreeRow.tsx:349-358`). *Coût payé le 25/09 : 898 sous-détails affichés « Sous-Ouvrage », vus
par l'utilisateur à l'écran, lien vidé en SQL — la base de référence le porte à 100 % parce qu'elle a été
peuplée en SQL (règle : un champ de la référence ne se copie que si l'écran le produit).* Rappels : `sale_order` est
vide **par conception** sur les lignes non racines (`ConstructionTreeSaveServiceImpl`) ; les valeurs initiales
(`construction_initial_*`) ne se posent que sur un devis d'exécution ou la copie d'un avenant. Frais généraux et
marges se saisissent par sous-détail : la marge **par nature** (fourniture, main-d'œuvre, matériel, service) se pose
là.

### 160. Situation de travaux : quatre prérequis, un avancement en INCRÉMENT — et le marché-cadre ne rattache que le devis qui le crée

La facture de situation exige : un marché sur le chantier (bouton « Créer le marché-cadre », qui exige l'**app
Contrats active ET sa démo**, sinon « séquence pour les contrats manquante ») ; une condition de paiement « RG » par
taux, COMPLÈTE (principal + échéance `isHoldback`), déclarée dans l'App BTP ; la taxe par défaut de l'App BTP (sinon
lignes sans TVA, ventilation refusée) ; une adresse de facturation client (`ValidateState:79-86`).
`applyGlobalProgress` applique l'avancement **de la période** (précédent + période ≤ 100 %), pas le cumul : convertir
les cumuls du scénario en incréments. *Constaté au premier jet du 25/09.*

**Le marché-cadre ne rattache que le devis qui le crée** (`ConstructionContractServiceImpl` pose
`saleOrder.setContract` une seule fois, à la création). Avenants, travaux supplémentaires et devis frères d'un même
marché (lotissement) restent hors marché ; aucun bouton ne les rattache. *Constaté à l'écran le 26/09 (diagnostic V3,
remarque 2) : le marché de Jean-Macé ne listait que le
devis initial.* **À faire :** poser `SaleOrder.contract` par l'API sur chaque devis du marché après sa création.

### 161. Les retenues du module pointent vers des produits vides — repointer par la retenue, par le code

Les 4 `ProjectHoldBack` pointent vers des fiches produit VIDES (liaison du data-init du module, correctif non
fusionné au 26/09) alors que le module livre `BTP-PROD-RG-ST`, `BTP-PROD-AVANCE`, `BTP-PROD-RG-CLIENT`,
`BTP-PROD-DC4` : premier remboursement d'avance → « configuration comptable manquante pour le produit : null ».

**À faire :** pour chaque retenue, chercher le produit par son **code**, repointer la retenue s'il ne l'est pas déjà
(idempotent, compatible avec une installation corrigée), lui donner unité et comptabilité. Ne jamais viser un id ni
« la fiche vide » : elles disparaissent une fois le correctif du module livré. *Constaté au premier jet du 25/09.*

### 162. Régler une facture de situation : hors retenue, et décider sur le reste dû

Un règlement du reste dû complet est refusé (« échéance marquée retenue de garantie : régler d'abord les autres »,
`InvoiceTermToolServiceImpl:209`) : payer la somme des échéances NON `isHoldBack` et filtrer
`invoiceTermPaymentList`. L'idempotence ne se fonde pas sur « un règlement existe déjà » : la **déduction d'un
paiement direct crée elle-même un règlement** sur la facture. *Coût payé le 26/09 : les situations 2 à 6 de
Jean-Macé (≈ 488 k€ HT au relevé de référence) restées impayées derrière ce règlement de
déduction, jusqu'au 3e passage de l'étape.* Seul critère :
reste dû hors retenue > 0,01.

### 163. Paiement direct confirmé = journal DC4 obligatoire à la ventilation suivante

Dès qu'un paiement direct est confirmé sur une commande de sous-traitance, toute facture de situation suivante
génère une O.D. (débit 401 sous-traitant / crédit 411 maître d'ouvrage) dans
`AppConstruction.constructionDirectPaymentJournal` — **vide par défaut** (et sur l'instance hébergée avant le
rejeu) : « Le journal de paiement direct (DC4) n'est pas configuré… », ventilation annulée
(`ConstructionDirectPaymentMoveServiceImpl`). La confirmation est datée du jour (date simulée) et n'exige pas de
situation.

**À faire :** poser le journal (démo BTP de référence : ODA de la démo, choix de l'utilisateur) avec la configuration de l'App BTP, avant
la première situation qui suit le paiement direct. *Constaté au rejeu V2, nuit du 25 au 26/09 (00 h 45).*

### 164. Circuit de sous-traitance : URSSAF « Valide » + Kbis sur la fiche du sous-traitant

Conformité → agrément exige une pièce fournisseur (`ConstructionSupplierDocument`) de type URSSAF au statut « Valide
» (2) ET un Kbis (`ConstructionSubcontractingWorkflowServiceImpl.checkGate`, transition 2 → 3) ; la démo n'en
contient aucune, aucune n'expire seule. `nextVerificationDate` = expiration + délai du type
(`computeNextVerificationDate`), calculé par le service, pas par REST. *Constaté dans la nuit du 25 au 26/09 : pièces
créées par l'API avant le geste de sous-traitance de l'utilisateur (00 h 20).* Dater
les pièces par rapport au jour de la démo (piège 173).

### 165. Commande de sous-traitance repassée au prix d'achat du produit

L'assistant « Générer PO brouillon depuis synthèse » prend le déboursé du chiffrage (22 € le point lumineux) ; le
rattachement aux phases / la validation repasse les lignes au `purchase_price` du produit de la démo (1,45 €) : la
commande tombe de 12 790 € à 2 266,75 € HT, sous le paiement direct déjà confirmé (26/09, 00 h 37).
Conséquence directe du piège 158 (produits sur les sous-détails).

**À faire :** remettre chaque ligne au déboursé du sous-détail sous-traité de même désignation, par l'action de calcul
de ligne puis de commande avec l'enregistrement entier (piège 132) — outil
du kit de rejeu (script de remise au prix), appelé par le geste scripté
de sous-traitance, qui s'arrête de lui-même si les montants ne sont pas ceux attendus. Rattachements
de la commande : piège 180.

### 166. Lots de pointage : salarié sans contrat ni utilisateur = feuille sans société = « Date invalide »

`EmployeeServiceImpl.getDefaultCompany` lit le contrat principal, sinon l'utilisateur. Un salarié qui n'a ni l'un ni
l'autre (créé par script sans compte, faute de siège) obtient des feuilles de temps **sans société** ;
`getTimesheetQuery` filtre sur la société du chantier, ne les retrouve pas au jour suivant, en recrée une plus loin,
et la ligne tombe hors période : « Date invalide. Elle doit être comprise dans la période de la feuille de temps »
(`TimesheetLineCreateServiceImpl.checkDate`). Sans planning de jours fériés, la **validation** du lot est refusée sous
`info`, `status 0` (piège 106). Tant que le salarié n'a pas de société par défaut, pré-créer les feuilles ne suffit pas
(la 1re semaine passe, pas la suivante). *Constaté au rejeu V2, nuit du 25 au 26/09 (00 h 45).*

**À faire :** compléter les salariés comme ceux de la démo (tous portent contrat principal, planning hebdomadaire,
jours fériés, 7 h/jour) : contrat minimal (société de paie, début, fonction), « Plein temps », « Jours fériés FR ».
En reprise, un lot déjà « Généré » se valide seulement — le regénérer double les lignes. Ouverture des feuilles, jours
vides et calendrier de fériés de la démo : piège 183 ; préremplissage, zone et paie : piège 181.

### 167. Devis perdu : envoyé, puis annulé avec un motif standard

Un devis perdu laissé en brouillon ne raconte rien. Le finaliser à sa date d'émission, puis
`action-sale-order-method-confirm-cancel` (bouton « Annuler ») avec `cancelReason` = un motif standard (« Montant
trop élevé » pour un concurrent moins-disant) et `cancelReasonStr` en précision → statut 5. *Appliqué au devis FIG-2
du rejeu (25-26/09).*

### 168. Contrôler le montant d'avenant du chantier, pas le message de confirmation

À la confirmation d'un avenant, le message serveur annonce « Delta CA 21 907,58 » pour un chapitre de +10 902,80 €
(environ le double) ; `Project.constructionMarketAmendmentAmount` vaut bien 10 902,80 €. Le contrôle se fait sur le
chantier (`ConstructionMarketComputeServiceImpl`), jamais sur le message. *Constaté le 26/09 (00 h 07).*

### 176. Avancement posé par l'API : chaque enregistrement crée une ligne d'historique datée du jour simulé — le poser sur les ouvrages, une fois par date

Enregistrer `progress` sur une tâche, par n'importe quelle requête d'enregistrement qui le contient, crée une ligne
`ProjectTaskProgress` datée de la date du jour **simulée** (observateur project-pro
`ProjectProProjectTaskObserver.onSave`). Une seconde sauvegarde le même jour lève « Duplicate ProjectTaskProgress »,
et la tâche est enregistrée quand même. Créer soi-même des `ProjectTaskProgress` (saisie « MANUAL ») recopie le
dernier en date sur la tâche, et AOS recalcule le chapitre (moyenne pondérée).

Deux conséquences d'écran. Une ligne d'historique posée sur un **chapitre** fausse le graphique « Avancement pondéré
» du Bilan chantiers, qui ne filtre pas les chapitres (lu dans la vue du Bilan). Et des ouvrages d'un même chapitre à
des valeurs différentes peuvent être écrasés par l'avancement du chapitre à l'ouverture de l'onglet Pilotage (recopie
parent → enfants **lue dans le code**, `ProjectTaskProgressUpdateServiceImpl`, non observée : parade appliquée par
précaution).

**À faire :** poser l'avancement sur les **ouvrages**, même valeur pour tous les ouvrages d'un chapitre, une seule
fois par date simulée, dans la boucle chronologique ; idempotence : sauter une tâche qui a déjà une ligne à cette
date. Vérifier la jauge Exécution sur un chantier connu : sans le correctif du module (jauge Exécution), chaque avancement y
est compté deux fois (chapitre et ouvrage). *Constaté le 26/09 à 9 h 33, appliqué
ensuite : Jean-Macé de 5,4 à 47,1 % en 7 dates.*

### 177. Réceptionner un chantier ne pose pas sa fin réelle : retard et pénalité provisoire continuent de courir

`ConstructionReceptionServiceImpl.recordReception` pose la date et le type de réception, les garanties et le statut
« terminé », **pas la fin réelle**. Seule une règle d'écran la pose, au changement de statut dans la fiche
(`Project.xml`) ; un changement fait côté serveur ou par l'API ne la déclenche pas. *Constaté à l'écran le 26/09
(diagnostic V3, remarque 1 bis) : Norvalys, réceptionné le 17/07, affichait « Retard 88 j — En cours » et 35 025,76 €
de pénalité provisoire ; Maison 1, réceptionnée à temps, 1 480,29 €.*

Cas particulier du piège 186 : **l'API ne joue aucune action de changement de l'écran**, pas plus que pour la zone
d'une demi-journée de pointage, qui déclenche le panier (piège 181).

**À faire :** poser la fin réelle (= date de réception) par l'API juste après la réception ; relire le retard et la
pénalité du chantier. Norvalys est alors passé en pénalité définitive (17 j × 398,02 € = 6 766,34 €). La tuile « En
clôture (DGD) » du Bilan exige « pas de fin réelle » : un chantier réceptionné en sort, défaut du module à remonter
à l'éditeur.

### 178. L'onglet Pilotage calcule ET ENREGISTRE à son ouverture : après un peuplement par l'API, rejouer son action sur chaque chantier

À l'ouverture de l'onglet (`onTabSelect`, `action-construction-dashboard-refresh-on-load`), le module recalcule et
**enregistre** le reste à faire et l'engagé de chaque tâche. Après un peuplement par l'API, personne n'a ouvert
l'onglet : les valeurs enregistrées restent à 0, alors que ce sont elles que lisent l'API, les listes et les agents IA.
Et deux instances rejouées à l'identique divergent selon qui a ouvert quel chantier.

*Constaté le 26/09 sur la répétition : 305 écarts entre les relevés d'avant et d'après rafraîchissement, tous sur les
tâches (211 restes à faire, 94 engagés).*

**À faire :** en fin de peuplement, appeler l'action d'ouverture sur chaque chantier, avec l'enregistrement entier
(piège 132) — outil du kit de rejeu (14 chantiers en 22 s sur l'instance
hébergée le 26/09). Contrôler après ce rafraîchissement, pas avant.

### 179. Un instantané de reste à faire enregistre l'état du moment ; sa date n'est qu'une étiquette

`ConstructionRafSnapshotServiceImpl.createSnapshot` recalcule le reste à faire puis fige les valeurs **du moment** —
engagé, reste à faire, ajustements, avancement, heures — sous la date qu'on lui donne. Un instantané « au 31/08 » créé
le 26/09 porte l'état du 26/09. L'engagé ne bouge qu'avec des lignes de commande rattachées aux tâches (piège 180).

**À faire :** créer chaque instantané **dans la boucle chronologique**, quand seules les pièces antérieures à sa date
existent (commandes, factures et avancements jusqu'au 31/08, puis l'instantané du 31/08, puis la suite) ; jamais après
coup. Un contrôle dans le script refuse d'en créer un quand un instantané plus récent existe. *Constaté le 26/09
(les instantanés hebdomadaires de septembre n'ont pas pu être créés
justes en local, un instantané plus récent existant déjà).* Même famille que le piège 170.

### 180. Achats d'un chantier : trois rattachements lus par trois écrans — sans celui de l'en-tête, la déduction du paiement direct vaut 0 € en silence

Une commande d'achat d'un chantier se rattache à trois endroits, chacun lu par un écran différent :

| Rattachement | Lu par | Sans lui |
|---|---|---|
| **lignes** de commande → tâche (`projectTask`), commande validée ou plus | engagé et reste à faire (`ConstructionRafComputeServiceImpl`), grille RAF, instantanés | engagé à 0 : l'en-tête ne suffit pas, les factures ne comptent pas |
| **en-tête** d'une commande de sous-traitance → tâche du lot | déduction du paiement direct des situations (`ConstructionDc4ComputeServiceImpl.resolveProgressPercent` : `po.projectTask.saleOrderLine`) | repli sur « une seule ligne sous-traitée du devis », qui échoue : **déduction à 0 €, sans aucune erreur** |
| **en-tête** de la facture fournisseur → chantier | courbe de trésorerie, jauge Déboursé | facture invisible du chantier |

L'assistant global de commande de sous-traitance (`action-construction-po-wizard-init`) ne pose pas la tâche de
l'en-tête. Il attend le mode `global` **en minuscules** (« GLOBAL » tombe dans le mode tâche et lève une NPE), liste
toutes les lignes de déboursé du devis sans fournisseur : sélectionner les lignes (`isSelected`) et poser
`supplierPartner` soi-même ; la génération relit `lineList`.

*Coût évité le 26/09 : à la répétition, les situations 2 à 6 de Jean-Macé sortaient sans déduction du paiement direct,
sans erreur ; le relevé par l'API l'a montré avant l'instance hébergée.* Engagé et courbe : lus dans le code (diagnostic
V3, remarques 5 et 6), puis constatés à l'écran après correction. Même famille que
le piège 138 (les quatre liens d'une affaire, au niveau ligne).

**À faire :** rattacher les lignes à leur tâche, l'en-tête de chaque commande de sous-traitance à la tâche du lot
avant la situation suivante, l'en-tête de chaque facture au chantier ; contrôler la déduction sur la première
situation qui suit.

### 181. Lots de pointage et paie du module : préremplir par le bouton dédié, zone sur chaque demi-journée, paie par le chemin de l'écran

Quatre faits du 26/09, joués à l'exécution en local :

- **Le préremplissage depuis le planning est un bouton séparé**, « Pré-remplir depuis le planning »
  (`action-construction-timesheet-batch-prefill-from-planning`), pas « 1. Générer les lignes ». Sans lui, aucune
  ligne ne reçoit la tâche du planning. Il remplit chantier, tâche et zone de chaque demi-journée. Planifier en blocs
  pleins (4 h le matin, 3 h l'après-midi).
- **Le panier vient de la zone de la demi-journée** ; l'écran recopie la zone du chantier, l'API non (piège 186). Sans
  code d'export PANIER / TRAJET / TRANSPORT dans l'App BTP, la préparation de paie n'a rien à exporter (lu dans le
  code, diagnostic V3 remarque 7, puis appliqué).
- **Le lot RH « Génération des préparations de paie » échoue** sur `OtherCostsEmployee.amount` (le module y pose des
  montants à 3 décimales, refusés par le validateur ; défaut du module à remonter à l'éditeur). Chemin qui passe :
  nouvelle préparation, « Actualiser » (`action-construction-payroll-preparation-group-fill-in`), frais arrondis à
  2 décimales.
- **Un pointage sans tâche ne compte pas dans la jauge Déboursé** (jointure implicite sur la tâche, défaut du module,
  correctif proposé) : sur Jean-Macé, 1 728 lignes validées pour 225 792,00 €, 120 comptées pour 15 680,00 €, soit
  40,08 % au lieu de 62,86 %. Le préremplissage pose la tâche ;
  sinon, la poser sur chaque ligne.

Avec le module avant son correctif, les lignes générées portaient le salarié de l'utilisateur connecté, pas celui
de la ligne de lot : vérifier `line.employee = timesheet.employee` sur le premier lot. Feuilles de temps elles-mêmes :
piège 183.
