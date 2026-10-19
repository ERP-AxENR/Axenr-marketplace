# Pièges capitalisés

Les lignes marquées `[P]` viennent de l'apport d'un chef de projet Axelor (paquet du 15/10/2026),
éprouvé sur AOS 9.1.6 / AOP EE 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : à vérifier sur la
version cible.

## Moteur de droits

| Piège | Effet | Parade |
|---|---|---|
| Croire qu'un utilisateur sans permission a un accès large | On laisse des objets non couverts, ils sont refusés | Règle d'or 1. Socle commun de lecture sur tous les groupes |
| Joker de package trop haut (`com.axelor.apps.*`) | Ne couvre rien, silencieusement | Une permission par package exact |
| Joker qui ne couvre pas un sous-package | Les objets spécifiques d'un module client restent inaccessibles | Vérifier le package réel dans `meta_model.package_name` |
| Vouloir retirer un droit par une permission restrictive | Aucun effet : les droits s'additionnent | Retirer la permission qui accorde |
| Rôle de dépannage ajouté à un groupe | Annule les conditions JPQL des autres rôles sur le même objet | Règle d'or 4. Retirer le rôle après diagnostic |
| Objet mal orthographié dans `object` | Permission inopérante, sans erreur | Contrôler contre `meta_model.full_name` |
| Tester avec un compte admin | Toujours « autorisé » | Compte de test dédié, hors du groupe `admins` |
| Renommer le code du groupe `admins` | Retire le contournement administrateur, sans message | Ne jamais y toucher |
| Rôle nommé `Read` qui autorise l'écriture | Le nom ment, l'audit passe à côté | Vérifier le contenu réel, pas le nom |
| Croire qu'un rôle `Read` est transverse | `Base Read (sans menu)` ne couvre que `com.axelor.apps.base.db.*` : l'ajouter pour un refus sur un objet RH n'a aucun effet | Chercher le rôle `<Entité> Read` du package de l'objet refusé |
| Attribuer le rôle complet pour débloquer des données | L'utilisateur récupère aussi les menus du module (ex. tout le menu RH) | Utiliser, ou créer, la variante `X Read (sans menu)` |
| Croire qu'un menu accessible donne accès aux données | L'erreur tombe après l'ouverture du menu, sur un autre modèle | Repartir de l'appel réseau en échec, pas du menu |
| Cliquer sur « + » dans l'onglet Autorisations d'un rôle pour une permission qui existe déjà | Violation de la contrainte d'unicité du nom de permission | Utiliser la loupe pour rattacher l'existante ; « + » seulement pour une permission réellement nouvelle |
| `Partner` entièrement accordé, enregistrement refusé dès qu'un e-mail ou une adresse est saisi `[P]` | « Non autorisé à créer » sur `EmailAddress` / `Address` | Les valeurs imbriquées demandent la création sur leur cible (`moteur-evaluation.md`, section 11) |
| Activer `technicalStaff` pour réparer une navigation vide `[P]` | Rien n'est réparé : ni menu ni permission ; expose des détails techniques et le bouton Studio | Retirer le drapeau, poser les liens de menus |
| Attacher le rôle de démo `Admin` à un « administrateur local » `[P]` | Il voit tout : le rôle porte des centaines de menus et des jokers, dont `com.axelor.auth.db.*` | Rôle dédié, construit au besoin ; seul le code de groupe `admins` est le vrai contournement |
| Groupe « Administration » hors `admins` doté de tout `com.axelor.auth.db.*` `[P]` | Créer un compte, changer un groupe ou des rôles, débloquer, saisir un mot de passe : refusé | Champs protégés de `User`, réservés à `admin` / `admins` depuis les écrans |
| Filtrer par `__user__.tradingName` avec le raccourci « nom commercial actif » d'App Base activé `[P]` | L'utilisateur change d'agence depuis la barre du haut et voit ses enregistrements | Raccourci désactivé, ou filtre sur un champ que l'utilisateur ne peut pas modifier (le groupe) |
| Écriture sur sa propre fiche `User` accordée pour enregistrer les préférences, sur un rôle filtré par agence `[P]` | L'utilisateur change `tradingName` dans ses préférences | Verrouiller le champ par une règle de champ (à tester), ou ne pas accorder l'écriture |
| Promettre « supprimer » sans préciser `[P]` | À l'écran, archiver demande le droit de suppression, et l'écriture pour enregistrer `archived` | Écrire la définition du client dans la matrice |
| Une permission conditionnée sur l'export ou l'import `[P]` | L'export suit le filtre de lecture ; l'import n'est pas filtré par ligne | `permissions-conditionnelles.md` |
| Une lecture sans condition plus une lecture conditionnée sur le même objet `[P]` | La liste peut être restreinte aux lignes conditionnées | Formes sûres de `permissions-conditionnelles.md` |
| Lecture globale de `DMSFile` pour faire taire une erreur `[P]` | Tous les fichiers de la GED exposés, ACL `DMSPermission` contournées | `fermeture-dependances-vues.md`, section GED |

## Menus

| Piège | Effet | Parade |
|---|---|---|
| Rattacher une feuille sans ses ancêtres | La feuille n'apparaît jamais | Fermeture transitive, contrôlée automatiquement |
| Oublier le menu racine d'un module | Tout le module reste invisible | Lister les racines du périmètre et les rattacher |
| Croire qu'un menu sans restriction est fermé | Vrai pour une racine, faux pour un enfant | Règle d'or 5 |
| Importer sur `Role.menus` | Rien n'est persisté, sans erreur | Importer sur `MetaMenu.roles` |
| Chercher un menu par `name` | Homonymes par surcharge de module | Compter les doublons, résoudre par `importId` |
| Menus rechargés à la montée de version | Visibilité perdue ou modifiée | Revérifier après chaque mise à jour de module |
| Activer une application après la conception des profils `[P]` | Ses menus enfants sans groupe ni rôle apparaissent sous les parents visibles, dans tous les profils | Sauvegarder `GET /ws/action/menu/all` de chaque profil avant, comparer après |
| « Tout restaurer… » sans redémarrer Tomcat `[P]` | Environ une requête sur dix répond en `admin` jusqu'au redémarrage : les tests de profil sont faux | Redémarrer Tomcat immédiatement après (`diagnostic.md`) |
| Rôle socle qui embarque les menus d'administration | Tout le monde voit la gestion des comptes | Séparer les sous-arbres, contrôler explicitement |
| Croire que masquer un menu protège la donnée | Faux sentiment de sécurité | La sécurité, c'est la `Permission` |

## Import

| Piège | Effet | Parade |
|---|---|---|
| Relation référencée par `name` ou `code` en Excel | Champ laissé vide, sans erreur | Résoudre par `importId` |
| Enregistrement existant sans `importId` | Doublon à l'import suivant | Poser l'`importId` d'abord |
| Attendre d'un import qu'il retire des droits | Les M2M sont additifs | Lister les retraits comme actions manuelles |
| Tout importer en une passe | Erreur 500 sur dépendances | Un onglet, ou un input, à la fois |
| Se fier aux statistiques « succès » | Faux positifs | Recouper en SQL |
| Colonne non mappée dans la correspondance | Ignorée en silence | Mapper explicitement chaque colonne de relation |
| `search` sans résultat en canal CSV | Crée un enregistrement fantôme | Contrôler l'existence de chaque clé en amont |
| Renommer une clé naturelle | Les imports suivants créent un doublon | Clés figées, `importId` stables |
| Mot de passe dans un fichier | Fuite, compte cassé | Interdit. Création de comptes hors import |
| `update="true"` sur Role, Permission ou Group en canal CSV `[P]` | Premier import : rien n'est créé, `Non vide : 0` | `search` seul ; `update="true"` réservé aux menus et utilisateurs existants |
| Se fier à `Réussi` plutôt qu'à `Non vide` `[P]` | Une ligne ignorée (menu mal orthographié) compte comme réussie | Lire `Non vide` pour chaque input (`import.md`) |
| Modifier droits ou utilisateurs en SQL pendant que l'application tourne `[P]` | Changement invisible : cache Hibernate | Passer par l'application, ou redémarrer Tomcat |
| Compte créé par API laissé tel quel `[P]` | Connexion refusée : `blocked = true` par défaut (AOS 9.1.6) | Débloquer, vérifier société, langue, employé |
| Archiver un rôle pour le révoquer `[P]` | Non prouvé : les résolveurs d'AOP 8.2.3 ne testent pas `archived` | Détacher le rôle, recharger, vérifier en non admin |

## Analyse et méthode

| Piège | Effet | Parade |
|---|---|---|
| Conclure « absent » sans regarder en base | Studio et les imports créent hors dépôt | Chercher des deux côtés, toujours |
| S'appuyer sur un export incomplet | Conclusions fausses sur un sous-ensemble | Comparer les identifiants référencés par les tables de liaison à ceux réellement décrits |
| Confondre règle métier et droit | Les tables `*_authorized_role_set` ne sont pas de la sécurité | Le distinguer explicitement dans le livrable |
| Comparer deux groupes pour trouver une cause | La différence visible n'est presque jamais la cause | Dérouler groupe puis rôles puis permissions |
| Prendre la documentation pour le code | Le javadoc peut contredire l'implémentation | Le code prime, noter l'écart |
| Appliquer une règle d'une autre version | Vrai en 7.x, faux en 8.x | Identifier la version avant tout |
| Permission ou rôle directement sur l'utilisateur | Ingérable, invisible dans un audit par rôle | Passer par groupe puis rôle |
| Permission directement sur le groupe | Ne se mutualise pas, échappe à l'audit | Passer par un rôle |
