# Entités — GMAO (parc d'équipements, contrats de maintenance, lignes de planification, interventions)

> Vérifié sur la GMAO AxENR (AOP 7.4, module `fr.gmao` sur `axelor-intervention`, instance de démo, 19/10/2026),
> par écriture REST puis contrôle à l'écran, pour deux démos clients (deux tiers, deux contrats actifs, un parc de
> deux installations chacun). Les pièges marqués **(R)** sont constatés à l'exécution. Les règles marquées
> **(M)** sont des règles métier données par le responsable produit AxENR : elles s'imposent même quand
> l'application accepterait autre chose.

Voie recommandée : **API REST en rejouant les gestes de l'écran** (actions d'ouverture, de changement de champ et
boutons). Un contrat ne s'active pas par un simple changement de statut, et une intervention n'a de questionnaire
que si elle est planifiée par l'action de l'écran.

Les gammes et questionnaires d'intervention eux-mêmes relèvent du skill `seeding-axelor-intervention-surveys`
(axenr-gmao) : cette fiche ne couvre que les données qui les entourent.

**Pièges couverts par cette fiche** (détail au §3) :

- 222. Le site, c'est le tiers : aucun équipement « Site X » (M) (R)
- 223. Équipement mono-produit : toujours créer sa ligne d'équipement (M) (R)
- 224. Contrat GMAO : l'activation est une chaîne d'actions qui passe par `pending` (R)
- 225. Lignes de planification : rattacher les installations, génération par lieu (R)
- 226. Intervention : c'est la planification qui génère le questionnaire (R)
- 227. Adresse : la ville est obligatoire et peut manquer dans le référentiel (R)

## 1. Le parc : une arborescence de lieux et d'équipements

`Equipment` porte les deux natures, distinguées par `typeSelect` :

| Niveau | `typeSelect` | `placeTypeSelect` | Exemple |
|---|---|---|---|
| Installation (racine du parc) | `place` | 1 = Installation | « Installation A (250 kWc) » |
| Emplacement | `place` | 2 = Emplacement | « Local technique », « Toiture » |
| Équipement | `equipment` | — | onduleur, champ de panneaux, borne |

La hiérarchie passe par `parentEquipment`. Le tiers (`partner`) et son adresse de livraison (`address`, un
`PartnerAddress`) se posent sur **chaque** niveau, avec `inService`, `commissioningDate` et la famille
(`equipmentFamily`) pour les équipements : une gamme « par équipement » ne se génère que pour la famille visée.

## 2. Ordre de création (couches)

1. Référentiels : ville (si absente, piège 227), articles de prestation des lignes de contrat (copiés d'un article
   de prestation existant par `/ws/rest/<modèle>/<id>/copy`).
2. Tiers client, adresse, `PartnerAddress` (livraison + facturation + défaut).
3. Parc : installations, puis emplacements, puis équipements, puis leurs `TrackingNumber` et `EquipmentLine`
   (piège 223).
4. Contrat GMAO avec ses lignes, puis activation par les actions (piège 224).
5. Rattachement des équipements au contrat (`Equipment.contract`), puis lignes de planification (piège 225).
6. Interventions de démonstration, planifiées par l'action de l'écran (piège 226).

## 3. Pièges (n° 222 à 227)

### 222. Le site, c'est le tiers : aucun équipement « Site X » (M) (R)
Dans la GMAO AxENR, le nom du site est porté par le **tiers**. Un équipement de type lieu nommé « Site A » placé
au-dessus des installations est un doublon du tiers : il apparaît dans les listes de lieux et dans les lignes de
planification, et le client ne le reconnaît pas. La racine du parc est l'équipement **Installation**
(`placeTypeSelect` = 1, `parentEquipment` vide), nommé du nom de l'installation, jamais du site. Constaté sur une
démo : un « Site A » créé à tort a dû être supprimé et les installations remontées en racine.

### 223. Équipement mono-produit : toujours créer sa ligne d'équipement (M) (R)
Un équipement `isMonoProduct` avec son `product` n'est pas complet tant que sa liste `equipmentLineList`
(`EquipmentLine`) est vide : l'écran affiche un tableau de lignes vide, et la quantité installée n'existe nulle
part. Pour chaque équipement mono-produit :
- une `EquipmentLine` avec `product`, `quantity` et `equipmentLineProductLabel` ;
- pour un article suivi en série (onduleur, borne), un `stock.TrackingNumber` (`trackingNumberSeq` = numéro de
  série, `product`) relié par `trackingNumber`, quantité 1 ;
- pour un champ de panneaux, la quantité réelle de modules (ex. 538) sans numéro de suivi, la puissance crête
  restant cohérente (quantité × puissance unitaire).

### 224. Contrat GMAO : l'activation est une chaîne d'actions qui passe par `pending` (R)
Poser le statut à la main laisse un contrat sans version active ni facturation. Rejouer l'écran :
1. valeurs par défaut par les actions d'ouverture (onNew du contrat GMAO, qui posent notamment `isGmao` et la
   version courante), puis enregistrement avec les lignes dans `currentContractVersion.contractLineList` ;
2. `action-contract-method-waiting` (mise en attente) ;
3. `action-contract-group-ongoing` (activation).

Deux comportements silencieux :
- la réponse de `/ws/action` contient `{"save": true, "pending": "<action>[n]"}` : le client web enregistre puis
  exécute la suite ; par l'API, il faut **recharger l'enregistrement et rappeler l'action `pending`** en boucle
  jusqu'à ce qu'il n'y en ait plus ;
- sans `firstPeriodEndDate` sur le contrat, la mise en attente répond `status: 0` avec un simple message `info`
  (« Veuillez remplir la première date de fin de période ») et **ne fait rien**. Afficher systématiquement les
  clés `info`, `alert` et `error` des réponses.

Contrôle : statut de version 3 (active) et statut du contrat 2 (en cours) relus par l'API, puis l'écran.

### 225. Lignes de planification : rattacher les installations, génération par lieu (R)
`ContractPlanningLine` (`fr.gmao`) : une ligne par prestation récurrente (article de la ligne de contrat, type
d'intervention, périodicité `Duration`, durée par défaut). Pour une génération par lieu (`generationTypeSelect` = 2),
`placeSet` reçoit **toutes les installations** du parc (les lieux de type Installation), pas les emplacements
(local technique, toiture) ; `equipmentSet` reçoit les équipements à visiter. Poser `lastVisitDateDone` et
`nextVisitDate` depuis l'horloge du scénario, sinon le planning prévisionnel est vide. Un équipement absent de toute
ligne de planification ne sera jamais visité : le contrôler.

### 226. Intervention : c'est la planification qui génère le questionnaire (R)
Une intervention créée par un POST reste sans questionnaire. Rejouer l'écran :
`gmao-action-intervention-method-fill-planification-defaults`, puis
`gmao-action-intervention-method-on-planification-date-change`, puis
`action-intervention-method-compute-estimated-end-date-time`, puis `action-intervention-method-plan`, avec les
champs transitoires `_xTechnicianUser`, `_xPlanificationDateTime`, `_xPlannedInterventionDuration` et
`_xEstimatedEndDateTime` dans le contexte. Autres pièges du POST : `requestSubject` est une M2O (`RequestSubject`),
pas un texte (« argument type mismatch ») ; `estimatedDuration` est un champ calculé à ne pas envoyer. Une
intervention planifiée avant une modification de gamme garde l'ancienne version du questionnaire : en replanifier
une neuve pour la démo.

### 227. Adresse : la ville est obligatoire et peut manquer dans le référentiel (R)
Sur l'instance vérifiée, `Address.city` est obligatoire (« Champ de l'adresse manquant : city »). Chercher la ville
par nom (`UPPER(self.name)`) ; si elle manque (constaté pour Bastia), la créer avec code postal, pays et département,
sous un `importId` préfixé de la démo, puis poser `city`, `zip`, `townName` et les lignes `addressL4` à `addressL6`.
