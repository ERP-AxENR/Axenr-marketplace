# Surface des fiches Tiers, Contact et Article — ce que l'écran affiche, et comment le remplir

**À lire dès qu'une fiche Tiers ou Article doit être « complète ».** Relevé le 2026-09-27 sur la vue
que l'application SERT (extensions de tous les modules fusionnées) : AOS 9.1.7, AOP EE 8.2.3, package
Industry (52 modules), 19 options d'app activées (§1). Sur une autre version ou un autre jeu de
modules, les noms tiennent presque tous, les blocs visibles non : **mesurer**, ne pas supposer.

## 0. Mesurer, fiche par fiche — `scripts/form_coverage.py`

```
python3 scripts/form_coverage.py --base http://<hôte>:<port>/<app> \
    --model com.axelor.apps.base.db.Partner --view partner-form --ids 101,102 --quiet --json sortie.json
```
Instance **hébergée** : aucun mot de passe dans la commande. L'utilisateur ouvre lui-même une session REST dans
son terminal (recette curl : SKILL.md, § Prérequis), exporte `AOS_URL`, `AOS_COOKIE_JAR` et `AOS_CSRF`, et le
script se lance alors par `python3 scripts/form_coverage.py --model … --view … --ids … --quiet --json
sortie.json`, sans `--base`, `--user` ni `--password` (ignorés : l'URL et le cookie viennent de la session). Sans
session, le script n'a aucun identifiant par défaut : `--user` (ou `AOS_USER`) et le mot de passe en `AOS_PASSWORD`,
exporté par l'utilisateur (jamais dans la commande).
Prérequis : `python3` et `node` (évaluation des conditions). Sur une passe complète (des dizaines de
fiches), toujours `--quiet --json` : le détail de chaque fiche sature le contexte. L'outil lit PAR
L'APPLICATION : après un `UPDATE` SQL sur une application qui tourne, il montre le cache (règle 12),
pas la base — redémarrer avant de mesurer.
Il rejoue le client web : vue servie, onLoad (ses `attrs` et ses valeurs), showIf / hideIf de chaque
élément ET de ses ancêtres, en lecture (une fiche existante s'ouvre en lecture) et en édition, puis
chaque tableau de bord par son action et son filtre réels. Sortie par fiche : éléments visibles, pleins,
couverture (toutes valeurs, puis hors cases à cocher — une case posée à « non » compte pleine),
et la liste des vides avec leur état :
- `vide` — à remplir, ou à justifier DANS LE RAPPORT (jamais dans le champ) : sans objet pour ce type de fiche
  (§6), produit par un flux que le contrat exclut, ou commentaire ou note sans information propre à la fiche (règle 2) ;
- `vide-calculé` / `zéro-calculé` — en lecture seule : une formule ou un flux le remplit (dates du
  dernier et du prochain événement : créer les événements ; prix moyen, dernier prix d'achat : jouer
  l'achat et la réception). Pas une excuse : la donnée source manque ;
- `zéro` — nombre saisissable à 0 : présent pour `count()`, vide pour la démo ;
- `sélection-invalide` — valeur absente de la liste : défaut franc (règle cardinale 4) ;
- `graphique` — tableau de bord graphique, hors calcul : contrôler sa donnée source en base.
Hors écran : `masqués mais remplis` — une donnée que la fiche NE montre PAS pour ce type (stock sur
un service…) : du hors-de-propos à signaler ; ne vider que ses propres créations (règle de sûreté).
Vues : tiers `partner-form`, contacts `partner-contact-form` (une autre fiche, §3), articles
`product-form`, famille `product-family-form` (sa configuration comptable).

Repères mesurés (Industrie 9.1.7, 19 options) — couverture BRUTE (éléments visibles pleins / visibles) :
tiers de démo AOS APOLLO (#1) 47/108, soit 43 % (34 % hors cases à cocher) ; article stockable de démo
EQPT-0002 (#3) 49/118, 42 % ; service ABO-0001 (#1) 31/66, 47 % — utilisables en témoin avec
`--expect` (valeurs de l'outil au 27/09 ; une nouvelle version de l'outil se re-mesure). Autre mesure,
autre dénominateur — éléments ATTENDUS pleins selon §6 : l'essai 0 du 27/09, sans cet outil,
atteint 85,5 % en moyenne, aucune fiche à 100 %.

## 1. Options d'app qui ajoutent des blocs — et celles qui piègent

Les gardes `if=` d'une vue sont évaluées par le serveur : une option décochée RETIRE le bloc de la fiche.
Relevé 9.1.7 (fiche Tiers 141 → 156 éléments, fiche Article 124 → 152 une fois les 19 activées) :

| Option (app) | Ce qu'elle ajoute |
|---|---|
| Relations entre tiers (Base) | liens « géré par / pour » (`base_partner_link`), tiers payeur |
| Filiales (Base) | tiers parent, tableau des filiales |
| Variantes (Base) | onglet Variantes (config, attributs, variantes générées) |
| Sécurité produit (Base) | onglet Sécurité (étiquette, CLP, pictogrammes, phrases, ICPE, COV, densité) |
| Codes-barres multiples, type modifiable (Base) | codes-barres alternatifs, type de code-barres |
| Processus CRM sur les tiers, agences, partenaires corporate (CRM) | statut du tiers et ses menus de prospects, agence, onglet partenaire corporate |
| Catalogue client, complémentaires du tiers, quantités multiples, configurateur (Vente) | catalogues client, produits complémentaires du tiers, quantités de vente multiples, lien configurateur |
| Quantités multiples, appels d'offres (Achat) | quantités d'achat multiples, attributs d'appel d'offres |
| Prélèvement SEPA (Paiement bancaire) | mandats de prélèvement par société (`account_invoicing_payment_situation`) |
| Sous-traitance, groupes de feuilles de coût (Production) | case « sous-traitant » du tiers, groupe de feuille de coût |

**Ne pas activer pour « avoir plus de champs »** : gestion des enseignes et vente/achat par enseigne
(lignes de commande masquées, devis figés) ; produits
par société (choix de modèle tarifaire ; en 9.1.3 les champs de prix listés quittent la fiche, en 9.1.7 la fiche
montre les valeurs de l'article, que les flux ne mettent plus à jour — piège 197) ; devis et commandes séparés (change le flux de vente) ;
sites de stock (change la gestion des emplacements). Une option d'app est une décision du demandeur :
la proposer dans la salve de départ ou dans le rapport, ne jamais la basculer en silence.

## 2. Fiche Tiers (`partner-form`) — par onglet

Chaque ligne : ce que l'élément exige, et la voie (SQL = état ; moteur = transition par `/ws/action`).
Les pièges par entité restent dans les fiches `entites-*.md` : tiers et contacts `entites-tiers-contacts.md`,
CRM `entites-crm.md`, ventes et factures `entites-ventes.md`, achats `entites-achats.md`, stock
`entites-stock.md`, affaires `entites-projet-temps.md`.

| Onglet / bloc | Éléments | Comment |
|---|---|---|
| En-tête, Propriétés | rôle (client, prospect, fournisseur, sous-traitant, transporteur, interne, corporate, affactureur, tiers payeur), statut CRM, photo | cases posées TOUTES (règle 3) et cohérentes avec le rôle réel ; statut = `crm_partner_status` (option CRM sur les tiers) ; photo d'une SOCIÉTÉ = logo sobre à initiales, par `scripts/generate_visuals.py --model partner` (§9) |
| Détails | catégorie, secteur, provenance, taille, tags, SIRET, NAF, n° TVA, chiffre d'affaires, tiers parent | SQL ; SIRET valide sur ses 14 chiffres, pas seulement le SIREN (piège 61) ; SIRET seulement pour une société française — un n° BCE belge ou un HRB allemand est légitime, le n° de TVA étranger porte le préfixe de son pays ET un chiffre de contrôle calculé selon l'algorithme du pays (§8) ; NAF ↔ secteur ↔ description (règle 10) |
| Relations entre tiers | liens « géré par / pour » | `base_partner_link` (partner1, partner2, type) |
| Information | adresses typées, consentements RGPD (e-mail, courrier, SMS, téléphone : dates), téléphones, e-mail, site, commercial, équipe, agence, sociétés, description | adresses : `base_address` + `base_partner_address` + ville obligatoire à l'écran (`entites-tiers-contacts.md`, colonne `city`) ; e-mail : `message_email_address` ; `base_partner_company_set` (piège 123) |
| Facturation / Paiement | envoi des factures, modes et conditions entrant et sortant selon le rôle, position fiscale (export), RIB, mandats de prélèvement, commentaires | RIB : IBAN à clé valide ; mandat seulement si le client paie par prélèvement ; commentaires de facture et de proforma : une consigne PROPRE au tiers, ou rien (règle 2) ; jamais un texte de vente sur un fournisseur ; la mention des pénalités de retard ne va pas dans le tiers — si le modèle d'impression ne la porte pas, le signaler dans le rapport, sans modifier ce modèle partagé (règle de sûreté) |
| Informations comptables | situation comptable par société | créée par l'application quand le tiers s'enregistre par l'écran ou l'API ; un tiers inséré en SQL n'en a pas avant sa première ventilation (piège 184, 3e point) : la créer (piège 13) |
| Blocages | blocages (`base_blocking`), cases « Compte bloqué » et « Compte bloqué manuellement » | au moins un client bloqué avec une raison, jamais sans raison ; un blocage ne coche PAS « Compte bloqué » : pour un scénario « compte bloqué », poser les deux cases sur ses propres tiers, sinon l'étiquette et la case se contredisent ; le traitement de blocage, seulement sur une base jetable (piège 196) |
| Événements | tableau des événements, dates du dernier et du prochain | événements passés ET à venir, rattachés au tiers, à un contact du tiers et en `relatedTo` (piège 42) ; les dates se remplissent seules |
| Opportunités, Contrats, E-mails, Campagnes | tableaux (voir §5) | contrats client (`targetTypeSelect = 1`) et fournisseur (`= 2`) ; e-mails = messages réels, facultatifs |
| Client | liste de prix (une seule par défaut), catalogue client, franco de port, commentaires, tableau des devis et commandes | commandes et factures par le moteur (règle 12) ; au moins une facture ventilée par client ; la colonne « date de commande » du tableau est la date de la 1re facture (piège 195) |
| Parc client | équipements, interventions, notes d'intervention | `intervention_equipment` (tiers, n° de série, mise en service) ; un équipement « en service » suppose la machine livrée (règle 12) |
| Partenaire corporate | domaines, zones de travail, fidélité du partenaire (`crm_fidelity`), partenaire depuis | seulement pour un distributeur ou revendeur coché « corporate » ; le palier de fidélité est cohérent avec le chiffre d'affaires de ses commandes (« Or > 250 k€ » pour 3 k€ de commandes se lit faux) |
| Fournisseur | catalogue fournisseur (référence et prix DU FOURNISSEUR, piège 84), liste de prix d'achat, franco, note qualité, tableau des commandes d'achat | au moins une commande d'achat réceptionnée ET facturée par fournisseur — organisme de contrôle, sous-traitant et transporteur compris |
| Tickets | tableau des tickets | `helpdesk_ticket.customer_partner`, sur les équipements du client |
| Transporteur, Livraison | modes de transport du transporteur ; délai, mode d'expédition, transporteur, NIMP 15, certificat de conformité, n° de compte chez le transporteur, commentaires | mode d'expédition et transporteur posés sur chaque client livré, selon ce qu'il reçoit (pas le même mode sur toute une famille de tiers) ; commentaires de livraison et de préparation : propres au tiers ou vides (règle 2) |
| Projets | affaires du client, projets de facturation | affaire créée depuis la commande par le moteur ; la compléter (code, nom) |
| Activité (option CRM) | activité récente et passée du prospect | événements et opportunités du prospect |
| Qualité | améliorations qualité client et fournisseur, contrôles qualité | `quality_quality_improvement` via son identification (client ou fournisseur) ; contrôle rattaché au tiers |
| Produit | produits complémentaires du tiers | `sale_complementary_product.partner` : AOS l'ajoute à chaque enregistrement de ses devis (piège 199) — seulement ce qui convient à toutes ses commandes, génération « par devis », jamais saisi en plus (doublon facturé) |

**Les tiers des sociétés du groupe** (fiche tiers de la mère et de chaque filiale) : ce sont des
fiches Tiers comme les autres dès qu'un flux intragroupe existe — SIRET, adresses, contacts, RIB,
conditions, situation comptable. *Essai 0 du 27/09 : fiche de la filiale laissée à 42 %, sans SIRET.*

## 3. Fiche Contact (`partner-contact-form`)
Civilité, prénom, NOM, fonction (`base_function`), service (`base_company_department`), responsable
(`reportsTo`, un autre contact de la même société), téléphones, e-mail AU DOMAINE de sa société,
consentements, société principale (`main_partner`) ET ligne dans `base_partner_contact_partner_set`
(piège 108), contacts liés ; tableaux : opportunités et devis où il est le contact, événements.
Dates de consentement et note propres à chaque personne (pas un jeu de dates par type de contact, pas la
fonction recopiée en note). « Contacts liés » est CALCULÉ : les autres contacts de la même société — un
contact de test de la démo AOS rattaché à cette société (DEMOERP, DEMOCRM) y apparaît : le signaler dans le
rapport, ne pas toucher à ce qu'on n'a pas créé.
*Essai 0 du 27/09 : service, responsable, consentement SMS vides sur les 45 contacts.*

## 4. Fiche Article (`product-form`) — par onglet
Pièges par entité : articles, familles, unités `entites-produits.md` ; stock et réceptions
`entites-stock.md` ; nomenclatures, gammes, OF `entites-production-btp.md` ; achats et catalogues
`entites-achats.md` ; ventes `entites-ventes.md`.

| Onglet / bloc | Éléments | Comment |
|---|---|---|
| En-tête | type, sous-type, mode d'approvisionnement (`procurementMethodSelect` ; avec l'option « produits par société », propre à chaque société : piège 197), délai standard, famille ET catégorie (pièges 11, 11 bis), code-barres, photo (visuel sobre par `scripts/generate_visuals.py --model product`, §9) | le code-barres (image) est généré par l'application à l'enregistrement, depuis le n° de série (= le code s'il est vide) et le TYPE de code-barres (§7) : pas de type sur un service ; délai standard réaliste pour le type d'article (des semaines pour une machine à l'affaire, pas 0) |
| Vente | prix, devise, unité, approvisionnement à la vente (`saleSupplySelect`), dates de validité, quantités multiples, catalogue client, **produits complémentaires**, descriptions | approvisionnement à la vente : COMMUN à toutes les sociétés, réglé sur la société qui vend (piège 197) ; « Achat » sur un article stocké fait naître un achat à chaque commande. Complémentaires (`sale_complementary_product.original_product`) = options, accessoires, pièces, services de CET article ; jamais lui-même, jamais un article non vendable, rien sur une matière ou un service acheté |
| Achat / Coûts | prix, devise, unité, fournisseur par défaut, délai, quantités multiples, prix de revient et mode, coefficient, catalogues fournisseur (1 à 3), historique d'achat | historique = commandes d'achat validées ou reçues (moteur) |
| Comptabilité | analytique, DEB, écotaxe, configuration comptable | la configuration vit sur la FAMILLE (`account_account_management.product_family`, par société, comptes de vente ET d'achat) : contrôler la famille |
| Stock | stock géré, unité, MRP, type d'inventaire, homologation, contrôle à réception, prix moyen, rotation ; tableaux : stock par emplacement, règles de stock, historiques | stock issu de vraies réceptions (moteur) ; règles mini/maxi sur les articles achetés et stockés ; RIEN de tout cela sur un service |
| Information production | nomenclature et gamme par défaut, valorisations (piège 25), groupe de feuille de coût ; tableaux : nomenclatures, « utilisé dans », gammes | chaque article FABRIQUÉ a sa nomenclature ET sa gamme (pièges 10, production) ; chaque composant apparaît dans au moins une nomenclature |
| Numéro de suivi | configuration | n° de série sur les machines, lot sur les consommables qui le justifient |
| Variantes | configuration, gestion du prix, variantes, article parent | SEULEMENT pour un article qui se décline en tailles ou capacités normalisées : `base_product_variant_config` + attributs + variantes générées (`parent_product`) |
| Modèles de tâches | modèles | services vendus qui ouvrent des tâches d'affaire (option d'affaire) |
| Liens | mouvements prévus et réalisés, consommations | produits par les flux : réceptions, livraisons, OF (règle 12) |
| Colisage | unité de masse, brut > net, unité de longueur, dimensions, code douanier, pays d'origine ; champs d'emballage ; ADR ; conditionnements | tout article physique a masses et dimensions AVEC leur unité (règle 2) ; emballage seulement pour un article « emballage » ; ADR seulement pour une marchandise dangereuse |
| Sécurité | étiquette (fichier), CLP, rétention, ICPE, pictogrammes, phrases de danger, densité, COV, empreinte carbone | SEULEMENT pour un produit dangereux (huile, solvant, colle…) ; l'empreinte carbone peut valoir pour tout article physique |
| Qualité | améliorations, contrôles, plans de contrôle, relevés | plan de contrôle sur les composants critiques reçus ; lignes de plan et d'échantillon, attributs attendus : pièges 50 et 51 (`methode-coherence.md`) |
| Nomenclature commerciale | kits de vente | facultatif |

## 5. Tableaux de bord : objet, filtre, ce qui les peuple (relevé 9.1.7)

| Tableau (fiche) | Objet | Filtre | Se peuple par |
|---|---|---|---|
| Devis/Cmdes (Tiers) | SaleOrder | client OU contact = le tiers | moteur |
| Commandes d'achat (Tiers) | PurchaseOrder | fournisseur = le tiers | moteur |
| Événements (Tiers) | Event | tiers, ou relatedTo = le tiers | SQL |
| Opportunités (Tiers) | Opportunity | tiers | SQL (sans lignes, règle 12) |
| Contrats client / fournisseur (Tiers) | Contract | tiers + `targetTypeSelect` 1 / 2 | moteur (contrat et versions) |
| Tickets (Tiers) | Ticket | `customerPartner` | SQL |
| Équipements, interventions (Tiers) | Equipment, Intervention | `partner`, `deliveredPartner` | SQL (équipements), moteur (interventions) |
| Filiales (Tiers) | Partner | tiers parent | SQL |
| Campagnes (Tiers) | Campaign | `partnerSet` | SQL |
| Qualité client / fournisseur (Tiers) | QualityImprovement | identification client / fournisseur | API (séquence par société, pièges 200 à 204, `entites-qualite.md`) |
| Audits qualité (Tiers, Article) | QualityControl | `relatedToSelect` + id | API + bouton de pré-remplissage (piège 211, `entites-qualite.md`) |
| Projets, projets de facturation (Tiers) | Project, InvoicingProject | client de l'affaire | moteur |
| Historique d'achat (Article) | PurchaseOrderLine | commande validée ou reçue, datée ≤ aujourd'hui | moteur |
| Stock (Article) | StockLocationLine | emplacements hors virtuels | moteur (réceptions) |
| Règles de stock (Article) | StockRules | article | SQL |
| Mouvements prévus, consommations (Article) | StockMoveLine | article + statut / type / emplacement | moteur |
| Nomenclatures, « utilisé dans », gammes (Article) | BillOfMaterial, BillOfMaterialLine, ProdProcess | article | SQL (pièges 10, production) |
| Variantes (Article) | Product | article parent | moteur (génération des variantes) |
| Conditionnements (Article) | ProductPackaging | article emballé | SQL |
| Gammes de contrôle (Article), relevés de contrôle (Article, Lot) | ControlPlan, ControlEntry | `relatedToSelect` + id | API + boutons (pièges 205 à 207, `entites-qualite.md` ; attributs et lignes à double rôle : pièges 50 et 51, `methode-coherence.md`) |
| Stock, historique du stock (Article) | graphiques | jeu SQL propre | leur donnée source : les lignes de stock |

## 6. Réalisme par type de fiche — attendu, au moins une fiche, sans objet

La MÉTHODE vaut pour toute base : par type de fiche, un élément affiché est attendu (sur chaque fiche),
attendu sur AU MOINS UNE fiche du type (la capacité se montre), au choix, sans objet, ou interdit
(rempli, c'est du hors-de-propos). La LISTE ci-dessous est un exemple : un fabricant industriel à
l'affaire (essais du 27/09, Industrie 9.1.7) — la réécrire pour un négoce, un BTP, une ESN.
- **Client** : au moins une fiche avec parc installé, interventions, contrat de maintenance, tickets,
  affaire, réclamation qualité, catalogue client, liste de prix, mandat de prélèvement, blocage motivé,
  filiale ou tiers parent ; aucun élément fournisseur.
- **Prospect** : statut, opportunités, événements, score ; un motif de perte sur au moins un ; JAMAIS
  de parc, de contrat, de mandat ni de catalogue client.
- **Fournisseur** (matières, composants, contrôle, prestations) : catalogue, commandes d'achat
  reçues et facturées, RIB, mode et condition de paiement sortants ; au moins un contrat
  (accord-cadre), une non-conformité, un contrôle qualité ; aucun élément client.
- **Sous-traitant**, **transporteur** : comme le fournisseur ; le transporteur porte ses modes de
  transport.
- **Tiers du groupe** : RIB et tout ce que ses flux intragroupe montrent.
- **Distributeur** (corporate) : domaines, zones, fidélité, date d'entrée.
- **Contact** : tout ce que sa fiche affiche, sauf la note (propre à la personne, ou vide : règle 2) ; téléphone
  portable, photo, tags au choix.
- **Machine fabriquée** : nomenclature, gamme, valorisations, n° de série, complémentaires ; au
  moins une avec conditionnement, catalogue client, réclamation, modèle de tâches ; JAMAIS de
  variantes (sauf gamme normalisée → type « décliné ») ni de fiche sécurité ; pas d'achat.
- **Sous-ensemble fabriqué** : nomenclature, gamme, « utilisé dans » ; pas de vente.
- **Composant, matière** : achat complet (catalogue, historique), stock non nul, règle de stock,
  « utilisé dans » ; au moins un avec quantités multiples, plan de contrôle, mouvements de
  consommation ; JAMAIS de complémentaire ni de fiche sécurité.
- **Produit dangereux** : achat, stock, règle, fiche sécurité complète, ADR s'il voyage.
- **Pièce détachée** : achat ET vente, stock, règle ; au moins une avec quantités multiples,
  catalogue client.
- **Article décliné** : configuration et variantes ; le modèle n'est ni vendable ni stocké quand il ne se vend que
  par ses variantes (sinon il double une variante dans les listes, et un devis le prend sans cote — essais 1 et 2 du
  27/09). **Variante** : parent, attributs, et sa propre description interne — la génération recopie celle du
  modèle (`ProductServiceImpl.createProduct`, 9.1.7) : la réécrire pour la variante.
- **Service vendu** : vente, modèles de tâches ; JAMAIS de stock, de colisage ni de type de code-barres (§7).
- **Service acheté** : achat, catalogue fournisseur ; au moins un avec historique ; JAMAIS de stock.

## 7. Pièges relevés par les essais du 27/09/2026 (Industrie 9.1.7)
- Compter les articles avec `dtype = 'Product'` : les lignes « article par société » partagent la table
  (`entites-ventes.md`, prédicats des menus produits).
- Avant de dater un historique de factures, lire `max(invoice_date)` des factures ventilées de chaque
  société : AOS refuse d'en ventiler une antérieure (piège 185) — une facture de test à la date réelle
  interdit tout historique.
- À chaque enregistrement par l'application (écran, API, import), AOS recopie le code dans le n° de
  série s'il est vide, puis génère l'image du code-barres si la génération est active
  (`ProductBaseRepository.save`, lu en 9.1.6). Le TYPE pris est celui de l'ARTICLE si l'option « type de
  code-barres modifiable » est active — sans type, pas d'image —, sinon celui de l'app pour tous les
  articles. Donc, option active : ne jamais poser de type sur un service. *Essai 0 du 27/09 : type QR posé sur
  les 13 services → QR code en tête de leur fiche, noté bloquant à l'aveugle.*
- Un même champ peut porter deux titres selon le type d'article : `usedInDEB` s'affiche « DES »
  (services) ou « DEB » (biens) — cocher selon la nature ET les échanges intra-UE réels.
- Des champs qu'on croit saisis sont posés par un flux précis — lire l'entrée avant de raconter une histoire avec
  eux : « date de commande » (piège 195) ; « Compte bloqué » (piège 196) ; quantité reçue et note qualité du
  fournisseur (piège 198) ; « date de dernière visite », si le module des tournées commerciales est installé :
  posée par la validation d'une ligne de tournée (`TourLineServiceImpl`, 9.1.7), jamais par un rendez-vous.
- Référentiel de transport de la démo AOS (dump Industrie 9.1.7) : des modes rattachés au mauvais
  transporteur (« Colissimo » et « La poste Business international solution » sous Mondial Relay, « TNT
  Express » sous La Poste, « Relais colis » sous UPS). Le transporteur d'un tiers se DÉDUIT de son mode :
  choisir « Colissimo » affiche « Mondial Relay ». Lire le couple avant de réutiliser un mode, ou créer le
  transporteur et ses modes du scénario (essai 2 du 27/09 : trois clients à « Colissimo / Mondial Relay »).
- Option « produits par société » active (c'est le cas du dump Industrie) : la fiche montre les valeurs de
  l'article, que les flux ne mettent plus à jour ; les valeurs à jour (prix de revient, prix moyen) sont dans la
  ligne de chaque société (piège 197).

## 8. Réalisme fin — exemple d'un fabricant industriel (notations à l'aveugle du 27/09/2026, essais 0, 1 et 2)
Ce que quatre correcteurs ont vu et que ni l'audit SQL ni la couverture d'écran ne mesurent — des
familles de défauts qui valent au-delà de cet exemple :
- **Un commentaire ou une note est propre à sa fiche, ou vide** (règle 2) : ni le même commentaire de
  facture, de livraison ou de commande sur plusieurs tiers, ni un texte de vente sur un fournisseur (« acompte
  à la commande pour les machines » chez le négociant d'aciers), ni une réponse de convenance écrite dans le
  champ (« Sans objet (fournisseur). ») ; même règle pour les notes de contact et les objets d'e-mails. Les
  descriptions de tiers et d'articles, elles, restent attendues. *Essai 1 du 27/09 : 30 des 34 défauts
  bloquants ; essai 2 : un seul commentaire d'achat identique sur 9 fournisseurs, 9 bloquants.*
- **Un scénario se lit dans ses propres champs** : « compte bloqué » ↔ case « Compte bloqué » (piège 196) ;
  palier de fidélité ↔ chiffre d'affaires de ses commandes ; approvisionnement à la vente ↔ ce que fait la société
  qui vend (piège 197) ; complémentaire d'un tiers ↔ chacune de ses commandes (piège 199) ; description d'un client
  ↔ son parc (« 1,2 km de convoyeurs » pour 68 m au parc se lit faux) ; opportunité en « Proposition » ↔ un devis.
- **Une histoire se dénoue.** Une non-conformité fournisseur se joue jusqu'au retour et à l'avoir, plutôt
  qu'une facture laissée « en attente » (décision de l'utilisateur du 27/09). Les factures échues d'un historique se
  règlent, sauf un retard que le scénario veut montrer ; par l'API, voir le piège 194. *Essai 2 du 27/09 : 21
  factures fournisseurs ventilées, aucune réglée, et la question renvoyée en fin de rapport.* Les conditions de
  paiement à plusieurs échéances ne s'utilisent que si la demande les nomme.
- **Chaque texte a son rôle** : la description interne dit ce que le client ne lit pas (fournisseur,
  méthode, point de vigilance), elle ne recopie pas la description commerciale ; la note d'un contact
  n'est pas sa fonction.
- **Paires corrélées du tiers** (règle 10) : catégorie (TPE, PME, ETI, grand compte) ↔ effectif ↔
  case « grand compte » — seuils : TPE moins de 10 personnes et au plus 2 M€ de chiffre d'affaires, PME
  moins de 250, ETI moins de 5 000 (essai 2 du 27/09 : une GmbH de 250 à 499 personnes en « PME », deux
  sociétés de 10 à 19 personnes en « TPE ») ; provenance = canal d'acquisition d'un client (jamais « Client existant » sur
  un fournisseur) ; équipe et agence ↔ région du tiers.
- **Note qualité fournisseur** : qui l'écrit décide (piège 93) — elle se calcule à la réalisation des
  réceptions, sur les seules lignes dont la conformité est renseignée (piège 198) ; une non-conformité se montre par une réception
  déclarée non conforme, sinon la note reste à 5/5 à côté.
- **Compatibilité** : un complémentaire ou une pièce de rechange doit aller sur la machine (largeur,
  capacité, dimensions portées par les noms, longueur développée d'une bande) ; une machine qui en
  transporte une autre doit la porter.
- **Complémentaires propres à chaque machine** : ses options et pièces (le palan d'une potence, la bande
  d'un convoyeur), pas seulement les mêmes services partout ; l'optionnel suit une règle (réglementaire
  = obligatoire, confort = optionnel). Ceux d'un TIERS s'ajoutent à toutes ses commandes (piège 199) : seulement
  ce qui convient à chacune (pas de forfait de déplacement sur des commandes de pièces, pas la caisse d'une machine).
- **Catalogue fournisseur** (piège 84) : pour un composant de marque, la référence CONSTRUCTEUR ;
  jamais notre libellé recopié ni une référence tirée d'un gabarit.
- **Prix unitaires** : prix de l'unité de l'article (pas d'une boîte) ; prix au kilo cohérents entre
  matières et nuances (un inox 316L coûte plus que le 304L) ; prix intragroupe = prix de cession de la
  liste de groupe, pas le prix de vente.
- **Codes et identifiants étrangers** : n° de TVA intracommunautaire avec le préfixe du pays ET un chiffre de
  contrôle calculé selon l'algorithme du pays (DE : 9e chiffre par ISO 7064 MOD 11,10 sur les 8 premiers ; BE :
  modulo 97) — faux aux essais 0 et 2 ;
  code douanier choisi sur la désignation réelle (convoyeur à rouleaux ≠ convoyeur à bande) — le
  chercher, ne pas le supposer.
- **Service suivi en feuille de temps** : unité de temps (heure, jour), jamais « Année » ou « Unité ».
- **Sécurité** : le type de rétention suit la substance (huile ≠ acide).
- **Variantes** : leurs libellés (fiche, catalogue fournisseur, lignes de commande) portent les valeurs
  d'attributs (cotes) ; leur description interne n'est pas celle du modèle (§6).
- **Calendrier** : pièces et rendez-vous en jours ouvrés ; un ticket de SAV suit la livraison.

## 9. Photos et logos — `scripts/generate_visuals.py`
Décision de l'utilisateur (27/09/2026) : sans catalogue photo du client, une fiche Article reçoit un visuel
SOBRE — pictogramme de sa nature (convoyeur, levage, table à ciseaux, pièce de rotation, fluide,
électrique, matière, visserie, service, colis par défaut), son code et son nom — et une fiche Société un
logo à initiales. La photo est donc attendue sur les articles et les sociétés ; un contact garde la sienne
au choix (pas de visage inventé).
```
python3 scripts/generate_visuals.py --base <url> --model product --ids <ids> --dry-run <dossier>
python3 scripts/generate_visuals.py --base <url> --model product --ids <ids>
python3 scripts/generate_visuals.py --base <url> --model partner --ids <ids>
```
Sur une instance **hébergée**, même règle que pour `form_coverage.py` (§0) : pas de mot de passe dans la
commande, session REST ouverte par l'utilisateur (variables `AOS_URL`, `AOS_COOKIE_JAR`, `AOS_CSRF`) ;
`--base`, `--user` et `--password` sont alors ignorés.
Regarder d'abord le rendu (`--dry-run` écrit les PNG). Le script ne remplace jamais une image posée,
mais il en pose une sur TOUTE fiche sans image qu'on lui donne : ne lui passer que ses propres créations.
Il téléverse (`MetaFile/upload`, réponse en tableau : piège 87) puis rattache `picture` par l'API — un
ENREGISTREMENT de la fiche, qui rejoue sa sauvegarde (§7) et réécrit l'entité depuis le cache : joué après
des `UPDATE` SQL sans redémarrage, il les annulerait (piège 96). Donc : avant les passes SQL de
complétion, ou après le redémarrage qui suit la dernière ; puis mesurer (dimension 14). Code retour 1 si
une fiche a échoué. Prérequis : Pillow.
