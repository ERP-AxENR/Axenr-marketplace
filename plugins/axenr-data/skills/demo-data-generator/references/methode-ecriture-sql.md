# Méthode — écriture SQL

**Pièges couverts par cette fiche :**

- 3. Les séquences doivent être relevées au-dessus de la plage d'ID de démo
- 4. Idempotence : `WHERE NOT EXISTS` plutôt que `ON CONFLICT DO UPDATE`
- 57. `v.xxx` absent de la liste `VALUES`
- 97. Appeler une `action-method` en REST SAUVEGARDE l'enregistrement

Pièges 5, 17 et 73 rattachés ici : 5 vit dans `entites-produits.md` (voir renvoi ci-dessous) ; 17 et 73 sont rangés ici par nature (technique SQL transverse, pas fait d'entité).

## Architecture des scripts SQL

**Par défaut : multi-fichiers avec un lanceur bash.** Un SQL monolithique unique n'est acceptable que pour des jeux de données triviaux (≤ 3 types d'entité, ≤ 50 lignes au total).

### Organisation recommandée

```
docs/demo/<client>/
├── 00-run-all.sh                # lanceur bash — set -euo pipefail + psql ON_ERROR_STOP=1
├── 99-cleanup.sql               # DELETE en ordre inverse des FK, scopé par import_origin (rejouable)
├── 01-org-structure.sql         # Hiérarchie TradingName + StockLocation
├── 02-catalog.sql               # Catégories + Produits + Postes de charge + Machines + ProdProcess + BoM
├── 03-customers.sql             # Tiers clients + 4 satellites (adresse + partner_address + email + company_set)
├── 04-hr.sql                    # EmploymentContractType + Employés + Contrats (+ Tiers techniques)
├── 05-sales-orders.sql          # SaleOrder + lignes
├── 06-projects.sql              # Projets business-project + lien retour SO/SOL.project
├── 07-production.sql            # ManufOrder + OperationOrder (avec planned_duration en secondes)
├── 08-timesheets.sql            # Timesheet + TimesheetLine (multi-qualification via produit/operation_order)
├── 09-invoicing.sql             # Facture + ligne de facture
├── 10-cards-groovy.sql          # (optionnel) ajuster les expressions Groovy des cartes AppProduction
├── 11..N-fix-*.sql              # corrections a posteriori pour tout problème de binding UI
```

### Pourquoi multi-fichiers

- **Point de contrôle visuel après chaque section.** Ouvrir l'interface entre les sections pour valider ; échouer vite dans le bon bloc.
- **Rollback local.** Chaque fichier a son propre BEGIN/COMMIT ; un crash en 07 n'efface pas 01–06.
- **Ré-exécution chirurgicale.** Rejouer uniquement `08-timesheets.sql` après un ajustement de taux sans retoucher le reste.
- **Charge cognitive réduite.** 9 fichiers de 100-300 lignes valent mieux qu'1 fichier de 1500.
- **Préoccupations spécifiques à un module localisées.** Si `axelor-btp` est absent sur la base cible, seuls 05/06 échouent et leurs correctifs sont isolés.

### Chaque fichier `.sql` doit

- S'ouvrir avec `BEGIN;` et se fermer avec `COMMIT;`
- Utiliser des gardes `WHERE NOT EXISTS (SELECT 1 FROM table WHERE id = N)` pour l'idempotence
- Utiliser une seule valeur `import_origin` (ex. `'DEMO-<CLIENT>-YYYY-MM-DD'`) sur chaque ligne insérée, pour la traçabilité ultérieure + le scoping du nettoyage
- Poser `version = 0`, `created_on = NOW()`, `updated_on = NOW()`, `created_by = 1`, `updated_by = 1`
- Se terminer par un **SETVAL** sur chaque séquence touchée par ce fichier
- Se terminer par un bloc de **VÉRIFICATION** `DO $$` qui lève une `NOTICE` pour les comptages attendus et un `WARNING` en cas d'écart

### Lanceur `00-run-all.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${PGHOST:?définir PGHOST}" "${PGUSER:?définir PGUSER}" "${TARGET_DB:?définir TARGET_DB}"   # mot de passe : PGPASSWORD ou fichier de mots de passe de psql
DB_OPTS="-h $PGHOST -U $PGUSER -d $TARGET_DB -v ON_ERROR_STOP=1"   # valeurs lues depuis axelor-config.properties — jamais de valeur par défaut en dur
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS=(01-org-structure 02-catalog 03-customers 04-hr 05-sales-orders 06-projects 07-production 08-timesheets 09-invoicing)
for s in "${SCRIPTS[@]}"; do
  echo ""; echo "▶ Running ${s}.sql"; echo "===================================================="
  psql $DB_OPTS -f "${SCRIPT_DIR}/${s}.sql"
  echo "OK ${s}.sql OK"
done
echo ""; echo "═══ Demo loaded. ═══"
```

`set -euo pipefail` + `ON_ERROR_STOP=1` = arrêt à la première erreur, en laissant les sections précédentes committées. Reprendre en corrigeant le fichier fautif et en relançant — les sections déjà committées sont idempotentes et sautées.

### Motif de nettoyage (`99-cleanup.sql`)

Réutilisable sur n'importe quelle base cible pour défaire un chargement de démo. Ordre : inverse des FK.

```sql
BEGIN;

DELETE FROM hr_timesheet_line          WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM account_invoice_line       WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM account_invoice            WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM hr_timesheet               WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM production_operation_order WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM production_manuf_order     WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM sale_sale_order_line       WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM sale_sale_order            WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM project_project            WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';

-- RH : lever la FK main_employment_contract AVANT de supprimer les contrats
UPDATE hr_employee SET main_employment_contract = NULL
 WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD' AND main_employment_contract IS NOT NULL;
DELETE FROM hr_employment_contract       WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM hr_employee                  WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM hr_employment_contract_type  WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';

DELETE FROM production_bill_of_material_line WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM production_bill_of_material      WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM production_prod_process_line     WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM production_prod_process          WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM production_work_center           WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM production_machine               WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';

DELETE FROM base_product           WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM base_product_category  WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';

-- Tiers : M2M pur company_set, scopé via les tiers dont on sait qu'on les a insérés
DELETE FROM base_partner_company_set
 WHERE base_partner IN (SELECT id FROM base_partner WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD');
DELETE FROM base_partner_address WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';

-- Lever les FK sur le tiers AVANT de supprimer les lignes email/adresse
UPDATE base_partner SET email_address = NULL WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD' AND email_address IS NOT NULL;
DELETE FROM message_email_address WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
UPDATE base_partner SET main_address = NULL WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD' AND main_address IS NOT NULL;
DELETE FROM base_partner WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM base_address WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';

DELETE FROM stock_stock_location WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';
DELETE FROM base_trading_name    WHERE import_origin = 'DEMO-<CLIENT>-YYYY-MM-DD';

COMMIT;
```

Ceci doit être **sûr à rejouer** (un DELETE sur des lignes déjà supprimées est un noop). Associer une vérification `DO $$` qui compte les lignes résiduelles à la fin.

### Règles d'idempotence

- Utiliser le motif `INSERT INTO ... SELECT ... WHERE NOT EXISTS (SELECT 1 FROM table WHERE code = 'XXX')`
- Ou des vérifications d'ID explicites : `WHERE NOT EXISTS (SELECT 1 FROM table WHERE id = N)`
- Toujours envelopper dans une transaction (BEGIN/COMMIT)
- Poser `version = 0` sur tous les nouveaux enregistrements
- Poser `created_on = NOW()`, `updated_on = NOW()`

### Champs calculés sur BtpOuvrage

Après l'insertion des lignes de détail, UPDATE l'ouvrage avec les totaux calculés :

```sql
UPDATE btp_btp_ouvrage SET
  total_material_cost = (SELECT COALESCE(SUM(total_cost), 0) FROM btp_btp_ouvrage_detail_line WHERE btp_ouvrage = X AND btp_detail_type_select = 1),
  total_labor_cost = (SELECT COALESCE(SUM(total_cost), 0) FROM btp_btp_ouvrage_detail_line WHERE btp_ouvrage = X AND btp_detail_type_select = 2),
  total_equipment_cost = (SELECT COALESCE(SUM(total_cost), 0) FROM btp_btp_ouvrage_detail_line WHERE btp_ouvrage = X AND btp_detail_type_select = 3),
  total_service_cost = (SELECT COALESCE(SUM(total_cost), 0) FROM btp_btp_ouvrage_detail_line WHERE btp_ouvrage = X AND btp_detail_type_select = 5),
  total_subcontracting_cost = (SELECT COALESCE(SUM(total_cost), 0) FROM btp_btp_ouvrage_detail_line WHERE btp_ouvrage = X AND btp_detail_type_select = 4),
  -- then total_cost, fg_amount, margin_amount, selling_price, coefficient
  ...
WHERE id = X;
```

### purchase_supplier_catalog

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| product | OUI (NOT NULL) | FK vers base_product |
| supplier_partner | OUI (NOT NULL) | FK vers base_partner (doit avoir is_supplier=true) |
| product_supplier_name | Recommandé | Nom dénormalisé — L'UTILISER pour décrire le niveau de service (ex. « Câble AR2V 240² — Livré chantier ») |
| product_supplier_code | Recommandé | Code de référence propre au fournisseur |
| price | Recommandé | Prix unitaire BigDecimal pour cette entrée de catalogue |
| min_qty | Recommandé | Quantité minimale de commande |
| max_qty | NON | Quantité maximale de commande |
| unit | NON | FK vers base_unit. Si NULL, utilise l'unité par défaut du produit |
| supplier_delivery_time | Recommandé | Délai de livraison en jours (0 = enlèvement, 3 = livré, etc.) |
| description | NON | Texte libre — décrit le niveau de service ou les conditions |
| is_taking_product_purchase_price | Recommandé | Booléen, false par défaut. Si true, utilise le purchase_price du produit au lieu du prix de catalogue |
| is_take_product_multiple_qty | Recommandé | Booléen, false par défaut |
| version | OUI | Mettre à 0 |

**Stratégie multi-prix :** créer plusieurs entrées de catalogue par paire produit×fournisseur pour représenter différents niveaux de service :

| Niveau | suffixe product_supplier_name | delivery_time | Ajustement de prix |
|---|---|---|---|
| Enlèvement magasin | "— Enlèvement magasin" | 0 | Prix de base |
| Livré chantier | "— Livré chantier" | 2-3 | +10% typique |
| Livré + déchargé chantier | "— Livré + déchargé chantier" | 3-5 | +20% typique |

La FK `supplier_catalog` sur `btp_btp_ouvrage_detail_line` permet de choisir quel niveau de prix utiliser par ligne d'ouvrage.

## Calcul financier de l'ouvrage

Pour chaque ouvrage, le prix de vente est calculé ainsi :

```
total_cost = material + labor + equipment + service + subcontracting
fg_amount = total_cost × fg_percentage / 100
subtotal = total_cost + fg_amount
margin_amount = subtotal × margin_percentage / 100
selling_price = subtotal + margin_amount
coefficient = selling_price / total_cost  (or 0 if total_cost = 0)
```

### 3. Les séquences doivent être relevées au-dessus de la plage d'ID de démo

Après avoir utilisé des ID explicites dans la plage 200000+, `setval()` chaque séquence touchée pour qu'AOS n'entre pas en collision lors des auto-inserts suivants :

```sql
SELECT setval('base_product_seq', GREATEST((SELECT last_value FROM base_product_seq), 200100));
-- répéter pour chaque séquence touchée
```

### 4. Idempotence : `WHERE NOT EXISTS` plutôt que `ON CONFLICT DO UPDATE`

L'interdiction du skill de « modifier les enregistrements existants » privilégie `WHERE NOT EXISTS` comme garde d'idempotence. Utiliser `ON CONFLICT (code) DO UPDATE` écraserait les modifications de l'utilisateur au rejeu — jamais acceptable dans un scénario de rejeu de démo.

Pour les tables sans code unique (comme `btp_btp_ouvrage_detail_line`), utiliser une clé logique composite : `WHERE NOT EXISTS (SELECT 1 FROM t WHERE btp_ouvrage = X AND sequence = Y)`.

*(Piège 5 — alignement des unités produit — voir `entites-produits.md`.)*

### 17. Les totaux d'en-tête du SaleOrder ne sont PAS auto-sommés depuis les lignes sur un insert/clone brut

Un `sale_sale_order` dont les lignes portent `ex_tax_total`/`in_tax_total` mais dont l'en-tête affiche `0` (fréquent sur des données seedées de clone dépouillées : statut confirmé mais 0 €, pas de seq) a simplement besoin que l'en-tête soit sommé :
```sql
UPDATE sale_sale_order so SET ex_tax_total=a.ex, in_tax_total=a.ttc, tax_total=a.ttc-a.ex
FROM (SELECT sale_order, SUM(ex_tax_total) ex, SUM(in_tax_total) ttc FROM sale_sale_order_line GROUP BY sale_order) a
WHERE so.id=a.sale_order AND so.id IN (...);
```
(Si les LIGNES sont aussi à 0, piloter plutôt l'action de calcul native d'AOS — la valorisation de ligne a besoin du moteur de taxe.)

### 57. `v.xxx` absent de la liste `VALUES`
Dans `JOIN (VALUES (…),(…)) v(col1,col2,…)`, une colonne référencée dans le SELECT mais **absente de
la liste `v(...)`** fait échouer tout le batch. Reproduit **3 fois** sur un même chantier, y compris
après avoir connu le piège. Parade mécanique avant exécution : compter les colonnes de `v(...)`,
compter les valeurs de la première ligne, et vérifier que chaque `v.xxx` du SELECT y figure — pour
**chaque** bloc, pas seulement le premier.

---

### 73. Prendre un numéro de séquence sans avancer le compteur = collision au `onSave`

```sql
-- FAUX : on vérifie que T0080..T0089 sont libres — ils le sont — et on s'arrête là
UPDATE base_partner SET partner_seq = 'T0080' WHERE id = 30001;
```

Le compteur vit dans `base_sequence_version.next_num` (joint à `base_sequence` par `sequence`).
Il est resté à 77 pendant que 89 devenait occupé : l'application ré-émet des numéros pris et la
contrainte d'unicité refuse tout enregistrement à l'écran. **Vérifier qu'un numéro est libre ne
suffit pas : il faut dire à la séquence qu'on l'a pris.**

```sql
UPDATE base_sequence_version v SET next_num = GREATEST(v.next_num,
         1 + (SELECT max(substring(partner_seq from '[0-9]+$')::int)
                FROM base_partner WHERE partner_seq ~ '^T[0-9]+$'))
  FROM base_sequence s WHERE s.id = v.sequence AND s.code_select = 'partner';
```

Dériver du **maximum réellement occupé**, jamais d'une valeur en dur : la correction reste juste si
d'autres numéros sont pris entre-temps. Asserter `next_num > max(occupé)`.

### 97. Appeler une `action-method` en REST SAUVEGARDE l'enregistrement — séquences consommées, namecolumns recalculés, lignes satellites créées

La règle 12 dit qu'un bouton AOS est une `action-method` appelable sur `/ws/action`, donc scriptable. Elle
ne dit pas qu'un tel appel **écrit**. Mesuré le 2026-09-03 (AOS 9.1.6 / EE 8.2.3, base `<base>`) :

```
action-sale-order-method-compute   -> la ligne 900007 passe de version 0 à 1, son full_name se remplit
onLoad « chantier » du projet 900010 -> version 0 -> 2
save de l'en-tête de commande       -> cascade : recalcule le full_name de TOUTES ses lignes,
                                       y compris une ligne témoin non visée (NULL -> renseigné)
```

Conséquences : séquences consommées, namecolumns recalculés, dénormalisations posées par le moteur et non
par l'INSERT (`sale_sale_order_line.main_sale_order` : NULL après l'INSERT, renseigné après le premier
save), lignes satellites créées (`base_sequence_version`, `base_reserved_sequence`). Un « appel de bouton »
n'est pas une lecture : il entre dans le périmètre de nettoyage d'un test et dans l'inventaire des
écritures d'un peuplement. Corollaire de la règle 12 : ce que le moteur pose au save, le SQL n'a pas à le
deviner ; ce qu'il laisse NULL (visibilité, namecolumn), le SQL de complétion le pose **après**.

### 118. Deux horloges de séquence, pas une — le compteur métier est distinct de la séquence PK

Le piège 73 couvre les séquences **PK Postgres** (`<table>_seq`). Il en existe une **seconde**,
indépendante : les compteurs de numérotation **métier** d'Axelor, dans `base_sequence` et
`base_sequence_version` (`next_num`), qui produisent `ACH0009`, `SO0013`, `FF260005`…

Ces deux horloges ne s'avancent pas ensemble. Un `INSERT` SQL qui pose directement un numéro de
pièce (`purchase_order_seq = 'ACH0018'`) **ne consomme pas** le compteur métier : celui-ci
n'avance qu'à un save passé par le moteur. Le compteur reste donc en retard sur les numéros
réellement occupés, et **le premier « Valider » cliqué depuis un écran régénère un numéro déjà
utilisé**.

*Coût payé le 2026-09-07 : 10 commandes fournisseur posées en SQL de `ACH0009` à `ACH0018`,
compteur `purchaseOrder` resté à 9. Un clic Valider sur n'importe quelle commande brouillon aurait
produit `ACH0009` en collision avec une commande existante. Attrapé par la dimension 7d de
`audit-completeness.sql` — pas par la 7e, qui ne regarde que les séquences PK.*

Règle : après tout `INSERT` qui pose un numéro de pièce à la main, avancer **aussi**
`base_sequence_version.next_num` au-delà du maximum réellement occupé, dans la même passe que le
`setval` des séquences PK.
### 130. Un prix à NULL (et non à zéro) échappe à toute passe écrite en `> 0`

`[prouvé 9.1.3 / AOP 8.2.2, 2026-09-22]` Une passe de prix écrite
`UPDATE base_product SET … WHERE cost_price > 0` **saute en silence tous les articles dont le prix est
NULL** : en SQL trois valeurs, `NULL > 0` n'est ni vrai ni faux, la ligne n'est simplement pas prise.
Le compte de lignes mises à jour ne le dit pas non plus — il annonce un succès partiel comme un
succès.

C'est l'exact analogue numérique du **piège 76** (`= false` exclut les NULL, un booléen non initialisé
rend l'enregistrement invisible) : même mécanisme, autre type, et il se glisse cette fois dans une
condition d'**écriture** plutôt que de lecture, donc aucun écran ne le révèle.

**Forme à tenir sur toute passe de montant** : `WHERE coalesce(cost_price, 0) = 0` pour cibler les
articles sans prix, `WHERE coalesce(cost_price, 0) > 0` pour cibler ceux qui en ont. Vaut pour tout
montant, tout ratio, toute quantité — `purchase_price`, `sale_price`, `qty`, `planned_duration`.
Garde à passer après la vague : `SELECT count(*) FROM <tbl> WHERE <col> IS NULL` doit rendre ce que le
contrat annonce, et non « 0 lignes restantes » obtenu en ne les ayant jamais regardées.

