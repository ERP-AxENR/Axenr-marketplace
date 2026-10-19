# Permissions conditionnelles : ce que le moteur fait vraiment

> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Lu dans le code d'AOP 8.2.3 / AOS 9.1.6
> (`AuthResolver`, `AuthSecurity`, `Resource`, `JPQLFilter`, `Filter`, `LogicalFilter`, domaine
> `Permission`) ; création observée sur AOP EE 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : à
> vérifier sur la version cible.

À lire dès qu'un profil doit avoir des droits différents selon les lignes d'un même objet : ses
propres enregistrements, une agence, des fournisseurs en lecture et des clients modifiables, une
écriture selon le statut. Complète la section « Conditions JPQL » de `conception.md`.

La lecture du code établit les chemins d'exécution. Elle ne remplace pas un test avec le vrai
profil non admin : un autre rôle, un joker, un contrôleur spécifique peuvent changer le résultat.

## Syntaxe : prédicat JPQL, paramètres Groovy

`Permission.condition` (`auth_permission.condition_value`) est un prédicat JPQL / HQL sur l'alias
`self`. Opérateurs JPQL, pas Java ni Groovy :

```text
self.isSupplier IS TRUE
self.isSupplier IS NOT TRUE
self.tradingName.id = ?
self.siteSet.tradingName.id in (?)
```

Pas de `==`. Préfère `IS NOT TRUE` à `= false` quand un booléen nullable doit inclure `false` et
`null`.

`conditionParams` est une liste séparée par des virgules. Pour chaque élément :

- exactement `__user__` lie l'objet `User` courant ;
- tout autre élément est évalué en Groovy avec `__user__` disponible : `__user__.id`,
  `__user__.tradingName.id`, `[__user__.tradingName?.id]`, `__user__.companySet.id.plus(0)`.

Les `?` sont positionnels ; leur nombre et leur ordre doivent correspondre aux paramètres.

**Syntaxe selon la version.** La forme `__user__.companySet.id.plus(0)` est celle relevée sur
AOP 8.2.3 par l'apport partenaire, et elle concorde avec la variante `.plus(0)` de la doc AOS 8.5.
La forme `__user__.companySet.id` sans `.plus(0)` est celle des preuves de ce skill sur AOP 7.x
(`conception.md`). Ce qu'il faut vérifier : sur l'instance cible, copier une condition qui
fonctionne déjà, ou tester les deux formes sur un utilisateur dédié.

`Permission.condition` est limité à **1 024 caractères** (validation du bean). Une ligne trop
longue fait échouer cette permission à l'import, même si toutes les autres passent. Avant de
livrer, contrôle pour chaque permission :

```text
length(condition) <= 1024
count('?') == nombre d'éléments de conditionParams
```

Quand le prédicat voulu est un OU de chemins indépendants, découpe-le en plusieurs permissions
(même objet, même opération, même rôle) : le moteur combine leurs filtres par OU. Ne découpe
jamais un ET : cela élargirait l'accès.

## Résolution : union, opération par opération

`AuthResolver.resolve(user, object, accessType)` réunit les permissions de l'utilisateur, de ses
rôles directs, de son groupe, des rôles du groupe, et le joker de package. Il ne garde que celles
qui accordent l'opération demandée. Leurs filtres conditionnels sont combinés par OU. Il n'existe
pas de permission négative (règle d'or 3).

Conséquences :
- une permission plus large, quelle que soit sa source, élargit le résultat ;
- une permission sans condition pour une opération court-circuite le contrôle par ligne de cette
  opération (règle d'or 4) ;
- `canWrite = false` ne refuse pas une écriture accordée ailleurs ;
- une condition distingue des lignes, pas le menu ou la vue qui les ouvre.

Après composition du profil, lance la requête Q4 (`recettes-sql.md`) et audite ensemble les
permissions sur l'objet exact et sur le joker `db.*`.

## Comportement par opération (AOP 8.2.3)

| Opération | Ce que le code contrôle | La condition sépare-t-elle les lignes ? |
|---|---|---|
| Lecture en liste / recherche | `getFilter(CAN_READ)` injecté dans la requête | Oui, avec le cas limite ci-dessous |
| Lecture par identifiant | Comptage des identifiants demandés qui satisfont le filtre | Oui |
| Écriture d'une ligne existante | Idem | Oui |
| Suppression d'une ligne existante | Idem | Oui |
| Création (enregistrement principal d'un formulaire ou d'un appel REST) | `Resource.save` : permission sans identifiant, puis `check(CAN_CREATE, model, newId)` après insertion, dans la transaction | **Oui** : une ligne hors condition est refusée (« non autorisé à créer cette ressource ») et annulée |
| Création imbriquée (nouvelle ligne dans la charge utile, `action-record` à l'ouverture) | Permission sans identifiant uniquement | **Non** : la nouvelle ligne n'est pas testée (lu dans le code, pas testé à l'exécution) |
| Création par duplication | Condition testée sur l'identifiant **source** ; le duplicata revient non enregistré | Le duplicata est contrôlé comme un enregistrement principal à son enregistrement |
| Import | `canImport` existe, mais aucun appelant de `CAN_IMPORT` n'a été trouvé dans le cœur d'AOP 8.2.3 | **Non établi : ne pas le considérer comme filtré par ligne** |
| Export | Lecture et export contrôlés sans identifiant ; la requête d'export utilise le filtre de LECTURE | Les lignes suivent la lecture, pas la condition posée sur l'export |

Conséquences pratiques :
- un utilisateur ne peut pas enregistrer un enregistrement principal hors de son périmètre (un
  devis copié depuis le modèle d'une autre agence échoue pour lui : ne jamais promettre le
  contraire) ;
- la garde ne couvre ni les lignes imbriquées saisies dans le parent, ni les enregistrements créés
  par des services Java (`action-method`, qui écrivent le plus souvent sans contrôle), ni les
  imports : protège ces chemins par une validation serveur, ou retire la création sur le modèle
  enfant ;
- pour l'export, une permission `canExport` conditionnée ne suffit pas : retire l'export, restreins
  la lecture aux lignes exportables, ou développe un export sécurisé dédié.

## Cas limite du filtre de liste : nuance de la règle d'or 4

`isPermitted()` et `getFilter()` ne traitent pas les permissions mixtes de la même façon :

- `isPermitted()` renvoie vrai dès qu'il trouve une permission sans condition ;
- `getFilter()` combine quand même par OU toutes les permissions conditionnées de l'opération, et
  renvoie ce filtre dès qu'il en existe au moins une.

| Position | Source et version | Portée |
|---|---|---|
| « Une permission sans condition annule une permission conditionnée » | Règle d'or 4, preuve AOP 7.4.13 (`AuthSecurity#isPermitted`) | Contrôle d'un enregistrement (lecture par id, écriture, suppression) |
| « Une lecture sans condition plus une lecture conditionnée peut **restreindre** la liste aux lignes conditionnées » | Apport partenaire, AOP 8.2.3 (`getFilter`) | Listes et recherches |

Les deux sont compatibles : la règle d'or 4 vaut pour le contrôle par enregistrement, le cas
limite pour le filtre de liste. Ce qu'il faut vérifier sur la version cible : `getFilter` en 7.4
renvoie-t-il aussi le filtre conditionnel en présence d'une permission sans condition ? Tant que
ce n'est pas établi, teste la liste **et** l'ouverture directe d'un identifiant.

Deux formes sûres :

1. **Toutes les lignes lisibles, une partie modifiable** : une permission de lecture sans
   condition, plus une seconde permission avec `canWrite` / `canRemove` et la condition, mais
   `canRead = false` sur cette seconde.
2. **Partitions lisibles différentes** : uniquement des lectures conditionnées complémentaires,
   dont le OU donne l'ensemble voulu.

Exemple, fournisseurs en lecture seule, non-fournisseurs modifiables :

```text
Permission A : canRead=true, sans condition
Permission B : canRead=false, canWrite=true, canRemove=true
               condition = self.isSupplier IS NOT TRUE
```

Si le profil ne doit pas lire tous les tiers, conditionne aussi la permission A.

## Combiner le type de ligne et la portée utilisateur

Mets toutes les dimensions dans le même prédicat, opération par opération :

```text
condition       = self.isSupplier IS NOT TRUE AND self.tradingName.id = ?
conditionParams = __user__.tradingName.id
```

Ne suppose pas que chaque modèle a `tradingName` : vérifie le chemin réel dans le domaine de la
version (accès direct `self.tradingName`, ou indirect comme `self.project.siteSet.tradingName`).
Une condition valable sur un objet n'est pas un filtre d'agence générique.

Quand des catégories booléennes se recouvrent, fixe la priorité explicitement : avec
`self.isSupplier IS NOT TRUE`, un tiers à la fois client et fournisseur reste du côté lecture seule.

Attention au filtre sur un champ que l'utilisateur peut modifier lui-même (`tradingName` dans ses
préférences, raccourci « nom commercial actif » d'App Base) : voir `pieges.md`. Préfère un champ
protégé, comme le groupe.

## Vérification

Avec un vrai utilisateur non admin, après invalidation des caches :

1. la liste renvoie les lignes voulues ;
2. ouverture directe d'un identifiant autorisé et d'un identifiant interdit ;
3. modification et suppression des deux côtés de la condition ;
4. création avec un type ou une agence volontairement interdits ;
5. import d'une ligne interdite ;
6. contenu de l'export, pas seulement le fonctionnement du bouton ;
7. requête Q4, jokers compris.

Note la version testée. La lecture du code soutient la conception ; seul le comportement observé
du profil permet d'annoncer la recette prête.
