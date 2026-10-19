---
name: seeding-axelor-intervention-surveys
description: >
  Modelise et livre un questionnaire d'intervention Axelor rempli par le
  technicien (gamme de controle, checklist terrain, fiche de mise en service,
  PV de verification, rapport de visite de maintenance) : chaine AnswerType,
  Question, Range, RangeQuestion, OrderedRange, InterventionType, livree en
  bundle d'import (bind XML + ZIP de CSV) sans rebuild du WAR ni acces base.
  Commence par cadrer le besoin (questions conditionnelles, non-conformites,
  blocs par equipement). Sert aussi a auditer un questionnaire qui sort dans le
  desordre, a blocs vides ou a questions conditionnelles qui n'apparaissent
  jamais. Declencheurs : « questionnaire d'intervention », « gamme de
  controle », « checklist terrain », « PV de verification », « points de
  controle », intervention survey, checklist. PAS pour : savoir si la GMAO
  AxENR sait faire quelque chose (gmao-capabilities), controle qualite produit
  (axelor-quality), formulaire Studio, enquete de satisfaction client.
metadata:
  owner: axenr
  family: fonctionnel
---

# Questionnaires d'intervention Axelor

> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur : moteur lu dans les
> sources AOS 9.0.13 (relu en 9.1.7 sur deux points), observé à l'écran en AOS 9.1.4 / AOP EE
> 8.2.3 ; la version actuelle du script n'a pas encore de preuve d'import de bout en bout. AxENR
> tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier.

## Environnement d'exécution

| Où | Comportement |
|---|---|
| claude.ai et Cowork | Pas d'accès à la base : cadrer le besoin (Phase 1), écrire la spécification YAML (Phase 2), produire les CSV et le `bind.xml` en appliquant les contrôles de `scripts/build_survey_bundle.py`, fournir les requêtes de contrôle de la Phase 4 à lancer par l'utilisateur. |
| Claude Code | `python3 scripts/build_survey_bundle.py <spec.yaml> --out <dossier>` (PyYAML requis) ; contrôles SQL en lecture seule si `psql` est disponible. |

Première importation sur une instance jetable ou de recette, jamais directement en production.

## Contexte AxENR

- Dans la GMAO AxENR, ces questionnaires sont les **gammes d'intervention** : types de réponse
  photo et signature (technicien et client) en standard, gammes par **famille d'équipement**
  (onduleur, borne, pompe à chaleur…). Rester générique multi-ENR dans les libellés.
- Vérifier d'abord que l'instance porte le module `axelor-intervention` standard et sur quelle
  version : la GMAO AxENR peut l'étendre, et les noms de tables ou de champs des contrôles de la
  Phase 4 sont à confirmer sur la base cible.
- Le `bind.xml` généré référence le schéma `data-import_8.2.xsd` : sur AOP 7.4, reprendre la
  version de schéma d'un fichier de liaison existant de l'instance.
- Les rapports d'intervention (docx) générés à partir des gammes relèvent de
  `axenr-template-expert`.

## Mission

Produire un questionnaire d'intervention complet et cohérent dans une base Axelor, livré sous forme
de bundle d'**Import Configuration** : un fichier de liaison `bind.xml` + un `.zip` de CSV, importable
depuis *Administration > Configurations d'import* sans recompiler le WAR et sans accès à la base.

Le moteur visé est celui du module `axelor-intervention` : c'est le seul moteur de questionnaire
générique d'AOS, et il est **déclaratif** — tout se joue dans le catalogue, rien dans du code.

Deux moitiés, également importantes :

1. **Cadrer** le besoin avec l'utilisateur (§ Phase 1). Les contraintes du moteur se décident à la
   modélisation ; une fois le questionnaire généré sur une intervention, on ne les rattrape pas.
2. **Produire** un bundle déterministe et rejouable (§ Phase 3), avec le script fourni plutôt qu'à
   la main : les erreurs coûteuses de ce moteur sont toutes silencieuses.

## Ce que ce skill couvre — et ce qu'il ne couvre pas

**Couvert** : le questionnaire rempli par un intervenant sur une intervention (terrain, atelier,
télémaintenance), attaché à un type d'intervention, éventuellement déroulé par équipement.

**Non couvert, et il faut le dire au lieu de produire un bundle inadapté** :

| Le besoin réel est… | Le bon moteur | Signal |
|---|---|---|
| contrôler un **produit** en réception ou en fabrication | `axelor-quality` (ControlPlan / ControlPoint / Characteristic) | on parle de tolérances, d'échantillons, de caractéristiques mesurées sur un article, pas de visite |
| un **formulaire libre** posé sur n'importe quelle fiche | champs json Studio (`json-o2m`) | le questionnaire n'est pas rempli lors d'une intervention |
| une **enquête de satisfaction** envoyée à un client | module Survey EE, ou campagne marketing | le répondant n'est pas un intervenant Axelor |

Si le besoin relève d'une de ces lignes, dis-le en une phrase et arrête-toi là.

## Prérequis

| Il faut | Obligatoire ? | Sans cela |
|---|---|---|
| Python 3 et PyYAML (`pip install pyyaml`) | oui, pour `scripts/build_survey_bundle.py` | le script ne tourne pas (il le dit et s'arrête) ; écrire les CSV à la main est possible mais déconseillé : ses contrôles existent pour des erreurs déjà commises |
| Une instance AOS avec le module `axelor-intervention` et son app activée (voir « Activer l'app » en fin de fichier) | oui | rien où importer |
| Un compte administrateur avec accès à *Administration > Configurations d'import* | oui, pour la livraison | — |
| `psql` en lecture sur la base cible | non : contrôles SQL de la Phase 4 | mêmes vérifications par les écrans de configuration (Gammes, Questions, Types d'intervention) ; le test à l'écran reste le contrôle décisif |
| `AskUserQuestion` (outil intégré de Claude Code) | non : Phase 1 | poser les mêmes questions en texte et attendre les réponses |
| Skills `axelor-import-export` et `demo-data-generator` | non : renvois | le script produit un bundle conforme au moteur ; un journal d'import vert ne prouve rien (Phase 4 : contrôler en base et à l'écran) ; sans `demo-data-generator`, peupler la base par ta procédure habituelle |
| Sources AOS du module `axelor-intervention` (`github.com/axelor/axelor-open-suite`) ou jars du WAR déployé | non : relire une règle du moteur | les règles portent la version et la date où elles ont été relevées (`references/moteur-questionnaire.md`) ; les re-tester sur une autre version |

## Le modèle en trois couches

Lire `references/moteur-questionnaire.md` avant de concevoir : la carte complète du moteur,
les 9 types de réponse, la mécanique de génération et le catalogue des pièges y sont.

Le minimum à avoir en tête :

- **Catalogue réutilisable** — `AnswerType` (le widget : liste, texte, date, photo, mesure, case,
  indication, signature) porte aussi l'unité, le libellé de case et le texte d'indication ;
  `AnswerValue` (les choix d'une liste, avec les drapeaux `nonConforming` / `following`) ;
  `Question` (l'intitulé + son AnswerType), globale et réutilisable.
- **La gamme** — `Range` (le questionnaire), `RangeQuestion` (la question *dans cette gamme* : ordre,
  obligatoire, privé, récap, conditionnement), `RangeType` (la multiplicité : une fois, une fois par
  équipement, une fois par famille d'équipement).
- **Le rattachement** — `OrderedRange` accroche les gammes à un `InterventionType` en trois blocs
  ordonnés : en-tête, équipement, pied.

La copie vers `InterventionRange` / `InterventionQuestion` se fait **à la planification** de
l'intervention ; le bouton « Ouvrir le questionnaire » ne s'active qu'à partir du statut *Démarrée*.

## Phase 1 — Cadrer le besoin

Six axes. Pose-les avec `AskUserQuestion` (en texte sur claude.ai), en deux ou trois questions groupées, pas six écrans.
Chaque axe existe parce qu'il décide d'un objet ou d'un drapeau qu'on ne peut plus changer après.

| Axe | Ce qu'on cherche | Ce que ça décide |
|---|---|---|
| **Finalité** | à quoi sert le questionnaire : preuve contractuelle, sécurité, relevé technique, satisfaction | signature obligatoire ou non, questions privées, récap |
| **Activité** | le métier et l'objet visité : chaudière, ascenseur, extincteur, borne, réseau | le vocabulaire des questions, et surtout si un **équipement** est en jeu |
| **Structure** | un seul bloc, ou un déroulé en-tête / par équipement / pied | `RangeType` et les trois listes d'`OrderedRange` |
| **Rendu** | où l'intervenant répond : écran web, app mobile ; ce qui doit ressortir en fin de visite | les types de réponse utilisables, le drapeau `summary` |
| **Suivi** | ce qui doit **alerter** : non-conformité, point à revoir plus tard | impose des questions de type **liste**, seul type qui porte les drapeaux |
| **Volume** | nombre de questions, questions conditionnelles, réutilisation entre gammes | découpage en gammes, et le besoin ou non de conditionnement |

Avant d'écrire la spécification, relever dans la base cible ce que le bundle va **référencer sans
le créer** : codes de familles d'équipement, noms d'unités, code de la catégorie d'intervention, et
l'absence du code de type d'intervention visé. Une référence non résolue ne produit aucun message.

Deux questions à poser explicitement, parce que l'utilisateur ne les anticipe jamais :

- **« Y a-t-il des questions qui n'apparaissent que si une autre a telle réponse ? »** Le
  conditionnement n'existe que sur une question à choix (liste), dans la **même gamme**, et la
  question conditionnée doit venir **après** la pilote. Si la réponse est oui, il faut la capturer
  maintenant.
- **« Une non-conformité doit-elle remonter sur l'intervention ? »** Si oui, la question doit être
  une liste et c'est le **choix** (pas la question) qui porte le drapeau.

Reformule le cadrage en une dizaine de lignes et fais-le valider avant de produire quoi que ce soit.
Un questionnaire mal cadré se voit à l'écran, tard, devant le client.

## Phase 2 — Écrire la spécification

La conception s'écrit dans un fichier YAML unique, que le script transforme en bundle. Le gabarit
commenté est dans `assets/questionnaire.example.yaml` ; le format complet est documenté dans
`references/moteur-questionnaire.md` § Spécification.

Forme courte :

```yaml
code: MES                       # préfixe d'espace de nommage des importId — obligatoire
intervention_type:
  code: MES
  name: Mise en service
  category: { code: MTN, name: Maintenance }
ranges:
  - title: Arrivée sur site
    block: header               # header | equipment | footer | startup
    type: standard              # standard | equipment | family
    questions:
      - title: État du site à l'arrivée
        answer: liste[Conforme, Non conforme!nc]
        required: true
      - title: Photo d'ambiance
        answer: photo
```

Quatre règles de conception qui évitent l'essentiel des reprises :

0. **Une gamme ne dépasse pas 20 questions.** Au-delà, l'ordre d'affichage casse — observé le
   14/09/2026 : sur une gamme de 23 questions parfaitement numérotées, trois se sont retrouvées en
   fin de bloc. Le générateur trie par paquets de 20 sur une requête sans tri. Découper en deux
   gammes, ce qui donne d'ailleurs deux blocs plus lisibles.

1. **Une question = un intitulé + un type de réponse.** Si deux questions ont besoin de libellés de
   case ou de textes d'indication différents, il leur faut **deux AnswerType** : ces libellés vivent
   sur le type de réponse, pas sur la question.
2. **Le conditionnement ne masque rien : libelle la question conditionnée en conséquence.** Sur le
   client web, une question conditionnée reste AFFICHÉE quand sa condition n'est pas remplie — elle
   est seulement non obligatoire et teintée en violet, et sa réponse est en lecture seule tant que la
   condition n'est pas remplie (lu dans les vues AOS 9.0.11 à 9.1.7, non observé à l'écran). « Si écart : références concernées » se lit
   correctement dans ce cas, « Références concernées » passe pour une erreur d'affichage. Ne jamais
   promettre un formulaire qui s'adapte aux réponses.
3. **Nomme les choix de façon unique dans un même type de réponse.** L'appariement d'une réponse
   conditionnelle se fait **par le nom du choix**, pas par son identifiant.
4. **Ne réutilise un AnswerType « liste » que si les drapeaux de non-conformité sont les mêmes.**
   Deux gammes qui ont besoin de « Conforme / Non conforme » avec des remontées différentes ont
   besoin de deux types.

## Phase 3 — Produire le bundle

```bash
python3 scripts/build_survey_bundle.py <spec.yaml> --out <dossier>
```

Le script produit `intervention-survey-bind.xml` et `intervention-survey-data.zip`, et **refuse de
produire** un bundle qui viole une contrainte du moteur (conditionnement hors liste ou hors gamme,
ordre incohérent, gamme « par famille » sans famille, choix homonymes). Ces contrôles existent parce
que l'import, lui, accepte tout : le journal affiche « Réussi » et le questionnaire est faux.

Il numérote systématiquement `orderSeq` et `sequence` des choix — laissés à zéro, l'ordre d'affichage
devient non déterministe, et c'est exactement le défaut que portent les données de démo AOS livrées
en standard.

Il préfixe tous les `importId` avec le `code` de la spécification (`MES-r1`, `MES-q3`…). C'est une
protection, pas une coquetterie : les données de démo d'AOS occupent les `importId` `1` à `13` sur
ces mêmes modèles, et un bundle numéroté à partir de 1 **écrase le questionnaire de démo** sur toute
base où il est chargé.

**Livraison** : import depuis *Administration > Configurations d'import*, type `csv`, fichier de
liaison = le `.xml`, fichier de données = le `.zip`. La mécanique du bundle, ses pièges de journal et
les règles d'idempotence sont portées par le skill `axelor-import-export` — s'y référer
plutôt que de les redécouvrir.

## Phase 4 — Contrôler

Le journal d'import est muet sur la complétude métier : trois compteurs verts décrivent très bien un
questionnaire inutilisable. Les contrôles qui comptent, en SQL lecture seule sur la base cible :

```sql
-- 1. Rien n'a écrasé les gammes existantes : les importId du bundle sont tous préfixés
SELECT import_id, title FROM intervention_range WHERE import_id LIKE 'MES-%';

-- 2. Aucun ordre laissé à zéro (ordre d'affichage non déterministe)
SELECT rq.id, rq.title FROM intervention_range_question rq
  JOIN intervention_range r ON r.id = rq.range_val
 WHERE r.import_id LIKE 'MES-%' AND COALESCE(rq.order_seq,0) = 0;

-- 2bis. Aucune gamme au-delà de 20 questions (au-delà, l'ordre d'affichage casse)
SELECT r.title, count(*) FROM intervention_range_question rq
  JOIN intervention_range r ON r.id = rq.range_val
 WHERE r.import_id LIKE 'MES-%' GROUP BY r.title HAVING count(*) > 20;

-- 2ter. Aucun conditionnement sans réponse déclenchante (sinon la question ne s'active JAMAIS)
SELECT c.id, c.title FROM intervention_range_question c
 WHERE c.is_conditional AND NOT EXISTS (
   SELECT 1 FROM intervention_range_question_conditional_answer_value_set s
    WHERE s.intervention_range_question = c.id);

-- 3. Toute question conditionnée pointe une pilote de la MÊME gamme, d'ordre inférieur
SELECT c.id FROM intervention_range_question c
  JOIN intervention_range_question p ON p.id = c.conditional_range_question
 WHERE c.is_conditional AND (p.range_val <> c.range_val OR p.order_seq >= c.order_seq);

-- 4. Les gammes sont bien accrochées au type d'intervention (sinon : questionnaire vide)
SELECT o.sequence, r.title,
       CASE WHEN o.intervention_type_header IS NOT NULL THEN 'en-tête'
            WHEN o.intervention_type_equipment IS NOT NULL THEN 'équipement'
            ELSE 'pied' END AS bloc
  FROM intervention_ordered_range o JOIN intervention_range r ON r.id = o.range_val
 WHERE r.import_id LIKE 'MES-%' ORDER BY o.sequence;

-- 5. Une gamme « par famille » sans famille ne produira RIEN, en silence
SELECT r.title FROM intervention_range r JOIN intervention_range_type t ON t.id = r.range_type
 WHERE t.range_type_select = 'family'
   AND NOT EXISTS (SELECT 1 FROM intervention_range_type_equipment_family_set s
                    WHERE s.intervention_range_type = t.id);
```

Le contrôle décisif reste l'écran : planifier une intervention du type visé, puis la démarrer, et
ouvrir le questionnaire. Tant que ce passage n'a pas été fait, dire « le questionnaire est en place »,
pas « il fonctionne ».

## Pièges du moteur

Détail et preuves dans `references/moteur-questionnaire.md` § Pièges. En résumé, tous silencieux :

1. **Conditionnement** : liste uniquement, même gamme, ordre strictement croissant. L'écran le
   contrôle à l'enregistrement ; **l'import ne le contrôle pas** — les données de démo AOS livrées en
   standard violent d'ailleurs la règle d'ordre.
2. **Ordre à zéro** = ordre d'affichage non déterministe, et le tri se fait par paquets de 20.
3. **Gamme « par famille » sans famille**, ou **« par équipement » sans famille de référence** : la
   gamme disparaît du questionnaire généré, sans message.
4. **Les drapeaux de suivi** (non conforme, à suivre) ne comptent que sur une réponse de type liste.
5. **Libellé de case, unité, texte d'indication, valeur par défaut** vivent sur l'`AnswerType`, pas
   sur la question : un libellé différent impose un type de réponse dédié.
6. **`importId` 1..13 sont occupés** par les données de démo AOS sur ces modèles.
6bis. **Ce que le bundle ne crée pas, il le cherche par son CODE métier** — jamais par `importId`.
   Catégorie, type d'intervention, famille d'équipement et unité préexistent en général dans la
   base cible. Chercher par `importId` une catégorie qui porte déjà le code visé en crée un
   **doublon** ; sur un type d'intervention, dont le code est unique, cela **viole la contrainte**.
   Et poser un `importId` sur une ligne qu'on n'a pas créée la re-marque : le bundle d'origine qui
   la cherchait par SON `importId` en fabriquera un doublon au passage suivant.
7. **La case « gamme privée » ne fait rien** : `Range.isPrivate` n'est lu par aucun service. Le
   cloisonnement se pose question par question.
8. **Aucun type de réponse ne saisit une heure** : « date » est une date seule, et il n'existe ni
   heure ni date-heure. Passer par une question texte avec le format en indication.
9. **Une liaison à plusieurs valeurs ne s'importe pas sur une seule ligne** : le moteur d'import ne
   découpe jamais sur « | », et une m2m multivaleur arrive VIDE, en silence. Le script produit donc
   une ligne par réponse déclenchante.
10. **Regénérer après coup** : le rattachement d'une question déjà générée se fait par le code
   séquence de la `RangeQuestion` (`RQ12`…). Réimporter un bundle qui recrée ces lignes avec de
   nouveaux codes fait **doubler** les questions des interventions déjà planifiées.

## Anti-patterns

- Produire un bundle avant d'avoir fait valider le cadrage : le coût d'un questionnaire faux se paie
  devant le client, pas devant l'écran d'import.
- Écrire les CSV à la main « parce que c'est simple » : les six contrôles du script existent tous
  pour une erreur déjà commise.
- Promettre une impression du questionnaire : le module ne livre **aucun modèle d'impression** du
  relevé. Le rendu natif est la grille web groupée par gamme, ou l'app mobile.
- Conclure « ça marche » sur un journal d'import vert.

## Voir aussi

- **Activer l'app** : activer l'app Intervention en installe d'autres. `AppServiceImpl.installApp` parcourt `studio_app_depends_on_set`
  récursivement et installe toute la chaîne sans la demander. Mesuré le 2026-09-04 (AOS 9.1.6 / AOP EE 8.2.4 build local, base de démo) :
  `intervention` dépend de `contract` ET `employee`, soit trois apps installées dont deux ouvrent des menus racine. Sur une base dont la
  recette est figée, lister la chaîne AVANT d'activer :
  ```sql
  SELECT a.code AS app, d.code AS depend
    FROM studio_app_depends_on_set s
    JOIN studio_app a ON a.id = s.studio_app
    JOIN studio_app d ON d.id = s.depends_on_set
   WHERE a.code = 'intervention';
  ```
  La colonne de jointure s'appelle `depends_on_set`, pas `depends_on`.
- `axelor-import-export` (skill) — mécanique du bundle, journal, idempotence.
- `gmao-capabilities` (skill) — ce que la GMAO AxENR sait faire en standard, en paramétrage ou en roadmap.
- `demo-data-generator` (skill) — si le besoin réel est de peupler une base, pas de modéliser un questionnaire.
