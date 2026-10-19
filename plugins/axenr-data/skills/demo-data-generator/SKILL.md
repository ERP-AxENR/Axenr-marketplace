---
name: demo-data-generator
description: >
  Produit des donnees dans une base Axelor (AOS/AOP) : demo prospect ou
  client, formation, capture marketing, jeu d'essai de recette. Cadre d'abord
  le scenario metier (identite, histoire, volumetrie par ecran, horloge), puis
  derive la surface technique par introspection, produit du SQL idempotent, des
  appels REST ou un bundle d'import, et audite le resultat. Deux regimes :
  completer un jeu troue, ou generer le volume commande. Declencheurs : « ma
  demo est vide », « il manque des donnees », « peuple », « complete »,
  « genere 50 affaires », « prepare la base pour la demo », « donnees
  incoherentes », « scenario de demo », demo data, seed, populate. PAS pour :
  importer les donnees reelles d'un client (axelor-import-export), creer des
  profils et des droits (axelor-droits-expert), modeliser un questionnaire
  d'intervention (seeding-axelor-intervention-surveys).
metadata:
  owner: axenr
  family: fonctionnel
---

# Demo Data Generator

> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.3 à 9.1.8 /
> AOP EE 8.2.3 et 8.2.4, de bout en bout. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège
> est une hypothèse à vérifier sur la base cible avant d'agir ou de renoncer à cause de lui.

## Environnement d'exécution

| Où | Comportement |
|---|---|
| claude.ai et Cowork | Pas d'accès à la base : cadrer le scénario (Phase 1), écrire le contrat, produire les fichiers (SQL idempotent ou bundle CSV + XML) à exécuter par l'utilisateur, avec la liste des contrôles d'audit à lancer. |
| Claude Code | Introspection, écriture et audit par les scripts de `scripts/` (`psql`, `python3`, `node`, `bash` 4). Connexion par `PGHOST` / `PGUSER` / `PGPASSWORD` ou session REST ouverte par l'utilisateur ; jamais de mot de passe dans la conversation. |

Sûreté avant tout passage : la base est-elle jetable, ou un dump filet existe-t-il ? Une base de
recette ou de production client ne s'écrit qu'avec un feu vert explicite. `scripts/audit-completeness.sql`
crée et alimente la table `public.zz_audit_invariants` (référence des invariants, dimension 13) :
à signaler au demandeur avant le premier passage. `scripts/align-pk-sequences.sql` avance des
séquences et affiche le SQL de retour arrière : conserver sa sortie.

## Contexte AxENR

- Les démos AxENR sont orientées énergies renouvelables : installateur PV, IRVE, pompes à
  chaleur ; CRM, suivi d'affaire (modèles d'affaire, tâches, jalons administratifs), GMAO
  (installations, contrats de maintenance, interventions). Le vocabulaire, les gammes et les
  délais du scénario viennent de ce métier, jamais d'un secteur générique.
- GMAO : le site est porté par le **tiers**, la racine du parc est l'installation, et tout
  équipement mono-produit a sa ligne d'équipement (`references/entites-gmao.md`, pièges 222 et 223).
- Vraisemblance métier : s'appuyer sur `enr-coherence-checker` (une donnée au bon moment du
  cycle commercial, généricité multi-ENR) pour valider le contrat de scénario avant la Phase 2.
- Bundles d'import (voie sans accès base) : renvoyer vers `axelor-import-export` pour le
  mécanisme d'import ; ce skill ne couvre que ce qui est propre aux données de démo.
- Profils et droits des comptes de démo : `axelor-droits-expert`, jamais de groupes fabriqués
  à la main.

**Peuple une base de démo Axelor avec des données riches, cohérentes et crédibles — tous métiers.**

Moitié **aval** de la paire : reçoit un contrat de scénario en langage métier, en dérive la surface
technique par introspection de la base réelle, produit un livrable idempotent qui respecte les
contraintes, les FK et les conventions Axelor, puis audite ce qu'il a écrit. Le demandeur reste en
vocabulaire métier ; la structure de stockage est décidée ici.

## Si vous ne lisez qu'une chose : les 12 règles cardinales

Chacune a coûté un aller-retour réel. Les `references/` les détaillent et documentent les cas par
entité — mais un piège dans un fichier non ouvert n'existe pas : ces douze-là tiennent seules.

0. **Règle zéro — connaître le socle avant de produire quoi que ce soit.**
   Lire `references/socle-aos-baseline.md`. Une install AOS livre déjà **470 tables peuplées**
   (dont NAF 732, PCG 1 044 comptes, 246 pays, 166 devises, 75 tiers, 80 produits, 21 employés,
   **et toute la couche droits** : 30 groupes, 33 rôles, 243 permissions). Les réinjecter est du
   travail perdu qui collisionne. **155 tables** sont au contraire vides d'origine : c'est là
   qu'il faut travailler. Et **709 tables** sont vides même après une démo réelle : ce sont des
   angles morts, ne pas prétendre les couvrir.
   Corollaire : un audit de complétude en valeur absolue ne vaut rien — auditer **en delta contre
   le socle**, sinon « vide parce qu'AOS ne le remplit jamais » et « vide parce qu'on a oublié »
   sont indistinguables. Ne jamais trier via `import_id`, `import_origin` ou `created_on` : vérifié
   faux dans les deux sens. Pour ces 155 tables, `references/socle-b-shape.md` donne la **shape**
   (colonnes renseignées, taux, colonnes restées vides) et signale celles qui **doivent être
   générées par le moteur** : rapports projet, feuilles de coût, ordres d'opération. Outils :
   `scripts/baseline-map.sh` régénère la carte, `scripts/fk-closure.py <base> <table>…` donne la
   fermeture FK avant d'arrêter un périmètre.
1. **Introspecter avant d'écrire.** `scripts/introspect.sh <base> <table>` sort en une passe : les
   colonnes et leur type, les NOT NULL, les FK et leur cible, **les sélections avec leurs valeurs
   valides**, les enfants O2M et les jonctions M2M. Supposer un type ou une valeur de sélection est
   la première cause d'échec.
2. **Remplir un maximum de champs utiles, pas seulement les NOT NULL.** Une fiche à moitié vide
   décrédibilise l'ERP plus qu'un enregistrement manquant : l'utilisateur ouvre **un** enregistrement
   et regarde tous les onglets. Passer les colonnes une par une et justifier chaque champ laissé vide.
   Nuance qui inverse la règle : une **mesure sans son unité est pire qu'un champ vide** (piège 88) —
   `length` sans `length_unit`, `net_mass` sans `mass_unit` affichent « 2,4 » sans dire si ce sont des
   kilos ou des livres. Poser l'unité dans le même `UPDATE` que la valeur, et asserter la cohérence
   métier (`gross_mass > net_mass` : l'emballage pèse).
   Second contrepoint : **utile veut dire propre à la fiche.** Un commentaire ou une note reçoit une
   information propre à la fiche, ou reste vide — jamais un gabarit ; le vide se justifie dans le
   rapport, jamais dans le champ, et les descriptions restent attendues (`references/surface-tiers-articles.md`
   §2 et §8) ; l'audit (dimension 4bis) liste les phrases répétées. *Coût payé le 2026-09-27 (essai 1,
   Industrie 9.1.7) : 30 des 34 défauts bloquants.*
3. **Aucun booléen NULL — et aucun booléen laissé de côté.** Un flag NULL est exclu des grids et
   des pickers (`is_model IS NULL` rend un produit invisible dans une ligne de vente) : poser
   `true`/`false` explicite sur **tous** les booléens de la table, pas seulement ceux qui paraissent
   principaux (piège 62). Symétriquement à la lecture : `= false` **exclut les NULL** (piège 76).
   Un domaine de vue en `self.expense = false` a masqué 20 produits dont `expense` était NULL —
   présents en base, sélectionnables ailleurs, jamais affichés au catalogue ; et un audit écrit en
   `= false` déclare conforme une base trouée. Auditer en `IS NULL` / `IS NOT TRUE`.
4. **Aucune sélection inventée.** Prendre une valeur de la liste réelle ; `0` est souvent invalide. Et
   certaines sélections sont des **unités**, pas des quantités (`horizon.value.select` = 0 Day / 1 Week / 2 Month, pas un nombre de jours).
   Une valeur fausse ne lève rien : elle produit un champ vide, un enregistrement filtré hors d'une
   liste, ou une exception tardive dans un service qui branche dessus. C'est une règle facile à
   énoncer et facile à enfreindre — `scripts/check-selects.sh <base> <tag> <.axelor>` balaie d'un
   coup **toutes** les valeurs écrites sous le tag, et distingue une invention d'une valeur neutre
   du socle. À passer avant l'audit de la Phase 4, pas après.
5. **`name` / `fullName` ne se calculent pas en SQL** → les poser à la main, sinon les M2O affichent
   un libellé vide. Et une concaténation nue (`seq || ' - ' || name || ' ' || first_name`) rend NULL dès
   qu'un composant est NULL : `full_name` NULL = enregistrement **invisible** (piège 71). Envelopper
   chaque composant dans `COALESCE`, respecter la convention de l'entité (contact : prénom inclus,
   piège 72), et recalculer `full_name` à chaque renommage (piège 70).
6. **Une FK résolue par sous-requête écrit NULL EN SILENCE** si le libellé est faux. Toujours
   `AND EXISTS (SELECT 1 FROM <ref> WHERE …)` dans le WHERE, **et** une garde finale qui lève.
7. **Un header sans ses satellites est inutilisable.** Remplir les enfants O2M et les jonctions M2M
   (sections 5 et 6 de la sortie de `scripts/introspect.sh`). Une table « peuplée » avec des panneaux
   vides ne compte pas.
8. **Prendre un enregistrement existant comme modèle de shape** avant de créer : il révèle les
   satellites attendus et le format réel d'un champ (une trame HTML, pas une phrase).
9. **Auditer contre le contrat et sur tous les niveaux, jamais contre son propre script.** Trois
   fautes rendent un audit vert sur une base fausse. (a) `count()` compte `0`, `0.00` et `''` comme
   « rempli » : vérifier les **valeurs**, pas la présence. (b) Un contrôle qui teste ce que le script
   **écrit** est fermé sur lui-même — 16 contrôles ont rendu « 0 anomalie » alors qu'un engagement du
   contrat était NULL sur 100 % des créations (piège 82) : dériver les assertions du contrat ligne à
   ligne, et comparer au **socle** plutôt qu'au vide (79 des 85 produits d'origine portaient ce champ
   resté vide). (c) Un piège a rarement un seul niveau — un renommage a laissé du vocabulaire périmé
   sur **cinq** niveaux de dénormalisation, dont un sur des enfants orphelins invisibles à tout
   contrôle passant par la relation évidente (piège 92) : chercher les dénormalisations par la
   structure, balayer aussi les lignes dont la FK attendue est NULL.
10. **Cohérence inter-champs** : les paires corrélées doivent tenir ensemble (code NAF ↔ secteur
    d'activité, secteur ↔ employeurs du CV, libellé géographique ↔ adresses réelles). Si le
    référentiel n'offre aucune valeur pertinente, **créer la valeur** — jamais prendre au hasard.
    Un nom en est une : **aucun nom ne se pose au hasard, y compris sans contrat de scénario**
    (Mode A — patch de complétude, où personne d'autre ne porte cette exigence). `WebSearch` sur le
    secteur, la région et le métier avant de nommer une société, un produit, une gamme ou un
    ouvrage ; principe **inspiré, pas copié** — on ne rhabille pas une entreprise réelle
    identifiable en tiers fictif, on reprend des formes, des suffixes, des spécialités, du
    vocabulaire métier. Proscrit à vue : « Client 1 », « Produit test », « Société ABC », toute
    série numérotée — un nom générique décrédibilise aussi vite qu'un champ NULL.
11. **Le temps est une relation, pas un champ.** Toute date se pose depuis l'horloge du contrat
    (date pivot, fenêtre, jalons) et respecte l'ordre des pièces qui se référencent : une pièce aval
    n'est jamais antérieure à son amont, un enfant reste dans la fenêtre de son parent, un statut
    terminé a une date passée, un brouillon n'a pas de date de validation. L'offset se **dérive de
    l'entité liée** (`employee * 11 % 90` jours), jamais constant — sinon tous les rendez-vous
    tombent le même jour ; et les dates dérivées se vérifient (une formule bâclée a produit des
    candidats de 9 ans). Les dates techniques (`created_on`, `updated_on`) s'alignent sur la date
    métier ou s'étalent, jamais toutes à la même seconde — ça se lit comme un import. Celles que le
    moteur dérive (échéance, `estimated_date`, date de calcul d'une feuille de coût) ne s'écrivent
    pas en SQL : elles s'héritent de dates prévues saisies avant le flux, ou se redatent après.
    Graphe de précédence, délais par défaut et audit temporel : `references/methode-dates.md`.
12. **Le SQL pose un ÉTAT, il ne simule pas une TRANSITION.** Test : le moteur produirait-il quelque
    chose que le SQL devrait ensuite réécrire (totaux, écritures, lignes dérivées) ?
    **Oui → le moteur** — commande, facture, mouvement de stock, ordre de fabrication, feuille de
    coût. **Non → le SQL**, en consommant la séquence (piège 73), en recopiant les dénormalisations
    (piège 74) et en rattachant un contact **du tiers de l'affaire** : une opportunité CRM n'a pas de
    lignes, `amount` / `best_case` / `worst_case` / `probability` sont saisis, aucune contrepartie
    comptable — leads, opportunités et événements se seedent en SQL. Les services de conversion
    (Lead → Opportunité → Commande) créent des objets liés multi-modules : eux restent au moteur.
    « Moteur » ne veut pas dire « clic à la main » : un bouton AOS est une `action-method` appelable
    en REST sur `/ws/action`, donc scriptable et rejouable. La frontière est **SQL contre moteur**,
    pas SQL contre UI — budgéter N clics manuels sans avoir cherché le point d'entrée du bouton est
    une erreur de chiffrage.
    **Troisième cas — moteur PUIS SQL de complétion.** Le moteur n'est pas garant de la couche
    UI-critical : un bouton de génération a créé 85 tâches avec type, assignation et date posés, mais
    `status` et `full_name` à NULL — les deux colonnes qui décident de la visibilité (4 des 7 menus
    filtrent `status.isCompleted`) et de la lisibilité. Après toute génération par le moteur,
    reprendre les colonnes de visibilité de la fiche `entites-*.md` concernée et compléter en SQL ce
    qu'il laisse NULL. *Coût payé le 2026-09-03 : 85 tâches en base, panneau « Phases et tâches » à
    0 ligne et « RAT incomplet — aucune tâche » sur la fiche héros.*
    Attention : **Un statut de flux physique est une TRANSITION déguisée en état** : « reçue » et « livrée »
    sont les conséquences d'un mouvement de stock réalisé ; un OF porte ses mouvements dès la
    planification — créés et planifiés par le moteur, réalisés au démarrage ou à la fin selon la
    gamme (`ManufOrderPlanServiceImpl` l.186-223, 9.1.3 ; piège 143).
    Posés en SQL sans eux, ces statuts se voient au premier clic (commande reçue sans bon de
    réception, OF sans mouvement). Moteur, ou état antérieur (validée non reçue ; OF brouillon, ou
    planifié par le moteur) ; un raccourci assumé se livre comme une limite visible, écrans compris
    (pièges 143 et 149). *Coût payé le 2026-09-23 : 27 achats « reçus », 25 OF démarrés et 7 ventes
    « livrées » sans un seul mouvement, découverts en navigation la veille de la démo — la limite
    n'était écrite que dans le rapport du lot.*
    Attention : **Ordre des passes, sur une base dont l'application TOURNE** : tout `UPDATE` SQL postérieur à
    un appel de moteur sur le même enregistrement est invisible à l'écran **et** sera réverti au
    prochain enregistrement fait depuis la fiche (pièges 52 et 96). Donc **SQL avant moteur**, ou
    repasser par le moteur après. *Coût payé le 2026-09-03 : `contact_partner = 9` en base,
    `contactPartner: null` rendu par l'application ; un simple enregistrement depuis l'écran aurait
    effacé l'alignement en silence, pendant la démo.*
    **Et quand la correction SQL doit vraiment venir APRÈS le moteur, la passe a trois temps, pas
    deux : SQL, puis REDÉMARRAGE, puis rappel du moteur.** Sans le redémarrage, le cache de second
    niveau sert les anciennes valeurs au recalcul, qui rend le même résultat faux — sans erreur, sans
    avertissement. *Coût payé le 2026-09-22 (9.1.3) : durées réelles corrigées en base sur 96 ordres
    de fabrication, coût recalculé sans redémarrer → feuille toujours à 0,00 € (piège 125).*
    Attention : **« Un bouton AOS est scriptable » a deux conditions que cette règle ne disait pas.**
    (a) Un `POST /ws/rest` **n'exécute aucun `onChange`** : la ligne créée sort sans prix, sans taxe,
    sans unité — c'est l'action de remplissage de la ligne qu'il faut appeler d'abord, une fois par
    article, et mettre en cache (piège 131). (b) Une action de calcul appelée avec
    `{"context":{"id":N}}` répond `status: 0` et **zéro clé** : le contexte doit être l'enregistrement
    **entier**, relu par `POST /ws/rest/<modèle>/<id>/fetch` (corps `{}` ; piège 132). Chiffrer un pilotage REST
    sans ces deux conditions est l'erreur symétrique de celle que la règle dénonce juste au-dessus.
    **Quand la fiche doit MONTRER l'état aval, sa chaîne amont se joue — elle ne se renvoie pas au
    demandeur.** Un état aval suppose sa chaîne : un stock suppose des réceptions (négoce), un avancement
    facturé des situations (BTP), un parc « en service » ou une machine facturée des ordres de fabrication
    terminés puis livrés (industrie : `references/entites-production-btp.md`, pièges 125 à 129). L'« état
    antérieur » (Attention : « Un statut de flux physique… », plus haut) n'est un raccourci que si le contrat
    n'exige pas l'état aval ; sinon
    jouer au moins la chaîne des fiches héros, sur une base jetable ou avec un dump filet (c'est la question
    de sûreté de la Phase 1), et ne pas finir sur « faut-il jouer la fabrication ? ». *Coût payé le
    2026-09-27 (essai 0, Industrie 9.1.7) : 7 machines confirmées ni fabriquées, ni livrées, ni
    facturées, parc « hors service », et la question renvoyée en fin de rapport — un aller-retour.*
    Frontière complète, dont la création de société qui ne se fait jamais en
    SQL : `references/socle-aos-baseline.md` §6.

**Un piège décrit une base, pas AOS.** Chaque piège a été constaté sur une base donnée, avec ses apps,
ses référentiels et sa version. Avant d'agir sur un piège — ou de renoncer à cause de lui — vérifier sa
condition sur la base cible (app active, référentiel présent, option cochée, version). *Coût payé le
2026-09-27 (essai 0, Industrie 9.1.7) : le piège 184 (« le virement exige l'app Paiement bancaire,
inactive ») appliqué sur une base où l'app est ACTIVE — aucun règlement fournisseur saisi, sur une
prémisse jamais vérifiée.*

## Règle de sûreté — ne pas toucher à ce qu'on n'a pas créé

La base est presque toujours partagée, souvent sans dump filet, et une donnée pré-existante
appartient à quelqu'un d'autre. Critères à tenir sur chaque script :

- aucune suppression de données existantes, aucun `TRUNCATE`, aucun `DROP` ;
- aucun `UPDATE` sur un enregistrement **pré-existant** qu'on n'a pas inséré soi-même — mettre à
  jour ce qu'on vient d'insérer dans la même transaction (totaux d'ouvrage calculés) est légitime ;
- aucun identifiant en dur qui puisse collisionner : lire `max(id)` d'abord, et avancer la séquence
  **après** les insertions, dérivée du maximum réellement occupé (piège 73) — un `setval` posé avant
  d'insérer laisse le compteur en retard et le premier enregistrement créé par l'UI collisionne ;
- rien qui touche un enregistrement **archivé** : filtrer `COALESCE(archived, false) = false` dans
  toute passe de renommage ou d'enrichissement (piège 79).

**La crédibilité est une affaire de distribution, pas de volume.** Cas réel : 95 projets, 270 tâches,
dont **13 projets à 0 tâche** et **77 à exactement 3** — copier-coller visible au premier clic.
Règles en §5 de `references/socle-aos-baseline.md` : aucun parent à 0 enfant sur un axe démontré,
profondeur en traîne longue jamais constante, des enregistrements héros à 5-10× la médiane, et **la
largeur avant le volume** (AOS livre 75 tiers dont 38 % des colonnes sont à 100 % NULL — mieux vaut
20 tiers complets). Après écriture, l'audit de la Phase 4 est obligatoire ; son contrôle
visuel vient *avant* de déclarer une table terminée, pas après.

## Deux modes de peuplement — les distinguer AVANT tout

Même exigence de qualité, mais objectifs, volumétries et techniques **opposés** : les confondre est
la première erreur de cadrage.

| | **Mode A — Patch de complétude** | **Mode B — Génération à la demande** |
|---|---|---|
| Déclencheur | « la démo est trouée », « ce panneau est vide », « il n'y a qu'un exemple et il est pauvre » | « crée 50 OF », « 200 produits », « une affaire complète : 5 commandes + 300 feuilles de temps » |
| Objectif | **Aucun écran vide** : chaque menu ouvert doit avoir de quoi montrer | **Répondre à la commande** : la volumétrie et le métier demandés |
| Volumétrie | **Celle du contrat de scénario.** À défaut, les seuils **par écran** de `references/cadrage-scenario.md` (étape 5 « Dimensionner par écran ») : liste 8 à 15 lignes avec plusieurs statuts, **chaque** colonne de kanban à 2-5 cartes, calendrier garni en passé / présent / futur, 12 points sur un indicateur, aucune tuile à zéro | **Celle qui est demandée.** Ne pas la réduire « pour faire propre » |
| Contenu | Le contrat le porte ; le combler est une dérivation, pas une invention | L'utilisateur l'impose ; votre travail est de le rendre crédible |
| Technique | `VALUES` explicites, contenu écrit à la main | **Génération** : `generate_series`, croisements, distributions |
| Métier | L'identité du contrat suffit | **Le métier doit être exact** : vocabulaire, process, gamme, unités |
| Audit | Couverture : reste-t-il un écran vide sous son seuil ? | Volumétrie atteinte **et** cohérence métier tenue |

**Mode A** est un *constat* : « il manque un exemple de liste de prix, 0 prospect, une seule
candidature et elle est pauvre → je complète jusqu'au seuil de l'écran concerné ». Ne pas interroger
longuement : introspecter, constater, écrire une matrice courte (dans la salve de départ si une
décision revient au demandeur, sinon en tête du rapport), exécuter. **Mode B** est un
*cadrage* : la volumétrie est donnée, c'est le **métier** qui doit être instruit
(`references/mode-b-volume.md` §1). Une demande peut mélanger les deux (« complète ce qui manque
**et** crée-moi 50 OF ») : deux passes distinctes, chacune avec sa volumétrie.

## Prérequis et dépendances

**Obligatoires** (sans eux le skill s'arrête ou perd l'essentiel de sa valeur) :

| Outil | À quoi il sert ici |
|---|---|
| Une base Axelor Open Suite / Open Platform sur PostgreSQL | cible du peuplement : voie SQL = accès en écriture ; voie API = instance joignable en HTTP avec un compte autorisé (instance hébergée comprise) |
| `psql` (client PostgreSQL) | introspection, écriture SQL, audit (`scripts/introspect.sh`, `audit-completeness.sql`…) ; connexion par les variables `PGHOST`, `PGUSER`, `PGPASSWORD` (ou le fichier de mots de passe de psql), jamais en dur dans un script |
| `bash` (4 ou plus : `shape-fiche.sh` utilise des tableaux associatifs ; sous macOS, le bash de Homebrew) et `python3` | tous les scripts de `scripts/` |
| `node` | évaluation des conditions de vue (`scripts/form_coverage.py` appelle `scripts/evalconds.js`) |
| `curl` | session REST, appels `/ws/rest` et `/ws/action` à la main |
| `jq` et `awk` | `scripts/shape-fiche.sh` |
| Python : `Pillow` (`pip install Pillow`) | `scripts/generate_visuals.py` seulement |
| Les sources de la version qui TOURNE (clone git du tag AOS/AOP, ou classes décompilées des jars déployés) | lire un comportement avant d'écrire (piège 215), `scripts/check-selects.sh` |

**Optionnelles** (comportement du skill sans elles) :

| Dépendance | Rôle | Sans elle |
|---|---|---|
| MCP Playwright (ou tout navigateur piloté) | vérifier un écran, relever la requête d'un bouton (pièges 91 et 210) | onglet Réseau des outils de développement du navigateur ; contrôle par l'API REST (piège 94) |
| `WebSearch` / `WebFetch` (outils de Claude Code) | recherche d'inspiration pour les noms (règle 10) | demander au demandeur la gamme et le secteur, inventer des formes sans copier ; jamais de « Client 1 » |
| `pdfinfo` (paquet poppler-utils) | vérifier des PDF minimaux posés comme pièces jointes (piège 116) | ouvrir le PDF à la main |
| Dossier de rejeu (scripts de rejeu par l'API : lanceur, outil de relevé, références, journaux) | `references/methode-rejeu-controle.md` et les entrées « rejeu » de `references/entites-production-btp.md` décrivent le kit d'une démo de référence | **fourni par l'utilisateur** ; ce skill n'en livre aucun : appliquer la méthode avec ses propres scripts |
| Skills AxENR : `axelor-import-export` (voie bundle), `axelor-droits-expert` (groupes et droits), `enr-coherence-checker` (vraisemblance ENR) | import par bundle, profils, cohérence métier | suivre `references/csv-xml-bundle.md` ; ne pas fabriquer de groupes à la main ; relire le contrat contre le cycle commercial ENR |

### Session REST sans accès à la base (recette curl)

Pour une instance sans accès à la base, les scripts qui parlent à l'API (`form_coverage.py`,
`generate_visuals.py`) lisent trois variables d'environnement : `AOS_URL` (URL de l'application, sans slash
final), `AOS_COOKIE_JAR` (fichier de cookies au format curl, avec `JSESSIONID`) et `AOS_CSRF` (jeton CSRF).
Les obtenir à la main, **dans le terminal de l'utilisateur** — le mot de passe est saisi sans écho, lu sur
l'entrée standard, et n'est jamais écrit dans un fichier, une commande ni le transcript :

```bash
export AOS_URL="https://<hôte>/<application>"          # sans slash final
export AOS_COOKIE_JAR="$(mktemp)"                       # à supprimer en fin de séance
read -rs -p "Mot de passe : " PW; echo
printf '%s' "$PW" | curl -s -o /dev/null -c "$AOS_COOKIE_JAR" -b "$AOS_COOKIE_JAR" -X POST \
     "$AOS_URL/callback?client_name=AxelorFormClient" \
     --data-urlencode "username=<login>" --data-urlencode "password@-"
unset PW
# contrôle : la réponse doit porter une clé "user" (avec le login) ; sans session valide, cette route
# publique répond quand même du JSON, mais sans "user" (seulement "application" et "authentication")
curl -s -b "$AOS_COOKIE_JAR" -c "$AOS_COOKIE_JAR" -H 'Accept: application/json' "$AOS_URL/ws/public/app/info"
# Jeton CSRF = valeur du cookie CSRF-TOKEN du fichier, à renvoyer en en-tête X-CSRF-Token sur POST/PUT/DELETE
export AOS_CSRF="$(awk -F'\t' '$6=="CSRF-TOKEN"{print $7}' "$AOS_COOKIE_JAR" | tail -1)"
```

Une réponse de contrôle sans clé `user`, ou un appel `/ws/rest` qui rend une page HTML, un 401 ou un 403,
signifie une session absente ou expirée : rouvrir la session plutôt que d'insister. Un compte créé par l'API peut
naître bloqué (piège 105). Les variables exportées dans ce terminal ne sont vues par Claude Code que s'il est lancé
ensuite depuis ce même terminal ; sinon, donner à Claude l'URL et le chemin du fichier de cookies (jamais le mot de
passe) : il pose `AOS_URL` et `AOS_COOKIE_JAR` dans ses propres commandes et relit `AOS_CSRF` dans le fichier, par
la même ligne `awk`.

## Table de routage

Ce SKILL.md ne détaille plus les pièges par entité ni l'architecture SQL : il route vers `references/`,
par besoin puis par phase (le workflow porte aussi ses renvois directement).

| Besoin | Fichier |
|---|---|
| Cadrer le scénario métier (identité, histoire, volumétrie par écran, horloge, contrat) | `references/cadrage-scenario.md` |
| Connaître le socle avant de produire (ne rien réinjecter) | `references/socle-aos-baseline.md` |
| Shape des 155 tables vides du socle (régénérée par `scripts/baseline-map.sh`, qui appelle `scripts/socle-b-shape.py`) | `references/socle-b-shape.md` |
| Introspecter une base cible avant d'écrire | `references/methode-introspection.md` |
| Architecture SQL multi-fichiers, idempotence | `references/methode-ecriture-sql.md` |
| Dates cohérentes entre pièces, redatage, audit temporel | `references/methode-dates.md` |
| Auditer une table déjà peuplée | `references/methode-audit.md` |
| Cohérence inter-champs, dénormalisations désynchronisées | `references/methode-coherence.md` |
| Extraire / rejouer un jeu de données sur base vierge | `references/methode-rejouabilite.md` |
| Rejouer un jeu par l'API vers une instance sans accès base (hébergée), contrôlé étape par étape (dossier de rejeu fourni par l'utilisateur) | `references/methode-rejeu-controle.md` |
| Générer un volume à la demande (Mode B) | `references/mode-b-volume.md` |
| Livrable bundle CSV + XML (pas d'accès DB) | `references/csv-xml-bundle.md` |
| Tiers, contacts, adresses, événements CRM | `references/entites-tiers-contacts.md` |
| Produits, familles, unités | `references/entites-produits.md` |
| Ventes : commandes, lignes, factures | `references/entites-ventes.md` |
| Projet, tâches, temps, plan de charge | `references/entites-projet-temps.md` |
| Production, BTP, ouvrages ; DPGF et bilan d'affaire (module construction) | `references/entites-production-btp.md` |
| Achats : commandes fournisseur, lignes, tarifs, rattachement à l'affaire | `references/entites-achats.md` |
| CRM : leads, opportunités, événements, motifs de perte | `references/entites-crm.md` |
| Stock : mouvements, emplacements, quantités, chaîne de réception | `references/entites-stock.md` |
| Qualité : gammes et relevés de contrôle, améliorations qualité (AQ), processus, audits, alertes | `references/entites-qualite.md` |
| GMAO : parc d'équipements, contrats de maintenance, lignes de planification, interventions | `references/entites-gmao.md` |
| Tableaux de bord, graphiques ou indicateurs de l'application mobile, accueil du téléphone, vues web | `references/tableaux-de-bord-mobiles.md` |
| **Remplir une fiche Tiers, Contact ou Article à 100 % de ce que l'écran affiche** (onglets, listes, tableaux de bord, réalisme par type de fiche, options d'app qui ajoutent des blocs) | `references/surface-tiers-articles.md`, mesure par `scripts/form_coverage.py` |
| Photos d'articles, logos de sociétés (visuels sobres, jamais par-dessus une image existante) | `scripts/generate_visuals.py`, `references/surface-tiers-articles.md` §9 |
| Configurateur commercial : attributs, formules, indicateurs, nomenclature et gamme générées | `references/entites-production-btp.md` (pièges 99 à 103) |
| RH, comptes utilisateurs (sections courtes) | `references/entites-autres.md` |
| Chercher un piège par son numéro | `references/index-pieges.md` |
| Vérifier les valeurs de sélection écrites | `scripts/check-selects.sh <base> <tag> <.axelor>` |
| Réaligner les séquences PK Postgres en retard sur `max(id)` (dimension 7e de l'audit : la création depuis l'écran plante) | `scripts/align-pk-sequences.sql` |
| Pièges runtime constatés sur AOS 9.1.7 | `references/pieges-runtime-aos-9-1-7.md` |

| Phase | Lire |
|---|---|
| Phase 1 — Contrat | `references/cadrage-scenario.md` (méthode et format du contrat) ; `references/mode-b-volume.md` §1 si Mode B (instruire le métier) |
| Phase 2 — Dérivation | `references/socle-aos-baseline.md`, `references/socle-b-shape.md`, `references/methode-introspection.md` |
| Phase 3 — Construire | `references/methode-introspection.md` avant d'écrire, `references/methode-ecriture-sql.md` pour l'architecture, `references/methode-dates.md` pour poser les dates, la ou les fiches `entites-*.md` du domaine visé (tiers-contacts, produits, **ventes**, **projet-temps**, **achats**, **crm**, **stock**, qualite, **gmao**, production-btp, autres), `references/surface-tiers-articles.md` dès qu'une fiche Tiers ou Article doit être complète, `references/csv-xml-bundle.md` si bundle |
| Phase 4 — Auditer | `scripts/form_coverage.py` sur chaque fiche créée ou étoffée (dimension 14), `references/methode-audit.md`, `references/methode-coherence.md`, `references/methode-dates.md` §6 pour l'audit temporel, `references/methode-rejouabilite.md` si le jeu doit être rejoué sur base vierge, `references/methode-rejeu-controle.md` s'il doit être rejoué par l'API sur une instance sans accès base |

---

# Le workflow en 4 phases

## Phase 1 — Récupérer le contrat de scénario

Le cadrage et la production sont dans le même skill : le demandeur n'a rien à choisir. Faire
un cadrage complet (`references/cadrage-scenario.md`) ou écrire directement le contrat est une
décision technique de cette phase, pas une question à lui poser.

Le contenu métier d'une démo — identité, histoire, objets métier, volumétrie par écran, statuts,
fenêtre de dates, noms — est cadré dans un **contrat de scénario** en langage métier : produit par la méthode de
`references/cadrage-scenario.md`, ou écrit directement au même format quand la demande suffit.

- **Pas de contrat ?** Le cadrage tient en **une seule salve**, au départ — elle porte aussi la
  question de sûreté ci-dessous —, puis plus aucun arrêt jusqu'au rapport. Si la demande donne
  l'identité, les objets et le métier, écrire soi-même le contrat AU FORMAT de `references/cadrage-scenario.md` (identité,
  objets et types de fiches à représenter avec leurs décisions `reutiliser` / `creer`, volumétrie par
  écran, période, états) dans le dossier de travail, et continuer. S'il manque une information que seul
  le demandeur détient, poser **toutes** les questions d'un coup, en fin de tour.
  Le cadrage complet de `references/cadrage-scenario.md` sert quand la demande ne dit ni l'identité ni les objets. Improviser
  l'histoire en écrivant les données reste la première cause de réécriture complète : le contrat
  s'écrit AVANT la première ligne. *Mesuré le 2026-09-27 (essai 0, Industrie 9.1.7) : l'agent a
  écrit son contrat et produit 25 sociétés, 45 contacts et 66 articles cohérents en une passe, sans
  cadrage complet.*
- **Un contrat ?** Le lire et passer directement en Phase 2. Chaque objet métier y est traduit en
  surface technique par l'introspection, et chaque décision `reutiliser` est confirmée contre ce que
  la base contient réellement : le contrat porte une **intention**, pas un constat.
- **Cas particulier — combler des panneaux vides sur une base qui a déjà une identité.** Le scénario
  est implicite : le reconstituer en trois lignes (identité constatée, écrans à combler, volumétrie
  minimale visée), l'écrire en tête du rapport, continuer. Pas de cadrage complet pour un patch de
  complétude, et pas d'arrêt pour le faire valider sur une base jetable ou dédiée.

Une question reste propre à l'exécutant — garde de sûreté, pas cadrage métier, et elle part dans la
salve de départ : **sur quelle base, est-elle vivante, et peut-on redémarrer l'application ?** Nom de
la base, qui l'utilise, y a-t-il un dump filet. Un flux joué par le moteur **mouvemente le stock existant** :
irréversible sans dump. Seul le DEMANDEUR y répond : une base qu'il déclare jetable, ou un dump filet qu'il
confirme — pas un dump que l'exécutant prendrait lui-même (le restaurer effacerait le travail des autres).
Le redémarrage (cache, règle 12) se demande ici, pas en cours de route.

*→ voir `references/mode-b-volume.md` §1 en Mode B.*

## Phase 2 — Dériver la surface technique et la mettre en matrice

C'est ici que le langage métier devient des tables : l'utilisateur n'a validé qu'une histoire, la
chaîne des pièces se déroule sans lui. Dérivation, dans cet ordre :

- **Objet métier → tables porteuses.** « Bilan d'affaire » ne se peuple pas : il se calcule depuis
  des ventes (devis, commandes, lignes de commande, produits, catégories) et des coûts (feuilles de
  temps, lignes de feuille, employés, taux). Cinq objets métier deviennent une dizaine de tables.
- **Fermeture FK.** `scripts/fk-closure.py <base> <table>…` donne la fermeture transitive : elle
  révèle les tables **sans menu**, invisibles à tout audit de couverture (`project_resource` requis
  par une réservation, `quality_characteristic_type` requis par un relevé).
- **Satellites.** L'introspection (sections 5 et 6 : enfants O2M, jonctions M2M) dit ce qu'un header
  exige pour ne pas afficher des panneaux vides.
- **Couche UI-critical.** Ni le schéma ni un enregistrement modèle ne la donnent : elle est dans les
  fiches `entites-*.md` et dans `references/socle-b-shape.md` — booléens filtrants, FK dont l'absence
  vide un écran, tables à laisser au moteur.
- **Mesurer un enregistrement modèle de chaque type de fiche** avec `scripts/form_coverage.py`
  (règle 8) : la liste des éléments affichés et de leurs tableaux de bord EST la matrice de la fiche,
  avant la première écriture — `references/surface-tiers-articles.md` pour les Tiers et les Articles.
- **Lire le `<domain>` ET les colonnes de la vue servie par chaque menu cible**, avant d'arrêter la
  matrice. Ce sont les **colonnes affichées** qui disent quoi peupler, pas le modèle. *Coût évité le
  2026-09-03 : `construction-project-grid` affiche le cumul facturé et aucune heure — les affaires
  figurantes avaient donc besoin de situations de travaux, pas de pointages ; décider sur le modèle
  aurait produit des milliers de lignes de temps sans valeur d'écran.*

Puis la **matrice**, contrat d'exécution : pour chaque élément, `table` → `count actuel` → `verdict`
→ `décision (REUSE / EXTEND / CREATE)` → `échantillon de valeurs proposées`. Chaque ligne se rattache
à un objet du contrat, et chaque `reutiliser` du contrat se confirme ici par le count réel. Deux
principes d'ordonnancement :

- **Peupler par couche de dépendance, pas par module.** Le module est l'axe de *couverture* (la
  checklist « aucun écran vide »), pas l'ordre d'exécution : socle transverse (unités, devises,
  exercices, plan comptable, taxes, séquences) → master data (tiers, produits, employés, emplacements)
  → référentiels secondaires par module → transactionnel → liaisons inter-modules.
- **Marquer ce qu'on ne peuplera pas**, avec la raison : « généré par le flux X non joué », « hors
  périmètre du contrat », « tampon d'import », « document à téléverser via l'UI » (une FK NOT NULL
  vers `MetaFile` signifie que l'enregistrement **est** un fichier). Sans cette porte de sortie
  écrite, la liste des « tables vides » ne converge jamais.

*→ `references/socle-aos-baseline.md`, `references/socle-b-shape.md`,
`references/methode-introspection.md`.*

## Phase 3 — Construire : SQL ou bundle CSV+XML

Deux voies, à choisir selon le contexte. Le choix appartient à ce skill, pas au demandeur.

| | **SQL direct** | **Bundle CSV + XML** |
|---|---|---|
| Quand | On a accès à la base ; itération rapide | Le partenaire/client n'a **pas** d'accès DB ; déploiement via l'UI ; livrable rejouable |
| Portée | Tout, y compris les correctifs ciblés | Création d'enregistrements métier |
| Rejouabilité | Idempotence à écrire à la main | Gérée par l'importeur |
| Détail | `references/methode-ecriture-sql.md` (§ *SQL Script Architecture*) | `references/csv-xml-bundle.md` |

Dans les deux cas, les 12 règles cardinales s'appliquent : la différence est le véhicule, pas
l'exigence de qualité.

**Ordonnancement des passes, quand l'application tourne** (mécanisme complet : règle 12, 3e cas,
pièges 52 et 96) : les passes SQL — insertion **puis** correction — précèdent toujours la passe
moteur. Le redémarrage est le correctif canonique une fois la passe moteur jouée, mais il est
souvent interdit sur un environnement partagé : prévoir dès l'écriture un script de repassage par
le moteur plutôt que de compter dessus. *Coût payé le 2026-09-03 : script de recharge écrit après
coup sur 10 affaires.*

*→ `references/methode-ecriture-sql.md`, `references/methode-dates.md` pour poser les dates, la fiche
`entites-*.md` du domaine visé ; `references/csv-xml-bundle.md` pour un bundle.*

## Un domaine s'appuie sur un champ métier

Quatre contrôles qui tiennent en une minute chacun, et qu'aucun `count(*)` ne remplace.

**1. Jamais de filtre sur du texte libre ni sur un identifiant en dur.** Le champ métier existe
presque toujours ; le chercher coûte une minute. *Vérifié le 2026-09-14 : un menu « Commandes avec
acompte attendu » filtré sur `Invoice.note LIKE '%compte%' AND note NOT LIKE '%olde%'` — une
exclusion pour attraper le mot « solde » — alors que le champ `advancePaymentNeeded` porte exactement
l'information. Mesure du même jour : 2 commandes à acompte absentes de la liste, 1 commande sans
acompte listée. Et un menu « Articles sur mesure » filtré `self.code = 'REG-DIVERS'`.*

**2. Toute vue livrée est atteignable par un menu.** Une vue que l'utilisateur ne peut pas ouvrir
n'existe pas pour lui. *Vérifié le 2026-09-14 : deux pages d'accueil construites et rattachées à
aucun menu.*

**3. Avant de déclarer qu'un domaine est faux, regarder qui porte le champ.** Un nom de champ ne dit
pas sa sémantique dans une base donnée. *Vérifié le 2026-09-14 : `isCorporatePartner`, lu comme
« est une personne morale », porte en fait les distributeurs — 24 de ses 25 porteurs en sont un. Le
domaine accusé était juste ; c'est la donnée qui était fausse.*
**4. Un domaine se valide sur DEUX critères, pas un : il ne lève pas, ET il rend des lignes.** Un
domaine syntaxiquement juste, qui répond `total=0` sans la moindre erreur, est mort-né si la colonne
qu'il compare est vide — et il est alors indistinguable d'un domaine correct sur une base sans cas.
*Vérifié le 2026-09-22 : le domaine « commandes dont un ordre de fabrication finit après la date de
livraison promise » répondait `total=0` en toute rigueur, parce que `estimatedDeliveryDate` était NULL
sur les 120 commandes. Le domaine était juste ; l'écran était vide.* Deux conséquences : tester tout
domaine neuf par `POST /ws/rest/<modèle>/search` avec `{"data":{"_domain":"..."}}` **avant** de le
livrer (quelques secondes, contre un écran mort découvert devant le client — pièges 141 et 142), et
compter la population de la colonne comparée avant de conclure qu'il n'y a « pas de cas ».

## Phase 4 — Auditer avant de déclarer terminé

Un audit qui ne teste que les NULL laisse passer l'essentiel. `scripts/audit-completeness.sql` porte
**treize dimensions numérotées** ; trois ne s'automatisent pas et sont rappelées en fin de sortie comme
checklist manuelle. La quatorzième, la couverture d'écran, est un script à part (`scripts/form_coverage.py`).

| Dim. | Ce qu'elle attrape |
|---|---|
| 1 | booléens NULL — exclus des grids et des pickers |
| 1bis | sélections NULL — invisibles en UI (nuance des champs conditionnels : piège 69) |
| 2 | zéros et chaînes vides que `count()` compte comme « rempli » — *20 contrats de travail « remplis » étaient intégralement à zéro* |
| 3 | *(manuel)* cohérence inter-champs : paires corrélées (règle 10), plus un attribut porté à la fois par l'enregistrement et son parent (`address.country` vs `address.city.country`) |
| 4 | unicité — une colonne à une seule valeur distincte sur N lignes est un copier-coller visible. **Et le symétrique : une valeur portée par un seul enregistrement sur N pairs est un intrus, pas une exception.** Un enregistrement peut avoir tous ses champs remplis et rester faux parce que sa *classification* contredit ce qu'il est — sa nature, les drapeaux du rôle pour lequel il existe, sa famille, sa séquence, sa convention de libellé. Cela ne se voit pas en lisant sa fiche : seule la comparaison à la distribution de ses pairs le révèle. *Vérifié le 2026-09-14 : un transitaire créé pour garnir un panneau transporteur portait `isCarrier = false` — il ne faisait pas le travail pour lequel il existait —, `partnerTypeSelect = 2` quand ses cinq pairs transporteurs sont tous à 1, et `isCorporatePartner = true` qui le faisait apparaître dans la liste des distributeurs.* **Troisième forme, mesurée le 2026-09-22 : l'uniformité PAR FAMILLE, que le contrôle global ne voit pas** — 114 articles de tôlerie tous à 18,00 €, 80 de débit tous à 12,00 €, soit deux valeurs distinctes au global et une seule par famille. La dimension 4 du script ne balaie de surcroît que les colonnes **texte** : un prix lui échappe deux fois (piège 140). |
| 4bis | textes répétés sur les fiches Tiers et Articles taguées : la même phrase sur plusieurs lignes (commentaire ou note recopié, description du modèle sur ses variantes) — à qualifier, une mention réglementaire commune peut être légitime (règle 2) |
| 5 | relations — FK obligatoires laissées à NULL, à justifier ou combler |
| 5bis | satellites — headers sans aucun enfant : panneau vide garanti |
| 6 | *(manuel, irremplaçable)* visibilité écran : ouvrir les écrans — pour les fiches elles-mêmes, la dimension 14 le mesure. Les dashlets filtrent (statut, `project` au niveau **ligne**, utilisateur courant, dates récentes, flags `App*`) — une table pleine peut donner un écran vide. Si l'application tourne, le cache Hibernate L2 masque les `UPDATE` SQL : redémarrer avant de conclure — l'accord se demande dans la salve de départ (Phase 1). **Ouvrir ne suffit pas : lire les dix premières lignes.** Un domaine qui rend des lignes n'est pas un domaine juste — la question est de savoir si ce sont *celles-là*. *Vérifié le 2026-09-14 : une liste de distributeurs rendait un transitaire ; une liste de nomenclatures ouvrait sur des nomenclatures génériques de démonstration.* |
| 7 | champs dérivés désynchronisés — `full_name` qui ne suit plus son nom, dénormalisations recopiées, compteurs de séquence en retard sur le max occupé |
| 8 | booléens filtrants et valeurs utiles — un domaine en `= false` exclut les NULL (règle 3) |
| 9 | configurations invalides — un état que l'écran natif refuserait et qui fait planter le moteur (suivi de stock → NPE en réception d'achat) |
| 10 | *(manuel)* le contrat, pas le script — relire le contrat de scénario ligne à ligne (règle 9) |
| 11 | cohérence temporelle — F1 précédence devis→commande→facture, F6/F6bis/F6ter contenance projet/feuille/tâche, F3 pointages le week-end, F5 statut ↔ date (commande, facture, opportunité, tâche), F7 pièce comptable hors période ; F4 (rafale de `created_on`) reste borné aux lignes taguées, F2 (fenêtre du contrat) ne s'active que si `-v debut=/-v fin=` sont fournis à l'appel |
| 12 | `version` NULL sur une ligne seedée, sur TOUTES les tables (pas seulement le tag) : lecture OK, NPE au premier enregistrement du moteur (piège 124) |
| 13 | invariants métier **à cliquet**, sur TOUTE la base : le 1er passage enregistre les compteurs comme référence (`zz_audit_invariants`), **défauts compris** ; ensuite, un compteur qui monte émet **une** ligne `ERROR` (comptée par le `grep` de fin), l'audit continue et psql sort à 0 — pas d'échec dur (vérifié le 2026-09-24). Donc **lancer l'audit une fois AVANT la première écriture** sur une base, et traiter **toute référence non nulle sur G4-G7 et G9** comme un signal à qualifier (nuls sur les pièces natives de la démo). G1-G3 marges et OF ↔ affaire (G2b quand le prix de revient est un champ par société : piège 197) ; G4-G6 flux physiques sans mouvement (achat reçu, vente livrée, OF planifié, démarré ou terminé) ; G7 pointage d'OF portant l'affaire ; G8 tâche sans priorité ; G9 affaire sans statuts de tâche (pièges 143 à 147) |
| 14 | *(script à part, hors de l'obligation d'audit SQL ci-dessous)* couverture d'écran fiche par fiche : `scripts/form_coverage.py` — voir le paragraphe « Dimension 14 » ci-dessous |

Attention : **Un contrôle qui saute doit le dire — corrigé le 2026-09-07.** Un contrôle portant sur une
colonne absente de la base échouait, et `ON_ERROR_STOP on` emportait **toutes les dimensions
suivantes** : l'audit s'arrêtait en annonçant qu'il avait tout couvert. Ce qui déclenche ce cas
n'est **pas** la version d'AOS mais le **module installé** — `project_project_planning_time.title`
manque sur 2 des 16 bases du parc et est bien présent en 9.1.6 (vérifié le 2026-09-07 sur les 16).
Depuis, le script laisse passer les contrôles suivants et rend compte de ce qu'il a sauté :

- il se termine par une **ligne `FIN DE L'AUDIT`** — absente, psql s'est arrêté avant la fin et
  l'audit ne couvre pas ce qu'il annonce ;
- chaque contrôle inapplicable se signale sur sa propre ligne. Les compter, **0 attendu** :
  `… -f audit-completeness.sql 2>&1 | tee audit.txt ; grep -c '^psql:.*ERROR:' audit.txt`.
  Chaque ligne comptée est une dimension **partiellement** évaluée : reprendre ce contrôle à la
  main sur cette base.

Mesuré sur 4 bases : `<base_1>` 0 sauté, `<base_a>` 0, `<base_b>` 2,
`<base_4>` 5 — les 4 atteignent la dimension 11. Corollaire d'écriture : **jamais
d'`UNION ALL` entre deux tables dans un même contrôle**, une colonne absente ferait tomber tous
ses membres d'un coup.

Attention : **Les seuils écrits à la main dans un `RAISE NOTICE` fabriquent une fausse confiance.** Mettre les
attendus dans le `IF … RAISE EXCEPTION`, pas dans le message : un message annonçant « 19 » quand il y
en a 18 ne déclenche rien.

Attention : **Qualifier un écart avant de l'annoncer comme un défaut.** Un test « CP adresse ≠ CP ville » a
levé 42 écarts dont **41 légitimes** (villes multi-CP comme Paris, CP par quartier à l'étranger) : un
contrôle doit connaître le format local, et borner ses assertions à son périmètre (piège 81).

**Dimension 14 — couverture d'écran, fiche par fiche (script à part, hors de l'obligation d'audit SQL).** L'audit SQL dit ce
que contiennent les tables, pas ce que voit la personne qui ouvre la fiche : passer
`scripts/form_coverage.py --quiet --json` sur CHAQUE fiche créée ou étoffée des objets demandés (mode
d'emploi : `references/surface-tiers-articles.md` §0). Un élément affiché ne reste vide que s'il est sans
objet pour ce type de fiche (§6), produit par un flux que le CONTRAT exclut, ou un commentaire ou une note
sans information propre à la fiche (règle 2) — chaque vide se justifie dans le rapport. Un taux obtenu par des
gabarits ne vaut rien : la couverture se lit avec le réalisme. Les « masqués mais remplis » se signalent ;
ne vider que ses propres créations. L'outil lit par l'application : après un `UPDATE` SQL, redémarrer avant de mesurer (règle 12) ; si le
redémarrage est refusé, faire passer le SQL avant toute lecture ou tout passage moteur sur ces fiches. Toute correction
SQL qui en découle relance l'audit. *Mesuré le 2026-09-27 (essai 0, sans cet outil) : 85,5 % des
éléments attendus remplis, aucune fiche à 100 %.*

**Cet audit est OBLIGATOIRE, il n'est pas optionnel.** Règle de conduite : ne jamais conclure un
peuplement — ni annoncer « c'est fait » — tant que du SQL de peuplement a été joué sans que
`scripts/audit-completeness.sql` ait tourné **après** la dernière écriture ; un audit lancé avant la
dernière écriture ne couvre pas ce qui a été écrit depuis. Raison d'être : le piège 75 a été reproduit
dans la session même où il était documenté — le texte en contexte ne suffit pas, seule une règle
appliquée mécaniquement change l'issue. Une exécution de l'audit après la dernière écriture satisfait
l'obligation, même si elle sort en échec : lire sa sortie et corriger, puis relancer l'audit après toute
correction SQL, plutôt que de le relancer pour obtenir un vert.

*→ `references/methode-audit.md`, `references/methode-coherence.md`, `references/methode-dates.md`
§6, `references/methode-rejouabilite.md`, `references/methode-rejeu-controle.md` si rejeu par l'API.*
