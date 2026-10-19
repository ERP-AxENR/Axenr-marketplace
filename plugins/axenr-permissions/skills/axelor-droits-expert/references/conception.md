# Concevoir une matrice de droits

## Principe directeur

**Un groupe par poste, des rôles mutualisés entre les groupes.**

Un utilisateur n'a qu'un seul groupe : le groupe est donc le profil d'accueil, pas l'unité de
droits. L'unité de droits est le rôle, et un rôle peut servir dans autant de groupes qu'on veut.
C'est là que se gagne la maintenabilité.

Indicateur de qualité : si chaque rôle n'apparaît que dans un seul groupe, la décomposition est
ratée. Reprends-la.

## Étape 0 : la porte de cadrage

Avant toute écriture (SQL ou fichier d'import), fais trancher le mode (démo ou projet), la méthode
de déploiement (SQL ou bundle d'import), les questions de périmètre et la checklist des cas limites
L1 à L17, puis fais valider un récapitulatif : `cadrage-profils.md`. Le reste de ce fichier décrit
comment concevoir la matrice une fois ce cadrage posé.

## Étape 1 : cadrer avant de demander

Un client à qui on envoie une matrice de tout l'ERP la remplit mal, ou pas du tout.
Trois questions préalables suffisent à réduire le périmètre :

1. Quel est le flux métier réel ? Pas les modules installés, ceux qui servent.
2. Quels postes existent ? Un poste devient un groupe. Vise cinq à huit groupes, rarement plus.
3. Quels objets chaque poste manipule-t-il, et pour y faire quoi ?

Produis ensuite la grille **limitée à ce périmètre**. `scripts/generer_grille.py` la génère.

## Étape 2 : auditer la grille reçue

Cherche systématiquement :

- **Le remplissage en bloc.** Une colonne de `x` alignés sur trois groupes consécutifs pour des
  rôles sans rapport signale un glissement de souris, pas une décision.
- **Le poste privé de son propre métier.** Un « chef de projet » sans rôle Projet, un « magasinier »
  sans rôle Stock. C'est fréquent et jamais volontaire.
- **L'administration donnée à un opérationnel.** Gestion des utilisateurs, des groupes, des rôles
  ou des permissions sur un profil métier : à remonter comme risque, pas comme détail.
- **Les onglets vides présentés comme validés.** L'onglet des droits objet est celui qu'on oublie
  le plus souvent, et c'est le seul qui compte vraiment.
- **Les incohérences entre onglets.** Un rôle cité dans la matrice et absent de la liste des rôles.

Remonte chaque écart avec sa conséquence concrète. Propose une correction. Ne corrige jamais
en silence : la grille est la source de vérité du client.

## Étape 3 : réutiliser avant de créer

L'instance contient déjà beaucoup de rôles, souvent sous la forme `<Module> Read / User / Manager`.
Avant d'en créer un, vérifie leur **contenu réel** : compte les permissions, et combien sont en
écriture ou en suppression. Un rôle nommé « Read » n'est pas forcément en lecture seule.

Ordre de préférence :

1. Un rôle existant convient tel quel : le réutiliser.
2. Un rôle existant convient à peu de chose près : créer un nouveau rôle, **sans jamais modifier**
   le rôle standard, qu'une montée de version réécrira.
3. Aucun ne convient : en créer un.

### Convention AxENR des rôles en double

Pour chaque module, AxENR tient deux variantes de rôle :

| Rôle | Contenu | Usage |
|---|---|---|
| `X User` | Permissions **et** menus du module | Profil qui travaille dans le module |
| `X Read (sans menu)` | Permissions de lecture seules, aucun menu | Profil qui doit seulement lire ces données depuis un autre écran (relation, planning, tableau de bord) |

Quand la variante « sans menu » manque (cas typique : un rôle `Employee Read` standard qui embarque
les menus RH), **crée-la** en reprenant les permissions sans les menus, plutôt que d'attribuer le
rôle complet : sinon le profil voit apparaître un module entier qu'il n'utilise pas.

Dans l'interface, pour rattacher une permission existante au nouveau rôle, utilise la **loupe** de
l'onglet Autorisations, jamais le **+** : le « + » crée une nouvelle permission et bute sur la
contrainte d'unicité du nom.

Cas fréquent du rôle « socle trop large » : un rôle de base fourni par l'éditeur donne souvent des
droits d'administration en plus des référentiels. Dans ce cas, crée un rôle socle dérivé qui reprend
les permissions métier et écarte les permissions d'administration, plutôt que de l'attribuer tel quel.

## Étape 4 : le socle commun

Un formulaire qui affiche une relation vers un objet non lisible provoque une erreur d'accès sur un
écran pourtant autorisé. Prévois donc un rôle socle en lecture seule, attribué à **tous** les
groupes, couvrant les objets lus partout : utilisateurs, sociétés, tiers, adresses, villes, pays,
devises, unités, articles, familles et catégories d'articles, taxes, modes et conditions de
règlement, séquences, objets de configuration applicative lus par les vues, fichiers et sélections.

Vérifie chaque classe dans `meta_model.full_name` : retire celles absentes de l'instance.

Si l'instance fournit déjà un rôle de lecture par package (une permission `.r` par module), c'est
le meilleur socle possible : il couvre tout sans rien ouvrir en écriture.

## Étape 5 : permissions et menus sur le rôle

**Jamais sur le groupe.** Exception uniquement sur demande explicite, documentée comme telle.

Motifs : un droit posé sur un groupe ne se mutualise pas, et il est invisible dans un audit qui
parcourt les rôles. Il ressort au pire moment, quand quelqu'un cherche pourquoi un profil voit
quelque chose qu'il ne devrait pas voir. Autre motif, côté champs : les règles de champ ne
s'additionnent pas, et une meta permission posée sur le groupe masque celles des rôles
(`moteur-evaluation.md`, section 11).

**Autre convention rencontrée.** L'apport d'un chef de projet Axelor (paquet du 15/10/2026,
AOS 9.1.6 / AOP EE 8.2.3) recommande « groupe = portée, rôle = permission » : les menus sur le
groupe (`meta_menu_groups`), les permissions sur le rôle, comme les groupes des données de démo
AOS. Le moteur accepte les deux (règles b et c, `moteur-evaluation.md`). Sur un projet AxENR, garde
la convention de ce fichier. Sache reconnaître l'autre sur une instance existante : ses menus
n'apparaissent pas dans un audit par rôle, il faut aussi lire `meta_menu_groups`. Le même apport
note que la voie d'import est de toute façon centrée sur le rôle (`meta_menu_roles`).

Pour les menus, trois contrôles avant de livrer :

1. Les menus **racines** du périmètre sont rattachés. Sinon rien n'apparaît en dessous.
2. **Toute la chaîne d'ancêtres** de chaque menu attribué porte le même rôle.
3. Aucun menu d'administration n'a atterri dans un rôle socle. Vérifie-le par un test explicite,
   pas à l'œil.

## Dépendances cachées et cas limites

Le socle commun ne suffit pas toujours : chaque geste (valider, réaliser, générer, saisir un e-mail
dans une fiche tiers) peut écrire des objets techniques invisibles à l'écran. Avant de livrer une
liste blanche, applique la méthode de `fermeture-dependances-vues.md`.

Trois cas limites à trancher avec le client, que la grille ne fait pas apparaître
(`cadrage-profils.md`, L14 à L16) :
- **administration déléguée** : hors `admins`, personne ne peut créer un compte, changer un groupe
  ou des rôles, ni saisir un mot de passe depuis les écrans (AOP 8.2.3) ;
- **libre-service** : comment chacun change son mot de passe et ses préférences, sans pouvoir
  changer d'agence au passage ;
- **supprimer ou archiver** : archiver demande le droit de suppression à l'écran.

## Conventions de nommage

Choisis un préfixe client court et tiens-le. Exemple avec `CLI` :

| Objet | Nom visible | `importId` |
|---|---|---|
| Permission | `perm.cli.<module>.<Objet>.<niveau>` | identique au nom |
| Permission conditionnée | `perm.cli.<module>.<Objet>.<niveau>.<condition>` | identique |
| Permission joker | `perm.cli.<module>.all.<niveau>` | identique |
| Rôle | `CLI - <Métier>` | `role-cli-<metier>` |
| Groupe | code `cli_<profil>`, nom `CLI <Profil>` | `grp-cli-<profil>` |
| Meta permission | `mperm.cli.<Objet>.<usage>` | identique |

`importId` en minuscules, sans espace ni accent, stable dans le temps.
**Ne renomme jamais un `name` ou un `code` existant** : c'est la clé de recherche des imports.

## Conditions JPQL

| Besoin | `condition` | `conditionParams` |
|---|---|---|
| Ses propres créations | `self.createdBy = ?` | `__user__` |
| Ses enregistrements | `self.user = ?` | `__user__` |
| Sociétés autorisées | `self.company.id in (?)` | `__user__.companySet.id` (7.x) ou `__user__.companySet.id.plus(0)` (8.2.3, apport partenaire) |

`self` désigne l'enregistrement, un `?` par paramètre, paramètres séparés par des virgules.

**Syntaxe des paramètres à vérifier selon la version.** La forme `__user__.companySet.id` est
celle des preuves sur AOP 7.x. La documentation AOS 8.5 montre une variante avec `.plus(0)`
(extraction texte peu fiable du PDF officiel). Avant de livrer une condition sur une instance 8.x,
relis la doc de la version exacte, ou copie une condition qui fonctionne déjà sur l'instance, puis
teste-la sur un utilisateur dédié.
Comportement réel par opération (création, import, export, cas limite des listes) :
`permissions-conditionnelles.md`.
Teste toujours une condition sur un utilisateur dédié avant de la généraliser : une condition
invalide rend l'objet inaccessible ou lève une erreur serveur.

**Et rappelle-toi la règle d'or 4** : une permission sans condition sur le même modèle, portée par
un autre rôle du même groupe, annule complètement la restriction. Avant de livrer une condition,
vérifie qu'aucun autre rôle du groupe n'ouvre le même objet sans condition.
