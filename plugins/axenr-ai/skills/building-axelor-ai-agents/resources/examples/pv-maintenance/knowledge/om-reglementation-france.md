# O&M photovoltaïque et réglementation France

Valeur non vérifiée = "(à vérifier)". État des textes au 19/10/2026 : les tarifs OA évoluent souvent, toujours revérifier sur photovoltaique.info et edf-oa.fr.

## 1. Maintenance préventive

**Périodicité** : visite **annuelle au printemps** (modèle HESPUL : 1er mars-30 avril, rapport sous 2 semaines) ; "fortement recommandée" > 36 kWc (HESPUL) ; inspection visuelle mensuelle sur grandes centrales (LONGi). Le monitoring reste le premier détecteur.

**Tronc commun** (UTE C15-712-1 via HESPUL) :
- Modules : décoloration, fissures, snail trails, diodes si points chauds ; ventilation dégagée ; élagage ; nettoyage si besoin.
- Voc par string vs référence de mise en service ; Riso +/terre et −/terre.
- Connecteurs : visuel, câbles non tendus, hors de l'eau.
- Coffrets : joints (IP65 mini DC), **resserrage borniers**, IR, fusibles (continuité/témoin).
- Parafoudres : témoin ; cartouches remplacées après orage. Équipotentialité : visuel.
- Onduleurs : dépoussiérage, filtres, journal de défauts, Riso affiché.
- Étiquetage et signalétique pompiers lisibles ; dossier technique à jour.

**Spécificités par type de site**

| Site | Points en plus |
|---|---|
| Centrale au sol | Fauche (ombrage et risque incendie), clôtures, corrosion et serrage des structures (boulons anti-desserrage en zone venteuse, LONGi), câbles et tranchées, boîtes de jonction de rangées, poste de livraison HTA (habilitation H), trackers, thermographie par drone |
| Toiture | Étanchéité et abergements, chéneaux bouchés, état du bac acier, connecteurs ne reposant pas sur le bac, cheminements et **ligne de vie**, neige ou charges, accès sécurisé |
| Ombrière | Structure et fondations (chocs véhicules), corrosion, évacuation des eaux pluviales, câbles en hauteur, éclairage et IRVE éventuels, accès nacelle |
| Résidentiel | Monitoring, inspection depuis le sol ou par drone, micro-onduleurs ou optimiseurs (alarmes), coffret AC (différentiel, parafoudre), visite tous les 1 à 2 ans (à vérifier, pas de règle) |

**Vérifications électriques réglementaires** (HESPUL) : Code du travail, initiale R4226-14 puis **annuelle** R4226-16 (arrêté 26/12/2011) ; ERP 1er groupe : CCH R123-43, arrêté 25/06/1980 art. EL 19.

## 2. KPI
- **PR** (IEC 61724-1) = `Yf / Yr`, avec `Yf = E_AC / P_c` (kWh/kWc) et `Yr = H_i (kWh/m² plan) / 1 kW/m²`. Typique ~75-85 % (à vérifier).
- **Disponibilité** : en temps ou en énergie (kWh produits / productibles), définition à fixer au contrat.
- **Productible** : PVGIS ou étude ; suivre l'écart réel/attendu et le ratio par string ou onduleur.
- **Contrat type HESPUL** : crédit de pertes 2 % de la production annuelle ; curatif niveau 1 sous J+1 ouvré ; devis niveau 2 sous J+2.

## 3. Sécurité des intervenants

**Habilitation électrique NF C 18-510** (délivrée par l'employeur, art. R4544-10 du Code du travail) :
- **BP photovoltaïque** : non-électriciens (couvreurs…). Pose, manutention, connexion de modules d'une même chaîne par connecteurs débrochables, nettoyage. **Interdit de raccorder la chaîne à une boîte de jonction.**
- **BR photovoltaïque** : "chargé d'intervention générale" PV. Raccordement, maintenance, connexion et sectionnement de conducteurs, essais, mesurages.
- HTA (poste de livraison) : habilitation H spécifique.
- Recyclage : périodicité recommandée par la norme (à vérifier, 3 ans couramment cité).

**Travaux en hauteur** : protection collective d'abord, sinon EPI antichute sur ancrage EN 795 (C = câble, 1 utilisateur par défaut, au-delà CEN/TS 16415 ; D = rail). **Ligne de vie : vérification tous les 12 mois** et après toute chute arrêtée, consignée au registre (pratique et notice ; article de référence à vérifier). EPI antichute : vérification annuelle (à vérifier, arrêté du 19/03/1993). Le champ ne se consigne pas côté modules : travailler hors charge, sectionneurs ouverts.

**Pompiers / coupure d'urgence**
- ERP : avis de la CCS du 05/11/2009 et du 07/02/2013 ; dossier au SDIS avant les travaux.
- Le SDIS exige **au moins une** mesure : coupure DC automatique **au plus près des chaînes**, câbles DC à l'extérieur, onduleurs à l'extérieur près des modules, DC en cheminement coupe-feu, ou DC limité au local onduleur à accès restreint. Cheminement de 90 cm souvent exigé. Coupure pour les secours : UTE §12.4.
- Optimiseurs < 60 V DC à l'arrêt : conformes. Micro-onduleurs : coupure DC non exigée. Logement : coupures AC et DC **hors onduleur** (guide complémentaire 2024).
- Le SDIS considère l'installation **sous tension** tant que la mise en sécurité n'est pas faite.

## 4. Réglementation électrique

**Textes**
- NF C 15-100 (amendée en 2008 pour inclure le PV) renvoie au **guide UTE C15-712-1**, version 3 en vigueur depuis le 01/07/2013, consultable gratuitement sur le site AFNOR.
- **Guide complémentaire** (Hespul, Consuel, SER, Enerplan, INES, CRER…), janvier 2024, v2 : il couvre les bifaciaux, micro-onduleurs et optimiseurs. **Non validé par l'AFNOR**, en attendant la révision du C15-712-1.
- Statut de la partie 7-712 dans la NF C 15-100 révisée : (à vérifier).

**Exigences clés** (UTE C15-712-1 via photovoltaique.info et HESPUL) :
- **Circuit DC en classe II**. Mise à la terre de toutes les masses (cadres, rails, chemins de câbles, coffrets) en peigne vers un conducteur d'équipotentialité, avec rondelles bimétal cuivre/aluminium. Prise de terre unique pour le bâtiment.
- **Protections** : fusibles DC dont le calibre est lié à l'Isc des modules ; parafoudres DC et AC ; différentiel et disjoncteur côté AC ; découplage automatique.
- **Parafoudres** :
  - au niveau de l'onduleur, plus dans un coffret DC près des modules si modules et onduleur sont distants de **plus de 10 m** ;
  - **≤ 50 cm** entre le raccordement du parafoudre sur la polarité et la terre ;
  - choix selon le niveau kéraunique du site ;
  - notion de **longueur critique** : sous cette longueur, pas de parafoudre spécifique (cas des micro-onduleurs, guide complémentaire) ;
  - parafoudres DC conformes NF EN 50539-11.
- **Sectionnement** DC et AC, avec sectionnement **à proximité de chaque onduleur**. Un bornier n'est **pas** un sectionneur. Pour les micro-onduleurs, des connecteurs débrochables IP2X valent sectionnement AC.
- **Chute de tension** : **3 % max, 1 % recommandé**.
- **Connecteurs** de même type et même marque (NF EN 50521).
- **Signalisation et étiquetage** aux organes de coupure, à destination des secours.

**Consuel**
- Attestation de conformité :
  - **bleue** : production sans stockage (Cerfa 15523) ;
  - **violette** : avec stockage (Cerfa 15524) ;
  - jaune / verte : consommation domestique / non domestique.
- Le dossier technique **SC144** accompagne la demande de visa.
- Autoconsommation sans injection : convention CACSI avec Enedis obligatoire. Seuil de dispense du Consuel (< 3 kVA sans batterie selon des sources commerciales, à vérifier).
- S21 depuis le 05/06/2026 : l'attestation Consuel n'est demandée à EDF OA **qu'en cas de contrôle** ou à sa demande.

## 5. Assurances (à vérifier au cas par cas)
- Installateur : RC décennale (PV intégré ou touchant l'étanchéité) + RC pro ; qualification RGE/QualiPV exigée pour l'OA.
- Producteur : déclarer à l'assurance habitation (sinistres Scheuten indemnisés ainsi) ; pro : bris de machine, perte d'exploitation (à vérifier). Un assureur a résilié une centrale pour connecteurs non d'origine (pv-magazine).

## 6. Contrat OA EDF (arrêté S21 du 06/10/2021 modifié)

**Éligibilité et tarifs**
- Pose sur bâtiment, hangar ou ombrière. **P + Q ≤ 100 kWc** depuis le 22/09/2025. Installateur qualifié. Attestation sur l'honneur du producteur.
- **Vente totale** possible **à partir de 9 kWc** seulement. ≤ 9 kWc : vente du surplus uniquement, depuis l'arrêté du 26/03/2025 (en vigueur le 28/03/2025).
- **Modification du 01/06/2026** (demandes de raccordement complètes déposées dès le **05/06/2026**) :
  - **tarif unique 1,1 c€/kWh** de 0 à 100 kWc, plus de dégressivité trimestrielle ;
  - indexation de +2 %/an (1,60 c€/kWh la 20e année) ;
  - **primes à l'investissement supprimées** ;
  - injection au-delà de **1 600 kWh/kWc·an non rémunérée** ;
  - un comptage propre à chaque installation.
- Contrats antérieurs : conditions de leur date de demande (ex. surplus à 4 c€/kWh après mars 2025, à vérifier).
- Durée : **20 ans**, à compter de la mise en service (date d'autorisation d'injection).

**Obligations du producteur**
- **Facturation** : relever les index à la date anniversaire et les saisir sur l'espace producteur EDF OA, qui paie ensuite. Périodicité selon la puissance : annuelle < 36 kWc, semestrielle 36-100 kWc (source secondaire, à vérifier).
- **Remplacement de modules** :
  - sans accord nécessaire si le remplacement est "standard" (même marque, même puissance) ;
  - remplacement ponctuel toléré sans expertise jusqu'à **1 % des modules par an** (arrondi à l'unité supérieure) et **10 % du nombre initial** sur la durée du contrat ;
  - au-delà, accord de la DGEC requis, sinon **résiliation**.
- **Sinistre** : contrat maintenu si la puissance reconstruite varie de ≤ ±10 %. Informer EDF OA.
- **Augmentation de puissance** : nouveau contrat + avenant au contrat initial (déclarer P1 et P2).

## 7. Cas réels de forums (forum-photovoltaique.fr, retours d'utilisateurs non vérifiés)

| # | Symptôme | Cause | Résolution | URL |
|---|---|---|---|---|
| 1 | Connecteur MC4 fondu | Jeu ou mauvais contact mâle/femelle, mélange de marques ou clones, P = R·I² | Remplacer le **couple** de même marque, vérifier les sertissages (panneaux → coffret DC) | https://forum-photovoltaique.fr/viewtopic.php?t=60724 |
| 2 | Tension en baisse sur un string | Diode bypass en court-circuit (perte de ½ à ⅕ de la Voc d'un panneau selon le nombre de diodes) | Voc panneau par panneau, inverser les entrées MPPT pour disculper l'onduleur, remplacer le module (Isc identique à ±2 %) | https://forum-photovoltaique.fr/viewtopic.php?t=22513 ; https://forum-photovoltaique.fr/viewtopic.php?t=62908 |
| 3 | Défaut d'isolement remonté par l'onduleur | Câble abîmé, connecteur mal clipsé ayant pris l'eau, verre fissuré | Relever Riso et tensions sur l'écran de l'onduleur, isoler les strings un par un, vérifier les joints des MC4 | https://forum-photovoltaique.fr/viewtopic.php?t=61177 ; https://forum-photovoltaique.fr/viewtopic.php?t=68796 |
| 4 | Production en baisse d'année en année (onduleur sans transformateur) | PID, potentiel négatif cadre/cellules | Boîtier de repolarisation de nuit. Garantie de performance non déclenchée tant que la perte reste sous le seuil | https://forum-photovoltaique.fr/viewtopic.php?t=31425 ; https://forum-photovoltaique.fr/viewtopic.php?t=26842 |
| 5 | Production 10-12 % sous un voisin de référence | Encrassement | Après nettoyage, +3 % au-dessus du voisin ; gain qui s'estompe vite. Fientes : ~10 kWh/j d'écart rapporté | https://forum-photovoltaique.fr/viewtopic.php?t=33362 |
| 6 | Boîtes de jonction brûlées (Scheuten Multisol) | Boîtes Solexus défectueuses (rappel 2012) | Remplacement des boîtes via Suncycle. Tarif d'achat maintenu si EDF OA est informé | https://forum-photovoltaique.fr/viewtopic.php?t=22428 ; https://pv-tech.org/fire_risk_fiasco_as_dutch_government_warns_about_650000_scheuten_solar_modu |
| 7 | Câble et connexion brûlés sans alarme | Échauffement de connexion | Détecté en maintenance préventive, pièce changée avant l'été (cas HESPUL) | Guide HESPUL ci-dessous |

## Sources
- UTE C15-712-1 : https://www.photovoltaique.info/fr/realiser-une-installation/regles-conception-mise-en-oeuvre/normes-electriques-applicables-aux-systemes-pv/guide-ute-c-15-712-1/
- Guide complémentaire 2024 : https://photovoltaique.info/media/filer_public/40/d2/40d2864e-eac2-478b-8254-44c4451ea517/guide_vfinal.pdf
- HESPUL guide exploitation : https://www.photovoltaique.info/media/filer_public/78/28/78284879-6f40-451b-b141-9d08d44c8c6b/170110_guide_exploitation_pv_hespul_crpv_v1_.pdf
- Incendie : https://www.photovoltaique.info/fr/realiser-une-installation/regles-conception-mise-en-oeuvre/securite-incendie-et-photovoltaique/dispositions-normatives-et-reglementaires/
- S21 2026 : https://www.photovoltaique.info/fr/actualites/detail/arrete-s21-detail-des-modifications-et-nouveau-tarif-unique/
- Changement de panneaux : https://www.photovoltaique.info/fr/exploiter-une-installation/vie-des-contrats/modification-de-linstallation/changement-de-panneaux/
- Habilitation BR PV : https://capeb.fr/www/capeb/media/cantal/document/habilitation-electrique-br-pv-1j.pdf
- Consuel : https://www.monkitsolaire.fr/blog/consuel-et-autoconsommation-n86
