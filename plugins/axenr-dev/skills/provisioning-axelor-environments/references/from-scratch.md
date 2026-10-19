# Assembler un environnement Axelor from scratch, ou auditer sa dérive

Référence du skill `provisioning-axelor-environments`. À lire quand la cible est une combinaison de versions et de
modules qu'aucun environnement existant ne porte, ou quand on audite la dérive d'un environnement livré. Les chemins
`scripts/` et `references/` sont relatifs au dossier du skill.

## Prérequis

**Obligatoires**

| Outil | Rôle dans ce skill |
|---|---|
| `bash` (script `scripts/probe-env.sh`) | exécution des probes rouge/vert |
| `curl`, `python3` | probes runtime (HTTP, décodage JSON de `menu/all` et `meta/view`) |
| `unzip` | probes WAR (`unzip -l` sur `WEB-INF/lib`) |
| `grep`, `sed`, `awk`, `find` | probes statiques sur `build.gradle`, `gradle.properties`, `axelor-config.properties` |
| `psql` (client PostgreSQL) + un serveur joignable | probes `--db` et probes runtime R4/R5/R6 ; création de la base neuve |
| JDK 21 et `./gradlew` de l'app donneuse | build du WAR |
| Identifiants du dépôt Maven entreprise d'Axelor (`axelorMavenUsername` dans `~/.gradle/gradle.properties`, ou variable `ORG_GRADLE_PROJECT_axelorMavenUsername`) | résolution des modules EE ; probe S9 |
| Une app Axelor qui boote déjà (le « donneur ») | on clone sa recette de build, on n'en écrit jamais une à la main |

**Optionnels, et ce qui se passe sans eux**

| Outil | Rôle | Sans lui |
|---|---|---|
| MCP `version-matcher` | résoudre AOS → AOP → modules, lister les versions publiées | lire `gradle.properties` / `settings.gradle` / `build.gradle` du donneur, le changelog AOS et les versions publiées sur le dépôt Maven ; la règle « aucune version devinée » reste entière |
| Plugin `axelor` (`axelor:setup`) | cloner les dépôts sources d'un projet | cloner et initialiser l'app à la main depuis le webapp template Axelor |
| Service Elasticsearch / OpenSearch | uniquement si `flag.elasticsearch = true` | laisser le flag à `false` ; les probes W4/R7/S13 sont alors ignorées |
| Registre d'envs de l'équipe (fichier texte) | contrôle de collision de nom de base (probe S8c) | la probe S8c est ignorée (`PROBE_REGISTRY_FILE` non défini) |
| `ss`, `fuser` | contrôle de port à la fermeture d'un env jetable | `curl` sur l'URL tranche ; vérifier que l'outil existe avant d'interpréter un silence |

## Division du travail avec le corps du skill

| Besoin | Skill |
|---|---|
| Reproduire un env existant (worktree, MR, démo jetable) | `SKILL.md` (patterns A, A-bis, B) |
| **Assembler une pile qui n'existe nulle part** (versions + modules + flags choisis) | **cette référence** |
| **Auditer la dérive d'un env** (livré hier ou il y a 6 mois) | **cette référence** (probes seules) |
| Fix détaillé d'un piège attrapé par une probe | table « Erreurs fréquentes » de `SKILL.md` |

`SKILL.md` est l'**encyclopédie des pièges et de leurs fixes**. Cette référence les rend
**exécutables** : chaque piège devient une probe, et la même suite sert trois fois —
pendant le provisionnement (TDD), à la livraison (recette), et plus tard (audit de dérive).

## Principe : le manifest est l'oracle, les probes sont les tests

On ne « suit pas une checklist » : on écrit d'abord un **manifest d'intention**
(`env-manifest.properties`), puis on fait passer les probes du rouge au vert,
phase par phase. C'est du TDD appliqué à l'infra :

```
1. Manifest écrit          → probe-env.sh --static     : TOUT ROUGE (normal)
2. Clone + chirurgie       → --static                  : vert
3. Base créée              → --db                      : vert
4. ./gradlew build         → --war                     : vert
5. Boot (GATE utilisateur) → --runtime                 : vert
6. Livraison               → manifest archivé avec l'env + registre d'envs de l'équipe à jour
```

Une probe rouge n'est jamais « à voir plus tard » : c'est un piège documenté qui
coûtera des heures au runtime s'il passe. Fix (via `SKILL.md`), puis re-run
de la phase — jamais deux fixes d'affilée sans re-test.

## Phase 0 — Manifest d'intention

Copier `references/manifest-template.properties` à la racine du futur env et le
remplir. Deux règles non négociables :

1. **Aucune version devinée — et aucune version crue sur parole.** Résoudre via
   le MCP `version-matcher` s'il est disponible (`resolve_aos_version` →
   `get_aos_platform` → `get_module_version`), sinon depuis les sources
   (`gradle.properties` / `settings.gradle` / `build.gradle` du donneur, changelog
   AOS, versions publiées sur le dépôt Maven). Puis **recouper chaque module avec
   ce qui est réellement publié** (avec le MCP : `list_module_versions`, qui
   énumère les versions publiées ; sans lui : le listing Maven du module), et en
   cas de divergence laisser **la résolution Gradle** (`./gradlew dependencyInsight
   --dependency <artefact> --configuration runtimeClasspath`) puis le contenu du WAR
   trancher.
   Ce recoupement n'est pas de la prudence rituelle : les deux interrogations du
   matcher peuvent se contredire (index qui ne se rafraîchissent pas ensemble).
   Mesuré sur AOS 9.1.6 pour `axelor-e-invoicing`, `axelor-facturx` et
   `axelor-file-generator` : le 2026-08-28, `get_module_version` donnait `9.1.4`
   (`exactMatch: true`) alors que `list_module_versions` plafonnait à `9.1.2`
   (`axelor-cii` et `axelor-ubl`, eux, avaient bien une 9.1.4 : d'où l'illusion de
   cohérence) ; le 2026-08-30, `list_module_versions` listait `9.1.3` et `9.1.4`
   pour les trois (+6 versions publiées par module en deux jours : l'index de
   listage était en retard). Le défaut n'est pas lié à l'appel groupé — un appel unitaire
   répond pareil. Pin sur une version absente du dépôt = échec de résolution
   Gradle, ou pire, un fallback silencieux ; pin sous un plancher transitif =
   écrasé en silence (Gradle arbitre au plus haut).
   Une version EE devinée = capability conflict ou classes legacy au build.
   Attention : Les tags `~patch` EE ne sont **pas** binairement compatibles entre eux
   (signatures de ctor changent) : prendre la version exacte résolue pour LA
   version AOS cible (matcher ou sources), pas « la plus récente ».
2. **Distinguer plateforme open vs enterprise.** `target.platform.ee=true`
   signifie JARs `axelor-core-enterprise`/`axelor-web-enterprise` (l'AEP), pas
   l'AOP open au même numéro. C'est la plateforme EE qui porte
   hibernate-search/Elasticsearch, le moteur de workflow, l'IA.

Renseigner aussi les **flags** (`facturation-electronique`, `elasticsearch`,
`guardian`) : ils arment les probes conditionnelles.

## Phase 1 — Choisir le donneur (jamais écrire un build à la main)

La règle d'or de `SKILL.md` tient : **on ne réinvente jamais le build**. From
scratch ≠ from nothing — on clone la recette **la plus proche de la cible** puis
on opère. Choisir parmi les envs de l'équipe qui bootent (registre d'envs s'il
existe, sinon les apps Gradle disponibles localement) selon, dans l'ordre :

1. **Le donneur porte-t-il déjà les garde-fous qu'exigent mes flags ?** C'est le
   critère qui prime, parce qu'un garde-fou absent ne se voit pas : il se paie au
   runtime. Facturation électronique → les 2 excludes JAXB ; guardian → le
   `sourceSets` src-gen ; Groovy → le `force`/`exclude` du train. **Se répond par
   `grep`, jamais par la prose du registre** :
   ```bash
   grep -nE "jaxb-runtime|jaxb-impl|src-gen|configurations.all" <donneur>/build.gradle
   ```
2. **Même train de plateforme** (8.2.x EE ↔ 8.2.x EE), au plus près de la cible —
   c'est le build.gradle qu'on hérite.
3. **Périmètre de modules le plus recouvrant** — chaque module déjà présent chez
   le donneur est une ligne de chirurgie en moins.
4. La fraîcheur des données du donneur est **indifférente** : on ne prend ni sa
   base ni ses données (base neuve), seulement sa recette de build.

**Comparer les candidats sur PIÈCES, jamais sur leur réputation.** Cas vécu
2026-08-28 : sur la cible 9.1.6 + facturation électronique, deux analyses ont
opposé deux donneurs, A et B. L'argument avancé pour écarter B
(« sa recette est orientée portail, elle n'a pas la famille
business-project/production ») était **faux** — un `grep` montre que les deux
déclarent exactement les mêmes 12 modules EE. Le départage réel tenait en trois
faits mesurables : B est sur la plateforme **8.2.3 exacte** de la cible
(A en 8.2.2), pinne ces modules à des versions **plus proches** de la cible,
et surtout **porte déjà les excludes JAXB** que A n'a pas — donc partir de
A revenait à reconstruire à la main le garde-fou qui protège du « 0 menu +
500 sur toute fiche ». Trois `grep` tranchent ce qu'un paragraphe de
justification peut faire croire à l'envers.

Consigner le choix et sa justification dans `env.donor` / `env.donor.why` du
manifest : dans 6 mois, l'audit de dérive commence par relire ça. Une
justification qui n'est pas adossée à une commande vérifiable n'en est pas une.

Cloner comme `SKILL.md` (Pattern A-bis §3) : `cp -a` sélectif de
`build.gradle gradle gradle.properties gradlew gradlew.bat settings.gradle src modules`,
jamais `build/`, `.gradle/`, `node_modules/`.

## Phase 2 — Chirurgie (diff donneur → manifest)

La chirurgie est la liste **exhaustive** des écarts entre la recette clonée et le
manifest. La calculer AVANT de toucher quoi que ce soit, l'exécuter, puis
`probe-env.sh <manifest> --static` doit passer au vert. Points d'attention que
les probes couvrent (fix détaillés dans `SKILL.md`) :

- **Pins en double** : les versions vivent dans `gradle.properties` ET parfois
  hard-codées dans `build.gradle` (qui shadowent). Aligner LES DEUX (probe S2).
- **Purge des dérives héritées du donneur** : `appName`, `db.default.url`,
  lignes `context.*` spécifiques à son métier, forces/excludes devenus inutiles
  pour la cible. Ce qui reste sans justification est une dérive importée.
- **Ce que le donneur doit à sa BASE ne suit pas.** On clone des fichiers, pas
  une base : les vues patchées en `meta_view`, les vues pilotées par Studio, les
  menus/actions seedés en SQL, les apps configurées à la main chez le donneur
  **n'existeront pas** dans l'env neuf. Le piège n'est pas que ça casse — c'est
  que l'écran qu'on a vu marcher chez le donneur est simplement absent ou nu
  chez nous, sans erreur. Avant de cloner, relire la documentation du donneur
  (fiche d'env, historique de ses correctifs, notes de livraison) et lister ses
  patchs base : chacun est soit à rejouer, soit à
  déclarer hors périmètre. Un donneur très patché en base est un mauvais donneur
  même si sa recette de build est parfaite.
- **Ajout de modules absents chez le donneur** : dépendance dans `build.gradle`
  + pin — et pour un module **local**, symlink dans `modules/` + `if-module`
  aligné (probe S3).
- **`axelor-observability` est recommandé (pas exigé par AOS) dans tout env
  destiné à être déployé/livré.** Il apporte une
  vue qui lit les **logs applicatifs directement dans l'ERP** — de quoi debugger
  sans accès à une plateforme d'observabilité externe, y compris pour un client
  qui fait du Studio.
  `implementation "com.axelor.addons:axelor-observability:<v>"`.
  Versions publiées au 2026-08-29 : **2.0.0** → train AOP **8.2.3**, **1.0.0** →
  train AOP **7.4.10**, **rien pour AOP 5.4** et rien de prévu ; une **2.0.1** est
  sortie depuis (résolue et embarquée le 2026-09-14). Vérifier la dernière version
  sur le dépôt Maven entreprise avant de l'épingler. `aosVersion: null` : le module s'aligne sur l'**AOP**,
  pas sur l'AOS. Nexus `requiresAuth` → mêmes creds `maven-enterprise` que les
  modules EE. Le déclarer en `module.axelor-observability` dans le manifest arme
  S2/W1/R6 sans toucher aux probes.
  Attention : **Config initiale non reproduite ici** (source interne non exportée) :
  l'obtenir auprès d'Axelor ou dans la documentation du module, ne jamais
  inventer les propriétés. Identique pour toutes les versions d'AOP,
  seule la version du module change.
- **Facturation électronique** dans le périmètre → poser les 2 excludes JAXB
  hors `subprojects` (probe S4) ; **guardian** → `sourceSets` src-gen (probe S5).

## Phase 3 — Base NEUVE (le territoire propre à ce skill)

`CREATE DATABASE <db.name> OWNER <role-pg>;` (sur l'hôte PostgreSQL de `db.default.url`), `ddl=update`,
`data.import.demo-data=false`. Une base vierge évite les pièges du clone
(licence 1020, données résiduelles) mais en crée **trois autres** :

1. **Rien n'active les apps framework.** `demo-data=false` ne crée/active aucune
   `studio_app` : menus et champs gatés `isApp('x')` seront invisibles module
   pourtant installé. Après le 1er boot, installer les apps du manifest **par
   l'UI** (la routine d'install pose la config associée — un flip SQL laisse la
   config vide : « Statut de tâche terminée est requis », etc.). Probe R5.
2. **La licence EE se charge par l'UI** sur une machine où aucune licence n'a
   encore été téléversée. Séquence : 1er boot → login admin → upload du fichier de
   licence par l'utilisateur → probe R4 (`app_license_status=ACTIVE`). Prévoir
   ce passage de main dans le déroulé — c'est un gate humain, pas un script.
   Nuance observée (guardian 3.0.2 et 3.1.1) : si `<data.upload.dir>/certificate.crt`
   existe déjà (dossier de pièces jointes partagé avec un env où la licence a été
   téléversée), le premier démarrage a enregistré la licence seul, ACTIVE sans
   téléversement. Dans tous les cas, R4 fait foi.
   Attention aussi au **plafond de sièges** (code 1021 au login, ressemble à un
   mauvais mot de passe ; la carte des sièges se construit au BOOT).
3. **Elasticsearch (plateforme EE)** : l'interrupteur est
   `hibernate.search.backend.type = elasticsearch`, et trois pièges attendent —
   les clés de tuning de la doc livrée sont fausses (silencieusement ignorées),
   aucun mapping par défaut n'est livré (index vide, silencieux), et **aucun
   service ES ne tournait dans l'environnement d'origine** (conteneur de dev :
   décision d'infra à faire trancher).
   Recette vérifiée dans les sources : lire `references/elasticsearch.md` avant
   de poser la moindre propriété ES. Probes W4/R7.

## Phase 4 — Build, boot, recette

- `JAVA_HOME=<chemin-JDK-21> ./gradlew build` puis
  `probe-env.sh <manifest> --war` : modules embarqués à la bonne version (W1),
  Groovy 4 seul (W2), MOXy vainqueur si facturation électronique (W3).
- **GATE : jamais de boot sans feu vert explicite de l'utilisateur** (ni
  `gradlew run`, ni démarrage de Tomcat, ni script maison). Proposer, attendre.
- Après boot + licence + apps : `probe-env.sh <manifest> --runtime --db`.
  Un boot vert ne prouve rien — ce sont R2 (menus) et R3 (meta/view) qui font foi.
  La phase runtime exige `PROBE_USER` et `PROBE_PASSWORD` (aucune valeur par
  défaut, cf. `scripts/probe-env.sh --help`). Le mot de passe ne passe jamais
  par la conversation : l'utilisateur lance cette phase dans son propre
  terminal (variables exportées là), ou démarre la session de l'agent avec ces
  variables déjà dans l'environnement.

## Phase 5 — Livraison = env + manifest + registre

Un env sans son manifest n'est pas auditable. Livrer les trois ensemble :

1. Le manifest archivé **à la racine de l'app** (committé si l'app est versionnée).
2. **Le registre d'envs de l'équipe mis à jour immédiatement** (s'il n'y en a
   pas, en créer un : un fichier texte suffit) : une ligne courte par env (nom,
   dossier, base, versions AOS/AOP, URL et contexte, port), le détail dans une
   fiche par env, une entrée d'historique datée, et le contrôle de cohérence
   registre ↔ bases réellement présentes sur le serveur.
3. La sortie verte des probes collée dans le handover (c'est la recette signée).

## Phase 6 — Teardown (envs jetables seulement)

Un env monté pour une **campagne de qualification de capacités** (injection de
cas de test, règle : on n'injecte jamais hors d'un env explicitement marqué
sacrifiable) est jetable : il se marque comme tel à
la naissance et se détruit avec preuve à la fin. Les deux gestes sont décrits
une fois pour toutes dans
`references/cycle-de-vie-env-jetable.md`
— marquage dans la liste blanche des envs sacrifiables de l'équipe, séquence de
destruction ordonnée, et checklist de preuve couche par couche.

Deux règles qui ne se devinent pas :

- **Jamais `docker compose down -v`** pour « repartir propre » : ça détruit le
  volume PostgreSQL, donc **toutes** les bases du parc, pas seulement la cible.
- Dans une preuve par sortie vide, **une commande absente ressemble à un
  succès**. Vérifier que l'outil existe avant de lire son silence comme une
  preuve (`ss` n'était pas installé dans le conteneur de dev de l'auteur).

## Audit de dérive (l'autre moitié du skill)

Toute demande « cet env est-il conforme / a-t-il dérivé ? » = rejouer la suite sur
le manifest archivé, **sans rien provisionner** :

```bash
scripts/probe-env.sh <env>/env-manifest.properties --static --db          # sans toucher au runtime
scripts/probe-env.sh <env>/env-manifest.properties --all                  # si l'app tourne déjà
```

Lecture des rouges — trois familles de dérive :

| Famille | Symptôme typique | Probes |
|---|---|---|
| **Héritée** (importée du donneur à la création) | context.* exotiques, appName du donneur, excludes orphelins | S6, S11, revue de chirurgie |
| **Écart au manifest** (la cible n'a jamais été atteinte) | JAR absent du WAR, module hors meta_module, app inactive | W1, R5, R6 |
| **Temporelle** (l'env a bougé depuis la livraison) | probe verte à la recette, rouge aujourd'hui | n'importe laquelle |

Pour la dérive temporelle, le diff qui fait foi est **probes d'aujourd'hui vs
sortie verte archivée à la livraison** — d'où l'importance de la coller dans le
handover. Un env sans manifest archivé : en reconstruire un a posteriori depuis
`gradle.properties` + WAR + `meta_module`, le faire valider par l'utilisateur,
puis auditer contre lui.

Attention : Les probes détectent l'écart, elles ne disent pas s'il est **légitime** (un
bump volontaire non consigné est une dérive de documentation, pas de code).
Rapporter les rouges avec leur preuve, laisser l'utilisateur qualifier.

## Pièges propres au from-scratch (complément de la table de `SKILL.md`)

| Piège | Conséquence | Parade |
|---|---|---|
| Version EE prise « la plus récente » au lieu de celle résolue pour la cible | un module tire tout un train AOS différent (`Invalid namespace` au generateCode) | résolution par module (version-matcher s'il est disponible, sinon sources), pour LA version AOS cible |
| Version du matcher pinnée sans recoupement | pin sur une version absente du dépôt ou en retard d'index (cf. phase 0) → résolution Gradle en échec ou arbitrage silencieux | recouper les deux interrogations (ou le listing Maven) ; en cas de divergence, la résolution Gradle puis le contenu du WAR font foi |
| Plateforme open et enterprise confondues au même numéro | features EE absentes (ES, workflow) ou résolution Nexus impossible | `target.platform.ee` explicite + repo `maven-enterprise` |
| Base vierge « ça boote donc c'est fini » | apps inactives, licence absente, config d'apps vide | phase 3 complète + probes R4/R5 |
| Env livré sans `axelor-observability` | Pas de lecture des logs dans l'ERP : tout debug client repasse par une plateforme d'observabilité externe (ou par le support) | Ligne `module.axelor-observability` au manifest dès la phase 0, config initiale du module (cf. phase 2) |
| Manifest jamais archivé | env inauditable, dérive indétectable | phase 5, manifest = livrable |
| Probe rouge contournée « on verra » | le piège ressurgit au runtime, plus cher | rouge = stop, fix, re-run |
