# Moteur d'évaluation des droits : les preuves

Toutes les preuves ci-dessous sont lues dans **Axelor Open Platform, tag v7.4.13**, module
`axelor-core`. Sur une autre version, revérifie avant d'affirmer.
Réserve : en édition entreprise, les classes de sécurité viennent de `axelor-core-enterprise`.
Le dépôt public sert de référence ; confronte au bytecode si un comportement diverge.

---

## 1. Aucune permission sur un modèle = refus

`com.axelor.auth.AuthSecurity#isPermitted`, lignes 166-175 :

```java
public boolean isPermitted(AccessType type, Class<? extends Model> model, Long... ids) {
  final User user = getUser();
  if (user == null) return true;                 // admin : tout permis
  final Set<Permission> permissions = authResolver.resolve(user, model.getName(), type);
  if (permissions.isEmpty()) return false;       // aucune permission : refus
  ...
```

Le refus est **par modèle et inconditionnel**. Il ne dépend pas de ce que l'utilisateur possède
sur d'autres objets.

Le contrôle est bien atteint depuis la couche REST : `com.axelor.rpc.Resource` appelle
`security.get().check(...)` sur chaque opération (une vingtaine de points d'appel : recherche,
lecture unitaire, export, création, écriture, suppression). `AuthSecurity#check` lève
`UnauthorizedException`.

**Conséquence.** Tout objet que les utilisateurs doivent atteindre a besoin d'une permission
explicite. C'est la raison d'être du socle commun de lecture.

**Croyance répandue à corriger.** On lit souvent qu'un utilisateur sans aucune permission a un
accès large, et que tout se ferme dès qu'une première permission apparaît. Le code ne fait rien
de tel : il n'existe aucun test sur « l'utilisateur possède-t-il des permissions ailleurs ».

---

## 2. Le joker ne couvre que le package exact

`com.axelor.auth.AuthResolver#filterPermissions`, lignes 73-96 :

```java
// add object permissions
for (final Permission permission : permissions)
  if (Objects.equal(object, permission.getObject()) && hasAccess(permission, type))
    all.add(permission);

// add wild card permissions
final String pkg = object.substring(0, object.lastIndexOf('.')) + ".*";
for (final Permission permission : permissions)
  if (Objects.equal(pkg, permission.getObject()) && hasAccess(permission, type))
    all.add(permission);
```

Le joker candidat est **calculé depuis l'objet demandé**, puis comparé par égalité stricte.

- `com.axelor.apps.sale.db.*` couvre `com.axelor.apps.sale.db.SaleOrder`.
- `com.axelor.apps.*` ne couvre **rien** du tout.
- `a.b.db.*` ne couvre pas `a.b.c.db.MonObjet` : packages différents.
- Un joker global n'existe pas.

**Conséquence.** Un rôle « lecture sur tout » se construit avec **une permission par package**.
Compte-les avant de promettre un délai.

---

## 3. Les droits s'additionnent, ils ne se retirent jamais

`AuthResolver#resolve`, lignes 112-137 :

```java
Set<Permission> all = filterPermissions(user.getPermissions(), object, type);
if (user.getRoles() != null)
  for (final Role role : user.getRoles())
    all.addAll(filterPermissions(role.getPermissions(), object, type));
if (user.getGroup() != null)
  all.addAll(filterPermissions(user.getGroup().getPermissions(), object, type));
if (user.getGroup() != null && user.getGroup().getRoles() != null)
  for (final Role role : user.getGroup().getRoles())
    all.addAll(filterPermissions(role.getPermissions(), object, type));
return all;
```

Quatre sources cumulées par `addAll` inconditionnel : permissions de l'utilisateur, de ses rôles,
de son groupe, des rôles de son groupe.

`filterPermissions` ne retient une permission que si `hasAccess(permission, type)` est vrai : une
case décochée n'entre pas dans l'ensemble, elle ne soustrait rien.

**Écart documentation / code.** Le javadoc de cette même méthode annonce une cascade avec des
`else` : « check the permissions directly assigned to the user, **else** check permissions assigned
to the user's roles, **else**... ». Le code n'implémente aucun `else`. Le code prime.

**Conséquence.** On ne corrige pas un excès de droits en ajoutant une permission restrictive plus
proche de l'utilisateur. On retire la permission qui accorde.

---

## 4. Une permission sans condition annule une permission conditionnée

`AuthSecurity#isPermitted`, lignes 177-182 :

```java
// check whether non-conditional permissions are granted
for (Permission permission : permissions) {
  if (permission.getCondition() == null && authResolver.hasAccess(permission, type))
    return true;
}
```

La méthode sort à `true` avant même de construire le filtre.

**Conséquence.** Un profil restreint par une condition JPQL (« ne voit que ses propres
enregistrements ») perd toute restriction dès qu'un autre de ses rôles porte une permission sans
condition sur le même modèle. C'est le cas classique du rôle de dépannage ajouté pour débloquer
un utilisateur, qui lui ouvre silencieusement toutes les lignes.

Côté filtrage, `AuthSecurity#getFilter` combine les conditions par `Filter.or(filters)` : jamais
de ET entre deux permissions conditionnées.

---

## 5 et 6. Visibilité des menus

`com.axelor.meta.service.menu.MenuChecker#isAllowed`, lignes 62-65 :

```java
return AuthUtils.isAdmin(user)
    || (myGroups != null && myGroups.contains(userGroup))
    || (myRoles != null && !Collections.disjoint(userRoles, myRoles))
    || (myRoles == null && myGroups == null && item.getParent() != null);
```

Quatre cas, dans l'ordre :

| Situation | Visible par |
|---|---|
| L'utilisateur est admin | tout |
| Le menu porte le groupe de l'utilisateur | ce groupe |
| Le menu porte un des rôles de l'utilisateur | ces rôles |
| Le menu ne porte ni rôle ni groupe **et a un parent** | **tout le monde** |
| Le menu ne porte ni rôle ni groupe **et est une racine** | **l'administrateur seul** |

La dernière ligne est la subtilité qui trompe : un menu racine sans restriction est fermé,
un menu enfant sans restriction est ouvert.

`com.axelor.meta.service.menu.MenuService`, lignes 84-97 :

```java
public MenuNodeResult preChildVisit(MenuNode childNode) {
  try {
    if (checker.isAllowed(childNode.getMetaMenu())
        && checker.canShow(childNode.getMetaMenu())) {
      return MenuNodeResult.CONTINUE;
    }
  } catch (Exception e) { ... }
  return MenuNodeResult.TERMINATE;
}
```

`TERMINATE` coupe **tout le sous-arbre**.

**Conséquence.** Rattacher un menu feuille à un rôle ne suffit pas : il faut rattacher au même rôle
**tous ses ancêtres jusqu'à la racine**. Un générateur de fichier d'import doit appliquer cette
fermeture transitive automatiquement, et la contrôler.

`MenuChecker#canShow` ajoute deux filtres indépendants des droits : `hidden`, et les conditions
`moduleToCheck` / `conditionToCheck`. Un menu peut donc rester invisible malgré des droits corrects.

---

## 7. Le propriétaire du M2M menus

Domaines AOP :

```xml
<!-- Role.xml ligne 14 -->
<many-to-many name="menus" ref="com.axelor.meta.db.MetaMenu" mappedBy="roles" />

<!-- Group.xml ligne 25 -->
<many-to-many name="menus" ref="com.axelor.meta.db.MetaMenu" mappedBy="groups" />

<!-- Meta.xml, entité MetaMenu, lignes 101-102 -->
<many-to-many name="groups" table="meta_menu_groups" column="meta_menu_id" column2="group_id"
              ref="com.axelor.auth.db.Group"/>
<many-to-many name="roles" ref="com.axelor.auth.db.Role"/>
```

`Role.menus` et `Group.menus` portent `mappedBy` : ce sont les **côtés inverses**.
Le propriétaire est `MetaMenu.roles` et `MetaMenu.groups`.

**Conséquence.** On importe sur `MetaMenu.roles`. Un import sur `Role.menus` ne persiste rien,
sans lever d'erreur.

---

## 8. Le contournement administrateur

`com.axelor.auth.AuthUtils`, lignes 82-85 :

```java
public static boolean isAdmin(final User user) {
  return "admin".equals(user.getCode())
      || (user.getGroup() != null && "admins".equals(user.getGroup().getCode()));
}
```

Deux contournements, tous deux **codés en dur sur des chaînes**.
`AuthSecurity#getUser` renvoie `null` pour un admin, et tous les points d'entrée traitent
`user == null` comme « tout autorisé ».

**Conséquences.**
- Renommer le **code** du groupe `admins` retire le contournement, sans aucun message.
- Créer un groupe « Administrateur » avec un autre code ne donne aucun privilège particulier.
- Donner le groupe de code `admins` à un utilisateur lui donne tout, quels que soient ses rôles.
- **Ne jamais tester des droits avec un compte admin** : le résultat est toujours « autorisé ».

`AuthUtils#isTechnicalStaff` (lignes 87-89) lit `group.technicalStaff` : c'est un attribut
distinct, qui ouvre des fonctions techniques mais ne contourne pas le moteur de droits.

---

## 9. Masquer un menu ne protège pas la donnée

Conséquence directe des points 1 et 5 : le contrôle de droits est fait par `Permission` dans la
couche REST, pas par la visibilité du menu. Un objet atteignable par une relation, une recherche,
ou un appel direct `/ws/rest/<Modèle>/search` reste accessible même si aucun menu n'y mène.

Les attributs de vue `can-new`, `can-edit`, `can-delete`, `readonly` ne sont pas de la sécurité :
ils pilotent l'interface. La sécurité serveur est la `Permission`.

---

## 10. Les droits sont chargés en session

Niveau de preuve : `[DOC]` et pratique terrain constante, non vérifié dans le code à ce jour.
Après toute modification de rôle, de groupe ou de permission, l'utilisateur doit **se déconnecter
et se reconnecter** pour que le changement s'applique. Un test réalisé sans reconnexion est faux.

À instruire si le besoin se présente : localiser le cache de session et savoir s'il existe un moyen
de l'invalider sans reconnexion.
