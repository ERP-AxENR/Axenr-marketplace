> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Lire l'entrée du client et la ramener au modèle Axelor

Méthode éprouvée sur une reprise ERP de grande taille (plusieurs centaines de champs relevés sur une trentaine
d'écrans du logiciel sortant, quelques dizaines de points d'arbitrage, plus de 250 colonnes retenues sur une
trentaine de tables). Elle vaut pour les trois formes d'entrée ; seule la
première étape change.

## 1. Relevé brut, champ par champ

Une ligne par champ client, avec un **identifiant stable** préfixé par domaine (`TI-01` tiers, `BI-03`
bibliothèque, `US-07` utilisateurs…) : c'est lui que citent le registre, le gabarit et le rapport.

| Entrée | Comment relever | Piège |
|---|---|---|
| **Captures d'écran** (PDF, images) | Page par page, onglet par onglet : chaque libellé visible = un champ, avec la page. Noter une valeur d'exemple lue sur l'écran. Les fenêtres dont le contenu n'est pas capturé sont notées « non vu » et ne s'inventent pas. | Un écran montre des champs **calculés** (totaux, compteurs) : ils se relèvent mais se classent « non repris ». |
| **Fichier d'export** du logiciel sortant | Une colonne = un champ ; profiler chaque colonne (taux de remplissage, valeurs distinctes, formats, colonne numérique dérivée d'une autre). Une colonne vide à 100 % se note et ne se mappe pas. | Les codes internes (statuts « AF/RE/OK », familles) demandent une **table de correspondance** de valeurs, pas seulement de colonnes. |
| **Excel brut** hors format (feuilles faites main) | Repérer la vraie ligne d'en-tête, les cellules fusionnées, les sous-totaux, les onglets redondants ; profiler comme un export. | Une même entité répétée sur plusieurs lignes (une par agence, par rôle) : à fusionner avant import. |

Colonnes du relevé : `id ; domaine ; où (écran/page ou fichier/colonne) ; champ client ; exemple ;
compréhension`.

## 2. Classement

Pour chaque ligne du relevé, en t'appuyant sur le relevé des champs **de l'env cible**
(`ee_api.py fields`), jamais sur la mémoire :

- **Direct** — un champ natif évident (`name ← Raison sociale`). Aucune question.
- **Ambigu** — plusieurs voies (établissement ou adresse ?), un sens incertain, ou un champ client qui
  en recouvre deux (« mode de règlement » = mode + condition). Il reçoit une **proposition** motivée.
- **Absent** — Axelor n'a pas le champ (consigne 2). S'il existe comme champ **Studio** sur l'env cible,
  il est signalé comme tel, pas mappé (consigne 3).
- **Non repris** — sans valeur une fois dans Axelor (calculé, obsolète, remplacé par un paramétrage).

## 3. Registre des arbitrages

Un point par ambigu, regroupant les lignes de relevé qu'il tranche :

`id (P01…) ; bloc ; question ; lignes du relevé ; statut (Tranché / Reporté / À signaler) ; proposition
Axelor ; décision ; raison ; qui a tranché ; date`

- Tu tranches seul tout ce qui a une réponse raisonnable (abandon ou correspondance alternative), en
  traçant la raison : c'est la consigne 4. Seuls **10 points au plus**, les ultra-ambigus, remontent à
  l'utilisateur — en une fois, en noms métier, chacun avec ta proposition et ses conséquences.
- Un point **reporté** (il faut mesurer sur les vraies données, ou le client doit trancher) garde dans le
  gabarit **toutes** les colonnes natives utiles aux voies possibles : on ne tranche pas à sa place.
- Le croisement de deux arbitrages crée parfois une incohérence (un devis historique à une ligne perd les
  heures prévues de l'offre) : elle va en « À signaler », pas en décision silencieuse.
- Une décision tranchée ne se rouvre pas, sauf fait nouveau.

## 4. Consolidation → colonnes attendues

Chaque ligne du relevé reçoit sa **destination finale** : Gabarit (onglet + colonne technique), Hors
gabarit (paramétrage, GED, autre flux), Non repris, Reporté. Les lignes « Gabarit » deviennent
`colonnes-attendues.csv` :

`classeur ; onglet ; colonne ; id du relevé ; consigne de remplissage`

- une cellule qui porte une **règle** (« = indice × 10 », « Fax : … dans la description ») est une
  consigne de remplissage, pas un nom de colonne ;
- un sous-champ de relation (`address.zip` d'un site) va dans l'onglet de la table cible (`Address`),
  relié par `<rel>.importId` ;
- une même table peut servir deux classeurs (tiers et contacts dans `Partner`) : un classeur ne peut pas
  avoir deux onglets du même nom, d'où un classeur de plus.

C'est ce fichier que `check_templates.py --expected` compare aux classeurs : 0 absente est la cible.

## 5. Gabarit vide ou rempli

- **Vide** : on exporte depuis l'env de répétition peuplé de 2 ou 3 fiches d'illustration par table
  (l'export ne crée pas les onglets liés sans données), puis on retire `id`, `<rel>.id` et les clés
  fabriquées, et on pose les lignes `EXEMPLE-…` tirées des valeurs vues chez le client.
- **Rempli** : on part des colonnes attendues et on écrit les lignes depuis les données client
  normalisées (import-ee-templates.md §5) ; chaque valeur transformée garde sa règle dans le registre.
