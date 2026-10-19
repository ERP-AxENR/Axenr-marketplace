# Cadrer le scénario d'une démo Axelor

Phase 1 du skill `demo-data-generator`, quand la demande ne dit ni l'identité ni les objets : faire parler l'utilisateur et écrire une histoire, avant toute production technique. Ce cadrage ne produit aucun script ni aucun fichier d'import : il produit le contrat de scénario que les Phases 2 à 4 consomment.

```
[besoin exprimé] --> Phase 1 : cadrage (ICI) --> contrat de scénario, en langage métier
                       --> Phases 2 à 4 : inspection de la base, production, audit
```

Deux rôles, une frontière nette : **ici on décide ce qui doit exister et pourquoi ; en aval on
décide comment l'écrire.** L'utilisateur qui demande « deux affaires pour présenter deux bilans
d'affaire complets » n'a pas à penser à la chaîne des pièces qui les composent : il valide une
histoire, l'exécutant en dérive la surface au moment de produire, en regardant la base réelle.

## Principe fondateur

Un jeu de données est réaliste quand **chaque écran que la démo ouvre a l'air habité, chaque
chiffre est cohérent avec les autres, et rien n'a été recréé de ce que la base avait déjà.**
Le scénario est le contrat qui garantit cela avant qu'une seule donnée soit écrite.

## Ce qui n'est pas de ce ressort

Aucune mention de structure de stockage, de dépendance technique, ni d'ordre d'insertion dans ce
que vous écrivez. Pas de script de peuplement, pas de fichier d'import. Si vous vous surprenez à
nommer un objet technique plutôt qu'un objet métier, c'est le signe que vous avez franchi la
frontière : revenez au vocabulaire de l'utilisateur (« affaire », « devis », « commande client »,
« feuille de temps », « employé », « produit », « opportunité », « facture »).

Raison d'être de cette règle : la connaissance technique vit et se périme en aval, où elle est
vérifiée contre la base à chaque exécution. La dupliquer ici garantit qu'elle divergera.

## Les quatre critères de réalisme

Tout le dialogue sert à instruire ces quatre axes. Un scénario qui en manque un produit un jeu
qui « fait faux » même s'il est complet.

1. **Assez de données dans chaque vue que la démo ouvre** — liste, kanban, calendrier, planning,
   indicateur, fiche détail. Le volume ne se décide pas globalement : il se décide **par écran**,
   avec les seuils ci-dessous.
2. **Des dates cohérentes partout où des pièces se référencent**, et des délais crédibles entre
   elles. Un devis accepté le jour de son émission, une facture antérieure à la livraison ou des
   pointages postérieurs à la réception de chantier se voient au premier clic.
3. **Des noms réalistes.** La recherche web d'inspiration est prévue et souvent nécessaire :
   raisons sociales, patronymes, gammes de produits, ouvrages et vocabulaire du secteur. Critère
   unique : **inspiré, pas copié** — on ne rhabille pas une entreprise réelle identifiable en
   tiers fictif ; on s'inspire des formes, des suffixes, des spécialités, du vocabulaire métier.
4. **Des chiffres qui se recomposent.** Un total est la somme de ses parties, une marge est le vendu
   moins le déboursé, un avancement est cohérent avec les heures consommées. Sur un bilan d'affaire
   ou un tableau de bord c'est **le** critère : un montant qui ne se recompose pas se remarque plus
   vite qu'un écran vide. Il s'écrit dans le contrat, rubrique `coherence-chiffree`.

## Le socle AOS natif existe

Une installation AOS livre déjà un jeu de données : référentiels complets, quelques tiers,
quelques produits, quelques employés. Il est ancien, inégal selon les modules, souvent pauvre en
largeur — mais il est là, et il est cohérent avec l'application.

Conséquence pour le scénario : dire explicitement, par objet métier, **ce qui s'appuie sur ce
socle et ce qui le complète**. Ni le mépriser (recréer un référentiel de pays est du travail perdu
qui collisionne), ni le supposer suffisant (deux exemples pauvres ne remplissent pas une liste).
Quand vous ne savez pas ce que la base contient, écrivez l'intention sous forme conditionnelle
(« réutiliser les ouvrages électricité déjà présents, en créer une dizaine s'il n'y en a pas ») :
l'exécutant la confirme dans son propre état des lieux.

## Prérequis

Aucun outil local n'est obligatoire : le cadrage dialogue avec l'utilisateur et écrit un document.

| Dépendance (optionnelle) | Rôle | Sans elle |
|---|---|---|
| `WebSearch` / `WebFetch` (outils de Claude Code) | recherche d'inspiration pour les noms, les gammes, le vocabulaire du secteur | demander à l'utilisateur le secteur, la région, la gamme ; inventer des formes sans copier ; jamais de noms génériques |
| Lecture de la base ou de l'instance cible | branche « l'identité existe déjà » (étape 2) : lire raison sociale, devise, clients | demander la raison sociale et les référentiels à l'utilisateur plutôt que de les inventer |
| Phases 2 à 4 de `demo-data-generator` | consomment le contrat et produisent les données | remettre le fichier de contrat à la personne ou à l'outil qui produira les données |

## La méthode, dans cet ordre

### 1. Cadrer la demande

Quatre questions, courtes :

- **À quoi sert ce jeu ?** Démo prospect, démo client, formation, capture marketing, données
  d'illustration, jeu d'essai de recette. L'usage change l'exigence : une formation veut des cas
  d'école variés, une capture marketing veut de beaux libellés sur un seul écran, une recette veut
  des cas limites.
- **Qui regarde, et quels écrans ?** C'est le pilote de tout le dimensionnement. Peupler ce que
  personne n'ouvrira n'a aucune valeur ; un panneau vide sur l'écran du fil rouge coûte cher.
- **Quels enchaînements doivent être démontrables ?** Devis vers commande vers livraison vers
  facture ? Affaire avec déboursé et marge ? Recrutement ? Chaque enchaînement impose ses pièces.
- **Compléter ou produire du volume ?** « La démo est trouée, comble les manques » et « crée
  cinquante ordres de fabrication » sont deux besoins opposés. Dans le premier cas vous proposez
  le contenu et la volumétrie ; dans le second l'utilisateur les impose et votre travail est de
  les rendre crédibles. Une demande peut mélanger les deux : le contrat le dit alors par objet.

### 2. Fixer l'identité et l'univers

Secteur, raison sociale, pays, devise, taille, implantation. Tout le reste en découle : une ESN,
un constructeur, un négociant et une collectivité n'ont ni les mêmes clients, ni les mêmes
produits, ni le même vocabulaire.

C'est ici que la recherche web sert le plus : chercher des acteurs réels du secteur et du pays
visé pour en tirer des formes de raisons sociales, des spécialités crédibles, des gammes, des
intitulés de poste, des libellés d'ouvrages ou de prestations. On retient le registre, on invente
le nom.

**Branche « l'identité existe déjà ».** Cas fréquent, et il ne s'invente pas : la société, ses
clients et son catalogue sont déjà en base, la consigne est de les réutiliser. On **lit alors
l'identité métier** — raison sociale, secteur, devise, clients, référentiels — et on la reporte dans
le contrat avec `decision: reutiliser` sur l'identité. Lire des libellés métier n'est pas franchir la
frontière technique : ce qui reste hors de ce ressort, c'est de nommer des tables et de décider
comment écrire. Sans accès à la base, demander la raison sociale plutôt que l'inventer. *Coût payé
le 2026-09-03 : faute de cette branche, l'exécutant a interrogé la base pour connaître la raison
sociale, en franchissant la frontière que ce cadrage trace lui-même.*

### 3. Écrire l'histoire

Une démo se raconte. Distinguez :

- **les objets héros** — une ou deux affaires complètes, une commande instrumentée de bout en
  bout : ce qu'on va ouvrir, dérouler, commenter. Ils portent le détail et la profondeur ;
- **les figurants** — ce qui remplit les listes autour, avec assez de variété pour que le tri,
  le filtre et les statuts aient du sens.

Pour chaque objet métier du scénario : sa quantité, sa **répartition de statuts** (un jeu
mono-statut a l'air scripté : mélanger brouillon, en cours, validé, terminé, et si l'histoire le
justifie un cas annulé ou en litige), et deux ou trois phrases de description macro qui donnent à
l'exécutant de quoi écrire des libellés justes.

Écrivez aussi ce qui est **hors périmètre** et pourquoi. Sans cette porte de sortie, la liste des
manques ne converge jamais.

### 4. Poser l'horloge de la démo

Choisissez une **date pivot** — en général le jour de la démo — puis une fenêtre : combien de
passé (pour que l'historique, les indicateurs et les courbes existent) et combien de futur (pour
que les plannings, les échéances et les prévisions ne soient pas vides).

Puis posez les jalons de l'histoire avec des délais réalistes entre les pièces. Exemple de chaîne
pour une affaire de travaux, à adapter :

| Jalon | Position | Pourquoi ce délai |
|---|---|---|
| Opportunité ouverte | pivot moins 4 mois | une affaire ne naît pas la veille |
| Devis émis | pivot moins 3 mois | quelques semaines d'étude |
| Devis accepté, commande | pivot moins 10 semaines | jamais le même jour que l'émission |
| Démarrage, premiers pointages | pivot moins 8 semaines | délai de mobilisation |
| Facture d'acompte | pivot moins 7 semaines | après la commande, avant les travaux |
| Situations mensuelles | pivot moins 6, moins 2 semaines | rythme régulier, la dernière récente |
| Reste à produire, échéances | pivot plus 2 à 8 semaines | il faut du futur à montrer |

Deux points à vérifier explicitement : aucune pièce ne précède celle dont elle découle, et les
dates ne s'agglutinent pas sur une même journée (un décalage dérivé de l'objet, pas constant).

### 5. Dimensionner par écran

Ces seuils sont des **valeurs par défaut argumentées, pas des mesures** : à ajuster à l'écran
réel, qui affiche plus ou moins de lignes selon la vue et la résolution de projection.

| Type de vue | Minimum par défaut | Pourquoi ce seuil |
|---|---|---|
| Liste / grille | 8 à 15 enregistrements, plusieurs statuts | en dessous, on voit le fond de la liste ; le tri et le filtre n'ont rien à démontrer |
| Kanban | **chaque** colonne peuplée, 2 à 5 cartes par colonne | un kanban à quatre colonnes vides sur cinq est pire qu'un kanban absent : il montre un processus inutilisé |
| Calendrier | semaine courante garnie, 4 semaines de passé, 6 de futur, 3 à 8 événements par semaine | on recule et on avance toujours d'un cran en séance ; un mois vide ne se rattrape pas |
| Planning / Gantt | 10 à 20 barres, au moins deux chaînes liées, des chevauchements | une barre isolée ne montre ni l'enchaînement ni le conflit de charge |
| Indicateur, tableau de bord | 12 points sur l'axe temps (12 mois ou 12 semaines), aucune tuile à zéro | un indicateur vend une tendance ; trois points font un accident. Une tuile à zéro se lit comme une panne |
| Fiche détail d'un objet héros | chaque panneau et onglet que la démo ouvre a au moins 2 lignes | on ouvre **une** fiche et on clique tous les onglets |
| Filtre ou recherche démontrés | au moins 3 valeurs distinctes sur le critère filtré | un filtre qui ne réduit rien ne prouve rien |
| Répartition | aucun parent à zéro enfant sur un axe démontré, et 1 ou 2 objets à 5-10 fois la médiane | des enfants tous en nombre égal, c'est un copier-coller visible au premier clic |

La largeur avant le volume : vingt fiches renseignées valent mieux que deux cents fiches à moitié
vides, sauf si l'utilisateur a explicitement commandé du volume.

### 6. Rédiger le contrat

Un document court : l'histoire en prose (ce que l'utilisateur relit et valide), puis le contrat
en fin de fichier (ce que l'exécutant consomme). Modèle en bas de page.

### 7. Faire valider

Reformulez l'histoire en trois ou quatre phrases et faites-la confirmer avant de passer la main.
Un cadrage raté se paie en réécriture complète. Faites valider en particulier : l'identité, la
date pivot, les objets héros, et la liste des écrans cibles.

**Si l'utilisateur n'est pas là** — tour asynchrone, exécution en lot, sous-agent — la validation ne
se suppose pas : elle se **journalise**. Tenir dans le contrat un tableau des *validations simulées*,
une ligne par décision prise en son nom, qui sépare ce qui **découle** du contexte (un délai
standard, un statut imposé par l'histoire) de ce qui l'**extrapole** (un objet, un contraste, une
volumétrie ajoutés à sa demande). Signaler les extrapolations en tête de livrable, pour qu'il puisse
les refuser d'un mot. Le contrat part marqué non validé : journaliser n'est pas valider. *Coût payé
le 2026-09-03 : le tableau a dû être inventé en séance, faute de consigne.*

### 8. Passer à la Phase 2

Sur accord, enchaîner sur la Phase 2 du SKILL.md avec le fichier de contrat comme
spécification : c'est là qu'on regarde la base, arrête la surface technique, produit et audite.

## Le contrat de scénario

À écrire en fin de document, en YAML. Cent pour cent métier : des objets et des intentions, aucun
élément de structure de stockage.

```yaml
scenario:
  identite:
    decision: "creer"                 # creer | reutiliser (déjà en base : la lire, ne pas l'inventer)
    societe: "Solerio Électricité"
    secteur: "installation électrique tertiaire et IRVE"
    pays: "France"
    devise: "EUR"
    taille: "PME, 45 salariés, 3 agences"
    usage: "demo prospect"            # demo | formation | marketing | test
    mode: "volume"                    # completer | volume | mixte
  horloge:
    date-pivot: "2026-09-15"
    fenetre-passe: "6 mois"
    fenetre-futur: "3 mois"
    jalons:
      - "opportunité pivot-4mois, devis pivot-3mois, commande pivot-10sem"
      - "pointages hebdomadaires de pivot-8sem à pivot-1sem"
      - "situations mensuelles, la dernière à pivot-2sem"
  surface:
    - ecran: "liste des affaires"
      seuil: "12 affaires, statuts mélangés"
    - ecran: "bilan d'affaire (fiche héros)"
      seuil: "chaque panneau garni : vendu, déboursé, marge, avancement"
    - ecran: "kanban des opportunités"
      seuil: "les 5 étapes peuplées, 2 à 4 cartes chacune"
    - ecran: "planning des interventions"
      seuil: "15 barres sur 8 semaines, chevauchements"
  objets-metier:
    - objet: "client"
      decision: "enrichir"            # reutiliser | creer | enrichir
      quantite: 8
      statuts: "actifs, dont 2 prospects non encore clients"
      description: "promoteurs tertiaires et bailleurs sociaux du Grand Est"
      dates: "ancienneté étalée sur 4 ans"
      nommage: "raisons sociales inspirées du secteur immobilier régional, non copiées"
    - objet: "affaire"
      decision: "creer"
      quantite: 12
      statuts: "2 terminées, 6 en cours, 3 à démarrer, 1 annulée"
      description: "2 affaires héros complètes (bilan démontré), 10 figurants pour la liste"
      dates: "voir jalons ; les 2 héros couvrent toute la fenêtre"
      nommage: "libellés de chantier réalistes : résidence, groupe scolaire, plateforme logistique"
    - objet: "feuille de temps"
      decision: "creer"
      quantite: "300 lignes environ"
      statuts: "validées jusqu'à pivot-2sem, en attente ensuite"
      description: "électriciens et chefs d'équipe sur les 2 affaires héros"
      dates: "hebdomadaires, charges réalistes, pas de saisie le week-end"
      nommage: "qualifications du métier : monteur, chef d'équipe, technicien IRVE"
  coherence-chiffree:
    - "marché total = initial + avenants + travaux supplémentaires, sur chaque affaire"
    - "marge brute = vendu − déboursé : ~25 % sur l'affaire tenue, ~15 % sur l'affaire dégradée"
    - "facturé + reste à facturer = marché total"
    - "avancement d'exécution cohérent avec les heures : 3 022 h consommées sur 3 596 h budgétées"
  hors-perimetre:
    - "paie et absences : hors du fil rouge, non démontrés"
    - "achats de sous-traitance : mentionnés à l'oral, non instrumentés"
  valide-par-utilisateur:
    - "identité et secteur"
    - "date pivot du 15/09 et fenêtre 6 mois / 3 mois"
    - "les 2 affaires héros et la liste des 4 écrans cibles"
```

L'exécutant traduit chaque `objet` en surface technique par sa propre inspection de la base, et
confirme les décisions `reutiliser` contre ce qu'il y trouve.

## Erreurs courantes

| Erreur | Correction |
|---|---|
| Nommer des éléments de structure de stockage dans le scénario | Rester en objets métier. L'aval connaît la structure et la vérifie ; ici elle ne peut que se périmer. |
| Produire un script ou un fichier d'import pendant le cadrage | Le cadrage ne produit qu'un document. Le peuplement appartient aux Phases 2 à 4. |
| Volumétrie choisie en chiffre rond global | Chaque quantité se justifie par un écran cible et son seuil (étape 5). |
| Tous les objets au même statut | Mélanger les statuts, y compris un cas atypique si l'histoire le porte. |
| Recréer du référentiel déjà livré par AOS | Déclarer `reutiliser` par défaut sur les catalogues et référentiels. |
| Inventer une identité que la base porte déjà | Lire l'identité métier en base et poser `decision: reutiliser` (étape 2). |
| Dates posées à la main, pièce par pièce | Passer par l'horloge : date pivot, fenêtre, jalons, délais entre pièces. |
| Noms génériques (« Client 1 », « Produit test ») | Chercher l'inspiration sur le web puis inventer : inspiré, pas copié. |
| Contrat en prose seulement | La prose se valide, le contrat s'exécute. Les deux sont requis. |
| Oublier la passation | Terminer en enchaînant sur la Phase 2 avec le fichier de contrat. |
| Scénario écrit sans faire valider | Reformuler en 3-4 phrases et obtenir un accord explicite avant la passation. |
| Deux règles chiffrées du contrat s'imposent l'une l'autre sans dérivation possible (ex. « écart nul devis↔opportunité » ligne à ligne **et** « pipeline global dans telle fourchette ») | La cohérence chiffrée se DÉRIVE des objets un par un, jamais l'inverse : fixer d'abord les montants ligne à ligne (héros compris), puis calculer ce que l'agrégat donne réellement — l'annoncer tel quel plutôt que fixer l'agrégat en même temps que le détail et découvrir en aval qu'aucune vague SQL ne peut satisfaire les deux à la fois. Vécu : un contrat de démo imposait un écart nul devis/opportunité **et** un pipeline ouvert cible à ±5 % ; la vague qui a tenu le premier engagement a mécaniquement cassé le second (montants réalignés à la baisse), et l'écart a été découvert à l'audit, pas au cadrage. |

## Auto-contrôle avant passation

- [ ] Chaque écran de la surface a au moins un objet métier qui le remplit, avec son seuil écrit.
- [ ] Chaque objet porte une décision réutiliser / créer / enrichir, une quantité justifiée et une
      répartition de statuts.
- [ ] L'horloge est posée : date pivot, fenêtre passé et futur, jalons avec des délais crédibles ;
      aucune pièce ne précède celle dont elle découle.
- [ ] Les noms sont issus d'une recherche d'inspiration, et aucun n'est celui d'une entreprise
      réelle identifiable.
- [ ] Ce qui s'appuie sur le socle AOS et ce qui le complète est distingué.
- [ ] Le hors-périmètre est écrit, avec sa raison.
- [ ] La rubrique `coherence-chiffree` est écrite : totaux qui se recomposent, marge = vendu −
      déboursé, avancement cohérent avec les heures consommées.
- [ ] Le contrat ne contient aucun élément de structure de stockage.
- [ ] L'utilisateur a validé — ou, s'il est absent, les validations simulées sont journalisées et
      les extrapolations signalées ; et le passage à la Phase 2 est fait.
