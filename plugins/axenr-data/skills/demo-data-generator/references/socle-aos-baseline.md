# Carte de référence du socle AOS

> **Ce que ce document sert.** Le skill ne doit **jamais réinjecter** ce qu'une install AOS
> livre déjà, et il doit savoir distinguer *« vide parce qu'AOS ne le remplit jamais »* de
> *« vide parce qu'on a oublié »*. Sans cette carte, un audit de complétude en valeur absolue
> confond les deux et produit soit du bruit, soit des angles morts.
>
> Ce document ne contient **aucune donnée métier**. Il contient le périmètre du socle, les
> volumétries de référence, et la méthode. La donnée métier se génère par démo, à partir du
> contexte réel du client — jamais par recopie d'un jeu antérieur.

## 1. Provenance et méthode (falsifiable, régénérable)

| Base | Rôle | AOS | Modules | Taille |
|---|---|---|---|---|
| `<base-vierge>` | install démo **vierge** — le socle | 9.1.3 | 60 | 178 Mo |
| `<base-vierge-alt>` | socle vierge alternatif | 9.0.8 | 43 | 167 Mo |
| `<base-travaillee>` | démo **travaillée** (29 batches, démo ESN) — la référence « crédible » | 9.0.8 | 45 | 190 Mo |

Comptages exacts (pas `reltuples`) sur les 1 410 / 1 350 tables `public`, via
`query_to_xml`. Régénération : `scripts/baseline-map.sh <base-vierge> <base-travaillee>`.

**Limite assumée** : les deux bases comparées ne sont pas sur la même version (9.1.3 vs
9.0.8) ni le même jeu de modules (60 vs 45). 1 340 tables sont communes et servent de base
au calcul ; les 70 tables propres à `<base-vierge>` ne sont pas comparables. Aucune conclusion de
ce document ne repose sur les tables non communes. À rafraîchir dès qu'un couple de bases de
même version est disponible.

### Provisionner un socle neuf avec données de démo (2026-09-07)

Sur une base **neuve** (0 table avant boot), poser `data.import.demo-data = true` +
`studio.apps.install = <liste explicite de codes>` (jamais `all`, non testé) +
`application.mode = dev` + `application.locale = fr` dans `axelor-config.properties`
installe, au 1er boot, les apps listées **avec leurs données de démo**
(`studio_app.active=true` et `demo_data_loaded=true`) ; les apps non listées restent
inertes. Vérifié sur AOS 9.1.6 / plateforme EE 8.2.3 / axelor-studio 4.0.7 (chantier
de package de démo Industry, 8 apps installées sur 51 disponibles). Sur une
base **déjà initialisée**, aucun re-seed n'a été observé ni testé : l'activation
d'une app supplémentaire APRÈS le 1er boot avec ses données de démo est lue au code
seul, non testée.

## 2. Les trois compartiments

Sur les **1 340 tables communes** :

| | Compartiment | Tables | Conséquence pour le skill |
|---|---|---:|---|
| **A** | AOS remplit déjà | **470** | Ne rien injecter. Maîtriser le périmètre, juger la crédibilité. |
| **B** | AOS laisse vide, une démo a dû remplir | **161** (155 utiles) | Le catalogue d'enrichissement. C'est là que le skill travaille. |
| **C** | Vide dans les deux | **709** | Angles morts. Jamais démontré, crédibilité inconnue. |

**Le compartiment C est la borne honnête du skill** : 709 tables sur 1 340 n'ont jamais été
peuplées, ni par AOS ni par une démo réelle. Le skill ne doit pas prétendre les couvrir.

## 3. Compartiment A — ce qu'AOS livre (ne pas réinjecter)

Extrait par volume, hors jonctions et tables techniques :

| Table | Lignes livrées par AOS |
|---|---:|
| `stock_customs_code_nomenclature` | 12 359 |
| `base_canton` | 2 054 |
| `account_account` (PCG, 1 société) | 1 044 |
| `base_main_activity` (NAF) | 732 |
| `stock_stock_location_line` | 275 |
| `base_period` | 258 |
| `base_address` | 252 |
| `base_country` | 246 |
| `base_citizenship` | 208 |
| `stock_stock_move_line` | 176 |
| `base_currency` | 166 |
| `account_interbank_code_line` | 164 |
| `base_city` | 129 |
| `base_department` | 101 |
| `base_sequence` | 100 |
| `stock_inventory_line` | 97 |
| `base_product` | 80 |
| `base_partner` | 75 |
| `budget_budget_line` | 70 |
| `account_accounting_situation` | 67 |
| `account_move_line` | 59 |
| `account_account_management` | 59 |
| `production_bill_of_material` | 44 |

**Y compris toute la couche droits** : 26 users, 30 groupes (`CST`, `CLT`, `OPS`, `DAF`,
`MGT`, `VTE`, `ACH`, `CPT`, `HRM`, `ERP`, `CRM`, `FRN`, `BPM`, `biUsers`, 12 × `mobile.*`),
33 rôles, 243 permissions. Vérifié : aucun groupe de `<base-travaillee>` n'est absent de `<base-vierge>`.
Construire des groupes métier en SQL revient donc, dans le cas général, à réécrire l'existant.

## 4. Le vrai défaut du socle : la largeur, pas le nombre de lignes

AOS livre des lignes, mais creuses. Colonnes **100 % NULL** (hors colonnes techniques) :

| Table | AOS vierge | Après 29 batches (`<base-travaillee>`) |
|---|---|---|
| `hr_employee` | 21 l. — **52 %** des colonnes vides | 21 l. — 48 % |
| `account_invoice` | 14 l. — **47 %** | 20 l. — 35 % |
| `contract_contract` | 1 l. — **47 %** | 2 l. — 49 % |
| `stock_stock_move` | 15 l. — **47 %** | 21 l. — 44 % |
| `sale_sale_order` | 13 l. — **43 %** | 18 l. — 37 % |
| `sale_sale_order_line` | 40 l. — **40 %** | 68 l. — 38 % |
| `base_partner` | 75 l. — **38 %** | 108 l. — 28 % |
| `purchase_purchase_order` | 9 l. — **37 %** | 14 l. — 37 % |
| `base_address` | 252 l. — **34 %** | 277 l. — 27 % |
| `crm_opportunity` | 32 l. — **33 %** | 62 l. — 37 % |
| `base_product` | 80 l. — **15 %** | 86 l. — 17 % |
| `production_manuf_order` | **0 ligne** | 1 l. — 46 % |

**Deux enseignements.** Un tiers à la moitié des colonnes métier sont structurellement vides
dans le socle AOS. Et 29 batches de travail ne les ont quasiment pas rattrapées : un écran
paraît rempli tant qu'on reste sur la grille, et se révèle creux dès qu'on ouvre la fiche.
**Le skill doit auditer en largeur (colonnes) autant qu'en profondeur (lignes).**

## 5. Règles de crédibilité — issues d'un cas réel raté

Mesuré sur les 95 projets `AFF-*` de `<base-travaillee>` : 270 tâches, moyenne **2,8 par projet**.
Distribution réelle : **13 projets à 0 tâche**, **77 projets à exactement 3 tâches**, 3 à 4,
1 à 6, 1 à 21.

Ce n'est pas un problème de volume, c'est un copier-coller. D'où les règles :

1. **Aucun parent à 0 enfant sur un axe démontré.** 14 % du portefeuille vide suffit à
   griller la démo si le prospect clique au hasard.
2. **La profondeur suit une traîne longue, jamais une constante.** 77 enregistrements de
   profondeur identique est la signature visible d'un jeu fabriqué.
3. **Plusieurs enregistrements héros, 5 à 10× la médiane.** `<base-travaillee>` n'en avait qu'un
   (21 tâches) : dès qu'on ouvrait un autre projet, l'illusion tombait.
4. **La largeur avant le volume.** Mieux vaut 20 tiers complets que 100 tiers à 38 % de
   colonnes vides. Cf. §4.
5. **Cohérence des agrégats.** Un total d'entête doit égaler la somme de ses lignes ; un
   `count()` non nul ne prouve pas qu'une donnée est exploitable.

## 6. Frontière UI / SQL — ce que l'agent ne fait jamais

Certains objets ne sont pas des lignes, ce sont les **produits d'un service applicatif**.
Les écrire en SQL fabrique un enregistrement d'apparence correcte et un système incohérent.

### L'utilisateur fait dans l'UI — l'agent attend

| Objet | Pourquoi le SQL est une aberration |
|---|---|
| **Création d'une société** | 19 tables `*_config` portent une FK `company` (`account`, `bank_payment`, `business_project`, `crm`, `hr`, `intervention`, `production`, `project`, `purchase`, `quality`, `sale`, `stock`, `supplychain`…) et **145 tables** portent une colonne `company`. Aucune n'est dérivable. |
| **Import du plan comptable** par société | Passe par le template comptable et ses contrôles ; 1 044 comptes à recréer avec leurs équivalences et positions fiscales. |
| **Configuration par module** de chaque société | Chaque `*_config` porte des invariants que l'UI seule garantit. |
| **Ventilation / comptabilisation d'une facture** | Génère les écritures équilibrées, le lettrage et la situation comptable. Un `account_invoice` ventilé à la main en SQL est un faux. |
| **Planification d'un ordre de fabrication** | Dérive les `operation_order`, les durées, la charge machine et les dates. |
| **Toute transition de statut d'un flux** (SO → facture, PO → réception, réception → mouvement de stock) | Le passage de statut *est* l'appel de service. |

### L'agent fait en SQL — après que l'utilisateur a fait sa part

| Action | Portée |
|---|---|
| **Squelette d'enregistrement à l'état brouillon** | En-têtes et lignes de `manufOrder`, `invoice`, `saleOrder` que l'utilisateur fera avancer ensuite dans l'UI. |
| **Alignement post-création de société** | Différencier les emplacements de stock par nom ; compléter **toutes** les séquences en les différenciant (aucune manquante) ; rattacher tiers, produits et employés aux sociétés concernées pour éviter l'invisibilisation ; rattacher les employés à rôle transverse (direction, fonctions groupe). |
| **Silotage des droits** | Groupes, rôles et permissions par structure — via le skill dédié aux profils, pas à la main. |
| **Enrichissement du compartiment B** | Cf. §7. |
| **Corrections de masse** | Booléens NULL, sélections invalides, FK résolues à NULL en silence, agrégats faux. |

**Séquence imposée** : l'utilisateur crée la société et ses configs dans l'UI → **puis**
l'agent aligne en SQL. Jamais l'inverse, jamais en parallèle.

### Séquence transactionnelle éprouvée (flux valorisés) — pourquoi la règle 12 est formulée ainsi

*(Déplacé depuis l'ancien SKILL.md, section « Transactionnel & redatage » : 3e copie de la même frontière SQL/UI, fusionnée ici plutôt que dupliquée.)*

Séquence éprouvée sur des ordres de fabrication, réutilisable pour tout flux qui calcule des montants :

**1) Plan** (volumétrie + statuts visés) → **2) dump filet** (un flux mouvemente le stock **existant**)
→ **3) saisir un maximum de dates DANS l'UI** → **4) jouer le flux via l'UI** → **5) redater en SQL ce
que le moteur a horodaté à `NOW()`** → **6) cloner le motif obtenu** pour l'historique.

Justification mesurée : **un seul OF** joué en UI a produit 1 ordre, **7 opérations** (gamme déployée,
postes et machines, dates enchaînées), **9 lignes de composants** aux quantités exactes (nomenclature ×
quantité), 1 feuille de coût et **20 lignes de coût**. Inécrivable proprement à la main.

- **Les dates PLANIFIÉES passées sont acceptées en UI** ; elles déclenchent un **avertissement modal
  non bloquant** (« la date de fin prévue est inférieure à la date actuelle ») → confirmer. Bénéfice :
  les `estimated_date` des mouvements de stock **héritent** de ces dates, la cohérence se propage sans
  SQL.
- **Les dates RÉELLES sont posées à `NOW()`** par les boutons → le redatage SQL reste indispensable et
  doit couvrir **tout le graphe** : ordre, opérations, **durées d'opération (couple start/stop dont la
  durée découle)**, mouvements de stock, lignes de mouvement, date de calcul de la feuille de coût.
  Décaler la seule table d'entête produit un ordre de mai qui consomme du stock en août.
- **Attention : Un offset unique ne suffit pas** : il conserve la cohérence relative mais **importe la durée du
  jeu** (5 serveurs « fabriqués en 11 minutes », opérations de 39 ms), et un décalage horaire fait
  **basculer les colonnes de type DATE au jour précédent**. Un facteur multiplicatif ne corrige pas des
  durées quasi nulles (39 ms × 410 = 16 s).
  **Pattern correct, en 3 règles** : (a) les dates réelles d'entête = les dates **prévues** ; (b) les
  dates réelles des lignes se **reconstruisent depuis la gamme** (`real = planned` de chaque opération,
  avec une **durée plancher** — 30 min — pour celles sans temps machine) ; (c) les colonnes **DATE** se
  recalent **explicitement** (consommation = début, production = fin), jamais par arithmétique
  d'intervalle. *(À nuancer avec le pitfall #26 : sur des ordres créés **purement en SQL**, ajouter de
  petits deltas variés pour éviter l'effet « trop parfait ». Sur un ordre **joué en UI puis redaté**,
  l'alignement sur le prévu est la seule façon d'obtenir des durées réalistes.)*
- **Attention : Ne JAMAIS relancer un calcul de coût après un redatage — quand il y a un coût JUSTE à
  préserver.** Vécu : la feuille produite par le flux valait **1 636,50 € pour 5 serveurs (327 €/u —
  juste)** ; un recalcul post-redatage a produit **537 862,50 €** en valorisant 7 postes à **1920 h**
  chacun. Ordre correct dans ce cas : jouer le flux → laisser le moteur calculer → **puis** redater, et
  ne plus recalculer.
  **L'exception, mesurée le 2026-09-22 (9.1.3)** : quand le flux a été joué **par script**, les durées
  réelles sortent à **zéro** (piège 125) et il n'y a rien à préserver — le recalcul est alors la seule
  voie, à la condition stricte d'un **redémarrage entre la correction SQL et le recalcul**. Trancher
  entre les deux cas en lisant `production_operation_order.real_duration` **avant** de décider :
  non nul = garde ci-dessus, nul = piège 125.
- **Un flux laisse des feuilles de coût parasites** : 3 feuilles pour un seul ordre (une correcte, une à
  0 € générée par le bouton de clôture, une fausse). Garder une seule feuille et contrôler la
  **plausibilité du coût unitaire** (garde : entre 100 et 5 000 € pour un assemblage) plutôt que la
  seule présence. `calculation_qty` sort à **0** même quand l'ordre porte 5 unités.
- **`CostSheetLine` est une arborescence** : seule la ligne racine porte `cost_sheet`, le détail pend par
  `parent_cost_sheet_line`. Compter par `cost_sheet` seul fait croire à des orphelines. Garde utile :
  `consumption_qty > 24` sur un poste = durée aberrante.
- **Granularité des boutons** : vérifier s'il existe un bouton global avant de budgéter N clics par
  ligne — un « Fin » a terminé les 7 opérations, créé leurs durées et recalculé les coûts en une fois.
- **Toutes les tables ne sont pas atteignables par le cycle de vie** : un ordre de production vient
  d'une **commande client**, un besoin en matière a son **menu propre** (saisie manuelle → SQL sans
  risque, aucun agrégat). **Vérifier quel bouton peuple quelle table avant de promettre une couverture.**
- **Tester l'idempotence par un re-run** avant de déclarer terminé (attendu : `INSERT 0` partout).
  Attention : Le test lui-même peut polluer : un re-run a créé 6 doublons parce que la garde portait sur
  `NOW()`. Une garde d'idempotence doit reposer sur une **clé métier stable** (code, nom, séquence),
  **jamais** sur une valeur dérivée de `NOW()`.

### Pourquoi la règle 12 ne parle plus de « statut »

La formulation historique était « les flux valorisés passent par l'UI ». Le 2026-08-11, sur `<base-travaillee>`, elle a été élargie en « tout ce qui porte un statut passe par l'UI » — une sur-généralisation qui a fait renoncer pendant plusieurs jours à du SQL parfaitement légitime. Le critère n'est pas le statut, c'est : **le moteur produit-il quelque chose que le SQL devrait ensuite réécrire ?** Une commande, une facture, un mouvement de stock : oui (totaux, écritures, lignes dérivées) → moteur. Une opportunité CRM : non — elle n'a pas de lignes, `amount`, `best_case`, `worst_case` et `probability` sont saisis, il n'existe aucune contrepartie comptable → SQL, en consommant la séquence (piège 73), en recopiant les dénormalisations (piège 74) et en rattachant un contact du tiers de l'affaire. Leads, opportunités et événements se seedent donc en SQL. Les services de conversion (Lead → Opportunité → Commande), eux, créent des objets liés multi-modules : ils restent au moteur.

Corollaire souvent oublié dans les deux sens : **« moteur » ne veut pas dire « clic à la main »**. Un bouton AOS est une `action-method`, appelable en REST sur `/ws/action` : la transition est scriptable et rejouable sans qu'un humain clique. La frontière est SQL contre moteur, pas SQL contre UI — et budgéter N clics manuels avant d'avoir cherché le point d'entrée du bouton est une erreur de chiffrage, pas une précaution.

C'est aussi pourquoi la création d'une société reste hors SQL sans exception : 19 tables `*_config` portent une FK `company` et 145 tables une colonne `company`, aucune n'est dérivable. L'utilisateur crée la société, le plan comptable et les configurations par module dans l'UI ; **puis** l'agent aligne en SQL (emplacements différenciés, séquences complètes, rattachement des tiers, produits et employés pour éviter l'invisibilisation, silotage des droits). Jamais l'inverse.

## 7. Compartiment B — catalogue d’enrichissement (155 tables)

Tables **vides dans le socle AOS** qu'une démo réelle a dû peupler. La colonne volumétrie
est une **référence empirique**, pas une cible : elle dit l'ordre de grandeur qui a suffi
une fois, à recalibrer selon la taille et le secteur du client (§5).

> **La shape de ces 155 tables est dans `references/socle-b-shape.md`** — quelles colonnes ont
> été effectivement renseignées, à quel taux, et lesquelles sont restées vides (981 renseignées,
> 250 vides). Ce fichier porte trois avertissements à lire **avant** de produire : les tables qui
> doivent être **générées par le moteur** et non écrites en SQL (rapports projet, feuilles de
> coût, ordres d'opération), les 24 jonctions M2M dont le remplissage conditionne l'affichage,
> et le statut d'observation — non de cible — de la volumétrie.

**`projectpro`** — 6 tables, 3323 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `projectpro_project_report_employee_line` | 1467 |
| `projectpro_project_report` | 1062 |
| `projectpro_project_report_line` | 663 |
| `projectpro_project_task_progress` | 128 |
| `projectpro_tree_project_reporting_project_set` | 2 |
| `projectpro_tree_project_reporting` | 1 |

**`projectscheduler`** — 7 tables, 519 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `projectscheduler_project_planning_project_set` | 385 |
| `projectscheduler_project_planning_employee_set` | 102 |
| `projectscheduler_employee_skill_planning_employee_set` | 10 |
| `projectscheduler_project_planning` | 9 |
| `projectscheduler_employee_skill_planning_skill_set` | 8 |
| `projectscheduler_employee_workload` | 3 |
| `projectscheduler_employee_skill_planning` | 2 |

**`businessproject`** — 6 tables, 346 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `businessproject_invoicing_project_log_times_set` | 275 |
| `businessproject_business_project_batch_project_set` | 59 |
| `businessproject_project_folder` | 5 |
| `businessproject_invoicing_project` | 3 |
| `businessproject_invoicing_project_project_task_set` | 3 |
| `businessproject_business_project_batch` | 1 |

**`quality`** — 24 tables, 181 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `quality_control_entry_plan_line` | 30 |
| `quality_quality_measuring_point` | 22 |
| `quality_tracking_number_characteristic` | 20 |
| `quality_control_entry_sample` | 8 |
| `quality_control_point` | 8 |
| `quality_control_point_model` | 7 |
| `quality_product_characteristic` | 7 |
| `quality_characteristic_type_characteristic_set` | 6 |
| `quality_control_plan_line_characteristic` | 6 |
| `quality_quality_corrective_action` | 6 |
| `quality_quality_pictures` | 6 |
| `quality_root_cause` | 6 |
| `quality_characteristic_property` | 5 |
| `quality_characteristic_type` | 5 |
| `quality_quality_alert` | 5 |
| `quality_required_document` | 5 |
| `quality_control_entry` | 4 |
| `quality_control_plan` | 4 |
| `quality_control_point_type` | 4 |
| `quality_qi_action_distribution` | 4 |
| `quality_quality_control` | 4 |
| `quality_control_plan_frequency` | 3 |
| `quality_qi_decision_distribution` | 3 |
| `quality_quality_process` | 3 |

**`project`** — 8 tables, 149 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `project_project_project_folder_set` | 123 |
| `project_resource_type` | 6 |
| `project_wiki` | 5 |
| `project_project_task_invoice_line_set` | 3 |
| `project_project_template` | 3 |
| `project_project_version` | 3 |
| `project_topic` | 3 |
| `project_wiki_folder` | 3 |

**`talent`** — 15 tables, 147 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `talent_experience` | 18 |
| `talent_certification` | 17 |
| `talent_job_application_industry_sector_set` | 16 |
| `talent_job_application_skill_set` | 16 |
| `talent_education` | 15 |
| `talent_job_application_language_set` | 14 |
| `talent_job_application` | 8 |
| `talent_skill` | 7 |
| `talent_positioning` | 6 |
| `talent_training_session` | 6 |
| `talent_education_level` | 5 |
| `talent_job_position` | 5 |
| `talent_training_category` | 5 |
| `talent_training_skill_set` | 5 |
| `talent_talent_source` | 4 |

**`hr`** — 17 tables, 112 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `hr_medical_visit` | 25 |
| `hr_lunch_voucher_mgt_line` | 24 |
| `hr_employee_bonus_mgt_line` | 16 |
| `hr_employment` | 6 |
| `hr_end_of_contract_reason` | 5 |
| `hr_qualification` | 5 |
| `hr_employment_amendment_type` | 4 |
| `hr_employment_contract_type` | 4 |
| `hr_pay_grid` | 4 |
| `hr_qualification_level` | 4 |
| `hr_employee_bonus_mgt` | 3 |
| `hr_lunch_voucher_mgt` | 3 |
| `hr_medical_visit_reason` | 3 |
| `hr_health_mutual_rejection_reason` | 2 |
| `hr_probation_period` | 2 |
| `hr_collective_agreement` | 1 |
| `hr_smic_value` | 1 |

**`production`** — 14 tables, 83 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `production_cost_sheet_line` | 20 |
| `production_sop_line` | 12 |
| `production_prod_product` | 9 |
| `production_operation_order` | 7 |
| `production_operation_order_duration` | 7 |
| `production_machine_tool` | 6 |
| `production_object_description` | 5 |
| `production_product_approval` | 4 |
| `production_production_batch` | 4 |
| `production_mps_charge` | 3 |
| `production_sop` | 2 |
| `production_workshop_sequence_config_line` | 2 |
| `production_cost_sheet` | 1 |
| `production_manuf_order` | 1 |

**`base`** — 11 tables, 64 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `base_industry_sector` | 20 |
| `base_price_list_line` | 10 |
| `base_file` | 5 |
| `base_partner_role` | 5 |
| `base_partner_price_list_price_list_set` | 4 |
| `base_price_list` | 4 |
| `base_stop_reason` | 4 |
| `base_trading_name` | 4 |
| `base_partner_price_list` | 3 |
| `base_site` | 3 |
| `base_routing` | 2 |

**`contract`** — 5 tables, 54 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `contract_contract_line` | 18 |
| `contract_contract_line_tax_line_set` | 18 |
| `contract_contract_template_contract_line_list` | 12 |
| `contract_revaluation_formula` | 4 |
| `contract_index_revaluation` | 2 |

**`account`** — 14 tables, 39 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `account_analytic_rules_analytic_account_set` | 14 |
| `account_invoice_stock_move_set` | 6 |
| `account_fixed_asset` | 4 |
| `account_pfp_partial_reason` | 3 |
| `account_analytic_rules` | 2 |
| `account_invoice_term_payment` | 2 |
| `account_accounting_config_template_company_set` | 1 |
| `account_accounting_report` | 1 |
| `account_analytic_journal_type` | 1 |
| `account_invoice_payment` | 1 |
| `account_invoice_term_payment_reconcile_list` | 1 |
| `account_reconcile` | 1 |
| `account_reconcile_group` | 1 |
| `account_tax_payment_move_line` | 1 |

**`crm`** — 7 tables, 32 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `crm_tour_line` | 8 |
| `crm_corporate_partner_domain` | 6 |
| `crm_lost_reason` | 6 |
| `crm_fidelity` | 4 |
| `crm_agency` | 3 |
| `crm_catalog_type` | 3 |
| `crm_tour` | 2 |

**`purchase`** — 4 tables, 24 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `purchase_call_tender_offer` | 9 |
| `purchase_call_tender_supplier` | 9 |
| `purchase_call_tender` | 3 |
| `purchase_call_tender_need` | 3 |

**`maintenance`** — 3 tables, 23 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `maintenance_maintenance_request` | 15 |
| `maintenance_equipement_maintenance` | 4 |
| `maintenance_maintenance_category` | 4 |

**`management`** — 3 tables, 21 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `management_forecast_recap_line` | 14 |
| `management_forecast` | 6 |
| `management_forecast_recap` | 1 |

**`team`** — 1 tables, 15 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `team_task` | 15 |

**`intervention`** — 4 tables, 10 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `intervention_intervention_note_type` | 3 |
| `intervention_justification` | 3 |
| `intervention_rescheduling_reason` | 3 |
| `intervention_intervention_config` | 1 |

**`supplychain`** — 3 tables, 9 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `supplychain_timetable_template_line` | 5 |
| `supplychain_timetable_template` | 2 |
| `supplychain_un_code` | 2 |

**`gdpr`** — 1 tables, 3 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `gdpr_gdpr_processing_register` | 3 |

**`helpdesk`** — 1 tables, 3 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `helpdesk_sla` | 3 |

**`sale`** — 1 tables, 3 lignes de référence

| Table | Volumétrie de référence |
|---|---:|
| `sale_pack` | 3 |

## 8. Ce que cette carte remplace

Le SQL rejouable extrait de `<base-travaillee>` (8,9 Mo, 8 fichiers, 65 tables ; dossier de l'auteur, non livré) apporte,
par-dessus une install AOS vierge : 1 société supplémentaire, 1 044 comptes (le PCG de cette
2ᵈᵉ société), 47 séquences, 8 journaux, 33 tiers, 6 produits, 6 villes, 101 projets, 282 tâches.
**Sur les 155 tables du compartiment B, il n'en couvre que 2** (`hr_qualification`,
`hr_employment_contract_type`, 9 lignes).

Autrement dit : l'enrichissement des tables nativement vides — RH, Qualité, Achats, Talent,
Contrat, Production, CRM, Maintenance, reporting projet — **n'est pas dans ce SQL**. Il n'existe
que dans `<base-travaillee>` et dans les 29 batches incrémentaux (non livrés), qui ne
sont pas rejouables sur base vierge.

Et il n'a pas à y être sous forme de données : ce qui doit survivre, c'est **la liste des
tables à peupler et l'ordre de grandeur** — c'est-à-dire ce document. La donnée se régénère
par démo, à partir du métier du client.

## 9. Rafraîchir cette carte

```bash
scripts/baseline-map.sh <base-vierge> <base-travaillee>
```

Produit les trois compartiments, les taux de remplissage par colonne et le catalogue B.
À relancer :

- à chaque montée de version AOS (le socle bouge : 9.1.3 livre 60 modules contre 43 en 9.0.8) ;
- dès qu'une démo travaillée plus riche que `<base-travaillee>` devient la nouvelle référence de
  crédibilité ;
- avant tout audit de complétude, si la version de la base cible diffère de celle du §1.

**Ne jamais raisonner sur `import_id`, `import_origin` ou `created_on` pour distinguer le
socle du travail ajouté.** Vérifié faux dans les deux sens : les batches ont massivement fait
des `UPDATE` sur des lignes d'origine AOS (l'`import_id` survit à la modification), et le tag
`import_origin` posé par les batches ne couvrait que 14 lignes sur ~8 000. La seule méthode
fiable est la comparaison de comptages contre une base vierge de référence.
