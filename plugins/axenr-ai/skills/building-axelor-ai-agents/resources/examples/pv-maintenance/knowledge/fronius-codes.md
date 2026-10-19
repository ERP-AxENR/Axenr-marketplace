# Fronius Symo (3.0-20.0-3-M, ex. Symo 15.0-3-M) : codes d'état, Datamanager 2.0, garantie

Source principale : instructions de service Fronius Symo / Fronius Eco, version 044-17072025 (manuals.fronius.com/html/4204101909/fr.html). Le Symo GEN24 a une autre liste de codes (non couverte ici, à vérifier dans son propre manuel).

## 1. Principes
- Classe 1 = réseau, momentanée : l'onduleur se découple, surveille le réseau pendant la durée prescrite puis se recouple (Soft-Start selon setup pays). Pas de défaut appareil.
- *) = si permanent : technicien de maintenance formé par Fronius (Service Partner). **) = s'élimine seul ; si permanent : contacter l'installateur.
- Écran éteint longtemps après le lever du soleil : vérifier la tension AC aux bornes, 220/230 V ou 380/400 V (+10 % / -5 %).
- 306 et 307 s'affichent **normalement chaque matin et chaque soir** (faible ensoleillement) : pas de défaut.

## 2. Codes les plus utiles
| Code | Description | Comportement | Action |
|---|---|---|---|
| 102 | Tension AC trop élevée | Reprise auto quand le réseau revient dans la plage | Vérifier les couplages au réseau ; si permanent : installateur, puis GRD |
| 103 | Tension AC trop faible | idem | idem |
| 105 / 106 | Fréquence AC trop élevée / trop basse | idem | idem |
| 107 | Réseau AC non disponible | idem | Disjoncteur AC, câble, fusibles |
| 108 | Îlotage détecté | idem | idem |
| 112 | Erreur de l'unité de surveillance des courants résiduels | idem | idem |
| 301 / 302 | Surintensité AC / DC | Brève interruption, redémarrage | *) |
| 303 / 304 | Surcharge thermique module de puissance DC / AC | Brève interruption | Souffler de l'air comprimé dans les ouïes et radiateurs ; **) |
| 305 | Pas d'injection malgré relais fermé | Brève interruption | **) |
| 306 | Puissance PV trop faible | Brève interruption | Attendre l'ensoleillement (normal matin/soir) |
| 307 | DC basse : tension d'entrée trop faible | Brève interruption | idem ; si en pleine journée : contrôler strings, sectionneur DC |
| 308 | Tension de circuit intermédiaire trop élevée | Brève interruption | **) |
| 309 / 313 | Tension d'entrée DC MPPT1 / MPPT2 trop élevée | Brève interruption | Vérifier Voc des strings |
| 311 | Inversion de polarité des chaînes DC | Brève interruption | Vérifier la polarité des strings |
| 314-316, 325 | Capteurs de courant, InterruptCheck, surchauffe zone de raccordement | Brève interruption | *) |
| **326 / 327** | **Erreur ventilateur 1 / 2** | | *) ; test ventilateur au menu |
| 401, 416, 425 / 406, 407, 603, 604 | Communication avec l'étage de puissance / capteurs de température | Reprise auto si possible | *) |
| 408 | Composante continue trop élevée dans le réseau | | *) |
| 412 | Mode tension fixe avec valeur trop faible/élevée | | Vérifier le setup MPP ; **) |
| 417, 436, 438, 445, 480, 481, 558, 559, 564, 608 | Identification matériel / incompatibilité cartes (souvent après changement de carte) | | **Mettre à jour le micrologiciel** ; *) |
| 431 | Problème logiciel | Pas d'injection | Réinitialisation AC (couper/réarmer le disjoncteur) + MAJ micrologiciel |
| 443 | Tension circuit intermédiaire trop faible ou asymétrique | Pas d'injection | *) |
| **447** | **Défaut isolation** | Pas d'injection | *) + recherche défaut d'isolement DC |
| 448 | Neutre non connecté | Pas d'injection | Contrôler le neutre AC |
| 457 | Erreur relais de tension du secteur | Pas d'injection | Vérifier le câble AC ; *) |
| 463 | Polarité AC inversée, connecteur AC mal branché | | Contrôler le câblage AC |
| 474 | Capteur de l'unité de surveillance des courants résiduels défectueux | Pas d'injection | **) |
| **475** | **Défaut d'isolation (liaison entre module solaire et terre)** | Pas d'injection | Mesure Riso par string, inspection câbles, connecteurs, modules |
| 482 | Setup interrompu à la première mise en service | Pas d'injection | Réinitialisation AC puis relancer le setup |
| 502 | Défaut d'isolation des modules (avertissement) | Avertissement, injection continue | **) ; surveiller, mesurer Riso |
| **509** | **Pas d'injection au cours des dernières 24 h** | Avertissement | Acquitter ; vérifier les conditions (neige, sectionneur, disjoncteur, défaut amont) |
| 517 | Réduction de puissance pour température trop élevée | Avertissement | Air comprimé dans ouïes et radiateurs ; s'élimine seul |
| 520 | Pas d'injection depuis MPPT1 en 24 h | Avertissement | Acquitter ; vérifier le string MPPT1 |
| 522 / 523 | DC basse chaîne 1 / 2 | Avertissement | *) |
| 560 | Réduction de puissance pour surfréquence | Réduction | S'élimine seul |
| 566 | Détection d'arc désactivée | Message quotidien | Pas une erreur ; acquitter |
| 572 / 573 | Limitation par l'étage de puissance / sous-température | | *) |
| 607 | Erreur unité surveillance courants résiduels | Pas d'injection | Acquitter (Entrée) ; si récurrent : inspecter l'installation PV |
| 705 | Conflit de numéro d'onduleur | | Corriger le numéro dans le setup (Solar Net) |

Autres : 601 bus CAN plein (MAJ micrologiciel) ; 721 EEPROM réinitialisée ; 731-746 clé USB ou fichier de MAJ (reformater en FAT12/16/32, retélécharger, attendre ~2 min avant de relancer) ; 751-758 perte de l'heure ou module horloge (régler date/heure) ; 766 limitation de puissance d'urgence à 750 W (*) ; 773 setup pays invalide (*) ; 1000-1299 statut interne, info pour le support.

**Codes de la demande non présents dans le manuel 2025** :
- **472** : absent (à vérifier).
- **567** : absent du manuel. Sur un fil de forum (Symo 6.0-3-M, 2023), 567 est associé à « réduction de puissance dépendante de la tension active » (P(U), au-delà de 253 V). **Ce n'est pas un code ventilateur** (les ventilateurs sont 326/327). À vérifier avec Fronius selon la version de micrologiciel.

## 3. Maintenance Symo
- Poussière : air comprimé propre dans radiateurs, ventilateurs arrière et ouïes du support.
- Test ventilateurs : menu Ventilateur > Test n°1/n°2, contrôle à l'oreille et au toucher (l'écran n'affiche pas le résultat).
- Menu Basic > Paramètres d'isolation : alarme ON/OFF, seuil d'avertissement. Réinitialisation AC = couper puis réarmer le disjoncteur.

## 4. Datamanager 2.0 et Solar.web : « hors ligne »
| DEL | État |
|---|---|
| Solar.web | Vert = connecté ; **rouge = connexion nécessaire mais absente** ; éteinte = non requise |
| WLAN | Vert = connecté ; rouge fixe = pas de connexion ; rouge clignotant = WLAN défectueux ; vert clignotant = mode service (point d'accès ouvert) ; vert/rouge alterné = point d'accès ouvert > 1 h |
| Alimentation | Vert = OK ; éteinte = alimentation Solar Net insuffisante (ou mode esclave) ; rouge clignotant = MAJ en cours (ne pas couper) ; rouge fixe = MAJ échouée |
| Connexion | Vert = Solar Net OK ; rouge = Solar Net interrompu |
| Solar Net (onduleur) | Clignote brièvement toutes les 5 s : surintensité (> 3 A, court-circuit) ou sous-tension (< 6,5 V, trop de composants DATCOM ; prévoir l'alimentation externe 43,0001,1194) |

Hors ligne : (1) Solar.web rouge + WLAN vert = Internet/box/pare-feu ; WLAN rouge = SSID, mot de passe, portée (préférer le LAN). (2) Accès local : commutateur IP en A = 169.254.0.180 (LAN) ou point d'accès « FRONIUS_240.XXXXXX » (192.168.250.181, mot de passe sur l'écran), http://datamanager ; B = DHCP. (3) Solar Net : un seul Datamanager par boucle, obturateurs sur les ports libres, numéros uniques (sinon 705). (4) Relancer l'assistant Solar.web.

## 5. Garantie Fronius (page Fronius France, consultée 10/2026)
- **Enregistrement sur Solar.web dans les 30 mois suivant la livraison** ; la garantie démarre à la mise en service.
- Onduleur **< 50 kW** (Symo 15.0-3-M) : **10 ans** gratuits après enregistrement. Onduleur ≥ 50 kW : 5 ans.
- Mention de la page : extension gratuite conditionnée à l'enregistrement d'un onduleur neuf **mis en service après le 1er juin 2026**. Les appareils plus anciens relèvent des conditions en vigueur à leur date (ex. septembre 2023 : modèle « 5 + 5 ans » ; ancien modèle revendeur « 2 ans + extension » : à vérifier sur le certificat Solar.web de l'appareil).
- Extension payante jusqu'à **15 ans**, à acheter **dans les 6 mois** suivant le début de la garantie, impossible si un dossier SAV est ouvert sur le n° de série.
- Certificat : Solar.web > Enregistrement des produits (Smart Meter, Ohmpilot et accessoires : la facture fait foi).
- SAV : formulaire Fronius avec l'e-mail du compte Solar.web, intervention via un Fronius Service Partner. Modalités d'échange standard : selon les conditions du pays (à vérifier).
- À préparer : n° de série, code d'état et historique (Solar.web ou menu LOG), version micrologiciel, photos plaque et câblage, mesures (Voc, Riso, tension AC).

## 6. Cas terrain
1. **Symo 15, MPP2 à zéro puis 475 sous la pluie (energiesparhaus.at, 2024)** : MPP2 perdu le 30/01, -40 % de production en février, 475 « Isolationsfehler » le 01/03 sous la pluie. Courbes MPP1/MPP2 comparées pour isoler le string. Cause : **module brûlé**, probablement une diode bypass défectueuse (ombrage hivernal) ; connecteur mis hors de cause. Module déposé : string de nouveau normal le 15/03, réclamation au fabricant du module. https://www.energiesparhaus.at/forum-pv-anlage-mpp2-liefert-keine-leistung-mehr/76627_2
2. **Symo 6.0-3-M, code 567 / P(U) (energiesparhaus.at, 2023)** : alertes « réduction de puissance dépendante de la tension » plusieurs fois par jour en semaine, pas le week-end ; le GRD affirme une tension dans la tolérance de 10 %. Micrologiciel mis à jour, sans solution confirmée. Piste : P(U) au-delà de 253 V, nouvelles installations PV voisines. https://www.energiesparhaus.at/forum/75461
3. **Gen24 10.0 : le différentiel saute par orage ou pluie (energiesparhaus.at, 2025)** : consigne Fronius citée : DDR type A **≥ 100 mA par onduleur**, pas de 30 mA ; corrélation pluie = défaut d'isolement probable ; terre de la batterie à ne pas raccorder sur le bornier de terre du Gen24. https://www.energiesparhaus.at/forum/82970

## Sources
- https://manuals.fronius.com/html/4204101909/fr.html (Symo/Eco, v044-17072025)
- https://s1.solacity.com/docs/Fronius/Fronius_Symo_operation_manual.pdf (Symo US 2016, même structure de codes)
- https://www.fronius.com/fr-fr/france/energie-solaire/installateurs-et-partenaires/service-et-assistance/warranty-models
- https://www.fronius.com/fr-fr/france/energie-solaire/a-propos/actualites/jusqu-a-10-ans-de-garantie-cinq-plus-cinq-04092023
- https://www.energiesparhaus.at/forum-pv-anlage-mpp2-liefert-keine-leistung-mehr/76627_2
- https://www.energiesparhaus.at/forum/75461
- https://www.energiesparhaus.at/forum/82970
