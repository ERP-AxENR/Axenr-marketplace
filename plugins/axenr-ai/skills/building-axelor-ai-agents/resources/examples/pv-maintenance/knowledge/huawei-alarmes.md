# Huawei SUN2000 / FusionSolar : alarmes fréquentes et diagnostic terrain

Périmètre : SUN2000-50KTL-M3, SUN2000-100KTL-M2 (C&I), SUN2000-2/6KTL-L1 (résidentiel, hybride), LUNA2000-5-S0, optimiseurs SUN2000-450W-P, SDongleA-05, SmartLogger3000A, compteurs DTSU666-H/HW.
Référence : Huawei « Inverter Alarm Reference » (Issue 10, 2025) et manuels 50KTL-M3, 2-6KTL-L1, 3-10KTL-M1.

## Règles de lecture
- Une alarme = **ID d'alarme** + **Cause ID** (sous-code). Exemple : 2064-1 ≠ 2064-13. Le Cause ID indique souvent le string (1..n = string 1..n) ou le ventilateur concerné.
- Gravité Huawei : **Major** (arrêt de production ou baisse de puissance), **Minor** (composant en défaut, production maintenue), **Warning** (onduleur OK, cause externe).
- Le libellé varie selon le modèle ou la version (ex. 2032 « Grid loss » ou « Grid Failure », 2063 « Cabinet overtemperature » ou « Overtemperature »). L'ID reste le même.
- Sécurité : avant d'intervenir côté DC, couper AC puis DC et attendre le délai indiqué sur l'étiquette (5 min en général). Ne jamais déconnecter un MC4 sous charge : attendre un courant de string < 0,5 A (2011/2012) ou couper le sectionneur DC.

## Tableau des alarmes onduleur (IDs vérifiés)

| ID | Nom | Gravité | Causes probables | Diagnostic / actions technicien |
|---|---|---|---|---|
| 2001 | High string input voltage | Major | Trop de modules en série : Voc du string > tension max de l'onduleur (1100 V sur M3/M2). Cause ID = paire de strings sur 50KTL-M3 | Recalculer la Voc à froid (coefficient de température), retirer des modules. L'alarme disparaît une fois la configuration corrigée. |
| 2002 (2003 : par string, Cause ID 1-28) | DC arc fault (AFCI) | Major | Arc électrique ou mauvais contact sur câble ou connecteur DC | Inspecter MC4 (fondus, mal sertis, marques mélangées), boîtes de jonction, câbles écrasés. Effacement auto si < 5 déclenchements/24 h. À partir de 5/24 h l'onduleur se **verrouille** : effacement manuel dans l'app (Gestion des alarmes > Effacer « DC arc fault ») après réparation. |
| 2011 | String reverse connection | Major | Polarité du string inversée | Attendre I < 0,5 A, DC SWITCH sur OFF, corriger la polarité. Si l'alarme persiste : reset depuis l'app, ou couper AC et DC 5 min. |
| 2012 | String current backfeed | Warning | String plus court que les autres sur le même MPPT, d'où une tension plus basse | Compter les modules par string, comparer les Voc, chercher un ombrage. Corriger après I < 0,5 A. |
| 2013 | Abnormal string power | Warning | String ombragé longtemps ou dégradé. Cause ID 1-28 = string | Comparer le courant au string voisin. Si string propre et non ombragé : chercher le module défaillant (I-V, thermographie). |
| 2015 | PV String Loss | Warning (Major sur firmwares récents) | String perdu (simple ou un des deux d'un connecteur 2-en-1) | Contrôler les connecteurs côté onduleur et côté champ, le Y 2-en-1, et l'état « string connecté » configuré manuellement. |
| 2021 | AFCI self-check failure | Major | Échec de l'autotest AFCI | Couper AC et DC, attendre 5 min, rallumer. Si persistant : support Huawei. |
| 2031 | Phase wire short-circuited to PE | Major | Impédance phase/PE faible | Mesurer l'isolement des phases AC, trouver le point bas. |
| 2032 | Grid loss / Grid failure | Major | Coupure réseau, disjoncteur AC ouvert, câble AC coupé | Mesurer la tension aux bornes AC. Si le disjoncteur AC est déclenché, **ne pas réarmer directement** : vérifier d'abord l'impédance onduleur et câbles. Normal si le DC est présent sans l'AC. |
| 2033 | Grid undervoltage | Major | Tension réseau sous le seuil, ou durée > LVRT | Occasionnelle : reprise auto. Persistante : mesurer au point de livraison, contacter le GRD, vérifier le disjoncteur et le câble AC. |
| 2034 | Grid overvoltage | Major | Tension réseau au-dessus du seuil, ou durée > HVRT. Souvent une montée en tension sur un câble AC long ou sous-dimensionné, en été à midi | Mesurer U au compteur et aux bornes de l'onduleur en pleine production : un écart de plusieurs volts signale une chute de tension dans le câble. Vérifier section, longueur, serrages. Contacter le GRD si U réseau > limites. Changer les seuils seulement avec l'accord du GRD. |
| 2035 | Grid voltage imbalance | Major | Écart entre phases au-dessus du seuil | Mesurer les 3 phases et le raccordement AC (neutre, serrage), puis GRD. |
| 2036 / 2037 | Grid overfrequency / underfrequency | Major | Fréquence hors des limites du code réseau | Occasionnelle : reprise auto. Persistante : vérifier le code réseau configuré, puis contacter le GRD. |
| 2038 | Unstable grid frequency | Major | ROCOF (vitesse de variation de la fréquence) hors code | Idem. Fréquent sur réseau faible ou groupe électrogène. |
| 2039 | AC overcurrent / Output overcurrent | Major | Chute brutale de tension ou court-circuit réseau | Reprise auto. Si fréquent : rechercher un court-circuit AC. |
| 2040 | Output DC component overhigh | Major | Composante DC du courant de sortie trop élevée | Reprise auto. Si persistant : support Huawei (défaut interne probable). |
| 2051 | Abnormal residual current | Major | Baisse de l'isolement DC/terre **pendant** le fonctionnement (pluie, connecteur humide) | Occasionnelle : reprise auto. Fréquente : mesurer l'isolement des strings (voir 2062). |
| 2061 | Abnormal grounding | Major | PE ou neutre non raccordé, mode de sortie incohérent avec le câblage | Vérifier le PE. En TN : vérifier le neutre et U(N-PE). Vérifier le paramètre de mode de sortie (3P4W ou 3P3W). |
| 2062 | Low insulation resistance | Major | Cause 1 : court-circuit PV/terre ou champ humide (rosée, pluie). Cause 2 : rack batterie à la terre ou en milieu humide | Lire dans le détail de l'alarme la **résistance mesurée (MΩ)** et la **position probable (%)** : 0 % = PV−, 100 % = PV+ ; position ≈ nb modules × % (±1 module). Vérifier le PE. Isoler string par string (voir procédures). Seuil abaissable (« Insulation resistance protection ») si le défaut n'apparaît que par temps humide **et** après vérification. |
| 2063 | Cabinet overtemperature / Overtemperature | Minor | Mauvaise ventilation, ambiance trop chaude, défaut | Dégager les entrées d'air, vérifier ventilateurs, exposition et dégagements. |
| 2064 | Device fault | Major | Défaut interne non récupérable. L1 : 1-2 boost, 3 contrôle, 4 onduleur, 5 capteur courant résiduel, 6 température, 7 EEPROM, 8 alim auxiliaire, 9 relais réseau, 10-12 bus DC | Couper AC et DC 5 min puis relancer. **AR Huawei, causes 1/10/11/12/20** : si un DC SWITCH est OFF, ne rien réarmer et appeler le support ; si l'aspect est anormal, ne retirer les MC4 qu'avec I < 0,01 A. Persistant : RMA. |
| 2065 | Upgrade failed or version mismatch | Minor | MAJ interrompue, versions incohérentes. L1 : 1-4, et 7 = échec MAJ optimiseur | Refaire la mise à jour (de jour, DC présent). Échecs répétés : support. |
| 2066 | License expired | Warning | Licence (ex. Smart I-V) en période de grâce ou expirée | Demander et charger une nouvelle licence. |
| 2067 | Faulty power collector | Major | Compteur (DTSU666/DDSU666) non joignable | Vérifier le modèle de compteur paramétré, l'adresse et le débit (par défaut 11 et 9600 bps, voir procédures), le câblage RS485 A/B, l'alimentation du compteur. |
| 2068 | Battery abnormal | Minor | 1 communication batterie, 2 surintensité port batterie, 3 câble d'enable, 4 tension port (L1). AR : 6 stockage incompatible, 7 débit compteur trop bas, 8 trop de racks, 9 PV câblé sur BAT | Voyant défaut batterie allumé : support. Vérifier câbles puissance, COM et enable, RS485, interrupteur auxiliaire. Arrêt app, couper AC, DC et batterie 5 min, rallumer batterie > AC > DC. Batterie retirée : Battery type = None. |
| 2080 | Abnormal PV module configuration | Major | Optimiseurs : 1-2 trop nombreux, 3 trop peu ou inversés, 4 trop de strings, 5 string inversé ou en CC, 6 parallèles inégaux, 7 position changée, 8 faible ensoleillement, 9 tension > entrée | Vérifier le nombre d'optimiseurs et de strings et les rallonges (+ à un bout, − à l'autre). Causes 7/8 : relancer la recherche d'optimiseurs par bon ensoleillement. 2080-12 : optimiseurs inversés (voir cas terrain). |
| 2081 | Optimizer fault | Warning (cause 1) / Major (cause 2) | 1 optimiseur(s) en défaut, 2 endommagé(s) | App : Maintenance > Optimizer layout > optimiseur en défaut (détail). Cause 2 : remplacement. |
| 2082 | Grid-tied/Off-grid Controller abnormal / Backup Box abnormal | Major | Perte de communication ou défaut du Backup Box | Arrêt via l'app, couper AC, DC et batterie, vérifier les câbles puissance et RS485, rallumer après 5 min. |
| 2086 | External fan abnormal | Major | Ventilateur externe en court-circuit, alimentation insuffisante, canal d'air obstrué. Cause ID 1-6 = ventilateur 1-6 | Couper AC et DC, contrôler les pales, retirer les corps étrangers, remonter. Si l'alarme persiste 15 min après redémarrage : **remplacer le ventilateur**. |
| 2087 | Internal fan abnormal | Major | Ventilateur interne en court-circuit ou HS | Couper AC et DC 5 min. Si persistant après 5 min de marche : support (remplacement de l'appareil). |
| 2102 | Protection upon communication failure | Minor | Perte de communication au-delà du délai, d'où une protection (bridage) | Rétablir la communication (dongle, SmartLogger, compteur). Désactiver la fonction si elle n'est pas requise. |
| 2103 / 2104 | AC / DC terminal temperature abnormal | Major | Câble sous-dimensionné ou oxydé, cosse mal sertie, couple de serrage insuffisant | Contrôler sertissage et serrage, thermographie des borniers. |
| 2110 | Power control abnormal at grid connection point | Major | Communication compteur anormale, ou courant au point de raccordement > seuil | Vérifier le câble compteur. Redémarrage manuel possible, **3 maximum par 30 jours**. |
| 61440 | Faulty monitoring unit | Minor | Mémoire flash pleine ou secteurs défectueux | Couper AC et DC 5 min. Si persistant : carte de supervision ou support. **Ce n'est pas une alarme ventilateur** (les ventilateurs sont 2086/2087). |

## Batterie LUNA2000-(5-30)-S0 (alarmes remontées par l'onduleur, manuel LUNA2000 Issue 17)

| ID | Nom | Gravité | Action |
|---|---|---|---|
| 3000 | Low battery DC input bus voltage | Major | Sectionneur DC batterie sur OFF ou câbles mal raccordés. Couper AC, DC et batterie 5 min, vérifier le câblage du module de puissance, rallumer batterie > AC > DC. |
| 3001 | Abnormal battery power control module | Major | Défaut interne du module de puissance. Redémarrage complet. Si le voyant défaut reste fixe : support (RMA). |
| 3006 | Abnormal battery expansion module | Major | Vérifier les câbles puissance et COM des modules 5 kWh, puis redémarrage complet. |
| 3012 / 3013 | Communication parallèle / module d'extension anormale | Major | Vérifier les câbles COM entre modules. |
| 3047 | Battery pack undervoltage | Major | Pack ou cellule trop bas (stockage long, batterie inactive). Recharger rapidement. Si l'alarme persiste après 1 h de charge : support. |

Comportements normaux à ne pas prendre pour une panne (FAQ Huawei LUNA2000-S0) : par temps froid, environ **300 W de « charge » sans hausse du SOC** (chauffage interne) ; au-delà de 99 % de SOC, passage en charge d'entretien et courant décroissant.

## Communication, supervision, optimiseurs

| Symptôme | ID | Diagnostic |
|---|---|---|
| Onduleur hors ligne dans FusionSolar (dongle) | (ID à vérifier) | LED SDongleA-05 : rouge clignotant rapide (0,2 s) = paramètres routeur absents ou faux ; rouge fixe = dongle HS, à remplacer ; rouge et vert alternés lents (1 s) = pas de communication avec l'onduleur (réenficher, tester sur un autre onduleur) ; rouge clignotant lent = échec de connexion au portail ; vert fixe = OK ; vert clignotant rapide = échanges en cours. Maximum 10 appareils en cascade RS485. |
| Perte de communication SmartLogger ↔ onduleurs | (ID à vérifier) | Vérifier le bus RS485 ou MBUS, les adresses et le débit. Effets possibles côté onduleur : 2102 (protection sur perte de communication) ou 2110 (contrôle au point de raccordement). |
| Optimiseurs non trouvés ou hors ligne | 2080 / 2081 / 2065-7 | Voir procédures et cas terrain : impédance string ≈ N × 1 kΩ, mise à jour MBUS (SPC330 ou plus), rallonges inversées. |

Autres IDs vérifiés (AR Huawei) : 2009 string en court-circuit à la terre, 2014 tension string/terre élevée (PID), 2070 îlotage actif, 2077 surcharge en mode secours, 2085 PID intégré anormal, 2090/2091 consigne DI P/Q anormale, 2113 région invalide, 2072 surtension AC transitoire ; LUNA : 3002 surchauffe du module de puissance, 3007 câble de module débranché, 3051 versions ESS incohérentes, 3061 fin de vie.

## Pièges connus
- Des sites tiers publient des correspondances fausses (ex. « 2011/2012 = tension réseau » ou « 2064 = courant résiduel »). Se fier aux tableaux Huawei ci-dessus.
- Les alarmes 3xx (ex. 313 = isolement) appartiennent aux anciennes générations SUN2000 (8-42KTL, avant M0/M1). Ne pas les mélanger avec les 20xx.

## Sources
- Huawei, Inverter Alarm Reference, Issue 10 (2025-02-08) : https://aqua-us.vn/wp-content/uploads/2025/05/Inverter-Alarm-Reference-1.pdf (copie). Officiel : https://support.huawei.com/enterprise/en/doc/EDOC1100345192
- SUN2000-(50KTL-ZHM3, 50KTL-M3) User Manual Issue 05 : https://shop.solexis.ch/documents/file/onduleurs/huawei/ma_en_huawei_sun2000-50ktl-m3_v5.pdf
- SUN2000-(2KTL-6KTL)-L1 User Manual Issue 10 : https://res.cloudinary.com/gpceurope/image/upload/v1690811120/eau10ickazhrwervcftj.pdf
- SUN2000-(3KTL-10KTL)-M1 UM : https://cdn.shopify.com/s/files/1/0839/6934/3828/files/SUN2000-5-6KTL-M1-UserManual_1_5.pdf
- SUN2000-(75KTL-M1, 100KTL-M2…) User Manual Issue 27 : https://solarshop.baywa-re.lv/en/documents/huawei-inverters-01074694-009-01074694-009-0/382/60.pdf
- LUNA2000-(5-30)-S0 User Manual Issue 17 : https://ske-solar.com/productdata/LUNA2000-S0/02_Manuals/UserManual_LUNA2000-(5-30)-S0_V17_2024-05-30_EN.pdf
- FAQ LUNA2000-5/10/15-S0 : https://solar.huawei.com/eg/products/luna2000-5-10-15-s0/support
- SDongleA-05 Quick Guide Issue 13 : https://solar-distribution.baywa-re.de/out/media/08-000441_SDongleA-05_Smart_Dongle_Quick_Guide_WLAN-FE.pdf
- Optimizer Troubleshooting Guide SUN2000-450W/600W-P : https://ske-solar.com/fileadmin/user_upload/TroubleshootingGuide_Optimizer_SUN2000-450W_SUN2000-600W-P_V01-2024-01-02_EN.pdf
- Huawei, Insulation Resistance (2018, anciennes gammes) : https://solar.huawei.com/-/media/Solar/attachment/pdf/au/service/Supporting/SUN2000/2018INV019.pdf
