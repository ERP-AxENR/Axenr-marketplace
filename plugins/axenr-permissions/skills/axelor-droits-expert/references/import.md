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
  toute création est une anomalie : contrôle en amont que chaque clé existe.
- L'échappement du pipe dans `split` varie selon les versions.
- Une colonne présente dans le CSV mais vide peut écraser une valeur obligatoire. N'inclus pas les
  colonnes que tu ne veux pas toucher.

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
