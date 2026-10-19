# Recettes SQL : créer, cloner, diagnostiquer un profil

> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3
> (conditions vérifiées en 9.1.1 / 8.2.3). AxENR tourne sur AOP 7.4 / AOS 8.x : à vérifier sur la
> version cible.

Voie SQL directe : réservée à une base que tu maîtrises (démo, instance jetable). Pour une
instance partenaire ou client, utilise le bundle d'import (`import.md`). Toute écriture exige un
GO explicite, jamais en production (SKILL.md, « Écriture »). Avant de scripter, le cadrage de
`cadrage-profils.md` doit être validé.

**Toujours confirmer le schéma avant d'écrire** : requête 0 de `scripts/audit.sql`. Les noms de
colonnes des tables de jointure ne suivent pas une convention unique (`modele-donnees.md`).

## Convention de rattachement des menus : deux positions

| Source | Position | Contexte |
|---|---|---|
| Ce skill (convention AxENR) | Permissions **et** menus sur le **rôle**, jamais sur le groupe (`conception.md`) | Audit par rôle, mutualisation entre groupes |
| Apport partenaire | « Groupe = portée, rôle = permission » : les menus sur le **groupe** (`meta_menu_groups`), les permissions sur le rôle, comme les groupes standard des données de démo AOS | Voie SQL rapide sur une démo |

Les deux fonctionnent pour le moteur (règles b et c de `MenuChecker`, voir `moteur-evaluation.md`).
Sur un projet AxENR, **garde la convention du skill** : utilise la recette « menus sur un rôle »
ci-dessous. La recette sur le groupe reste utile pour une démo jetable, ou pour comprendre une
instance configurée ainsi.

## La recette en 5 étapes

1. **Groupe** : `INSERT INTO auth_group` (code unique, `technical_staff = false`).
2. **Rôle(s)** : `INSERT INTO auth_role`, puis rattachement au groupe par `auth_group_roles`.
3. **Permissions objet** : `INSERT INTO auth_permission` (classe complète ou joker, `can_*`),
   rattachées au rôle par `auth_role_permissions`.
4. **Permissions de champ** (optionnel) : `meta_permission` (une par objet) et
   `meta_permission_rule` (une ligne par champ restreint), rattachées au rôle par
   `auth_role_meta_permissions`.
5. **Menus** : liens menu ↔ rôle (`meta_menu_roles`) ou menu ↔ groupe (`meta_menu_groups`).
   **C'est l'étape la plus oubliée** : sans elle, la barre de navigation est vide.

Puis invalider les caches (voir `diagnostic.md`, « Caches et reconnexion »). Résoudre les vrais
identifiants par requête : jamais d'identifiant inventé.

## Menus sur un rôle (idempotent, sous-arbre)

PK de `meta_menu_roles` : (`menus`, `roles`).

```sql
WITH RECURSIVE subtree AS (
  SELECT id FROM meta_menu WHERE id IN (:roots)
  UNION ALL
  SELECT m.id FROM meta_menu m JOIN subtree s ON m.parent = s.id
)
INSERT INTO meta_menu_roles (menus, roles)
SELECT s.id, :role_id
FROM subtree s
WHERE EXISTS (SELECT 1 FROM meta_menu_groups WHERE meta_menu_id = s.id)
   OR EXISTS (SELECT 1 FROM meta_menu_roles  WHERE menus        = s.id)
ON CONFLICT (menus, roles) DO NOTHING;
```

La clause `WHERE EXISTS` ne vise que les menus déjà restreints : un menu enfant sans groupe ni
rôle est déjà visible de tous (règle d'or 5). Le `WITH RECURSIVE` descend le sous-arbre ; la règle
d'or 6 (chaîne d'ancêtres) reste à contrôler vers le haut quand tu accordes une feuille isolée.

Pour cibler par nom plutôt que par identifiant : `WHERE m.name IN ('crm-root', 'menu-mail', …)`,
après avoir compté les homonymes (`import.md`, « Le cas des menus »).

## Menus sur un groupe (alternative, démo)

PK de `meta_menu_groups` : (`meta_menu_id`, `group_id`).

```sql
WITH RECURSIVE subtree AS (
  SELECT id FROM meta_menu WHERE id IN (:roots)
  UNION ALL
  SELECT m.id FROM meta_menu m JOIN subtree s ON m.parent = s.id
)
INSERT INTO meta_menu_groups (meta_menu_id, group_id)
SELECT s.id, :gid
FROM subtree s
WHERE EXISTS (SELECT 1 FROM meta_menu_groups WHERE meta_menu_id = s.id)
   OR EXISTS (SELECT 1 FROM meta_menu_roles  WHERE menus        = s.id)
ON CONFLICT (meta_menu_id, group_id) DO NOTHING;
```

## Nettoyage

```sql
-- Retirer les menus d'un groupe
DELETE FROM meta_menu_groups WHERE group_id = :gid;

-- Retirer les permissions d'un rôle
DELETE FROM auth_role_permissions WHERE auth_role = :role_id;

-- Suppression complète d'un groupe (à manier avec soin, non idempotent)
BEGIN;
DELETE FROM meta_menu_groups WHERE group_id = :gid;
DELETE FROM auth_group_roles WHERE auth_group = :gid;
DELETE FROM auth_group_permissions WHERE auth_group = :gid;
UPDATE auth_user SET group_id = NULL WHERE group_id = :gid;  -- ou réaffecter
DELETE FROM auth_group WHERE id = :gid;
COMMIT;
```

Attention : la colonne de groupe de `auth_user` s'appelle `group_id` dans la recette partenaire
(AOP 8.2.x) et `"group"` dans `scripts/audit.sql`. Confirme avec la requête 0 avant d'exécuter.

## Cloner un profil

Après avoir inséré le nouveau groupe `:dst_gid` :

```sql
INSERT INTO meta_menu_groups (meta_menu_id, group_id)
SELECT meta_menu_id, :dst_gid FROM meta_menu_groups WHERE group_id = :src_gid
ON CONFLICT DO NOTHING;

INSERT INTO auth_group_roles (auth_group, roles)
SELECT :dst_gid, roles FROM auth_group_roles WHERE auth_group = :src_gid
ON CONFLICT DO NOTHING;

INSERT INTO auth_group_permissions (auth_group, permissions)
SELECT :dst_gid, permissions FROM auth_group_permissions WHERE auth_group = :src_gid
ON CONFLICT DO NOTHING;
```

Les liens menu ↔ groupe sont propres à chaque groupe : un clone sans la première requête a une
barre de navigation vide.

## Permissions de champ (exemples)

L'`id` vient de la séquence de la table : vérifie-le sur la base cible (`\d meta_permission_rule`)
et ajoute la colonne `id` s'il n'y a pas de valeur par défaut.

```sql
-- Masquer un champ
INSERT INTO meta_permission_rule (meta_permission, field, can_read, can_write)
VALUES (:meta_perm_id, 'salePrice', false, false);

-- Champ visible mais verrouillé
INSERT INTO meta_permission_rule (meta_permission, field, can_read, can_write, can_export)
VALUES (:meta_perm_id, 'creditLimit', true, false, true);

-- Lecture seule conditionnelle (Groovy)
INSERT INTO meta_permission_rule (meta_permission, field, can_read, can_write, readonly_if)
VALUES (:meta_perm_id, 'amountTotal', true, true, 'statusSelect == 3');

-- Masquage conditionnel (expression Groovy dans une chaîne SQL : guillemets internes doublés)
INSERT INTO meta_permission_rule (meta_permission, field, can_read, can_write, hide_if)
VALUES (:meta_perm_id, 'commercialMargin', true, true, '!(__user__.group?.code in [''VTE'',''ERP''])');

-- Sans cela, les règles sont ignorées
UPDATE meta_permission SET active = true WHERE id = :meta_perm_id;
```

## Menus racines courants (AOS 8.5.x)

Les identifiants changent d'une base à l'autre : toujours chercher par `name`. Vérifier sur toute
nouvelle instance : `SELECT name, title FROM meta_menu WHERE parent IS NULL ORDER BY name`.

| Usage | Nom du menu |
|---|---|
| Messagerie | `menu-mail` |
| GED | `menu-dms` |
| Équipe et tâches | `menu-team`, `menu-team-tasks-due/todo/open/created` |
| Calendrier | `menu-calendar` |
| Projets | `menu-project-root` |
| Mes projets | `menu-my-project-root` |
| Facturation | `invoice-root` |
| Comptabilité | `account-root` |
| RH | `hr-root` |
| Mon espace RH | `my-hr-root` |
| CRM | `crm-root` |
| Ventes | `sc-root-sale` |
| Achats | `sc-root-purchase` |
| Stock | `stock-root` |
| Production | `manufacturing-root` |
| Qualité | `menu-quality-root` |
| Helpdesk | `helpdesk-root` |
| Maintenance | `maintenance-root` |
| Marketing | `marketing-root` |
| Flotte | `fleet-root` |
| Contrats | `contracts-root` |
| Budget | `budget-root-budget-management` |
| Immobilisations | `assets-management-root` |
| Trésorerie | `forecast-root` |
| Configuration applicative (admin) | `admin-root` |
| RGPD | `gdpr-root` |

Les modules spécifiques (dont ceux d'AxENR) ajoutent leurs propres racines : liste-les sur
l'instance.

## Gabarits de menus par métier (point de départ)

| Profil | Menus racines |
|---|---|
| Commercial / ADV | `crm-root`, `sc-root-sale`, `invoice-root` (lecture), `stock-root` (lecture), `menu-project-root`, `menu-mail`, `menu-dms`, `menu-team`, `menu-calendar`, `menu-my-project-root` |
| Magasinier | `stock-root`, `menu-mail`, `menu-dms`, `menu-team`, `menu-calendar`, `menu-my-project-root` |
| Comptable | `account-root`, `invoice-root`, `stock-root` (lecture), `menu-mail`, `menu-dms`, `menu-team`, `menu-calendar`, `menu-my-project-root` |
| Acheteur | `sc-root-purchase`, `stock-root`, `menu-mail`, `menu-dms`, `menu-team`, `menu-calendar`, `menu-my-project-root` |
| Atelier / production | `manufacturing-root`, `menu-quality-root`, `stock-root`, `menu-mail`, `menu-dms`, `menu-team`, `menu-calendar`, `menu-my-project-root` |
| Bureau d'études | `manufacturing-root`, `menu-quality-root`, `sc-root-sale` (lecture), `menu-project-root`, `menu-mail`, `menu-dms`, `menu-team`, `menu-calendar` |
| Chef de projet | `menu-project-root`, `sc-root-sale`, `manufacturing-root`, `menu-mail`, `menu-dms`, `menu-team`, `menu-calendar` |

Un gabarit n'est pas un périmètre validé : il alimente la discussion de cadrage.

## Requêtes de diagnostic

À lancer **avant** de soupçonner un cache. Complètent `scripts/audit.sql`.

### Q1 : nombre de menus visibles par un utilisateur

```sql
WITH user_ctx AS (
  SELECT u.code AS user_code, g.code AS group_code,
    (SELECT array_agg(rname) FROM (
       SELECT r.name AS rname FROM auth_user_roles ur JOIN auth_role r ON r.id = ur.roles
       WHERE ur.auth_user = u.id
       UNION
       SELECT r.name AS rname FROM auth_group_roles gr JOIN auth_role r ON r.id = gr.roles
       WHERE gr.auth_group = u.group_id
    ) sub) AS user_roles
  FROM auth_user u LEFT JOIN auth_group g ON u.group_id = g.id
  WHERE u.id = :uid
),
menu_status AS (
  SELECT mm.id, mm.parent,
    (SELECT array_agg(g.code) FROM meta_menu_groups mg JOIN auth_group g ON g.id = mg.group_id
     WHERE mg.meta_menu_id = mm.id) AS m_groups,
    (SELECT array_agg(r.name) FROM meta_menu_roles mr JOIN auth_role r ON r.id = mr.roles
     WHERE mr.menus = mm.id) AS m_roles
  FROM meta_menu mm
)
SELECT COUNT(*) FILTER (WHERE
    (uc.user_code = 'admin' OR uc.group_code = 'admins')
    OR (ms.m_groups @> ARRAY[uc.group_code])
    OR (ms.m_roles && uc.user_roles)
    OR (ms.m_groups IS NULL AND ms.m_roles IS NULL AND ms.parent IS NOT NULL)
  ) AS visible_menus,
  COUNT(*) AS total_menus
FROM menu_status ms CROSS JOIN user_ctx uc;
```

Ce comptage ignore la chaîne d'ancêtres (règle d'or 6) et les filtres `hidden`, `moduleToCheck`,
`conditionToCheck` : c'est un majorant.

### Q2 : menus racines visibles

```sql
WITH user_ctx AS ( /* identique à Q1 */ )
SELECT mm.id, mm.name, mm.title FROM meta_menu mm CROSS JOIN user_ctx uc
WHERE mm.parent IS NULL AND (
  (uc.user_code = 'admin' OR uc.group_code = 'admins')
  OR EXISTS (SELECT 1 FROM meta_menu_groups mg JOIN auth_group g ON g.id = mg.group_id
             WHERE mg.meta_menu_id = mm.id AND g.code = uc.group_code)
  OR EXISTS (SELECT 1 FROM meta_menu_roles mr JOIN auth_role r ON r.id = mr.roles
             WHERE mr.menus = mm.id AND r.name = ANY(uc.user_roles))
)
ORDER BY mm.id;
```

Q2 ne liste que les racines. Pour les sous-menus, la référence est l'évaluation du serveur :
`GET /ws/action/menu/all` avec une session de l'utilisateur (`diagnostic.md`).

### Q3 : profil à moitié construit

```sql
SELECT g.id, g.code,
  (SELECT COUNT(*) FROM meta_menu_groups WHERE group_id = g.id) AS direct_menus,
  (SELECT COUNT(*) FROM meta_menu_roles mr WHERE mr.roles IN
     (SELECT roles FROM auth_group_roles WHERE auth_group = g.id)) AS via_role_menus,
  g.technical_staff
FROM auth_group g
ORDER BY g.id;
```

Une ligne avec `direct_menus = 0`, `via_role_menus = 0` et un code autre que `admins` : profil
cassé (`technical_staff` ne donne aucun menu).

### Q4 : permissions effectives (utilisateur, objet)

```sql
SELECT DISTINCT p.name, p.object, p.can_create, p.can_read, p.can_write, p.can_remove,
       p.condition_value, src
FROM (
  SELECT permissions, 'user_direct' AS src FROM auth_user_permissions WHERE auth_user = :uid
  UNION
  SELECT rp.permissions, 'user_role' FROM auth_user_roles ur
    JOIN auth_role_permissions rp ON rp.auth_role = ur.roles
    WHERE ur.auth_user = :uid
  UNION
  SELECT gp.permissions, 'group' FROM auth_user u
    JOIN auth_group_permissions gp ON gp.auth_group = u.group_id
    WHERE u.id = :uid
  UNION
  SELECT rp.permissions, 'group_role' FROM auth_user u
    JOIN auth_group_roles gr ON gr.auth_group = u.group_id
    JOIN auth_role_permissions rp ON rp.auth_role = gr.roles
    WHERE u.id = :uid
) all_perms
JOIN auth_permission p ON p.id = all_perms.permissions
WHERE p.object = :object_fqn
   OR p.object = regexp_replace(:object_fqn, '\.[^.]+$', '.*')
ORDER BY src;
```

Le joker est calculé depuis l'objet, exactement comme le moteur (règle d'or 2). C'est la requête
qui tranche le piège de la « lecture seule » (L3 de `cadrage-profils.md`) : aucune ligne ne doit
porter `can_write`.
