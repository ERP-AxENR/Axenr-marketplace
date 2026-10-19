---
name: gmao-capabilities
description: >
  Capacites reelles de la GMAO AxENR, validees par les experts AxENR : ce qui est
  standard, parametrage, roadmap fin 2026 ou specifique. A charger pour qualifier
  un besoin GMAO, repondre a un appel d'offres ou un cahier des charges de
  maintenance (photovoltaique, IRVE, PAC, eolien), ou des qu'on demande « est-ce
  que la GMAO sait faire », « offline », « photo », « signature », « OT preventifs »,
  « planning techniciens », « GTI / GTR », « monitoring », « stock ». PAS pour :
  parametrer l'instance (axenr-erp) ou developper (axenr-dev).
metadata:
  owner: axenr
  source: reponse au CDC GMAO SEM 24 / AgirEnergy (parc photovoltaique)
---

# Capacites reelles de la solution GMAO AxENR

Cette section capitalise des reponses REELLES validees par les experts AxENR (source : reponse au CDC GMAO SEM 24 / AgirEnergy, parc photovoltaique). Elle fait autorite pour qualifier un besoin en "Standard / Parametrage / Specifique" et pour repondre aux appels d'offres GMAO. En cas de doute, ces faits priment sur une supposition.

## Terminologie et modele de donnees
- L'entite "centrale / site de production" se modelise via l'objet **Installation** (nom commercial AxENR ; techniquement Equipment). Champs deja presents : **PRM, Puissance, date de mise en service, date de fin de garantie**. Extensible via **Studio**.
- Hierarchie du parc : **Site -> Installation -> equipement (onduleur / module / borne)**. Generique, reutilisable IRVE / PAC / eolien.
- Branding : dans les livrables client, parler de **"AxENR" / "AxENR Open Suite"**, jamais "Axelor".

## Fonctions STANDARD (natif ou DEJA developpe dans le module GMAO)
- Fiche Installation (identite, adresse, client, GPS) ; hierarchie equipements parent/enfant.
- Contrats de maintenance par Installation et par type de prestation ; **plusieurs contrats simultanes sur une meme Installation** (relation 1-N) ; echeances + alertes / rappels automatiques (DEJA codes).
- **Generation automatique des OT preventifs** selon frequence contractuelle (DEJA codee dans le module GMAO).
- Planning visuel multi-techniciens (semaine / mois) ; gestion des priorites (curatif urgent vs preventif) ; workflow statut planifie -> en cours -> termine -> valide.
- **Planification intelligente anti-doublon** : le systeme evite la multi-planification sans contraindre (pour gerer le multi-technicien) ; une intervention ne se planifie qu'une seule fois -> risque de conflit quasi nul par defaut. (=> la "detection de conflits de planning" est STANDARD, PAS du developpement.)
- **Application mobile terrain (AxENR Open Mobile)** : acces fiche + historique, creation / cloture de bon d'intervention, saisie des travaux, **temps passe via chronometre**.
- **Formulaire de gamme d'intervention** avec types de reponse configurables, dont **"image"** (photos avant / apres / anomalie) et **"signature"** (technicien ET client). => Photo et signature electronique sont STANDARD via les gammes, PAS un dev mobile specifique.
- Gestion de stock native ; **alertes de stock bas** (seuils de reapprovisionnement).
- **Gammes de maintenance par FAMILLE d'equipement** (ex : "Onduleur Huawei" et "Borne Schneider" ont chacun leurs propres gammes).
- Reporting / dashboards de synthese ; exports Excel / PDF natifs ; **export FEC** pour la comptabilite (dont interfacage EBP via exports parametrables).
- **Module AxENR Template** : generation automatique de rapports (docx) declenchee par les gammes d'intervention ; on peut y integrer les modeles de rapport du client.
- Utilisateurs / roles / droits ; carte / geolocalisation par GPS ; acces web (Chrome / Edge) ; hebergement France ; import standard (Excel / CSV) ; evolutivite native.
- **GTI / GTR** : traçables sur le contrat de maintenance, avec verification du temps d'intervention reel vs prevu.

## Fonctions PARAMETRAGE / CONFIGURATION
- Champs techniques additionnels sur l'Installation (via Studio).
- GED / typage documentaire (contrats, plans, schemas unifilaires, certificats, rapports Q19).
- Tableaux de bord contrats (actifs / a renouveler / expires) ; rapports par technicien / par Installation.
- **Mode OffLine** : il existe un **module OffLine** a **configurer** selon les cas d'usage. => L'app mobile PEUT fonctionner hors ligne apres configuration. NE PLUS presenter l'offline comme "non supporte" ou "risque bloquant" : c'est FAUX. C'est un lot de configuration / cadrage, pas un developpement from scratch.
- **Ressources utilisees** (nacelle, etc.) : systeme existant mais aujourd'hui NON modifiable ; pour tracer le materiel utilise, passer par des **questions de gamme** ou l'utilisateur selectionne le materiel.
- **Interface monitoring Epices Energies** : existante ; finalisation import / export prevue **fin 2026**. Autres plateformes (SolarEdge, Fusion Solar) integrables si elles exposent une API.

## Fonctions ROADMAP (prevu fin 2026) — annoncer comme "prevu", jamais comme dispo aujourd'hui
- **Zone geographique** d'attribution + affectation automatique au technicien de zone.
- **Lien equipement <-> stock** (suivi du stock depuis l'Installation).
- **Tracabilite pieces consommees <-> bon d'intervention**.
- Finalisation de l'**interface Epices Energies** (monitoring / pertes de production).

## Fonctions SPECIFIQUES / hors perimetre actuel
- Suivi des pertes de production par Installation : dependant du monitoring externe (lie a l'interface Epices / API constructeur) tant que non finalise.
- **Connecteur bornes de recharge (IRVE)** : PAS de connecteur a ce stade. Le socle generique (Site / Installation / puissance / gammes) facilite l'ajout, mais c'est un developpement dedie.

## Regles de posture commerciale (apprises)
- Ne PAS survendre, mais ne pas sous-estimer non plus. Deux erreurs a NE PLUS commettre : (1) classer l'offline "non supporte" (le module OffLine existe) ; (2) classer photo / signature en "dev specifique" (standard via gammes).
- Distinguer clairement trois horizons : **dispo aujourd'hui** vs **roadmap fin 2026** vs **specifique / hors perimetre**.
- Prix / delais / support : renvoyer au cadrage commercial, pas de chiffres inventes.
- Rester fidele au principe de genericite multi-ENR : modeliser Installation / puissance / famille d'equipement, jamais "en photovoltaique pur".
