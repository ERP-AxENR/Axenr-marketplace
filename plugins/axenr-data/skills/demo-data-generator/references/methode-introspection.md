# Méthode — introspection

**Pièges couverts par cette fiche :**

- 30-bis. Une `meta_select` existante ne garantit PAS la colonne sur cette table
- 31. `meta_field` ne contient ni `selection` ni `name_column` (AOP 8.2)
- 32. Fetcher le TYPE réel : des champs « évidents » sont des VARCHAR
- 33. PostgreSQL tronque tout identifiant à 63 caractères
- 34. Le rattachement d'une ligne n'est pas toujours la FK au nom évident
- 35. Deux référentiels homonymes coexistent
- 36. Une colonne « integer » peut être une FK
- 37. Une FK résolue par sous-requête écrit NULL EN SILENCE
- 41. `base_address` : les champs structurés sont obligatoires
- 43. Ne pas confondre deux entités de noms proches
- 16. `__config__.date` à NULL → NPE à l'ouverture des vues stock (binding de configuration manquant)

Piège 16 rattaché ici : c'est une vérification de binding de configuration, même famille que les ghost columns ci-dessous.

## Avant d'écrire quoi que ce soit

Avant de générer QUELQUE donnée que ce soit, il FAUT :

1. **Lire la spécification** depuis `$ARGUMENTS` (chemin de fichier ou description en ligne)
2. **Identifier la base cible** (voir « Validation de la base cible » ci-dessous) — **ne jamais supposer une base par défaut**
3. **Lister les modules installés** sur cette base (production-pro, business-production, axelor-btp, hr-enterprise, etc.) — ils ajoutent/retirent des colonnes silencieusement et cassent les inserts si ce n'est pas anticipé
4. **Interroger la base de données** pour trouver :
   - Les ID max de chaque table cible (éviter les collisions)
   - Les enregistrements existants réutilisables (éviter les doublons)

## Validation de la base cible (NON NÉGOCIABLE)

Sur les hôtes PostgreSQL Axelor, on trouve typiquement 5 à 15 bases côte à côte (`<base_a>`, `<base_b>`, `<base_c>`, etc.). Elles partagent souvent le même motif de nom de schéma mais diffèrent sur :
- La version AOS (8.5 vs 9.x)
- Les modules installés (présence/absence de `axelor-btp`, `axelor-business-production`, `axelor-production-pro`)
- Les colonnes qui en résultent sur des tables par ailleurs standard (colonnes `btp_*`, `manuf_order` sur `hr_timesheet_line`, `workshop` sur `hr_employee`, etc.)

**Avant tout INSERT/UPDATE, il FAUT identifier quelle base l'application web cible réellement** :

1. Lire `src/main/resources/axelor-config.properties` (ou tout `application.properties` équivalent) pour trouver `db.default.url` — l'URL JDBC indique la base vivante.
2. Si l'utilisateur mentionne une base différente (ex. « on travaille sur `<base>` »), faire confiance à l'utilisateur et **revérifier la disponibilité des colonnes** sur cette base — les schémas divergent.
3. Vérifier l'existence et le `MAX(id)` courant de chaque table à écrire, **sur cette base spécifique**, pas sur une base d'exemple générique.

> **Leçon apprise le 2026-05-28 (sur une démo de services) :** le générateur a écrit par défaut sur une base codée en dur ; l'application web vivante était sur `<base_demo>`. La démo s'est chargée silencieusement sur la mauvaise base ; des dizaines de minutes perdues à nettoyer deux bases polluées. Toujours confirmer la base en lisant le fichier de config.

## Connexion à la base de données

```
psql -h <hôte> -U <utilisateur> -d <DB_NAME>    # mot de passe : PGPASSWORD déjà exporté, ou fichier de mots de passe de psql
```

Hôte, utilisateur et mot de passe se lisent dans `db.default.url`, `db.default.user` et `db.default.password` de
`axelor-config.properties` ; l'hôte n'est pas forcément `localhost` (dans un déploiement Docker, c'est le nom du
service de base de données). Le mot de passe ne se tape jamais dans une commande que Claude exécute (il
finirait dans le transcript) : l'utilisateur l'exporte en `PGPASSWORD` dans son terminal avant de lancer la
session, ou le range dans le fichier de mots de passe de psql (droits 600). **`DB_NAME` n'est pas une constante** — le dériver de
`axelor-config.properties` ou de l'instruction explicite de l'utilisateur.

## Colonnes fantômes dépendantes d'un module

Les schémas varient selon les modules installés. Avant de référencer l'une des colonnes suivantes dans un INSERT, confirmer sa présence via `information_schema.columns` :

| Colonne | Module requis |
|---|---|
| `hr_timesheet_line.manuf_order`, `.operation_order` | `axelor-business-production` |
| `hr_employee.workshop` | `axelor-production-pro` |
| `project_project.is_cost_by_manuf_order` | `axelor-business-production` |
| `production_manuf_order.invoiced`, `.is_to_invoice` | `axelor-business-production` |
| `production_operation_order.is_micro_planning_done`, `.is_pinned`, `.is_to_invoice` | `axelor-production-pro` |
| `*.btp_*` (n'importe quelle table) | `axelor-btp` ET la bonne version (certaines colonnes btp disparaissent d'une version à l'autre, ex. `sale_sale_order.btp_is_vat_reverse_charge`) |
| `project_project.btp_is_btp_project`, `sale_sale_order.btp_*` | `axelor-btp` |

Symptôme d'un décalage : `ERROR: column "X" of relation "Y" does not exist`. Le correctif est **toujours** de retirer la colonne (et sa valeur) de l'INSERT, jamais de l'ajouter en base.

## Chantier ESN — préambule (pièges 30 → 57)

# Pièges vérifiés sur un chantier de peuplement exhaustif (30 → 50)

Ces pièges viennent d'un chantier réel où l'objectif était « aucun écran vide » sur une base ESN
(AOS 9.0.11). Chacun a coûté au moins un aller-retour de correction. Ils complètent les 29 ci-dessus,
qui restent valables.

### 30. Une `meta_select` existante ne garantit PAS la colonne sur cette table
*(anciennement numéroté 30-bis ; renommé le 2026-09-03 : aucune citation externe)*

`account.fixed.asset.technical.type.select` existe bien, mais `technical_type_select` est portée par la
**catégorie d'immobilisation**, pas par l'immobilisation. Voir une sélection ne prouve pas que le champ
est là où on le croit → vérifier dans `information_schema.columns`.

### 31. `meta_field` ne contient ni `selection` ni `name_column` (AOP 8.2)
Ces informations vivent dans le XML du domaine et dans `meta_select`. `meta_field` porte `name`,
`relationship`, `mapped_by`, `type_name` — utile pour énumérer les relations, pas les sélections.

### 32. Fetcher le TYPE réel : des champs « évidents » sont des VARCHAR
`hr_employment_contract.coefficient`, `trial_period_duration`, `employment`, `position`, `duration`
sont des **chaînes** (pas des entiers ni des FK) ; `base_partner.sale_turnover` est un `integer`.
Un `COALESCE(varchar, int)` échoue à l'exécution. Corollaire : un `VALUES` multi-lignes de littéraux
quotés est typé `text` → cast explicite (`v.size::int`) pour alimenter une colonne entière.

### 33. PostgreSQL tronque tout identifiant à 63 caractères
Deux conséquences : lire `pg_sequences` avant d'écrire un `setval` sur une table à nom long ; et
surtout **les tables de jonction M2M sont tronquées** — la convention
`<table_owner>_<champ_snake_case>` ne suffit pas à les retrouver (vérifié : 8 tables à exactement
63 caractères, dont `stock_tracking_number_configuration_profile_profile_field_formu`). Confirmer le
nom réel via `information_schema.tables` avec un `LIKE`, sinon un audit conclut « jonction
introuvable » à tort.

### 34. Le rattachement d'une ligne n'est pas toujours la FK au nom évident
Une ligne de nomenclature se rattache par **`bill_of_material_parent`**, pas par `bill_of_material`
(qui pointe une *sous*-nomenclature). Compter avec la mauvaise FK fait croire à des nomenclatures
vides — un diagnostic faux qui a failli déclencher un enrichissement inutile. **Toujours lire une
ligne existante pour voir quelles colonnes sont réellement peuplées.**

### 35. Deux référentiels homonymes coexistent
`base_source` (provenance CRM) ≠ `talent_talent_source` (provenance recrutement). Une valeur présente
dans l'un est absente de l'autre : « Site carrière » n'existe que côté recrutement.

### 36. Une colonne « integer » peut être une FK
`hr_probation_period.minimum_duration` → `base_duration`. Vérifier `pg_constraint` avant d'injecter
un entier brut.

## Le piège le plus systémique


### 37. Une FK résolue par sous-requête écrit NULL EN SILENCE
`INSERT … (SELECT id FROM base_source WHERE name='libellé faux')` **insère NULL sans erreur** (vérifié
par test). C'est le pattern de résolution portable recommandé, donc le risque est partout : une faute
de frappe, un référentiel homonyme (§35) ou une valeur absente vide le champ.
**Deux parades cumulées** : (a) `AND EXISTS (SELECT 1 FROM <ref> WHERE …)` dans le `WHERE` de l'INSERT,
pour que la ligne soit ignorée plutôt que créée incomplète ; (b) un bloc final qui
`RAISE EXCEPTION` si un champ attendu est NULL. *Vécu : seule la garde a rattrapé un prospect créé
sans provenance, avec rollback intégral.*

### 41. `base_address` : les champs structurés sont obligatoires
Remplir `addressl4`/`addressl6`/`full_name` ne suffit pas : le clone remplit aussi `street_name`,
`zip`, **`city` (FK `base_city`** — créer la ville si absente) et `formatted_full_name` (3 lignes :
rue / CP VILLE / PAYS). Casse = **MAJUSCULES** ; `full_name` est préfixé d'un espace.
`street` (FK) et `country_sub_division` restent NULL (ce dernier ne contient que des codes d'États US).
Le CP de la ville (`base_city.zip`) est souvent NULL dans les clones — dérivable du CP le plus fréquent
de ses adresses, avec un garde-fou de format par pays.

### 43. Ne pas confondre deux entités de noms proches
`PartnerPriceList` (conteneur rattaché au tiers) ≠ `PriceList` (la grille tarifaire), reliées par le
M2M `priceListSet`.

### 16. `__config__.date` à NULL → NPE à l'ouverture des vues stock (binding de configuration manquant)

**Symptôme :** `NullPointerException: Cannot invoke method plusMonths() on null object` sur `__config__.date.plusMonths(2)` (groovy) à l'ouverture de la **liste TrackingNumber** (et de toute vue stock utilisant `__config__.date.plusWeeks/minusMonths`). La vue est de l'AOS standard — les données sont correctes.

**Cause :** `__config__.X` est lié depuis les clés `context.X = <Class>:<method>` de `axelor-config.properties`. Une config dépouillée/clonée qui n'a gardé que `context.app` laisse `__config__.date` non lié → null.

**Correctif (config, nécessite un redémarrage) :** ajouter les bindings AOS standard présents dans tout projet complet :
```
context.date = com.axelor.apps.base.service.DateService:date
context.appLogo = com.axelor.apps.base.service.user.UserService:getUserActiveCompanyLogoLink
```
Toujours comparer (diff) un `axelor-config.properties` dépouillé contre un projet fonctionnel pour repérer les clés `context.*` manquantes.


*(Piège 16 : voir aussi les ghost columns ci-dessus — même classe d'erreur, supposer un binding/une colonne plutôt que le vérifier.)*
