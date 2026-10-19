# Entités — qualité (gammes et relevés de contrôle, améliorations qualité, processus, audits, alertes)

> Vérifié sur AOS 9.1.8 / AOP EE 8.2.3 (sur une démo client, 05/10/2026), par lecture du code, à blanc par l'API, puis
> par l'écriture réelle. Les pièges marqués **(R)** sont constatés à l'exécution ; les autres sont lus dans le code 9.1.8.

Voie recommandée : **API REST en rejouant les gestes de l'écran** (actions d'ouverture et de changement de champ
lues, puis boutons) ; le SQL ne sait ni numéroter une AQ, ni calculer une conformité, ni recopier un processus.

**Pièges couverts par cette fiche** (détail au §3) :

- 200. Une AQ ne s'enregistre pas sans séquence propre à sa société
- 201. L'API ne crée pas « depuis le relevé » dans la bonne société
- 202. Identification, résolution, analyse : laisser le dépôt les créer (R)
- 203. Les enfants de l'AQ se référencent entre eux : plusieurs passes
- 204. Responsables « Employé » et « Détecté par (interne) » : il faut des personnes
- 205. Conformité calculée par une formule Groovy côté serveur
- 206. Prélèvements créés par un bouton, numérotés à partir de 0
- 207. Le lien « Relié à » d'un relevé dépend du geste (R)
- 208. Fréquence de contrôle : nom calculé en anglais, traduit par l'onSave, et masquée
- 209. Types de contrôle : les champs de mesure sont des champs personnalisés à contexte
- 210. Diffusions d'AQ : séquence de la configuration qualité, puis requête de l'écran (R)
- 211. Audit (QualityControl) : le pré-remplissage est un bouton, et les points facultatifs polluent la liste
- 212. Conformité d'un point de mesure : l'écran pose deux champs
- 213. Rapport qualité et calendriers
- 214. Créer une équipe (Team) crée des menus (R)

Nés du même peuplement, deux pièges de méthode vivent dans `methode-rejouabilite.md` : 215 (le jar qui tourne prime
sur les sources) et 216 (comparer comme l'application stocke). Le piège 212 corrige la nuance du piège 69
(`methode-rejouabilite.md`). Pièges qualité plus anciens, dans `methode-coherence.md` : 49 (répartir les relevés de
mesure sur tous les contrôles), 50 (`planAttrs` / `entryAttrs` lus par la formule de conformité), 51 (lignes de gamme
et de prélèvement, `typeSelect` 1 / 2). Dans le piège 69 (et vraisemblablement le 49), « relevé » désigne un point de
mesure (QualityMeasuringPoint, ancienne génération), pas un relevé de contrôle.

**Libellés de l'écran (9.1.8)** : ControlPlan = gamme de contrôle (à ne pas confondre avec la gamme de fabrication,
ProdProcess, des autres fiches), ControlEntry = relevé de contrôle, QualityImprovement = amélioration qualité (AQ),
QualityControl = audit qualité, QualityAlert = alerte qualité.

## 1. Deux générations, trois familles
- Caractéristiques de produit / de lot (CharacteristicType, ProductCharacteristic, TrackingNumberCharacteristic) :
  souvent déjà utilisées par un déroulé (traçabilité) — vérifier avant d'y toucher.
- Nouvelle génération : ControlType → ControlPlanLineCharacteristic, ControlPlanFrequency → ControlPlan
  (+ lignes ControlEntryPlanLine typeSelect 1) → ControlEntry → ControlEntrySample (+ lignes typeSelect 2) →
  QualityImprovement (+ QIIdentification, QIResolution, QIAnalysis, défauts, décisions, causes, QITask).
- Ancienne génération : ControlPointType, QualityProcess (+ ControlPointModel, QualityMeasuringPoint modèles,
  QualityCorrectiveAction modèles) → QualityControl (+ ControlPoint, points de mesure, actions copiées) ;
  RootCause, Team (typeSelect 'quality'), Tag → QualityAlert.

## 2. Ordre de création (couches)
1. Référentiels : unités, MachineType (appareils de contrôle), Team quality, Tag (concernedModelSet = QualityAlert),
   RootCause, ControlPointType, **Sequence qualityImprovement par société**.
2. ControlType (+ MetaJsonField à contexte), ControlPlanLineCharacteristic, ControlPlanFrequency, ControlPlan + lignes.
3. ControlEntry → bouton createSamples → mesures → bouton conformité → statut 3.
4. QIStatus, QIDetection, QIDecision (+ QIDecisionConfigCompany), puis par société : QIDefault, QIProcess, QIAction,
   QIAnalysisMethod (+ items), QICause (branche = item de la même société).
5. QualityImprovement **seule** (le dépôt crée identification, résolution, analyse) → étiqueter et compléter ces trois
   fiches par leur id → défauts → décisions → causes → tâches → avancement → statut.
5 bis. (option) Séquences de diffusion par société dans QualityConfig → boutons « Générer les diffusions » (requête
   de l'écran rejouée) → étiqueter.
6. QualityProcess (+ modèles imbriqués) → QualityControl → bouton preFill → statuts 3, 4 → mesures → points fermés → 6.
7. QualityAlert → statuts 2, 3, 4.

## 3. Pièges (n° 200 à 214)

### 200. Une AQ ne s'enregistre pas sans séquence propre à sa société
`QualityImprovementManagementRepository.save` appelle `getSequenceNumber("qualityImprovement", company, …)` ;
`SequenceService.getSequence(code, company)` filtre `self.company = :company` dès que la société n'est pas nulle :
la séquence « AQ%YY » de l'init-data, sans société, n'est jamais trouvée → `PersistenceException` « La société … n'a
pas de séquence configurée pour Amélioration qualité ». Créer une séquence par société (préfixe distinct, sinon
collision de numéros entre sociétés) ; libellé `fullName` calculé par le groupe d'enregistrement de l'écran
`action-sequence-group-onsave` (le POST ne le pose pas). Les versions de séquence se créent seules au premier numéro.

### 201. L'API ne crée pas « depuis le relevé » dans la bonne société
Le bouton « Ajouter une amélioration qualité » (et l'onNew de l'AQ) prend la **société active de l'utilisateur**
(`setDefaultValues`) : en démo multi-société jouée en admin, poser `company` explicitement par un POST générique et
recopier le lien `qiIdentification.controlEntry` (ce que fait le bouton), plutôt que de changer la société active
d'admin.

### 202. Identification, résolution, analyse : laisser le dépôt les créer (R)
Envoyées imbriquées dans le POST de l'AQ, elles sont refusées : `ConstraintViolation QIAnalysis.qi ne doit pas être
nul` (le setter du côté propriétaire `QualityImprovement.setQiAnalysis` ne pose pas le lien inverse ; seul
`QIAnalysis.setQi` le fait). Créer l'AQ seule : `save` du dépôt appelle `getOrCreate*`, qui créent les trois fiches
via le setter inverse (analyse avec `planOwner` = utilisateur courant) ; puis les étiqueter (`importOrigin`) et les
compléter par leur id. Clé de rejeu : `qiIdentification.documentReference` (l'AQ n'a pas de nom ; son numéro naît à
l'enregistrement) — la poser immédiatement après la création, sinon un rejeu après incident recrée l'AQ.

### 203. Les enfants de l'AQ se référencent entre eux : plusieurs passes
Décisions, causes et tâches pointent les défauts (`qiResolutionDefault`, `qiResolutionDefaultsSet` obligatoires) :
créer les défauts, relire leurs ids, puis le reste. Règles de l'écran à tenir soi-même : quantité d'un défaut ≤
quantité non conforme ; somme des décisions d'un défaut ≤ quantité du défaut ; décision de résolution corrective,
décision de tâche préventive (domaines) ; coût total = forfait + coût direct ; forfait = montant de la décision pour
la société (QIDecisionConfigCompany) ; acceptation 1 si la décision n'en exige pas, 2 « En attente » sinon (quantités
acceptées en lecture seule au back-office : une AQ soldée avec décision « en attente » se lit comme incohérente).

### 204. Responsables « Employé » et « Détecté par (interne) » : il faut des personnes
Domaines : tiers `isEmployee = true` ; contacts rattachés à la société (`companySet`). `detectedByInternal` est
**obligatoire à l'écran** pour une détection interne (requiredIf) : laissé vide, l'AQ ne se réenregistre plus depuis
la fiche. Créer un contact consomme la numérotation des tiers (`PartnerServiceImpl.onSave`) ; « Responsable » des
audits, points et alertes est un **salarié** (Employee, contact obligatoire). Décision de démo à prendre en Phase 1
(numérotation des tiers).

### 205. Conformité calculée par une formule Groovy côté serveur
Ligne de relevé : `entryAttrs` (JSON) puis action `action-quality-control-entry-line-method-control-conformity` avec
`{id}` (le contrôleur relit la ligne en base : ici `{id}` suffit, à l'inverse du piège 132, `entites-ventes.md`) : résultat de la ligne et
du prélèvement. Écrire `resultSelect` à la main donne un relevé dont la conformité ne suit pas les mesures. Champs
JSON envoyés en **chaîne JSON**, décimaux en texte (`"34.00"`), comme l'écran les enregistre ; la plateforme les type
à la lecture (JsonContext). [R : 356 lignes saisies et vérifiées le 05/10/2026, résultats tous conformes à la règle
recalculée côté script]

### 206. Prélèvements créés par un bouton, numérotés à partir de 0
`createSamples` crée `sampleCount` prélèvements (n° 0 à n-1, référence « - ») en copiant les lignes de la gamme
(typeSelect 2, résultat « Non contrôlé ») et passe le relevé « En cours ». Ne pas créer prélèvements et lignes en
POST : la copie porte `controlPlanLine`, `planAttrs`, `controlType`.

### 207. Le lien « Relié à » d'un relevé dépend du geste (R)
Depuis le menu, en 9.1.8 **jar** : `onControlPlanChange` ne calcule rien (il sort dès que `getRelatedToSelectId()`
n'est pas nul, et ce getter généré d'un champ `long` rend 0, jamais nul) : réponse `relatedToSelect = null,
relatedToSelectId = 0` pour toute gamme. Les sources lues (plus récentes) le calculent : se fier au jar.
L'utilisateur choisit le lien dans le RefSelect « Relié à » : le reproduire (article de la gamme ; pour une gamme
d'opération, « OperationOrder » sans id). Depuis l'onglet Qualité d'un lot / d'une ligne de mouvement / d'un OF /
d'une opération : `addControlEntry` relie à cette fiche et propose la gamme de l'article (ou de l'opération) **si une
seule est Applicable**. Un relevé « relié à X » sans id et seul pour sa gamme devient un **modèle** (nom, nombre,
contrôleur) pour ce bouton.

### 208. Fréquence de contrôle : nom calculé en anglais, traduit par l'onSave, et masquée
Le dépôt calcule le nom en anglais (exemple d'une démo client : « 5 (<article>) each 1 (Livraison) ») ; l'action
d'enregistrement crée la traduction de valeur (« chaque ») : la jouer **avant** la création, une seule fois (sinon
doublon de traduction au rejeu). La fréquence est cachée sur la gamme et ses lignes dans les vues 9.1.8.

### 209. Types de contrôle : les champs de mesure sont des champs personnalisés à contexte
« Dimension » lit `acceptedDimension`, `minTolerance`, `maxTolerance`, `mesuredDim` (MetaJsonField,
`contextField = controlType`, `contextFieldValue` = id du type en texte). Un type nouveau sans ses propres champs
n'affiche aucune zone de saisie. Les champs créés ou modifiés par l'API, et même en SQL, s'affichent sans redémarrer
le serveur : en 8.2.3, `MetaStore.findJsonFields` relit `meta_json_field` en base à chaque ouverture de vue et
l'entité n'est pas en cache de second niveau (vérifié dans le code et le jar le 06/10/2026 ; constaté le 05/10 :
trois champs passés « visibles sur le mobile » par l'API, vus par le téléphone à la reconnexion). Recharger la page
ouverte suffit. Le redémarrage du piège 103 tient au configurateur, pas à ce cache.

### 210. Diffusions d'AQ : séquence de la configuration qualité, puis requête de l'écran (R)
« Générer les diffusions » exige `qiActionDistributionSequence` / `qiDecisionDistributionSequence` sur la
configuration qualité de la société (vide en init-data ; domaine `codeSelect` + `company = :company` : une séquence
par société). Par `/ws/action`, un contexte construit à la main échoue : diffusions d'action → « Detached entity …
QIAnalysis.version null » dès que le contexte porte une clé que l'écran n'envoie pas (`qi`, tâches avec `version`) ;
diffusions de décision → **aucune erreur et rien de généré** (le contrôleur relit la résolution et la sélection
`selected` se perd). Ce qui marche : relever la requête du navigateur (onglet Réseau des outils de développement, ou
MCP Playwright : `browser_network_request`) et la rejouer en ne changeant que les ids (gabarit relevé sur
une démo client le 05/10/2026, conservé dans le dossier de travail de cette démo). À l'écran, les deux
boutons fonctionnent. Sans modèle d'impression : pas de fichier, et « Envoyer » ne fait rien (saute les diffusions
sans fichier). Diffusions créées sans `importOrigin` : les étiqueter après.

### 211. Audit (QualityControl) : le pré-remplissage est un bouton, et les points facultatifs polluent la liste
`action-quality-control-method-pre-fill-operations` (modèle Wizard, contexte `qualityProcess`, `_qualityControl`)
copie points, points de mesure et actions correctives ; il crée aussi une copie « En attente » de chaque point
**facultatif**, rattachée à aucun audit visible, listée par le menu Points de contrôle (sans domaine). « Planifier »
exige des points ; « Fin » exige tous les points faits.

### 212. Conformité d'un point de mesure : l'écran pose deux champs
Type Conformité : la case `compliant` ET la note `measuringNote` 5 / 0 (action
`action-measuring-point-attrs-on-compliant-change`) ; type Note : seulement la note. Corrige la nuance du piège 69
(`methode-rejouabilite.md`).

### 213. Rapport qualité et calendriers
Le tableau de bord qualité ne compte que l'ancienne génération, filtré sur `created_on` du 1er janvier à aujourd'hui
(pas sur les dates métier) ; les calendriers s'ouvrent sur le mois courant. Des données « historiques » créées par
l'API comptent à la date d'écriture.

### 214. Créer une équipe (Team) crée des menus (R)
L'abonnement des membres (`MailFollowerRepository`) crée pour chacun un menu personnel `menu-team-<id>` (« Travail
d'équipe › <équipe> ») et son action-view `team.<id>` : une empreinte de la base qui suit `meta_menu` / `meta_action`
(exemple d'une démo client : la « photo du déroulé ») les voit (+1 menu par membre, +1 action par équipe). À annoncer dans
les écarts attendus, ou créer les équipes sans membres si les menus gênent.
