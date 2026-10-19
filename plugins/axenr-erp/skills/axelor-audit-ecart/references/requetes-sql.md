# Requêtes SQL d'audit (méta-modèle Axelor)

> Toutes en **SELECT seul** (read-only). Jamais d'écriture sur une base client.
> Le méta-modèle Axelor stocke le low-code (Studio) dans des tables `meta_*`. Ces requêtes permettent
> de voir ce qui existe en base, y compris ce qui n'est PAS dans les fichiers du dépôt.

## Établir la connexion

Identifiants dans `axelor-config.properties` (`db.default.url`, `db.default.user`, `db.default.password`).

```bash
# Base distante
psql "postgresql://<user>:<password>@<host>:<port>/<db>"

# Base en conteneur Docker
docker ps                                   # repérer le conteneur PostgreSQL
docker exec -it <conteneur_pg> psql -U <user> -d <db>
```

## 0. Calibrage — prouver que la méthode voit le low-code

Avant tout audit, retrouver un élément CONNU pour exister (témoin). S'il ne ressort pas, l'accès/la requête est mauvais → corriger avant de continuer.

```sql
-- Témoin : un champ custom dont on sait qu'il existe (ex. vu à l'écran)
SELECT mf.name, mf.type_name, mf.label, mm.name AS model
FROM meta_field mf
JOIN meta_model mm ON mf.meta_model = mm.id
WHERE mf.name = '<champ_temoin>';
```

## 1. Un champ custom existe-t-il ? Sur quel objet ?

```sql
SELECT mf.name, mf.type_name, mf.label, mm.name AS model, mf.is_json
FROM meta_field mf
JOIN meta_model mm ON mf.meta_model = mm.id
WHERE mf.name ILIKE '%<motcle>%'
ORDER BY mm.name, mf.name;
```

- `is_json = false` → **vraie colonne PostgreSQL** (champ Studio « dur »). Si elle n'est pas dans les fichiers du dépôt → dette low-code à signaler (risque de perte au rebuild).
- `is_json = true` → champ stocké dans la colonne `attrs` (custom field JSON), moins risqué.

Lister tous les champs custom d'un objet donné :

```sql
SELECT mf.name, mf.type_name, mf.label, mf.is_json
FROM meta_field mf
JOIN meta_model mm ON mf.meta_model = mm.id
WHERE mm.name = '<NomObjet>'        -- ex. Product, Invoice, SaleOrder, StockMove, Partner, StockLocation
ORDER BY mf.name;
```

## 2. Une sélection (liste de valeurs) existe-t-elle ? Quelles valeurs ?

```sql
-- La sélection existe ?
SELECT id, name FROM meta_select WHERE name ILIKE '%<motcle>%';

-- Ses valeurs réelles
SELECT msi.value, msi.title, msi.order_seq
FROM meta_select_item msi
JOIN meta_select ms ON msi.select_id = ms.id
WHERE ms.name = '<nom.de.la.selection>'
ORDER BY msi.order_seq;
```

Utile pour vérifier, par ex., qu'une sélection « Oui/Non » a (ou pas) une 3ᵉ valeur attendue.

## 3. Une vue / un onglet existe-t-il ?

```sql
SELECT name, type, title, model
FROM meta_view
WHERE name ILIKE '%<motcle>%' OR title ILIKE '%<motcle>%'
ORDER BY model, name;
```

`type` vaut typiquement `form`, `grid`, `cards`, `tree`…

## 4. Un menu existe-t-il ?

```sql
SELECT name, title, action
FROM meta_menu
WHERE name ILIKE '%<motcle>%' OR title ILIKE '%<motcle>%'
ORDER BY name;
```

Pratique pour confirmer/infirmer un menu attendu (ex. un menu de pilotage attendu par la SFD).

## 5. Une action / un batch existe-t-il ?

```sql
SELECT name, type
FROM meta_action
WHERE name ILIKE '%<motcle>%'
ORDER BY name;
```

`type` : `action-method`, `action-record`, `action-condition`, `action-view`, `action-script`…
Pour un batch métier, chercher aussi côté fichiers `.java` (classe du batch) ET la valeur dans la sélection des actions du batch concerné.

## 6. Repérer la dette low-code d'un objet (champs en base absents des fichiers)

Stratégie : lister les champs `is_json=false` en base pour un objet, puis comparer à ce que déclare le domain XML du dépôt. Tout champ en base mais absent du fichier = dette à verser.

```sql
SELECT mf.name, mf.type_name, mf.label
FROM meta_field mf
JOIN meta_model mm ON mf.meta_model = mm.id
WHERE mm.name = '<NomObjet>' AND mf.is_json = false
ORDER BY mf.name;
```

Puis : `grep -n "name=\"<champ>\"" modules/*/src/main/resources/domains/<NomObjet>.xml` pour chaque champ, et noter ceux qui ne ressortent pas.

## Astuces

- Les noms de tables/colonnes du méta-modèle peuvent varier légèrement selon la version d'Axelor (AOP). Si une colonne n'existe pas (`meta_field.meta_model` vs `meta_field.model_id`…), inspecter le schéma : `\d meta_field` sous psql.
- Pour une recherche transverse rapide « ce mot apparaît-il quelque part en méta » : balayer `meta_field.name`, `meta_select.name`, `meta_view.name`, `meta_action.name`, `meta_menu.name` avec le même `ILIKE '%<motcle>%'`.
