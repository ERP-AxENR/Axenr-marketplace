# Entités — autres (RH, achats, stock)

**Pièges couverts par cette fiche :**

- 12. TrackingNumberConfiguration + Sequence : `full_name` (namecolumn) doit être renseigné
- 83. Configuration de suivi : `purchase_qty_by_tracking` NULL → NPE en réception
- 105. Un utilisateur créé par REST naît BLOQUÉ, et son login répond en HTML
- 110. Comptes utilisateurs créés en SQL : `blocked=false` explicite ne suffit pas — compter les sièges nommés de la licence Guardian

Sections courtes tant qu'elles le restent. Pièges 12 et 83 rattachés ici : 12 = séquence/TNC (stock), 83 = configuration de suivi (stock).

## RH

### hr_employee

Un employé opérationnel (affectable à une feuille de temps / un projet / un OperationOrder) demande plus que la forme minimale — plusieurs colonnes doivent être renseignées, sinon le front affiche silencieusement un assistant / le planificateur s'affiche vide / les calculs de coût rapportent zéro.

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| name | OUI | "Prénom NOM" (respecte la convention `{first_name} {NAME}`). |
| contact_partner | **CRITIQUE** | FK vers `base_partner` où `partner_type_select=2` ET `is_contact=true` ET `is_employee=true`. Mauvaise forme → non sélectionnable dans les sélecteurs Employé. |
| hourly_rate | Recommandé | NUMERIC (€/h) |
| daily_work_hours | Recommandé | NUMERIC, typiquement 7.00 |
| weekly_work_hours | Recommandé | NUMERIC, typiquement 35.00 |
| daily_salary_cost | **CRITIQUE** | NUMERIC. Doit être égal à `hourly_rate * daily_work_hours`. Utilisé par le KPI Coût d'axelor-dashboard-project et par les rapports de coût RH. NULL est traité comme 0 dans les calculs — sous-valorisation silencieuse. |
| weekly_planning | **CRITIQUE** | FK vers `base_weekly_planning`. `1 = Plein temps` est la valeur standard par défaut. Sans elle, les vues du planificateur s'affichent vides pour cet employé. |
| time_logging_preference_select | **CRITIQUE** | Énumération chaîne : `'hours'` (atelier) ou `'days'` (conseil). NULL casse le rendu du formulaire de feuille de temps — la sauvegarde échoue ou les champs de saisie ne s'affichent pas. |
| step_by_step_select | **CRITIQUE** | Étape entière de l'assistant d'accueil. **Toujours poser à `5` (Terminé)** pour un employé de démo « prêt à l'emploi ». Les valeurs 1..4 (1=Infos de base, 2=Contrat, 3=Congés/FdT, 4=Utilisateur, 5=Terminé) gardent l'assistant `stepByStepControlsPanel` visible et **remplacent le formulaire employé complet par un assistant de paramétrage en 4 étapes** dans l'interface. |
| sex_select | Recommandé | `'M'` / `'F'` |
| hire_date | Recommandé | DATE |
| workshop | Recommandé (BTP/industrie) | FK vers `stock_location`. Spécifique à axelor-production-pro. |
| main_employment_contract | Recommandé | FK vers `hr_employment_contract`. À câbler après l'insert (le contrat référence l'employé, donc insérer le contrat d'abord, puis UPDATE l'employé). |
| external | OUI | Booléen, false par défaut |
| hr_manager, is_create_timesheet_automatically, negative_value_leave, profit_sharing_beneficiary, timesheet_reminder | OUI | Booléens, false par défaut |
| import_id, import_origin | Recommandé | Pour un rollback DELETE en masse |
| version | OUI | Mettre à 0 |

### hr_employment_contract

Contrat de travail lié à un employé. Nécessaire si le formulaire employé doit afficher « Contrat OK », et requis en amont des flux de paie / validation de feuille de temps.

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id). Convention : même id que l'employé pour les paires 1:1 (simplifie l'UPDATE de câblage retour). |
| employee | OUI (NOT NULL) | FK vers `hr_employee` |
| contract_type | Recommandé | FK vers `hr_employment_contract_type` (ex. CDI = 1, type propre au secteur créé pour la démo, etc.) |
| pay_company | OUI | FK vers `base_company`, généralement 1 |
| status | Recommandé | `1` = en cours. Les valeurs supérieures représentent un contrat terminé/clôturé. |
| start_date | OUI | DATE |
| weekly_duration | Recommandé | NUMERIC, typiquement 35.00 |
| hourly_gross_salary | Recommandé | NUMERIC (€/h) |
| employment_contract_version | Recommandé | Entier, défaut 1 |
| full_name | **CRITIQUE** | Motif : `"{contract_type_name}-{employee.name}-{YYYY-MM-DD start_date}"`. NULL laisse les listes déroulantes de contrat vides. Idéalement peuplé via un UPDATE post-insert joint sur `hr_employee` :
```sql
UPDATE hr_employment_contract c
SET full_name = ct.name || '-' || e.name || '-' || to_char(c.start_date, 'YYYY-MM-DD')
FROM hr_employee e, hr_employment_contract_type ct
WHERE c.employee = e.id AND c.contract_type = ct.id AND c.full_name IS NULL;
``` |
| import_id, import_origin | Recommandé | Même précaution que pour l'employé |
| version | OUI | Mettre à 0 |


Après l'insertion des contrats : UPDATE `hr_employee.main_employment_contract` pour câbler la référence retour (le panneau Contrat du formulaire employé lit depuis là).

## Stock

### 12. TrackingNumberConfiguration + Sequence : `full_name` (namecolumn) doit être renseigné

`stock_tracking_number_configuration.full_name` et `base_sequence.full_name` sont tous deux `namecolumn="true"`. Laissés à NULL à l'insert → **libellé vide dans chaque sélecteur m2o** (la configuration paraît « manquante »). Renseigner après l'insert :
```sql
UPDATE base_sequence SET full_name = name WHERE code_select LIKE '<prefix>%' AND full_name IS NULL;
UPDATE stock_tracking_number_configuration t SET full_name = t.name || ' / ' || s.name FROM base_sequence s WHERE t.sequence = s.id AND t.full_name IS NULL;
```
(Forme de référence : le TNC cloné a fullName = `"<name> / <sequence.fullName>"`.) Le préfixe de numérotation des lots périssables supporte les tokens `%YY%` (année 2 chiffres) et `%YYYY%` (4 chiffres) — préférer `%YYYY%` pour des numéros de lot lisibles (ex. `ARTHRO-2026-00042`), et relever `base_sequence_version.next_num` au-delà de tout numéro posé manuellement.

### 83. Configuration de suivi : `purchase_qty_by_tracking` NULL → NPE en réception

Piège FONCTIONNEL, pas cosmétique. Une `stock_tracking_number_configuration` avec
`is_purchase_tracking_managed = true`, `generate_purchase_auto_tracking_nbr = true` et
`purchase_qty_by_tracking`/`sequence` à NULL fait planter toute réception d'achat :

```
StockMoveLineServiceImpl:353  BigDecimal qty = config.getPurchaseQtyByTracking();   // NULL
StockMoveLineServiceImpl:402  if (qtyByTracking.compareTo(BigDecimal.ZERO) <= 0)    // NPE
```

La valeur est lue brute et passée sans garde. L'écran natif refuse cet état (séquence obligatoire
si génération automatique) : **une configuration écrite en SQL peut être dans un état que l'UI
n'autorise pas.** Avant de rattacher des produits à une configuration de suivi, la vérifier :

```sql
SELECT id, is_purchase_tracking_managed, generate_purchase_auto_tracking_nbr,
       purchase_qty_by_tracking, sequence FROM stock_tracking_number_configuration;
```

Poser la quantité sur les **trois** axes (achat, vente, production) : n'en corriger qu'un reproduit
le NPE ailleurs. La séquence est lue par sa clé étrangère (`config.getSequence()`), donc la société
portée par la séquence est décorative ici.

### 105. Un utilisateur créé par REST naît BLOQUÉ, et son login répond en HTML

Créer un `com.axelor.auth.db.User` par `POST /ws/rest` rend `status:0` et un id, le mot de passe est bien haché en `$shiro2$argon2id` — et `auth_user.blocked` vaut `true`. La connexion répond alors **HTTP 401 avec une page d'erreur Tomcat en HTML**, pas un corps JSON : un script qui suppose du JSON plante sur la réponse, et le diagnostic part sur le mot de passe alors que le compte est simplement bloqué.

**Correctif de seed** : poser `blocked = false` explicitement à la création (ou par un second appel), et vérifier le compte par un login réel avant de livrer un jeu qui promet plusieurs profils. Utile aussi pour une démo multi-profils : un utilisateur qui n'apparaît nulle part comme « bloqué » à l'écran peut l'être en base.

### 110. Comptes utilisateurs créés en SQL : `blocked=false` explicite ne suffit pas — compter les sièges nommés de la licence Guardian

Prolonge le piège 105 (né sur une création REST) au cas symétrique : un `INSERT INTO auth_user`
direct hérite lui aussi de `blocked` par défaut si la colonne n'est pas posée explicitement.
**Mesuré** (chantier package CRM, `<base>`, 2026-09-07) : 3 des 4 comptes de démo créés en SQL
sont nés avec `blocked=true` (seuls les 2 comptes techniques du socle, `biUser`/`templateUser`,
sont censés l'être) — `AuthUtils.isActive()` (AOP) refuse toute connexion sur `blocked=true` ou
`archived=true`. Corrigé en posant `blocked=false` explicitement sur les 4.

**Mais la correction ne suffit pas toujours.** Une fois `blocked=false` posé et vérifié bit à bit
identique à un compte fonctionnel (mot de passe compris), **3 des 4 comptes restaient incapables de
se connecter** : `catalina.out` donnait la cause réelle,
**licence Guardian EE — code 1021 « No license line found »** (`AppLicenseObservers.preLogin`), un
mécanisme de **sièges nommés**, indépendant du flag `blocked` et hors de portée du SQL. Seul le
compte qui tenait dans le quota de sièges pouvait se connecter et voir des écrans garnis ; les 3
autres restaient fonctionnellement morts malgré une donnée parfaitement conforme.

**Règle de seed** : avant de créer N comptes de démo, **compter les sièges nommés disponibles** sur
la licence Guardian de l'environnement cible (`enterprise_app_license` / logs `catalina.out` au
premier login de test) — poser `blocked=false` est nécessaire mais pas suffisant. Si le quota est
inférieur au nombre de personas promis, arbitrer AVANT de livrer : soit réduire le nombre de
comptes nommés de la démo, soit obtenir un élargissement de licence — jamais découvrir le plafond
en séance.
