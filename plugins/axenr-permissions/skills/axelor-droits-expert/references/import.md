# Générer et passer le fichier d'import

## Règles valables quel que soit le canal

| # | Règle | Conséquence si ignorée |
|---|---|---|
| 1 | Chaque enregistrement a un `importId` unique et stable | Doublons, réimport impossible |
| 2 | Un enregistrement existant sans `importId` doit d'abord en recevoir un | Création de doublons |
| 3 | L'objet référencé s'importe avant l'objet qui le référence | `Relation not found` |
| 4 | Un onglet ou un input à la fois, jamais tout en une passe | Erreur 500, dépendances non committées |
| 5 | Les M2M s'**ajoutent**, ils ne remplacent pas | Droits résiduels non voulus |
| 6 | Tester sur 3 à 10 lignes, puis lire les statistiques d'import | Erreurs en masse |
| 7 | Les statistiques « succès » ne suffisent pas : recouper en SQL | Faux positifs |
| 8 | Booléens `TRUE` / `FALSE`, dates `YYYY-MM-DD`, décimaux avec un point | Erreurs de parsing |
| 9 | Ne jamais inclure `admin`, le groupe `admins`, ni aucun mot de passe | Compte cassé, fuite |
| 10 | Ne jamais retirer de droits au compte qui réalise l'import | Se verrouiller dehors |

**Un import ne retire jamais un lien M2M.** Tout retrait de droit est une action manuelle, à lister
explicitement dans le livrable. Ne laisse jamais croire qu'un import « remet à plat » les droits.

## Ordre d'import

```
Permission
MetaPermission
MetaPermissionRule
Role              (puis Role.permissions)
Group             (puis Group.roles)
User              (mise à jour des affectations uniquement)
MetaMenu.roles    (côté propriétaire)
```

## Canal Excel : un onglet par objet

Le plus courant. Chaque onglet porte le **nom exact du modèle**, un onglet M2M le format
`Modele.champ`. Un onglet dont le nom dépasse 31 caractères est ignoré en silence et demande un
mécanisme de configuration supplémentaire : aucun des onglets ci-dessous n'est concerné.

| Onglet | Colonnes |
|---|---|
| `Permission` | `importId`, `name`, `object`, `canRead`, `canWrite`, `canCreate`, `canRemove`, `canExport` |
| `MetaPermission` | `importId`, `name`, `object`, `active` |
| `MetaPermissionRule` | `importId`, `metaPermission.importId`, `field`, `canRead`, `canWrite`, `canExport` |
| `Role` | `importId`, `name`, `description` |
| `Role.permissions` | `importId`, `permissions.importId` |
| `Group` | `importId`, `code`, `name`, `technicalStaff` |
| `Group.roles` | `importId`, `roles.importId` |
| `User` | `importId`, `group.importId` |
| `MetaMenu.roles` | `importId`, `roles.importId` |

**Les relations ne se résolvent de façon fiable que par `importId`.** Une colonne `.name` ou
`.code` peut rester vide sans lever d'erreur. Conséquence pratique : les enregistrements existants
que tu veux référencer doivent d'abord recevoir un `importId`. La méthode : inclure ces
enregistrements dans l'onglet de leur modèle, avec l'`importId` que tu leur attribues et leur clé
naturelle, en recherchant sur cette clé. Une permission déjà présente reçoit ainsi son `importId`
sans être modifiée par ailleurs.

Mappe explicitement chaque colonne `.importId` dans l'écran de correspondance : une colonne non
mappée est ignorée en silence.

Le fichier d'import ne contient **que** des colonnes réellement mappées. Les libellés destinés à
la relecture vont dans un document séparé. Une colonne préfixée `_` est ignorée à l'import, mais
elle n'a rien à faire dans un fichier d'import.

## Canal CSV + XML de binding

Préférable pour un lot versionné en Git, ou quand tu veux rechercher par clé naturelle plutôt que
par `importId`.

CSV : UTF-8, séparateur `;`, tous les champs entre guillemets, M2M en une colonne séparée par `|`.

```xml
<input file="04_auth_role.csv" separator=";"
       type="com.axelor.auth.db.Role"
       search="self.name = :name">
  <bind to="permissions" column="permissions"
        search="self.name in :permissions"
        eval="permissions ? permissions.split('\\|') as List : null"/>
</input>
```

Reprends l'en-tête `csv-inputs` et la version du XSD depuis un fichier de configuration d'import
existant du dépôt : elle doit correspondre à la version de la plateforme.

Points de vigilance propres à ce canal :

- Un `search` qui ne trouve rien **crée** un nouvel enregistrement. Pour `User` et `MetaMenu`,
  toute création est une anomalie : contrôle en amont que chaque clé existe. Avec
  `update="true"`, l'input devient au contraire **mise à jour seule** : une clé introuvable est
  ignorée en silence (voir la recette ci-dessous, piège IP2).
- L'échappement du pipe dans `split` varie selon les versions. Sur AOP 8.2.x, l'apport partenaire
  constate que `split('\\|')` est du Groovy invalide pour l'évaluateur d'import (« Unexpected
  character: '\\' », ligne en échec) et recommande `tokenize('|')`. L'exemple ci-dessus vient d'un
  dépôt plus ancien : sur la version cible, teste les deux formes sur 3 lignes, et préfère
  `tokenize('|')` si `split` échoue.
- Une colonne présente dans le CSV mais vide peut écraser une valeur obligatoire. N'inclus pas les
  colonnes que tu ne veux pas toucher.

## Recette du bundle de profil complet (csv-inputs)

> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Bundle validé de bout en bout une fois
> en AOS 9.1.1 / AOP 8.2.1 par Administration > Configurations d'import ; mécanismes lus dans AOP
> 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : à vérifier sur la version cible.

Voie partenaire ou recette : déployer rôles, permissions, menus, groupe et affectations par
**Administration > Configurations d'import**, sans accès à la base ni reconstruction du WAR. C'est
le format d'initialisation standard d'AOS (fichiers `apps/roles/<module>-config.xml` de chaque
module), réemballé pour un import lancé depuis l'interface. Le cadrage de `cadrage-profils.md`
doit être validé avant.

Prérequis : l'instance tourne sous AOS (`axelor-base` présent). Le rattachement des permissions
aux rôles passe par le script livré `com.axelor.csv.script.ImportPermission:importPermissionToRole`.

### Ordre propre à cette recette

```
Role -> Permission (script ImportPermission) -> Group (+ roles) -> MetaMenu (+ roles) -> User
```

**Différence avec l'ordre général ci-dessus** (Permission avant Role) : ici, c'est le script
`ImportPermission` qui rattache chaque permission au rôle nommé dans sa colonne `roleName`, donc le
rôle doit exister d'abord. Dans le canal Excel, la liaison passe par l'onglet `Role.permissions`
importé après les deux : les deux ordres sont cohérents avec leur mécanisme. Chaque `<input>` est
validé avant le suivant ; un `search` ne voit pas les lignes créées plus tôt **dans le même**
input, mais voit celles d'un input précédent. Une entité par input.

### `bind.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<csv-inputs xmlns="http://axelor.com/xml/ns/data-import"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://axelor.com/xml/ns/data-import
    http://axelor.com/xml/ns/data-import/data-import_8.1.xsd">

  <!-- 1. Rôles : search seul = vrai upsert -->
  <input file="role.csv" separator=";" type="com.axelor.auth.db.Role"
    search="self.name = :name">
    <bind column="name" to="name"/>
    <bind column="description" to="description"/>
  </input>

  <!-- 2. Permissions, rattachées à leur rôle par le script AOS -->
  <input file="permission.csv" separator=";" type="com.axelor.auth.db.Permission"
    search="self.name = :name"
    call="com.axelor.csv.script.ImportPermission:importPermissionToRole">
    <bind column="name" to="name"/>
    <bind column="object" to="object"/>
    <bind to="canRead"   eval="can_read   == 'x' ? 'true' : 'false'"/>
    <bind to="canWrite"  eval="can_write  == 'x' ? 'true' : 'false'"/>
    <bind to="canCreate" eval="can_create == 'x' ? 'true' : 'false'"/>
    <bind to="canRemove" eval="can_remove == 'x' ? 'true' : 'false'"/>
    <bind to="canImport" eval="can_import == 'x' ? 'true' : 'false'"/>
    <bind to="canExport" eval="can_export == 'x' ? 'true' : 'false'"/>
    <bind column="condition" to="condition"/>
    <bind column="conditionParams" to="conditionParams"/>
  </input>

  <!-- 3. Groupe, avec les rôles de l'étape 1 -->
  <input file="group.csv" separator=";" type="com.axelor.auth.db.Group"
    search="self.code = :code">
    <bind column="code" to="code"/>
    <bind column="name" to="name"/>
    <bind to="technicalStaff" eval="false"/>
    <bind column="roles" to="roles" search="self.name in :roles"
      eval="roles.tokenize('|')"/>
  </input>

  <!-- 4. Menus : mise à jour des menus existants, ajout des rôles (mise à jour seule) -->
  <input file="metaMenu.csv" separator=";" type="com.axelor.meta.db.MetaMenu"
    search="self.name = :name" update="true">
    <bind column="name" to="name"/>
    <bind column="roles" to="roles" search="self.name in :roles"
      eval="roles.tokenize('|')"/>
  </input>

  <!-- 5. Affectation des utilisateurs au groupe -->
  <input file="user.csv" separator=";" type="com.axelor.auth.db.User"
    search="self.code = :code" update="true">
    <bind column="code" to="code"/>
    <bind column="group" to="group" search="self.code = :group"/>
  </input>

</csv-inputs>
```

Reprends la version du XSD depuis une configuration d'import existante de la version cible
(`data-import_8.1.xsd` ci-dessus vient d'AOP 8.2.x) et valide :
`xmllint --noout --schema <aop>/axelor-core/src/main/resources/data-import.xsd bind.xml`.

### Fichiers de données (séparateur `;`, en-tête = noms de champs Java)

```
# role.csv
name;description
role.vente;Commercial, devis et commandes

# permission.csv (booléens en x ; roleName lu par le script ImportPermission)
name;object;can_read;can_write;can_create;can_remove;can_import;can_export;condition;conditionParams;roleName
perm.vente.saleorder;com.axelor.apps.sale.db.SaleOrder;x;x;x;;;x;;;role.vente
perm.vente.partner.r;com.axelor.apps.base.db.Partner;x;;;;;;;;role.vente

# group.csv (roles séparés par |)
code;name;roles
VTE;Commercial;role.vente

# metaMenu.csv (un menu existant + les rôles à lui donner)
name;roles
sale-root;role.vente
sale-quotations;role.vente

# user.csv
code;name;group
jdupont;Jean Dupont;VTE
```

Ces fichiers suivent le nommage de l'exemple partenaire ; sur un projet AxENR, applique les
conventions de `conception.md` (`perm.cli.*`, `CLI - <Métier>`, `cli_<profil>`).

`canImport` existe dans le domaine même si le formulaire Permission d'AOP 8.2.3 ne l'affiche pas :
lie-le explicitement si la matrice distingue l'import. Avant d'utiliser `condition`, lis
`permissions-conditionnelles.md` : création imbriquée et import ne sont pas filtrés par ligne, et
l'export suit le filtre de lecture.

Empaquetage : ZIP avec les fichiers à la racine (`zip -j data.zip *.csv`), ou chargement fichier
par fichier.

### Menus par l'import : centré sur le rôle, mise à jour seule

L'import accorde la visibilité par `MetaMenu.roles` (`meta_menu_roles`, côté propriétaire, règle
d'or 7). Comme les rôles sont attachés au groupe (étape 3), tous les membres héritent de la
visibilité. Le `update="true"` sur `MetaMenu` est voulu : les menus existent déjà, on ne fait
qu'ajouter des rôles. Conséquence : un nom de menu mal orthographié est ignoré **sans erreur**.

Pour accorder par groupe plutôt que par rôle (contraire à la convention AxENR, voir
`conception.md`) :

```xml
<bind column="groups" to="groups" search="self.code in :groups"
  eval="groups.tokenize('|')"/>
```

### Permissions de champ par l'import

Extension du même mécanisme (les configurations de rôles AOS n'en livrent pas) : attacher une
`MetaPermission` et ses règles à `Role.metaPermissions`.

```xml
<input file="metaPermission.csv" separator=";"
  type="com.axelor.meta.db.MetaPermission" search="self.name = :name">
  <bind column="name" to="name"/>
  <bind column="object" to="object"/>
  <bind to="active" eval="true"/>
  <bind column="fieldName" to="rules" search="self.metaPermission.name = :name
    AND self.field = :fieldName">
    <bind column="fieldName" to="field"/>
    <bind to="canRead"  eval="can_read  == 'x' ? 'true' : 'false'"/>
    <bind to="canWrite" eval="can_write == 'x' ? 'true' : 'false'"/>
  </bind>
</input>
```

Puis un input `Role` qui lie `metaPermissions` (`search="self.name in :metaPermissions"`).
`active = true` est obligatoire pour que les règles s'appliquent.

### Idempotence, réimport, nettoyage

- Les clés de `search` (`Role.name`, `Group.code`, `Permission.name`, `MetaMenu.name`,
  `User.code`) **sont** les clés d'idempotence : réimporter met à jour sur ces clés naturelles.
  Pas besoin d'`importId` pour les entités de droits dans ce canal.
- **Pas de `update="true"`** sur Role, Permission, Group : le `search` seul donne un vrai upsert ;
  avec `update="true"`, une première création serait ignorée en silence. Réservé à `MetaMenu`
  (menus préexistants) et à l'affectation des `User` existants.
- Rappel : un import ne retire jamais un lien. Retirer un rôle d'une liste `roles`, ou une ligne de
  `permission.csv`, puis réimporter ne détache rien (les liaisons de collection ne font
  qu'ajouter, AOP 8.2.3). Détacher explicitement, puis vérifier avec un compte non admin.
- `Role.archived = true` n'est pas une révocation prouvée : `AuthResolver` et `MenuChecker`
  (AOP 8.2.3) ne testent pas ce drapeau.

### Pièges propres au profil

| # | Piège | Symptôme | Parade |
|---|---|---|---|
| IP1 | `update="true"` sur Role, Permission ou Group | Le premier import n'insère rien (`Non vide : 0`) | `search` seul ; `update="true"` uniquement sur MetaMenu et User |
| IP2 | Nom de menu mal orthographié | Menu ignoré en silence, absent de la navigation | Vérifier que `Non vide` égale le nombre de lignes de menus ; contrôler contre `meta_menu.name` |
| IP3 | Permission importée avant son rôle | Permission rattachée à rien : refus malgré le menu visible | Input Role avant l'input Permission |
| IP4 | Menu accordé au rôle, mais rôle absent du groupe ou de l'utilisateur | Menu toujours masqué | `Group.roles` (étape 3) ou `User.roles` doit porter le rôle |
| IP5 | Nom de rôle dans `roleName` ou `roles` absent de `role.csv` | Permission orpheline ou menu partiellement accordé, sans erreur | Recouper l'orthographe de chaque nom de rôle |
| IP6 | Permission présente, menu non accordé (ou l'inverse) | Refus au clic, ou écran inatteignable | Les deux contrôles sont indépendants : accorder la permission **et** le menu |
| IP7 | Booléens écrits `true` / `1` alors que le binding attend `x` | Toutes les cases à faux | Respecter la convention `eval="… == 'x'"`, ou changer l'`eval` |
| IP8 | `technicalStaff = true` pour « réparer » une navigation vide | Faille ; la navigation dépend toujours des liens de menus | Jamais ; poser les rôles de menus correctement |
| IP9 | Modifier `auth_user`, permissions ou menus en SQL pendant que l'application tourne | Changement invisible (connexion refusée, navigation inchangée) : l'entité est servie par le cache Hibernate de niveau 2 | Passer par l'application (import, interface, REST), ou redémarrer Tomcat. Un utilisateur créé par l'API est `blocked = true` par défaut : le débloquer |
| IP10 | Réexécuter un input utilisateur dont le `search` trouve le compte, avec une colonne `password` liée | Le compte est réécrit, mot de passe compris | Lier le mot de passe avec `if-empty="true"`, ou l'exclure des réexécutions. Rappel AxENR : jamais de mot de passe dans un fichier (règle 9) |
| IP11 | Retirer un rôle d'une liste, ou une ligne de `permission.csv`, puis réimporter | Rien n'est détaché | Détachement explicite, puis vérification non admin |

### Vérification

1. Valider `bind.xml` contre le XSD.
2. **Jouer d'abord sur une instance de test locale**, jamais en première chez le partenaire.
3. **Lire `Non vide`, pas `Réussi`** : il doit égaler le nombre de lignes attendu pour chaque input.
   `Non vide : 0` sans anomalie = ignoré en silence (IP1, IP2). Exemple constaté : un nom de menu
   inexistant donne `Total : 5 - Réussi : 5 - Non vide : 4 - Anomalies : 0`.
4. Recharger les métadonnées, puis **redémarrer Tomcat immédiatement**, puis rafraîchir le
   navigateur (voir `diagnostic.md`, « Caches et reconnexion », et l'avertissement sur
   « Tout restaurer… »).
5. Requêtes Q1 à Q3 (`recettes-sql.md`) pour un utilisateur représentatif, et `scripts/audit.sql`.
6. Connexion avec un compte cible, parcours des menus accordés et des refus attendus.
7. Seulement ensuite, livrer le bundle avec une note d'installation qui inclut l'étape
   « recharger puis redémarrer Tomcat », et son motif.

## Le cas des menus

`MetaMenu.name` n'est **pas unique** : les surcharges par module créent des homonymes, parfois
trois pour un même nom. Compte-les avant de choisir ta clé :

```sql
SELECT name, COUNT(*), string_agg(COALESCE(module,'(sans module)'), ', ')
FROM meta_menu GROUP BY name HAVING COUNT(*) > 1;
```

S'il y a des homonymes, une recherche par `name` cible le mauvais menu ou en crée un fantôme.
Utilise alors le canal Excel, qui résout par `importId`.

Et applique la fermeture transitive des ancêtres : voir règle d'or 6.

## Renommer un groupe ou un rôle existant

Un import recherche par clé naturelle. On ne peut pas chercher sur une clé et la remplacer dans la
même passe. Deux options, à annoncer clairement :

1. L'import change le **libellé**, le changement de **code** reste une action manuelle.
2. Le canal CSV permet de figer la recherche sur l'ancienne valeur dans le XML, et de porter la
   nouvelle dans le fichier.

Dans les deux cas, rappelle que renommer une clé naturelle casse les imports ultérieurs qui s'y
référaient.

## Avant de rendre la main

- Chaque classe citée dans `object` existe dans `meta_model`, jokers mis à part.
- Aucune clé M2M orpheline : tout ce qui est référencé existe, dans le fichier ou en base.
- Aucun doublon de `name` ou de `code`.
- Le côté propriétaire est respecté pour chaque M2M.
- Un état des lieux a été exporté avant l'import, et un moyen de revenir en arrière est fourni.
- Les actions manuelles restantes sont listées, avec la requête qui permet de les vérifier.
