# Huawei FusionSolar : procédures terrain

Sources : manuels Huawei (2022-2026), politique de garantie résidentielle (Issue 04, 2025). Points non confirmés : **(à vérifier)**.

## 1. Mesure de résistance d'isolement (alarmes 2062, 2051)

### Avant raccordement (manuels 100KTL-M2 Issue 27 et 20-40KTL-M3 Issue 28)
1. Multimètre DC (calibre ≥ 1100 V) entre + et − : valeur négative = polarité inversée ; U > 1100 V = **ne pas raccorder**.
2. Au mégohmmètre, mesurer **PV+ / terre** puis **PV− / terre** pour chaque string (avec optimiseurs : relier + et − au câble de dérivation, puis mesurer câble/terre). Tension d'essai **1500 V DC maximum**.
3. Critère Huawei : **≥ 1 MΩ = normal** ; **< 1 MΩ** = contrôler l'isolement du câble ou du string (rallonge, puis chaque optimiseur et module).
- Note Huawei 2018 (anciennes gammes, alarme 313) : seuil onduleur 100 kΩ, ≥ 400 kΩ acceptable au mégohmmètre 1000 V. Ne pas transposer aux gammes M1/M2/M3/L1.
- Pour un dossier de garantie, Huawei demande des mesures **+/terre** et **−/terre**. La mesure +/− est inutile (forum-photovoltaique t=72180).

### Humidité, défaut fugitif
- Un défaut d'isolement peut **disparaître puis revenir** (rosée du matin) : mesurer **dès l'apparition**, tôt le matin, avant séchage (Huawei, 2018).
- Causes typiques : vis traversant un module, câble pincé sur rail, jonctions vieillies, eau dans une boîte de jonction ou un sectionneur DC, câble AC abîmé.
- Seuil réglable dans l'app, SmartLogger ou NMS (« Insulation resistance protection threshold ») **uniquement** si l'impédance n'est basse que par temps humide, après contrôle. L'AR Huawei propose aussi de passer temporairement le seuil au minimum et de redémarrer pour diagnostiquer.

### Localisation par l'onduleur, string par string (annexes « Locating Insulation Resistance Faults »)
1. Lire dans l'app, détail de l'alarme 2062 : résistance (MΩ) et **position probable %** (0 % = PV−, 100 % = PV+). Position ≈ nb de modules × % (exemple : 14 modules × 34 % = module 4 ou 5), précision ±1 module. 50KTL-M3 : niveau MPPT seulement. Sans court-circuit franc (R > 0,001 MΩ) : pas de %, contrôler chaque module.
2. Si « Conditions not met » (ensoleillement ou tension trop forts) : AC connecté, arrêt par l'app (Maintenance > Inverter ON/OFF), DC SWITCH OFF, batterie et auxiliaire coupés.
3. Raccorder **un seul string**, DC ON, relancer l'onduleur. Pas de 2062 après 1 min : string sain, passer au suivant. 2062 présent : aller au point 4.
4. Contrôler connecteurs et câbles autour de la position calculée. Si rien n'est visible : retirer le module suspect et son optimiseur, ponter avec une rallonge MC4 et retester.
5. Isoler module ou optimiseur : brancher l'optimiseur sans le module. Alarme absente : module défaillant. Alarme présente : optimiseur défaillant.
- Limite : **2 défauts ou plus sur un même string** rendent la méthode inopérante. Contrôler alors module par module.

## 2. Smart I-V Curve Diagnosis
- Fonction C&I (100KTL-M2 : scan I-V et diagnostic de santé des strings ; 50KTL-M3 : voir *SmartPVMS Smart I-V Curve Diagnosis User Manual*).
- **Licence** requise (scénario SmartLogger3000), stockée dans l'onduleur et liée à son SN. Fin de validité : alarme 2066.
- Conditions recommandées (manuel NetEco) : ensoleillement **> 600 W/m²** (sinon le scan peut échouer sur certains strings), modules d'un même sous-champ également propres, plage **11 h - 13 h** pour éviter les ombres.
- Lancement (NetEco) : Maintenance > Smart I-V Curve Diagnosis > Start Scanning. Chemin SmartLogger3000 ou FusionSolar **(à vérifier)**.

## 3. Remplacement d'un ventilateur
Déclencheur : **2086** (Cause ID = n° du ventilateur) toujours présente 15 min après nettoyage. 2087 (ventilateur interne) : remplacement de l'appareil via le support.
- Prévention : tous les 6-12 mois, nettoyer les grilles et écouter les bruits anormaux (manuel 100KTL-M2).
- **50KTL-M3** : onduleur hors tension, outils isolés, EPI. (1) Dévisser la platine ventilateurs et la pivoter à l'horizontale. (2) Couper le collier, défaire le connecteur, retirer le ventilateur. (3) Remonter dans l'ordre inverse. Brider le câble en laissant **80 mm** côté connecteur.
- **100KTL-M2** : dévisser et tirer le tiroir à l'affleurement, couper les colliers, débrancher, sortir le tiroir, remplacer le FAN 1/2/3, brider selon le repère, rentrer, rebrancher selon les étiquettes, revisser. Si le tiroir coince, le soulever légèrement.

## 4. Mise à jour firmware
- **Locale (app FusionSolar)** : Moi > Mise en service de l'appareil > connexion au WLAN de l'onduleur ou du dongle (QR code de l'étiquette) > Maintenance > Mise à niveau de l'appareil > choisir le paquet (téléchargé sur support.huawei.com). L'app affiche la comparaison des versions. Faire la mise à jour **de jour, DC présent**.
- **À distance (SmartPVMS)** : Plants > Device > Update Management > Software Packages > Add (téléverser) > créer une tâche dans Device Upgrade > suivre la progression.
- **SmartLogger** : app > scan du QR WLAN du SmartLogger > Maintenance > Upgrade (guide Huawei de mise en service). Interface WebUI SmartLogger3000 **(à vérifier)**.
- **Optimiseurs** : mise à jour **MBUS en SPC330 ou plus** par bon ensoleillement. Corrige les optimiseurs hors ligne par intermittence et l'état « loader » (2065-7).
- **LUNA2000** : environ 30 min (activation différée : 4 h après déconnexion de l'app). En cas d'échec (2065), vérifier le câblage et recommencer.
- Garantie : les batteries non connectées à FusionSolar perdent la couverture des dommages cellules dus à l'absence de mise à jour.

## 5. Code réseau France
- En Quick Settings, **Grid code = N/A** par défaut : pas de démarrage tant qu'il n'est pas choisi. Le code fixe aussi la tension nominale.
- Codes France relevés dans les tableaux Huawei :

| Code Huawei | Description manuel | Vu dans |
|---|---|---|
| `UTE C 15-712-1(A)` | France mainland power grid (métropole) | L1, M1, 50KTL-M3, 100KTL-M2, 20-40KTL-M3 |
| `UTE C 15-712-1(B)` | France island power grid | M1 |
| `UTE C 15-712-1(C)` | France island power grid | L1, 50KTL-M3, 100KTL-M2 |
| `UTE C 15-712-1-MV480` | France island power grid (480 V) | 50KTL-M3, 100KTL-M2 |
| `FRANCE-EN50549-230` | « France FD C11-519-1… » | 100KTL-M2 (Issue 27), 20-40KTL-M3 (Issue 28, 2026) |
| `FRANCE-EN50549-519/12-230` | « France FD C11-519-1… » | idem |

- **Non trouvés** : « EN50549-LV-FR » n'existe pas dans ces tableaux (`EN50549-LV` = Irlande). `VDE-AR-N-4105` = Allemagne, ne pas utiliser en France.
- Choix entre UTE C 15-712-1(A) et FRANCE-EN50549-* : **(à vérifier avec Huawei France / exigences Enedis)**. Liste dépendante du firmware. Seuils U/f modifiables seulement avec l'accord du GRD.

## 6. Limitation d'injection et zéro injection (DTSU666-H / DDSU666-H)
- Compteur : **DTSU666-H** pour le triphasé (C&I, M1), **DDSU666-H** pour le monophasé (L1 seul). En cascade de L1 avec des triphasés, tous les L1 sur la même phase.
- Réglages par défaut (guide DTSU666-HW Issue 07) : adresse Modbus **11**, **9600 bps**, n.1 (sans parité, 8 bits, 1 stop), mot de passe utilisateur **701**. Paramètres : rapport TC, câblage n.34 (3P4W) ou n.33 (3P3W), direct (≤ 80 A) ou via TC. Pour le DTSU666-H, valeurs par défaut identiques **(à vérifier sur l'étiquette)**.
- Contrôle : **Pa, Pb ou Pc négatif** = TC branché à l'envers (P1/P2), à retourner. RS485 muet : câble coupé ou A/B inversés, adresse ou débit différents de l'onduleur.
- App : Réglage de puissance > Grid-tied point control > Active power :
  - `Unlimited` / `Grid connection with zero power` (zéro injection) / `Grid connection with limited power (kW)`.
  - `Closed-loop controller` : **Inverter** si un seul onduleur, **SDongle/SmartLogger** en cascade (forum : le paramètre se règle alors sur le dongle).
  - `Limitation mode` = Total power ; `Power adjustment period` ; `Power control hysteresis`.
  - Repli en cas de perte de communication : `Communication disconnection fail-safe` (Enable), `Communication disconnection detection time`, `Active power output limit for fail-safe` (%).
- Alarmes liées : 2067 (compteur), 2110 (contrôle au point de raccordement, 3 redémarrages manuels maximum par 30 jours), 2102.

## 7. Remplacement sous garantie (RMA)
À fournir à Huawei (politique de garantie 2.2.6) :
1. Description du défaut : grandeurs d'entrée et de sortie, **ID d'alarme + Cause ID**, **journaux** (logs).
2. **Numéro de série** du produit.
3. **Justificatif d'achat**.
- Optimiseurs : logs onduleurs et optimiseurs (40-50 kW : Settings > Feature parameters > Expert > Inverter all logs), modèles et quantités, plan des strings, R1, R2, N1, N2.
- Bonne pratique (non exigée par écrit) : photos de la plaque SN, de l'alarme, du câblage et des dégâts.
- Déroulé : Huawei expédie la pièce, la pièce défectueuse est à renvoyer **sous 15 jours** (sinon facturée au prix catalogue). Pièces de remplacement « même performance ou mieux », pas forcément neuves. Garantie de la pièce : 90 jours ou reste de la garantie d'origine, le plus long des deux.
- Remplacement **de l'appareil entier**, sauf : dongle livré avec l'onduleur, module de puissance et pack batterie (garanties séparées), fusible du module de puissance, module ventilateur.
- Contact France : eu_inverter_support@huawei.com, 00 800 33 88 88 88.
- Exclusions : force majeure, usure, non-respect du manuel, SN altéré, environnement hors spécifications, intervenant non autorisé, produits tiers, consommables.

## 8. Garanties standard Huawei (Europe)
Politique résidentielle globale, Issue 04 (2025-11-30) :

| Produit | Europe |
|---|---|
| SUN2000-L1 (monophasé) | 10 ans |
| SUN2000-M1 / M2 / M5 / MB0 (triphasé résidentiel) | 10 ans |
| Optimiseurs SUN2000 (450W-P…) | 25 ans (garantie liée au plan d'implantation physique correct) |
| SDongle livré avec l'onduleur / vendu seul | 10 ans / 2 ans (3 ans en Espagne et au Portugal) |
| Smart Power Sensor (compteur) | 2 ans (3 ans en Espagne et au Portugal) |
| LUNA2000-S0 module de puissance | 10 ans |
| LUNA2000-S0 module 5 kWh | 10 ans ou 16,45 MWh à 60 % EOL (Allemagne et Suisse : 13,17 MWh à 80 %), premier atteint |
| LUNA2000-S1 | 15 ans (5 ans de base + 10 ans avancés, si connecté à FusionSolar) |

- Départ de la garantie : 90 jours après expédition Huawei (vente directe), **180 jours** (distribution).
- Batterie : installer dans le mois qui suit l'achat, déclarer un défaut sous 1 mois. Les dommages dus à l'absence de recharge sont exclus. S1 : garantie avancée perdue si **déconnectée de FusionSolar plus de 6 mois**.
- **C&I (50KTL-M3, 100KTL-M2), SmartLogger3000A** : hors politique résidentielle. Des revendeurs annoncent **5 ans standard, extensibles** pour le 100KTL-M2. Durées et extensions **(à vérifier auprès de Huawei France ou du distributeur)**.

## Sources
- SUN2000-(75KTL-M1, 100KTL-M2…) UM Issue 27 : https://solarshop.baywa-re.lv/en/documents/huawei-inverters-01074694-009-01074694-009-0/382/60.pdf
- SUN2000-(20-40KTL)-M3 UM Issue 28 : https://solarshop.baywa-re.lv/en/documents/huawei-inverters-01075485-115-01075485-115-0/382/65.pdf
- SUN2000-50KTL-M3 UM Issue 05 : https://shop.solexis.ch/documents/file/onduleurs/huawei/ma_en_huawei_sun2000-50ktl-m3_v5.pdf
- SUN2000-(2-6KTL)-L1 UM Issue 10 : https://res.cloudinary.com/gpceurope/image/upload/v1690811120/eau10ickazhrwervcftj.pdf
- Huawei Insulation Resistance 2018 : https://solar.huawei.com/-/media/Solar/attachment/pdf/au/service/Supporting/SUN2000/2018INV019.pdf
- Inverter Alarm Reference : https://support.huawei.com/enterprise/en/doc/EDOC1100345192
- Smart I-V (NetEco) : https://support.huawei.com/enterprise/en/doc/EDOC1100047682 ; licences SmartLogger3000 : https://support.huawei.com/enterprise/en/doc/EDOC1100108365
- Guide de mise en service FusionSolar / SUN2000 app : https://support.huawei.cn/enterprise/en/doc/EDOC1100273864/3f8845ec/maintenance
- Optimizer Troubleshooting Guide : https://ske-solar.com/fileadmin/user_upload/TroubleshootingGuide_Optimizer_SUN2000-450W_SUN2000-600W-P_V01-2024-01-02_EN.pdf
- FAQ LUNA2000-S0 : https://solar.huawei.com/eg/products/luna2000-5-10-15-s0/support
- DTSU666-HW Quick Guide Issue 07 : https://res.cloudinary.com/gpceurope/image/upload/v1700224367/dravfukwswn7hmd5nmtf.pdf
- Residential Smart PV Warranty Policy Issue 04 : https://solar.huawei.com/admin/asset/v1/pro/view/d373d9834172413b85d346e1f691915d.pdf
- Garantie 100KTL-M2 (revendeur) : https://www.alternergy.co.uk/shop/sun2000-100ktl-m2-afci-huawei-sun2000-100ktl-m2-afci-3ph-inverter-2040
- Forum (mesures + et − pour garantie) : https://forum-photovoltaique.fr/viewtopic.php?t=72180&start=60 ; zéro injection sur dongle : https://forum-photovoltaique.fr/viewtopic.php?t=79459
