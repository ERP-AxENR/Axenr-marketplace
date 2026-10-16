# Modèle de données des droits

## Entités

| Classe | Table | Clé naturelle | Rôle |
|---|---|---|---|
| `com.axelor.auth.db.User` | `auth_user` | `code` (login) | Un seul groupe, N rôles, N permissions directes |
| `com.axelor.auth.db.Group` | `auth_group` | `code` et `name`, uniques | Profil d'accueil. Porte des rôles |
| `com.axelor.auth.db.Role` | `auth_role` | `name`, unique | Paquet cumulable : permissions + menus |
| `com.axelor.auth.db.Permission` | `auth_permission` | `name`, unique | Droit CRUD + export sur un objet |
| `com.axelor.meta.db.MetaPermission` | `meta_permission` | `name` | Conteneur de droits au champ |
| `com.axelor.meta.db.MetaPermissionRule` | `meta_permission_rule` | (`metaPermission`, `field`) | Une règle par champ |
| `com.axelor.meta.db.MetaMenu` | `meta_menu` | `name` **non unique** | Visibilité des menus |
| `com.axelor.meta.db.MetaView` | `meta_view` | `name` **non unique** | Visibilité des vues |
| `com.axelor.meta.db.MetaModel` | `meta_model` | `full_name` | Référentiel, sert à valider `Permission.object` |

## Chaîne principale

```
auth_user ──> auth_group ──> auth_group_roles ──> auth_role ──> auth_role_permissions ──> auth_permission
```

Trois chemins secondaires existent et doivent être audités : permissions directes sur
l'utilisateur, permissions directes sur le groupe, rôles directs sur l'utilisateur.
Les trois contournent la chaîne et deviennent invisibles dans un audit par rôle.
Règle de conception : les éviter.

## Ne jamais supposer un nom de colonne

Le nommage des tables de jointure n'est pas homogène. Exemples relevés :

| Table de jointure | Colonnes réelles |
|---|---|
| `auth_group_roles` | `auth_group`, `roles` |
| `auth_group_permissions` | `auth_group`, `permissions` |
| `auth_role_permissions` | `auth_role`, `permissions` |
| `meta_menu_groups` | `meta_menu_id`, `group_id` |
| `meta_menu_roles` | `menus`, `roles` |

`meta_menu_groups` utilise le suffixe `_id`, `meta_menu_roles` non. Toute requête d'audit part de
`information_schema.columns`, jamais d'une convention supposée.

`group` est un mot réservé PostgreSQL : écrire `u."group"`.

## Champs de Permission

| Champ | Notes |
|---|---|
| `name` | Clé naturelle, unique, obligatoire |
| `object` | Classe complète, ou joker de package `a.b.db.*`. Voir règle d'or 2 |
| `canRead` `canWrite` `canCreate` `canRemove` `canExport` `canImport` | Booléens |
| `condition` | Filtre JPQL, `self` désigne l'enregistrement |
| `conditionParams` | Paramètres positionnels, un `?` par paramètre, séparés par des virgules |

Codification usuelle des niveaux : `r`, `re`, `rw`, `rwc`, `rwce`, `rwcd`, `rwcde`.
Le nom de la permission doit refléter son contenu : un objet nommé `.r` qui autorise la suppression
est un mensonge qui se paiera lors du prochain audit.

## Côtés propriétaires des M2M

| Relation | Propriétaire | Ne jamais importer sur |
|---|---|---|
| Rôle ↔ menu | `MetaMenu.roles` | `Role.menus` |
| Groupe ↔ menu | `MetaMenu.groups` | `Group.menus` |
| Rôle ↔ permission | `Role.permissions` | — |
| Groupe ↔ rôle | `Group.roles` | — |

Vérification : le côté portant `mappedBy` dans le domaine XML est l'inverse.
Un import sur le côté inverse ne persiste rien, **sans lever d'erreur**.

## Attributs de groupe à connaître

| Champ | Effet |
|---|---|
| `code` | Clé de recherche. La valeur `admins` contourne tous les droits, en dur |
| `technicalStaff` | Ouvre des fonctions techniques. À réserver aux administrateurs |
| `viewCustomizationPermission` | Autorise la personnalisation des vues |
| `homeAction` | Écran d'accueil du profil |
| `navigation` | Mode d'affichage du menu |

## Le piège low-code

Studio, les imports et la saisie en administration créent des permissions, des rôles, des menus et
des champs qui n'existent nulle part dans le dépôt. Les tables à regarder en plus :
`meta_json_field_roles`, `meta_json_model_roles`, `meta_attrs_roles`, `studio_studio_menu_roles`,
`studio_studio_menu_groups`, `dms_permission`.

Par ailleurs, de nombreuses tables métier portent des noms en `*_authorized_role_set`.
Elles ne relèvent **pas** du moteur de sécurité : ce sont des règles métier applicatives.
Ne les confonds pas avec des droits, et dis-le explicitement dans tes livrables.
