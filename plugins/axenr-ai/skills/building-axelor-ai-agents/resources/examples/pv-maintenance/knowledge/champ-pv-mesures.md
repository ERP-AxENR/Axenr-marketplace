# Mesures sur champ PV : méthodes, seuils, interprétation

Valeur non vérifiée = "(à vérifier)". IEC 62446-1/-3 non consultées directement : seuils issus de sources secondaires.

## 0. Préalables sécurité
- Champ sous tension dès qu'il y a de la lumière. Ouvrir le sectionneur DC **avant** de toucher un connecteur ; **jamais de MC4 déconnecté en charge** (arc DC). Habilitation BR PV, EPI isolants, appareil CAT III 1000/1500 V DC.
- Relever irradiance dans le plan et température module (sonde au dos) **au même instant** que la mesure.

## 1. Voc / Isc par string

**Formules (méthode simplifiée ; méthode rigoureuse : IEC 60891)**
- Température cellule estimée : `Tc ≈ Tamb + (NOCT − 20) / 800 × G` (G en W/m²). Une sonde au dos du module est plus fiable.
- `Voc_attendu = N_modules × Voc_STC × [1 + β × (Tc − 25)]`, avec β en %/°C divisé par 100. La Voc dépend peu de G (variation logarithmique) : on peut la mesurer dès que G > ~200 W/m² (à vérifier).
- `Isc_attendu = Isc_STC × (G / 1000) × [1 + α × (Tc − 25)]`. L'Isc est proportionnelle à G : mesurer par **ciel stable**, G > ~700 W/m² conseillé (à vérifier).

**Exemple JA JAM72S30-550/MR** (Voc 49,90 V ; Isc 14,00 A ; β −0,275 %/°C ; α +0,045 %/°C), string de 18 modules, G = 800 W/m², Tc = 45 °C :
- Voc = 18 × 49,90 × (1 − 0,00275 × 20) = 18 × 47,16 = **848,8 V**
- Isc = 14,00 × 0,8 × (1 + 0,00045 × 20) = **11,30 A**

**Interprétation**
- **Comparer les strings entre eux**, à mêmes conditions (même orientation, quelques minutes d'écart) : c'est la méthode la plus robuste ("méthode de la comparaison", guide HESPUL).
- Écart Voc ≈ 1/3 de Voc module : diode en court-circuit.
- Écart ≈ 1 Voc module : module court-circuité ou erreur de comptage.
- Voc ≈ 0 V : fusible, connecteur ou câble coupé.
- Polarité inversée : erreur de câblage. **Danger** si des strings sont en parallèle.
- Isc basse sur un string seul : salissure, ombrage ou dégradation. Isc basse sur tous les strings : irradiance mal mesurée.
- Tolérance d'acceptation IEC 62446-1 pour l'écart Voc et Isc mesuré/attendu : (à vérifier sur le texte de la norme).
- **À la réception** : mesurer et archiver la Voc de chaque string, qui sert de référence (HESPUL).

## 2. Résistance d'isolement (Riso)

**Méthodes IEC 62446-1** (description de sources secondaires) :
- **Méthode 1** : court-circuiter + et − du string par un dispositif dimensionné pour l'Isc, puis mesurer entre ce point et la terre.
- **Méthode 2** : mesurer + / terre, puis − / terre, sans court-circuit (recommandée par HESPUL : "Riso +/terre et −/terre").

**Tension d'essai et seuil minimal** (synthèse Fluke de l'IEC 62446-1) :

| Tension système du champ | Tension d'essai | Riso minimale |
|---|---|---|
| < 120 V | (à vérifier, 250 V souvent cité) | (à vérifier) |
| 120 – 500 V | 500 V DC | 1 MΩ |
| 500 – 1000 V | 1000 V DC | 1 MΩ |
| > 1000 V | 1500 V DC | 1 MΩ |

- **Module seul** : Riso × surface ≥ **40 MΩ·m²** (≥400 MΩ si la surface est < 0,1 m²). Critère du manuel O&M LONGi, issu des essais de qualification modules.
- **Durée** : lire la valeur à 15 s et à 60 s (LONGi) ; maintien 1 min selon Solis.
- **Seuil de l'onduleur** : chaque onduleur mesure le Riso avant de démarrer, avec son propre seuil (voir la notice). Un forum cite des onduleurs "qui tolèrent mal < ~10 MΩ", valeur non normative.
- **Recherche de défaut** :
  1. Isoler les strings un par un (repérer le string fautif sur l'écran de l'onduleur ou par mesure + / terre et − / terre).
  2. Mesurer "une zone après l'autre" avec un plan de câblage (HESPUL).
  3. Suspects habituels : MC4 dans l'eau ou sur le bac acier, câble pincé par un rail, backsheet fissuré, boîte de jonction.
  4. Défaut seulement le matin ou par pluie : humidité (connecteur, backsheet).
- Jamais de mégohmmètre sur un circuit raccordé à l'onduleur ; décharger après l'essai.

## 3. Courbe I-V

- **Facteur de forme** : `FF = (Vmp × Imp) / (Voc × Isc)`. JA 550 : 41,96 × 13,11 / (49,90 × 14,00) = **0,787**. Calculer le FF de référence à partir de la fiche de chaque module.
- Mesurer avec un traceur (IEC 62446-1, catégorie 2) par ciel clair et stable (G > ~700 W/m², à vérifier), puis ramener aux STC par le logiciel (IEC 60891).

| Déformation | Cause probable |
|---|---|
| Marches / escalier | Ombrage partiel, mismatch, diode bypass active, cellule fissurée |
| Marche à −1/3 de Voc module | Diode en court-circuit / sous-string HS |
| Pente forte près de l'Isc (Rshunt bas) | PID, shunts, cellules fissurées |
| Pente faible près de la Voc (Rs élevée) | Connecteur oxydé ou mal serti, câble sous-dimensionné, corrosion des rubans |
| Isc uniformément basse | Salissure, EVA jaunie, irradiance surestimée |
| Voc basse | Température élevée, diode, PID avancé, module manquant |
| Arrondi général, FF bas | Vieillissement, LeTID, mismatch global |

## 4. Thermographie IR (IEC TS 62446-3)

**Conditions** (IEA PVPS T13-10, qui renvoie à 62446-3) :
- Irradiance > **600 W/m²** dans le plan des modules, stable : pas de nuages, vent faible, température ambiante stable.
- Système **en fonctionnement** (au MPP) : un string ouvert ne chauffe pas comme un string en charge.
- ΔT naturel jusqu'à **8 K** dans un module sain. Choisir une météo qui donne un ΔT actif/inactif > 2,5 K.
- Échelle de couleur conseillée : span de 20 à 30 K (module de 15 % de rendement à 1000 W/m²).
- **Qualification de l'opérateur** : ISO 9712 niveau 2 citée par IEC TS 62446-3. Plan de calepinage obligatoire pour localiser les modules. Ne pas confondre une réflexion avec un hotspot : changer l'angle de vue.

**Seuils de criticité ΔT** (pratique terrain courante, classes "CoA" de 62446-3 non vérifiées) :

| ΔT vs cellule de référence | Action (à vérifier) |
|---|---|
| < 10 K | Surveiller |
| 10 – 20 K | Planifier une intervention |
| > 20 K | Intervention rapide (IEA illustre des "hot spots > 20 K") |

**Motifs typiques**
- 1 cellule chaude : hotspot.
- 1/3 du module chaud : sous-string bypassé.
- Module entier chaud : module déconnecté (en circuit ouvert).
- String entier chaud : string déconnecté.
- Cellules chaudes en damier près du cadre bas, côté − : PID.
- Connecteur ou borne chaude : MC4 ou serrage.
- Coffret DC : fusible ou cosse.

## 5. Électroluminescence (EL)

- **Principe** : injecter un courant DC (jusqu'à l'Isc) dans le module ou le string, alimentation capable de fournir environ la Voc. Caméra Si ou InGaAs, **de nuit** ou sous bâche. Les conditions sont souvent réunies environ 1 h après le coucher du soleil (IEA).
- **Révèle** : microfissures, zones mortes, rubans coupés, PID (cellules sombres). Classification : VDE SPEC 90031.
- **Usage** : réception (preuve pour réclamation), après grêle, confirmation PID.

## 6. Nettoyage des modules

D'après le manuel O&M LONGi V2.0, référence la plus précise trouvée (consulter le manuel de chaque marque) :
- **Eau** : eau de ville acceptée, sinon pH 6-8, chlorures ≤1000 mg/L, dureté ≤450 mg/L, matières dissoutes ≤1000 mg/L, conductivité ≤3000 µS/cm. Une eau très minéralisée laisse des dépôts. **Eau déminéralisée ou osmosée recommandée** en pratique (absence de traces).
- **Pression** au niveau du module : **≤ 0,7 MPa (7 bar)**. Un nettoyeur haute pression standard est donc proscrit.
- Écart de température eau/module ≤ 10 °C. Pas de nettoyage si l'ambiante est < 5 °C. Pas d'eau chaude sur la neige ou le givre.
- **Moment** : tôt le matin, le soir ou par temps couvert (G ≤ 200 W/m²), idéalement onduleur à l'arrêt, pour éviter le choc thermique et l'ombre portée de l'opérateur.
- **Produits interdits** : abrasifs, solvants, acides et bases, vapeur. Le détergent n'est admis que si l'eau seule ne suffit pas, avec rinçage. Brosse douce (nylon 0,06-0,1 mm), éponge non abrasive. **Ne jamais marcher sur les modules.** Garder les connecteurs secs. Ne pas nettoyer un module cassé.
- **Fréquence** :
  - Selon LONGi (grandes centrales) : 40-50 j en zone pluvieuse, 20-30 j en zone sèche ; face arrière des bifaciaux tous les 6 mois.
  - HESPUL : observer l'encrassement pendant 2 ans avant de fixer une périodicité. Au-delà de 15° d'inclinaison et en site peu poussiéreux, la pluie suffit.
- **Garantie** : JA conditionne sa garantie à une installation, une utilisation et un entretien conformes aux manuels d'installation et de maintenance. Un nettoyage non conforme (haute pression, abrasif, chimique) **expose au refus de garantie**. Le fabricant ne couvre pas la "contamination".

## 7. Garanties modules et réclamation

- **Garantie produit** : défauts matériaux et fabrication (délamination, boîte de jonction, diode, backsheet). Elle exclut l'aspect et l'usure.
- **Garantie de performance** : puissance minimale dans le temps (linéaire). Puissance garantie à l'année n : `P_min(n) = Pnom × [1 − d1 − d × (n − 1)]`.

| Module | Produit | Performance |
|---|---|---|
| JA JAM72S30 | 12 ans | d1 ≤2 %, d ≤0,55 %/an, ≥84,8 % à 25 ans |
| Trina Vertex S+ | 25 ans | 30 ans, ≤0,4 %/an (d1 à vérifier) |
| LONGi Hi-MO 5m | 12 ans | 25 ans (paliers à vérifier) |
| Q CELLS L-G6 | 12 ans | 25 ans ; courbe Q.PEAK DUO 98 % / 0,54 % / 85 % (à vérifier L-G6) |
| DualSun FLASH Shingle | 25 ans (30 si activée) | 25 ans (à vérifier) |

**Exemple** : JA 550 W en année 8 → P_min = 550 × (1 − 0,02 − 0,0055 × 7) = 550 × 0,9415 = **517,8 W** à STC. La tolérance positive de plaque n'est pas comptée (Pnom = valeur plaque).

**Procédure de réclamation** (garantie JA 2026, pratique similaire chez les autres fabricants) :
1. Réclamation **écrite** au fabricant ou au distributeur, **pendant** la période de garantie.
2. **Charge de la preuve sur le client** : démontrer que la seule cause est un défaut couvert.
3. Pièces à fournir :
   - numéros de série lisibles (refus si plaque altérée) ;
   - facture et preuve de propriété ;
   - date de mise en service ;
   - photos, I-V ramenées aux STC, IR, EL ;
   - historique de monitoring ;
   - preuve d'une pose par un installateur qualifié et conforme au manuel.
4. **Exclusions fréquentes** : modules déplacés ou réinstallés ailleurs, association non autorisée avec des produits tiers (ex. connecteurs d'une autre marque), conception non conforme (IEC 62548), environnement extrême (sel, ammoniac, sable), force majeure (foudre, grêle).
5. En cas de **litige technique** : laboratoire tiers indépendant désigné en commun (accrédité). Le labo annonce l'incertitude de son banc de mesure, qui est intégrée à la conclusion.
6. **Flash test** : mesure de la Pmax aux STC (IEC 60904 / IEC 61215) en laboratoire ou en camion-laboratoire mobile. Calcul : `dégradation = (Pnom − Pmesurée moyenne) / Pnom`, à comparer à la courbe garantie. Incertitude typique de quelques % (à vérifier selon le labo).
7. **Réparation** : remplacement ou réparation au choix du fabricant. Transport souvent avancé par le client, remboursé si la réclamation est fondée (JA). La main-d'œuvre de dépose et repose n'est généralement pas couverte (à vérifier selon le contrat).

## 8. Calcul simple d'une perte de production

`E_perdue (kWh) = P_indisponible (kWc) × productible spécifique (kWh/kWc/j) × nb jours`

- **String arrêté** : 18 × 550 W = 9,9 kWc. En juin, ~5 kWh/kWc/j (à adapter au site, cf. PVGIS) × 10 jours → 9,9 × 5 × 10 = **495 kWh**.
- **Diode en court-circuit** : −1/3 de module = 0,183 kWc. Avec un productible de 1200 kWh/kWc/an (à adapter) → **≈ 220 kWh/an**, à valoriser au tarif OA ou au prix de l'électricité évitée.
- **Par le PR** : `E_perdue = (PR_attendu − PR_mesuré) × H_i (kWh/m² dans le plan) × P_c (kWc)`.

## Sources
- IEA PVPS T13-10:2018 (IR/EL) : https://iea-pvps.org/wp-content/uploads/2020/01/Review_on_IR_and_EL_Imaging_for_PV_Field_Applications_by_Task_13.pdf
- Fluke, IRT et IEC 62446-1 : https://www.fluke.com/en/learn/blog/renewable-energy/insulation-resistance-testing-in-solar
- LONGi Maintenance Manual V2.0 : https://static.longi.com/LON_Gi_Maintenance_Manual_V2_0_EN_43815b2263.pdf
- HESPUL/CRPV guide exploitation (2017) : https://www.photovoltaique.info/media/filer_public/78/28/78284879-6f40-451b-b141-9d08d44c8c6b/170110_guide_exploitation_pv_hespul_crpv_v1_.pdf
- Garantie JA 2026 : https://fvcomponentes.com/wp-content/uploads/2026/05/Warranty_Manual_EN.pdf
- Fiche JA JAM72S30-MR : https://solarics.de/cdn/shop/files/01-000841_JAM72S30_530-555_MR_MC4-400Global_EN_20220118A_2278-1134-35-33-17.pdf
