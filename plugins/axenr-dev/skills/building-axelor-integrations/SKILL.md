---
name: building-axelor-integrations
description: >-
  Cadrer, verifier, specifier, construire et chiffrer une interface entre Axelor
  (AOS/AOP) et un outil tiers : connecteur API vers un SaaS (RH, paie, signature,
  banque, fournisseur, punch-out) ou flux de fichiers (releves bancaires, export
  paie ou cabinet comptable), y compris verifier qu'un connecteur existant couvre
  vraiment les flux annonces au client, ou decider si le travail peut etre
  delegue a un modele plus petit. Livre un emulateur HTTP, un client REST et des
  controles SQL en lecture seule. Declencheurs : « connecteur », « interface
  avec », « synchronisation », « API tierce », « flux de fichiers », « webhook »,
  « chiffrer un connecteur » ; integration, connector, third-party API, sync,
  emulator, mock API. PAS pour : un import ponctuel de donnees sans outil tiers
  derriere (axelor-import-export), le peuplement d'une base de demo
  (demo-data-generator), les droits d'acces (axelor-droits-expert).
metadata:
  owner: axenr
  family: technique
---

# Building an interface between Axelor and a third-party tool

Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.7 / AOP EE 8.2.3 et 8.2.4, de bout en
bout contre des émulateurs de l'API tierce, jamais contre un service réel. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque
piège est une hypothèse à vérifier.

**Mise en garde :** après « Tout restaurer… » (Administration > Gestion des vues > Les Vues, rechargement des
métadonnées), environ une requête sur dix s'exécute sous l'identité `admin` jusqu'au redémarrage (mesuré sur AOP 8.2.2).
Redémarrer Tomcat immédiatement après ; pour recharger les vues d'un module, préférer le rechargement ciblé décrit dans
`references/pitfalls.md` (« New views or translations missing after a redeploy »).

## Contexte AxENR

| Point | Chez AxENR |
|---|---|
| Versions | AOP 7.4 / AOS 8.x : la ligne « AOS 9 / AOP 8 : Java 21, `javax.*` → `jakarta.*` » de `references/environment-and-proof.md` ne s'applique pas. Compiler contre la version du projet client (`gradle.properties`, `gradle/libs.versions.toml`) et ne jamais modifier `JavaLanguageVersion` (LESSON-030) |
| Connexion REST | Session par cookie ouverte par l'utilisateur dans son propre terminal : `AXELOR_USER` exporté, mot de passe sur l'entrée standard de `scripts/axelor_rest.py`. Le mot de passe ne passe jamais par la conversation ni par un fichier |
| Environnement de test | Base jetable ou copie, jamais une base de recette client sans feu vert explicite. Monter l'environnement avec `provisioning-axelor-environments` |
| Livraison | Le module est ajouté aux dépendances de l'application, qui est reconstruite (jamais un jar déposé dans un WAR construit). Pas de nom de client dans un module partagé, tests compris |
| Données | Un import ponctuel de référentiel sans outil tiers relève de `axelor-import-export`, pas de ce skill |

## Why this skill exists

On a real connector project (an HR SaaS connector, AOS 9.1.7 / AOP EE 8.2.3), an agent ported an existing connector
from AOS 8.5 to 9.1 in about 45 minutes, then built four missing flows in 2 h 16 — 62 unit tests, 44 batch runs checked
object by object in the database — against an emulator built from the tool's public documentation. Estimates made at
human pace did not apply to that part. What made it work was the order of the steps, four rules, and pitfalls already
known. This skill makes that repeatable for any third-party tool.

## Four rules

1. **Proof is in the database, not in a counter.** "Processed: 12" proves nothing; the expected Axelor object, read back
   from the database with the right values, does.
2. **Every third-party field cites its documentation page.** A field the docs do not show is marked "to confirm" and the
   code tolerates its absence; it is never invented.
3. **Emulate the tool instead of waiting for access.** Results are reported as "validated against the emulator built from
   the docs"; validation on the real service is a human task, estimated separately.
4. **Measure agent time; estimate the human remainder separately.** Real timestamps only, nothing dated in the future.

## Prerequisites

| Need | Required? | Without it |
|---|---|---|
| Python 3 (standard library only: `mock_api.py`, `axelor_rest.py`, `db_check.py`, `junit_summary.py`) | yes | the emulator, the REST driver and the checks cannot run |
| `psql` (PostgreSQL client) and a disposable copy of a database | yes, for `db_check.py` and the database proof (rule 1) | no database proof: report the flow as « not verified in the database », never as validated |
| JDK 21, the Gradle wrapper of the application and of the module (for EE modules: the enterprise Maven repository credentials, as Gradle properties) | yes, to compile and deploy; `rebuild_and_deploy.sh` also needs `unzip`, `pgrep` and a standalone Tomcat | steps 0 to 3 (framing, contract, mapping, emulator) still work; nothing is reported as run on Axelor |
| A sacrificial AOS / AOP environment (application + database copy) and its owner's go-ahead | yes, for steps 4 and 5 | specification and emulator only |
| A login on that environment for `scripts/axelor_rest.py`: `AXELOR_USER`, and the secret on standard input (or `AXELOR_PASSWORD` on a disposable environment only: to be set by the user in their own terminal; never paste the password into the conversation) | for REST configuration and batch runs | configure through the screens, then check in the database as usual |
| Write access to the connector repository, and `glab` or `gh` for merge requests | no | step 6 falls back to a patch series (`git format-patch`) handed to a developer of the repository |
| An AOS ↔ AOP ↔ module version catalogue, for example a `version-matcher` MCP server | no | read `gradle.properties`, `settings.gradle` and the `build.gradle` of the application, the Axelor changelog and the versions published on Maven; never guess a version |

## Workflow

Keep a `TASKS.md` in the working folder. Steps marked **[decision]** wait for the person who owns the decision.

### 0 — Frame the flows (`references/framing.md`)
One sheet per flow: direction, master data, trigger, frequency, scope, matching key, lifecycle, effects inside Axelor,
volume and quotas, errors and retries, security, test environment, acceptance, what was already promised or estimated.
Look up what can be found (requirements, tickets, minutes, code) before asking anything.
**[decision]** scope, master data, what happens to an unmatched record, and the **vehicle** (native import, native
accounting format, n8n, Studio/BPM, Java connector module): present at least two options with their consequences.

### 1 — Inventory what exists (`references/framing.md` § 4)
Existing connector (search the Git server by the tool's name), its branches and AOS versions, the customer it was built
for; flow by flow, what the code does (`file:line`) and a verdict covered / partial / missing; what standard AOS or EE
already offers. Check **write access to the connector repository** now (role, forking allowed): it decides how delivery
will work.
**[decision]** when a flow announced as "native" is missing or partial: report it flow by flow, separating real gaps,
features never estimated, and internal tooling costs (version ports).

### 2 — Contract and mapping (`references/contract-and-emulator.md`)
Per-route contract from the public docs (authentication, envelope, paging, schema, errors, quotas), each with its URL;
contradictions between doc pages noted. Field-by-field mapping to the AOS entities of the target version, with
`file:line` in the AOS sources. Customer-specific values (axis numbers, statuses, codes) become settings.

### 3 — Emulator (`scripts/mock_api.py`, example `scripts/mock_scenario_example.py`)
The exact routes the connector calls; a base data set and one set per family of edge cases; failures (429, 400, 5xx,
silent server); request validation that rejects what the docs reject (missing required field, wrong status transition).
The emulator journal is the proof of what the connector sends. The deliverable carries everything needed to run it:
copy `mock_api.py` next to the scenario and give the start command.

### 4 — Compile, then set up a disposable environment (`references/environment-and-proof.md`)
Compile against the AOS version of the **customer's application** (commonly Java 21, AOP 8, `javax` → `jakarta`).
**[decision]** starting an environment needs the owner's go-ahead. Copy the application of a sacrificial environment whose
stack contains the module's dependencies, clone its database, handle the licence row before the first start, record the
environment wherever the workspace keeps its environment inventory. A module that extends AOS entities is integrated by
**rebuilding the application** with it (`scripts/rebuild_and_deploy.sh`), not by dropping a jar into a built WAR.

### 5 — Build, flow by flow
Tests first (`scripts/junit_summary.py`), then code, emulator, publish-rebuild-start, configuration through the REST API
(`scripts/axelor_rest.py`), batch run, **database check** (`scripts/db_check.py`), fix, replay the same scenario. A flow
is done when its edge cases are proven in the database; replay every flow at the end. Report the actual output of the
test and check runs; a run that could not be executed is reported as such. Decisions go to an arbitration file: a
non-blocking one becomes a setting with a recommended default marked "provisional"; a blocking one is a **[decision]**.

### 6 — Estimate and deliver (`references/estimate-and-delivery.md`)
Measured agent time per flow; human remainder per task (code review, real third-party validation, customer settings,
acceptance, go-live). MR in English, short, split (version port, then one flow per commit or MR); without write access,
an MR request to a repository developer with a verified patch series. For a module shared between customers, list each
behaviour change for the other customers. Run the repository's pre-push metadata checks when it has any.

### 7 — Hand back and capitalize
Stop the environment and the emulator; record the database state the tests left. New pitfalls go into
`references/pitfalls.md`.

## Delegating (`references/delegation.md`)

The coordinator frames, settles decisions with the owner, and reviews; execution is delegated. Bounded units (one route
contract, transfer objects, mapping rows, emulator data sets, database expectations) suit a small model; building a flow
suits a mid-size or large model; an adversarial review by a model with a fresh context catches what the builder no longer
sees. The execution prompt follows the template in `references/delegation.md` § 3. Re-check key figures (test counts,
timestamps, environment state, objects in the database) before reporting them.

## Pitfalls

`references/pitfalls.md`, worth reading before step 4 and before delivery. The costliest ones: a jar dropped into a built
WAR (Hibernate `mappedBy` failure), a 4xx answer read as an empty success, an empty third-party field erasing Axelor
data, an unmatched reference skipped silently, AOS versions forced by the module, a missing write access discovered at
push time, an emulator that accepts what the real service refuses.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/mock_api.py` | Generic HTTP emulator: routes from a scenario file, switchable data sets, injected failures, journal |
| `scripts/axelor_rest.py` | Axelor REST driver: login (from `AXELOR_USER`, secret on stdin; no default account), search, save, action, wait for a batch, traces |
| `scripts/db_check.py` | Read-only database checks from a JSON expectations file (connection through the standard `PG*` variables); exit code 1 on any failure |
| `scripts/rebuild_and_deploy.sh` | Publish the module, rebuild the application, redeploy it keeping the environment config |
| `scripts/junit_summary.py` | JUnit summary; fails when no test ran |
