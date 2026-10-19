-- =====================================================================
-- Axelor : kit d'audit des droits. LECTURE SEULE.
-- Aucune requête ci-dessous ne modifie quoi que ce soit.
-- `group` est un mot réservé PostgreSQL : toujours écrire u."group".
-- Confirmer le schéma avec la requête 0 avant d'exécuter les suivantes :
-- les noms de colonnes des tables de jointure ne suivent pas une convention unique.
-- =====================================================================

-- 0. CONFIRMER LE SCHÉMA. À exécuter en premier, toujours.
SELECT table_name, string_agg(column_name, ', ' ORDER BY ordinal_position) AS colonnes
FROM information_schema.columns
WHERE table_name LIKE 'auth\_%' OR table_name LIKE 'meta\_permission%'
   OR table_name IN ('meta_menu_roles','meta_menu_groups','meta_view_groups')
GROUP BY table_name ORDER BY table_name;

-- =====================================================================
-- ÉTAT DES LIEUX
-- =====================================================================

-- 1. Matrice complète : groupe -> rôle -> permission -> objet -> CRUD -> condition
SELECT g.code AS groupe, r.name AS role, p.name AS permission, p.object,
       p.can_read, p.can_write, p.can_create, p.can_remove, p.can_export,
       p.condition_value, p.condition_params
FROM auth_group g
LEFT JOIN auth_group_roles gr ON gr.auth_group = g.id
LEFT JOIN auth_role r ON r.id = gr.roles
LEFT JOIN auth_role_permissions rp ON rp.auth_role = r.id
LEFT JOIN auth_permission p ON p.id = rp.permissions
ORDER BY g.code, r.name, p.object;

-- 2. Droits effectifs d'un utilisateur donné. Paramètre : son code.
SELECT p.object, p.name AS permission,
       bool_or(p.can_read) AS lire, bool_or(p.can_write) AS ecrire,
       bool_or(p.can_create) AS creer, bool_or(p.can_remove) AS supprimer,
       bool_or(p.can_export) AS exporter,
       string_agg(DISTINCT p.condition_value, ' | ') AS conditions
FROM auth_user u
LEFT JOIN auth_group g ON g.id = u."group"
LEFT JOIN auth_group_roles gr ON gr.auth_group = g.id
LEFT JOIN auth_user_roles ur ON ur.auth_user = u.id
LEFT JOIN auth_role r ON r.id = gr.roles OR r.id = ur.roles
LEFT JOIN auth_role_permissions rp ON rp.auth_role = r.id
LEFT JOIN auth_permission p ON p.id = rp.permissions
WHERE u.code = :code_utilisateur
GROUP BY p.object, p.name ORDER BY p.object;

-- 3. Qui peut lire, écrire ou supprimer un modèle donné.
--    Prend en compte le joker du package exact : c'est le seul qui s'applique.
SELECT DISTINCT g.code AS groupe, r.name AS role, p.name AS permission,
       p.can_read, p.can_write, p.can_remove, p.condition_value
FROM auth_permission p
JOIN auth_role_permissions rp ON rp.permissions = p.id
JOIN auth_role r ON r.id = rp.auth_role
LEFT JOIN auth_group_roles gr ON gr.roles = r.id
LEFT JOIN auth_group g ON g.id = gr.auth_group
WHERE p.object = :classe_complete
   OR p.object = regexp_replace(:classe_complete, '\.[^.]+$', '.*')
ORDER BY g.code, r.name;

-- 4. Volumétrie par rôle : permissions, dont écriture et suppression, et menus.
--    Un rôle nommé "Read" avec des droits d'écriture est une anomalie de nommage.
SELECT r.name AS role,
       COUNT(DISTINCT rp.permissions) AS permissions,
       COUNT(DISTINCT p.id) FILTER (WHERE p.can_write)  AS en_ecriture,
       COUNT(DISTINCT p.id) FILTER (WHERE p.can_remove) AS en_suppression,
       (SELECT COUNT(*) FROM meta_menu_roles mr WHERE mr.roles = r.id) AS menus,
       (SELECT COUNT(*) FROM auth_group_roles x WHERE x.roles = r.id)  AS groupes
FROM auth_role r
LEFT JOIN auth_role_permissions rp ON rp.auth_role = r.id
LEFT JOIN auth_permission p ON p.id = rp.permissions
GROUP BY r.id, r.name ORDER BY r.name;

-- 5. Utilisateurs, groupe, rôles directs, état.
SELECT u.code, u.name, g.code AS groupe,
       string_agg(r.name, ' | ' ORDER BY r.name) AS roles_directs,
       u.blocked, u.archived
FROM auth_user u
LEFT JOIN auth_group g ON g.id = u."group"
LEFT JOIN auth_user_roles ur ON ur.auth_user = u.id
LEFT JOIN auth_role r ON r.id = ur.roles
GROUP BY u.code, u.name, g.code, u.blocked, u.archived ORDER BY u.code;

-- =====================================================================
-- ANOMALIES. Chaque requête doit idéalement ne rien renvoyer.
-- =====================================================================

-- 6. Permission visant un objet inexistant. Jokers exclus.
SELECT p.name, p.object FROM auth_permission p
LEFT JOIN meta_model m ON m.full_name = p.object
WHERE m.id IS NULL AND p.object NOT LIKE '%*';

-- 7. Permissions orphelines : rattachées à aucun rôle, groupe ni utilisateur.
SELECT p.name, p.object FROM auth_permission p
WHERE p.id NOT IN (SELECT permissions FROM auth_role_permissions)
  AND p.id NOT IN (SELECT permissions FROM auth_group_permissions)
  AND p.id NOT IN (SELECT permissions FROM auth_user_permissions);

-- 8. Rôles vides : aucune permission.
SELECT r.name FROM auth_role r
LEFT JOIN auth_role_permissions rp ON rp.auth_role = r.id
GROUP BY r.id, r.name HAVING COUNT(rp.permissions) = 0;

-- 9. Droits qui contournent la chaîne groupe -> rôle.
SELECT 'permission sur groupe' AS type, g.code AS cle, p.name AS droit
FROM auth_group g JOIN auth_group_permissions gp ON gp.auth_group = g.id
JOIN auth_permission p ON p.id = gp.permissions
UNION ALL
SELECT 'permission sur utilisateur', u.code, p.name
FROM auth_user u JOIN auth_user_permissions up ON up.auth_user = u.id
JOIN auth_permission p ON p.id = up.permissions
UNION ALL
SELECT 'role sur utilisateur', u.code, r.name
FROM auth_user u JOIN auth_user_roles ur ON ur.auth_user = u.id
JOIN auth_role r ON r.id = ur.roles;

-- 10. Doublons de clés naturelles.
SELECT 'permission' AS type, name, COUNT(*) FROM auth_permission GROUP BY name HAVING COUNT(*) > 1
UNION ALL SELECT 'role', name, COUNT(*) FROM auth_role GROUP BY name HAVING COUNT(*) > 1
UNION ALL SELECT 'groupe', code, COUNT(*) FROM auth_group GROUP BY code HAVING COUNT(*) > 1;

-- 11. Permissions en doublon fonctionnel : même objet, mêmes droits, noms différents.
SELECT p.object, p.can_read, p.can_write, p.can_create, p.can_remove, p.can_export,
       COUNT(*) AS nb, string_agg(p.name, ' | ' ORDER BY p.name) AS noms
FROM auth_permission p WHERE COALESCE(p.condition_value,'') = ''
GROUP BY p.object, p.can_read, p.can_write, p.can_create, p.can_remove, p.can_export
HAVING COUNT(*) > 1 ORDER BY nb DESC;

-- 12. Utilisateurs métier dans le groupe qui contourne tous les droits.
SELECT u.code, u.name FROM auth_user u JOIN auth_group g ON g.id = u."group"
WHERE g.code = 'admins';

-- 13. Utilisateurs sans groupe, ou bloqués, ou hors période d'autorisation.
SELECT u.code, u.name, u."group" IS NULL AS sans_groupe, u.blocked,
       u.activate_on, u.expires_on
FROM auth_user u
WHERE u."group" IS NULL OR u.blocked OR u.expires_on < now() OR u.activate_on > now();

-- =====================================================================
-- MENUS
-- =====================================================================

-- 14. Menus homonymes : empêchent toute recherche fiable par nom à l'import.
SELECT name, COUNT(*) AS nb, string_agg(COALESCE(module,'(sans module)'), ', ') AS modules
FROM meta_menu GROUP BY name HAVING COUNT(*) > 1 ORDER BY nb DESC;

-- 15. Menus RACINES sans rôle ni groupe : visibles du seul administrateur.
--     Si un module du périmètre apparaît ici, il est invisible pour tous les utilisateurs.
SELECT m.id, m.title, m.name FROM meta_menu m
WHERE m.parent IS NULL
  AND NOT EXISTS (SELECT 1 FROM meta_menu_roles  x WHERE x.menus = m.id)
  AND NOT EXISTS (SELECT 1 FROM meta_menu_groups y WHERE y.meta_menu_id = m.id)
ORDER BY m.title;

-- 16. Menus ENFANTS sans rôle ni groupe : visibles de tout le monde.
SELECT COUNT(*) AS menus_ouverts_a_tous FROM meta_menu m
WHERE m.parent IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM meta_menu_roles  x WHERE x.menus = m.id)
  AND NOT EXISTS (SELECT 1 FROM meta_menu_groups y WHERE y.meta_menu_id = m.id);

-- 17. Chaîne d'ancêtres cassée : un menu porte un rôle qu'aucun de ses ancêtres ne porte,
--     donc il n'apparaîtra jamais. C'est la cause n°1 des menus fantômes.
WITH RECURSIVE chaine(feuille, courant, role) AS (
  SELECT m.id, m.parent, mr.roles
  FROM meta_menu m JOIN meta_menu_roles mr ON mr.menus = m.id
  WHERE m.parent IS NOT NULL
  UNION ALL
  SELECT c.feuille, p.parent, c.role
  FROM chaine c JOIN meta_menu p ON p.id = c.courant
)
SELECT DISTINCT m.id, m.title, r.name AS role_sans_ancetre
FROM chaine c
JOIN meta_menu m ON m.id = c.feuille
JOIN auth_role r ON r.id = c.role
WHERE c.courant IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM meta_menu_roles x WHERE x.menus = c.courant AND x.roles = c.role)
  AND NOT EXISTS (SELECT 1 FROM meta_menu_groups y WHERE y.meta_menu_id = c.courant)
ORDER BY m.title;

-- 18. Menus visibles par un groupe donné, via ses rôles ou en direct.
SELECT DISTINCT m.id, m.title, COALESCE(pm.title, '(racine)') AS parent
FROM meta_menu m LEFT JOIN meta_menu pm ON pm.id = m.parent
WHERE m.id IN (SELECT mr.menus FROM meta_menu_roles mr
               JOIN auth_group_roles gr ON gr.roles = mr.roles
               JOIN auth_group g ON g.id = gr.auth_group WHERE g.code = :code_groupe)
   OR m.id IN (SELECT mg.meta_menu_id FROM meta_menu_groups mg
               JOIN auth_group g ON g.id = mg.group_id WHERE g.code = :code_groupe)
ORDER BY parent, m.title;

-- 19. Comparer deux groupes : ce que l'un a et pas l'autre.
--     Rappel : la différence visible est rarement la cause d'un écart constaté.
SELECT 'role' AS type, r.name AS element,
       bool_or(g.code = :groupe_a) AS dans_a, bool_or(g.code = :groupe_b) AS dans_b
FROM auth_group g JOIN auth_group_roles gr ON gr.auth_group = g.id
JOIN auth_role r ON r.id = gr.roles
WHERE g.code IN (:groupe_a, :groupe_b)
GROUP BY r.name HAVING NOT (bool_or(g.code = :groupe_a) AND bool_or(g.code = :groupe_b))
ORDER BY element;

-- 20. Permissions et meta permissions conditionnées, avec leurs paramètres.
SELECT p.name, p.object, p.condition_value, p.condition_params,
       string_agg(r.name, ' | ') AS portee_par
FROM auth_permission p
LEFT JOIN auth_role_permissions rp ON rp.permissions = p.id
LEFT JOIN auth_role r ON r.id = rp.auth_role
WHERE COALESCE(p.condition_value, '') <> ''
GROUP BY p.name, p.object, p.condition_value, p.condition_params ORDER BY p.object;

-- 21. Objets conditionnés menacés par une permission sans condition sur le même modèle.
--     Voir règle d'or 4 : la permission sans condition l'emporte et annule la restriction.
SELECT c.object,
       string_agg(DISTINCT c.name, ' | ') AS permissions_conditionnees,
       string_agg(DISTINCT n.name, ' | ') AS permissions_sans_condition
FROM auth_permission c
JOIN auth_permission n ON n.object = c.object AND COALESCE(n.condition_value,'') = ''
WHERE COALESCE(c.condition_value,'') <> ''
GROUP BY c.object ORDER BY c.object;
