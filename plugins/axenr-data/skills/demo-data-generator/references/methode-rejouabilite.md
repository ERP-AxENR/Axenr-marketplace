# Méthode — rejouabilité

**Pièges couverts par cette fiche :**

- 58. `AND EXISTS(...)` protège de la FK NULL mais crée un échec SILENCIEUX sur base vierge
- 59. Un jeu de données tagué n'est PAS un jeu de données rejouable
- 60. Le skill sait « comment », pas « quoi » : exiger une spécification de scénario
- 61. SIREN valide ≠ SIRET valide
- 62. Remplir « les booléens principaux » ne suffit pas — il faut TOUS les booléens
- 63. `quote_nullable(NULL)` renvoie le TEXTE `'NULL'` — un override en `NULL` nu vide la ligne
- 64. Cycles FK via `created_by` / `updated_by`
- 65. Cycles FK « vers l'avant » entre fichiers
- 66. Cycles à deux tables
- 67. L'ordre FK-safe réel diverge de l'ordre « logique métier »
- 68. Tables de jonction M2M : pas de colonne `id`
- 69. Nuance sur « aucune sélection NULL » : les champs CONDITIONNELS
- 79. Les archives ne se réécrivent pas
- 80. Sélectionner par motif de libellé rend la vague non rejouable
- 86. FK attendant un `id`, alimentée par un code métier
- 116. Un livrable qui pose des `MetaFile` réels n'est pas complet sans l'archive des fichiers physiques
- 215. Le jar qui tourne prime sur les sources : appeler l'action (elle peut écrire, piège 97) ou lire le bytecode avant d'écrire
- 216. Rejeu : `widgetAttrs` réécrit clés triées ; références comparées par id

Rejouer un jeu **par l'API** vers une instance sans accès base ni retour arrière (instance hébergée, base d'un
partenaire), contrôlé étape par étape contre une répétition : `methode-rejeu-controle.md`.

# Rejouer un jeu de données sur une base VIERGE (le piège qui annule tout)

### 58. `AND EXISTS(...)` protège de la FK NULL mais crée un échec SILENCIEUX sur base vierge
La parade au piège n°37 (une sous-requête FK sans résultat écrit NULL en silence) consiste à ajouter
`AND EXISTS (SELECT 1 FROM <ref> WHERE …)` dans le `WHERE` de l'INSERT. Excellente sur la base de
travail — **et dévastatrice sur une base vierge** : le prérequis étant absent, la garde **ignore la
ligne** au lieu de lever. Le script s'exécute, rapporte `COMMIT`, et n'insère presque rien.

Mesuré sur un chantier réel : 29 fichiers SQL, **51 références** à des données préexistantes
(produits par code, tiers par nom, projets, journaux, employés, catégories, périodes) et **16 gardes
`EXISTS`**. Sur un environnement vierge, l'essentiel aurait été silencieusement sauté.

**Parade : un contrôle de PRÉREQUIS en tête de chaque script**, qui lève si le socle n'est pas là :

```sql
DO $$
DECLARE manquants text := '';
BEGIN
  IF NOT EXISTS (SELECT 1 FROM base_company)                       THEN manquants := manquants||'société, '; END IF;
  IF NOT EXISTS (SELECT 1 FROM base_currency WHERE code='EUR')     THEN manquants := manquants||'devise EUR, '; END IF;
  IF NOT EXISTS (SELECT 1 FROM base_product)                       THEN manquants := manquants||'produits, '; END IF;
  IF NOT EXISTS (SELECT 1 FROM account_journal)                    THEN manquants := manquants||'journaux, '; END IF;
  IF manquants <> '' THEN
    RAISE EXCEPTION 'PRÉREQUIS ABSENTS : % — exécuter d''abord les scripts de socle', manquants;
  END IF;
END $$;
```


*(Renvoi résolu : piège 37 → `references/methode-introspection.md`.)*

### 59. Un jeu de données tagué n'est PAS un jeu de données rejouable
Le tag `import_origin` marque ce **qu'on a ajouté**, pas ce dont on **dépend**. Sur le chantier cité :
0 produit, 0 projet, 0 compte et 0 société ne portaient le tag — ils venaient tous du clone de départ.
Extraire « les lignes taguées » produit donc un livrable inexploitable.

**Pour un livrable rejouable, extraire par TABLE ENTIÈRE**, dans l'ordre des couches
(socle transverse → master data → référentiels par module → transactionnel → liaisons), en résolvant
les FK par code/nom, et **valider sur un boot réellement vierge** — pas sur la base de travail, qui
masque toutes les dépendances implicites.

### 60. Le skill sait « comment », pas « quoi » : exiger un contrat de scénario
Ce document évite les erreurs de forme ; il ne contient pas le **contenu métier** d'une démo donnée.
Ce qui manque n'est pas une liste de tables, c'est un **contrat de scénario** au sens de
`references/cadrage-scenario.md` : les **objets métier** avec leur décision (réutiliser / créer /
enrichir), leur **volumétrie justifiée par un écran cible** et leur répartition de statuts, plus
l'**horloge** (date pivot, fenêtre passé / futur, jalons). Les tables se dérivent de ces objets en
Phase 2. Demander la liste des tables au demandeur inverse la frontière et fabrique une spécification
qui se périme : la surface technique se vérifie contre la base cible à chaque exécution, elle ne se
transporte pas.

Si la demande est « repeuple comme l'autre environnement », deux voies seulement : récupérer le SQL
auto-portant de l'origine, ou **faire produire le contrat** (suivre
`references/cadrage-scenario.md`) puis dériver la surface en Phase 2. Jamais improviser l'histoire
en écrivant les données. Cas particulier : combler quelques panneaux vides sur une base qui a déjà
une identité n'appelle pas le skill amont — reconstituer le scénario en trois lignes (identité
constatée, écrans à combler, volumétrie minimale visée), le faire confirmer, continuer.

### 61. SIREN valide ≠ SIRET valide
> Complète le piège 24 (registration_code = SIREN/SIRET valide), dans `entites-tiers-contacts.md`.
Le pitfall #24 impose des numéros Luhn-valides. Précision qui a coûté un aller-retour :
**la clé de Luhn du SIREN (9 chiffres) ne rend pas valide le SIRET (14 chiffres)**. Concaténer
`siren || nic` avec un NIC arbitraire produit un SIRET rejeté par `RegistrationNumberValidator`
(« N° SIRET invalide » dans les logs, à chaque affichage de la fiche). Choisir le dernier chiffre du
NIC pour que **l'ensemble des 14 chiffres** satisfasse Luhn.


*(Renvoi résolu : piège 24 → `references/entites-tiers-contacts.md`.)*

### 62. Remplir « les booléens principaux » ne suffit pas — il faut TOUS les booléens
Renseigner les flags qu'on a en tête (`is_customer`, `is_prospect`…) laisse les autres à NULL, donc
exclus des grids et des filtres. Vérifié par audit sur un chantier pourtant soigné : **12 booléens à
NULL sur les tiers créés** (`is_carrier`, `is_factor`, `is_internal`, `is_key_account`, `is_nurturing`,
`is_partner`, `is_subcontractor`, `has_blocked_account`…) et 2 sur les adresses. Lister les colonnes
booléennes de la table (`introspect.sh` section 2) et les poser **toutes** explicitement ;
`scripts/audit-completeness.sql` dimension 1 le vérifie.

---

# Extraire un jeu REJOUABLE : pièges d'ordre, de cycles et de génération

Vérifiés en produisant un replay de 64 tables (socle + master data) rechargé sur une base au schéma
complet et sans données — 0 écart de count, idempotent, 0 FK orpheline.

### 63. `quote_nullable(NULL)` renvoie le TEXTE `'NULL'` — un override en `NULL` nu vide la ligne
`quote_nullable(col)` gère nativement les valeurs NULL : il produit la chaîne `NULL` (4 caractères),
exactement ce qu'il faut dans le SQL généré. **Mais** si l'on injecte soi-même un override avec le
mot-clé SQL `NULL` dans une concaténation de génération, toute l'expression `||` s'évalue à NULL et la
ligne générée sort **vide, sans aucune erreur** — 0 ligne produite, silencieusement. Pour un override
qui doit produire le mot `NULL` en sortie, écrire le littéral texte `'NULL'`.

### 64. Cycles FK via `created_by` / `updated_by`
`auth_user` ↔ `auth_group` : le groupe référence `created_by` (un utilisateur) tandis que
l'utilisateur référence `group_id`. Aucun ordre de chargement ne résout ce cycle.
**Parade** : charger avec ces colonnes à NULL (bootstrap), puis les restaurer par `UPDATE` en seconde
passe dans le même fichier. Les colonnes d'audit sont les cycles les plus faciles à oublier parce
qu'on ne les considère pas comme des FK métier.

### 65. Cycles FK « vers l'avant » entre fichiers
`base_company.address`, `default_bank_details` et `partner` pointent vers des tables de la couche
**master data**, chargée *après* le socle — alors que `base_partner.company_department` pointe vers le
socle, chargé *avant*. La dépendance est donc croisée entre couches et aucun ordre ne la satisfait.
**Parade** : nuller à l'insertion, puis restaurer par `UPDATE` dans le fichier de la couche cible.
Sur ce chantier, 6 relations étaient concernées (`auth_user.partner/employee`,
`base_company.address/default_bank_details/partner`, `stock_stock_location.address`,
`account_account_management.product/bank_details`).

### 66. Cycles à deux tables
`account_tax.active_tax_line` pointe une ligne de `account_tax_line`, qui référence elle-même
`account_tax`. Même parade (null puis restauration), mais **à l'intérieur d'un seul fichier**.

### 67. L'ordre FK-safe réel diverge de l'ordre « logique métier »
`account_fixed_asset_category.journal` impose de charger `account_journal` avant les catégories
d'immobilisation, alors qu'un tri par thème mettrait les journaux « après ». **Calculer l'ordre par
introspection** (`pg_constraint contype='f'`, fermeture transitive), ne jamais le déduire du plan
comptable ou de l'intuition fonctionnelle.

### 68. Tables de jonction M2M : pas de colonne `id`
`base_partner_company_set`, `auth_group_roles`… n'ont que deux colonnes FK. Deux conséquences pour un
générateur : la boucle `setval` **plante** (`column "id" does not exist`) si on ne les exclut pas, et
la garde d'idempotence doit porter sur **la paire de colonnes**, pas sur un id.

### 69. Nuance sur « aucune sélection NULL » : les champs CONDITIONNELS
La règle cardinale 4 vise les sélections d'un champ **visible dans le contexte de l'enregistrement**.
Certaines sélections sont conditionnées par un autre champ, et leur NULL est alors **porteur de sens** :
sur une immobilisation, `disposal_type_select` et `disposal_qty_select` ne se remplissent qu'en cas de
**cession** ; `fiscal_*` et `ifrs_*` n'ont de sens que si le plan d'amortissement correspondant est
actif. Y poser une valeur affirmerait une cession ou un plan qui n'existent pas.
Même logique pour un booléen : `quality_quality_measuring_point.compliant` doit rester NULL sur les
relevés de type « Note » (vérifié : les relevés de type Note portent `measuring_note` seul). Ceux de type
Conformité portent `compliant` **et** `measuring_note` (5 si conforme, 0 sinon) : c'est l'onChange de
l'écran (`action-measuring-point-attrs-on-compliant-change`, AOS 9.1.8) — piège 212 (`entites-qualite.md`).
La démo de référence dont `socle-b-shape.md` relève la shape (la démo ESN de référence, peuplée par 29 lots SQL :
`socle-aos-baseline.md` §1 et §8 ; la table est vide dans le socle AOS) ne porte que l'un des deux sur chaque point de
mesure (`compliant` 55 %, `measuring_note` 45 %) : sur ce point, elle n'est pas un modèle de shape (règle 8).
**Méthode** : avant de combler un NULL en masse, vérifier si le champ dépend d'une condition
(`showIf`/`hidden` dans la vue, ou un champ discriminant dans les données). Combler aveuglément
transforme un audit vert en données fausses.

---

### 79. Les archives ne se réécrivent pas

Une vague renommait 31 affaires dont une **archivée**, alors que le même chantier s'interdisait
explicitement de toucher une autre opportunité archivée, garde à l'appui. Une règle appliquée à un
enregistrement et pas à son voisin n'est pas une règle. Filtrer `COALESCE(archived,false) = false`
dans toute passe de renommage ou d'enrichissement.

### 80. Sélectionner par motif de libellé rend la vague non rejouable

```sql
-- FAUX : après la première exécution, ce motif ne matche plus rien : la vague est morte
WHERE o.name LIKE 'AO —%'
-- JUSTE : l'appartenance ne bouge pas
WHERE o.partner BETWEEN 30001 AND 30010
```

Une vague idempotente ne peut pas cibler par une propriété **qu'elle modifie elle-même**. Cibler
par appartenance, par `import_origin`, par identifiant — jamais par le libellé qu'on réécrit.

### 86. FK attendant un `id`, alimentée par un code métier

```sql
-- FAUX : column "country_of_origin" is of type bigint but expression is of type text
SET country_of_origin = 'CN'
-- JUSTE
SET country_of_origin = c.id  ... JOIN base_country c ON c.alpha2code = 'CN'
```

Erreur bénigne parce qu'elle échoue bruyamment. Elle mérite sa place parce qu'elle rappelle que
`scripts/introspect.sh` donne les types **et** les cibles de FK : le lire évite l'aller-retour.

### 116. Un livrable qui pose des `MetaFile` réels n'est pas complet sans l'archive des fichiers physiques

Quand une FK NOT NULL vers `MetaFile` force un vrai document (piège 40 : `crm_catalog.pdf_file`,
`hr_employment_contract_template.meta_file`), traiter le champ « proprement » plutôt que le classer
justifié-vide exige de déposer un fichier réel dans `data.upload.dir` (lu dans
`axelor-config.properties`, typiquement `{user.home}/.axelor/attachments`) **avant** d'insérer la
ligne `meta_file` qui le référence (taille exacte, `store_type` cohérent). Fait sur le chantier
package CRM : 6 PDF minimaux mais structurellement valides (1 page, PDF 1.4, vérifiés par
`pdfinfo`) déposés puis référencés par 6 lignes `meta_file` réelles.

**Conséquence pour la rejouabilité (généralise piège 59 : un jeu tagué n'est pas un jeu rejouable)**
— un dump SQL/pg_dump seul ne suffit PAS à restaurer ce jeu de données ailleurs : la ligne
`meta_file` pointe un fichier sur le disque de l'environnement source, absent de tout dump base.
**Le livrable d'un jeu de données qui pose des `MetaFile` réels est donc TOUJOURS double : le dump
(ou le bundle CSV+XML) ET une archive du répertoire d'attachements** (au minimum les fichiers
créés par ce chantier, identifiables par leur id ou leur tag), à restaurer au même chemin
`data.upload.dir` sur l'environnement cible avant tout premier accès aux fiches concernées. Un
guide de restauration qui ne mentionne que le dump laisse les fiches avec un fichier référencé mais
introuvable (téléchargement en 404, sans qu'aucune ligne de base ne le signale).

---

# Peupler par l'API un jeu rejouable : le code qui tourne, la forme stockée

Deux pièges de méthode constatés à l'exécution **(R)** pendant un peuplement par l'API (module Qualité, AOS 9.1.8,
démo client, 05/10/2026 — `entites-qualite.md`).

### 215. Méthode : en cas de doute, le jar qui tourne prime sur les sources (R)
Le 05/10/2026, trois comportements déduits des sources (checkout AOS du tag visé) avant l'écriture étaient faux
sur le jar 9.1.8 qui tournait (pièges 202, 207, 210, `entites-qualite.md`). Avant d'écrire un script qui dépend
d'un onChange ou d'un contrôleur, appeler l'action sur un enregistrement réel et lire sa réponse — l'appel peut
écrire (piège 97, `methode-ecriture-sql.md`) : enregistrement jetable, ou compté dans l'inventaire des écritures —,
ou lire le bytecode (`unzip` du jar de `WEB-INF/lib`, `javap -c -p`).

### 216. Rejeu : comparer comme l'application stocke (R)
`widgetAttrs` d'un MetaJsonField est réécrit clés triées (`{"colSpan": 12, "showTitle": true}`) : l'envoyer trié,
sinon chaque rejeu le réécrit. Comparer les références par id (une recherche REST rend `{id, $version, fullName}`)
et demander le champ dans la recherche avant de le comparer. Comparer par id vaut sur la même base, pour décider
s'il faut réécrire ; entre deux instances, la comparaison passe par des clés naturelles, jamais par un id
(`methode-rejeu-controle.md` §3).
