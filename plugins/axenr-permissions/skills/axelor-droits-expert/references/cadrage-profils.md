# Cadrer un profil avant de le créer

> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3
> (lu dans le code et vérifié sur une instance jetable avec des comptes de profil). AxENR tourne sur
> AOP 7.4 / AOS 8.x : à vérifier sur la version cible.

Un profil encode des **décisions métier** (« que doit voir et faire ce poste ? »), pas seulement du
SQL. L'échec récurrent : écrire l'`INSERT` tout de suite et décider le périmètre à la place du
client, ou modifier un groupe partagé et casser l'accès de tous ses membres.

Ce fichier complète l'étape 1 de la méthode (cadrer, puis produire la grille) : il fixe les
questions à trancher **avant toute écriture**. Il ne sert pas à déboguer un profil existant :
pour un menu vide ou un refus d'accès, va directement à `diagnostic.md`.

## La loi de fer

```
AUCUN ARTEFACT DE PROFIL (SQL OU BUNDLE D'IMPORT) AVANT UN RÉCAPITULATIF VALIDÉ.
```

La lecture de la base est libre (groupes, utilisateurs, menus, permissions existants). Aucune
écriture sur `auth_*`, `meta_menu_*`, `meta_permission*`, ni aucun fichier d'import tant que :

1. le mode (démo ou projet) est établi ;
2. la méthode de déploiement (SQL ou bundle d'import) est établie ;
3. les questions de cadrage ont reçu une réponse de l'utilisateur ;
4. la checklist des cas limites est explicitement résolue ;
5. un récapitulatif a été montré et validé.

Pas d'exception : ni « la démo est dans deux heures », ni « le périmètre est évident d'après le
métier », ni « je produis le SQL et je pose les questions en parallèle ». Découvrir un groupe
existant en lisant la base n'autorise pas à le modifier.

Exception unique : un ajout ponctuel et idempotent que l'utilisateur a explicitement décrit
(« ajoute le menu `invoice-root` au groupe X ») est une instruction, pas une conception. Confirme
le rayon d'impact (L1), puis exécute.

## Étape 0 : démo ou projet ?

Première question, toujours.

| | Démo | Projet |
|---|---|---|
| Utilisateurs | Réutiliser des utilisateurs de démo existants | Vrais utilisateurs, liste nominative |
| Groupes | Nouveaux, jetables, préfixés démo | Nouveaux, codes validés avec le chef de projet ou le client |
| Source du périmètre | Le scénario de démo | Les périmètres rédigés par le chef de projet, les comptes rendus |
| Rigueur | Légère, mais jamais de modification d'un groupe partagé | Checklist complète, traçable, rejouable |
| Livrable | SQL éphémère | Script rejouable ou bundle d'import, plus la feuille de cadrage pour la recette |
| Réversibilité | Haute (supprimer le groupe de démo) | Faible : tout verrouiller |

## Étape 0.5 : SQL direct ou bundle d'import ?

Deuxième question, juste après le mode. Elle change l'artefact, qui peut l'exécuter, et le modèle
de rattachement des menus.

| | SQL direct | Bundle d'import (XML/CSV) |
|---|---|---|
| Accès requis | `psql`, accès direct à la base | Aucun : le partenaire charge le bundle par l'administration |
| Reconstruction du WAR | Non | Non |
| Artefact | Script `.sql` | `bind.xml` (`csv-inputs`) et fichiers `.csv` |
| Menus | Souvent `meta_menu_groups`, avec `WITH RECURSIVE` | `meta_menu_roles`, centré sur le rôle |
| Adapté à | Démo sur une base que tu maîtrises | Instance partenaire, client ou recette que tu ne maîtrises pas |
| Recette | `recettes-sql.md` | `import.md`, section « Recette du bundle de profil complet » |

Règle simple : **pas d'accès à la base sur la cible, donc bundle d'import.** Ne bascule jamais par
défaut sur du SQL pour un livrable partenaire.

Rappel AxENR : toute écriture exige un GO explicite, et jamais d'import de droits en production
(voir SKILL.md, « Écriture »).

## Questions de cadrage

Pose seulement les questions dont la réponse change quelque chose. N'invente aucune réponse.

### Communes
1. Mode (Étape 0) et méthode de déploiement (Étape 0.5).
2. **Nouveau groupe ou groupe existant ?** Par défaut et recommandé : nouveau groupe. Toucher un
   groupe existant affecte tous ses membres.
3. Convention de rattachement : AxENR pose permissions **et** menus sur le rôle (voir
   `conception.md`). La voie d'import est de toute façon centrée sur le rôle (`meta_menu_roles`).

### Démo
4. Quels utilisateurs de démo rattacher au nouveau groupe ? Liste les candidats depuis `auth_user`,
   ne choisis pas en silence.
5. Que doit montrer la démo ? Cela fixe les menus racines (gabarits par métier dans
   `recettes-sql.md`).
6. Faut-il masquer quelque chose pour l'histoire (une marge, par exemple) ? Meta permission.

### Projet
4. **La liste des utilisateurs est obligatoire.** Si « elle est dans le compte rendu », demande le
   fichier. Jamais de valeurs fictives pour l'affectation des groupes.
5. Codes de groupe : propose-les, fais-les valider (risque de collision avec les codes standard).
6. Pour chaque périmètre, traduis la phrase du chef de projet en droits concrets : menus racines,
   permissions objet (niveau CRUD), restrictions de champ. **Relis chaque verbe ambigu sous forme
   de question fermée** : « gère », « consulte », « accède », « voit tout » ne sont pas assez
   précis pour être scriptés. Exemple : « consulte les stocks », est-ce tout le module Stock en
   lecture, ou seulement le niveau de stock sur la fiche article ?

## Checklist des cas limites

Avant de produire l'artefact, consigne une décision pour chaque ligne. Une ligne non résolue
bloque. En mode projet, livre cette feuille avec l'artefact.

| # | Cas limite | Question à trancher | Si mal traité |
|---|---|---|---|
| L1 | Rayon d'impact sur un groupe partagé | Modifie-t-on un groupe qui a déjà des membres ? | Un « petit réglage » change l'accès de tous les comptables |
| L2 | Collision de code | Le code choisi existe-t-il déjà ? `SELECT code FROM auth_group` | Doublon, ou détournement d'un autre groupe |
| L3 | Piège de la « consultation » | Les droits s'additionnent sans refus possible (règle d'or 3). Une source quelconque donne-t-elle l'écriture sur cet objet ? La lecture seule ne tient que si **aucune** ne le fait. Vérifier avec la requête Q4 de `recettes-sql.md` | « Lecture seule » en réalité modifiable |
| L4 | Joker trop large | Un joker `...db.*` ouvre-t-il des objets hors périmètre ? | L'utilisateur modifie des objets hors de son métier |
| L5 | Portée des menus | Les liens menu ↔ rôle (ou groupe) sont-ils posés ? | Barre de navigation vide malgré des permissions parfaites |
| L6 | Racine et sous-arbre | Les enfants restreints disparaissent-ils si seule la racine est accordée ? | Module visible, sous-écrans bloqués |
| L7 | Refus malgré le menu visible | Chaque menu accordé a-t-il la permission objet correspondante ? | Menu affiché, clic refusé |
| L8 | `admins`, `technicalStaff`, rôle `Admin` | Un utilisateur cible est-il dans `admins`, ou dans un groupe `technicalStaff = true` ? Ne jamais activer `technicalStaff` pour « réparer » le menu : il ne donne ni menu ni permission. Le rôle nommé `Admin` est une donnée, pas le contournement : dans les données de démo AOS, il porte des centaines de menus et de jokers, dont `com.axelor.auth.db.*`. Ne jamais l'attacher à un « administrateur local » | Faille, test incohérent, « admin limité » qui voit tout |
| L9 | Réaffectation d'utilisateur | Un utilisateur a **un seul** groupe : le changer retire-t-il un accès nécessaire ? | Accès existant perdu |
| L10 | Dépendance entre modules | La fonction demande-t-elle une lecture complémentaire (les ventes lisent tiers et articles ; facturation ≠ comptabilité) ? | Formulaires à moitié cassés |
| L11 | Objet ou champ | « Voit X mais pas le champ Y » relève de la meta permission, pas de la permission objet | Champ toujours visible |
| L12 | Persistance et méthode | La cible offre-t-elle un accès base (Étape 0.5) ? Sans accès : bundle idempotent sur clés naturelles, jamais de `psql` improvisé | Le partenaire ne peut pas déployer, la recette ne se reconstruit pas |
| L13 | Entités techniques écrites par les actions natives | Une liste d'objets sans joker est une liste blanche. Pour chaque **geste** du flux, quelles entités enfants cachées AOS écrit-il ? Voir ci-dessous et `fermeture-dependances-vues.md` | L'écran s'ouvre, le bouton est là, le clic meurt sur « Vous n'êtes pas autorisé(e) à… » |
| L14 | Administration des utilisateurs déléguée | Un profil hors `admins` doit-il créer des comptes, changer un groupe ou des rôles, bloquer, saisir un mot de passe ? Depuis les écrans, AOP 8.2.3 refuse ces champs à tout autre que `admin` / `admins`, quelles que soient les permissions sur `com.axelor.auth.db.*` (voir `moteur-evaluation.md`, section 11). Décider : vraie appartenance à `admins`, ou administration des comptes laissée à un admin | « Administration » accordée sur le papier, première création de compte refusée |
| L15 | Mot de passe et préférences en libre-service | Comment chaque utilisateur change-t-il son mot de passe ? Sur AOS 9.1.6, le formulaire Préférences effectif n'a pas de bouton « Changer le mot de passe », et « mot de passe oublié » exige un compte mail sortant. Enregistrer ses préférences demande l'écriture sur son propre `User`, et ce formulaire expose `tradingName` sans domaine | Aucun libre-service, ou un utilisateur filtré par agence qui change d'agence et contourne le filtre |
| L16 | Supprimer ou archiver | Que signifie « supprimer » pour le métier ? À l'écran, le bouton Archiver demande le droit de suppression (AOP EE 8.2.3), et l'enregistrement du champ `archived` demande aussi l'écriture | Archivages imprévus, ou archivage promis impossible |
| L17 | Application activée après la conception | Quels menus enfants sans groupe ni rôle la nouvelle application ajoute-t-elle sous des parents que les profils voient déjà ? Ils deviennent visibles (règle d'or 5). Sauvegarder les menus de chaque profil avec un vrai compte (`GET /ws/action/menu/all`, voir `diagnostic.md`) avant chaque activation, et comparer après | Les écrans d'une nouvelle application apparaissent dans tous les profils |

### L13 : les entités cachées, geste par geste

Énumérer les objets visibles couvre ce que l'utilisateur **voit**, pas ce qu'AOS **écrit** pour
lui.

| Geste | Demande aussi | Symptôme si absent |
|---|---|---|
| Tout assistant ou popup (génération, actions de masse) | `com.axelor.utils.db.Wizard` : lecture pour toute action, création quand une `action-record` écrit un vrai champ | Le bouton ne fait rien ; `/ws/action` renvoie `status:-1` |
| Modifier un prix ou un montant sur une ligne de commande | La taxe de ligne (`PurchaseOrderLineTax`, `SaleOrderLineTax`) en création | Enregistrement refusé |
| Réaliser un mouvement de stock entrant | `Product` en écriture et `StockLocationLine` en création | « Réaliser » refusé |
| Tout chargement de page avec la brique workflow AEP | `com.axelor.meta.db.MetaWorkflowTask` en lecture (vérifier la classe dans la distribution) | Aucun effet visible, mais le journal se remplit d'erreurs d'autorisation |
| Menu Calendrier porté par une `action-method` | `ICalendarEvent`, `ICalendarUser` ; le calendrier CRM renvoie `Event` | Menu visible, puis « non autorisé à lire cette ressource » |
| Nouvel événement d'agenda (formulaire CRM) | `ICalendarEvent` en lecture **et** création | Formulaire ouvert avec « non autorisé à créer », dates par défaut vides |
| Formulaire avec `<mail-messages>` | `MailMessage`, `MailAddress`, `MailFlags`, `MailFollower` ; pièces jointes `MetaAttachment` / `MetaFile` | Formulaire en échec bien que l'objet métier soit autorisé |
| Formulaire parent avec lignes ou taxes | Le modèle de ligne ou de taxe | Ouverture partielle, ou enregistrement en échec |
| Création d'un tiers ou d'un contact (AOS 9.1.6) | `EmailAddress` (création), `Address` (création / écriture), `PartnerAddress` (création) ; `City` en création seulement si autorisé ; lecture de `Country`, `Department`, `Canton` ; `AccountingSituation` en lecture | Enregistrement refusé dès qu'un e-mail ou une adresse est saisi, alors que `Partner` est entièrement accordé |
| Boutons d'information stock d'un article | `StockLocation`, `StockLocationLine`, parfois `StockRules` | Erreur ou boutons vides |
| Documents GED contextuels | Les ACL issues de `DMSPermission`, pas une lecture globale de `DMSFile` | Une lecture globale expose des fichiers hors périmètre |

Pourquoi un geste qui « ne fait que » lancer un service peut être refusé : la plupart des services
écrivent sans contrôle, mais le formulaire renvoie à l'enregistrement les valeurs imbriquées (dont
les lignes ou taxes que le service vient de produire), et chaque action contrôle son modèle (voir
`moteur-evaluation.md`, section 11).

Trois façons de trouver ces dépendances, dans l'ordre :

0. **Inventaire en une passe, avant le premier test de profil.** Jouer chaque scénario une fois avec
   un compte qui a tous les droits, en enregistrant les appels (export réseau du navigateur ou outil
   d'automatisation) : chaque `/ws/rest/<modèle>/…` et chaque `/ws/action` donne une paire
   (modèle, opération), et chaque charge utile d'enregistrement liste ses valeurs imbriquées (sans
   id : création sur la cible ; id + version : écriture). Toute paire non couverte sera refusée.
   C'est un inventaire, **pas une preuve** : il manque les contrôles explicites internes à certains
   services AOS.
1. **Jouer le geste avec le vrai profil et lire le journal**, seule preuve :
   `grep -a 'Authorization Error' <catalina.out> | tail -20` (voir `diagnostic.md`).
2. Lire l'action native derrière le bouton :
   `SELECT xml FROM meta_action WHERE name = '<action>'`, attribut `model="…"`.

Pour l'audit systématique menu → contrôleur → widget → enfants, lire `fermeture-dependances-vues.md`
avant de livrer.

**Ne jamais valider un périmètre en `admin`, ni en lisant du XML.** `admin` contourne la couche de
permissions (règle d'or 8). Seul un parcours avec le vrai compte fait preuve.

## Mode « découverte » en recette (optionnel)

Quand le client veut explorer les écrans disponibles pendant la recette avant de figer le
périmètre, ne déforme pas le rôle métier permanent. Sépare trois couches :

1. le **porteur permanent des permissions**, normalement un rôle, qui implémente la matrice
   validée et le filtrage des lignes ;
2. un **porteur de navigation**, qui expose l'arbre de menus candidat pour discuter des écrans
   manquants ;
3. un **rôle temporaire de lecture recette**, clairement nommé, qui fournit les lectures et les
   dépendances de vues nécessaires pour ouvrir ces écrans.

Conditions : environnement de recette uniquement, et une étape de retrait testée. Les droits
s'additionnent : une permission de recette non filtrée annule le filtrage permanent sur le même
objet (règle d'or 4). Répète le prédicat (personnel, agence, société) sur les modèles porteurs de
données métier. Jamais de création, d'écriture, de suppression, d'import ou d'export métier pour
rendre un bouton visible. La GED reste gouvernée par `DMSPermission`.

Retirer le rôle temporaire, c'est supprimer les associations groupe / utilisateur ↔ rôle, puis
recharger, puis vérifier avec un compte non admin. Omettre le rôle d'un import ultérieur ne le
détache pas (les M2M s'ajoutent). `archived = true` n'est pas non plus une révocation prouvée :
les résolveurs de permissions et de menus d'AOP 8.2.3 ne testent pas ce drapeau. Un profil n'est
pas prêt pour la production tant que le rôle de découverte reste attaché.

## Récapitulatif à faire valider

```
MODE :            <démo | projet>
DÉPLOIEMENT :     <SQL | bundle d'import (csv-inputs)> ; accès base sur la cible ? <o/n>
GROUPE(S) :       <code> ; <nom> ; nouveau ? <o/n> ; membres existants : <n>
RÔLE(S) :         <rôle> -> <permissions objet, niveau CRUD>
MENUS :           <menus racines par rôle>
UTILISATEURS :    <utilisateurs de démo | liste projet complète>
RÈGLES CHAMP :    <meta permissions, s'il y en a>
DÉCOUVERTE :      <désactivée | porteur de navigation + rôle temporaire + retrait testé>
CAS LIMITES :     L1 à L17 résolus (décision notée pour chacun)
POINTS OUVERTS :  <ce qui attend encore le chef de projet ou le métier>
```

Un point ouvert qui bloque le script (liste d'utilisateurs manquante, lecture seule non
confirmée) reste ouvert : pas de SQL deviné, pas d'identifiants inventés. Signale-le et arrête-toi.

## Signaux d'arrêt

- Tu t'apprêtes à écrire sur `auth_*` ou `meta_*` sans récapitulatif validé.
- Tu as choisi un utilisateur de démo, un code de groupe ou des menus **sans demander**.
- Tu modifies « juste un peu » un groupe existant qui a des membres.
- Ton SQL contient des identifiants inventés, des codes devinés, des logins fictifs.
- Un verbe de périmètre est encore flou et tu scriptes quand même.
- Un rôle de découverte n'a pas d'étape de retrait testée.
