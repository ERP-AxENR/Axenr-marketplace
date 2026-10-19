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

---

## 11. Compléments AOP 8.2.3

> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Lu dans le code d'AOP 8.2.3 / AOS 9.1.6
> et vérifié sur instance. AxENR tourne sur AOP 7.4 / AOS 8.x : à vérifier sur la version cible.
> Les numéros de ligne des sections 1 à 10 portent sur 7.4.13 ; en 8.2.3, l'apport relève
> `MenuChecker.isAllowed` ligne 56, `canShow` ligne 96, `AuthUtils.isAdmin` ligne 108,
> `AuthResolver.resolve` ligne 98, `AuthSecurity.getFilter` ligne 116 et `isPermitted` ligne 153.
> Repère chaque règle par classe et méthode, pas par numéro de ligne.

### Ce qui concorde avec les sections 1 à 10

Les quatre règles de visibilité des menus, le court-circuit `admin` / `admins`, l'union des quatre
sources de permissions, le joker calculé depuis l'objet, `canShow` (`hidden`, `moduleToCheck`,
`conditionToCheck`) : identiques en 8.2.3. L'apport ajoute un cas rare : un menu dont le champ
`user` est renseigné n'est visible que de cet utilisateur.

### Nuance sur la règle d'or 4

Elle vaut pour le contrôle d'un enregistrement. Pour les listes, `getFilter` combine quand même
les permissions conditionnées par OU, même en présence d'une permission sans condition : la liste
peut se retrouver **restreinte**. Détail et formes sûres : `permissions-conditionnelles.md`.

### Nuance sur la règle d'or 10

L'apport constate qu'en 8.2.3 l'utilisateur courant est relu à chaque requête
(`AuthUtils.getUser`) : une modification faite par l'application s'appliquerait à la requête
suivante (non mesuré), et le vrai piège est le cache Hibernate après une modification en SQL. La
règle 10 reste en place tant qu'elle n'est pas instruite dans le code de la version cible.
Pratique retenue : `diagnostic.md`, « Caches et reconnexion ».

### Les valeurs imbriquées d'un enregistrement

`Resource.save` contrôle l'enregistrement principal (création sans identifiant, écriture avec) et
chaque valeur imbriquée de la charge utile (`checkRelationalPermissions`) :

| Valeur imbriquée envoyée | Contrôle sur le modèle cible |
|---|---|
| Sans identifiant (éditeur en ligne, `canNew`, nouvelle ligne O2M) | Création |
| Identifiant + `version` (enregistrement modifié sur place) | Écriture sur cet identifiant |
| Identifiant seul | Aucun : simple référence |

Observé avec le client web AOP 8.2.3 : une valeur imbriquée existante voyage **sans** version (une
taxe de ligne `{id, name, selected}`, une ville `{id, fullName}`), donc sans contrôle d'écriture.
Le « + » d'un champ lien (nouvelle ville, nouvelle adresse) enregistre son enregistrement seul,
avant le parent.

Deux réglages transforment ces refus, et ceux des actions, en simples avertissements :
`application.permission.disable-relational-field` et `application.permission.disable-action`
(défaut `false`). Un bundle qui marche sur une instance et échoue sur l'autre : compare d'abord
ces deux réglages.

### Les actions contrôlent leur modèle

Chaque action nommée contrôle la lecture sur son `model`, ou sur le modèle du contexte quand elle
n'en déclare pas, et sur l'enregistrement lui-même quand le contexte a un identifiant
(`Action.checkPermission`, `ActionHandler.checkPermission`). Une `action-record` qui écrit de vrais
champs contrôle la création (pas d'identifiant) ou l'écriture. Exemptées : les actions sur
`MetaAction` ou `MetaFilter`, et les `action-view` sur `MailMessage`.

### Les règles de champ ne s'additionnent pas

Contrairement aux permissions objet, `MetaPermissions.find` prend la **première** meta permission
active qui porte une règle pour le champ, dans cet ordre : utilisateur, groupe, rôles de
l'utilisateur, rôles du groupe. Une règle posée sur l'utilisateur ou le groupe masque celles des
rôles. Raison de plus pour tout poser sur le rôle.

### Champs protégés de la fiche utilisateur

Pour tout utilisateur qui n'est pas `admin` / `admins`, `Resource.save` refuse une charge utile
`User` (création ou mise à jour, sa propre fiche ou non) contenant `code`, `group`, `blocked`,
`activateOn`, `expiresOn`, `password`, `passwordUpdatedOn`, `roles`, `permissions` ou
`metaPermissions` (`USER_RESTRICTED_FIELDS`), quelles que soient les permissions sur
`com.axelor.auth.db.*`. Un « administrateur délégué » hors `admins` peut modifier les champs
ordinaires, mais ne peut ni créer un compte (`code` est obligatoire), ni changer un groupe ou des
rôles, ni bloquer / débloquer, ni saisir un mot de passe. La garde n'existe que dans
`Resource.save` : services et batchs écrivent `User` directement. Seul chemin trouvé hors
`admins` : le batch AOS « Changement de mot de passe » (`BatchPasswordChange`), soumis aux seules
permissions sur `BaseBatch`. `forcePasswordChange` n'est pas protégé.

Changement de mot de passe : `UserController.changePassword` (AOP) accepte son propre compte, ou
tout compte pour un admin ; la lecture sur `User` suffit. Sur AOS 9.1.6, le formulaire Préférences
effectif n'a pas le bouton : le chemin sans permission est `forcePasswordChange = true`, qui fait
demander un nouveau mot de passe à la connexion (`AxelorAuthenticator`).

### `technicalStaff` en 8.2.3

Ni `MenuChecker` ni `AuthSecurity` ne le lisent : seul `admin` / `admins` contourne. Usages relevés
(AOP 8.2.3 / AOS 9.1.6) : détails d'erreur affichés, exécution d'une requête non enregistrée,
données techniques dans À propos, accès à l'observabilité, et, avec `viewCustomizationPermission`
et le réglage Studio, le bouton « Ouvrir Studio » sur les vues. Aucun ne contourne les droits.
Concorde avec la section 8.
