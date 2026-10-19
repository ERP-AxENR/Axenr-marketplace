# Compartiment B — shape des 155 tables

Complément de `socle-aos-baseline.md` §7. Pour chaque table qu'AOS laisse vide et qu'une démo
réelle a dû peupler : **quelles colonnes ont effectivement été renseignées**, à quel taux, et
lesquelles sont restées vides.

Total : **155 tables, 981 colonnes renseignées, 250 restées vides.**

## Comment lire ce fichier

- `pleines` — renseignées sur 100 % des lignes. Un `*` marque une colonne **NOT NULL**.
- `partielles (N%)` — renseignées sur une partie des lignes. Souvent légitime (un champ
  conditionnel), parfois le signe d'un peuplement inachevé : à trancher au cas par cas.
- `restées vides` — **ne pas les traiter comme optionnelles.** Elles n'ont pas été remplies
  une fois ; c'est une donnée d'expérience, pas une norme. La règle 2 impose de passer chaque
  colonne et de justifier chaque vide, y compris celles-ci.

Aucune valeur métier n'est reproduite ici — uniquement la structure. Extraire des exemples de
contenu réintroduirait le biais sectoriel de la base d'origine, ce que cette carte doit éviter.
Pour les types, les NOT NULL et **les valeurs valides des sélections**, passer par
`scripts/introspect.sh <base> <table>` au moment de produire.

## Trois avertissements avant d'utiliser ce fichier

**1. Certaines de ces tables ne s'écrivent pas — elles se font produire par le moteur.**
Une table dont les colonnes sont massivement des montants ou des durées calculés est la
sortie d'un service ou d'un batch. L'écrire en SQL fabrique des chiffres faux qui ne se
recalculeront jamais. Cas identifiés, à faire générer par l'application :

| Table | Nature |
|---|---|
| `projectpro_project_report` (1 062 l., 58/59 col.) | rapport projet par `period` — montants, marges, avancement |
| `projectpro_project_report_employee_line` (1 467 l.) | ventilation du rapport par employé |
| `projectpro_project_report_line` (663 l.) | ventilation du rapport par produit |
| `production_cost_sheet_line` (20 l.) | feuille de coût d'un OF |
| `production_operation_order` (7 l.) | issu de la **planification** d'un OF — UI seule |
| `management_forecast_recap` / `_line` | récapitulatif de prévisionnel |
| `businessproject_invoicing_project` / `_log_times_set` | préparation de facturation projet |

Cette liste est établie par lecture de la nature des colonnes, pas par inspection du code
applicatif : la vérifier avant de conclure sur une table qui n'y figure pas. Le critère
opérationnel reste celui de la règle 12 — si l'objet porte taxe, marge, coût, écriture,
avancement ou date planifiée, il passe par le moteur.

**2. 24 des 155 tables sont des jonctions M2M** (`*_set`, `*_list`). Leur shape est triviale
mais leur remplissage ne l'est pas : c'est la règle 7 — un header sans ses satellites est
inutilisable, et une jonction vide rend le panneau vide à l'écran.

**3. La volumétrie de ce fichier est une observation, pas une cible.** Elle dit ce qui a suffi
une fois, sur une démo de services. À recalibrer selon la taille et le secteur du client, en
appliquant les règles de distribution du §5 de `socle-aos-baseline.md`.

---

## Index

| Table | Lignes | Colonnes renseignées |
|---|---:|---:|
| `projectpro_project_report_employee_line` | 1467 | 17/17 |
| `projectpro_project_report` | 1062 | 58/59 |
| `projectpro_project_report_line` | 663 | 14/20 |
| `projectscheduler_project_planning_project_set` | 385 | 2/2 |
| `businessproject_invoicing_project_log_times_set` | 275 | 2/2 |
| `projectpro_project_task_progress` | 128 | 3/3 |
| `project_project_project_folder_set` | 123 | 2/2 |
| `projectscheduler_project_planning_employee_set` | 102 | 2/2 |
| `businessproject_business_project_batch_project_set` | 59 | 2/2 |
| `quality_control_entry_plan_line` | 30 | 15/16 |
| `hr_medical_visit` | 25 | 6/8 |
| `hr_lunch_voucher_mgt_line` | 24 | 15/16 |
| `quality_quality_measuring_point` | 22 | 7/7 |
| `base_industry_sector` | 20 | 1/1 |
| `production_cost_sheet_line` | 20 | 15/15 |
| `quality_tracking_number_characteristic` | 20 | 7/7 |
| `contract_contract_line` | 18 | 19/31 |
| `contract_contract_line_tax_line_set` | 18 | 2/2 |
| `talent_experience` | 18 | 9/9 |
| `talent_certification` | 17 | 3/3 |
| `hr_employee_bonus_mgt_line` | 16 | 7/8 |
| `talent_job_application_industry_sector_set` | 16 | 2/2 |
| `talent_job_application_skill_set` | 16 | 2/2 |
| `maintenance_maintenance_request` | 15 | 15/16 |
| `talent_education` | 15 | 6/6 |
| `team_task` | 15 | 14/22 |
| `account_analytic_rules_analytic_account_set` | 14 | 2/2 |
| `management_forecast_recap_line` | 14 | 11/11 |
| `talent_job_application_language_set` | 14 | 2/2 |
| `contract_contract_template_contract_line_list` | 12 | 2/2 |
| `production_sop_line` | 12 | 9/9 |
| `base_price_list_line` | 10 | 7/8 |
| `projectscheduler_employee_skill_planning_employee_set` | 10 | 2/2 |
| `production_prod_product` | 9 | 7/13 |
| `projectscheduler_project_planning` | 9 | 4/4 |
| `purchase_call_tender_offer` | 9 | 15/19 |
| `purchase_call_tender_supplier` | 9 | 2/2 |
| `crm_tour_line` | 8 | 5/6 |
| `projectscheduler_employee_skill_planning_skill_set` | 8 | 2/2 |
| `quality_control_entry_sample` | 8 | 5/5 |
| `quality_control_point` | 8 | 9/10 |
| `talent_job_application` | 8 | 31/41 |
| `production_operation_order` | 7 | 19/23 |
| `production_operation_order_duration` | 7 | 5/5 |
| `quality_control_point_model` | 7 | 6/7 |
| `quality_product_characteristic` | 7 | 6/6 |
| `talent_skill` | 7 | 1/3 |
| `account_invoice_stock_move_set` | 6 | 2/2 |
| `crm_corporate_partner_domain` | 6 | 1/1 |
| `crm_lost_reason` | 6 | 2/2 |
| `hr_employment` | 6 | 5/10 |
| `management_forecast` | 6 | 8/10 |
| `production_machine_tool` | 6 | 13/15 |
| `project_resource_type` | 6 | 1/1 |
| `quality_characteristic_type_characteristic_set` | 6 | 2/2 |
| `quality_control_plan_line_characteristic` | 6 | 1/1 |
| `quality_quality_corrective_action` | 6 | 4/4 |
| `quality_quality_pictures` | 6 | 3/4 |
| `quality_root_cause` | 6 | 1/1 |
| `talent_positioning` | 6 | 16/19 |
| `talent_training_session` | 6 | 9/10 |
| `base_file` | 5 | 6/10 |
| `base_partner_role` | 5 | 2/2 |
| `businessproject_project_folder` | 5 | 2/2 |
| `hr_end_of_contract_reason` | 5 | 1/1 |
| `hr_qualification` | 5 | 3/5 |
| `production_object_description` | 5 | 3/4 |
| `project_wiki` | 5 | 5/6 |
| `quality_characteristic_property` | 5 | 1/1 |
| `quality_characteristic_type` | 5 | 3/3 |
| `quality_quality_alert` | 5 | 15/15 |
| `quality_required_document` | 5 | 11/14 |
| `supplychain_timetable_template_line` | 5 | 5/6 |
| `talent_education_level` | 5 | 1/1 |
| `talent_job_position` | 5 | 17/18 |
| `talent_training_category` | 5 | 1/1 |
| `talent_training_skill_set` | 5 | 2/2 |
| `account_fixed_asset` | 4 | 25/77 |
| `base_partner_price_list_price_list_set` | 4 | 2/2 |
| `base_price_list` | 4 | 8/12 |
| `base_stop_reason` | 4 | 2/2 |
| `base_trading_name` | 4 | 2/12 |
| `contract_revaluation_formula` | 4 | 5/5 |
| `crm_fidelity` | 4 | 1/2 |
| `hr_employment_amendment_type` | 4 | 2/3 |
| `hr_employment_contract_type` | 4 | 3/3 |
| `hr_pay_grid` | 4 | 4/6 |
| `hr_qualification_level` | 4 | 3/5 |
| `maintenance_equipement_maintenance` | 4 | 11/13 |
| `maintenance_maintenance_category` | 4 | 1/1 |
| `production_product_approval` | 4 | 4/4 |
| `production_production_batch` | 4 | 8/8 |
| `quality_control_entry` | 4 | 8/8 |
| `quality_control_plan` | 4 | 7/7 |
| `quality_control_point_type` | 4 | 1/1 |
| `quality_qi_action_distribution` | 4 | 8/9 |
| `quality_quality_control` | 4 | 11/14 |
| `talent_talent_source` | 4 | 2/2 |
| `account_pfp_partial_reason` | 3 | 1/1 |
| `base_partner_price_list` | 3 | 4/4 |
| `base_site` | 3 | 9/12 |
| `businessproject_invoicing_project` | 3 | 14/16 |
| `businessproject_invoicing_project_project_task_set` | 3 | 2/2 |
| `crm_agency` | 3 | 1/1 |
| `crm_catalog_type` | 3 | 1/1 |
| `gdpr_gdpr_processing_register` | 3 | 6/7 |
| `helpdesk_sla` | 3 | 5/9 |
| `hr_employee_bonus_mgt` | 3 | 6/6 |
| `hr_lunch_voucher_mgt` | 3 | 13/14 |
| `hr_medical_visit_reason` | 3 | 1/1 |
| `intervention_intervention_note_type` | 3 | 2/2 |
| `intervention_justification` | 3 | 2/2 |
| `intervention_rescheduling_reason` | 3 | 2/2 |
| `production_mps_charge` | 3 | 2/2 |
| `project_project_task_invoice_line_set` | 3 | 2/2 |
| `project_project_template` | 3 | 9/13 |
| `project_project_version` | 3 | 3/5 |
| `project_topic` | 3 | 4/4 |
| `project_wiki_folder` | 3 | 1/1 |
| `projectscheduler_employee_workload` | 3 | 3/3 |
| `purchase_call_tender` | 3 | 5/8 |
| `purchase_call_tender_need` | 3 | 7/9 |
| `quality_control_plan_frequency` | 3 | 6/6 |
| `quality_qi_decision_distribution` | 3 | 12/13 |
| `quality_quality_process` | 3 | 2/2 |
| `sale_pack` | 3 | 8/8 |
| `account_analytic_rules` | 2 | 4/4 |
| `account_invoice_term_payment` | 2 | 5/6 |
| `base_routing` | 2 | 4/4 |
| `contract_index_revaluation` | 2 | 2/2 |
| `crm_tour` | 2 | 3/3 |
| `hr_health_mutual_rejection_reason` | 2 | 3/4 |
| `hr_probation_period` | 2 | 2/8 |
| `production_sop` | 2 | 8/8 |
| `production_workshop_sequence_config_line` | 2 | 3/3 |
| `projectpro_tree_project_reporting_project_set` | 2 | 2/2 |
| `projectscheduler_employee_skill_planning` | 2 | 2/2 |
| `supplychain_timetable_template` | 2 | 2/2 |
| `supplychain_un_code` | 2 | 2/3 |
| `account_accounting_config_template_company_set` | 1 | 2/2 |
| `account_accounting_report` | 1 | 35/44 |
| `account_analytic_journal_type` | 1 | 2/2 |
| `account_invoice_payment` | 1 | 16/28 |
| `account_invoice_term_payment_reconcile_list` | 1 | 2/2 |
| `account_reconcile` | 1 | 11/13 |
| `account_reconcile_group` | 1 | 5/6 |
| `account_tax_payment_move_line` | 1 | 10/11 |
| `businessproject_business_project_batch` | 1 | 6/9 |
| `hr_collective_agreement` | 1 | 4/4 |
| `hr_smic_value` | 1 | 3/3 |
| `intervention_intervention_config` | 1 | 5/9 |
| `management_forecast_recap` | 1 | 14/15 |
| `production_cost_sheet` | 1 | 7/8 |
| `production_manuf_order` | 1 | 20/36 |
| `projectpro_tree_project_reporting` | 1 | 1/1 |

---

**`projectpro_project_report_employee_line`** — 1467 lignes, **17/17** colonnes renseignées

- pleines : `current_expense_cost` · `current_margin` · `current_ts_cost` · `current_turnover` · `fixed_price_production` · `production_time_percent` · `time_planned` · `timespent` · `timespent_production` · `total_expense_cost` · `total_margin` · `total_time_planned` · `total_timespent` · `total_ts_cost` · `total_turnover` · `employee` · `project_report`

**`projectpro_project_report`** — 1062 lignes, **58/59** colonnes renseignées

- pleines : `additional_cost` · `additional_sales` · `current_cost` · `current_expense_cost` · `current_invoiced` · `current_margin` · `current_project_invoiced` · `current_subscription_invoiced` · `current_ts_cost` · `current_turnover` · `fixed_price_current_invoiced` · `fixed_price_current_turnover` · `fixed_price_production` · `fixed_price_theoretical_turnover` · `fixed_price_total_invoiced` · `initial_cost` · `initial_margin` · `initial_sales` · `invoiced_in_advance` · `margin_at_the_end` · `percent_ts_tp` · `planned_cost` · `production_time` · `production_time_percent` · `progress` · `progress_percent` · `remaining_margin` · `remaining_to_sale` · `time_base_current_invoiced` · `time_base_current_turnover` · `time_base_theoretical_turnover` · `time_base_total_invoiced` · `time_planned` · `timespent` · `timespent_production` · `total_additional_cost` · `total_additional_sales` · `total_cost` · `total_estimated` · `total_expense_cost` · `total_invoiced` · `total_margin` · `total_percent_ts_tp` · `total_production_time` · `total_production_time_percent` · `total_progress` · `total_progress_percent` · `total_project_invoiced` · `total_remaining_cost` · `total_remaining_time` · `total_subscription_invoiced` · `total_theoretical_turnover` · `total_time_planned` · `total_timespent` · `total_ts_cost` · `unbilled_work_in_progress` · `period*` · `project*`
- **restées vides** : `project_task`

**`projectpro_project_report_line`** — 663 lignes, **14/20** colonnes renseignées

- pleines : `additional_amount` · `additional_quantity` · `quantity` · `timesheet_amount` · `timesheet_qty` · `total_amount` · `type_select` · `product` · `product_category` · `unit`
- partielles : `current_cost_project_report (23%)` · `current_turnover_project_report (14%)` · `remaining_cost_project_report (32%)` · `total_cost_project_report (32%)`
- **restées vides** : `current_invoiced_project_report` · `initial_cost_project_report` · `initial_sales_project_report` · `remaining_to_sale_project_report` · `total_invoiced_project_report` · `total_theoretical_turnover_project_report`

**`projectscheduler_project_planning_project_set`** — 385 lignes, **2/2** colonnes renseignées

- pleines : `projectscheduler_project_planning*` · `project_set*`

**`businessproject_invoicing_project_log_times_set`** — 275 lignes, **2/2** colonnes renseignées

- pleines : `businessproject_invoicing_project*` · `log_times_set*`

**`projectpro_project_task_progress`** — 128 lignes, **3/3** colonnes renseignées

- pleines : `progress` · `progress_date` · `project_task`

**`project_project_project_folder_set`** — 123 lignes, **2/2** colonnes renseignées

- pleines : `project_set*` · `project_folder_set*`

**`projectscheduler_project_planning_employee_set`** — 102 lignes, **2/2** colonnes renseignées

- pleines : `projectscheduler_project_planning*` · `employee_set*`

**`businessproject_business_project_batch_project_set`** — 59 lignes, **2/2** colonnes renseignées

- pleines : `businessproject_business_project_batch*` · `project_set*`

**`quality_control_entry_plan_line`** — 30 lignes, **15/16** colonnes renseignées

- pleines : `description` · `is_custom_frequency` · `name` · `plan_attrs` · `priority` · `reference` · `result_select` · `type_select` · `characteristic` · `control_plan_frequency` · `control_type`
- partielles : `entry_attrs (80%)` · `control_entry_sample (80%)` · `control_plan (20%)` · `control_plan_line (80%)`
- **restées vides** : `machine_type`

**`hr_medical_visit`** — 25 lignes, **6/8** colonnes renseignées

- pleines : `medical_visit_end_datet*` · `medical_visit_start_datet*` · `note` · `status_select` · `employee*` · `visit_reason*`
- **restées vides** : `i_calendar_event` · `medical_visit_file`

**`hr_lunch_voucher_mgt_line`** — 24 lignes, **15/16** colonnes renseignées

- pleines : `canteen_entries` · `card_format_number` · `days_overseas` · `days_worked_nbr` · `given_to_employee` · `in_advance_nbr` · `invitation` · `lunch_voucher_format_select` · `lunch_voucher_number` · `paper_format_number` · `restaurant` · `status_select` · `employee` · `lunch_voucher_mgt`
- partielles : `comments (25%)`
- **restées vides** : `payroll_preparation`

**`quality_quality_measuring_point`** — 22 lignes, **7/7** colonnes renseignées

- pleines : `coefficient` · `measuring_type_select` · `name` · `observations` · `control_point`
- partielles : `compliant (55%)` · `measuring_note (45%)`

**`base_industry_sector`** — 20 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`production_cost_sheet_line`** — 20 lignes, **15/15** colonnes renseignées

- pleines : `bom_level` · `code` · `consumption_qty` · `cost_price` · `name` · `ratio` · `type_select` · `type_select_icon` · `unit_cost_price` · `unit`
- partielles : `cost_sheet (5%)` · `cost_sheet_group (45%)` · `parent_cost_sheet_line (95%)` · `product (45%)` · `work_center (55%)`

**`quality_tracking_number_characteristic`** — 20 lignes, **7/7** colonnes renseignées

- pleines : `conforms` · `tracking_number_comment` · `characteristic*` · `product*` · `tracking_number*`
- partielles : `measured_value (50%)` · `observed_value (50%)`

**`contract_contract_line`** — 18 lignes, **19/31** colonnes renseignées

- pleines : `ex_tax_total` · `full_name` · `price` · `product_name*` · `qty` · `product` · `unit`
- partielles : `discount_amount (33%)` · `discount_type_select (33%)` · `in_tax_total (33%)` · `initial_price_per_year (33%)` · `is_consumption_line (33%)` · `is_invoiced (33%)` · `is_to_revaluate (33%)` · `price_discounted (33%)` · `sequence (33%)` · `type_select (33%)` · `yearly_price_revalued (33%)` · `contract_version (33%)`
- **restées vides** : `consumption_max_quantity` · `description` · `from_date` · `initial_unit_price` · `analytic_distribution_template` · `axis1analytic_account` · `axis2analytic_account` · `axis3analytic_account` · `axis4analytic_account` · `axis5analytic_account` · `fiscal_position` · `pricing`

**`contract_contract_line_tax_line_set`** — 18 lignes, **2/2** colonnes renseignées

- pleines : `contract_contract_line*` · `tax_line_set*`

**`talent_experience`** — 18 lignes, **9/9** colonnes renseignées

- pleines : `company` · `description` · `duration` · `from_date` · `job_description` · `job_title` · `location` · `job_applicant`
- partielles : `to_date (61%)`

**`talent_certification`** — 17 lignes, **3/3** colonnes renseignées

- pleines : `certification_name` · `issue_date` · `job_applicant`

**`hr_employee_bonus_mgt_line`** — 16 lignes, **7/8** colonnes renseignées

- pleines : `amount` · `coef` · `seniority_date` · `status_select` · `employee` · `employee_bonus_mgt` · `weekly_planning`
- **restées vides** : `payroll_preparation`

**`talent_job_application_industry_sector_set`** — 16 lignes, **2/2** colonnes renseignées

- pleines : `talent_job_application*` · `industry_sector_set*`

**`talent_job_application_skill_set`** — 16 lignes, **2/2** colonnes renseignées

- pleines : `talent_job_application*` · `skill_set*`

**`maintenance_maintenance_request`** — 15 lignes, **15/16** colonnes renseignées

- pleines : `action_select` · `duration_hours` · `expected_date*` · `mtn_comments` · `mtn_task` · `request_date*` · `sequence` · `status_select` · `assigned_to` · `equipement_maintenance` · `machine` · `request_by`
- partielles : `done_on (53%)` · `end_date (53%)` · `start_date (73%)`
- **restées vides** : `manuf_order`

**`talent_education`** — 15 lignes, **6/6** colonnes renseignées

- pleines : `degree_name` · `description` · `from_date` · `institute` · `to_date` · `job_applicant`

**`team_task`** — 15 lignes, **14/22** colonnes renseignées

- pleines : `description` · `do_apply_to_all_next_tasks` · `has_date_or_frequency_changed` · `is_first` · `name*` · `priority` · `sequence` · `status` · `task_date` · `task_deadline` · `task_duration` · `type_select` · `assigned_to` · `team`
- **restées vides** : `related_id` · `related_model` · `related_name` · `frequency` · `next_team_task` · `related_process_instance` · `role` · `wkf_task_config`

**`account_analytic_rules_analytic_account_set`** — 14 lignes, **2/2** colonnes renseignées

- pleines : `account_analytic_rules*` · `analytic_account_set*`

**`management_forecast_recap_line`** — 14 lignes, **11/11** colonnes renseignées

- pleines : `amount` · `balance` · `estimated_date` · `related_to_select` · `related_to_select_bank_details` · `related_to_select_id` · `related_to_select_name` · `related_to_select_payment_mode` · `type_select*` · `forecast_recap` · `forecast_recap_line_type`

**`talent_job_application_language_set`** — 14 lignes, **2/2** colonnes renseignées

- pleines : `talent_job_application*` · `language_set*`

**`contract_contract_template_contract_line_list`** — 12 lignes, **2/2** colonnes renseignées

- pleines : `contract_contract_template*` · `contract_line_list*`

**`production_sop_line`** — 12 lignes, **9/9** colonnes renseignées

- pleines : `sop_real_manuf` · `sop_real_sales` · `sop_real_stock` · `sop_sales_forecast` · `sop_sales_gap` · `currency` · `period` · `sop` · `year`

**`base_price_list_line`** — 10 lignes, **7/8** colonnes renseignées

- pleines : `amount` · `amount_type_select` · `min_qty` · `type_select` · `price_list`
- partielles : `product (50%)` · `product_category (50%)`
- **restées vides** : `anomaly_select`

**`projectscheduler_employee_skill_planning_employee_set`** — 10 lignes, **2/2** colonnes renseignées

- pleines : `projectscheduler_employee_skill_planning*` · `employee_set*`

**`production_prod_product`** — 9 lignes, **7/13** colonnes renseignées

- pleines : `planned_qty` · `qty` · `real_qty` · `product` · `unit`
- partielles : `to_consume_manuf_order (89%)` · `to_produce_manuf_order (11%)`
- **restées vides** : `diff_consume_manuf_order` · `diff_consume_operation_order` · `to_consume_operation_order` · `to_consume_prod_process_line` · `waste_manuf_order` · `waste_product_tracking_number`

**`projectscheduler_project_planning`** — 9 lignes, **4/4** colonnes renseignées

- pleines : `horizon` · `name*` · `project_scope_select` · `show_all_members_automatically`

**`purchase_call_tender_offer`** — 9 lignes, **15/19** colonnes renseignées

- pleines : `call_tender_offer_seq` · `counter` · `proposed_date` · `proposed_price` · `proposed_qty` · `requested_date` · `requested_qty*` · `status_select` · `call_tender` · `call_tender_need` · `call_tender_supplier` · `product*` · `proposed_unit` · `requested_unit` · `supplier_partner*`
- **restées vides** : `offer_comment` · `offer_mail` · `requested_delivery_time` · `call_tender_attr_config`

**`purchase_call_tender_supplier`** — 9 lignes, **2/2** colonnes renseignées

- pleines : `call_tender` · `supplier_partner*`

**`crm_tour_line`** — 8 lignes, **5/6** colonnes renseignées

- pleines : `is_validated` · `tour_line_order*` · `address*` · `partner*` · `tour`
- **restées vides** : `event`

**`projectscheduler_employee_skill_planning_skill_set`** — 8 lignes, **2/2** colonnes renseignées

- pleines : `projectscheduler_employee_skill_planning*` · `skill_set*`

**`quality_control_entry_sample`** — 8 lignes, **5/5** colonnes renseignées

- pleines : `entry_sample_nbr` · `entry_sample_ref` · `full_name` · `result_select` · `control_entry`

**`quality_control_point`** — 8 lignes, **9/10** colonnes renseignées

- pleines : `control_frequency` · `control_point_date` · `name*` · `notes` · `sequence` · `status_select` · `control_point_type*` · `quality_control` · `responsible`
- **restées vides** : `optional_quality_control`

**`talent_job_application`** — 8 lignes, **31/41** colonnes renseignées

- pleines : `appreciation` · `availability_from` · `commentary` · `creation_date` · `current_salary` · `date_of_birth` · `description` · `evaluation` · `expected_salary` · `experience_select` · `family_status_select` · `first_name` · `full_name` · `last_name` · `mobile_phone` · `title` · `title_select` · `citizenship` · `company` · `currency` · `education_level` · `email_address` · `employee_address` · `hiring_stage` · `hr_manager` · `job_position*` · `responsible` · `service` · `talent_source`
- partielles : `linked_in_profile (62%)` · `proposed_salary (50%)`
- **restées vides** : `fax` · `fixed_phone` · `function_id` · `reason_not_hired` · `referred_by` · `cv` · `dms_file` · `employee` · `picture` · `resume`

**`production_operation_order`** — 7 lignes, **19/23** colonnes renseignées

- pleines : `is_with_difference` · `name` · `operation_name` · `outsourcing` · `planned_duration` · `planned_end_datet` · `planned_end_with_waiting_datet` · `planned_human_duration` · `planned_machine_duration` · `planned_start_datet` · `priority` · `real_duration` · `real_end_datet` · `real_start_datet` · `status_select` · `manuf_order` · `prod_process_line` · `work_center`
- partielles : `machine (57%)`
- **restées vides** : `comments` · `bar_code` · `machine_tool` · `outsourcing_partner`

**`production_operation_order_duration`** — 7 lignes, **5/5** colonnes renseignées

- pleines : `starting_date_time` · `stopping_date_time` · `operation_order` · `started_by` · `stopped_by`

**`quality_control_point_model`** — 7 lignes, **6/7** colonnes renseignées

- pleines : `control_frequency` · `name*` · `notes` · `sequence` · `control_point_type*` · `quality_process`
- **restées vides** : `optional_quality_process`

**`quality_product_characteristic`** — 7 lignes, **6/6** colonnes renseignées

- pleines : `product_comment` · `characteristic*` · `product*`
- partielles : `max_value (43%)` · `min_value (43%)` · `expected_value (43%)`

**`talent_skill`** — 7 lignes, **1/3** colonnes renseignées

- pleines : `name*`
- **restées vides** : `type_select` · `validity_duration`

**`account_invoice_stock_move_set`** — 6 lignes, **2/2** colonnes renseignées

- pleines : `invoice_set*` · `stock_move_set*`

**`crm_corporate_partner_domain`** — 6 lignes, **1/1** colonnes renseignées

- pleines : `name`

**`crm_lost_reason`** — 6 lignes, **2/2** colonnes renseignées

- pleines : `free_text` · `name*`

**`hr_employment`** — 6 lignes, **5/10** colonnes renseignées

- pleines : `csp` · `full_name` · `is_all_companies` · `name` · `collective_agreement`
- **restées vides** : `company_set_str` · `experience_duration` · `export_code` · `qualification_level_set_str` · `qualification_set_str`

**`management_forecast`** — 6 lignes, **8/10** colonnes renseignées

- pleines : `amount` · `comments` · `estimated_date` · `forecast_seq` · `type_select` · `bank_details*` · `company*` · `forecast_recap_line_type*`
- **restées vides** : `realization_date` · `forecast_generator`

**`production_machine_tool`** — 6 lignes, **13/15** colonnes renseignées

- pleines : `buying_date` · `buying_price` · `code` · `description` · `hours_of_use` · `last_overhaul_date` · `maintenance_cost` · `manuf_date` · `manufacturer` · `name` · `next_overhaul_date` · `buying_currency` · `machine`
- **restées vides** : `disposal_date` · `image`

**`project_resource_type`** — 6 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`quality_characteristic_type_characteristic_set`** — 6 lignes, **2/2** colonnes renseignées

- pleines : `quality_characteristic_type*` · `characteristic_set*`

**`quality_control_plan_line_characteristic`** — 6 lignes, **1/1** colonnes renseignées

- pleines : `name`

**`quality_quality_corrective_action`** — 6 lignes, **4/4** colonnes renseignées

- pleines : `details` · `is_applicable` · `name` · `quality_control`

**`quality_quality_pictures`** — 6 lignes, **3/4** colonnes renseignées

- pleines : `create_date` · `name` · `quality_measuring_point`
- **restées vides** : `meta_file`

**`quality_root_cause`** — 6 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`talent_positioning`** — 6 lignes, **16/19** colonnes renseignées

- pleines : `average_daily_cost` · `cost` · `daily_sales_rate` · `end_date` · `free_days` · `margin` · `name` · `occupancy_rate` · `profitability` · `revenue` · `sold_days` · `start_date` · `status_select` · `type_select` · `client` · `opportunity_manager`
- **restées vides** : `comment_details` · `applicant` · `opportunity`

**`talent_training_session`** — 6 lignes, **9/10** colonnes renseignées

- pleines : `duration` · `from_date*` · `full_name` · `location` · `nbr_registered` · `status_select` · `to_date*` · `training*`
- partielles : `rating (50%)`
- **restées vides** : `overall_rating_to_apply`

**`base_file`** — 5 lignes, **6/10** colonnes renseignées

- pleines : `file_description` · `full_name` · `record_date` · `employee` · `file_type`
- partielles : `expiration_date (40%)`
- **restées vides** : `file_type_select` · `contract_version` · `dms_file` · `meta_file`

**`base_partner_role`** — 5 lignes, **2/2** colonnes renseignées

- pleines : `code` · `name`

**`businessproject_project_folder`** — 5 lignes, **2/2** colonnes renseignées

- pleines : `description` · `name`

**`hr_end_of_contract_reason`** — 5 lignes, **1/1** colonnes renseignées

- pleines : `reason*`

**`hr_qualification`** — 5 lignes, **3/5** colonnes renseignées

- pleines : `code` · `full_name` · `name`
- **restées vides** : `executive_status_select` · `collective_agreement`

**`production_object_description`** — 5 lignes, **3/4** colonnes renseignées

- pleines : `description` · `sequence` · `prod_process_line`
- **restées vides** : `image`

**`project_wiki`** — 5 lignes, **5/6** colonnes renseignées

- pleines : `content` · `sequence` · `title` · `folder` · `project`
- **restées vides** : `project_template`

**`quality_characteristic_property`** — 5 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`quality_characteristic_type`** — 5 lignes, **3/3** colonnes renseignées

- pleines : `characteristic_type_select*` · `name*` · `unit`

**`quality_quality_alert`** — 5 lignes, **15/15** colonnes renseignées

- pleines : `dead_line_date` · `description` · `full_name` · `priority_select` · `reference` · `start_date` · `status_select` · `product*` · `responsible` · `root_cause` · `team*` · `work_center`
- partielles : `corrective_actions (80%)` · `end_date (40%)` · `preventive_actions (80%)`

**`quality_required_document`** — 5 lignes, **11/14** colonnes renseignées

- pleines : `comment_str` · `doc_version` · `document_id` · `is_active_version` · `name*` · `related_to_select` · `related_to_select_id` · `sequence` · `status_select` · `type_select` · `project`
- **restées vides** : `dms_file` · `meta_file` · `sale_order`

**`supplychain_timetable_template_line`** — 5 lignes, **5/6** colonnes renseignées

- pleines : `payment_time` · `percentage*` · `period_type_select` · `type_select*` · `timetable_template`
- **restées vides** : `day_select`

**`talent_education_level`** — 5 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`talent_job_position`** — 5 lignes, **17/18** colonnes renseignées

- pleines : `experience_select` · `job_description` · `job_reference` · `job_title*` · `location` · `nb_open_job` · `nb_people_hired` · `position_status_select` · `profile_wanted` · `publication_date` · `salary` · `starting_date` · `status_select` · `company` · `company_department` · `contract_type` · `employee`
- **restées vides** : `mail_account`

**`talent_training_category`** — 5 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`talent_training_skill_set`** — 5 lignes, **2/2** colonnes renseignées

- pleines : `talent_training*` · `skill_set*`

**`account_fixed_asset`** — 4 lignes, **25/77** colonnes renseignées

- pleines : `accounting_value` · `acquisition_date` · `computation_method_select` · `depreciation_plan_select` · `first_depreciation_date` · `first_depreciation_date_init_select` · `first_service_date` · `fixed_asset_seq` · `gross_value` · `is_equal_to_fiscal_depreciation` · `is_ifrs_equal_to_fiscal_depreciation` · `name*` · `number_of_depreciation` · `origin_select` · `periodicity_in_month` · `periodicity_type_select` · `qty` · `reference` · `residual_value` · `status_select` · `company*` · `fixed_asset_category*` · `journal*` · `partner*` · `purchase_account`
- **restées vides** : `comments` · `corrected_accounting_value` · `degressive_coef` · `depreciated_amount_current_year` · `depreciation_end_date` · `disposal_date` · `disposal_qty_select` · `disposal_type_select` · `disposal_value` · `duration_in_month` · `fail_over_depreciation_end_date` · `fiscal_computation_method_select` · `fiscal_degressive_coef` · `fiscal_depreciated_amount_current_year` · `fiscal_duration_in_month` · `fiscal_fail_over_depreciation_end_date` · `fiscal_first_depreciation_date` · `fiscal_first_depreciation_date_init_select` · `fiscal_number_of_depreciation` · `fiscal_periodicity_in_month` · `fiscal_periodicity_type_select` · `ifrs_computation_method_select` · `ifrs_degressive_coef` · `ifrs_depreciated_amount_current_year` · `ifrs_duration_in_month` · `ifrs_fail_over_depreciation_end_date` · `ifrs_first_depreciation_date` · `ifrs_first_depreciation_date_init_select` · `ifrs_number_of_depreciation` · `ifrs_periodicity_in_month` · `ifrs_periodicity_type_select` · `import_already_depreciated_amount` · `import_depreciation_date` · `import_fiscal_already_depreciated_amount` · `import_fiscal_nbr_of_past_depreciations` · `import_ifrs_already_depreciated_amount` · `import_ifrs_nbr_of_past_depreciations` · `import_nbr_of_past_depreciations` · `initial_periodicity_in_month` · `move_generation_exception` · `serial_number` · `transferred_reason_select` · `analytic_distribution_template` · `asset_disposal_reason` · `barcode` · `barcode_type_config` · `disposal_move` · `invoice_line` · `purchase_account_move` · `sale_account_move` · `stock_location` · `tracking_number`

**`base_partner_price_list_price_list_set`** — 4 lignes, **2/2** colonnes renseignées

- pleines : `base_partner_price_list*` · `price_list_set*`

**`base_price_list`** — 4 lignes, **8/12** colonnes renseignées

- pleines : `is_active` · `non_negotiable` · `title*` · `type_select*` · `currency*`
- partielles : `application_begin_date (75%)` · `general_discount (75%)` · `hide_discount (75%)`
- **restées vides** : `application_end_date` · `based_on_select` · `comments` · `parent_price_list`

**`base_stop_reason`** — 4 lignes, **2/2** colonnes renseignées

- pleines : `code` · `name`

**`base_trading_name`** — 4 lignes, **2/12** colonnes renseignées

- pleines : `name` · `company`
- **restées vides** : `analytic_distribution_template` · `component_default_stock_location` · `finished_products_default_stock_location` · `logo` · `partner` · `quality_control_default_stock_location` · `receipt_default_stock_location` · `shipping_default_stock_location` · `waste_default_stock_location` · `workshop_default_stock_location`

**`contract_revaluation_formula`** — 4 lignes, **5/5** colonnes renseignées

- pleines : `code*` · `description` · `formula` · `invoice_comment` · `name`

**`crm_fidelity`** — 4 lignes, **1/2** colonnes renseignées

- pleines : `name`
- **restées vides** : `partner`

**`hr_employment_amendment_type`** — 4 lignes, **2/3** colonnes renseignées

- pleines : `all_companies` · `name`
- **restées vides** : `type_select`

**`hr_employment_contract_type`** — 4 lignes, **3/3** colonnes renseignées

- pleines : `description` · `is_no_longer_used` · `name*`

**`hr_pay_grid`** — 4 lignes, **4/6** colonnes renseignées

- pleines : `conv_hourly_rate` · `conv_monthly_rate` · `collective_agreement` · `qualification`
- **restées vides** : `hourly_complement` · `qualification_level`

**`hr_qualification_level`** — 4 lignes, **3/5** colonnes renseignées

- pleines : `code` · `full_name` · `name`
- **restées vides** : `collective_agreement` · `qualification`

**`maintenance_equipement_maintenance`** — 4 lignes, **11/13** colonnes renseignées

- pleines : `code` · `create_mtn_request_select` · `mtn_each_cycle` · `mtn_each_day` · `mtn_each_duration` · `mtn_procedure` · `name*` · `next_mtn_date` · `machine` · `maintenance_category` · `last_mtn_operating_hours_ref`
- **restées vides** : `image` · `mtn_file`

**`maintenance_maintenance_category`** — 4 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`production_product_approval`** — 4 lignes, **4/4** colonnes renseignées

- pleines : `code*` · `control_on_receipt` · `description` · `name*`

**`production_production_batch`** — 4 lignes, **8/8** colonnes renseignées

- pleines : `action_select*` · `code` · `description` · `fetch_limit` · `company` · `workshop_stock_location`
- partielles : `valuation_date (25%)` · `mtn_anticipation_days (25%)`

**`quality_control_entry`** — 4 lignes, **8/8** colonnes renseignées

- pleines : `entry_date_time*` · `name*` · `related_to_select` · `related_to_select_id` · `sample_count` · `status_select` · `control_plan*` · `inspector*`

**`quality_control_plan`** — 4 lignes, **7/7** colonnes renseignées

- pleines : `code*` · `description` · `name*` · `related_to_select` · `related_to_select_id` · `status_select` · `control_plan_frequency`

**`quality_control_point_type`** — 4 lignes, **1/1** colonnes renseignées

- pleines : `name`

**`quality_qi_action_distribution`** — 4 lignes, **8/9** colonnes renseignées

- pleines : `description` · `distribution_sent` · `document_reference` · `recipient*` · `sequence` · `qi_analysis` · `qi_decision` · `recipient_partner*`
- **restées vides** : `generated_file`

**`quality_quality_control`** — 4 lignes, **11/14** colonnes renseignées

- pleines : `dead_line_date` · `name` · `reference` · `related_to_select` · `related_to_select_id` · `sequence` · `start_date` · `status_select` · `responsible` · `team`
- partielles : `end_date (25%)`
- **restées vides** : `customer_signature` · `inspector_signature` · `printing_settings`

**`talent_talent_source`** — 4 lignes, **2/2** colonnes renseignées

- pleines : `code*` · `name*`

**`account_pfp_partial_reason`** — 3 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`base_partner_price_list`** — 3 lignes, **4/4** colonnes renseignées

- pleines : `is_exclusive` · `label*` · `type_select*` · `currency*`

**`base_site`** — 3 lignes, **9/12** colonnes renseignées

- pleines : `code*` · `full_name` · `invoicing_type_select*` · `is_usable_on_expense` · `is_usable_on_project` · `is_usable_on_timesheet` · `name*` · `type_select*` · `company*`
- **restées vides** : `address` · `partner` · `trading_name`

**`businessproject_invoicing_project`** — 3 lignes, **14/16** colonnes renseignées

- pleines : `additional_element_set_priority_select` · `attach_annex_to_invoice` · `consolidate_phase_when_invoicing` · `expense_line_set_priority_select` · `invoice_line_set_priority_select` · `log_times_set_priority_select` · `project_set_priority_select` · `project_task_set_priority_select` · `purchase_order_line_set_priority_select` · `sale_order_line_set_priority_select` · `status_select` · `stock_move_line_set_priority_select` · `project`
- partielles : `invoice (67%)`
- **restées vides** : `comments` · `deadline_date`

**`businessproject_invoicing_project_project_task_set`** — 3 lignes, **2/2** colonnes renseignées

- pleines : `businessproject_invoicing_project*` · `project_task_set*`

**`crm_agency`** — 3 lignes, **1/1** colonnes renseignées

- pleines : `name`

**`crm_catalog_type`** — 3 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`gdpr_gdpr_processing_register`** — 3 lignes, **6/7** colonnes renseignées

- pleines : `code*` · `description` · `is_archive_data` · `name*` · `retention_period` · `status`
- **restées vides** : `anonymizer`

**`helpdesk_sla`** — 3 lignes, **5/9** colonnes renseignées

- pleines : `days` · `hours` · `is_working_days` · `name*` · `priority_select`
- **restées vides** : `description` · `reach_stage_ticket_status` · `team` · `ticket_type`

**`hr_employee_bonus_mgt`** — 3 lignes, **6/6** colonnes renseignées

- pleines : `base_amount` · `status_select` · `company` · `employee_bonus_type` · `leave_period` · `pay_period`

**`hr_lunch_voucher_mgt`** — 3 lignes, **13/14** colonnes renseignées

- pleines : `export_date_time` · `given_lunch_vouchers` · `lunch_voucher_employers_share` · `lunch_voucher_wage_share` · `requested_lunch_vouchers` · `status_select` · `stock_line_comment` · `stock_line_quantity` · `stock_quantity_status` · `total_lunch_vouchers` · `company` · `leave_period` · `pay_period`
- **restées vides** : `csv_file`

**`hr_medical_visit_reason`** — 3 lignes, **1/1** colonnes renseignées

- pleines : `name*`

**`intervention_intervention_note_type`** — 3 lignes, **2/2** colonnes renseignées

- pleines : `attached_file` · `name*`

**`intervention_justification`** — 3 lignes, **2/2** colonnes renseignées

- pleines : `code` · `name`

**`intervention_rescheduling_reason`** — 3 lignes, **2/2** colonnes renseignées

- pleines : `code` · `name`

**`production_mps_charge`** — 3 lignes, **2/2** colonnes renseignées

- pleines : `end_month_date` · `start_month_date`

**`project_project_task_invoice_line_set`** — 3 lignes, **2/2** colonnes renseignées

- pleines : `project_project_task*` · `invoice_line_set*`

**`project_project_template`** — 3 lignes, **9/13** colonnes renseignées

- pleines : `code` · `description` · `full_name` · `is_business_project` · `is_invoicing_expenses` · `is_invoicing_purchases` · `name*` · `synchronize` · `company`
- **restées vides** : `invoicing_comment` · `task_status_management_select` · `assigned_to` · `team`

**`project_project_version`** — 3 lignes, **3/5** colonnes renseignées

- pleines : `content` · `status_select` · `title`
- **restées vides** : `production_server_date` · `testing_server_date`

**`project_topic`** — 3 lignes, **4/4** colonnes renseignées

- pleines : `is_closed` · `message` · `title` · `project`

**`project_wiki_folder`** — 3 lignes, **1/1** colonnes renseignées

- pleines : `name`

**`projectscheduler_employee_workload`** — 3 lignes, **3/3** colonnes renseignées

- pleines : `from_date*` · `name` · `to_date*`

**`purchase_call_tender`** — 3 lignes, **5/8** colonnes renseignées

- pleines : `call_tender_seq` · `description` · `name` · `company` · `is_attach_file_email`
- **restées vides** : `call_for_tender_mail_template` · `product_attr_report_config` · `supplier_respond_report_config`

**`purchase_call_tender_need`** — 3 lignes, **7/9** colonnes renseignées

- pleines : `requested_date` · `requested_qty*` · `type_select` · `call_tender` · `product*` · `unit` · `description`
- **restées vides** : `requested_delivery_time` · `call_tender_attr_config`

**`quality_control_plan_frequency`** — 3 lignes, **6/6** colonnes renseignées

- pleines : `name` · `sample_frequency*` · `sample_qty*` · `sample_type_select` · `sample_frequency_unit*` · `sample_qty_unit*`

**`quality_qi_decision_distribution`** — 3 lignes, **12/13** colonnes renseignées

- pleines : `answer_required` · `description` · `distribution_sent` · `document_reference` · `recipient*` · `sequence` · `qi_decision` · `qi_resolution*` · `recipient_partner*`
- partielles : `answer_comment (33%)` · `answered_on (33%)` · `answered_by (33%)`
- **restées vides** : `generated_file`

**`quality_quality_process`** — 3 lignes, **2/2** colonnes renseignées

- pleines : `code` · `name*`

**`sale_pack`** — 3 lignes, **8/8** colonnes renseignées

- pleines : `code*` · `do_not_display_header_and_end_pack` · `is_hide_unit_amounts` · `is_show_total` · `name*` · `company` · `currency` · `unit`

**`account_analytic_rules`** — 2 lignes, **4/4** colonnes renseignées

- pleines : `name*` · `company` · `from_account` · `to_account`

**`account_invoice_term_payment`** — 2 lignes, **5/6** colonnes renseignées

- pleines : `company_paid_amount` · `financial_discount_amount` · `paid_amount` · `invoice_term`
- partielles : `invoice_payment (50%)`
- **restées vides** : `financial_discount`

**`base_routing`** — 2 lignes, **4/4** colonnes renseignées

- pleines : `code*` · `is_active` · `name*` · `priority`

**`contract_index_revaluation`** — 2 lignes, **2/2** colonnes renseignées

- pleines : `code*` · `name`

**`crm_tour`** — 2 lignes, **3/3** colonnes renseignées

- pleines : `date_val*` · `name*` · `salesperson_user`

**`hr_health_mutual_rejection_reason`** — 2 lignes, **3/4** colonnes renseignées

- pleines : `code` · `is_inactive` · `name`
- **restées vides** : `old_code`

**`hr_probation_period`** — 2 lignes, **2/8** colonnes renseignées

- pleines : `is_previously_hired` · `name`
- **restées vides** : `comments` · `contract_sub_type` · `contract_type` · `maximum_duration` · `minimum_duration` · `probation_period_duration`

**`production_sop`** — 2 lignes, **8/8** colonnes renseignées

- pleines : `growth_coef` · `is_forecast_on_historic` · `is_generated` · `name` · `company` · `historic_period_year` · `period_year` · `product_category`

**`production_workshop_sequence_config_line`** — 2 lignes, **3/3** colonnes renseignées

- pleines : `production_config` · `sequence*` · `workshop_stock_location*`

**`projectpro_tree_project_reporting_project_set`** — 2 lignes, **2/2** colonnes renseignées

- pleines : `projectpro_tree_project_reporting*` · `project_set*`

**`projectscheduler_employee_skill_planning`** — 2 lignes, **2/2** colonnes renseignées

- pleines : `horizon` · `name*`

**`supplychain_timetable_template`** — 2 lignes, **2/2** colonnes renseignées

- pleines : `code*` · `name*`

**`supplychain_un_code`** — 2 lignes, **2/3** colonnes renseignées

- pleines : `code*` · `code_description*`
- **restées vides** : `security`

**`account_accounting_config_template_company_set`** — 1 lignes, **2/2** colonnes renseignées

- pleines : `account_accounting_config_template*` · `company_set*`

**`account_accounting_report`** — 1 lignes, **35/44** colonnes renseignées

- pleines : `balance` · `complementary_export` · `date_val*` · `date_from` · `date_to` · `detailed` · `display_analytic_accounts_details` · `display_closing_accounting_moves` · `display_code_account_column_on_printing` · `display_cumulative_balance` · `display_details` · `display_move_line_sequence_on_printing` · `display_name_account_column_on_printing` · `display_only_not_completely_lettered_move_lines` · `display_opening_accounting_moves` · `exclude_commitment_special_account` · `exclude_view_account` · `export_type_select` · `exported` · `fixed_asset_line_type_select` · `global` · `global_by_partner` · `is_comparative_balance` · `min_amount_excl` · `move_status_select` · `publication_date_time` · `ref` · `status_select` · `subtotal_by_analytic_distribution` · `total_credit` · `total_debit` · `company` · `currency` · `report_type` · `year`
- **restées vides** : `other_date_from` · `other_date_to` · `analytic_distribution_template` · `analytic_journal` · `journal` · `other_period` · `other_year` · `payment_mode` · `period`

**`account_analytic_journal_type`** — 1 lignes, **2/2** colonnes renseignées

- pleines : `code*` · `name*`

**`account_invoice_payment`** — 1 lignes, **16/28** colonnes renseignées

- pleines : `amount*` · `apply_financial_discount` · `financial_discount_amount` · `financial_discount_tax_amount` · `financial_discount_total_amount` · `manual_change` · `payment_date*` · `status_select` · `total_amount_with_financial_discount` · `type_select` · `company_bank_details` · `currency*` · `invoice` · `move` · `payment_mode` · `reconcile`
- **restées vides** : `bank_deposit_date` · `cheque_number` · `delay_reason` · `description` · `financial_discount_deadline_date` · `invoice_payment_ref` · `bank_order` · `cancel_reason` · `company_bank_card` · `financial_discount` · `imputed_by` · `payment_session`

**`account_invoice_term_payment_reconcile_list`** — 1 lignes, **2/2** colonnes renseignées

- pleines : `account_invoice_term_payment*` · `reconcile_list*`

**`account_reconcile`** — 1 lignes, **11/13** colonnes renseignées

- pleines : `amount` · `can_be_zero_balance_ok` · `effective_date` · `must_be_zero_balance_ok` · `reconcile_seq` · `reconciliation_date_time` · `status_select` · `company*` · `credit_move_line*` · `debit_move_line*` · `reconcile_group`
- **restées vides** : `reconciliation_cancel_date_time` · `foreign_exchange_move`

**`account_reconcile_group`** — 1 lignes, **5/6** colonnes renseignées

- pleines : `code` · `is_proposal` · `lettering_date_time` · `status_select` · `company*`
- **restées vides** : `unlettering_date_time`

**`account_tax_payment_move_line`** — 1 lignes, **10/11** colonnes renseignées

- pleines : `date_val` · `detail_payment_amount` · `functional_origin_select` · `is_already_reverse` · `tax_amount` · `tax_rate` · `vat_system_select` · `move_line` · `origin_tax_line` · `reconcile`
- **restées vides** : `fiscal_position`

**`businessproject_business_project_batch`** — 1 lignes, **6/9** colonnes renseignées

- pleines : `action_select*` · `code` · `consolidate_phase_select` · `fetch_limit` · `company` · `period`
- **restées vides** : `deadline_date` · `description` · `from_date`

**`hr_collective_agreement`** — 1 lignes, **4/4** colonnes renseignées

- pleines : `code` · `full_name` · `name` · `weekly_work_duration`

**`hr_smic_value`** — 1 lignes, **3/3** colonnes renseignées

- pleines : `name` · `smic_value` · `update_date`

**`intervention_intervention_config`** — 1 lignes, **5/9** colonnes renseignées

- pleines : `customer_request_creation_automatic_mail` · `intervention_planification_automatic_mail` · `intervention_re_planification_automatic_mail` · `intervention_validation_automatic_mail` · `company*`
- **restées vides** : `customer_request_creation_message_template` · `intervention_planification_message_template` · `intervention_re_planification_message_template` · `intervention_validation_message_template`

**`management_forecast_recap`** — 1 lignes, **14/15** colonnes renseignées

- pleines : `calculation_date` · `current_balance` · `display_type_select` · `ending_balance` · `forecast_recap_seq` · `from_date` · `is_complete` · `is_report` · `opportunities_type_select` · `starting_balance*` · `to_date` · `company*` · `currency` · `user_recap`
- **restées vides** : `sales_man`

**`production_cost_sheet`** — 1 lignes, **7/8** colonnes renseignées

- pleines : `calculation_date` · `calculation_qty` · `calculation_type_select` · `cost_price` · `manuf_order_produced_ratio` · `currency` · `manuf_order`
- **restées vides** : `bill_of_material`

**`production_manuf_order`** — 1 lignes, **20/36** colonnes renseignées

- pleines : `cost_price` · `end_time_difference` · `is_cons_pro_on_operation` · `manuf_order_seq` · `operation_order_max_priority` · `outsourcing` · `plan_only_missing_quantities` · `planned_end_datet` · `planned_start_datet` · `priority_select` · `qty` · `real_end_datet` · `real_start_datet` · `status_select` · `type_select` · `bill_of_material` · `company` · `prod_process*` · `product` · `unit`
- **restées vides** : `cancel_reason_str` · `mo_comment_from_sale_order` · `mo_comment_from_sale_order_line` · `note` · `waste_prod_description` · `bar_code` · `cancel_reason` · `client_partner` · `machine` · `machine_type` · `manuf_order_merge_result` · `outsourcing_partner` · `parentmo` · `sale_order_line` · `waste_stock_move` · `workshop_stock_location`

**`projectpro_tree_project_reporting`** — 1 lignes, **1/1** colonnes renseignées

- pleines : `name*`
