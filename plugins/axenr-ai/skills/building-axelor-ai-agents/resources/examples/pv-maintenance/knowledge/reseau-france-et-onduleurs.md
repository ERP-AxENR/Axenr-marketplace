# Exigences réseau France (Enedis BT) et maintenance onduleurs générique

## 1. Référentiel en vigueur
- **Enedis-NMO-RES_025E v1 (15/09/2025)** remplace **Enedis-PRO-RES_10E v7 (01/01/2025)**, qui intégrait l'ancienne note NOI-RES_13E : description et étude des protections de découplage. Base réglementaire : **arrêté du 9 juin 2020** (code réseau européen RfG).
- **DIN VDE 0126-1-1/A1** (réglages VFR2014 puis **VFR2019**) : référence Enedis jusqu'en 2024. VFR2014 refusé depuis le 25/06/2020. VFR2019 a relevé le seuil haut de fréquence à 51,5 Hz.
- **NF EN 50549-1** (BT) / -2 : depuis le **1er janvier 2025**, toute installation > 800 W (date de demande de raccordement) doit fournir un certificat NF EN 50549-1 ou -2, établi selon la norme d'essai **NF EN 50549-10**, en français, avec les réglages de l'**annexe C** (sinon une attestation de réglage est tolérée). Organisme certificateur accrédité ISO/IEC 17065. À terme, contrôle par bureau de contrôle au-delà de 36 kVA (modalités BT en discussion).
- Seuls des onduleurs NF EN 50549-1 sont acceptés pour les installations neuves, les extensions et le **remplacement à l'identique** en maintenance.

## 2. Protection de découplage
| Puissance installée | Solutions admises |
|---|---|
| **Pinst ≤ 250 kVA** (branchement BT ou poste HTA) | Relais externe **B.1** ; ou protection **intégrée aux onduleurs** NF EN 50549-1 (cas normal du PV, plusieurs onduleurs possibles dans la limite de 250 kVA au total) ; ou relais externe NF EN 50549-1 (réservé aux producteurs autres que PV) |
| **Pinst > 250 kVA** | Protection externe de type H (arbre de décision Enedis, raccordement HTA) |

Réponse à la question « protection externe au-delà de 250 kVA en BT ? » : Enedis ne prévoit pas de protection intégrée au-delà de 250 kVA. En HTA, la protection de découplage est **obligatoirement externe**. Une installation de plus de 250 kVA ne relève pas d'un branchement BT (limite de raccordement BT à 250 kVA : à vérifier dans la DTR raccordement).

**Réglages (protection intégrée NF EN 50549-1, instantanés)**
| Fonction | Mesure | Réglage |
|---|---|---|
| Défauts polyphasés : min de V | 3 tensions simples | **80 % Vn** (B.1 : 85 % Vn) |
| Réseau séparé : max de V | 1 tension simple | **115 % Vn** |
| Min de f | 1 tension simple | **47,5 Hz** |
| Max de f | 1 tension simple | **51,5 Hz** |
| Perte de réseau amont | NF EN 50549-1 §4.9.4 | **Détection par saut de phase interdite** |

- Mesure entre phase et **neutre du réseau public** obligatoire : pas de neutre reconstitué, onduleurs triphasés avec neutre raccordé.
- **Moyenne 10 minutes** : seuil réglable entre **110 % Un (réglage usine = 253 V)** et 115 % Un. Le producteur peut demander à Enedis l'autorisation de le relever jusqu'à 115 % Un au plus, notamment si la tension aux bornes de l'onduleur est nettement supérieure à celle du point de raccordement (câble long).
- La protection intégrée assure aussi l'isolement DC avant couplage, le différentiel DC+AC et la détection d'injection DC (1 A).
- Réglage sur site : attestation de réglage en français remise au plus tard à la demande de mise en service ; réglage inaccessible à l'utilisateur.

**Tension de fourniture BT** : 230 V ±10 % en moyenne 10 minutes (arrêté du 24/12/2007), soit 207-253 V. Au-delà de 253 V, le Linky peut afficher « SURTENSION AMONT ».

**Réactif BT** : installations raccordées en BT **après le 01/02/2023** : **tan φ = -0,35** (absorption de réactif égal à 35 % de P en production). Enedis a relevé des écarts sur plus de 7 000 installations > 36 kVA en vente totale ; risque de suspension du contrat d'accès au réseau. Des courriers ont aussi été envoyés aux sites 36-250 kVA en autoconsommation avec vente du surplus. Lois Q(U)/P(U) en BT France : aucune obligation trouvée dans les sources (à vérifier dans la DTR / annexe C). P(U) est imposée en Autriche (TOR Erzeuger) : ne pas transposer.

## 3. Décrochages sur surtension réseau
**Mécanisme** : en injection, la tension aux bornes monte (impédance du réseau + câble AC). En fin de ligne, à midi et à faible consommation locale, la moyenne 10 min dépasse 253 V : découplage (SMA 301/101, Fronius 102), reprise, nouveau décrochage. Signature : dents de scie à midi les jours clairs.

**Élévation dans le câble AC (triphasé équilibré, cuivre)** : ΔU ≈ ρ × L × I / S × cos φ, avec ρ ≈ 0,0225 Ω·mm²/m (à chaud). Monophasé : ×2. Exemple : CORE1 72,5 A, 50 m, 35 mm² → ≈ 2,3 V par phase ≈ 1 %. Cible de conception courante : ≤ 1 % entre onduleur et point de livraison (recommandation UTE C15-712-1, à vérifier).

**Diagnostic**
1. Journal onduleur : horodatage, n° d'événement, tension de déclenchement par phase.
2. Mesurer en injection au point de livraison ET aux bornes de l'onduleur (même instant) : l'écart donne la chute de tension du câble.
3. Enregistreur de tension (analyseur classe A, ou moyenne 10 min sur plusieurs jours ensoleillés), sur les 3 phases. Comparer avec la tension à vide (onduleur arrêté) : si le réseau dépasse déjà ~245-250 V, le problème est le réseau.
4. Déséquilibre : en monophasé, une autre phase peut être moins chargée.
5. Serrage et état des connexions AC (une connexion résistive ajoute de l'élévation) : thermographie.
6. Si la tension réseau est hors plage : réclamation à Enedis (qualité de fourniture) avec relevés. Enedis peut changer la prise du transformateur, rééquilibrer ou renforcer. Pose d'un enregistreur par Enedis : à vérifier.

**Remèdes côté installation** : augmenter la section ou réduire la longueur AC ; demander à Enedis l'autorisation de relever le seuil 10 min (≤ 115 % Un) ; absorption de réactif (tan φ imposée) ; limitation de puissance active ou autoconsommation (pilotage) ; ne jamais modifier les seuils sans accord Enedis (code SMA Grid Guard, accès installateur Fronius).

## 4. Maintenance préventive onduleur : checklist annuelle
- [ ] Consignation (AC puis DC), décharge, VAT, matériel ≥ 1000 V DC.
- [ ] Journaux d'événements sur 12 mois (fréquence, horaires, météo).
- [ ] Visuel : boîtier, presse-étoupes, humidité, rongeurs, étiquetage, dégagements.
- [ ] Nettoyage des radiateurs et ventilateurs (brosse souple, air comprimé propre selon le fabricant, pas de produit nettoyant) ; test ventilateurs (Fronius : menu Ventilateur).
- [ ] Parafoudres AC/DC : voyants ou cartouches, remplacement si déclenchés.
- [ ] Connecteurs DC : état, même marque et même modèle accouplés, pas de chauffe ni de déformation.
- [ ] Mesures DC par string : Voc et Isc (ou courbe I-V), polarité, Riso +/terre et -/terre.
- [ ] AC : tension par phase en injection et à vide, neutre, PE, continuité de terre ; test du dispositif différentiel (Fronius recommande un type A ≥ 100 mA par onduleur s'il est requis).
- [ ] **Couples de serrage** : uniquement les valeurs du fabricant (ex. CORE1 : PE 6 Nm, bornes AC 20 Nm de 35 à 95 mm², 30 Nm en 120 mm²). Resserrer avec une clé dynamométrique, marquage au vernis.
- [ ] **Thermographie** des connexions AC en charge (> 50 % de Pnom de préférence) : comparer les phases identiques entre elles ; tout point chaud isolé est à reprendre (seuils de classification ΔT : à vérifier selon le référentiel retenu, IEC TS 62446-3 pour les modules).
- [ ] Micrologiciel, heure, communication, portail ; réglages réseau (jeu France, tan φ, attestation archivée) ; rapport avec mesures et photos.

## 5. Lire les courbes de production
- **Comparer les onduleurs identiques** entre eux (kWh/kWc) : un écart durable > quelques % appelle une analyse.
- **Par MPPT et par string** : courant MPP proportionnel au nombre de strings. Courant nul = fusible, connecteur, string ouvert. Courant réduit d'environ 1/3 du module = diode bypass ou cellule. Tension MPP basse = modules court-circuités.
- **Formes caractéristiques** : plateau à midi = écrêtage (surdimensionnement DC, limitation d'injection ou derating thermique, à corréler avec la température) ; dents de scie à midi = décrochages réseau ; démarrage tardif ou matin à zéro = défaut d'isolement à la rosée (Riso) ; creux à heure fixe = ombrage ; baisse progressive = encrassement.
- **PR (IEC 61724-1)** = E_AC / (P_STC × H_POA / 1 kW/m²), H_POA = irradiation dans le plan (kWh/m²). Ordre de grandeur 75-85 % (à vérifier selon le site) ; le PR corrigé en température gomme l'effet saisonnier.
- **Disponibilité** = temps de production / temps au-dessus du seuil d'irradiance (seuil fixé au contrat O&M, à définir). Indisponibilités réseau exclues ou non selon le contrat.

## 6. Cas terrain
1. **Décrochages à 253 V (Belgique, bricozone.be ; résumé de recherche, fil non relu)** : coupure sur moyenne 10 min > 253 V (264,5 V en instantané). Pistes appliquées : comparer les 3 phases au moment des décrochages et changer de phase si une phase est plus basse ; signalement au GRD (changement de phase ou baisse de la tension de référence en cabine) ; contrôle de la section AC (> 6 V d'écart constaté sur une faible longueur). Le GRD a conclu à l'absence de dépassement sur des moyennes 15 min alors que l'onduleur décrochait : mesurer soi-même en 10 min. https://www.bricozone.be/t/decrochage-chute-de-tension-interessant-de-passer-du-42-au-62-avec-une-longueur-de-11m.157305/ , https://www.bricozone.be/t/tension-ac-trop-haute-onduleur.114341/
2. **Fronius Symo, code 102 alors que la tension mesurée est normale (forum Mike Holt, USA ; résumé de recherche)** : apparu après une mise à jour du Datamanager. Retirer la carte n'a rien changé. Contournement : fermer le sectionneur DC seulement après l'affichage « DC basse » (~30 s). Cause non identifiée : vérifier le micrologiciel avant de soupçonner le réseau. https://forums.mikeholt.com/threads/fronius-symo-error-102-ac-voltage-too-high.125480/

## Sources
- https://www.enedis.fr/media/2162/download (Enedis-NMO-RES_025E v1 / PRO-RES_10E v7, §2.3, §3.6)
- https://www.photovoltaique.info/fr/realiser-une-installation/regles-conception-mise-en-oeuvre/normes-electriques-applicables-aux-systemes-pv/protection-de-decouplage/
- https://www.photovoltaique.info/fr/actualites/detail/publication-conformite-des-onduleurs-passage-la-din-vde-0126-1-1-vfr2019/
- https://www.photovoltaique.info/fr/actualites/detail/nouveau-courrier-enedis-concernant-le-reglage-du-reactif-en-basse-tension/
- https://selectra.info/energie/actualites/marche/ampoules-qui-grillent-tension-trop-haute (207-253 V, arrêté 24/12/2007)
- https://www.seban-associes.avocat.fr/?p=118756 (moyenne 10 min ±10 %)
- https://manuals.sma.de/STP50-40/fr-FR/391152011.html (couples CORE1)
- https://manuals.fronius.com/html/4204101909/fr.html
- https://www.energiesparhaus.at/forum/82970 (DDR ≥ 100 mA, Fronius)
- Cas : liens bricozone.be et forums.mikeholt.com ci-dessus
