# Pièges capitalisés

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

## Menus

| Piège | Effet | Parade |
|---|---|---|
| Rattacher une feuille sans ses ancêtres | La feuille n'apparaît jamais | Fermeture transitive, contrôlée automatiquement |
| Oublier le menu racine d'un module | Tout le module reste invisible | Lister les racines du périmètre et les rattacher |
| Croire qu'un menu sans restriction est fermé | Vrai pour une racine, faux pour un enfant | Règle d'or 5 |
| Importer sur `Role.menus` | Rien n'est persisté, sans erreur | Importer sur `MetaMenu.roles` |
| Chercher un menu par `name` | Homonymes par surcharge de module | Compter les doublons, résoudre par `importId` |
| Menus rechargés à la montée de version | Visibilité perdue ou modifiée | Revérifier après chaque mise à jour de module |
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
