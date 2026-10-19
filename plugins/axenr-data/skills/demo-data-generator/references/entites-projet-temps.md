# Entités — projet & temps (projet, tâche, employé, contrat, feuille de temps, plan de charge)

> **Couche UI-critical uniquement.** Ce que ni le schéma (`scripts/shape-fiche.sh`,
> `introspect.sh`) ni un enregistrement modèle ne donnent. Les NOT NULL, FK, sélections et taux de
> remplissage s'introspectent au moment de produire (règle 1) — ils ne sont pas ici.
>
> **Établie empiriquement le 2026-09-03** sur `<base>` — **AOS 9.1.6 / plateforme
> EE 8.2.3** (périmètre business-project, project-pro, project-scheduler, business-support, +
> module local `axelor-construction`). Même protocole que `entites-ventes.md` : INSERT minimal
> tagué `import_origin='stress-c3'` (ids ≥ 900000), test de chaque domaine de menu au REST,
> ouverture au navigateur, bissection, nettoyage vérifié par comptage.
> Le journal et les captures citées (`c3-*.png`) ne sont pas livrés avec ce skill.
>
> `[prouvé]` = reproduit sur cette version, preuve citée · `[statique]` = repris de l'analyse des
> sources, **non reproduit à l'écran** · `[non résolu]` = la bissection n'a pas tranché.

**Pièges déjà existants que cette fiche concerne** (numéros inchangés) :

- 4. Aucune sélection inventée : `0` est souvent invalide — `methode-ecriture-sql.md`
- 6.bis. `contact_partner` d'un employé : la forme canonique à 4 booléens — `entites-tiers-contacts.md`
- 52. Cache Hibernate L2 — `methode-audit.md` (**étendu par le 96 ci-dessous**)
- 62 / 76. Booléen NULL exclu des grids ; `= false` exclut les NULL — `methode-audit.md`
- 70 / 71 / 92. `full_name` périmé, NULL = invisible, et la cascade à N niveaux — `entites-tiers-contacts.md`, `methode-audit.md`
- 73. Consommer la séquence, `setval` dérivé du max réellement occupé — `methode-ecriture-sql.md`
- 91. Lire le panneau ACTIF, pas `document.body` — `methode-audit.md`
- 94. Omettre la clé `data` au REST désactive le filtre `archived` — `methode-audit.md`
- Règle 11 et `methode-dates.md` : les temps natifs AOS ne sont pas fiables, la contenance
  projet / feuille / tâche s'audite (dimension 11).

**Filtres transverses cités une seule fois** : `archived` sur tous les menus, périmètre société par
`:__user__.activeCompany`.

---

## 0. Le fait structurant du domaine : ici, la visibilité dépend d'AUTRE CHOSE que de l'enregistrement

Sur les ventes, une ligne invisible l'est presque toujours à cause de ses propres colonnes. Sur
projet/temps, **trois des sept tables dépendent d'un enregistrement tiers** — et c'est ce que ni le
schéma ni une lecture des vues ne donnent :

| Table | Ce qui décide de sa visibilité | Preuve |
|---|---|---|
| `hr_timesheet` | `employee` → **l'existence d'un `auth_user` lié à cet employé** | `[prouvé]` §5 |
| `hr_timesheet_line` | `project` → **`manage_time_spent = true` sur ce projet** | `[prouvé]` §6 |
| `project_project_task` | `project` → `isBusinessProject` du projet ; `status` → `isCompleted` du statut | `[prouvé]` §2 |

Corollaire de méthode : un audit de complétude qui compte les lignes de ces trois tables et les
déclare « peuplées » peut décrire un écran vide. Les compter **par le domaine du menu**, pas par
`count(*)`.

**Aucune des 7 fiches ne casse à l'ouverture sur un enregistrement minimal** : les 7 groupes onLoad
effectifs (vue fusionnée, priorité 21) rendent `status:0`, et les 7 fiches s'ouvrent au navigateur
sans erreur console. `[prouvé]` captures `c3-project-900010.png`, `c3-task-900011.png`,
`c3-tsl-900016.png`, `c3-timesheet-900015.png`, `c3-employee-900013.png`,
`c3-empcontract-900014.png`, `c3-planningtime-900017.png`.

---

## 1. `project_project`

**Domaine filtrant — il n'existe AUCUN menu « tous les projets »**

Les trois seuls menus qui ciblent `Project` filtrent tous les trois :

| Menu | Domaine |
|---|---|
| Affaires (`business.project.all`) | `self.isBusinessProject = true` |
| Chantiers (`construction.root.projects`) | `self.constructionIsConstructionProject = true` |
| Mes chantiers (portefeuille) | `self.assignedTo = :__user__ AND self.constructionIsConstructionProject = true AND self.projectStatus.isCompleted = false` |

> Attention : **Un projet qui n'est ni « affaire » ni « chantier » n'est atteignable par aucun menu.** Ce
> n'est pas une hypothèse : le socle de cette base en contient déjà un (projet 1,
> « 123Service Project », les deux booléens à `false`).
> `[prouvé]` les 3 domaines rendent `total=0` sur le projet minimal ; `total=1` sur
> `self.isBusinessProject = true` après `is_business_project=true`.
> `[prouvé]` `SELECT id,name FROM project_project WHERE COALESCE(is_business_project,false)=false
> AND COALESCE(construction_is_construction_project,false)=false` → 1 ligne dans le socle.

- `project_status` NULL : le kanban projet est `columnBy="projectStatus"`, et plusieurs
  `showIf`/`hideIf` de boutons déréférencent `projectStatus.isCompleted`. `[statique]` — le kanban
  n'a pas été rouvert ici. Le menu « Mes chantiers » ci-dessus, lui, l'exige explicitement au
  domaine : `[prouvé]` `total=0` avec `project_status` NULL.

**Champ requis par la VUE et nullable en base** : `client_partner` (et `name`, déjà NOT NULL).
`[prouvé]` `required` de la vue fusionnée `business-project-form`.

**`manage_time_spent` — le booléen qui commande un autre écran**

`manage_time_spent = true` sur le projet est ce qui fait entrer ses lignes de temps dans le menu
« Temps passé » (détail §6). C'est la seule colonne de `Project` dont l'effet est **hors de sa propre
fiche**. `[prouvé]`

**namecolumn — `full_name` est dérivé par une FORMULE GROOVY PARAMÉTRABLE**

`ProjectManagementRepository.save()` appelle `ProjectNameComputeServiceImpl.setProjectFullName()`,
qui évalue `AppProject.fullNameGroovyFormula` — avec repli sur `code + "-" + name` si elle est vide.
**Le format réel dépend donc de la base**, il ne se déduit pas des sources.

```
[prouvé] SELECT full_name_groovy_formula FROM studio_app_project;  ->  code + " - " + name
[prouvé] save moteur -> full_name = 'ZSC3P - ZZ Stress C3 Projet'  (SQL avait écrit 'ZZ Stress C3 Projet')
```

> Attention : Le socle de cette base est **déjà incohérent** sur ce point : les projets 2 et 3 portent
> `SSK1-SASAKI...` (sans espaces, format du seed) et le projet 1 `123SP - 123Service Project`
> (format de la formule courante). Écrire `full_name` à la main aligné sur un échantillon pris au
> hasard produit un troisième format. **Lire la formule, l'appliquer.**
> `[prouvé]` `SELECT id,code,name,full_name FROM project_project`.
>
> Attention : Et `full_name` **reste périmé** après un `UPDATE` SQL du `code` ou du `name` jusqu'au prochain
> save moteur (piège 70/92, ici confirmé sur 9.1.6) : `[prouvé]` après `UPDATE ... SET code=NULL`,
> `full_name` valait toujours `ZSC3P - ZZ Stress C3 Projet`. Le save cascade en plus vers les
> **sous-projets** (`child.setFullName(...)`), ce que le SQL ne fait pas.

**`code` NULL : la sauvegarde ne casse pas, le moteur CONSOMME LA SÉQUENCE** `[prouvé]` — corrige un `[statique]`

L'analyse statique concluait qu'avec `code` NULL le Groovy `code.plus("-")` levait et que « la
sauvegarde du projet depuis l'UI échoue purement et simplement ». **C'est faux sur 9.1.6.** Test sur
un projet inséré en SQL avec `code` NULL et jamais chargé par l'application avant le save :

```
[prouvé] INSERT SQL (code NULL) -> save REST, 1er chargement de l'entité -> status:0
         en base : version=2, code='PRJ00001', full_name='PRJ00001 - ZZ Projet code NULL'
```

Le repository **attribue le code depuis la séquence AOS `project`** avant de calculer `full_name`.
Deux conséquences pour la production de données :

1. Un projet SQL sans `code` n'est pas cassé, mais son code sera **imprévisible** (le prochain de la
   séquence) et sans rapport avec la convention du jeu de démo. Poser `code` en SQL.
2. **Ce premier save laisse des traces hors de `project_project`** : il a créé une ligne
   `base_sequence_version` (séquence 1 = `project`, `next_num=2`) **et** une ligne
   `base_reserved_sequence` (`caller_class='com.axelor.apps.project.db.Project'`,
   `caller_field='code'`, `generated_sequence='PRJ00001'`). Un nettoyage qui ne vise que la table
   métier les laisse derrière lui — et `base_reserved_sequence` porte une FK vers
   `base_sequence_version`, donc l'ordre de suppression compte. `[prouvé]` le `DELETE` de la version
   seule échoue sur `fk_jnvqd7i5q0rki8q5xcfsol8hp`.

**À laisser au moteur** : `next_project_task_sequence` (`default="1"`, compteur interne de
numérotation des tâches) `[statique]` ; les totaux et ratios d'avancement —
`action-project-method-compute-project-totals` les recalcule et **le dit** quand la matière manque :
`[prouvé]` `notify: "Aucune tâche de ce projet ne comporte d'estimation de temps ; tous les ratios
d'avancement et de consommation ont été fixés à 0."` C'est le message qu'un jury de démo verra si
les tâches n'ont pas de temps estimé.

## 2. `project_project_task`

**Casse à NULL / domaine filtrant — `type_select` et `status` excluent des menus entiers**

Sur les 7 menus qui ciblent `ProjectTask`, la tâche minimale n'apparaissait que dans **un seul**
(`project.task.customer.new`, sans domaine). `[prouvé]`

| Prédicat | Colonne | Effet du NULL |
|---|---|---|
| `self.typeSelect = :_typeSelect` (6 menus sur 7) | `type_select` | NULL → absente des menus Tâches **et** Tickets. `[prouvé]` `total=0` à NULL, `total=1` après `type_select='task'`. Valeurs valides : `task`, `ticket` — **pas** de valeur numérique |
| `self.project.isBusinessProject = true` | *sur le PARENT* | une tâche d'un projet non-affaire est absente du menu Tâches d'affaire, quoi que porte la tâche. `[prouvé]` |
| `self.status.isCompleted = false` (4 menus) | `status` (FK) | NULL → absente des menus « ouvertes » **et** « traitées ». `[prouvé]` `total=0` avec `status` NULL, `total=1` après pose d'un `project_task_status` à `is_completed=false` |
| `self.isPrivate = false` (5 menus) | `is_private` | NULL exclu (piège 76) |
| `self.assignment = 1` / `= 2` | `assignment` | NULL → absente des deux menus « traitée par le client / par le prestataire » |

**Champs requis par la VUE et nullables en base** : `assigned_to`, `project`, `task_date`.
`[prouvé]` `required` de `business-project-task-form` — aucun des trois n'est NOT NULL en base.

**namecolumn — `full_name` au format `#<id> <name>`** `[prouvé]`

```
[prouvé] SQL avait écrit full_name='ZZ Stress C3 Tache' ; après save moteur :
         full_name = '#900011 ZZ Stress C3 Tache'
```

Le format exige l'`id`, donc il ne se calcule qu'après l'insertion : un INSERT SQL doit poser
`'#' || id || ' ' || name` lui-même (ou faire une passe d'UPDATE juste après), sinon toutes les
tâches SQL s'affichent autrement que celles créées par l'interface — l'écart se voit au premier
coup d'œil dans une liste mixte.

**À laisser au moteur** : les valorisations financières. `action-project-task-method-compute` rend
`companyExTaxTotal`, `discountAmount`, `discountTypeSelect`, `exTaxTotal`, `priceDiscounted`,
`totalCosts` `[prouvé]` ; l'onLoad chantier rend `constructionEngagedAmount`,
`constructionRafAmount`, `constructionTimeAdjustmentAmount` `[prouvé]`.

**Kanbans** : trois kanbans différents par `columnBy` (`status`, `projectTaskCategory`,
`activeSprint`) ; une colonne pilote NULL retire la tâche de toutes les colonnes du kanban concerné.
`[statique]` — non reproduit ici. À noter que dans cette base `active_sprint` est à 0 % de
remplissage : **toutes** les tâches sont absentes du kanban par sprint.

## 3. `hr_employee`

**Casse à NULL — `step_by_step_select` : la fiche est réduite à son assistant d'accueil** `[prouvé]`

C'est le constat le plus visible en démo, et il est invisible au schéma.

```
[prouvé] step_by_step_select NULL -> panneau actif :
  « Informations de base | Contrat de travail +2 | ... Responsable RH Externe Email Site Web
    Téléphone N° Mobile »   (capture c3-employee-900013.png)
[prouvé] après step_by_step_select = 5 -> panneau actif :
  « Informations personnelles : Date de naissance, Statut marital, Sexe, Pays de naissance,
    Nationalité, Enfants à charge, Numéro sécurité sociale, Contact en cas d'urgence… |
    onglets Contrats de travail / Compteurs de congés / Feuilles de temps / Avantages et notes de
    frais / Formations / Fichiers | Informations contractuelles : Date d'embauche, Date
    d'ancienneté, Date de départ… »   (capture c3-employee-900013-step5.png)
```

Confirme sur 9.1.6 l'exigence déjà notée dans `entites-tiers-contacts.md` (§6.bis) : `step_by_step_select = 5`
n'est pas un détail cosmétique, c'est ce qui rend la fiche employé montrable.

- `main_employment_contract` NULL → NPE dans **au moins 7 services**, dont la résolution de la
  société active à la connexion (`UserHrServiceImpl.setActiveCompany`). `[statique]` — dans cette
  base 20 employés sur 21 le portent ; le contrat de travail n'est pas optionnel en pratique.

**Domaine filtrant** : néant — `employee.all` n'a aucun `domain`. `[prouvé]` `total=1` sur
l'employé minimal. C'est la seule table du domaine dont la visibilité ne dépend de rien.

**namecolumn — il n'y en a pas sur `Employee`**

La grille et la fiche employé s'affichent et se trient **via `contactPartner.simpleFullName` /
`contactPartner.fullName`**. Un `base_partner` lié dont le `full_name`/`simple_full_name` est NULL
donne une ligne employé **sans nom** dans son propre module RH. `[statique]` — chaîne à trois
niveaux, à croiser avec `entites-tiers-contacts.md`.
`[prouvé]` que la colonne `hr_employee.name` existe et vaut ce que le SQL y écrit (`ZZ STRESS C3
CONTACT`), mais ce n'est pas elle que la vue affiche.

**À laisser au moteur** : `lunch_voucher_distribution` (`default="100"`). `[statique]`

## 4. `hr_employment_contract`

- **Casse à NULL / valeur hors domaine — `status`.** La sélection `hr.employment.contract.status`
  ne définit que `1` En essai, `2` Actif, `3` Fermé. `[prouvé]` avec `status` NULL, le badge de
  statut de la fiche affiche les trois libellés « En essai / Actif / Fermé » sans aucun sélectionné
  (capture `c3-empcontract-900014.png`). `[statique]` que la valeur `0` — portée par **les 20 lignes
  du socle** de cette base — est également hors sélection ; c'est un défaut du socle, à ne pas
  recopier (règle 4).
- **Domaine filtrant** : néant, `employment.contracts.all` n'a aucun `domain`. `[prouvé]` `total=1`.
- **namecolumn** : `full_name` est un champ fonction (corps CDATA) concaténant
  `contractType.name` + `employee.name` + `startDate` + `endDate` ; à NULL, le contrat est
  introuvable en m2o. `[statique]`. `[prouvé]` qu'un INSERT SQL conserve exactement la valeur écrite
  (`ZZ Stress C3 Contrat`) — aucun recalcul spontané. Le format du socle est
  `T0049 - MARQUES Yoann`, donc dépendant en cascade du nom du tiers de l'employé.
- **À laisser au moteur** : `employment_contract_version` (`default="0"` ; le panneau
  `amendmentDetailsPanel` est en `showIf="employmentContractVersion > 0"`). `[statique]`

## 5. `hr_timesheet`

**Un seul menu, et il filtre sur l'UTILISATEUR de l'employé** `[prouvé]` — corrige un `[statique]`

L'analyse statique concluait « aucun menu autonome filtrant par valeur exacte n'a été trouvé …
pas de piège d'exclusion identifié ici ». Il y en a un, et il est sévère :

```
action.timesheet.view.my.timesheet  ->  domain: self.employee.user.id = :user_id
                                        context: user_id = eval:__user__.id
```

Le filtre ne porte ni sur `status_select` ni sur aucune colonne de `hr_timesheet` : il exige que
l'employé de la feuille soit **relié à un `auth_user`** (relation portée par `auth_user.employee`, il
n'y a pas de colonne `user` sur `hr_employee`), et que ce soit l'utilisateur courant.

```
[prouvé] /ws/action -> domain 'self.employee.user.id = :user_id', context {user_id: 1}
[prouvé] feuille 900015, employé 900013 sans auth_user lié : total=0
         même recherche sans le prédicat user                : total=1  (la ligne existe bien)
         témoin positif, feuilles de l'employé d'admin        : total=3  (ids 1,2,3)
```

**Ce que ça impose à un jeu de démo** : les feuilles de temps ne sont montrables que sous le compte
de l'utilisateur qui les porte, et **seulement si l'employé a un `auth_user`**. Dans cette base les
21 employés en ont un — ne pas généraliser ce confort à un jeu créé en SQL.
Attention : Ne pas créer d'`auth_user` à la légère pour contourner : les comptes actifs sont plafonnés par la
licence Guardian (dépassement = code 1021 au login, carte des sièges construite **au boot**).

- **Casse à NULL** : `status_select` est nullable malgré son `default="1"` et son `readonly` — mais
  aucun menu ne le filtre. `[prouvé]` (le domaine ci-dessus ne le mentionne pas). Poser `1`.
- **namecolumn — `full_name`, recalculé au save, chaîne à trois niveaux** `[prouvé]`

```
[prouvé] SQL avait écrit 'ZZ Stress C3 Feuille' ; après save moteur (fromDate/toDate posés) :
         full_name = 'ZZ STRESS C3 CONTACT 15/06/2026-21/06/2026'
         format du socle : 'T0067 - Admin 17/08/2026-24/08/2026'
```

Soit `<employee.name> <du>-<au>` — et `employee.name` dérive lui-même de `contactPartner`
(§3). Trois maillons : `Timesheet.fullName` → `Employee.getName()` → `Partner.fullName`. N'importe
lequel à NULL dégrade le libellé.

- **À laisser au moteur** : `period_total` (total calculé, pas une recopie) `[statique]` ; l'éditeur
  de saisie. Attention : **Ne pas confondre la fiche et l'éditeur** : la fiche `timesheet-form` s'ouvre sans
  incident ici avec `show_editor=false` (capture `c3-timesheet-900015.png`, le panneau « Lignes de
  feuille de temps » et « Totaux sur la période » se rendent normalement). Cela **ne dit rien** de
  l'endpoint EE `GET /ws/aos/timesheet` documenté comme cassé sous hibernate 6.6.53 avec
  `studio_app_timesheet.is_show_all_tasks_assigned = true` : je ne l'ai pas exercé, la question
  reste ouverte sur cette pile.

## 6. `hr_timesheet_line`

**Il y a bien un menu, et son filtre est indirect à DEUX niveaux** `[prouvé]` — corrige un `[statique]`

L'analyse statique concluait « pas de filtre de menu direct trouvé sur `TimesheetLine` (les lignes
se consultent via l'éditeur imbriqué dans `Timesheet`) ». Il existe un menu autonome, « Temps
passé » :

```
project.spent.time  ->  domain: self.project.id IN :_projectIds
    context: _projectIds = call:TimesheetContextProjectService:getActiveProjectIds()
```

Et `getActiveProjectIds()` (source AOS 9.1.6, `TimesheetContextProjectServiceImpl`) ne retourne pas
« tous les projets » : si l'utilisateur n'a pas de projet actif, c'est
`projectRepository.all().filter("self.manageTimeSpent = true")` — plus leurs sous-projets.

```
[prouvé] /ws/action sur project.spent.time -> context {_projectIds: [1, 2, 3]}
         après UPDATE project_project SET manage_time_spent=true WHERE id=900010
                                          -> context {_projectIds: [1, 2, 3, 900010]}
[prouvé] ligne 900016, project NULL           -> total=0
         après project=900010                 -> total=1
```

**Deux items UI-critical prouvés, tous les deux hors de la table** :

1. **`project` NULL ⇒ la ligne de temps n'est dans aucun écran « temps passé ».** Le socle de cette
   base en porte déjà **3 sur 16**. `[prouvé]`
   `SELECT count(*) FILTER (WHERE project IS NULL), count(*) FROM hr_timesheet_line` → `3|16`.
2. **`manage_time_spent = false` sur le projet ⇒ toutes ses lignes de temps sont invisibles**, même
   avec `project` renseigné. C'est le booléen à ne pas oublier quand on peuple un projet dont on
   veut montrer les temps. `[prouvé]`

- **Casse à NULL** : `timesheet` — `TimesheetLineComputeNameServiceImpl` déréférence
  `timesheetLine.getTimesheet().getFullName()` sans garde au save. `[statique]`
- **namecolumn — `full_name` : le socle le laisse NULL, et personne ne le remplit.** `[prouvé]`
  `SELECT full_name FROM hr_timesheet_line WHERE id IN (1, 900016)` → `<NULL>` **sur les deux**, y
  compris sur la ligne du socle. Le champ domaine est vide (`<string name="fullName"
  namecolumn="true"></string>`), le calcul vit dans un service appelé au save et exige l'`id`.
  Conséquence : les lignes de temps s'affichent par `#<id>` dans les sélecteurs, partout, y compris
  dans le socle AOS. **Ne pas le traiter comme une anomalie à corriger** ; si un sélecteur de ligne
  de temps doit être lisible dans une démo, il faut poser `full_name` explicitement (format
  `<timesheet.full_name> <date> <id>`), sinon s'abstenir — mais ne pas s'en inquiéter.
- **À laisser au moteur** : `duration`. `action-timesheet-line-method-compute-duration-onchange`
  rend `values: duration` `[prouvé]` ; et rappel de `methode-dates.md` :
  `spentTime` / `totalRealHrs` ne sont pas fiables.
- Attention : La fiche s'ouvre proprement sur la ligne minimale et affiche « Projet ZSC3P - ZZ Stress C3
  Projet », « Employé ZZ STRESS C3 CONTACT », Durée vide. `[prouvé]` capture `c3-tsl-900016.png`.

## 7. `project_project_planning_time`

- **Casse à NULL** : néant au-delà du schéma — `employee`, `project`, `start_date_time`,
  `end_date_time`, `time_unit` sont **tous les cinq** NOT NULL. `[prouvé]` la fiche minimale s'ouvre
  complète (capture `c3-planningtime-900017.png`).
- **Champ requis par la VUE et nullable en base** : `product`. `[prouvé]` `required` de
  `project-planning-time-form` (extension project-pro). Le plan de charge exige donc une
  **activité** que le schéma ne réclame pas.
- **Domaine filtrant** : néant — `project.project.planning.time` n'a aucun `domain`. `[prouvé]`
  `total=1`. C'est, avec l'employé et le contrat, la troisième table du domaine sans filtre de menu.
- **namecolumn — `full_name` au format `<employee.name>-<project.code>-<start_date>`** `[prouvé]`

```
[prouvé] SQL n'avait rien écrit ; après save moteur :
         full_name = 'ZZ STRESS C3 CONTACT-ZSC3P-16/06/2026'
         format du socle : 'T0067 - Admin-SSK1-01/09/2026'
```

Noter la dépendance à `project.code` : un projet sans `code` (§1) donne un libellé de plan de charge
amputé.

- **À laisser au moteur** : `display_planned_time`, `display_time_unit`, `daily_planned_time` — les
  services testent `if (getDisplayTimeUnit() == null)` et reconvertissent depuis
  `planned_time`/`time_unit` à l'ouverture. `[statique]`, corroboré : `[prouvé]`
  `action-project-planning-time-method-compute-planned-time` rend `dailyPlannedTime`,
  `dailyPlannedTimeOption`, `displayPlannedTime`, `displayPlannedTimeRestricted`, `displayTimeUnit`.
  Les laisser NULL en SQL est **sans risque**.

---

## Générer et alimenter une affaire — mesures du 2026-09-22

> `[prouvé REST 9.1.3 / AOP 8.2.2]` sur une passe de **25 affaires** générées depuis des commandes de
> vente, dans une base portant 361 lignes de vente, 272 lignes d'achat et 250 ordres de fabrication.

### 137. Générer une affaire depuis une commande exige deux clés de contexte non documentées

`action-business-project-method-generate-project` répond
`{"error":{"message":"Name is null"}}` — **message trompeur, le nom n'est pas en cause** — tant que le
contexte ne porte pas ces deux clés, qu'aucun écran ne montre :

| Clé | Valeur |
|---|---|
| `_projectGeneratorType` | énumération `com.axelor.apps.project.db.ProjectGeneratorType` : **`PROJECT_ALONE`**, **`SUB_PROJECT_BY_LINE`**, **`TASK_BY_LINE`**, **`TASK_TEMPLATE`** |
| `_elementStartDate` | format **`YYYY-MM-DDTHH:MM:SS.000Z`**, exactement |

Attention : Le format de date est strict : `...T08:00:00` seul lève
`Text '...' could not be parsed at index 19`. L'erreur pointe la position 19, pas le champ.

**Et le code de l'affaire dépend d'un drapeau d'app** : `studio_app_project.generate_project_sequence`
doit valoir **vrai**, sinon le code reste **vide**. À vrai, il vient de la séquence (`PRJ00001`).
Même séquence que celle décrite en §1 pour un projet SQL sans `code` — avec la même conséquence :
`base_sequence_version` et `base_reserved_sequence` reçoivent des lignes, à compter dans le périmètre
de nettoyage.

### 138. Les indicateurs d'affaire lisent zéro tant que les QUATRE liens de rattachement ne sont pas posés — et aucun ne l'est tout seul

Une affaire générée par le moteur naît **sans aucune des liaisons** que ses indicateurs lisent. Les
quatre ont été mesurés absents après génération, et les quatre sont nécessaires :

| Ce qu'on veut montrer | Ce qu'il faut poser | Constat après génération |
|---|---|---|
| Le **vendu** | `sale_sale_order_line.project` | **11 lignes sur 361** |
| L'**engagé** | `purchase_purchase_order_line.project` | **0 sur 272** |
| Le **coût de production** | `production_production_order.project` **et** la jonction `production_manuf_order_production_order_set` | table `production_production_order` **entièrement vide** |
| La **traçabilité pièce à pièce** | `production_manuf_order.sale_order_line` et `production_manuf_order_sale_order_set` | absent |

Attention : **Rattacher la commande à l'affaire ne suffit pas : ce sont les LIGNES qui portent le lien.**
C'est la même leçon que la frontière déjà documentée en `entites-achats.md` §1 et §7 — les dashlets
« Expense budget » et « Supplier purchase flow » lisent bien l'en-tête
(`purchase_purchase_order.project`), mais « Expenditure Synthesis » et le calcul du RAF passent par la
**ligne**. Une affaire rattachée par les seuls en-têtes a des tuiles pleines et un tableau ventilé à
zéro : l'écart se voit à l'écran, dans la même page.

*Non mesuré* : lequel de `purchase_purchase_order_line.project` et `purchase_purchase_order_line.project_task`
alimente quel indicateur. La fiche achats documente `project_task` pour D12 et le RAF ; la mesure du
2026-09-22 porte sur `project`. Les deux sont écrits, aucun n'est arbitré contre l'autre.

Voir aussi, côté vente, `sale_sale_order_line.main_sale_order` (`entites-production-btp.md`, « DPGF et
bilan d'affaire ») : une cinquième FK, de même nature, dont l'absence donne un bilan à zéro en silence.

## Temps d'atelier, tâches d'affaire et temps du BE — mesures de la nuit du 23 au 24/09 (démo industrielle, 9.1.3)

### 144. Un pointage d'atelier ne porte PAS l'affaire — et il ne montre son OF que si l'employé est « imputé sur OF »

`[prouvé 9.1.3, source + base]` Le pointage créé depuis un OF (`TimesheetLineBusinessProductionServiceImpl`)
pose `manuf_order` et `operation_order`, **jamais `project`** : les 363 pointages natifs sur OF ont
`project` NULL. Un historique qui posait l'affaire sur ses 128 pointages d'atelier a fait afficher, dans
« Indicateurs projet » (module `axelor-project-reporting`, hors standard AOS), **« budget de temps
dépassé » de 151 à 207 %** (le temps d'atelier comparé au temps d'étude vendu) et une ligne
« Main-d'œuvre 0,00 € ».

Et la feuille de temps n'affiche la grille OF / opération que si `AppProduction.enableTimesheetOnManufOrder`
**et** `employee.timesheetImputationSelect = 2` (business-production, `Timesheet.xml` l.19-27 ;
1 = imputé sur projet, 2 = imputé sur OF). Pointeurs laissés à 1 : la feuille montre des lignes sans OF
ni opération, alors que la base les porte.

**À faire :** pointage d'atelier = OF + opération, `project` NULL ; pointeurs d'atelier
`timesheet_imputation_select = 2` ; ouvrir une feuille à l'écran avant de conclure. Changer
l'imputation d'un employé change l'affichage de **toutes** ses feuilles : compter d'abord ses lignes
sur affaire (sur la démo : 30 sur 301, sans OF, qui perdent leur colonne affaire). **Garde :** G7 (pointage sur
OF portant une affaire), 128 → 0 après correction — à cliquet : elle ne mord que si l'audit a tourné
avant l'écriture (piège 143).

### 145. Une affaire issue d'une commande a des tâches et un jeu de statuts de tâche — seedée sans eux, l'onglet Tâches est vide

`[prouvé 9.1.3]` Les 10 affaires de l'historique n'avaient **aucune tâche** et **aucun lien**
`project_project_project_task_status_set` ; les 26 autres affaires non archivées
(`task_status_management_select = 2`) en ont 6 chacune. Onglet « Tâches » vide, aucun temps d'étude,
sélecteur de statut de tâche vide.

**Forme d'une tâche générée par AOS depuis une ligne de service** (modèle : tâche native d'une affaire
générée) : `name` = « SOxxxx - <séquence de la ligne> - <article> » ; `full_name` = « #id nom »
(`ProjectTaskProjectRepository.save`) ; `sale_order_line`, `product` ; `quantity` = `sold_time` =
`updated_time` = quantité vendue ; `unit_price`, `unit_cost` ; `invoicing_type` 3,
`theoretical_turnover_type` 3, `type_select` 'task', `level_indicator` '1' ; `priority` « Normal » ;
`time_unit` et `invoicing_unit` = unité de la ligne ; `imputable` true, tous les autres booléens false ;
totaux calculés à 0 tant que le calcul de l'affaire n'a pas tourné (comme les natives).

**Deux pièges liés.** (1) La fin d'affaire (`to_date`) valait la date d'expédition : la mise en service
tombait après, dimension 11 F6 à 10 violations — reporter la fin à celle de la dernière tâche. (2) Une
tâche « Terminé » a sa date « Réalisé le » (`completed_on`, F5f).

**À faire :** seeder l'affaire avec ses tâches (forme ci-dessus) et ses liens de statut de tâche ;
fin d'affaire = fin de la dernière tâche ; `completed_on` sur toute tâche « Terminé ». **Garde :** G9
(affaire gérée par projet sans statuts de tâche), 10 → 0 — à cliquet (piège 143).

### 146. Le coût d'un pointage n'existe qu'après le calcul de l'affaire — et les indicateurs lisent cette colonne

`[prouvé 9.1.3, source]` `TimesheetProjectServiceImpl.setCostDetails` : coût horaire daté de l'employé
(`hr_employee_hourly_cost`), à défaut `hr_employee.hourly_rate`, × heures → `company_ex_tax_cost_total`
et `unit_cost_price`. Il n'est posé **qu'au calcul de l'affaire**, jamais lancé sur une base de démo : un
pointage seedé à coût NULL sort « Main-d'œuvre 0,00 € » dans le déboursé du module
`axelor-project-reporting` (hors standard AOS), qui lit `company_ex_tax_cost_total` (le taux horaire ne
lui sert qu'à signaler un écart). Le même module range le temps passé par **profil = article**
(`tl.product`) : sans article, il tombe en « (aucun profil sur la ligne) » face au temps vendu.

**À faire :** poser le coût avec la même formule que le calcul, ou jouer le calcul par le moteur ; poser
l'article vendu (étude, mise en service) sur le pointage de la tâche. **Garde :** aucune dans
`scripts/audit-completeness.sql`.

### 147. Une tâche sans priorité ne s'enregistre pas depuis l'écran si son projet affiche les priorités — la dimension 5 ne voit pas les champs obligatoires du formulaire

`[prouvé 9.1.3]` Avant-projet BE de la démo industrielle : **61 tâches sans `priority`** (obligatoire au
formulaire quand le projet affiche les priorités : `requiredIf="project.isShowPriority"`,
`ProjectTask.xml` l.267-268, case cochée par défaut, `Project.xml` l.84 ; les 36 affaires non archivées
de la démo l'ont ; nullable en base) ni `time_unit`, et 30 tâches « Terminé » sans `completed_on`. En
consultation tout s'affiche ; au premier enregistrement (statut, pointage), le formulaire bloque. La
dimension 5 ne lit que les NOT NULL du schéma. Référentiel : `project_project_priority` ; 1 Low,
2 Normal, 3 High, 4 Urgent sont les valeurs de `technical_type_select` (`ProjectPriority.xml` l.10),
pas des id — retrouver l'id par ce type (ils coïncident sur cette démo) ; unité = `project_time_unit` du
projet.

**À faire :** poser `priority` et `time_unit` sur toute tâche seedée d'un projet à priorités,
`completed_on` sur toute tâche « Terminé ». **Garde :** G8 (tâche sans priorité), 61 → 0 — à cliquet
(piège 143) ; G8 ne filtre pas sur `is_show_priority`.

### 150. Une affaire seedée sans jeu de priorités de tâche ne s'enregistre PLUS depuis l'écran — poser aussi le jeu de statuts par défaut de l'application

`[prouvé 9.1.x, démo industrielle, 24/09/2026]` `projectTaskPrioritySet` (`project_project_project_task_priority_set`)
est `requiredIf="isShowPriority"` (`incl-project-config-panel-form`, axelor-project et
axelor-project-scheduler 9.1.x) et `is_show_priority` vaut vrai par défaut : une affaire seedée sans ce
jeu affiche les priorités mais bloque au premier enregistrement depuis l'écran, distinct du piège 147
(la priorité individuelle de la tâche). Les 10 affaires de l'historique de la démo n'avaient aucune priorité ;
les 25 affaires natives portent le jeu par défaut de l'application
(`studio_app_project_default_priority_set` : Low, Normal, High, Urgent). Correctif joué sur la séance
par l'API (script du lot).

**Effet du moteur à noter à l'enregistrement d'une affaire** (à anticiper, pas à corriger a
posteriori) : réenregistrer une affaire réenregistre aussi ses lignes de commande d'achat (libellé
complet recalculé) et recalcule les heures planifiées de ses tâches depuis les lignes de planification.

**À faire :** seeder l'affaire avec le jeu de priorités ET le jeu de statuts par défaut de
l'application (en plus des tâches et de leur propre `priority`, piège 147). **Garde :** aucune dans
`scripts/audit-completeness.sql` (G10 à créer : affaire qui affiche les priorités sans jeu de
priorités).

Voir aussi le piège 145 (affaire sans tâches ni jeu de statuts de tâche) et le piège 147 (tâche sans
priorité individuelle).

## Ce que ce protocole n'a PAS couvert

- Les **kanbans** (projet, 3 kanbans de tâches) et les **cards** : mécanisme `columnBy` NULL réel
  mais non reproduit ici.
- Le **Gantt**, le **calendrier** et les **dashlets de reporting projet** : non ouverts.
- L'**éditeur de feuilles de temps** (`/ws/aos/timesheet`) : non exercé, cf. §5.
- Les **permissions** : tout mesuré en `admin`.
- `hr_timesheet.status_select` et la cohérence temporelle feuille / lignes / tâche : c'est le sujet
  de la dimension 11 de `scripts/audit-completeness.sql`, pas de cette fiche. Le socle de cette base
  est connu comme temporellement incohérent (13 pointages antérieurs à leur tâche, mesuré) —
  ne pas le re-signaler comme une découverte.
