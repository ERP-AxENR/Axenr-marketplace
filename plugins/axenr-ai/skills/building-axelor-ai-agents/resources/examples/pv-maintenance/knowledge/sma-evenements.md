# SMA Sunny Tripower CORE1 (STP 50-40 / STP 50-41) : événements, procédures, garantie

Source principale : manuel d'utilisation en ligne CORE1 (manuals.sma.de/STP50-40, couvre STP 50-40 et STP 50-41), textes repris du manuel FR. Les numéros ci-dessous sont **ceux listés dans le manuel CORE1**. Règle : un numéro absent de cette liste n'est pas un événement CORE1 documenté.

## 0. Repères matériel (manuel, caractéristiques techniques)
- 6 entrées MPP indépendantes, 2 strings par MPP, 20 A max par entrée, Isc max 30 A par entrée. Tension DC max 1000 V, plage MPP 500-800 V, démarrage 188 V.
- AC : 50 kW, 230/400 V, 72,5 A, plage de tension 202-264 V (selon jeu de données régionales). Fusible AC max 100 A.
- Surveillance d'isolement : Riso > 34 kΩ. Unité de surveillance du courant de défaut sensible à tous les courants.
- Refroidissement SMA OptiCool, **3 ventilateurs**. Température de fonctionnement -25 °C à +60 °C. Poids 84 kg.
- Couples de serrage : PE (TX 25) 6 Nm ; bornes AC (six pans creux surplat 8) 20 Nm pour 35-95 mm², 30 Nm pour 120 mm² ; vis couvercle Connection Unit AC 6 Nm (serrage en croix).
- Schémas de terre : TN-C, TN-S, TN-C-S, TT (si U N-PE < 20 V).

## 1. Signaux DEL
Verte+rouge clignotent ensemble = pas de jeu de données régionales ; verte clignote 2 s = attente conditions d'injection ; verte clignote vite = MAJ ; verte fixe/pulse = injection ; **rouge fixe = événement** (lire le n° dans l'interface web ou le Data Manager) ; bleue fixe = LAN/WLAN actif ; clignotement rapide de toutes les DEL = surtension DC (34xx).

## 2. Événements réseau (101-901)
| N° | Message | Cause | Action technicien |
|---|---|---|---|
| 101 | Dérangement du secteur | Tension ou impédance réseau trop élevée au point de raccordement, déconnexion | Mesurer la tension au point de raccordement. Si hors plage : contacter le GRD (Enedis). Si dans la plage et le message persiste : SMA Service |
| 301 | Dérangement du secteur | **Moyenne 10 min** de la tension réseau hors plage autorisée | Mesurer en injection. Cas typique de surtension en fin de ligne (voir reseau-france-et-onduleurs.md). GRD si tension hors plage |
| 401 | Dérangement du secteur | Réseau en site isolé (îlotage) ou forte variation de fréquence | Vérifier absence de coupure/travaux réseau ; contacter le GRD |
| 501 | Dérangement du secteur | Fréquence hors plage | Si fréquent : demander au GRD l'autorisation de modifier les paramètres, puis SMA Service |
| 601 | Dérangement du secteur | Composante continue élevée dans le courant réseau | Contrôler la composante DC au raccordement ; si fréquent, voir GRD |
| 801 | Attente tension réseau / Panne réseau / Vérifier fusible | Câble AC mal raccordé ou jeu de données régionales incorrect | Vérifier disjoncteur AC enclenché, câble AC, jeu de données régionales, tension réseau |
| 901 | Pas de raccordement terre | Conducteur de protection mal raccordé | Contrôler le PE (6 Nm) |

## 3. Événements DC, isolement, arc
| N° | Message | Cause | Action |
|---|---|---|---|
| 3401, 3402, 3404, 3407, 3410, 3411 | Surtension DC / Débrancher le générateur | Surtension à l'entrée DC, **l'onduleur peut être détruit** | Mettre hors tension immédiatement, condamner. Mesurer Voc des strings < 1000 V (attention au froid). Si > 1000 V : revoir le nombre de modules par string |
| 3412 | Erreur d'isolement / Vérifier générateur | Défaut à la terre dans le champ PV | Procédure recherche défaut à la terre (§5) |
| 3501 | Erreur d'isolement / Vérifier générateur | Défaut à la terre côté PV, Riso mesuré avant couplage trop faible : pas de connexion au réseau | Idem §5. Typique le matin (rosée) ou par pluie |
| 3701 | Courant de défaut trop élevé | Courant de défaut dû à une mise à la terre momentanée des modules | Idem §5 |
| 3801, 3802, 3803, 3805, 3806, 3807, 3808 | Courant de défaut trop élevé (texte manuel) | **Surintensité à l'entrée DC**, interruption courte de l'injection | Si fréquent : vérifier dimensionnement (Isc par entrée ≤ 30 A, 20 A utiles) et câblage des strings |
| 4301 | Arc électrique série dans le string détecté par AFCI | Arc dans le string affiché (String N/A = non attribuable) | Mettre hors tension, inspecter modules, connecteurs et câbles du string (tous si N/A). Réinitialiser le blocage si redémarrage manuel configuré |
| 4302 | Arc électrique série string (D, E ou F) | Arc dans le string D, E ou F | Idem 4301 |
| 8208 / 8209 | Échec autotest AFCI (niveau de nuisance trop élevé / signal trop faible) | Défaut autotest détecteur d'arc | SMA Service |

## 4. Températures, internes, protections
| N° | Message | Action |
|---|---|---|
| 6001-6499 | Diagnostic automatique / Dysfonctionnement onduleur | SMA Service |
| 6502 | Surtempérature : arrêt | Nettoyer à la brosse souple les ailettes à l'arrière et les canaux de refroidissement sur le dessus ; ventilation suffisante ; température ambiante max respectée |
| 6512 | En dessous de la température min. de service | Reprise de l'injection à partir de -25 °C |
| 6603 | Courant de surcharge réseau (HW) | SMA Service |
| 6604 | Surtension du circuit intermédiaire (SW) | SMA Service |
| 7702 | Dysfonctionnement onduleur | SMA Service |
| 7801 | Erreur protection contre les surtensions | Parafoudre(s) déclenché(s) ou mal enfichés : remplacer les cartouches déclenchées |
| 8003 | Limitation de puissance active : température | Derating > 10 min : nettoyer ailettes/canaux, ventilation, pas d'ensoleillement direct sur l'onduleur |
| 9033-9038 | Arrêt rapide (Rapid Shutdown) : déclenché, erreur, réussi, échec mise en circuit | Vérifier configuration et interrupteurs de modules SunSpec ; 9038 : SMA Service |
| 10513 | Arrêt par commande installation | Protection réseau et installation déclenchée par le relais de surveillance |

**8001 et 7xxx "ventilateur"** : **aucun événement ventilateur n'est listé dans le manuel CORE1** (à vérifier avec SMA si un message ventilateur apparaît dans le journal). Un ventilateur défaillant se traduit en pratique par 8003 (derating) puis 6502 (arrêt).

## 5. Mises à jour, paramètres, communication
- 7102 fichier de paramètres introuvable/défectueux (recopier) ; 7105 réglage des paramètres échoué (vérifier code Grid Guard) ; 7106/7110 fichier de MAJ défectueux/non trouvé ; 7330 paquet micrologiciel incompatible ; 7333 transport MAJ échoué (réessayer, Ethernet plutôt que WLAN) ; 7342/7352/7354/7356 échec MAJ bootloader/WLAN/fuseaux/WebUI (réessayer) ; 7303 MAJ ordinateur principal échouée (SMA Service) ; 7347/7348 fichier de configuration incompatible/format défectueux.
- 7619 pas de données du compteur d'énergie (même réseau que l'onduleur) ; 7622 pas de communication avec le module I/O (déconnexion par sécurité).
- 6701, 6702, 8101 perturbation communication, injection continue (SMA Service si fréquent) ; 8102-8104 défaut de communication (SMA Service).
- 9002 code installateur invalide ; 9003 paramètres réseau verrouillés (Installateur + code Grid Guard) ; 9005 attente ordinateur principal (code Grid Guard ou tension DC sous le seuil de démarrage) ; 9007 autotest interrompu (raccordement AC, jeu régional) ; 29001 code Grid Guard valable.
- 10110 échec NTP ; 10248/10249 réseau surchargé (espacer les requêtes, moins d'appareils) ; 10250/10252/10253/10254 paquets défectueux, liaison perdue, 10 Mbit, half-duplex (câble, RJ45, switch, DHCP) ; 10282 connexion verrouillée (15 min utilisateur, 12 h Grid Guard) ; 10283 module WLAN défectueux (SMA Service) ; 10284/10286 WLAN impossible/perdu.

## 6. Procédures
**Mise hors tension (ordre imposé)** : couper le disjoncteur AC et condamner ; interrupteur-sectionneur DC sur O (cadenas si requis) ; attendre l'extinction des DEL ; vérifier l'absence de courant DC à la pince ampèremétrique ; noter la position des connecteurs ; déconnecter avec gants et outils isolés. Multimètre catégorie ≥ 1000 V DC.

**Recherche d'un défaut à la terre (3501, 3601, 3701 cités par le manuel)** :
1. Onduleur hors tension. Par string : mesurer U(+/terre), U(-/terre), U(+/-).
2. Défaut à la terre si les tensions sont stables et U(+/terre) + U(-/terre) ≈ U(+/-). Le rapport des deux tensions localise le module en défaut.
3. Si non concluant : mesure de Riso avec dispositif de court-circuitage sécurisé ; tension d'essai proche de la tension système max des modules sans la dépasser. Repère SMA : ~40 MΩ par module couche mince, ~50 MΩ par module cristallin (information technique SMA « Riso »).
4. Ne jamais reconnecter un string en défaut d'isolement à un onduleur sans transformateur.

**Nettoyage** : chiffon humidifié à l'eau claire uniquement, pas de produit nettoyant. Retirer poussière et feuilles. Sur 6502/8003 : brosse souple sur les ailettes arrière et les canaux de refroidissement en haut. Cassette 3 ventilateurs vendue en pièce détachée (réf. revendeur NR-PL-EXFAN-SET-01, à vérifier auprès de SMA).

**Mise à jour micrologiciel** : automatique (recommandée : Appareil > Mise à jour > Mise à jour automatique = Oui ; désactivée dans l'onduleur si le Data Manager la gère) ; fichier via l'interface web (Configuration des appareils > engrenage) ; clé USB ; « Chercher et installer la mise à jour » si l'onduleur a Internet. Vérifier ensuite le journal.

**Journal** : interface web de l'onduleur (Ethernet, WLAN, LAN), menu Événements ; export via Données > Exporter. Sunny Portal powered by ennexOS : événements par installation et par appareil.

**SMA Data Manager M (EDMM-10)** : DEL système verte = normal, rouge > 2 min = erreur de démarrage, rouge clignotant = erreur système, orange clignotant = MAJ. DEL COM : vert clignotant = tous les appareils LAN joignables, orange = au moins un perdu, rouge = tous perdus, orange/rouge alterné = pas d'adresse DHCP. Reset : 5-10 s redémarrage, 10-15 s mot de passe et compte admin, 15-20 s réglages usine.

## 7. Garantie SMA (conditions SMA Werksgarantie COM-RES-GB-de-88, achats après 20.05.2026)
- **STP50-41 : 5 ans** de garantie usine standard. La prolongation automatique à 10 ans par enregistrement ne vise que certains produits (ex. STPxx-3AV-40, Sunny Boy -1AV-41), **pas le CORE1**.
- **Data Manager M** : listé dans le premier groupe du tableau (2 ou 5 ans, colonne non lisible : à vérifier).
- Enregistrement produit sur my.sma-service.com/s/product-registration **sous 12 mois** après mise en service ou facture, sinon la garantie court depuis la date de livraison SMA.
- Extensions payantes : FLEX possible jusqu'à l'an 10 ; ACTIVE/COMFORT années 11-20 uniquement pour les produits passés à 10 ans par enregistrement. SMA peut exiger une vérification préalable de l'appareil.
- **France = pays Comfort** : échange sur site par SMA ou un partenaire, ou remplacement par l'installateur indemnisé d'un forfait (montant via la SMA Service Line). Appareil neuf ou reconditionné ; retour du défectueux sous 30 jours. Modification non autorisée = fin de garantie.
- **À fournir** : copie du PV de mise en service avec n° de série (la facture peut être demandée) et plaque signalétique lisible. Pour le support technique : type d'appareil, n° de série, version micrologiciel, message d'événement, lieu et hauteur de montage, type et nombre de modules, produits de communication, nom et accès Sunny Portal, réglages régionaux spéciaux, mode du relais multifonction. Contacts : go.sma.de/service.

## 8. Cas terrain
- **Riso par temps de pluie (SMA, landtreff.de)** : 3 onduleurs SMA en avertissement Riso 300-900 kΩ sous pluie, refus de couplage sous 500 kΩ. Tension des strings mesurée sans rien trouver. Un autre utilisateur cite comme cause un défaut à la terre sur les **connecteurs entre modules côté ouest**, où la pluie rentrait sous les panneaux. Leçon : ne pas abaisser le seuil Riso (le minimum SMA reste 200 kΩ pour cette génération), isoler string par string et inspecter les connecteurs exposés. https://www.landtreff.de/sma-wechselrichter-storung-bei-regen-riso-t127198.html (+ page 2 : ...-t127198-15.html)

## Sources
- https://manuals.sma.de/STP50-40/fr-FR/index.html (événements, DEL, défaut à la terre 391466379.html, nettoyage 391501579.html, micrologiciel 4145422987.html, caractéristiques 43470603.html, contact 535095051.html)
- https://manuals.sma.de/EDMM-10/fr-FR/index.html (DEL 13833956747.html, reset 13968966795.html)
- https://files.sma.de/assets/278703.pdf (conditions de garantie SMA)
- https://files.sma.de/downloads/Isolationsfehler-TI-en-10.pdf
- https://www.wattuneed.com/de/ersatzteile/27656-core-1-fan-cassette-with-3-fans.html
- https://www.landtreff.de/sma-wechselrichter-storung-bei-regen-riso-t127198.html
