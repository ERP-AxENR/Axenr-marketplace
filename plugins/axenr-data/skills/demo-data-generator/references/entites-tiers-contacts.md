# Entités — tiers & contacts

**Pièges couverts par cette fiche :**

- 6. `base_partner` n'a pas de colonne `is_individual` — utiliser `partner_type_select`
- 6.bis. Employee contact_partner — la forme canonique à 4 booléens
- 8. Valeurs par défaut du tiers : s'aligner sur la forme d'un tiers existant, pas seulement sur les champs obligatoires
- 9. Panneaux du tiers vides sur un insert minimal — 4 relations à peupler
- 23. Contacts (individus) : séparer prénom / NOM + civilité + localisation
- 24. `registration_code` du tiers doit être un SIREN/SIRET VALIDE (Luhn) + renseigner les modes de paiement
- 70. Renommer `name` sans recalculer `full_name` = renommage INVISIBLE
- 71. `full_name` à NULL rend l'enregistrement INVISIBLE — pire que le libellé périmé
- 72. La convention d'un contact inclut le PRÉNOM
- 85. Table de couple : renseigner les DEUX côtés
- 123. Un tiers sans ligne `base_partner_company_set` est INVISIBLE dans les sélecteurs client d'un devis et fournisseur d'une commande d'achat
- 87. `MetaFile` par l'API : la réponse porte `data` sous forme de TABLEAU
- 7. Motif d'illustration fournisseur : tiers par défaut + catalogue multi-lignes
- 84. `purchase_supplier_catalog` : la référence est celle du FOURNISSEUR
- 13. Tiers clients : `account_accounting_situation` est obligatoire pour la facturation (prolonge les pièges 8 et 9)
- 42. Événements CRM sur un tiers : trois liaisons à remplir ensemble
- 108. Un contact créé via `main_partner` n'alimente PAS la jonction `base_partner_contact_partner_set` — panneau Contacts vide
- 109. Un domaine `:__user__`/`:_internalUserId` exige une FK utilisateur EXPLICITEMENT posée, sur CHAQUE tiers

Pièges 7, 13, 42, 84 rattachés ici : 7↔84 forment la paire fournisseur/catalogue ; 13 est la suite directe de 8/9 ; 42 est un fait d'entité (Event/Partner) sans fiche CRM dédiée à ce stade.

## Couche satellite du tiers (base_address, emails, company_set)

### base_address

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | Utiliser la séquence ou un ID explicite > max(id) |
| country | OUI (NOT NULL) | FK vers base_country. France = 3 |
| street_name | NON mais recommandé | Texte libre |
| zip | NON mais recommandé | Code postal en chaîne |
| full_name | NON | Recalculé automatiquement par Axelor, mais le renseigner par clarté |
| city | NON en base, **OUI à l'écran** | FK vers `base_city`. Le SQL accepte NULL mais toute sauvegarde UI de l'adresse échoue ensuite (`AxelorException : Champ de l'adresse manquant : city`) : les champs requis sont lus **par pays** dans `base_address_template_line` (France = city, street_name, zip). Créer la `base_city` si elle manque, ne jamais laisser NULL. *(prouvé 9.1.6 / EE 8.2.3, stress-test 2026-09-03 ; corrige l'ancienne consigne « laisser NULL si absent »)* |
| version | OUI | Mettre à 0 |

### base_partner

Colonnes booléennes réelles disponibles sur base_partner (vérifiées via information_schema) :
`is_already_convert_from_lead`, `is_carrier`, `is_compensation`, `is_contact`, `is_corporate_partner`, `is_customer`, `is_do_not_call`, `is_do_not_email`, `is_employee`, `is_factor`, `is_internal`, `is_ispm_required`, `is_key_account`, `is_main_contact`, `is_needing_conformity_certificate`, `is_nurturing`, `is_partner`, `is_prospect`, `is_subcontractor`, `is_supplier`, `is_third_party_payer`.

**Pas de `is_individual`** — utiliser `partner_type_select = 2` (Individu) vs `1` (Société). La sélection officielle AOS `partner.partner.type.select` n'a **que deux valeurs valides** : `1 = Société`, `2 = Individu`. Écrire `0` constitue une **métadonnée invalide** (aucun item de sélection correspondant) et casse silencieusement les listes déroulantes Employé/Contact ainsi que les filtres de recherche. Écrire `is_individual` lève `column does not exist`.

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| name | OUI (NOT NULL) | Nom de la société ou de la personne |
| partner_type_select | **CRITIQUE** | **1 = Société**, **2 = Individu** (selon `partner.partner.type.select`). NE JAMAIS écrire `0` — métadonnée invalide, casse silencieusement les listes déroulantes Employé/Contact. |
| is_customer | Recommandé | Booléen, false par défaut |
| is_supplier | Recommandé | Booléen, false par défaut |
| is_subcontractor | Recommandé | Booléen, false par défaut |
| is_contact | Recommandé | Booléen, false par défaut. **Doit être `true` pour le `contact_partner` d'un employé** (voir hr_employee). |
| is_employee | Recommandé | Booléen, false par défaut. **Doit être `true` pour le `contact_partner` d'un employé**. |
| is_prospect | Recommandé | Booléen, false par défaut |
| is_internal | Recommandé | Booléen, false par défaut — marque les enregistrements de société interne type AXELOR |
| currency | Recommandé | FK vers base_currency. EUR = 46 |
| payment_condition | Recommandé | FK vers account_payment_condition. « 30j fin de mois » = 6 |
| in_payment_mode | Recommandé | FK vers account_payment_mode. Enc. Chèque = 6, Enc. Virement = 8 |
| out_payment_mode | Recommandé | FK vers account_payment_mode. Dec. Chèque = 14, Dec. Virement = 15 |
| main_address | NON | FK vers base_address. À renseigner après création de l'adresse + partner_address |
| partner_seq | Recommandé | Format "T" + numéro zéro-paddé (ex. T0100). Utiliser une plage haute type T9001+ pour les fournisseurs de démo, afin d'éviter toute collision avec un partner_seq existant. |
| full_name | Recommandé | Identique à name pour les sociétés |
| version | OUI | Mettre à 0 |
| import_id | Recommandé | Utiliser la plage 200000+ pour les données de démo |

### base_partner_address

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| address | OUI (NOT NULL) | FK vers base_address |
| partner | NON mais standard | FK vers base_partner |
| is_default_addr | Recommandé | Booléen, true pour l'adresse principale |
| is_invoicing_addr | Recommandé | Booléen |
| is_delivery_addr | Recommandé | Booléen |
| version | OUI | Mettre à 0 |

### message_email_address

Entité e-mail référencée par `base_partner.email_address` (FK vers son id) et les FK e-mail similaires à travers AOS.

| Colonne | Obligatoire | Notes |
|---|---|---|
| id | OUI | ID explicite > max(id) |
| address | OUI | La chaîne e-mail elle-même, ex. `contact@company.fr` |
| name | Recommandé | Libellé d'affichage, convention : `"<partner_seq> - <partner_name> [<address>]"` |
| version | OUI | Mettre à 0 |

Après avoir créé la ligne e-mail, **UPDATE base_partner SET email_address = \<cet_id\>** — sinon le panneau « Coordonnées générales » reste vide.

### base_partner_company_set

Table de jonction M2M reliant `base_partner` à `base_company`. **Pas d'id de substitution** — c'est une paire pure (base_partner, company_set).

| Colonne | Obligatoire | Notes |
|---|---|---|
| base_partner | OUI | FK vers base_partner.id |
| company_set | OUI | FK vers base_company.id (typiquement 1 = AXE) |

Sans au moins une ligne ici, le panneau `companySet` du formulaire tiers est vide. Toujours insérer une paire après création d'un tiers.

### 6. `base_partner` n'a pas de colonne `is_individual` — utiliser `partner_type_select`

Tenter un INSERT sur `is_individual` échoue avec `column does not exist`. La distinction individu vs société est portée par `partner_type_select` (**2 = Individu**, **1 = Société**). Écrire `0` est une métadonnée invalide (la sélection AOS `partner.partner.type.select` n'a que les valeurs 1 et 2) — les listes déroulantes Employé/Contact excluent silencieusement ces lignes. Voir la liste des colonnes booléennes en tête de la référence `base_partner` ci-dessus.

### 6.bis Employee contact_partner — la forme canonique à 4 booléens

Un `base_partner` utilisé comme `hr_employee.contact_partner` doit combiner :
- `partner_type_select = 2` (Individu)
- `is_contact = true`
- `is_employee = true`
- `full_name = "{partner_seq} - {first_name} {NAME}"` (respecte la convention de démo AOS « T0049 - MARQUES Yoann »)

Un employé de démo dont le `contact_partner` viole l'une de ces règles (en particulier `partner_type_select=0` ou `is_contact=false`) est **exclu silencieusement** du sélecteur Employé dans les feuilles de temps, l'affectation projet et les formulaires de planification. Aucune erreur n'est levée — la ligne n'apparaît simplement pas dans les listes déroulantes.

À associer à l'exigence `hr_employee.step_by_step_select = 5` : un tiers à la bonne forme à 4 booléens mais un employé à `step_by_step_select<5` masquera quand même le formulaire employé complet derrière le panneau assistant d'accueil (`stepByStepControlsPanel`).

### 7. Motif d'illustration fournisseur : tiers par défaut + catalogue multi-lignes

Pour illustrer le **multi-fournisseur** et le **multi-prix par conditionnement/niveau de service** sur un produit de démo :

1. **Fournisseur par défaut** sur le produit : `UPDATE base_product SET default_supplier_partner = <partner_id>` — donne une expérience d'achat en 1 clic.
2. **Multi-fournisseur** : créer 2+ lignes `purchase_supplier_catalog` avec le même `product` mais des `supplier_partner` différents (un fournisseur marque propre + un généraliste déjà existant en base forme une paire convaincante).
3. **Multi-conditionnement** : au sein de chaque paire `(product, supplier)`, créer 2-3 lignes avec des suffixes `product_supplier_name` distincts — « Enlèvement magasin » / « Livré chantier » / « Livré + déchargé chantier ». Faire varier `price` (+10 % / +20 %), `supplier_delivery_time` (0 / 3 / 5 j) et `min_qty` en conséquence.
4. **Aucune contrainte d'unicité sur `(product, supplier_partner)`** — plusieurs lignes de catalogue par paire sont légales et attendues pour ce motif.

### 8. Valeurs par défaut du tiers : s'aligner sur la forme d'un tiers existant, pas seulement sur les champs obligatoires

Un `INSERT` minimal dans `base_partner` avec seulement `name / is_supplier / currency / partner_type_select / payment_condition / in_payment_mode / out_payment_mode` laisse ~18 booléens et ~13 valeurs numériques/select par défaut à NULL. Le formulaire tiers d'AOS et les écrans liés (commande client, facture, comptabilité) lisent bon nombre de ces champs et peuvent lever une NPE ou s'afficher de façon incohérente sur NULL.

**Forme de référence** (relevée sur le tiers existant MASSON SA, id=8) :

| Champ | Valeur par défaut |
|---|---|
| `simple_full_name` | identique à `name` |
| `is_already_convert_from_lead`, `is_carrier`, `is_compensation`, `is_corporate_partner`, `is_do_not_call`, `is_do_not_email`, `is_factor`, `is_ispm_required`, `is_key_account`, `is_main_contact`, `is_needing_conformity_certificate`, `is_nurturing`, `is_partner`, `is_third_party_payer`, `group_products_on_printings`, `has_blocked_account`, `has_manually_blocked_account` | `false` |
| `charge_back_purchase` | `100.00` |
| `charge_back_purchase_select` | `0` |
| `delivery_delay` | `0` |
| `invoice_sending_format_select` | `'emailpaper'` |
| `invoices_copy_select` | `2` |
| `lead_scoring_select` | `0` |
| `pay_notice_sending_method_select` | `1` |
| `payer_quality` | `0.00` |
| `payment_delay` | `0.00` |
| `sale_turnover` | `0` |
| `sequence` | `0` |
| `size_select` | `0` |
| `supplier_arrival_product_qty` | `0.00` |

**Motif pour la démo :** INSERT un tiers minimal, puis exécuter un bloc `UPDATE ... SET <field> = COALESCE(<field>, <default>)` scopé par `partner_seq` / `import_origin`.

**Vérifier en cas de doute :** `SELECT * FROM base_partner WHERE id = 8;` sur n'importe quelle base AOS installée donne une forme de référence vivante pour ce à quoi ressemble un tiers bien formé.

### 9. Panneaux du tiers vides sur un insert minimal — 4 relations à peupler

Un `INSERT INTO base_partner` minimal (name, is_supplier, currency, modes de paiement) laisse les panneaux d'interface suivants vides :

| Panneau du formulaire tiers | Ce qui manque | Comment le remplir |
|---|---|---|
| **generalContactDetailsPanel** | FK `email_address`, `fixed_phone`, `web_site` | INSÉRER une ligne dans `message_email_address`, puis UPDATE `base_partner.email_address` avec son id. Renseigner `fixed_phone` et `web_site` directement. |
| **partnerAddress** | FK `main_address` + ligne `base_partner_address` | INSÉRER dans `base_address` (obligatoire : `country` = 3 pour la FR, `addressl4` + `addressl6` pour l'affichage), INSÉRER dans `base_partner_address` avec les booléens `is_default_addr / is_delivery_addr / is_invoicing_addr`, UPDATE `base_partner.main_address`. |
| **companySet** | Lien M2M | INSÉRER `(base_partner, company_set)` dans `base_partner_company_set`. Typiquement company_set=1 (AXE). Paire pure, sans id de substitution. |
| **partnerDetailsPanel** | `partner_category`, `web_site`, parfois `localization`, `source`, `industry_sector` | UPDATE `base_partner.partner_category` (3 = PME pour les fournisseurs de démo génériques). Les champs restants sont optionnels mais enrichissent l'interface. |

Les quatre doivent être peuplés pour qu'un fournisseur de démo paraisse « réel » dans l'interface. MASSON SA (id=8) est de nouveau la forme de référence.

**Séquences à relever** après des inserts sur ce motif :
- `base_address_seq`, `message_email_address_seq`, `base_partner_address_seq` → toutes à ≥ 200100 après des données de démo dans la plage 200001+.

### 13. Tiers clients : `account_accounting_situation` est obligatoire pour la facturation (prolonge les pièges 8 et 9)

Un `base_partner` client créé sans ligne `account_accounting_situation` n'a **aucun compte client** → les flux de facturation/comptabilité se cassent, et le panneau comptable du tiers est vide (l'écart de densité est flagrant face à des tiers seedés comme APOLLO). Par société :
```sql
INSERT INTO account_accounting_situation (id, version, created_on, updated_on, created_by, updated_by,
  company, partner, customer_account, supplier_account, vat_system_select, name,
  accepted_credit, used_credit, balance_cust_account, balance_due_cust_account, balance_due_debt_recovery_cust_account,
  invoice_automatic_mail, invoice_automatic_mail_on_validate, cust_account_must_be_update_ok)
SELECT nextval('account_accounting_situation_seq'),0,NOW(),NOW(),1,1,
  1, p.id, 406, 385, 1, p.partner_seq||' - '||p.name, 50000,0,0,0,0,false,false,false
FROM base_partner p WHERE ... AND NOT EXISTS (SELECT 1 FROM account_accounting_situation s WHERE s.partner=p.id AND s.company=1);
```
ids `customer_account` / `supplier_account` : les copier depuis un tiers seedé qui fonctionne (`SELECT customer_account,supplier_account FROM account_accounting_situation WHERE partner=1;`). Renseigner aussi `localization`, `registration_code`, `payment_condition`, `partner_category` pour égaler la densité des données seedées.

**Contacts** = lignes `base_partner` séparées : `partner_type_select = 2` (Individu) + `is_contact = true` + `main_partner = <id du tiers société>`. Sans elles, le panneau Contacts de la société est vide. Attention : `job_title_function` est une **FK (bigint)**, PAS du texte libre — mettre une chaîne de rôle dans `description` (ou laisser job_title_function à NULL), sinon `column "job_title_function" is of type bigint but expression is of type text`.

### 23. Contacts (individus) : séparer prénom / NOM + civilité + localisation

Un contact `base_partner` (partner_type_select=2, is_contact=true, main_partner=<société>) ne doit PAS porter tout le « Prénom NOM » dans `name`. Reproduire la forme seedée : `name` = NOM, `first_name` = Prénom, `title_select` (`partner.title.type.select` : 1 M. / 2 Ms. / 3 Mx.), `localization`, et `full_name` = `"NOM Prénom"`. Sinon le contact paraît à moitié rempli face aux contacts seedés.

### 24. `registration_code` du tiers doit être un SIREN/SIRET VALIDE (Luhn) + renseigner les modes de paiement
> Prolongé par le piège 61 (SIREN valide ≠ SIRET valide), dans `methode-rejouabilite.md`.

Axelor valide le code d'immatriculation français (SIREN 9 / SIRET 14 chiffres, **clé de Luhn**). Des chiffres aléatoires sont rejetés comme invalides. Générer des numéros valides au sens de Luhn. Renseigner aussi `in_payment_mode` / `out_payment_mode` (copier depuis un tiers seedé — ex. 8 = Enc. Virement / 15 = Dec. Virement sur une base de démo standard) — NULL laisse le panneau de paiement du tiers vide.

### 42. Événements CRM sur un tiers : trois liaisons à remplir ensemble
Le clone remplit **`partner`** + **`contact_partner`** + **`related_to_select`**
(`'com.axelor.apps.base.db.Partner'`) + **`related_to_select_id`**. Même mécanisme polymorphe pour
d'autres entités (`…talent.db.JobApplication`), sur la table **`ical_event`** avec `dtype='Event'`.
Calquer le volume et les statuts sur l'étape du cycle (à traiter = 1 planifié → gagné = cycle complet).

### 70. Renommer `name` sans recalculer `full_name` = renommage INVISIBLE

Fait trois fois dans la même session : évité sur `base_partner`, oublié sur `project_project`,
puis re-cassé autrement sur les contacts.

```sql
-- FAUX : le renommage ne se voit NULLE PART
UPDATE project_project SET name = 'Déploiement Microsoft 365 — 450 postes' WHERE id = 31001;
-- l'écran continue d'afficher : « AFF-2026-001 - MOE <ouvrage> — <commune> »
```

`full_name` est une **copie dénormalisée** que l'application affiche partout (sélecteurs, listes,
impressions) alors que `name` ne sort quasiment jamais. Après tout renommage, recalculer.
Conventions relevées sur AOS 9 : `base_partner` → `partner_seq || ' - ' || name` ;
`project_project` → `code || ' - ' || name` ; **contact** → `partner_seq || ' - ' || name || ' ' ||
first_name` (cf. 72). Toujours **relever** la convention sur les lignes déjà conformes de la base,
jamais la supposer.

### 71. `full_name` à NULL rend l'enregistrement INVISIBLE — pire que le libellé périmé

```sql
-- FAUX : partner_seq est NULL sur les contacts importés → la concaténation vaut NULL
UPDATE base_partner SET full_name = partner_seq || ' - ' || name WHERE is_contact;
```

Dix contacts ont disparu des sélecteurs. Une concaténation SQL avec un seul opérande NULL vaut
NULL ; le remède devient la maladie. Toujours `COALESCE`/`CASE` sur les composants, et **asserter
`COALESCE(full_name,'') <> ''`** : un `full_name` vide ne lève aucune erreur, il efface juste
l'enregistrement de l'interface.

### 72. La convention d'un contact inclut le PRÉNOM

`full_name = '<seq> - <NOM> <Prénom>'`, `simple_full_name = '<NOM> <Prénom>'`. Écrire le nom seul
affiche « MARTIN » au lieu de « MARTIN Claire ». Cette erreur a été commise deux fois de suite sur le
même `UPDATE` — d'abord NULL, puis nom seul — parce que la convention était supposée au lieu d'être
relevée. Requête qui la donne en une passe :

```sql
SELECT partner_seq, name, first_name, full_name, simple_full_name
  FROM base_partner WHERE is_contact AND COALESCE(partner_seq,'') <> '' LIMIT 5;
```

### 84. `purchase_supplier_catalog` : la référence est celle du FOURNISSEUR

```
FAUX : code = 'EQPT-0010-TOP'        nom = 'Ordinateur portable 14 pouces (TOP Components)'
JUSTE : code = 'TOP-NBK-7K2M4'        nom = 'TopLine Portable Business 14 — 16 Go / 512 Go'
```

Notre code interne n'a rien à faire dans le catalogue d'un fournisseur, et le fournisseur est déjà
une colonne. Règle générative : `{MNÉMO}-{FAMILLE}-{TOKEN}` où le token est un hash déterministe
de `(supplier_id, product_id)` — opaque comme une vraie référence constructeur, stable au rejeu :

```sql
upper(substr(md5(k.supplier_partner::text || ':' || k.product::text), 1, 5))
```

Le nom est une désignation commerciale de marque, avec 2-3 caractéristiques discriminantes.

### 85. Table de couple : renseigner les DEUX côtés

`sale_complementary_product` porte `original_product` (le produit vendu) **et** `product` (le
complément). N'en remplir qu'un crée une relation orpheline, acceptée par la base et invisible à
l'écran. Avant d'insérer dans une table de liaison, lister ses FK et vérifier qu'aucune n'est
laissée vide.

### 87. `MetaFile` par l'API : la réponse porte `data` sous forme de TABLEAU

```js
// FAUX : up.data.id est undefined → on croit l'upload échoué… alors qu'il a RÉUSSI
const fid = up.status === 0 && up.data.id;
// JUSTE
const fid = up.status === 0 && up.data && up.data[0] && up.data[0].id;
```

Vingt-six `meta_file` créés et laissés orphelins, avec leurs fichiers physiques, par un test sur la
mauvaise forme. **Un upload réussi mal interprété laisse des débris silencieux.** Les supprimer
par l'application (`DELETE /ws/rest/…/MetaFile/{id}`), jamais en SQL, pour que le fichier physique
parte avec la ligne. Ne pas confondre avec les `ProductBarCode<id>.png` qu'AOS génère
automatiquement à chaque sauvegarde de produit et rattache à `base_product.bar_code` : artefacts
légitimes, pas des débris.

### 108. Un contact créé via `main_partner` n'alimente PAS la jonction `base_partner_contact_partner_set` — panneau Contacts vide

Le contact d'une société (piège 13 : `base_partner` séparé, `partner_type_select=2`,
`is_contact=true`, `main_partner=<société>`) porte la relation UNIQUEMENT côté contact. Le panneau
« Contacts » de la fiche société est peuplé par une jonction M2M **distincte**,
`base_partner_contact_partner_set` (côté société → ensemble de contacts) — jamais renseignée
automatiquement par l'INSERT du contact, quel que soit `main_partner`.

```
FAUX : INSERT INTO base_partner (main_partner, is_contact, ...) VALUES (<societe>, true, ...);
   -- la fiche société ouvre : onglet Contacts VIDE, alors que le contact existe et pointe bien
   -- vers cette société via main_partner
JUSTE : INSERT INTO base_partner_contact_partner_set (base_partner, contact_partner_set)
   VALUES (<societe>, <contact>);
```

Table de couple pure (piège 85), sans colonne `id`, sans colonne d'audit — les deux côtés (société,
contact) doivent être posés, mais ici il n'y a qu'un seul sens possible (société → contact), donc
c'est bien l'ABSENCE totale de ligne qui est le piège, pas un côté oublié.

**Coût mesuré** (chantier package CRM, `<base>`, 2026-09-07/08) : 44 tiers-sociétés créées avec
leurs contacts correctement rattachés par `main_partner` — **aucune** n'avait cette jonction posée.
Trouvé par contrôle écran (défaut P1 : panneau Contacts vide sur les fiches
vitrines malgré des contacts réels en base), confirmé par requête REST (`contactPartnerSet` vide),
corrigé par 57 lignes sur les 28 organisations restantes —
44/44 organisations couvertes après correction.

### 109. Un domaine `:__user__`/`:_internalUserId` exige une FK utilisateur EXPLICITEMENT posée, sur CHAQUE tiers

Plusieurs menus « Mes … » filtrent par `self.user.id = :_internalUserId` (ou `:__user__` selon le
mécanisme) : `crm.my.lead` (`entites-crm.md` §1), la feuille de temps « Ma feuille de temps »
(`self.employee.user.id = :user_id`, `entites-projet-temps.md` §5). Le piège n'est pas propre à un
écran : il est **transverse à toute table qui porte une FK `user`/`user_id` consommée par un tel
domaine**. Une FK NULL sur cette colonne ne vide pas l'écran que pour l'utilisateur visé — elle le
vide pour **tout le monde**, admin compris, puisque `self.user.id = :_internalUserId` ne matche
jamais un NULL.

**Mesuré** (chantier package CRM, `<base>`, 2026-09-07/08) : `base_partner.user_id` NULL sur les
48 organisations prospects/clientes — socle (21/21) **et** créations (16/16 mesurées côté
prospects) — soit le menu `crm-my-prospects`
(`self.isContact=false AND self.isProspect=true AND self.user.id=:_internalUserId`) rendait 0 ligne
pour n'importe quel utilisateur, y compris `admin`. Corrigé en posant `user_id` sur les 48
(rapport de finalisation, P1-2 : 0 organisation sans `user_id`, ≥2 commerciaux affectés à
≥5 prospects chacun).

**Règle générale** : avant de déclarer un jeu de données prêt pour un persona nommé (« démo pour
un directeur d'agence », « portefeuille d'un commercial CRM »), lister toutes les FK utilisateur consommées par les
domaines `:__user__`/`:_internalUserId` du périmètre (grep sur ces deux tokens dans `meta_action`)
et vérifier qu'elles sont posées sur CHAQUE ligne concernée par ce domaine — pas seulement sur
celles créées pour le héros de la démo.

### 123. Un tiers sans ligne `base_partner_company_set` est INVISIBLE dans les sélecteurs client d'un devis et fournisseur d'une commande d'achat

**Symptôme :** le tiers existe, sa fiche s'ouvre, la recherche globale le trouve — et il **n'apparaît
pas** dans le sélecteur « Client » d'un devis ni « Fournisseur » d'une commande d'achat. Aucune
erreur. En démonstration, ça se traduit par « créons un devis pour ACME » suivi d'une liste vide.

La cause est dans le domaine calculé par les services, pas dans une vue — donc invisible à un grep
sur les XML. Lu au `javap` sur les jars **déployés** (AOS 9.1.4) :

```
axelor-sale-9.1.4.jar     SaleOrderDomainServiceImpl
  self.id != %d AND self.isContact = false AND (self.isCustomer = true or self.isProspect = true)
  AND :company member of self.companySet

axelor-purchase-9.1.4.jar PurchaseOrderDomainServiceImpl
  ... AND self.isSupplier = true AND :company member of self.companySet
```

`companySet` est le M2M porté par la table de jonction `base_partner_company_set`
(`base_partner`, `company_set`). Un tiers créé par l'interface la reçoit automatiquement ; **un
tiers créé en SQL ne l'a pas**, et rien ne le signale.

**Correctif de seed** — une ligne par tiers et par société, à poser dans le même lot que le tiers :

```sql
INSERT INTO base_partner_company_set (base_partner, company_set)
SELECT p.id, c.id FROM base_partner p, base_company c
WHERE p.import_origin = :tag AND COALESCE(p.archived,false) = false
  AND NOT EXISTS (SELECT 1 FROM base_partner_company_set x
                  WHERE x.base_partner = p.id AND x.company_set = c.id);
```

**Garde à écrire** : rejouer le domaine réel plutôt que compter les lignes de jonction — c'est lui
qui décide.

```sql
SELECT count(*) FROM base_partner p
 WHERE COALESCE(p.archived,false) = false AND COALESCE(p.is_contact,false) = false
   AND (p.is_customer OR p.is_prospect)
   AND EXISTS (SELECT 1 FROM base_partner_company_set cs
               WHERE cs.base_partner = p.id AND cs.company_set = :company);
```

*Coût payé le 2026-09-14* : 73 tiers réels sur 75 invisibles dans les deux sélecteurs, découvert par
une relecture adverse et non par l'audit de complétude — aucune dimension ne teste une table de
jonction absente. Ne pas confondre avec le piège 85 (table de couple, les deux côtés d'une jonction
existante) : ici la jonction n'existait pas du tout.

## Règle de sûreté (ex-PROHIBITIONS)

- Ne jamais créer d'adresse sans `country` : la colonne est NOT NULL, l'insert échoue sinon.
