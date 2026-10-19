# Méthode — rejeu contrôlé par l'API vers une instance sans accès base

**Pièges couverts par cette fiche :**

- 189. L'ordre de création n'est pas une clé : deux rejeux identiques peuvent créer des homonymes dans un ordre différent
- 190. Un essai factice ne prouve rien ; seul un essai à blanc qui lit la cible réelle renseigne
- 191. Estimer la durée d'un rejeu distant par le nombre d'appels de la répétition et le débit mesuré, pas au jugé
- 192. Un script modifié après sa répétition n'est plus répété

Voir aussi : 171 (geste sous date simulée, script en pause) et 185 (une seule boucle triée par date) dans
`methode-dates.md` ; 178 (un écran qui écrit à son ouverture) dans `entites-production-btp.md` ; 186 et 187 (ce que
l'API ne fait pas, dates-heures en UTC) dans `pieges-runtime-aos-9-1-7.md` ; 169 et 188 (étiquette d'import, audit
sans écriture) dans `methode-audit.md`. Pour rejouer un jeu extrait en SQL sur une base vierge :
`methode-rejouabilite.md`.

Cette fiche décrit une méthode générique. Elle a été éprouvée une fois, sur la démo BTP de référence du 26/09/2026 : rejeu par
l'API d'un scénario complet (module Construction, AOS 9.1.7 / AOP EE 8.2.4-SNAPSHOT) vers une instance hébergée, 17 lignes,
toutes OK, un arrêt au contrôle de l'étape 06 levé par décision de l'utilisateur. Chaque point porte l'exemple de la démo BTP de référence. Les scripts, relevés, rapports et journaux qu'elle
cite appartiennent au **dossier de rejeu** de cette démo (lanceur, outil de relevé, références, journaux) : ce
dossier est **fourni par l'utilisateur**, ce skill n'en livre aucun ; sans lui, la méthode s'applique avec ses
propres scripts.

## 1. Quand en a-t-on besoin

Quand l'instance cible n'offre **ni accès base ni retour arrière** : instance hébergée d'une démo, base d'un partenaire,
recette distante. Une écriture fausse ne se défait pas ; la seule sortie est de vider la base et de tout refaire. Un
arrêt, lui, ne coûte presque rien. Toute la méthode sert cette asymétrie : **tout est conçu pour s'arrêter**, jamais
pour « débloquer ».

Inutile quand la cible est locale avec un dump : on travaille alors par paliers et restaurations.

*Démo BTP de référence : instance hébergée sans dump ni accès base ; « la seule issue serait de vider la base et de tout refaire, une
journée entière ».*

## 2. Une répétition, et une référence relevée à chaque étape

1. Monter une **copie locale du même point de départ** que la cible (même démo importée, même date, même
   configuration) et y jouer tout le rejeu, avec les scripts dans leur version finale.
2. Après chaque étape d'écriture, et à chaque pause voulue, **relever l'état** par l'API (§3) : c'est la référence de
   l'étape.
3. Avant d'écrire sur la cible, relever son état de départ et le comparer à celui de la répétition : les écarts de
   départ sont connus et nommés, ou le rejeu ne part pas.
4. Garder les journaux de la répétition : ce sont eux qui prouvent qu'une étape a été répétée (piège 192) et qui donnent
   les textes à exiger (§6) et le nombre d'appels (§8).

*Démo BTP de référence : répétition `<base>`, copie de la démo importée au 05/01, même point de départ que l'hébergée
à trois réglages près ; 11 références (du relevé initial au relevé de pilotage), copies exactes des
relevés de la répétition (md5 identiques, « Vérifié et conforme » à la relecture).*

## 3. Relevé par clés naturelles, numéros neutralisés

L'outil de relevé lit la cible **par l'API seule**, en lecture (`GET /ws/meta/fields/<modèle>`,
`POST /ws/rest/<modèle>/search`), et range chaque pièce sous une **clé naturelle** : nom, date métier, montant, jamais
un `id` ni un numéro de séquence, qui diffèrent d'une instance à l'autre.

- Les numéros de pièces (`SO0022`, `PRJ00900`…) sont **neutralisés** dans les clés et les valeurs (`<n°>`), et relevés
  à part « pour information », jamais comparés.
- Une date-heure se compare sur la **date** : l'heure est celle, réelle, du rejeu.
- Décimaux arrondis au centime, textes longs remplacés par une empreinte, familles volumineuses agrégées (nombre et
  somme par mois, par salarié…).
- Une famille par objet métier du scénario, pas par table.
- Les homonymes se départagent par un **discriminant métier**, jamais par l'ordre de création (piège 189).
- Les **angles morts** s'écrivent : ce que le relevé ne voit pas n'est pas contrôlé.

*Démo BTP de référence : l'outil de relevé, 35 familles (tiers, articles, devis, chantiers, tâches, situations, factures, échéances,
règlements, écritures, achats, mouvements de stock, temps, paie, réserves…). Angles morts énoncés : les lignes de devis,
de commande, de facture et d'écriture une à une, et les montants des écritures (seul leur nombre par journal, statut et
mois est comparé), couverts indirectement par les totaux des pièces.*

### 189. L'ordre de création n'est pas une clé : deux rejeux identiques peuvent créer des homonymes dans un ordre différent

`[constaté le 2026-09-26 à 19 h 39, instance hébergée]` Deux ouvrages homonymes d'un même chapitre (Norvalys,
« Terrassement en pleine masse », 1.1 à 380 h et 1.4 à 90 h) sont sortis de « Créer le chantier » dans l'ordre inverse
de la répétition — même script, mêmes données ; deux autres paires du même chantier sont restées dans l'ordre. Le relevé
lisait les tâches par `id` et suffixait les homonymes `#2` dans cet ordre : il a vu les deux tâches **croisées** alors
que leurs 16 valeurs comparées étaient identiques. Contrôle de l'étape 06 KO, arrêt, rapport
d'arrêt.

Levée : décision de l'utilisateur d'admettre la paire, un écart n'étant admis que si la valeur de la cible est **exactement**
celle de l'autre tâche de la paire à la répétition (dans le code du contrôle, `PAIRE`, testé hors ligne sur 24 cas), puis
contrôle rejoué (§6) ; 14 minutes d'arrêt, contrôles 07 à 10-pilotage ensuite OK.

**À faire :** clé des homonymes par un discriminant métier (ici le numéro d'ouvrage, `constructionSequenceStr`) ; à la
répétition, traiter toute clé suffixée `#2` comme un avertissement. Les scripts, eux, visaient les ouvrages par leur
numéro : aucun effet sur les données.

## 4. Un contrôle par étape, contre la répétition au même stade

Après chaque étape d'écriture, relever la cible et la comparer à la référence de la même étape. **OK** : aucun écart
non admis. **KO** : arrêt, rien de corrigé sur la cible, rapport au propriétaire de la démo.

- **Écarts admis nommément** : chacun désigné par sa famille, sa clé (ou toutes) et son champ, établi à la répétition,
  écrit dans le code du contrôle — jamais laissé au jugement de l'exécutant. **Et à valeur exacte quand on la connaît**.
  Un écart dont la valeur ne peut pas être connue d'avance n'est admis que jusqu'au contrôle suivant, qui le juge.
- **Une seule tolérance générale**, affichée à chaque contrôle : une date réelle du jour J contre J+1, si le rejeu
  passe minuit.
- **Contrôles en plus du relevé** : la date simulée de l'application et de l'utilisateur (vide, sauf pause voulue) ; les
  numéros que les étapes suivantes visent.
- **Sortie** : un résumé par famille, dix écarts au plus par famille ; une troncature globale cacherait une famille
  derrière une autre (relecture adverse, défaut 4).
- Un relevé qui échoue pour une raison de réseau se relance une fois dans le contrôle ; ensuite, ligne `controle` (§6).

*Démo BTP de référence (le contrôle) : réglages présents sur l'hébergée avant l'étape 5, admis aux contrôles 00-initial à 04 ;
retenue de 136 € posée par le geste de sous-traitance, admise aux contrôles 09 à 10-pilotage seulement si la valeur
vaut exactement 136 ; restes à faire des tâches admis au contrôle 10, jugés au 10-pilotage après rafraîchissement
(piège 178) ; numéros des chantiers comparés dès le contrôle 06, l'étape 10 les visant par numéro. Au rejeu hébergé :
4 écarts admis à l'étape 04, 7 aux étapes 09, 10 et 10-pilotage.*

## 5. Les gestes manuels, reproduits par script

Un geste de l'utilisateur prévu par le scénario (un avenant saisi à l'écran, un circuit de sous-traitance) ne se refait
pas à la main sur la cible : il se reproduit par un script, qui donne le même résultat et se contrôle.

- **Essai à blanc** : le script lit la cible réelle, affiche ce qu'il ferait et n'écrit rien ; sa sortie contient des
  textes exigés par le lanceur (« chapitre déjà présent : 0 », « assistant : 49 ligne(s) »). Voir piège 190.
- **Arrêt de lui-même** (code de sortie dédié) sur toute valeur intermédiaire non conforme, **avant** l'écriture
  irréversible suivante ; à la fin, contrôle des valeurs d'arrivée.
- Il repère ses objets par leur référence de scénario, jamais par leur numéro.
- Un geste daté « du jour » se joue sous la date simulée voulue (piège 171).
- **Un geste ne se relance jamais** : il s'analyse.

*Démo BTP de référence : le script du geste d'avenant (recopie un chapitre de 14 lignes ; s'arrête si le total de l'avenant n'est
pas 1 105 338,43 € HT) et le script du geste de sous-traitance (sous la date du 31/03 ; s'arrête avant la
confirmation du paiement direct si l'en-tête, les lignes, la remise au prix, le statut, les montants ou le circuit ne
sont pas conformes, puis contrôle 15 valeurs finales). Ces arrêts ont été ajoutés après la relecture adverse
(défaut 2 : « tous les contrôles se font après ses écritures »).*

### 190. Un essai factice ne prouve rien ; seul un essai à blanc qui lit la cible réelle renseigne

`[constaté les 24 et 26/09/2026]` Un « dry-run » qui simule les réponses du serveur exerce l'enchaînement du script, pas
le serveur. Le 24/09, celui du rejeu de la démo BTP de référence sortait vert (code 0, 1 137 appels) ; la relecture adverse du même jour
concluait NO-GO : le script ne pouvait pas produire le jeu de données (relecture mal lue, erreurs rendues sous `info`
ignorées, groupes d'actions arrêtés à leur enregistrement) — « le dry-run vert ne prouve rien sur ces points ».
Et ce mode n'exécute aucune recherche : tout y rend vide, les objets à retrouver comme les
doublons à éviter (lu dans la réponse factice du client REST du kit).

**À faire :** distinguer trois essais, et ne compter pour preuve que les deux derniers :

1. l'**essai factice** (réponses simulées) : syntaxe et enchaînement seulement ;
2. l'**essai à blanc** : lectures réelles sur la cible réelle, aucune écriture, arrêt avant la première ;
3. la **sonde** : une écriture réelle, sur une copie jetable, pour trancher une hypothèse d'API avant la vague.

## 6. Un lanceur unique

Toutes les lignes du déroulé vivent **dans un seul lanceur** : commande, variables, délai, textes exigés, contrôle de
l'étape. L'exécutant ne compose aucune commande à la main (relecture adverse, défaut 8 : une
variable perdue aurait joué l'étape 9 sans le geste, de façon irréversible).

- **Ordre imposé** : seule la ligne suivante est acceptée ; une ligne déjà OK est refusée. Un **fichier d'état** porte
  les lignes OK, les compteurs de relance, le contrôle en attente et le dernier échec.
- **Verrou exclusif** : tout second appel est refusé tant qu'une ligne tourne, vidage de date compris. **Une seule
  session** touche au lanceur (incident du 26/09 : deux instances de la session de rédaction ont écrit sur le même
  lanceur).
- **Journaux horodatés**, jamais écrasés ; en cas d'échec, le lanceur affiche les lignes d'erreur du journal entier,
  puis ses dernières lignes.
- **Verdict** : code retour 0, aucun texte d'erreur dans le journal (y compris les réserves que le script écrit
  lui-même, complément du piège 106), tous les textes exigés présents, puis contrôle de l'étape OK.
- **Environnement propre** : les variables du rejeu héritées de l'appelant sont retirées, seules celles de la ligne
  sont posées.
- **Relance** : c'est le lanceur qui décide, et il l'écrit. Une seule fois, pas avant 10 minutes (le serveur peut
  encore terminer l'écriture précédente), et seulement sur une erreur de transport reconnue à son texte exact
  (`HTTP Error 502/503/504`, `Connection refused`, `Connection reset by peer`, `Remote end closed connection`). **Jamais
  sur un délai dépassé** (le serveur a pu continuer à écrire), **jamais sur un geste**. Précaution : aucune écriture en
  double n'a été observée ; la relance repose sur l'idempotence déclarée des scripts, lue dans le code, jamais éprouvée
  sur un échec réel.
- **Ligne `controle`** : quand les écritures d'une ligne ont réussi mais que le relevé du contrôle a échoué, on rejoue
  le seul contrôle, en lecture ; la ligne elle-même est refusée tant que ce contrôle est en attente. Même chemin après
  une décision du propriétaire d'admettre un écart : le contrôle est corrigé (diff soumis), le fichier d'état reçoit
  `controle_en_attente`, et **le lanceur revérifie lui-même** — une ligne n'est jamais marquée OK à la main.
- **Date simulée** : chaque étape la vide en partant et la relit ; après un arrêt, une ligne `reset-date` la vide, sauf
  pause voulue (piège 171), qu'on signale.
- **Lancement en arrière-plan** : une ligne peut dépasser le délai d'un appel d'outil ; on la lance en tâche de fond et
  on attend sa fin.

*Démo BTP de référence : le lanceur du kit, 17 lignes plus `reset-date` et `controle`. Après l'arrêt de l'étape 06 et la
décision de l'utilisateur, `controle_en_attente` posé, puis « LIGNE 06 : OK (contrôle rejoué) » à 19 h 53.
Écart à la règle : ce lanceur ne comptait pas les réserves écrites par le script
(relecture adverse, défaut 10) ; le contrôle de l'étape les aurait vues ensuite.*

## 7. Une passation d'exécution, relue en adverse avant de lancer

La passation est un prompt autoportant pour un **exécutant pur** : ni amélioration, ni correction, ni contournement ;
KO = arrêt. Elle dit ce qui a été éprouvé et ce qui ne l'a pas été. Avant l'exécution, un relecteur au contexte neuf la
relit **contre le code et les références**, pas contre elle-même ; chaque défaut est traité ou accepté explicitement
par le propriétaire de la démo.

*Démo BTP de référence : première relecture NO-GO, 16 défauts dont un bloquant — la retenue de 136 € posée par le geste aurait fait
échouer les contrôles 09, 10 et 10-pilotage après des écritures irréversibles, et la passation affirmait répétés des
scripts modifiés depuis (piège 192) ; seconde relecture GO avec réserves, trois majeurs : relance de toute la ligne
quand seul le relevé échouait, relance sur 50x ou délai dépassé alors que le serveur peut encore écrire, absence de
verrou. Tous traités.*

### 192. Un script modifié après sa répétition n'est plus répété

`[constaté par les relectures du 2026-09-26]` La passation affirmait « la répétition a joué exactement ce déroulé ».
Les dates de fichiers disaient autre chose : le geste d'avenant modifié à 15:49 UTC, après son usage (journal de
l'étape 7 à 15:15) ; le geste de sous-traitance modifié à 16:24, après toutes les références (au plus tard 15:57) et
après le dump final ; aucun journal des deux gestes. À la seconde relecture, le lanceur lui-même avait été modifié à
16:50, pendant l'étape 9 de validation : sa version finale n'avait joué aucune ligne d'écriture.

**À faire :** avant la passation, comparer la date de modification de chaque script, du lanceur et du contrôle à celle
du journal de répétition qui l'a exercé. Tout fichier modifié après se rejoue sur la répétition, depuis un palier
restauré, ou s'écrit « non éprouvé » dans la passation.

## 8. Estimer la durée en comptant les appels

### 191. Estimer la durée d'un rejeu distant par le nombre d'appels de la répétition et le débit mesuré, pas au jugé

`[mesuré le 2026-09-26, instance hébergée, journaux du rejeu]` La passation estimait les durées
« à distance » au jugé : 15 min pour l'étape 06, 30 à 60 min pour la 9 b, 1 à 2 h pour la 10. Mesuré :

| Ligne | Appels (journal de la ligne) | Durée | Débit |
|---|---|---|---|
| 06 | 804 | 4 min 18 | 3,1 appels/s |
| 09b | 2 504 | 11 min 11 | 3,7 appels/s |
| 10 | 7 297 | 27 min 50 (27 min en local) | 4,4 appels/s |

De 3 à 4,5 appels par seconde sur les lignes longues, du même ordre qu'en local : les estimations de la passation
étaient **2 à 6 fois trop longues pour les lignes de plus d'une minute** (ligne 10 : 1 à 2 h prévues, 28 min
réelles ; ligne 09b : 30 à 60 min prévues, 11 min), et bien davantage pour les lignes de quelques secondes. Des délais
larges ne gênent pas le lanceur (jusqu'à 6 h pour la ligne 10) ; mais le calendrier, le gel et la présence de
l'utilisateur se bâtissent sur l'estimation.

**À faire :** compter les appels de chaque ligne dans les journaux de la répétition (« Rejeu termine (N appel(s)) »),
mesurer le débit sur une première ligne courte de la cible, multiplier ; garder des délais larges.

## 9. Risques d'une exécution longue dans un conteneur sur un poste portable

- **La veille du poste hôte suspend le conteneur** (ou la VM), et avec lui la ligne en cours : la suspension est
  établie (après une veille, `ps` décale les heures de lancement du temps de sommeil) ; son effet sur une ligne
  en cours est déduit, jamais vécu pendant un rejeu (coupure de connexion probable au réveil). Tenir le poste
  branché et éveillé pendant le rejeu ; après une veille, lire l'horloge et les journaux, pas `ps`.
- **Archiver une session Claude Code tue ce qu'elle héberge** : constaté le 24/09 sur des sessions lancées dans son
  panneau terminal (application de bureau) ; pour les commandes qu'elle a lancées
  en arrière-plan, c'est déduit (ce sont ses processus enfants). Ne rien archiver ni fermer tant qu'une ligne tourne ;
  une ligne tuée est un échec non réseau : arrêt et rapport.
- **Personne d'autre sur la cible** pendant le rejeu : la date simulée vaut pour toute l'application.

## 10. Sauvegarder le kit et les données sur un remote

À la fin, déposer sur un dépôt distant ce qui permet de refaire le rejeu : scripts, outil de relevé et références,
documents, journaux (compressés s'ils sont ignorés par git), copie de la base de secours avec son empreinte, et
l'archive des pièces jointes que la base référence (piège 116). Choisir une branche où un push ne déclenche rien ;
contrôler l'absence de secrets et les fichiers ignorés avant de pousser.

*Démo BTP de référence : dossier `seed/` d'une branche de démo dédiée d'un dépôt distant (le 26/09). Un push seul
sur une branche de démo n'y créait aucune pipeline : les règles `workflow` du `.gitlab-ci.yml` n'acceptaient que
« Run pipeline » depuis l'écran et les merge requests (relu le 26/09). Copie de base, empreinte et pièces jointes
décrites dans un `LISEZMOI.md` de la branche.*
