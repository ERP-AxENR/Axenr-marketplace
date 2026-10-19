# Protocole de recette à livrer au client

Le client teste. Ton rôle est de lui fournir un protocole qu'il peut dérouler seul, et une grille
où consigner. Un test non consigné est un test non fait.

## Mode opératoire

| Étape | Action | Pourquoi |
|---|---|---|
| 1 | Créer ou choisir un **compte de test dédié** par profil | Jamais un compte réel, jamais `admin` : un administrateur contourne tous les droits, le test serait faux |
| 2 | Ouvrir le compte de test en **navigation privée**, ou dans un autre navigateur | La session administrateur reste ouverte en parallèle, pour corriger sans perdre la main |
| 3 | Affecter le groupe au compte de test, côté administration | |
| 4 | **Se déconnecter et se reconnecter** côté navigation privée | Les droits sont chargés en session. Sans reconnexion, le test ne reflète pas le paramétrage |
| 5 | Parcourir tout le menu et comparer aux menus attendus | |
| 6 | Ouvrir chaque écran attendu | Aucune erreur d'accès ne doit apparaître |
| 7 | Créer, modifier, puis tenter de supprimer sur chaque objet du périmètre | |
| 8 | **Tester les refus** autant que les accès | Un refus attendu qui ne se produit pas est un défaut |
| 9 | Consigner résultat et commentaire | |
| 10 | Supprimer les comptes et enregistrements de test | |

L'étape 4 est celle qu'on oublie, et elle invalide tout ce qui suit.

## Grille à fournir

Une ligne par test, une colonne par profil, une case à remplir.

| Domaine | Test à réaliser | Résultat attendu | Profil A | Profil B | ... |
|---|---|---|---|---|---|

Couvre au minimum :

- **Connexion** : l'application s'ouvre sur l'écran d'accueil attendu.
- **Menus** : seuls les menus prévus apparaissent. Nomme explicitement ceux qui doivent être absents.
- **Lecture** : chaque écran du périmètre s'ouvre sans erreur d'accès.
- **Écriture** : création et modification conformes à la matrice.
- **Suppression** : autorisée ou refusée selon la matrice. C'est le droit le plus souvent mal posé.
- **Export** : conforme au droit d'export, qui est distinct de la lecture.
- **Relations** : ouvrir une fiche liée depuis un formulaire. C'est le test du socle commun.
- **Conditions** : si une condition JPQL existe, tester avec un enregistrement dans le périmètre
  et un autre hors périmètre.
- **Refus** : ouvrir un module hors périmètre. Menu absent ou refus.

## Ce que tu vérifies, toi, en parallèle

Le test fonctionnel ne remplace pas les contrôles techniques. Après import, rejoue `audit.sql` et
compare à la matrice source, ligne à ligne. Les écarts à chercher :

- un rôle dont le nombre de permissions ne correspond pas à l'attendu ;
- une permission qui vise un objet inexistant ;
- une permission orpheline, rattachée à rien ;
- un utilisateur métier dans le groupe `admins` ;
- un doublon de clé naturelle ;
- un menu du périmètre resté sans rôle.

## Compléments de recette

> Apport d'un chef de projet Axelor (paquet du 15/10/2026), éprouvé sur AOS 9.1.6 / AOP EE 8.2.3.
> À vérifier sur la version cible.

- **Valeurs imbriquées** : sur chaque formulaire du périmètre, saisir aussi ce qui se crée en ligne
  (un e-mail, une nouvelle adresse, une ligne de commande) : c'est là que tombent les refus que la
  simple ouverture ne montre pas.
- **Chaque geste**, pas seulement l'ouverture : Valider, Réaliser, Facturer, Générer, assistants.
- **Menus servis par le serveur** : sauvegarder `GET /ws/action/menu/all` de chaque profil
  (`diagnostic.md`) ; le refaire après toute activation d'application et comparer.
- **Mobile** : si le profil utilise l'application mobile, jouer démarrage, liste, détail et
  modification avec le compte de test (`fermeture-dependances-vues.md`).
- **Conditions** : liste, ouverture directe d'un identifiant interdit, création hors périmètre,
  contenu de l'export (`permissions-conditionnelles.md`).
- **Prérequis des comptes** : société active et sociétés, `blocked = false`, langue, employé quand
  un flux RH ou de validation est concerné, sièges Guardian restants (édition entreprise).
- **Caches** : après une modification en SQL, redémarrer Tomcat avant de tester ; jamais de test
  entre un « Tout restaurer… » et le redémarrage (`diagnostic.md`).

## Avant la production

- [ ] Chaque profil a été testé par un compte dédié, avec reconnexion
- [ ] Les refus ont été testés, pas seulement les accès
- [ ] Les contrôles SQL post-import ne remontent rien
- [ ] Les actions manuelles restantes sont faites et vérifiées
- [ ] Les comptes de test sont supprimés
- [ ] La matrice est à jour de ce qui a été réellement mis en place
