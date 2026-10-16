---
name: bi-templates-catalog
description: Catalogue de references pour axenr-bi-architect - 10 templates SQL PostgreSQL pretes (pipeline commercial, taux de conversion, CA mensuel N/N-1, marge par affaire, DSO encours client, delai DP, puissance installee, top clients, jalons chantier, rotation stock), catalogue KPI par niveau (strategique/tactique/operationnel/ENR), bonnes pratiques Superset (dataset types, chart decision tree, layout, Jinja, index, RLS), conventions de nommage et modele de donnees Axelor detaille par domaine.
---

# BI Templates Catalog

> Knowledge base SQL + KPI + Superset pour l'agent `axenr-bi-architect`.

## TABLE DES MATIERES

1. 10 TEMPLATES SQL POSTGRESQL
2. CATALOGUE KPI AXENR (STRATEGIQUE / TACTIQUE / OPERATIONNEL / ENR)
3. BONNES PRATIQUES APACHE SUPERSET
4. MODELE DE DONNEES AXELOR PAR DOMAINE (colonnes detaillees)

---

## 1. TEMPLATES SQL POSTGRESQL

Tous les templates sont en PostgreSQL. Adapter la syntaxe JSON (`->>`) en `JSON_EXTRACT` si MySQL. Utiliser des CTE pour la lisibilite.

### T1 - Pipeline commercial par etape et commercial

```sql
WITH pipeline AS (
  SELECT
    u.full_name AS commercial,
    os.name AS etape_pipeline,
    os.sequence AS ordre_etape,
    COUNT(o.id) AS nb_opportunites,
    SUM(o.amount) AS montant_total,
    SUM(o.amount * o.probability / 100) AS montant_pondere,
    ROUND(AVG(o.probability)::numeric, 1) AS proba_moyenne
  FROM opportunity o
  LEFT JOIN auth_user u ON u.id = o.user_id
  LEFT JOIN opportunity_status os ON os.id = o.opportunity_status_id
  WHERE o.archived IS NOT TRUE
    AND o.company_id = :company_id
    AND o.lost_reason_id IS NULL
    AND NOT EXISTS (
      SELECT 1 FROM opportunity_status os2
      WHERE os2.id = o.opportunity_status_id AND os2.is_won = true
    )
  GROUP BY u.full_name, os.name, os.sequence
)
SELECT * FROM pipeline ORDER BY commercial, ordre_etape;
```

### T2 - Taux de conversion du funnel (lead -> gagne)

```sql
WITH metrics AS (
  SELECT
    (SELECT COUNT(*) FROM lead
     WHERE created_on::date BETWEEN :date_start AND :date_end
       AND archived IS NOT TRUE) AS nb_leads,
    (SELECT COUNT(*) FROM opportunity
     WHERE created_on::date BETWEEN :date_start AND :date_end
       AND archived IS NOT TRUE) AS nb_opps,
    (SELECT COUNT(*) FROM sale_order
     WHERE status_select >= 2
       AND created_on::date BETWEEN :date_start AND :date_end
       AND archived IS NOT TRUE) AS nb_devis,
    (SELECT COUNT(*) FROM sale_order
     WHERE status_select >= 3
       AND confirmation_date_time::date BETWEEN :date_start AND :date_end
       AND archived IS NOT TRUE) AS nb_signes
)
SELECT
  nb_leads, nb_opps, nb_devis, nb_signes,
  ROUND(100.0 * nb_opps / NULLIF(nb_leads, 0), 2) AS taux_lead_to_opp,
  ROUND(100.0 * nb_devis / NULLIF(nb_opps, 0), 2) AS taux_opp_to_devis,
  ROUND(100.0 * nb_signes / NULLIF(nb_devis, 0), 2) AS taux_devis_to_signe
FROM metrics;
```

### T3 - CA mensuel factures validees avec comparaison N-1

```sql
WITH ca_mensuel AS (
  SELECT
    DATE_TRUNC('month', i.invoice_date) AS mois,
    SUM(CASE WHEN i.operation_type_select = 3 THEN i.ex_tax_total ELSE 0 END) AS ca_ht,
    SUM(CASE WHEN i.operation_type_select = 4 THEN i.ex_tax_total ELSE 0 END) AS avoirs_ht
  FROM invoice i
  WHERE i.status_select IN (3, 4)
    AND i.archived IS NOT TRUE
    AND i.company_id = :company_id
    AND i.operation_type_select IN (3, 4)
  GROUP BY DATE_TRUNC('month', i.invoice_date)
)
SELECT
  mois,
  ca_ht,
  avoirs_ht,
  ca_ht - avoirs_ht AS ca_net_ht,
  LAG(ca_ht - avoirs_ht, 12) OVER (ORDER BY mois) AS ca_n_moins_1,
  ROUND(100.0 * ((ca_ht - avoirs_ht) - LAG(ca_ht - avoirs_ht, 12) OVER (ORDER BY mois))
        / NULLIF(LAG(ca_ht - avoirs_ht, 12) OVER (ORDER BY mois), 0), 2) AS evolution_pct
FROM ca_mensuel
ORDER BY mois;
```

### T4 - Marge par affaire (CA facture - achats - main d'oeuvre)

```sql
WITH ca_par_affaire AS (
  SELECT il.project_id, SUM(il.ex_tax_total) AS ca_facture_ht
  FROM invoice_line il
  JOIN invoice i ON i.id = il.invoice_id AND i.status_select IN (3, 4)
  WHERE i.company_id = :company_id AND i.operation_type_select = 3
  GROUP BY il.project_id
),
couts AS (
  SELECT pol.project_id, SUM(pol.ex_tax_total) AS cout_achat_ht
  FROM purchase_order_line pol
  JOIN purchase_order po ON po.id = pol.purchase_order_id AND po.status_select IN (3, 4)
  GROUP BY pol.project_id
),
mo AS (
  SELECT tl.project_id, SUM(tl.duration * e.hourly_cost) AS cout_mo
  FROM timesheet_line tl
  JOIN timesheet t ON t.id = tl.timesheet_id AND t.status_select = 3
  JOIN employee e ON e.id = t.employee_id
  GROUP BY tl.project_id
)
SELECT
  p.code AS code_affaire,
  p.name AS nom_affaire,
  cp.name AS client,
  COALESCE(ca.ca_facture_ht, 0) AS ca_ht,
  COALESCE(c.cout_achat_ht, 0) AS cout_achat,
  COALESCE(mo.cout_mo, 0) AS cout_main_oeuvre,
  COALESCE(ca.ca_facture_ht, 0) - COALESCE(c.cout_achat_ht, 0) - COALESCE(mo.cout_mo, 0) AS marge_euros,
  ROUND(100.0 * (COALESCE(ca.ca_facture_ht, 0) - COALESCE(c.cout_achat_ht, 0) - COALESCE(mo.cout_mo, 0))
        / NULLIF(ca.ca_facture_ht, 0), 2) AS marge_pct
FROM project p
LEFT JOIN partner cp ON cp.id = p.client_partner_id
LEFT JOIN ca_par_affaire ca ON ca.project_id = p.id
LEFT JOIN couts c ON c.project_id = p.id
LEFT JOIN mo ON mo.project_id = p.id
WHERE p.archived IS NOT TRUE
  AND p.company_id = :company_id
  AND p.is_business = true
  AND COALESCE(ca.ca_facture_ht, 0) > 0
ORDER BY marge_euros DESC;
```

### T5 - Encours client et DSO (delai moyen de paiement)

```sql
WITH factures_ouvertes AS (
  SELECT
    i.partner_id,
    p.name AS client,
    SUM(i.in_tax_total - i.amount_paid) AS encours_ttc,
    AVG(CURRENT_DATE - i.due_date) AS retard_moyen_jours,
    COUNT(*) FILTER (WHERE i.due_date < CURRENT_DATE) AS nb_factures_echues
  FROM invoice i
  JOIN partner p ON p.id = i.partner_id
  WHERE i.status_select IN (3, 4)
    AND i.operation_type_select = 3
    AND i.amount_remaining > 0
    AND i.archived IS NOT TRUE
    AND i.company_id = :company_id
  GROUP BY i.partner_id, p.name
),
dso AS (
  SELECT AVG(EXTRACT(EPOCH FROM (ip.payment_date - i.invoice_date)) / 86400) AS dso_jours
  FROM invoice i
  JOIN invoice_payment ip ON ip.invoice_id = i.id
  WHERE i.status_select = 4
    AND i.operation_type_select = 3
    AND i.invoice_date >= CURRENT_DATE - INTERVAL '12 months'
    AND i.company_id = :company_id
)
SELECT
  fo.client,
  fo.encours_ttc,
  fo.retard_moyen_jours,
  fo.nb_factures_echues,
  (SELECT ROUND(dso_jours::numeric, 1) FROM dso) AS dso_global
FROM factures_ouvertes fo
ORDER BY fo.encours_ttc DESC LIMIT 20;
```

### T6 - Delai moyen depot DP -> obtention DP (specifique AxENR)

```sql
SELECT
  DATE_TRUNC('quarter', (p.attrs::jsonb ->> 'dateDepotDP')::date) AS trimestre_depot,
  (p.attrs::jsonb ->> 'gestionnaireReseau') AS gestionnaire,
  COUNT(*) AS nb_dp,
  ROUND(AVG(
    (p.attrs::jsonb ->> 'dateObtentionDP')::date - (p.attrs::jsonb ->> 'dateDepotDP')::date
  )::numeric, 1) AS delai_moyen_jours,
  MAX((p.attrs::jsonb ->> 'dateObtentionDP')::date - (p.attrs::jsonb ->> 'dateDepotDP')::date) AS delai_max_jours
FROM project p
WHERE p.archived IS NOT TRUE
  AND p.company_id = :company_id
  AND (p.attrs::jsonb ->> 'dateDepotDP') IS NOT NULL
  AND (p.attrs::jsonb ->> 'dateObtentionDP') IS NOT NULL
GROUP BY trimestre_depot, gestionnaire
ORDER BY trimestre_depot DESC;
```

### T7 - Puissance installee cumulee par mois (specifique AxENR)

```sql
WITH mes_affaires AS (
  SELECT
    p.id,
    (p.attrs::jsonb ->> 'dateMiseEnService')::date AS date_mes,
    COALESCE(
      SUM(e.kwc_power),
      NULLIF((p.attrs::jsonb ->> 'puissanceInstalleeKwc'), '')::numeric,
      0
    ) AS puissance_kwc
  FROM project p
  LEFT JOIN equipment e ON e.project_id = p.id
  WHERE p.archived IS NOT TRUE
    AND p.company_id = :company_id
    AND p.is_business = true
    AND (p.attrs::jsonb ->> 'dateMiseEnService') IS NOT NULL
  GROUP BY p.id, p.attrs
)
SELECT
  DATE_TRUNC('month', date_mes) AS mois,
  COUNT(*) AS nb_installations,
  SUM(puissance_kwc) AS puissance_mois_kwc,
  SUM(SUM(puissance_kwc)) OVER (ORDER BY DATE_TRUNC('month', date_mes)) AS puissance_cumulee_kwc
FROM mes_affaires
WHERE date_mes BETWEEN :date_start AND :date_end
GROUP BY DATE_TRUNC('month', date_mes)
ORDER BY mois;
```

### T8 - Top 10 clients par CA signe

```sql
SELECT
  p.partner_seq AS code_client,
  p.name AS nom_client,
  COUNT(DISTINCT so.id) AS nb_commandes,
  SUM(so.ex_tax_total) AS ca_ht_total,
  ROUND(AVG(so.ex_tax_total)::numeric, 2) AS panier_moyen
FROM sale_order so
JOIN partner p ON p.id = so.client_partner_id
WHERE so.status_select >= 3
  AND so.archived IS NOT TRUE
  AND so.company_id = :company_id
  AND so.confirmation_date_time::date BETWEEN :date_start AND :date_end
GROUP BY p.id, p.partner_seq, p.name
ORDER BY ca_ht_total DESC LIMIT 10;
```

### T9 - Respect des jalons chantier

```sql
WITH jalons AS (
  SELECT
    p.code AS affaire,
    pt.name AS jalon,
    pt.task_end_date AS date_fin_prevue,
    CASE WHEN ts.is_completed THEN pt.updated_on::date ELSE NULL END AS date_reelle
  FROM project_task pt
  JOIN project p ON p.id = pt.project_id
  LEFT JOIN task_status ts ON ts.id = pt.status_id
  WHERE pt.archived IS NOT TRUE AND p.company_id = :company_id
    AND pt.task_end_date IS NOT NULL
)
SELECT
  CASE
    WHEN date_reelle IS NULL AND CURRENT_DATE > date_fin_prevue THEN 'En retard'
    WHEN date_reelle IS NULL THEN 'En cours'
    WHEN date_reelle <= date_fin_prevue THEN 'A l''heure'
    ELSE 'Terminee en retard'
  END AS statut_respect,
  COUNT(*) AS nb_taches,
  ROUND(AVG(COALESCE(date_reelle, CURRENT_DATE) - date_fin_prevue)::numeric, 1) AS retard_moyen_jours
FROM jalons
GROUP BY 1;
```

### T10 - Rotation de stock par produit

```sql
WITH sorties AS (
  SELECT sml.product_id, SUM(sml.qty) AS qte_sortie
  FROM stock_move_line sml
  JOIN stock_move sm ON sm.id = sml.stock_move_id
  WHERE sm.status_select = 3 AND sm.type_select = 2
    AND sm.realization_date_t >= CURRENT_DATE - INTERVAL '6 months'
  GROUP BY sml.product_id
),
stock_actuel AS (
  SELECT product_id, SUM(current_qty) AS stock_dispo
  FROM stock_location_line WHERE current_qty > 0
  GROUP BY product_id
)
SELECT
  p.code, p.name,
  COALESCE(sa.stock_dispo, 0) AS stock_actuel,
  COALESCE(s.qte_sortie, 0) AS sorties_6_mois,
  CASE
    WHEN COALESCE(s.qte_sortie, 0) = 0 THEN NULL
    ELSE ROUND(COALESCE(sa.stock_dispo, 0) * 180 / s.qte_sortie, 1)
  END AS couverture_jours
FROM product p
LEFT JOIN stock_actuel sa ON sa.product_id = p.id
LEFT JOIN sorties s ON s.product_id = p.id
WHERE p.archived IS NOT TRUE AND p.product_type_select = 'storable'
ORDER BY couverture_jours DESC NULLS FIRST;
```

---

## 2. CATALOGUE KPI AXENR

### Niveau strategique (direction - trimestriel/annuel)

- CA total HT : `SUM(invoice.ex_tax_total)` sur factures validees
- Marge nette consolidee : (CA - Couts directs - Frais generaux) / CA - cible ENR moyenne 5-15 %
- Puissance installee totale : `SUM(equipment.kwc_power WHERE in_service = true)`
- Nombre d'affaires gagnees / an : `COUNT(project WHERE is_business AND date_mes IS NOT NULL)`
- Revenus recurrents (MRR) : `SUM(contract.monthly_amount WHERE active)`

### Niveau tactique (management - mensuel)

- Pipeline en EUR non pondere / pondere
- Taux de conversion lead -> opp -> devis -> signe
- Duree moyenne cycle de vente (benchmarks : B2C PV 30-60j, B2B 90-180j, industriel 6-24 mois)
- DSO (delai moyen paiement client) - cible 30-60j
- Respect jalons chantier - cible > 85 %
- Prix moyen au kWc (benchmark 2024 : residentiel 1.8-2.8 EUR/Wc, tertiaire 100-500 kWc 0.9-1.3 EUR/Wc, sol 0.6-0.9 EUR/Wc)
- Marge brute par affaire - cible PV residentiel 15-25 %, tertiaire 20-30 %, IRVE 10-20 %

### Niveau operationnel (quotidien)

- Planning chantiers de la semaine
- Taches en retard
- Factures impayees echues
- Stock critique / rupture
- Interventions SAV ouvertes
- Feuilles de temps non validees
- Affaires bloquees (aucune progression > 60j) -> alerte chef de projet

### KPIs specifiques ENR

- Delai depot -> obtention DP : delai reglementaire 1 mois - surveiller > 45j
- Delai depot -> obtention PC : delai reglementaire 2 mois - surveiller > 90j
- Delai raccordement Enedis : < 36 kVA 2-3 mois, > 36 kVA 6-12 mois
- Delai signature -> MES : PV residentiel 3-6 mois, tertiaire < 100 kWc 4-8 mois
- Taux de renouvellement contrats maintenance - cible > 80 %
- MTTR (delai resolution SAV) - cible < 48h sur critiques
- Taux de disponibilite installation - cible > 98 % (monitoring externe)

### Regles bonnes pratiques KPI

Toujours associer un KPI a :
1. Une cible chiffree (sinon c'est du reporting, pas du pilotage)
2. Une frequence de suivi
3. Un responsable (qui regarde et qui agit)
4. Une action si hors cible
5. Une periodicite de revue de la definition

Jamais :
- Afficher un KPI sans cible ou comparaison N-1 / budget
- Mesurer ce qu'on ne peut pas influencer
- Depasser 5-8 KPIs par dashboard
- Moyenner sur < 10 observations

---

## 3. BONNES PRATIQUES APACHE SUPERSET

### Architecture recommandee

```
Axelor PostgreSQL  ->  Superset (utilisateur en lecture seule)
                       |
                       +-- Physical datasets  (tables Axelor directes)
                       +-- Virtual datasets   (requetes SQL versionnees)
                       +-- Materialized views (pour les gros volumes)
                       +-- Charts             (visualisations atomiques)
                       +-- Dashboards         (assemblage charts + filtres)
```

### Utilisateur PostgreSQL dedie

```sql
CREATE USER superset_reader WITH PASSWORD 'xxx';
GRANT CONNECT ON DATABASE axelor_prod TO superset_reader;
GRANT USAGE ON SCHEMA public TO superset_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO superset_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO superset_reader;
-- Ne jamais donner INSERT/UPDATE/DELETE/DDL
```

### Physical dataset vs Virtual dataset vs Materialized view

| Choix | Quand |
|-------|-------|
| Physical dataset | Requete simple sur une table, filtrage natif, drill-down - perfs optimales |
| Virtual dataset | Logique metier (CTE, jointures, JSON), reutilisable, cache Superset |
| Materialized view | Gros volumes (millions de lignes), KPI non temps-reel, rafraichi nuitamment |

Exemple de MV :

```sql
CREATE MATERIALIZED VIEW mv_ca_mensuel AS
SELECT DATE_TRUNC('month', invoice_date) AS mois, company_id, partner_id,
       SUM(ex_tax_total) AS ca_ht
FROM invoice
WHERE status_select IN (3, 4) AND archived IS NOT TRUE
GROUP BY 1, 2, 3;

CREATE INDEX idx_mv_ca_mois ON mv_ca_mensuel(mois);
-- Rafraichir : REFRESH MATERIALIZED VIEW CONCURRENTLY mv_ca_mensuel;
```

### Choix du graphique (arbre de decision)

| Tu veux montrer | Graphique recommande | A eviter |
|-----------------|----------------------|----------|
| KPI unique avec evolution | Big Number with Trendline | Gauge |
| Evolution temporelle | Line Chart | Pie |
| Comparaison < 7 categories | Bar Chart horizontal | 3D bar |
| Top N | Bar Chart trie + filtre Top N | Table non triee |
| Composition (%) < 5 parts | Pie Chart | Pie > 6 parts |
| Hierarchie / composition | Treemap / Sunburst | Pie multi-niveaux |
| Flux | Sankey | Line |
| Correlation | Scatter Plot | Bar |
| Distribution | Histogram / Box Plot | Line |
| Geographie | Country Map / Deck.gl | Table |
| Pipeline / funnel | Funnel Chart | Bar empile |
| Ratio / % avec cible | Big Number + target line | Gauge |

### Layout dashboard standard

```
+-----------------------------------------------------------+
| [TITRE]                     [Date]  [Societe]             |
+-----------------------------------------------------------+
| [Big Number 1] [Big Number 2] [Big Number 3]              |  Ligne 1 : KPIs
+-----------------------------------------------------------+
| [Line Chart evolution]   [Bar Chart Top N]                |  Ligne 2 : Tendances
+-----------------------------------------------------------+
| [Stacked Bar composition]   [Table details filtrable]     |  Ligne 3 : Details
+-----------------------------------------------------------+
```

Regles :
- KPIs en haut (vision globale) - max 5 Big Numbers
- Tendances au milieu - 2-4 charts
- Details en bas - tableaux filtrables
- Filtres globaux a gauche ou en haut : Date, Societe, Responsable
- Max 10 charts par dashboard (sinon scinder en tabs)

### Macros Jinja Superset

```sql
-- Periode dynamique injectee par Superset
WHERE invoice_date BETWEEN '{{ from_dttm }}' AND '{{ to_dttm }}'

-- Multi-selection societe
WHERE company_id IN {{ filter_values('company_id') | where_in }}

-- Conditionnel
{% if filter_values('user_id') | length > 0 %}
  AND user_id IN {{ filter_values('user_id') | where_in }}
{% endif %}

-- Utilisateur connecte
WHERE created_by = '{{ current_username() }}'
```

### Index PostgreSQL recommandes pour BI

```sql
-- Requetes par societe + periode (le cas le plus frequent)
CREATE INDEX idx_invoice_company_date
  ON invoice(company_id, invoice_date)
  WHERE archived IS NOT TRUE AND status_select IN (3, 4);

-- JOIN invoice / invoice_line
CREATE INDEX idx_invoice_line_invoice_project
  ON invoice_line(invoice_id, project_id);

-- Recherche dans attrs JSON (champs AxENR custom)
CREATE INDEX idx_project_attrs_gin
  ON project USING GIN ((attrs::jsonb));

-- Filtres soft-delete
CREATE INDEX idx_project_not_archived
  ON project(id) WHERE archived IS NOT TRUE;
```

### Row-Level Security (par societe utilisateur)

```
Superset -> Settings -> Row Level Security Filters
Clause : company_id IN (SELECT company_id FROM user_company WHERE user_id = current_user_id())
```

---

## 4. MODELE DE DONNEES AXELOR PAR DOMAINE (colonnes detaillees)

Voir le meta-modele complet dans `/Users/macbook/Downloads/export-12026303288952708643.xlsx` (940 modeles, 21 815 champs). Extraits des tables les plus utilisees ci-dessous.

### CRM & Commercial

**`lead`** : `id`, `name`, `first_name`, `enterprise_name`, `fixed_phone`, `mobile_phone`, `primary_address`, `primary_city_id`, `primary_postal_code`, `primary_country_id`, `email_address_id`, `web_site`, `department`, `industry_sector_id`, `estimated_budget`, `contact_date`, `status_select`, `lead_status_id`, `source_id`, `lost_reason_id`, `is_do_not_call`, `is_do_not_send_email`, `is_recycled`, `user_id`, `team_id`, `partner_id`, `type_id`, `picture`, `description`, `note`, `source_description`, `archived`, `created_on`, `created_by`, `updated_on`, `updated_by`.

**`opportunity`** : `id`, `name`, `opportunity_seq`, `description`, `customer_description`, `amount`, `recurrent_amount`, `recurring_start_date`, `recurring_end_date`, `expected_duration_of_recurring_revenue`, `probability`, `worst_case`, `best_case`, `expected_close_date`, `opportunity_rating`, `next_step`, `memo`, `status_select`, `opportunity_status_id`, `opportunity_type_id`, `source_id`, `lost_reason_id`, `lost_reason_str`, `partner_id`, `contact_id`, `lead_id`, `user_id`, `team_id`, `company_id`, `currency_id`, `bank_details_id`, `trading_name_id`, `archived`, `created_on`, `updated_on`, `attrs`.

Champs AxENR custom via `attrs` : `puissanceEstimeeKwc`, `adresseChantier`, `roundTripDistance`, `isPcRequired`, `isDpRequired`, `totalSelfConsumption`, `isGroundMounted`.

**`partner`** : `id`, `name`, `simple_full_name`, `partner_seq`, `partner_type_select` (1=Entreprise, 2=Particulier), `is_customer`, `is_supplier`, `is_prospect`, `is_carrier`, `is_contact`, `is_employee`, `is_subcontractor`, `is_factor`, `title_select`, `first_name`, `fax`, `mobile_phone`, `fixed_phone`, `email_address_id`, `web_site`, `industry_sector_id`, `main_activity_id`, `category_id`, `currency_id`, `tax_nbr`, `siren`, `nic`, `registration_code`, `main_address_id`, `delivery_address`, `invoicing_address`, `company_set`, `contact_partner_set`, `parent_partner_id`, `reports_to`, `language_id`, `team_id`, `user_id`, `payment_condition_id`, `in_payment_mode_id`, `out_payment_mode_id`, `customer_type_select`, `sale_price_list_id`, `purchase_price_list_id`, `sale_turnover`, `credit_limit`, `head_office_address`, `description`, `note`, `archived`, `attrs`.

**`sale_order`** : `id`, `sale_order_seq`, `external_reference`, `name`, `status_select`, `delivery_condition`, `delivery_date`, `expected_shipping_date`, `expected_realisation_date`, `ex_tax_total`, `in_tax_total`, `tax_total`, `amount_invoiced`, `advance_total`, `total_cost_price`, `company_cost_total`, `currency_id`, `company_currency_id`, `company_id`, `client_partner_id`, `contact_partner_id`, `invoiced_partner_id`, `delivered_partner_id`, `opportunity_id`, `project_id`, `price_list_id`, `payment_mode_id`, `payment_condition_id`, `confirmation_date_time`, `creation_date`, `archived`, `attrs`.

### Gestion d'affaire

**`project`** : `id`, `code` (= N dossier), `name`, `full_name`, `description`, `sequence`, `from_date`, `to_date`, `due_date`, `project_status_id`, `project_folder_id`, `parent_project_id`, `client_partner_id`, `customer_address_id`, `contact_partner_id`, `invoicing_address`, `currency_id`, `company_id`, `company_department_id`, `trading_name_id`, `is_business`, `is_project`, `is_show_phases_elements`, `team_id`, `assigned_to`, `priority`, `membership_status_select`, `product_set`, `project_task_category_set`, `imputable`, `exclude_timesheet_editor`, `to_invoice`, `invoicing_sequence_select`, `invoicing_comment`, `invoiced`, `is_invoicing_purchases`, `is_invoicing_timesheet`, `total_estimated_costs`, `total_real_costs`, `total_expenses`, `total_times_planned`, `total_times_realised`, `total_real_hrs`, `total_produced_turn_over`, `time_spent`, `estimated_time_hrs`, `unit_on_printing`, `product_to_invoice`, `dtype`, `template`, `archived`, `attrs`, `created_on`, `updated_on`.

Champs AxENR custom `attrs` : `numeroDossier`, `numeroDP`, `numeroPC`, `numeroConsuel`, `dateDepotDP`, `dateObtentionDP`, `dateDepotPC`, `dateObtentionPC`, `gestionnaireReseau`, `referenceGRD`, `dateMEO`, `dateMiseEnService`, `dateRemiseDOE`, `dateOuvertureChantier`, `dateAchevementTravaux`, `puissanceInstalleeKwc`, `typeInstallation`.

**`project_task`** : `id`, `name`, `description`, `internal_description`, `type_select`, `priority`, `status`, `status_id`, `progress_select`, `planned_progress`, `task_date`, `task_end_date`, `target_version_id`, `assigned_to`, `customer_referral`, `parent_task_id`, `project_id`, `project_task_section_id`, `sequence`, `frequency_id`, `is_task_refused`, `is_paid`, `is_private`, `to_invoice`, `invoiced`, `duration_hours`, `total_real_hrs`, `unit_id`, `unit_price`, `ex_tax_total`, `in_tax_total`, `discount_amount`, `currency_id`, `quantity`, `project_task_tag_set`, `start_to_start_set`, `finish_to_start_set`, `project_planning_time_list`, `sprint_id`, `process_instance_id`, `archived`, `attrs`.

### Facturation

**`invoice`** : `id`, `invoice_id`, `supplier_invoice_nb`, `internal_reference`, `external_reference`, `invoice_date`, `due_date`, `origin_date`, `estimated_payment_date`, `operation_type_select` (1=FA fourn, 2=AV fourn, 3=FA client, 4=AV client), `status_select`, `operation_sub_type_select`, `partner_id`, `contact_partner_id`, `invoiced_partner_id`, `delivered_partner_id`, `partner_account_id`, `company_id`, `currency_id`, `company_currency_id`, `trading_name_id`, `bank_details_id`, `sale_order_id`, `purchase_order_id`, `project_id`, `contract_id`, `ex_tax_total`, `in_tax_total`, `tax_total`, `company_ex_tax_total`, `company_in_tax_total`, `company_tax_total`, `amount_paid`, `amount_remaining`, `journal_id`, `move_id`, `payment_mode_id`, `payment_condition_id`, `duplicate_from_id`, `invoice_message_template_id`, `created_on`, `updated_on`, `archived`, `attrs`.

**`invoice_line`** : `id`, `invoice_id`, `product_id`, `product_name`, `product_code`, `qty`, `unit_id`, `price`, `ex_tax_total`, `in_tax_total`, `company_ex_tax_total`, `company_in_tax_total`, `discount_amount`, `discount_type_select`, `tax_line_set`, `tax_rate`, `tax_code`, `type_select`, `sequence`, `description`, `parent_line_id`, `fixed_assets`, `project_id` (critique pour CA par affaire), `sale_order_line_id`, `purchase_order_line_id`, `contract_line_id`, `stock_move_line_id`, `analytic_distribution_template_id`, `analytic_move_line_list`, `budget_id`, `account_id`, `archived`, `attrs`.

**`invoice_payment`** : `id`, `invoice_id`, `amount`, `amount_paid`, `currency_id`, `payment_date`, `type_select` (1=Paiement, 2=Acompte, 3=Avoir), `status_select` (1=Brouillon, 2=Valide, 3=Annule), `payment_mode_id`, `bank_details_id`, `description`, `journal_id`, `move_id`.

### Maintenance et interventions

**`equipment`** : `id`, `code`, `name`, `sequence`, `type_select`, `indicator_select`, `equipment_family_id`, `parent_equipment_id`, `partner_id`, `project_id`, `project_code`, `contract_id`, `address_id`, `commissioning_date`, `customer_warranty_on_part_end_date`, `in_service`, `kwc_power`, `kva_power`, `specific_access_schedule`, `schedule_of_operation`, `comments`, `picture_list`, `site_project_list`, `equipment_line_list`, `archived`, `attrs`.

**`contract`** : `id`, `name`, `contract_id_seq`, `partner_id`, `invoiced_partner_id`, `contact_partner_id`, `company_id`, `currency_id`, `start_date`, `end_date`, `renewal_date`, `next_invoicing_date`, `revaluation_date`, `last_revaluation_date`, `frequency`, `status_select` (1=Brouillon, 2=Actif, 3=Termine), `is_additional_benefit_management`, `automatic_invoicing`, `invoicing_moment_select`, `renewal_tactic_select`, `current_contract_version_id`, `next_contract_version_id`, `initial_contract_version_id`, `ex_tax_total`, `in_tax_total`, `archived`, `attrs`.

**`intervention`** : `id`, `name`, `sequence`, `description`, `status_select` (1-5), `priority`, `estimated_date`, `planif_start_date_time`, `planif_end_date_time`, `last_start_date_time`, `end_date_time`, `total_duration`, `technical_follow_up`, `commercial_follow_up`, `supplier_partner_id`, `contact_id`, `request_subject_id`, `commercial_user_id`, `user_in_charge`, `customer_request_id`, `contract_id`, `equipment_set`, `opportunity_id`, `assigned_to`, `company_id`, `address_id`, `archived`, `attrs`.

### RH et feuilles de temps

**`timesheet`** : `id`, `full_name`, `employee_id`, `user_id`, `company_id`, `from_date`, `to_date`, `status_select` (1-4), `period_total`, `time_logging_preference_select`, `validated_by`, `validation_date`, `validation_date_time`, `refused_by`, `refusal_date`, `sent_date`, `show_editor`, `is_completed`, `archived`.

**`timesheet_line`** : `id`, `timesheet_id`, `employee_id`, `date`, `duration`, `hours_duration`, `time_logging_preference_select`, `project_id`, `project_task_id`, `product_id`, `activity_id`, `comments`, `user_id`, `to_invoice`, `invoiced`, `product_category_id`, `archived`, `attrs`.

### Comptabilite

**`move`** : `id`, `reference`, `date`, `period_id`, `journal_id`, `company_id`, `currency_id`, `partner_id`, `origin_date`, `origin`, `description`, `validation_date`, `status_select` (1=Brouillon, 2=Comptabilisee, 3=Justifiee, 4=Annulee, 5=Simulee), `invoice_id`, `payment_id`, `fiscal_position_id`, `tax_number_id`, `stock_move_id`, `partner_bank_details_id`, `company_bank_details_id`, `move_line_list`, `archived`.

**`move_line`** : `id`, `move_id`, `counter`, `date`, `due_date`, `account_id`, `partner_id`, `description`, `origin`, `debit`, `credit`, `amount_remaining`, `amount_paid`, `currency_amount`, `currency_id`, `currency_rate`, `company_id`, `tax_line_set`, `tax_amount`, `vat_system_select`, `analytic_distribution_template_id`, `reconcile_group_id`, `credit_date`, `debit_date`, `reconcile_date`, `payment_mode_id`, `archived`.

### Base / Organisation

**`company`** : `id`, `name`, `code`, `currency_id`, `country_id`, `city_id`, `address_id`, `contact_address_id`, `postal_code`, `sequence_type_list`, `tax_nbr`, `timezone`, `language_id`, `logo_id`, `working_days_set`, `archived`, `attrs`.

**`auth_user`** (table `user` renommee) : `id`, `code`, `name`, `full_name`, `email`, `employee_id`, `group_id`, `role_set`, `team_set`, `active_company_id`, `active_team_id`, `company_set`, `password`, `archived`.
