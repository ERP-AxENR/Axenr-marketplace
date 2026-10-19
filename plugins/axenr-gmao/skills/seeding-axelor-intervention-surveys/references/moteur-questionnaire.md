# Le moteur de questionnaire d'`axelor-intervention` — carte vérifiée

Établi le 2026-09-14 par lecture des sources AOS **9.0.13** (`axelor-intervention`) et vérification
en base sur deux bases AOS **9.1.6** (un socle vierge et une base de démo construction — schéma identique,
aucune colonne ajoutée sur les six tables du catalogue). **Aucune exécution applicative lors de la
rédaction de cette carte** : elle ne prouve par elle-même ni le rendu à l'écran ni l'import de bout en bout.
Les constats faits ensuite à l'écran et en base le même jour (AOS 9.1.4 / AOP EE 8.2.3) figurent dans
`SKILL.md` (règles de conception 0 et 2, pièges 8 et 9). Relu le 2026-10-15 dans les sources AOS 9.1.7 : la taille
de paquet de 20 (`InterventionSurveyGeneratorImpl`, `BATCH_SIZE`, `Lists.partition`) et l'absence de lecture de
`Range.isPrivate` par un service y sont toujours en place (lecture seule, non exécuté).

## Sommaire

1. [Les trois couches](#1-les-trois-couches)
2. [Les neuf types de réponse](#2-les-neuf-types-de-réponse)
3. [La multiplicité des gammes](#3-la-multiplicité-des-gammes)
4. [Le rattachement au type d'intervention](#4-le-rattachement-au-type-dintervention)
5. [La génération du questionnaire](#5-la-génération-du-questionnaire)
6. [Le conditionnement](#6-le-conditionnement)
7. [Le suivi : non-conformité et à-suivre](#7-le-suivi--non-conformité-et-à-suivre)
8. [Pièges](#8-pièges)
9. [Spécification YAML](#9-spécification-yaml)
10. [Le jeu de démo AOS comme gabarit](#10-le-jeu-de-démo-aos-comme-gabarit)

---

## 1. Les trois couches

```
AnswerType ──< AnswerValue                     catalogue réutilisable
    ^
    │
 Question                                      intitulé global, réutilisable
    ^
    │
 RangeQuestion >── Range >── RangeType         la gamme = le questionnaire
    │
    │  (à la planification de l'intervention)
    v
 InterventionQuestion >── InterventionRange >── Intervention     l'exemplaire rempli
```

| Entité | Table | Rôle |
|---|---|---|
| `AnswerType` | `intervention_answer_type` | le widget : type + unité + libellé de case + texte d'indication + valeur par défaut |
| `AnswerValue` | `intervention_answer_value` | un choix d'une liste ; porte `nonConforming` et `following` |
| `Question` | `intervention_question` | intitulé + indication + un `answerType` (obligatoire) |
| `Range` | `intervention_range` | la gamme ; titre obligatoire, `rangeType` obligatoire |
| `RangeQuestion` | `intervention_range_question` | la question dans la gamme ; ordre, obligatoire, privé, récap, conditionnement |
| `RangeType` | `intervention_range_type` | la multiplicité de la gamme |
| `OrderedRange` | `intervention_ordered_range` | accroche une gamme à un bloc d'un type d'intervention |
| `InterventionType` | `intervention_intervention_type` | le type ; code unique, catégorie obligatoire |
| `InterventionCategory` | `intervention_intervention_category` | code + nom |

Menus de configuration : *Intervention > Configuration >* Questions, Gammes, Types de gamme,
Types de réponse, Types d'intervention, Catégories d'intervention.

## 2. Les neuf types de réponse

`AnswerType.answerTypeSelect`, sélection `answer.type.select` :

| Valeur | Écran | Champ de réponse rempli | Remarque |
|---|---|---|---|
| `list` | liste déroulante | `listAnswer` (m2o) | **le seul** qui porte les drapeaux de suivi et le seul conditionnable |
| `text` | texte long | `textAnswer` | `defaultTextValue` pré-remplit |
| `date` | date | `dateAnswer` | |
| `picture` | image | `pictureAnswer` (MetaFile) | |
| `measure` | décimal | `measureAnswer` | `desiredUnit` affiche l'unité attendue |
| `checkbox` | case à cocher | `checkboxAnswer` | `checkboxName` porte le libellé |
| `indication` | texte affiché | `indicationText` | **jamais considéré comme répondu** (absent de `isAnswered`) |
| `signature` | pavé de signature | `signatureAnswer` (MetaFile) | signature à l'écran ou depuis l'app mobile |
| `advancedMonitoring` | liste figée | `advancedMonitoringAnswer` | domicile / agence / intervention précédente / suivante — remplit une adresse automatiquement. Spécifique à la prise de poste, **pas un type générique** |

Les quatre attributs `defaultTextValue`, `desiredUnit`, `checkboxName`, `indicationText` vivent sur
l'`AnswerType`, pas sur la `Question` : deux questions qui ont besoin de libellés différents ont
besoin de **deux AnswerType**.

## 3. La multiplicité des gammes

`RangeType.rangeTypeSelect`, sélection `range.type.type.select` :

| Valeur | Ce que produit la génération | Champ qui pilote |
|---|---|---|
| `standard` | **un** bloc, sans équipement | — |
| `equipment` | **un bloc par équipement** de l'intervention appartenant à la famille pointée | `equipmentFamily` (m2o, **singulier**) |
| `family` | **un** bloc, à condition qu'au moins un équipement de l'intervention appartienne à une des familles | `equipmentFamilySet` (m2m) |

Deux champs de famille distincts sur la même entité, un par mode. Se tromper de champ produit une
gamme qui ne s'affiche jamais.

Source : `InterventionSurveyGeneratorImpl.generateQuestionsForRange(Long)`.

## 4. Le rattachement au type d'intervention

`InterventionType` porte quatre points d'accroche :

- `advancedStartupMonitoringRange` — m2o, la gamme de prise de poste, générée **en premier** ;
- `headerRangeList` — `OrderedRange` via `interventionTypeHeader` ;
- `equipmentRangeList` — via `interventionTypeEquipment` ;
- `footerRangeList` — via `interventionTypeFooter`.

Une ligne d'`OrderedRange` ne remplit **qu'une** de ces trois colonnes ; la colonne remplie décide du
bloc. `sequence` ordonne à l'intérieur du bloc. Ordre de génération : prise de poste, en-tête,
équipement, pied.

Une gamme non rattachée par un `OrderedRange` existe en base et n'apparaît sur aucune intervention.

## 5. La génération du questionnaire

Déclencheur : **la planification** de l'intervention (`InterventionServiceImpl.plan`), dans un thread
séparé (`isSurveyGenerationRunning` porte le voyant à l'écran). Deux autres déclencheurs :
le changement de la liste d'équipements sur une intervention déjà planifiée dont le questionnaire
existe (`InterventionObserver`), et l'API mobile (`InterventionRestServiceImpl`).

Le bouton « Ouvrir le questionnaire » est verrouillé tant que `statusSelect < 30` (Démarrée).

La copie, par `RangeQuestion` :

- `InterventionQuestion.rangeQuestionSequence` ← le code séquence de la `RangeQuestion` (`RQ12`) ;
  c'est **la clé de rattachement** (contrainte d'unicité `interventionRange, rangeQuestionSequence`) ;
- intitulé, indication, type de réponse, unité, libellé de case, texte d'indication, valeur par
  défaut : recopiés depuis la `Question` et son `AnswerType` ;
- les `AnswerValue` sont **dupliqués** (`answerValueRepository.copy`) et rattachés à l'exemplaire ;
- `isRequired`, `isPrivate`, `isConditional`, `summary` : recopiés depuis la `RangeQuestion`.

Une question déjà générée n'est **jamais** mise à jour : la méthode sort dès qu'elle trouve
l'exemplaire. Modifier le catalogue ne rejaillit pas sur les interventions déjà planifiées.

Tri : `Comparator.comparing(RangeQuestion::getOrderSeq)` — appliqué **à l'intérieur de paquets de 20**
(`Lists.partition(ids, 20)`), sur une liste issue d'une requête **sans `ORDER BY`**.

## 6. Le conditionnement

Trois contraintes, dont deux seulement sont contrôlées par l'écran :

1. **Type liste** — le domaine de `conditionalRangeQuestion` est
   `self.question.answerType.answerTypeSelect = 'list'`.
2. **Même gamme** — le même domaine impose `self.rangeVal.id = <la gamme courante>`.
3. **Ordre strictement croissant** — `action-range-question-condition-check-order-seq`, à
   l'enregistrement : *« The order must be strictly greater than the conditional question's order »*.

Aucune des trois n'est contrôlée à l'import CSV.

L'appariement à la génération se fait **par le nom du choix** :
`findInterventionQuestionAnswerValue` cherche, parmi les copies rattachées à la question pilote, celle
dont `getName()` est égal. Deux choix homonymes dans un même `AnswerType` rendent le conditionnement
indéterminé.

À l'exécution, `InterventionQuestionHelper.isActive` : une question conditionnée est active si la
pilote a une réponse **et** que cette réponse est dans l'ensemble déclaré. Une conditionnée sans
pilote ou sans ensemble est inactive — donc jamais obligatoire. Elle n'est **pas** masquée pour autant :
le client web l'affiche (teintée en violet si elle a été enregistrée une fois) — voir `SKILL.md`, règle de
conception 2.

## 7. Le suivi : non-conformité et à-suivre

`InterventionHelper.computeTag`, rappelée à chaque enregistrement d'une réponse
(`InterventionQuestionManagementRepository`) et en fin de génération :

- `Intervention.following` ← vrai s'il existe **une** réponse dont le choix porte `following` ;
- `Intervention.nonConforming` ← le **nombre** de réponses dont le choix porte `nonConforming`.

Les deux requêtes joignent `listAnswer` : **seules les réponses de type liste comptent**. Une
non-conformité exprimée par une case à cocher ou un texte ne remonte nulle part.

## 8. Pièges

**P1 — Ordre non déterministe.** `orderSeq` à 0 partout (le défaut) : le tri ne discrimine rien, la
requête source n'a pas d'`ORDER BY`, et le tri se fait par paquets de 20. Vérifié en base : les 13
`RangeQuestion` du jeu de démo AOS ont toutes `order_seq = 0`. Toujours numéroter.

**P2 — Les données de démo AOS violent la règle d'ordre.** `RQ13` est conditionnée par `RQ12`, les
deux à `order_seq = 0` — l'écran refuserait cet enregistrement, l'import l'a accepté. Preuve que le
chemin CSV ne passe par aucun contrôle de vue.

**P3 — `importId` 1..13 occupés.** Le jeu de démo AOS pose `import_id` `1`…`13` sur `Question`,
`RangeQuestion`, et `1`…`9` sur `AnswerType`, `1`…`12` sur `AnswerValue`, `1`…`4` sur `Range`,
`RangeType`, `OrderedRange`, `InterventionCategory`. Les binds de démo cherchent par
`self.importId = :importId` : un bundle numéroté à partir de 1 **écrase** ces lignes. Vérifié
présent sur huit bases AOS 9.1.x (un socle vierge et sept bases de démo). Préfixer.

**P4 — Gamme muette.** `family` avec `equipmentFamilySet` vide → la liste de familles retenues est
vide → aucun bloc généré. `equipment` avec `equipmentFamily` nul → bascule dans la branche standard,
donc un bloc **sans** équipement, ce qui n'est pas ce qui était demandé. Aucun message dans les deux
cas.

**P5 — Le code séquence est la clé de rattachement.** `RangeQuestion.sequence` est posé par la
séquence AOP `range.question.sequence` (`RQ1`, `RQ2`…). Supprimer puis réimporter les
`RangeQuestion` leur donne de nouveaux codes ; les interventions déjà planifiées ne reconnaissent
plus leurs questions et une nouvelle génération **les ajoute en double**.

**P6 — La séquence AOP, elle, est bien posée à l'import.** Nuance à une idée répandue (« le moteur d'import ne
remplit ni la namecolumn ni la séquence ») : une séquence déclarée **au domaine** (`<string sequence="…">`) est
affectée par un écouteur Hibernate
(`AuditListener.onPreInsert` → `JpaSequence.nextValue`), hors chaîne de repository — donc le moteur
`com.axelor.data` la remplit. C'est la séquence **AOS par service** (type `Partner.partnerSeq`) qui
ne l'est pas. Même remarque pour la namecolumn : `RangeQuestion.title` est un champ **calculé au
domaine** et il est bien rempli à l'import (vérifié en base). Fournir malgré tout la valeur dans le
CSV reste préférable pour un bundle rejouable : l'écouteur ne pose la séquence que si la valeur
arrive nulle.

**P6bis — Clé de recherche : le code métier, pas l'importId, pour tout ce qui préexiste.**
Vérifié sur `<base>` (AOS 9.1.6) : la base porte déjà les catégories `AFF`/`MTN`/`SAV`/`TLM`
et les types `MTN`/`PAN`, tous marqués `import_id` 1..4 par le jeu de démo AOS. Un `<input>` sur
`InterventionCategory` cherchant par `importId` y crée une **seconde** catégorie « Maintenance » ;
sur `InterventionType`, dont `code` est `unique="true"` au domaine, la ligne échoue sur la
contrainte. Et écrire un `importId` sur une ligne préexistante la re-marque, ce qui casse la
recherche du bundle qui l'avait posée. Règle : **ce que le bundle crée** se cherche par `importId`
préfixé ; **ce qu'il référence sans le créer** — catégorie, type, famille d'équipement, unité — se
cherche par son code ou son nom, et ne reçoit pas d'`importId`.

**P7 — Aucune impression native.** Le module ne livre aucun modèle BIRT ni Carbone du relevé. Le
panneau « Rapport » de la fiche intervention porte le suivi commercial, pas une impression. Le rendu
natif est la grille `intervention-question-grid` (groupée par bloc, `orderBy` bloc puis ordre, avec
un code couleur par état) ou l'app mobile.

**P8 — Ordre des choix.** La liste des réponses est triée par `AnswerValue.sequence` (`x-order` sur
le champ). Le jeu de démo laisse toutes les valeurs à 0. Numéroter.

**P9 — Type `indication` jamais « répondu ».** `InterventionQuestionHelper.isAnswered` ne connaît pas
`indication` : une question d'indication marquée obligatoire ne pourra jamais passer à l'état
répondu. Ne pas la marquer obligatoire.

**P10 — La case « gamme privée » ne fait rien.** `Range.isPrivate` est affiché dans la grille et
le formulaire de la gamme, et **aucun service d'AOS ne le lit** : `grep -rn 'getIsPrivate' --include=*.java`
sur tout l'arbre AOS 9.0.13 rend deux occurrences, toutes deux sur `RangeQuestion` /
`InterventionQuestion`. Le cloisonnement réel se pose question par question
(`RangeQuestion.isPrivate`, recopié dans l'exemplaire et lu par
`InterventionQuestionHelper` pour l'état `PRIVATE`). Cocher la case au niveau de la gamme donne
un faux sentiment de confidentialité.

## 9. Spécification YAML

Consommée par `scripts/build_survey_bundle.py`.

```yaml
code: MES                        # obligatoire, [A-Z0-9-]+, préfixe de tous les importId
label: Mise en service chaudière # facultatif, documentaire

intervention_type:               # facultatif : sans lui, aucune gamme n'est rattachée
  code: MES
  name: Mise en service
  category: { code: MTN, name: Maintenance }

ranges:
  - title: Arrivée sur site
    block: header                # header | equipment | footer | startup
    type: standard               # standard | equipment | family
    families: []                 # obligatoire si type = equipment (une) ou family (une ou plusieurs)
                                 # valeurs = codes d'EquipmentFamily DÉJÀ présents dans la base cible
    private: false
    description: ""
    questions:
      - title: État du site à l'arrivée
        answer: liste[Conforme, Non conforme!nc]
        required: true           # défaut false
        private: false           # question visible de l'intervenant seul
        summary: false           # remontée dans le récapitulatif de fin
        indication: ""           # aide affichée sous l'intitulé
      - title: Détail de l'écart
        answer: texte
        if: { question: "État du site à l'arrivée", answers: ["Non conforme"] }
```

**Grammaire du champ `answer`** — un type, éventuellement paramétré :

| Écriture | AnswerType produit |
|---|---|
| `liste[A, B, C]` | `list` avec trois choix, dans cet ordre |
| `liste[Conforme, Non conforme!nc]` | `!nc` pose `nonConforming` sur le choix |
| `liste[OK, À revoir!suivi]` | `!suivi` pose `following` |
| `liste[A!def, B]` | `!def` pose `isDefault` |
| `texte` / `texte("valeur par défaut")` | `text` |
| `date` | `date` |
| `photo` | `picture` |
| `signature` | `signature` |
| `mesure(kg)` | `measure` avec l'unité de nom `kg` (elle doit exister en base) |
| `case("Libellé de la case")` | `checkbox` |
| `indication("Texte affiché")` | `indication` |
| `suivi_avance` | `advancedMonitoring` — liste FIGÉE domicile / agence / intervention précédente / suivante, qui remplit une adresse automatiquement. N'a de sens que dans une gamme `block: startup` |

Les `AnswerType` sont **factorisés automatiquement** : deux questions qui déclarent exactement le
même type et les mêmes choix partagent un seul `AnswerType`. Deux listes de mêmes libellés mais de
drapeaux différents donnent deux types distincts — c'est voulu.

Le champ `if` produit le conditionnement. Le script vérifie que la pilote est dans la même gamme,
qu'elle est de type liste, que les réponses citées existent, et il place la conditionnée après elle.

## 10. Le jeu de démo AOS comme gabarit

`axelor-intervention/src/main/resources/apps/demo-data/{fr,en}/` + `intervention-config.xml`.
Neuf fichiers pour la chaîne questionnaire, tous en `;`, tous avec une colonne `importId` :

`intervention_answerType.csv`, `intervention_answerValue.csv`, `intervention_question.csv`,
`intervention_rangeType.csv`, `intervention_range.csv`, `intervention_rangeQuestion.csv`,
`intervention_orderedRange.csv`, `intervention_interventionCategory.csv`,
`intervention_interventionType.csv`.

Deux conventions de colonne y cohabitent, les deux fonctionnent :
`question_importId` (liée explicitement par un `<bind>`) et `rangeVal.importId` (résolue
implicitement par le binder). Le script produit la forme pointée, avec un `<bind>` explicite quand
un contrôle de présence est utile.

Contenu livré : 4 gammes, 13 questions, 9 types de réponse, 2 types d'intervention
(Maintenance, Panne), 4 catégories. Sur les huit bases vérifiées, `intervention_intervention_range`
est **vide** : aucun questionnaire n'y a jamais été généré.

## Sources

- `axelor-intervention/src/main/resources/domains/{AnswerType,AnswerValue,Question,Range,RangeQuestion,RangeType,OrderedRange,InterventionType,InterventionQuestion,InterventionRange}.xml`
- `axelor-intervention/src/main/java/com/axelor/apps/intervention/service/InterventionSurveyGeneratorImpl.java`
- `.../service/helper/{InterventionQuestionHelper,InterventionHelper}.java`
- `.../service/InterventionServiceImpl.java:plan`, `.../events/InterventionObserver.java`
- `axelor-intervention/src/main/resources/views/{RangeQuestion,Range,InterventionQuestion,Selects,Menu}.xml`
- `axelor-core/src/main/java/com/axelor/db/audit/AuditListener.java:106` (séquence au domaine)
- Vérifications SQL : un socle vierge et une base de démo construction, toutes deux AOS 9.1.6
