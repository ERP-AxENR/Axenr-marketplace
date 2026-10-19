# Pièges runtime constatés sur AOS 9.1.7 / AOP 8.2.3

Chacun a été constaté sur un WAR en service, sauf mention contraire ; sa cause est lue dans le code quand
l'entrée le dit, et ce qui n'a pas été rejoué est marqué comme tel. Ils échouent tous
**sans message utile** : le moteur rend un code de succès, ou un message qui nomme autre chose que la
cause. Les vérifier avant de seeder coûte quelques minutes ; les découvrir en cours de vague coûte
une vague.

## 1. Un type de code-barres inadapté bloque le moteur, avec un message qui ne le dit pas

Une configuration en **EAN_13** fait échouer **toute création d'ordre de fabrication** — le numéro de
brouillon, préfixé `#`, n'est pas encodable — et interdit tout **numéro de série alphanumérique**.
Le message parle de nombre de caractères autorisés, jamais de configuration.

**Quatre applications portent une configuration de code-barres, pour six champs au total** :

| Application | Champ |
|---|---|
| Configuration de base | code-barres des produits |
| Production | code-barres des ordres de fabrication |
| Stock | mouvements de stock, numéros de suivi, emplacements |
| Comptabilité | immobilisations |

Les vérifier toutes avant de seeder. CODE_128 encode l'ASCII complet, y compris `#` et les tirets.

## 2. L'unicité des numéros de pièces ignore l'archivage

Un document de test **archivé verrouille son numéro pour toujours** : les index uniques sont posés
sans condition sur l'archivage, sur neuf tables de pièces. Archiver un essai ne libère donc pas le
numéro qu'il a consommé — et si ce numéro est celui d'une pièce réelle du client, il faut renommer le
résidu.

## 3. Une ligne fille archivée reste affichée

L'archivage ne retire pas une ligne d'une collection à l'écran ; seule la suppression le fait. Et la
suppression d'une donnée qu'on n'a pas créée est un **arbitrage**, pas une décision d'exécutant : la
remonter.

## 4. `meta_menu.left_menu` doit valoir `true`

À NULL, le champ est lu comme faux côté serveur et le front filtre le menu : **il est invisible dans
la barre alors que l'API le sert correctement**. Un menu seedé en SQL sans ce drapeau ne se voit
jamais, et rien ne signale pourquoi.

## 5. Les valeurs par défaut d'un attribut de configurateur commercial ne sont pas typées

Elles sont écrites en **chaîne JSON brute, sans conversion de type** :

- une chaîne `"false"` est évaluée comme **vraie** — poser la chaîne vide pour obtenir un faux ;
- une valeur par défaut sur un **champ de relation ne se pose pas du tout** : le moteur ne parse
  jamais la chaîne en objet, quel que soit son contenu.

*Portée : vérifié sur le configurateur commercial, pas au-delà.*

## 6. Les dates de réalisation sont écrasées par la date du jour

Mouvements de stock et ordres de fabrication reçoivent la date du jour à la réalisation, **sans
condition**. Les factures, elles, se rétrodatent : leur date n'est posée que si elle est vide, et
seule une date future est refusée.

Le seul levier est la **date simulée**, et **elle a deux porteurs avec une précédence** : la date de
l'utilisateur courant l'emporte, celle de la configuration de base ne sert que de repli — lu dans le
bytecode du WAR en service. Elle se pose **par paquet de date** : poser la date, jouer les transitions
de cette date, passer à la suivante.

Attention : **Sa remise à NULL est une étape de sortie, pas une politesse.** Une date simulée oubliée fausse
tous les écrans et tous les indicateurs, et rien ne le signale.

Elle n'agit qu'en `application.mode = dev` (en `prod`, la date réelle s'applique sans message) : peupler en
`dev`, repasser en `prod` avant le dump. Après un 1er démarrage à la date réelle, un import sous date simulée
antérieure crée une seconde version pour les numérotations non annuelles (tiers, produit, ABC) ; dès la date
réelle, la version du démarrage reprend à 1 → « La séquence générée T0001 existe déjà » : la supprimer à l'écran
après l'import (vérifié 9.1.6 et 9.1.7, 25/09/2026). Vider la date simulée **à l'écran** ne tient pas toujours
(le champ revient à sa valeur) : la vider par `POST /ws/rest/com.axelor.auth.db.User/<id>` et
`…/com.axelor.studio.db.AppBase/1` (`todayDateT: null`, avec `version`), puis relire en base.

## 7. Ordre imposé : réceptions avec leurs lots avant les ordres de fabrication

Un contrôle à la réalisation réclame un numéro de suivi sur chaque composant suivi par lot. Sans les
lots créés à la réception, **aucun ordre de fabrication ne se termine** — et le message nomme les
composants, pas l'ordre des opérations.

## 8. Une unité de ligne de nomenclature différente de celle de l'article fait échouer la planification

Le moteur cherche une conversion et s'arrête sur son absence. Le bon correctif est d'**aligner l'unité
de la ligne sur celle de l'article** quand la quantité est déjà exprimée dans cette unité — inventer
une conversion entre deux unités sans rapport (une pièce vers un mètre) fait passer l'erreur et fausse
les coûts.

## 9. Une ligne seedée sans `version` passe la lecture et plante au premier enregistrement du moteur

Le message ne nomme ni la table ni la colonne : `NullPointerException: Cannot invoke
"java.lang.Integer.intValue()" because "current" is null`, levé au **flush Hibernate** déclenché dans le
`save` d'un enregistrement voisin (pile constatée : `JsonReferenceUpdater.afterSave` ←
`JpaRepository.save` ← `PartnerAccountRepository.save` ← confirmation d'une commande client).
Hibernate incrémente la colonne `version` de chaque ligne modifiée et tombe sur NULL. Les listes, les
fiches et les compteurs sont corrects : **le défaut n'apparaît qu'au premier clic qui écrit**.

Vérifié le 15/09/2026 (AOS 9.1.7) : 16 tables portaient des lignes à `version` NULL (tiers, adresses,
listes de prix, contrôles qualité, métas) ; après `UPDATE … SET version = 0 WHERE version IS NULL`
sur chacune, la même confirmation de commande est passée. La règle « poser `version = 0` » existait
déjà (`methode-ecriture-sql.md`) ; ce qui manquait, c'est le **contrôle** : la dimension 12 de
`scripts/audit-completeness.sql` (piège 124) balaie toutes les tables porteuses de la colonne et échoue
dur s'il en reste.

## 10. Une filiale se crée à l'écran : 17 prérequis, chacun trahi par un message différent

Ni la duplication de la société mère (elle ne copie aucune configuration et garde le tiers et la banque de la
mère), ni un script qui pose ses versions de numérotation à `CURRENT_DATE` (piège de la date réelle). La liste
ordonnée, avec le message qui trahit chaque oubli, est donnée dans le tableau ci-dessous (établie au runtime le
25/09/2026, AOS 9.1.7 / AOP EE 8.2.3, sur une filiale créée à l'écran d'une société de démo).
Les quatre qui coûtent le plus cher : **modèles d'impression** des configurations (« La configuration pour
imprimer ce modèle est manquante » dès « Demandé »), **comptes par famille d'articles** pour la société
(« La configuration comptable est manquante pour le produit »), **« Générer BR pour les articles »** dans la
configuration Supply Chain (« pas de mouvement de stock à générer »), **adresses** de la société, de son
entrepôt et de son tiers (incoterm exigé, « Adresse d'origine est requis »). Numérotations et préfixes propres à
chaque société (décision de chantier).

À faire sous la date simulée du peuplement (les versions de numérotation naissent à la date de la première
pièce) :

| # | Geste (écran) | Si on l'oublie : message ou symptôme observé |
|---|---|---|
| 1 | Société : nom, code, société mère, devise, **paramètres d'impression**, planning hebdomadaire, localisation | « Impressions est requis » à l'enregistrement |
| 2 | Société : **adresse** (pays) | incoterm exigé à la confirmation d'une commande (pays de livraison ≠ pays de l'entrepôt/société) |
| 3 | Tiers de la société : cases client, fournisseur, interne ; **adresse de facturation et de livraison par défaut** ; relié à la fiche société | « Adresse d'origine est requis » à la réception de l'autre société (adresse en lecture seule hors mode modification) |
| 4 | Coordonnées bancaires de la société, puis banque par défaut (liste vide tant que la banque n'est pas enregistrée) ; **sur le tiers de la société, cocher « par défaut » sur ce RIB** (la fiche société ne le fait pas) | la facture fournisseur miroir chez l'autre société naît sans RIB ; payée par virement, « RIB est requis » (bandeau fugace) bloque sa validation |
| 5 | Comptes utilisateurs : ajouter la société à leurs « sociétés » (sélection par la loupe de la grille) | la société n'est pas proposée |
| 6 | Exercices fiscal et civil de chaque année, **date des à-nouveaux** (fiscal), enregistrer, puis durée « Un mois » et « Générer les périodes » | « Date des à-nouveaux est requis » ; durée grisée avant enregistrement |
| 7 | Configuration comptable : modèle « France - Plan Comptable Général », « Importer/Générer les configurations comptables » (≈ 1 min) | comptes, journaux, numérotations comptables absents. 22 taxes rejetées « Code and name must be unique » : communes, déjà présentes, sans effet |
| 8 | **Chaque famille d'articles utilisée** : ligne de comptes de la société (compte d'achat, compte de vente, TVA achat, TVA vente) | « La configuration comptable est manquante pour le produit : … (société : …) » à la saisie d'une ligne |
| 9 | Numérotations des pièces de la société, **préfixes propres à la société** : devis/commande, achat, livraison, réception, mouvement interne, OF, ordre de production — et, si besoin, factures/avoirs/écritures (le plan comptable importe les mêmes préfixes que la mère : deux FC260001 dans le groupe) | pièce refusée faute de numérotation ; homonymie de numéros entre sociétés |
| 10 | Emplacements de la société : entrepôt (interne, **avec adresse**), client, fournisseur, inventaire, production (virtuels), rebuts ; onglet « Configuration » : **utilisable en vente** (client), **en achat** (fournisseur), **en production** (production, rebuts), les trois pour l'entrepôt | emplacements virtuels absents des listes de la configuration stock |
| 11 | Configurations par module (boutons de la fiche société) : Ventes, Achats, Stock (10 emplacements par défaut), Supply Chain (**« Générer BR pour les articles »**), Production si OF | « Il n'y a pas de mouvement de stock à générer pour cette commande fournisseur » |
| 12 | **Modèles d'impression** des configurations : commande d'achat (Achats), devis (Ventes), bon de préparation, inventaire, emplacement, certificat (Stock), facture, relevés ventes/achats, remise de chèques (Compta) | « La configuration pour imprimer ce modèle est manquante » dès le passage d'un achat à « Demandé » |
| 13 | Tiers utilisés par la société : ajouter la société à leurs « Sociétés » (la démo ne les rattache qu'à la mère) | fournisseur ou client introuvable dans la société |
| 14 | **Encours autorisé** : la situation comptable créée pour la société vaut 0 € (config Ventes neuve : 0) — relever pour chaque client **avant** la première finalisation | « … bloqué : encours maximal autorisé dépassé » ; le devis garde ensuite sa marque « Bloqué » |
| 15 | Intragroupe (config de l'app Supply Chain) : « Interco depuis une commande fournisseur » **et** statut de déclenchement « Validé » ; « Interco depuis une facture » | aucun miroir créé (statut à 0 par défaut) |
| 16 | Prix de cession : liste de prix « groupe » sur les achats intragroupe | « Un produit est vendu à perte » à la finalisation du miroir |
| 17 | **Taxe du devis miroir** : la remplacer par la TVA collectée tant qu'il est brouillon (il recopie la TVA d'achat, §11) | « Veuillez sélectionner un compte de vente d'après les débits pour la taxe : N_D » à la facturation ; non corrigible après confirmation |

Non couvert par ce test : ordres de fabrication de la filiale (nomenclatures, gammes, postes, configuration
Production), RH et feuilles de temps de la filiale, sens vente de la mère → achat de la filiale, facture
fournisseur de la filiale à un tiers extérieur.

## 11. Le devis miroir intragroupe recopie la TVA de l'achat

`IntercoServiceImpl.createIntercoSaleLineFromPurchaseLine` copie les taxes de la ligne d'achat (TVA déductible)
sur la ligne de vente : devis, commande et livraison passent, la **facture** est refusée (« Veuillez sélectionner
un compte de vente d'après les débits pour la taxe : N_D »), et la taxe n'est plus modifiable après confirmation.
Parade : corriger la taxe du devis miroir **au brouillon**. Deux autres réglages : le statut de déclenchement
intragroupe vaut 0 par défaut (aucun miroir), et l'encours autorisé d'une société neuve vaut 0 € (devis bloqué,
marque « Bloqué » conservée après relèvement). Le miroir de **facture** traduit bien la taxe. Anomalie confirmée
le 25/09/2026 (code identique de la 8.3.0 à la version en développement, même recopie dans le sens vente → achat) ;
à remonter en anomalie AOS Core (aucun ticket existant relevé le 25/09/2026 après lecture par titre des tickets « interco » et recherches plein texte).

## 12. En 9.1.7, l'import de la démo Supply Chain ne réalise plus les réceptions d'achat

Un contrôle ajouté à la réception (`StockMoveServiceSupplychainImpl.realizeStockMove`) lève une
`LazyInitializationException` dans le contexte d'import ; l'exception est avalée et l'import se dit réussi.
Données de démo identiques à la 9.1.6. Effet : 5 commandes d'achat non reçues, 390 composants hors stock, 0 facture
fournisseur dans la démo (≈ 43 k€ TTC), 5 réceptions planifiées en retard. La réception **à l'écran** fonctionne.
Contrôle après import : `purchase_purchase_order.receipt_state` des commandes « terminées » de la démo, et
`base_trace_back`.

## 13. Facture fournisseur payée par virement : sans RIB du fournisseur, « Valider » semble sans effet

Règle standard (vue facture, 9.1.7) : une facture ou un avoir fournisseur dont le mode de paiement est un virement
exige le RIB du fournisseur. Sans lui, le clic sur « Valider » n'affiche qu'un bandeau rouge fugace « RIB est
requis » en bas à droite, suivi d'une erreur JavaScript « undefined » sans conséquence : on croit à un bogue (il a
fallu une session pour le voir). Une facture générée (miroir intragroupe, facture depuis une commande) ne reprend le
RIB du tiers que s'il est **actif ET « par défaut »**. Or la démo AOS 9.1.7 livre 11 fournisseurs payés par virement
sans aucun RIB, et le RIB saisi sur la fiche d'une société neuve n'est pas coché « par défaut » sur son tiers.
Au peuplement : un RIB actif « par défaut » sur chaque fournisseur utilisé et payé par virement, et sur le tiers de
chaque société du groupe ; contrôle : `account_invoice.bank_details` non vide sur les factures fournisseurs payées
par virement. Vérifié à l'écran le 25/09/2026.

## 14. (piège 174) 9.1.7 : livraison ↔ devis par `StockMove.saleOrderSet` ; la démo ne crée aucune livraison à la confirmation

Le lien d'un mouvement de stock à son devis est le M2M `saleOrderSet` (table `stock_stock_move_sale_order_set`) ;
`originTypeSelect` / `originId` n'existent plus (« No such field 'originTypeSelect' in object
'com.axelor.apps.stock.db.StockMove' », constaté au rejeu du 25/09). La démo a `AppSupplychain.customerStockMoveGenerationAuto`
= faux (relu au rejeu V2) : confirmer un devis dont les
sous-détails portent des produits stockés, avec un dépôt, ne crée **aucune** livraison (aucune sur les 14
confirmations du rejeu hébergé du 26/09, AOP EE 8.2.4 pré-version, build exact non documenté, contrôle intégré au script). À relire sur toute base avant de
compter dessus.

## 15. (piège 175) Numérotation sans remise annuelle : une pièce datée AVANT la première version repart au n° 1

Complète le §6 (versions du premier démarrage sous date simulée) : sur une numérotation sans remise annuelle (devis,
chantiers, contrats…), une pièce datée avant le début de la version existante en crée une nouvelle au n° 1,
**même préfixe** → « … existe déjà » (constaté au premier jet de la démo BTP de référence du 25/09 sur devis, chantiers et contrats :
« SO0001 / PRJ00001 / C0001 existe déjà »). Parade qui a tenu sur tout le rejeu, jusqu'à l'instance hébergée : une
version **bornée par période**, numéros disjoints (2025 à partir de 900), plus **une seule** version ouverte à partir de
la date de la démo ; fusionner les doublons sans jamais supprimer une version qui a émis un numéro
(bilan du premier jet, 25/09).

## 16. (piège 182) Réception d'achat : une unité de ligne différente de celle de l'article exige une conversion exacte, et inversible

Constaté le 26/09 en local (AOS 9.1.7 / AOP EE 8.2.4-SNAPSHOT). Les lignes d'achat héritent de l'unité du chiffrage (m², unité) alors que l'article est stocké dans une
autre (kg, mètres) : générer la réception exige une conversion (« Veuillez configurer les conversions d'unités de
'Mètre carré' à 'Kilogrammes' »), sur 7 commandes des 10 du scénario. Puis trois pièges dans la conversion elle-même :

1. une conversion « Formule » voit l'article (`$Product.code$`), mais AOS la saute quand il convertit un prix **sans**
   article (`StockMoveLineServiceSupplychainImpl.convertUnitPrice`, écrans de ligne de réception) : préférer un
   coefficient, pour un couple d'unités porté par un seul article ; la colonne `formula` est limitée à 255 caractères ;
2. le prix unitaire converti est arrondi à 2 décimales (réglage de l'app) : choisir le coefficient pour que prix /
   coefficient tombe juste, sinon « Reçu » ≠ « Facturé » ;
3. l'**inverse** d'un coefficient revient arrondi à 12 décimales : 600 m² → 87 600 kg → 599,9999999568 m², et la ligne
   reste « partiellement reçue » pour toujours (3 commandes de la démo BTP de référence laissées en l'état, décision de l'utilisateur).

**À faire :** avant la première réception, lister les couples d'unités (ligne ≠ article) et poser pour chacun une
conversion exacte : coefficient de la forme 2^a·5^b (inverse décimal exact : 8 m/m² plutôt que 7), ou conversion
écrite dans l'autre sens en formule calculée à 30 décimales. Complète le §8 : quand la quantité est déjà exprimée dans
l'unité de l'article, aligner l'unité de la ligne plutôt que convertir.

## 17. (piège 183) Feuilles de temps générées : ouvertes au fil des lignes, un jour ouvré vide refusé, et des fériés faux dans la démo

Constaté le 26/09 en local (AOS 9.1.7, lots de pointage du module construction) :

- sans feuille antérieure, AOS ouvre la 1re feuille au jour de la 1re ligne traitée et refuse les jours d'avant ;
  ensuite chaque feuille repart du lendemain de la précédente (`TimesheetCreateServiceImpl.getOrCreateTimesheet`,
  l. 166-199). Parade appliquée sur 31 lots : ouvrir une feuille brouillon au lundi de la 1re semaine ;
- la validation refuse un jour ouvré sans ligne ENTRE deux jours pointés (« Line for 2026-05-14 is missing »,
  `TimesheetLineGenerationServiceImpl.checkEmptyPeriod`, l. 202-243) ; les jours ouvrés sont ceux du calendrier du
  salarié ;
- le calendrier « Jours fériés FR » de la démo AOS pose Pâques, l'Ascension et la Pentecôte à date fixe (21/04, 21/05,
  01/06) : faux en 2026 (06/04, 14/05, 25/05).

**À faire :** corriger le calendrier de fériés pour les années du récit, pointer chaque semaine sans trou de jour ouvré,
ouvrir la première feuille au lundi. **Non éprouvé** : pointer des semaines ANTÉRIEURES aux feuilles existantes d'un
salarié devrait échouer (AOS rouvre au lendemain de la dernière) ; la parade envisagée, pré-créer une feuille brouillon
par salarié et par semaine, n'a jamais été jouée (chantier abandonné). Cause
distincte : un salarié sans société par défaut (piège 166).

## 18. (piège 184) Comptabilité fournisseur de la démo : si l'app Paiement bancaire est inactive, le virement échoue ; l'acompte exige deux comptes absents

Constaté le 26/09 en local (AOS 9.1.7) :

- **constaté quand l'app « Paiement bancaire » était inactive** (`SELECT active FROM studio_app WHERE
  code = 'bank-payment'` — le vérifier AVANT de renoncer) : le mode « Virement » de la démo (DEC_VIR)
  génère un **ordre bancaire** (`generateBankOrder`) et tout règlement fournisseur par virement échoue
  (« RIB par défaut manquant », puis « configurer les informations de paiement bancaire pour la
  société »). Le chèque (DEC_CHQ) passe sans rien configurer. RIB du fournisseur : §13. App ACTIVE : voir d'abord
  le piège 194 (un règlement créé par l'API sans ses échéances tombe en NullPointerException en virement) — tenter un
  virement sur une facture jetable avant de conclure. *Appliqué sans vérification le
  27/09 (essai 0, Industrie 9.1.7, app active) : aucun règlement fournisseur saisi ;*
- la facture d'acompte fournisseur exige la comptabilité du produit d'acompte (PFA-0000) puis un compte de la taxe N_D
  pour les acomptes, absents de la démo ;
- la première facture de chaque fournisseur garde un régime de TVA vide : la situation comptable du fournisseur naît à
  sa ventilation.

**À faire :** régler par chèque quand la comptabilité est hors périmètre (choix de l'utilisateur sur la démo BTP de référence) ; sinon activer
et configurer le paiement bancaire avant la première facture. Ne promettre un acompte fournisseur qu'une fois ces deux
comptes posés.

## 19. (piège 186) Ce que l'écran dérive au changement d'un champ, l'API ne le fait jamais — relevé sur quatre champs

Le piège 131 (ligne de vente sans prix ni taxe) n'est pas propre aux lignes de vente : aucune action d'écran —
`onChange`, règle au changement de statut — ne s'exécute sur un enregistrement créé ou modifié par `/ws/rest`, ni
quand un service change le champ côté serveur. Relevé le 26/09 en local (AOS 9.1.7, modules construction et EE
project-scheduler) :

| Champ posé par l'API ou un service | Ce que l'écran aurait fait | Effet constaté |
|---|---|---|
| ligne de commande d'achat | prix TTC par `action-purchase-order-line-method-onchange-price` | TTC à 0 |
| créneau de planning | `title` = nom de la tâche | barres qui n'affichent que les heures |
| zone d'une demi-journée de lot de pointage | recopie de la zone du chantier, qui déclenche le panier | aucun panier (piège 181) |
| statut « terminé » d'un chantier réceptionné | pose de la fin réelle | retard et pénalité qui courent (piège 177) |

**À faire :** pour chaque champ posé par l'API, lire la vue (`onChange`, `onSave`, règles d'attributs) ; appeler
l'action concernée avec l'enregistrement entier (piège 132), ou poser soi-même le champ dérivé. Contrôler le champ
dérivé, pas le champ posé.

## 20. (piège 187) L'API rend les dates-heures à fuseau en UTC : une clé d'idempotence sur l'heure doit convertir

Constaté le 26/09 en local (AOP EE 8.2.4-SNAPSHOT) sur les créneaux de planning (`ProjectPlanningTime.startDateTime`) : l'API
renvoie « …T06:00:00Z » pour un créneau posé à 08:00 heure de Paris. Un script qui retrouve ses créneaux en comparant
l'heure envoyée à l'heure relue, sans conversion, ne les retrouve pas : à la relance, il les recrée en double
(déduit, non observé ; parade en place dans le kit de rejeu : une fonction de conversion en heure de Paris).
**À faire :** convertir en heure locale avant de comparer, ou bâtir la clé sur la date et la tâche. Les colonnes de la
base, elles, portent l'heure de Paris.

## 21. (piège 193) Commande d'achat créée par l'API : la case « intragroupe » reste vide, aucune commande miroir ne naît

La case `interco` d'une commande d'achat n'est posée que par le service de création (et l'écran) :
`PurchaseOrderCreateServiceSupplychainImpl.setIntercoOnPurchaseOrder` (supplychain 9.1.7, l. 186-191) la coche si
l'app Supply Chain crée les ventes depuis les achats et que le fournisseur est le tiers d'une société. Un
`POST /ws/rest/PurchaseOrder` ne passe pas par là : la validation (`PurchaseOrderWorkflowServiceSupplychainImpl`,
l. 90-95) ne génère alors aucune commande de vente miroir, sans rien dire — seule la facture miroir naît plus tard.
*Constaté le 27/09 (essai 1, Industrie 9.1.7) : achat intragroupe ACH0015 à `interco = false`, commande de la
filiale recréée à la main par l'API.* **À faire :** poser `"interco": true` à la création, et vérifier le statut de
déclenchement de l'app (piège 152, § 11 : 0 par défaut, aucun miroir). Même famille que le piège 186 : ce que le
service de création ou l'écran pose, l'API ne le pose pas.

## 22. (piège 194) Règlement par l'API sans ses échéances : validé sans écriture ni lettrage — en virement, une NullPointerException

La pièce comptable d'un règlement se construit sur les échéances qu'il règle (`invoiceTermPaymentList`,
`InvoicePaymentMoveCreateServiceImpl` l. 318, account 9.1.7). Un `InvoicePayment` créé par `/ws/rest` sans cette liste
passe au statut validé : pas d'écriture de trésorerie, pas de lettrage, facture toujours due. Les lignes à solder
viennent des seules échéances réglées (`MoveToolServiceImpl.getInvoiceCustomerMoveLines`, l. 175-186) ; sans elles,
`createMoveForInvoicePayment` rend `null` (l. 187-188). Avec un mode de paiement qui génère un ordre bancaire (virement),
ce `null` est déréférencé : **NullPointerException** (`InvoicePaymentMoveCreateServiceBankPayImpl` l. 123) — la cause
est vraisemblablement l'absence d'échéances, pas la configuration bancaire (lu dans le code, non rejoué : ne pas
conclure au piège 184 sans avoir essayé le virement avec ses échéances). *Constaté le 27/09 (essai 1) :
25 règlements sans lettrage à l'audit, refaits avec leurs échéances — 25 sur 25 avec écriture et lettrage ; le virement
fournisseur est tombé en NPE aux essais 1 et 2 (réglé par chèque, puis laissé impayé et renvoyé au demandeur) ; cause
lue dans le code, virement avec échéances non rejoué.*
**À faire :** répartir le montant sur les échéances ouvertes de la facture (`invoiceTerm`, `paidAmount`,
`companyPaidAmount`), puis contrôler `move` et `reconcile` du règlement.

## 23. (piège 195) La « date de commande » d'une commande client est la date de sa première facture

`SaleOrderInvoiceServiceImpl.fillSaleOrder` (supplychain 9.1.7, l. 571-575) écrit `orderDate` = date du jour — réelle,
ou simulée si elle est posée — à la génération de la facture. Une facture générée aujourd'hui puis redatée laisse
la commande à la date d'aujourd'hui, et fait lever le contrôle F1 de l'audit (facture antérieure à sa commande) :
défaut réel, qui se corrige en générant la facture sous la date simulée. Le tableau des commandes d'un tiers affiche donc, pour une commande confirmée en mars et
facturée fin avril, le 30 avril. *Constaté le 27/09 (essai 1) : 13 commandes facturées sur 13 ; un correcteur à l'aveugle a lu
la réception usine et le transport « avant la commande » dans une affaire pourtant jouée dans l'ordre.*
**À faire :** générer chaque facture sous la date simulée de son jour (piège 171) ; raconter la chronologie avec
`confirmationDateTime`, en sachant que l'écran datera la commande du jour de sa facture.

## 24. (piège 196) « Compte bloqué » ne se coche ni par un blocage, ni par un règlement

`hasBlockedAccount` se coche par le traitement « Bloquer les clients en retard de paiement »
(`BatchBlockCustomersWithLatePayments`, account 9.1.7) ou à la main sur la fiche (l'écran recopie alors la valeur
dans `hasManuallyBlockedAccount`). Un règlement ne la recalcule que si elle est déjà cochée, pour la décocher
(`InvoicePaymentToolServiceSupplychainImpl` l. 105-108). Un blocage (`base_blocking`) ne la touche pas.
*Constaté le 27/09 (essai 1) : client à 2 factures échues impayées, étiquette « Compte bloqué » et 2 blocages motivés, case à
non — relevé bloquant à l'aveugle. Mécanisme lu dans le code, traitement non rejoué.*
Ce traitement parcourt TOUTES les relances de la base : il bloque et débloque des clients qu'on n'a pas créés.
**À faire :** pour un scénario « compte bloqué », poser les deux cases (`hasBlockedAccount`,
`hasManuallyBlockedAccount`) sur ses propres tiers, comme l'écran ; le traitement, seulement sur une base déclarée
jetable en Phase 1 (règle de sûreté).

## 25. (piège 197) « Produits par société » : des copies figées à l'enregistrement, et un approvisionnement à la vente commun

Option active (liste des champs par société non vide dans l'app Base), `ProductStockRepositorySave` (stock 9.1.7,
l. 55-95) crée à l'enregistrement d'un article une ligne par société dotée d'un emplacement de réception, en
COPIANT les champs par société de ce moment-là ; les changements ultérieurs de l'article ne s'y propagent pas, et les
services lisent la ligne de la société (prix de revient, prix moyen, mode d'approvisionnement). L'approvisionnement
à la vente (`saleSupplySelect`) n'est pas dans la liste : il vaut pour toutes les sociétés.
*Constaté le 27/09 (essais 1 et 2) : prix de revient 1,38 € au niveau de l'article, 1,34 € (PMP réel) dans la ligne d'une société ;
pièce fabriquée par la filiale en « Produire » chez elle mais « Achat » à la vente pour tous — sa commande partait
en achat.* **À faire :** poser les champs de la liste dans la ligne de CHAQUE société, avant toute réception, avec
leurs écarts réels (un mode d'approvisionnement peut différer d'une société à l'autre) ; ne jamais recopier l'article
sur une ligne après un flux, qui a mis la ligne à jour et laissé l'article en l'état. Régler l'approvisionnement à la
vente sur la société qui vend l'article ; si les deux sociétés le vendent, le régler sur l'article pour l'une et le
corriger sur la ligne de commande de l'autre (la ligne le porte).

## 26. (piège 198) « Qté de produits reçus du fournisseur » et la note qualité ne comptent que les lignes contrôlées

`PartnerProductQualityRatingServiceImpl.calculate` (stock 9.1.7, l. 58-78), appelé à la réalisation d'une réception,
ne retient que les lignes dont la conformité est renseignée. Des commandes entièrement reçues laissent donc le
compteur du fournisseur à 0,00 ; une prestation achetée (sans réception) le laisse toujours à 0. *Constaté le 27/09 (essai 1) :
13 commandes d'achat reçues à 100 %, compteur nul sur les fournisseurs dont aucune ligne n'avait de conformité — lu
« réception fantôme » à l'aveugle ; à l'essai 2, conformité saisie sur chaque ligne : notes calculées (4,23/5 après
une non-conformité).* **À faire :** renseigner la conformité de chaque ligne de réception des fournisseurs montrés,
AVANT de réaliser la réception (le calcul se fait à la réalisation) ; la valeur 1 de la sélection n'a peut-être pas
de libellé (`entites-stock.md`, `conformity_select`).

## 27. (piège 199) Un produit complémentaire du TIERS s'ajoute seul à chaque devis — le saisir en plus le double

Option « complémentaires du tiers » active, chaque ENREGISTREMENT d'un devis par l'application — écran, API ou
import — lui ajoute les produits complémentaires de son client (`SaleOrderManagementRepository.save`, sale 9.1.7,
l. 82-84, qui appelle `SaleOrderServiceImpl.manageComplementaryProductSOLines`, l. 297-340) : une fois par devis, ou
une fois PAR LIGNE selon le type de génération. Son contrôle anti-doublon ne reconnaît que les lignes qu'il a
lui-même ajoutées : une ligne saisie en plus pour le même article fait doublon, facturé.
*Constaté le 27/09 (essais 0 et 1) : chaque commande du client portait deux caisses d'export de 6,2 m,
facturées 2 × 780 € sur la commande d'une bande de rechange.* **À faire :** vérifier que le type de génération est
« par devis » ; ne jamais saisir la ligne soi-même ; après création, contrôler qu'elle figure une fois et une seule.
Ne mettre en complémentaire d'un tiers que ce qui convient à TOUTES ses commandes (la notice dans sa langue, un
document de conformité) ; le reste va en complémentaire de l'article concerné.
