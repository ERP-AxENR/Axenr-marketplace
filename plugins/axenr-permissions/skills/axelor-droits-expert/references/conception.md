# Concevoir une matrice de droits

## Principe directeur

**Un groupe par poste, des rôles mutualisés entre les groupes.**

Un utilisateur n'a qu'un seul groupe : le groupe est donc le profil d'accueil, pas l'unité de
droits. L'unité de droits est le rôle, et un rôle peut servir dans autant de groupes qu'on veut.
C'est là que se gagne la maintenabilité.

Indicateur de qualité : si chaque rôle n'apparaît que dans un seul groupe, la décomposition est
ratée. Reprends-la.

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
quelque chose qu'il ne devrait pas voir.

Pour les menus, trois contrôles avant de livrer :

1. Les menus **racines** du périmètre sont rattachés. Sinon rien n'apparaît en dessous.
2. **Toute la chaîne d'ancêtres** de chaque menu attribué porte le même rôle.
3. Aucun menu d'administration n'a atterri dans un rôle socle. Vérifie-le par un test explicite,
   pas à l'œil.

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
| Sociétés autorisées | `self.company.id in (?)` | `__user__.companySet.id` |

`self` désigne l'enregistrement, un `?` par paramètre, paramètres séparés par des virgules.
Teste toujours une condition sur un utilisateur dédié avant de la généraliser : une condition
invalide rend l'objet inaccessible ou lève une erreur serveur.

**Et rappelle-toi la règle d'or 4** : une permission sans condition sur le même modèle, portée par
un autre rôle du même groupe, annule complètement la restriction. Avant de livrer une condition,
vérifie qu'aucun autre rôle du groupe n'ouvre le même objet sans condition.
