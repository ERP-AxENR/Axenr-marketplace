# Huawei FusionSolar : cas terrain (symptôme → cause → résolution)

Fiabilité : **[Huawei]** = documenté par Huawei ; **[Forum]** = retour utilisateur non validé ; **[Forum, extrait]** = lu via un extrait de recherche seulement (page bloquée), à relire avant de citer.

## 1. Alarme 2062 le matin, disparaît dans la journée [Huawei]
- **Symptôme** : défaut d'isolement au démarrage du matin ou après la pluie, puis production normale.
- **Cause** : humidité ou rosée sur un point d'isolement faible. Exemples cités : vis de fixation traversant le dos d'un module, câble pincé contre un rail, jonctions vieillies, eau dans une boîte de jonction ou un sectionneur DC mal étanche.
- **Résolution** : mesurer **immédiatement** à l'apparition (le défaut s'efface en séchant). Faire PV+/terre et PV−/terre string par string, puis exploiter le % de position affiché par l'onduleur (voir procédures). Ne baisser le seuil de protection qu'après ce contrôle.
- Pour un dossier de garantie, Huawei demande ces mesures **+/terre** et **−/terre** ; la mesure +/− est inutile [Forum, extrait].
- Sources : https://solar.huawei.com/-/media/Solar/attachment/pdf/au/service/Supporting/SUN2000/2018INV019.pdf ; https://forum-photovoltaique.fr/viewtopic.php?t=72180&start=60

## 2. SUN2000-5KTL-L1 qui décroche l'après-midi en été (surtension, 2034) [Forum, extrait]
- **Symptôme** : arrêts de plusieurs heures l'après-midi. L'onduleur affiche 253 à 261 V alors que le multimètre et Home Assistant lisent moins de 253 V. Écart de plus de 6 V.
- **Cause suspectée** : chute de tension dans la liaison AC (câble, connexions) qui fait monter la tension vue par l'onduleur. Résolution non confirmée dans le fil.
- **Action technicien** : mesurer U au compteur et aux bornes AC de l'onduleur **en pleine production**. Un écart de quelques volts désigne la liaison AC : section, longueur, serrages, bornier du tableau.
- Cas voisin : onduleur lisant 9 V de plus qu'au disjoncteur aux pics de production ; cause avancée : câbles ou connexions défectueux [Forum, extrait].
- Sources : https://www.bricozone.be/t/surtension-huawei-sun2000-bug-onduleur-ou-autre-probleme.161402/ ; https://www.bricozone.be/t/onduleur-huawei-sun2000-qui-naffiche-pas-la-bonne-tension.156834/

## 3. Éviter les décrochages : « Suppression de l'augmentation de tension » [Forum, extrait]
- **Symptôme** : décrochages répétés à 253 V.
- **Contournement** : activer la fonction SUN2000 qui **réduit progressivement la puissance** avant le seuil au lieu de décrocher (essai avec des seuils autour de 232-234 V). Les auteurs rappellent que les seuils dépendent du site et que la fonction ne remplace pas les protections réglementaires.
- **Garde-fou** : modifier les protections U/f seulement avec l'accord du GRD (manuel Huawei, 2034).
- Source : https://www.bricozone.be/t/utilisation-de-suppression-de-laugmentation-de-tension-sur-sun2000-pour-eviter-les-decrochages.143868/

## 4. Optimiseurs tous trouvés mais pas de couplage, alarme 2080 (Cause 12) [Huawei]
- **Site** : SUN2000-10KTL-M1, 29 optimiseurs (PV1 : 14, PV2 : 15).
- **Symptôme** : recherche d'optimiseurs OK, mais échec du couplage et « Abnormal PV module configuration ».
- **Diagnostic** : impédance au multimètre côté onduleur. PV1 : R1 = 14,45 kΩ, R2 = 13,4 kΩ (normal, R1 ≈ N × 1 kΩ et R1 > R2). PV2 : R1 = 14,98 kΩ, R2 = 14,89 kΩ (R1 ≈ R2, donc une partie des optimiseurs est inversée).
- **Cause** : deux rallonges avaient **le même genre de connecteur aux deux bouts**, ce qui inversait les 4 optimiseurs du milieu.
- **Résolution** : remplacer les rallonges. Après correction : R1 = 15,5 kΩ, R2 = 14,35 kΩ, couplage OK.
- Source : https://ske-solar.com/fileadmin/user_upload/TroubleshootingGuide_Optimizer_SUN2000-450W_SUN2000-600W-P_V01-2024-01-02_EN.pdf

## 5. Optimiseurs SUN2000-450W-P non détectés [Huawei]
- **« Command search failed »** : le contact sec de l'onduleur est réglé en « DI rapid shutdown ». Le passer à **NC**, puis relancer. Sinon, onduleur défaillant.
- **Pas tous trouvés, impédance trop haute (R1 >> N)** : diode anti-retour ou parafoudre entre modules et onduleur (le shunter pendant la recherche), boîtier de sécurité mal raccordé, mauvais sertissage côté modules, entrée d'optimiseur mal branchée, string ouvert, optimiseur HS (impédance de sortie ≠ 1 kΩ).
- **Pas tous trouvés, impédance normale** : mauvais sertissage côté onduleur. Re-sertir.
- Mesure : par bon ensoleillement, avec la tension du string < 1 V (optimiseurs en sécurité). Attendu : (R1 + R2)/2 ≈ N × 1 kΩ (16 optimiseurs ≈ 16 kΩ).
- Source : guide optimiseurs ci-dessus.

## 6. Optimiseurs « hors ligne » par intermittence alors que l'énergie s'incrémente [Huawei]
- **Cause** : arrêts liés au « heartbeat » (signal de présence) entre optimiseurs et onduleur.
- **Résolution** : par bon ensoleillement, mettre à jour le **MBUS en SPC330 ou plus** (app locale, ou SmartPVMS > Update Management). Si le problème persiste : ajouter une self à air sous l'onduleur (intérieur) ou sous les modules.
- Variante : hors ligne longtemps avec alarme **2065-7**. Les optimiseurs sont restés en mode « loader » après une mise à jour ratée : refaire la mise à jour MBUS.
- Source : guide optimiseurs ci-dessus.

## 7. Production en baisse : Huawei remplace l'onduleur, sans effet [Forum, extrait]
- **Symptôme** : production anormalement basse. L'onduleur est remplacé par Huawei, le problème reste.
- **Cause** : **connecteur MC4 défectueux** au passage du coffret disjoncteurs.
- **Résolution** : connecteur shunté ou remplacé, tout refonctionne.
- **Leçon** : comparer les strings (alarme 2013) et inspecter les MC4 **avant** de déclarer un RMA.
- Source : https://forum-photovoltaique.fr/viewtopic.php?t=74932

## 8. Dongle : Modbus local OK mais plus de données dans FusionSolar [Forum]
- **Symptôme** : « Abnormal communication between management system and equipment ». Le Modbus TCP (port 502) répond toujours.
- **Résolution rapportée** : app FusionSolar > Moi > Gestion de centrale > Appareils > **+** > scanner le QR du SDongleA-05 > **Quick Setup** pour remettre les équipements en service.
- Diagnostic par les LED du dongle : rouge fixe = dongle HS ; rouge et vert alternés lents = pas de dialogue avec l'onduleur ; rouge clignotant lent = portail injoignable (Quick Guide Huawei).
- Source : https://community.openhab.org/t/i-can-read-modbus-data-via-tcp-with-sdongle-a05-but-inverter-no-longer-sends-data-to-fusionsolar-server/153148

## 9. Zéro injection impossible à régler [Forum, extrait]
- **Symptôme** : le réglage de zéro injection ne prend pas.
- **Cause** : avec un dongle, le paramètre est **au niveau du dongle et non de l'onduleur** (contrôleur en boucle fermée = SDongle).
- **Résolution** : réglage corrigé par le SAV Huawei au téléphone, en environ 5 minutes.
- Source : https://forum-photovoltaique.fr/viewtopic.php?t=79459

## 10. Compteur DDSU666-H toujours « hors ligne » (2067) [Forum, extrait]
- **Résolution rapportée** : mise hors tension puis sous tension de l'onduleur.
- Si l'alarme revient : vérifier l'adresse du compteur (11 par défaut) et le débit (9600), le modèle déclaré dans l'onduleur, les bornes RS485 utilisées et A/B. Un fil australien signale un câble RS485 posé sur les bornes 1-2 au lieu de 3-4 comme cause probable [Forum, extrait].
- Sources : https://forum-photovoltaique.fr/viewtopic.php?t=64637 ; https://forums.whirlpool.net.au/archive/38mqllz9-2

## 11. LUNA2000 « charge » 300 W en hiver sans que le SOC monte [Huawei]
- **Cause** : batterie froide, le **chauffage interne** fonctionne (environ 300 W typique) et la batterie ne se charge pas pendant ce temps.
- **Résolution** : rien à faire. Vérifier la température d'installation (optimum 15-30 °C selon la politique de garantie).
- Autre « non-panne » : au-delà de 99 % de SOC, charge d'entretien avec courant décroissant.
- Batterie qui reste vide : vérifier le **mode de fonctionnement**. « Fully fed to grid » contourne la batterie ; utiliser « Maximum self-consumption » [guide installateur tiers].
- Sources : https://solar.huawei.com/eg/products/luna2000-5-10-15-s0/support ; https://solar-tech-support.co.uk/brands/huawei/problems/battery-not-charging/

## 12. LUNA2000 en décharge profonde après 3 mois à l'arrêt, garantie refusée [Forum]
- **Symptôme** : 3 modules de 5 kWh. Après environ 3 mois hors ligne avec onduleurs arrêtés, packs à 0,0 / 0,0 / 0,5 V. Le BMS refuse la charge.
- **Réponse Huawei rapportée** : garantie refusée, système « hors ligne depuis plus de 30 jours ».
- **Cadre officiel** : la politique de garantie exclut les dommages dus à l'absence de recharge et l'absence de connexion à FusionSolar (mises à jour). L'alarme 3047 (pack undervoltage) impose une recharge rapide.
- **Leçon** : ne jamais laisser un stockage éteint ou hors ligne pendant des semaines.
- Source : https://akkudoktor.net/t/huawei-luna2000-akkumodul-5kwh-defekt/13000?page=2

## 13. AFCI 2002 qui revient et bloque l'onduleur [Huawei + guide installateur]
- **Symptôme** : arrêts répétés « DC arc fault », puis onduleur verrouillé.
- **Mécanisme** : effacement auto si moins de 5 déclenchements en 24 h. À partir de 5 en 24 h, **verrouillage**, effacement manuel dans l'app.
- **Causes terrain** : MC4 desserrés, corrodés, mal sertis ou de marques mélangées, eau, gaine frottant sur un rail, rongeurs.
- **Résolution** : inspection et remplacement des connecteurs **avant** l'effacement.
- Sources : manuel 50KTL-M3 (annexe AFCI) https://shop.solexis.ch/documents/file/onduleurs/huawei/ma_en_huawei_sun2000-50ktl-m3_v5.pdf ; https://solar-tech-support.co.uk/brands/huawei/problems/afci-fault/

## Bonus : différentiel qui saute (cascade d'onduleurs)
- Exigence Huawei (manuel L1) : différentiel en sortie AC **≥ 100 mA**, et pour un différentiel général : ≥ nombre d'onduleurs × 100 mA. Sur le forum, un installateur a contourné le problème avec deux 30 mA séparés [Forum, extrait]. Conformité à NF C 15-100 / UTE C 15-712-1 **(à vérifier)**.
- Sources : https://res.cloudinary.com/gpceurope/image/upload/v1690811120/eau10ickazhrwervcftj.pdf ; https://forum-photovoltaique.fr/viewtopic.php?t=45396&start=340

## Sources
URL citées dans chaque cas. En complément : https://forum-photovoltaique.fr/viewtopic.php?t=82154 (FusionSolar inaccessible : domaine « intl » remplacé par « eu5 », annonce d'un arrêt de l'app en Europe, à vérifier) ; https://www.elektroda.com/rtvforum/topic3721385.html (dongle : passage en Ethernet si le WiFi échoue).
