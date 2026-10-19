# Défauts des modules photovoltaïques : diagnostic et prise en charge

Valeur non vérifiée = "(à vérifier)". Réf. principale : IEA PVPS Task 13 (T13-01:2014 failures ; T13-10:2018 IR/EL).

## 1. Modules du parc (données fiche)

| Module | Techno | Voc STC | Isc STC | β Voc | α Isc | γ Pmax | Diodes | Garantie produit / perf. |
|---|---|---|---|---|---|---|---|---|
| JA Solar JAM72S30-550/MR | PERC mono, 144 demi-cellules, verre/backsheet | 49,90 V | 14,00 A | −0,275 %/°C | +0,045 %/°C | −0,350 %/°C | 3 (IP68) | 12 ans / 25 ans : ≤2 % an 1, puis ≤0,55 %/an, ≥84,8 % à 25 ans |
| Trina Vertex S+ 440 (NEG9R.28 / NEG9RC.27) | N-type TOPCon bi-verre | 52,2 V (revendeur, à vérifier) | 10,67 A (revendeur, à vérifier) | −0,24 %/°C | +0,04 %/°C | −0,30 %/°C | 3 (à vérifier) | 25 ans / 30 ans, dégradation max 0,4 %/an (communiqué Trina) ; 1 % an 1 (à vérifier) |
| LONGi Hi-MO 5m LR5-72HPH-520M | PERC mono, 144 demi-cellules | (à vérifier) ~49 V gamme | (à vérifier) ~13,6 A gamme | ≈ −0,27 %/°C (gamme, à vérifier) | ≈ +0,05 %/°C (à vérifier) | −0,34 à −0,37 %/°C selon puissance (à vérifier) | 3 | 12 ans / 25 ans (paliers à vérifier) |
| Q CELLS Q.PEAK DUO L-G6 400 | PERC Q.ANTUM, demi-cellules | (à vérifier) | (à vérifier) | −0,27 %/K | +0,04 %/K | −0,36 %/K | 3 (à vérifier) | 12 ans / 25 ans ; courbe Q.PEAK DUO : ≥98 % an 1, −0,54 %/an max, ≥85 % à 25 ans (à vérifier sur fiche L-G6) |
| DualSun FLASH 400 Shingle Black | Mono shingle | 49,50 V | 10,12 A | −0,27 %/K | +0,04 %/K | −0,34 %/K | (à vérifier) | Doc. garantie 03/2023 : Shingle 30 ans si garantie activée sur my.dualsun.com, 25 ans sinon (à vérifier) |

JA : NOCT 45±2 °C, fusible série max 25 A, 1000/1500 V DC.

## 2. Règles de lecture rapide

- Module demi-cellules à 3 diodes : chaque diode protège 1/3 du module (les deux moitiés en parallèle). **1 diode passante ou en court-circuit = −1/3 de la Voc du module** (≈ −16,6 V sur JA 550, ≈ −17,4 V sur Trina 440).
- Cellule seule en court-circuit : perte de tension ≈ 1/72 à 1/48 de la Voc, quasi invisible au voltmètre.
- Selon IEA PVPS : surface de cellule inactive >8 % → perte de puissance ~linéaire ; ≥50 % de cellule inactive → la diode s'active et le module perd 1/3 de sa puissance.
- IR : moins de 10 % de modules avec anomalie thermique = dispersion normale ; plus de 10 % = rechercher une cause qualité, conception ou exploitation (IEA T13-10).

## 3. Fiches défauts

### 3.1 Hotspot (point chaud cellule)
- **Symptôme** : brunissement local, marque de brûlure au dos, baisse de production d'un string.
- **Signature IR** : 1 cellule ou une partie de cellule nettement plus chaude. IEA montre des cas >20 K. Classes de ΔT : voir `champ-pv-mesures.md` (à vérifier).
- **I-V** : marche ou bosse si la diode s'active ; FF dégradé.
- **Causes** : cellule fissurée, shunt local, mauvais tri des cellules, ombrage local (fiente, feuille), verre cassé (grêle).
- **Criticité** : moyenne à élevée. Risque de brûlure du backsheet et d'incendie si la diode est défaillante.
- **Action** : nettoyer et supprimer l'ombrage, refaire l'IR. Si le point chaud persiste sans cause externe → EL + I-V module → remplacement.
- **Garantie** : oui si défaut de fabrication prouvé (cellule ou soudure). Non si ombrage, fientes, casse mécanique ou grêle (force majeure exclue, ex. JA).

### 3.2 Diode bypass défaillante
- **Deux modes** :
  - **Court-circuit** (cas le plus fréquent) : le tiers du module est shunté en permanence.
  - **Circuit ouvert** : plus de protection contre la polarisation inverse, donc risque de feu.
- **Signature IR** : 1/3 du module uniformément plus chaud (sous-string en court-circuit qui ne produit pas). Boîte de jonction chaude sur la diode active.
- **I-V string** : marche d'escalier. **Voc du string abaissée d'environ Voc_module/3**. Pmax module −33 %.
- **Mesure terrain** : Voc string < valeur attendue d'environ 1/3 de module. Isoler le module en mesurant la Voc module par module : le module fautif est à environ 2/3 de sa Voc.
- **Diode ouverte** : la Voc reste normale. On ne la détecte qu'en ombrant volontairement 1 sous-string ou au testeur de diode, module déconnecté. IEA cite une centrale de 1272 modules où 47 % des modules avaient au moins une diode défectueuse et 3 % des marques de brûlure, toujours sur une diode ouverte.
- **Causes** : diodes Schottky sensibles aux décharges électrostatiques et à la foudre, surchauffe chronique liée à un ombrage permanent.
- **Criticité** : élevée (sécurité incendie si ouverte).
- **Action** : remplacer le module. Le remplacement de diode n'est possible que si la boîte de jonction le permet et que le fabricant l'autorise, sinon on perd la garantie.
- **Garantie** : en général oui pendant la période produit (12 ans JA, LONGi, Q CELLS ; 25 ans Trina), sauf foudre ou surtension.

### 3.3 PID (Potential Induced Degradation)
- **Symptôme** : perte de production qui s'aggrave d'année en année et touche surtout les modules proches du **pôle négatif** du string (onduleur sans transformateur, potentiel négatif cellules/cadre).
- **Signature** :
  - **IR au soleil** : cellules plus chaudes près du cadre bas, motif en damier ("patchwork").
  - **EL** : cellules sombres.
  - **IR de nuit** (courant injecté) : cellules affectées plus froides.
  - Puissance qui décroît le long du string : exemple IEA de 188 Wp côté − à 220 Wp côté + pour des modules de 225 Wp.
- **I-V** : FF et Rshunt effondrés ; Voc en baisse à faible éclairement.
- **Facteurs** : tension système, humidité/rosée, sel, température. Perte jusqu'à ~100 % en quelques mois (IEA).
- **Criticité** : élevée (économique), sans risque sécurité direct.
- **Action** :
  - Confirmer par EL ou par la Pmax module par module.
  - Régénération : tension inverse la nuit (boîtier anti-PID / "PID box" ou "offset box"), fonction anti-PID de l'onduleur, ou mise à la terre du pôle − si l'onduleur l'autorise.
  - IEA : récupération en heures (tension inverse + chaleur), en mois sans accélération ; PID formé à 85 °C peu réversible.
- **Garantie** : couverte par la garantie de performance seulement si la perte dépasse la courbe garantie. Une perte de quelques % reste souvent sous le seuil (retour forum). Les modules récents sont certifiés "PID-resistant" (IEC TS 62804).

### 3.4 LID / LeTID
- **LID** : perte initiale (bore-oxygène, p-type), non classée défaut si dans la tolérance (IEA) ; incluse dans la perte "an 1" garantie (JA ≤2 %).
- **LeTID** : lumière + chaleur (>50 °C), PERC p-type, sur plusieurs années puis régénération partielle ; jusqu'à ~6 % (Kiwa), 2,3-2,5 % en test IEC TS 63342 ; négligeable sur TOPCon (étude 2026). Concerne JA, LONGi, Q CELLS ; peu Trina.
- **Signature** : baisse homogène, IR normale, EL plus sombre homogène. **Action** : suivi PR annuel, flash d'échantillon. **Garantie** : performance seulement si sous la courbe (tolérance incluse).

### 3.5 Snail trails (traces d'escargot)
- **Symptôme** : lignes grises ou noires sur les doigts d'argent, le long des bords de cellule et des microfissures invisibles. Elles apparaissent 3 mois à 1 an après la pose.
- **Cause** : nanoparticules d'argent (composés S, P, C) dans l'EVA. Le rôle de l'EVA et du backsheet est probable.
- **Impact** : IEA ne connaît **aucun cas où la décoloration seule cause une perte mesurable**. En revanche elle **révèle des microfissures**, qui peuvent coûter de la puissance.
- **Action** : EL pour quantifier les fissures, puis I-V. Surveillance.
- **Garantie** : l'esthétique est exclue (JA exclut les changements d'aspect). Seule une perte de puissance prouvée est couverte.

### 3.6 Microfissures
- **Causes** : transport, manutention, marche sur les modules, charge neige ou vent, grêle, cycles thermiques.
- **Signature** :
  - **EL** : lignes sombres, zones mortes.
  - **IR** : cellule partiellement chaude si une zone est isolée.
  - **I-V** : quasi rien tant que les zones restent connectées.
- **Évolution** : les fissures dendritiques sont les plus pénalisantes (IEA).
- **Action** : EL de réception, interdiction de marcher sur les modules, suivi.
- **Garantie** : difficile à obtenir. Si la casse est mécanique après livraison, c'est un sinistre ou la responsabilité du poseur ou du transporteur. Faire l'EL à la réception pour garder la preuve.

### 3.7 Délamination
- Bulles, décollement EVA, humidité, corrosion des rubans ; Riso bas possible. Critique si bords/boîte atteints (perte classe II). **Action** : Riso module, remplacement. **Garantie** : oui (matériau).

### 3.8 Jaunissement EVA
- Dégradation UV/thermique, Isc en baisse lente. **Action** : comparer l'Isc à un module sain, flasher. **Garantie** : aspect exclu ; couvert seulement sous la courbe de puissance.

### 3.9 Backsheet fissuré
- **Polymères à risque** : polyamide **"AAA"** (fissures traversantes dès 4 ans selon NIST ; >12 GW revendiqués par DuPont, source concurrente). PET aussi touché (ZSW).
- **Signature** : fissures le long des busbars ; **défaut Riso le matin ou par temps humide** ; arcs possibles.
- **Criticité** : élevée. **Action** : Riso string puis module, remplacement. **Garantie** : réclamation produit (matériau). Bi-verre (Trina) non concerné.

### 3.10 Boîte de jonction brûlée / défaillante
- **Symptôme** : boîte noircie ou déformée, odeur, couvercle décollé, string à 0 A ou Voc réduite.
- **Signature IR** : boîte ou bornier très chaud (IEA montre une borne surchauffée).
- **Causes** : soudure ou serrage défaillant, corrosion des contacts, diode en surchauffe, infiltration d'eau.
- **Cas historique** : boîtes Solexus des Scheuten Multisol P6 (2009-2010), ~650 000 modules, incendies FR/IT, remplacement via Suncycle.
- **Criticité** : critique (incendie).
- **Action** : consigner le string, remplacer le module, vérifier les modules voisins à l'IR.
- **Garantie** : oui (défaut de fabrication), sauf intervention non autorisée dans la boîte.

### 3.11 Connecteurs MC4 incompatibles ou mal sertis
- **Symptôme** : connecteur fondu ou noirci, string intermittent, défaut d'isolement (joint abîmé, connecteur posé dans l'eau ou sur le bac acier).
- **Signature IR** : connecteur nettement plus chaud que les autres du même string (P = R·I² : la perte croît avec le carré du courant).
- **Causes** :
  - **Mélange de marques mâle/femelle** : diamètres de contact différents. Stäubli ne garantit pas les accouplements croisés.
  - Sertissage à la pince inadaptée, connecteur non enclenché jusqu'au clic, câble en traction.
- **Règle** : le guide UTE C15-712-1 (relayé par HESPUL) impose des connecteurs **de même type et même marque** que ceux des modules et proscrit les "compatibilités annoncées" entre marques. Connecteurs conformes NF EN 50521 (IP55 mini, −40/+85 °C selon UTE).
- **Criticité** : critique (première cause terrain de départ de feu côté DC, à vérifier statistiquement).
- **Action** : remplacer **le couple** (mâle et femelle) par la même marque que le connecteur du module, sertir à l'outil du fabricant, faire un test de traction, refaire l'IR sous charge.
- **Garantie** : connecteur d'usine garanti avec le module (JA) ; un accouplement de marques différentes engage l'installateur (un assureur a résilié une centrale de 2 MW pour connecteurs non d'origine, pv-magazine).

### 3.12 Encrassement / salissure
- **Ordres de grandeur** : ~5 % typique (paramètre NREL), 0,01-0,5 %/jour selon site (à vérifier) ; plus fort à faible inclinaison.
- **Fientes** = ombrage partiel localisé : diode activée, hotspot, perte disproportionnée.
- **Angle** : >15° et site peu poussiéreux, la pluie suffit ; pose horizontale = nettoyage obligatoire (+30 % de Pmax après nettoyage, HESPUL). Bande de saleté en bas de cadre typique.
- **Signature** : Isc uniforme en baisse vs string témoin. **Garantie** : non (contamination exclue). Nettoyage : voir `champ-pv-mesures.md`.

### 3.13 Ombrage
- **Types** :
  - **Local** : cheminée, antenne, paratonnerre, poteau, végétation.
  - **Rangée voisine** : centrale au sol en hiver.
- **Signature** :
  - **IR** : cellules chaudes qui suivent la forme de l'ombre.
  - **I-V** : marches multiples. Courbe de production journalière "entaillée" à heure fixe.
- **Action** : élaguer (recommandation UTE C15-712-1 relayée par HESPUL), déplacer des modules, optimiseurs ou micro-onduleurs.
- **Garantie** : non.

## 4. Tableau de tri rapide

| Observation | Hypothèse n°1 | Vérification |
|---|---|---|
| Voc string −⅓ de module | Diode en court-circuit / sous-string ouvert | Voc module par module, IR |
| Voc string −1 module entier | Module court-circuité ou erreur de câblage | Continuité, comptage des modules |
| Voc OK, Isc basse sur tout le string | Salissure, EVA jaunie, irradiance | Nettoyer, comparer à un string témoin |
| Voc OK, Isc basse sur un seul module | Ombrage, fissures, cellule morte | IR, EL |
| Pertes croissantes côté − | PID | EL, Pmax selon la position |
| Défaut Riso le matin ou par pluie | Connecteur dans l'eau, backsheet fissuré, câble abîmé | Riso string puis module |
| Connecteur chaud à l'IR | MC4 mixte ou mal serti | Remplacer le couple |

## Sources
- IEA PVPS T13-01:2014 : https://iea-pvps.org/wp-content/uploads/2020/01/IEA-PVPS_T13-01_2014_Review_of_Failures_of_Photovoltaic_Modules_Final.pdf
- IEA PVPS T13-10:2018 IR/EL : https://iea-pvps.org/wp-content/uploads/2020/01/Review_on_IR_and_EL_Imaging_for_PV_Field_Applications_by_Task_13.pdf
- Fiche JA JAM72S30-MR : https://solarics.de/cdn/shop/files/01-000841_JAM72S30_530-555_MR_MC4-400Global_EN_20220118A_2278-1134-35-33-17.pdf
- Garantie JA : https://solar-distribution.baywa-re.pl/out/media/46_-_JAM66S30_EN_JA_Solar_limited_warranty.pdf
- Trina Vertex S+ : https://www.trinasolar.com/en-glb/20220413-0025/
- Q CELLS (courbe G6+) : https://solarproof.com.au/datasheets/panel_datasheet_Q_CELLS_Data_sheet_Q.PEAK_DUO-G6+_345-355_2020-02_Rev01_EN.pdf
- DualSun FLASH 400 : https://dualsun.com/wp-content/uploads/2023/05/dualsun-en-datasheet-flash-400-shingle-black-1.pdf ; garanties : https://shop.solexis.ch/fr/documents/file/pv/dualsun/ga_fr_dualsun_202303.pdf
- HESPUL guide exploitation : https://www.photovoltaique.info/media/filer_public/78/28/78284879-6f40-451b-b141-9d08d44c8c6b/170110_guide_exploitation_pv_hespul_crpv_v1_.pdf
- LeTID TOPCon : https://www.pv-magazine.com/2026/09/01/new-research-confirms-negligible-letid-degradation-in-topcon-solar-cells/
- Backsheets PA : https://nrel.gov/docs/fy21osti/79155.pdf
- Connecteurs : https://www.pv-magazine.com/2016/06/15/burnt-out-incompatible-connectors_100024992
