---
name: provisioning-axelor-environments
description: >-
  Monter un environnement Axelor (AOS/AOP) isole a partir d'une app qui demarre
  deja (worktree, branche, base dediee, app dediee : tester une MR, demo avec sa
  propre base, version AOS/AOP pour analyse de diff, dev d'un module standalone),
  assembler une pile qu'aucun environnement ne porte (manifest + probes
  rouge/vert), ou auditer la derive d'un environnement livre. Declencheurs : «
  monte un env », « worktree », « base dediee », « clone de base », « env
  jetable », « l'app ne boote pas », « LicenseException », « 0 menu », « 500 sur
  toute fiche », « audit de derive » ; provision environment, worktree, disposable
  env, drift audit. PAS pour : le deploiement local courant d'axenr-app (build
  Gradle + Tomcat), le setup initial d'un depot (axelor:setup), les imports de
  donnees (axelor-import-export), les profils et droits (axelor-droits-expert),
  les donnees de demo (demo-data-generator).
metadata:
  owner: axenr
  family: technique
---

# Provisioning Axelor Environments

Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.0.x à 9.1.8 / AOP EE 8.2.2 à
8.2.4-SNAPSHOT (patterns et pièges) et, pour `references/from-scratch.md`, sur AOS 9.1.6 / AOP EE 8.2.3 (base vierge,
toutes sondes vertes). AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier. Les commandes
ont été réécrites en version générique par l'auteur et n'ont pas été rejouées hors de son environnement.

**Mise en garde, quelle que soit la version :** après « Tout restaurer… » (Administration > Gestion des vues > Les Vues,
rechargement des métadonnées), environ une requête sur dix s'exécute sous l'identité `admin` jusqu'au redémarrage
(mesuré sur AOP 8.2.2). **Redémarrer Tomcat immédiatement après**, avant toute recette ou démonstration ; mieux, ne pas
l'utiliser (voir `references/cycle-de-vie-env-jetable.md` §2).

## Contexte AxENR

Le corps du skill décrit un environnement de l'auteur (AOS 9 / AOP 8, Java 21, `./gradlew run`). Sur les projets
AxENR, vérifier d'abord ce qui diffère :

| Point | Chez AxENR | Source |
|---|---|---|
| Versions | axenr-app sur AOP 7.4.7 et AOS 8.x : lire `gradle.properties` et `gradle/libs.versions.toml` du projet, jamais ce skill | `CLAUDE.md` du dépôt marketplace |
| Java | Ne jamais modifier `JavaLanguageVersion` dans `build.gradle`. Le JDK utilisé au build doit correspondre à la toolchain du projet : un `JAVA_HOME` qui pointe sur un autre JDK est la première cause d'échec de build local | LESSON-030 |
| Déploiement local | Build Gradle puis Tomcat externe. Pièges connus, à vérifier dans cet ordre : `JAVA_HOME` qui ne pointe pas sur le JDK de la toolchain ; fichier de configuration sous `~/.axelor` qui surcharge `axelor-config.properties` du projet ; identifiants PostgreSQL ; base absente (à créer avant le premier démarrage) ; port déjà occupé | pratique de l'équipe AxENR |
| Clé de chiffrement | Renseigner `encryption.password` dans `axelor-config.properties` de **chaque** worktree, sans jamais le committer. Sans elle, sur un dump AxENR, l'installation des modules s'interrompt, `meta_module` reste vide pour le module custom et l'app répond quand même en HTTP 200 | LESSON-077, ticket-solver R10 |
| Rebuild | Après toute édition de source : clean rebuild (`./gradlew clean generateCode copyWebapp build`). Un build incrémental produit `Type specified for TypedQuery … ParallelWebappClassLoader`, bruit de dev absent en prod | LESSON-078 |
| Port | Vérifier le port avant de booter : `lsof -nP -iTCP:8080 -sTCP:LISTEN` | agent axenr-montee-version |
| Base | `ddl=update` modifie le schéma : jamais sur une base métier sans accord explicite ; préférer une base jetable | agent axenr-montee-version |

Ce qui reste valable tel quel : les 3 axes d'isolation, le clonage d'une recette qui boote plutôt qu'un build écrit à
la main, la vérification `if-module`, la checklist « un boot propre ne prouve pas une app saine » et la session REST par
cookie ouverte par l'utilisateur.

## Overview

Monter un environnement Axelor **isolé** à partir d'un environnement déjà
fonctionnel, sans casser l'existant ni perdre du temps sur des properties
manquantes.

**Principe central :** on ne réinvente jamais le build. On **clone une recette
qui marche déjà** (worktree d'un monorepo qui boote, ou app dédiée déjà câblée)
puis on n'isole que **trois choses** : la branche, la **base de données**, et le
**nom de module** vu par les vues (`if-module`). Tout le reste (versions maven,
guardian, groovy, React) est hérité tel quel et ne doit PAS être touché.

**Règle d'or build/run (convention du projet) :** tout build et run passe par
`./gradlew`. INTERDICTION d'inventer `docker run`, un second Tomcat, `mvn`, ou
des scripts ad hoc. Si tu hésites sur l'infra de run → c'est `./gradlew run`.
(Seule exception documentée : valider le WAR sur un Tomcat standalone, voir la
ligne « Groovy 3 de Gradle » de « Erreurs fréquentes ».)

## Prérequis

**Obligatoires**

| Outil | Rôle dans ce skill |
|---|---|
| `git` (avec `git worktree`) | branches et worktrees des patterns A / A-bis / B |
| JDK 21 | build et run des apps AOP 8.x / AOS 9 (le skill relève un build AOP 8.1.2 qui échoue en Java 11 : « requires JVM 21 ») |
| `./gradlew` (wrapper de l'app) | tout build et run |
| PostgreSQL (serveur joignable) + clients `psql`, `pg_dump` (et `pg_restore` si dump binaire) | création, clone (`CREATE DATABASE … TEMPLATE`) et contrôle des bases |
| `curl` et `python3` | vérifications HTTP et one-liners JSON de la checklist |
| Identifiants du dépôt Maven entreprise d'Axelor (`axelorMavenUsername` / `axelorMavenPassword` dans `~/.gradle/gradle.properties`) | résolution des modules EE et Studio ; sans eux la résolution échoue |

**Optionnels, et ce qui se passe sans eux**

| Outil | Rôle | Sans lui |
|---|---|---|
| MCP `version-matcher` | résoudre les versions AOS ↔ AOP ↔ modules EE | lire `gradle.properties`, `settings.gradle` et le `build.gradle` d'une app qui boote, le changelog AOS et les versions publiées sur le dépôt Maven ; ne jamais deviner une version |
| Plugin `axelor` (`axelor:setup`) | setup initial d'un repo Axelor | cloner et initialiser l'app à la main depuis le webapp template Axelor |
| Tomcat standalone (l'auteur utilisait Tomcat 10.1) | valider le WAR hors `gradlew run` (piège Groovy 3) | `./gradlew run` reste valable pour le dev rapide hors expressions de vue `.size` |
| `rsync` | copier une app sans `build/` | `cp -a` sélectif item par item |
| `fuser`, `lsof`, `ss`, `netstat` | libérer ou contrôler un port | `curl` sur l'URL tranche (voir « Erreurs fréquentes ») |
| extension PostgreSQL `dblink` et rôle superuser | seulement pour « Seeder un env neuf » | ne pas utiliser cette section |

## Choisir le pattern selon le besoin

```
Besoin                                          → Pattern
─────────────────────────────────────────────────────────────────
Tester une MR / branche remote du MONOREPO      → A. Worktree
Tester une MR du repo MODULE-ONLY (dépôt privé du module) → A-bis. Worktree module + app clonée
Review de code, démo rapide, env jetable        → A. Worktree
Démo client avec sa propre base                 → A. Worktree (DB dédiée)
Déployer une version AOS/AOP spécifique (diff)  → A. Worktree + variante Versions
Développer LE MODULE pour pousser une MR        → B. App dédiée + module standalone
Pile qu'aucun env ne porte (versions + modules)  → references/from-scratch.md
Auditer la dérive d'un env livré                → references/from-scratch.md (probes seules)
```

> **Avant de choisir A vs A-bis :** d'où vient la branche ? Un remote de type
> **module-only** (le dépôt privé d'un module métier) contient le module à la
> racine, pas le webapp. Sa branche `<branche-ticket>` n'est **PAS runnable seule** et ne
> se transpose **PAS** sur le webapp local `<webapp>` : leurs lignées
> React ont divergé (le webapp local n'a même pas un composant React que la
> branche suppose). Vérifier en
> 1 commande avant toute tentative de greffe : `git apply --check --3way
> --directory=modules/<module>/ <patch>` — si « does not exist in index » →
> abandonner la transposition, partir sur **A-bis** (faire tourner le standalone
> tel quel via une app wrapper clonée).

| | A. Worktree | B. App dédiée |
|---|---|---|
| Emplacement | `.worktrees/<nom>` (dans le repo, gitignored) | dossier frère `<app>` + repo module standalone |
| Source | monorepo, swap de branche | wrapper webapp + symlink du module |
| Quand | tester/démo/review/version | dev module → MR sur le dépôt module-only |
| Exemple | `.worktrees/<nom>` (une branche + une base par worktree) | `<app-wrapper>` + `<module>-standalone` |

**Pas pour** le clone/setup initial d'un repo Axelor (versions, AOS/AOP, addons à
cloner depuis zéro) → plugin axelor (`axelor:setup`) s'il est installé ; sinon
cloner et initialiser l'app à la main depuis le webapp template Axelor. Pour la
mécanique git worktree générique hors Axelor → `git worktree` directement.

## Les 3 axes d'isolation (ne jamais en oublier un)

1. **Branche** — chaque env = sa branche dédiée (jamais détacher HEAD du tree principal).
2. **Base de données** — `db.default.url` distinct dans `axelor-config.properties`.
   Une démo SANS DB dédiée écrase les données d'une autre démo. C'est l'erreur n°1.
3. **`if-module`** — la valeur dans les vues doit matcher le **nom du module
   installé** dans CET env (`modules/<dir>`). Mismatch = vues/menus absents
   **sans aucune erreur** au build.

---

## Pattern A — Worktree (tester une MR / démo / review)

Référence : vérifier d'abord `git worktree list`.

### 1. Récupérer la branche

```bash
# MR remote
git -C <repo-monorepo> fetch <remote> <branche-remote>
git -C <repo-monorepo> branch test/<nom> <remote>/<branche-remote>

# OU démo depuis la branche fonctionnelle courante
git -C <repo-monorepo> branch demo/<nom> <branche-fonctionnelle>
```

### 2. Créer le worktree (toujours sous `.worktrees/`, gitignored)

```bash
git -C <repo-monorepo> worktree add .worktrees/<nom> <branche>
```

### 3. Isoler la base de données

Éditer `.worktrees/<nom>/src/main/resources/axelor-config.properties` :

```properties
db.default.url = jdbc:postgresql://<hote-pg>:5432/<nom_db>
# laisser db.default.ddl = update  → Hibernate crée le schéma au 1er boot
# (JAMAIS create : ça wipe à chaque restart)
```

> `axelor-config.properties` est **tracké en git** → le worktree apparaît
> « dirty ». NE PAS committer ce changement de DB (c'est un override local).
> Il ne se masque pas : `info/exclude` n'agit que sur les fichiers **non suivis**.
> Ne pas recourir à `git update-index --skip-worktree` pour le cacher : `git status`
> devient muet, plus rien de ce fichier n'est jamais commité, et un WAR construit
> depuis la branche part avec la config versionnée, pas celle du disque (constaté :
> `utils.api.enable` présent sur le disque, absent du WAR déployé → 403 sur `/ws/aos/**`).
> Vérifier `git status` avant chaque commit et ne jamais ajouter ce fichier.

> **Piège — bindings `context.*` manquants (NPE silencieux différé).** `__config__` ne connaît QUE les propriétés `context.*` du `axelor-config.properties` (cf. AOP `ConfigContext` : `getPropertiesStartingWith("context.")`). Si une app custom omet une de ces lignes (fréquent quand le `axelor-config.properties` a été réécrit à la main, pas dérivé de `open-suite-webapp`), `__config__.<clé>` renvoie **null** — pas une erreur de config, juste null. Des conditions AOS **standard** s'en servent (ex. `Invoice.xml` track : `statusSelect == 3 && dueDate.isAfter(__config__.date)`) → `dueDate.isAfter(null)` → NPE, qui surgit surtout dans le `AuditProcessor`/`LeaderElectionWorker` au boot (rejeu des audit logs, avec retries + ERROR). Vérifier/poser au minimum :
> ```properties
> context.app  = com.axelor.studio.app.service.ScriptAppService   # 38+ menus isApp() (cf. AOP 8 ScriptPolicy)
> context.date = java.time.LocalDate:now                          # sinon __config__.date null → NPE track Invoice/audit
> ```
> Diag : `grep '^context\.' axelor-config.properties`. `ConfigContext` sait invoquer une méthode **statique no-arg** (`Classe:methode`), d'où `java.time.LocalDate:now`.

### 4. Créer la base (hôte = celui de `db.default.url` ; si PostgreSQL tourne dans un autre conteneur, c'est le nom de ce service, pas `localhost`)

```bash
# mot de passe : variable PGPASSWORD du shell ou ~/.pgpass (jamais en clair dans une commande partagée)
psql -h <hote-pg> -U <role-pg> -d postgres -c "CREATE DATABASE <nom_db> OWNER <role-pg>;"
```

Pour une démo qui doit partir d'un jeu de données existant : créer la base puis
restaurer un dump (`pg_restore`/`psql -f`) AVANT le premier boot.

### 5. Vérifier `if-module` (piège silencieux AOS 9) — TOUJOURS, 2 commandes

Ne JAMAIS sauter cette vérif, même si l'env semble cohérent : c'est gratuit et
c'est le piège n°1 (vues/menus absents **sans aucune erreur** au build). Une MR
remote, un cherry-pick ou un backport peut introduire un `if-module` qui ne
matche pas le nom du module de CET env.

```bash
# nom(s) de module installé(s) dans cet env :
ls .worktrees/<nom>/modules/
# valeurs if-module présentes dans les vues :
grep -rho 'if-module="[^"]*"' .worktrees/<nom>/modules/*/src/main/resources/views/ | sort -u
```

Toute valeur `if-module` doit correspondre à un dossier de `modules/`. Sinon →
aligner les vues (ou installer le bon module). Idem pour
`:modules:<nom>:copyReactWebapp` dans le `war`/`run` (root build.gradle) et le
sélecteur d'app `isApp('<code-app>')` dans les vues.

### 6. Build puis run (1 env à la fois par port)

```bash
cd <repo-monorepo>/.worktrees/<nom>
./gradlew build                 # valider la compilation d'abord
# arrêter l'instance précédente (Ctrl-C de son `gradlew run`, ou arrêt de son process Java)
# et vérifier que le port est libre : ports observés occupés par un run précédent
# = 8080, 5005 et 35729, plus les daemons Gradle
./gradlew run                   # Tomcat embarqué, http://localhost:8080
```

Premier boot : `ddl=update` crée les tables (2-3 min), login `admin/admin`.

### 7. Teardown

```bash
git -C <repo-monorepo> worktree remove .worktrees/<nom> --force
git -C <repo-monorepo> branch -D test/<nom>
psql -h <hote-pg> -U <role-pg> -d postgres -c "DROP DATABASE <nom_db>;"   # données jetables uniquement
```

---

## Pattern A-bis — Tester une MR du repo module-only (dépôt privé du module)

Cas vécu (2026-06) : tester des correctifs livrés sur une branche
`<branche-ticket>` d'un dépôt module-only privé. La branche n'est pas runnable
seule et ne se transpose pas sur le webapp local. **Recette** : worktree du repo
**module** standalone + **clone** du wrapper app qui boote déjà
(`<app-wrapper>`) + **DB clonée** pour hériter des données de test.

C'est un hybride : isolation type A (worktree d'une branche) mais sur l'unité
runnable de B (app wrapper + module standalone symlinké).

### 1. Mesurer le périmètre de la branche (toujours d'abord)

```bash
git -C <repo-monorepo> fetch <remote-module> <branche-ticket>
git -C <repo-monorepo> fetch <remote-module> main
git diff --stat <remote-module>/main...<remote-module>/<branche-ticket>   # quels fichiers ? Java/React/i18n ?
git log --oneline <remote-module>/main..<remote-module>/<branche-ticket>  # quels tickets ?
```

Si la branche ne touche que React/i18n (pas de Java), l'écart de version AOS
(9.1 remote vs 9.0.8 local) est sans effet : le bundle React est autonome.

### 2. Worktree du repo MODULE standalone (pas le monorepo)

```bash
git -C <repo-module> fetch origin <branche-ticket>
git -C <repo-module> worktree add \
    <worktree-module> <branche-ticket>
```

### 3. Cloner le wrapper app qui boote (sans build/, .gradle/, node_modules/)

`rsync` peut être **absent** → `cp -a` sélectif (jamais copier `build/` : ~0.5 Go inutile, régénéré).

```bash
SRC=<app-wrapper>
DST=<app-wrapper>-<branche-ticket>
mkdir -p "$DST"
for i in build.gradle gradle gradle.properties gradlew gradlew.bat settings.gradle src modules; do
  cp -a "$SRC/$i" "$DST/$i"
done
# repointer le symlink du module vers le worktree de la branche :
rm "$DST/modules/<module>"
ln -s <chemin-relatif-vers-worktree-module> "$DST/modules/<module>"
readlink -f "$DST/modules/<module>"   # doit pointer sur le worktree
```

### 4. Isoler DB (clone TEMPLATE = données de test instantanées) + appName

Pour tester un comportement UI (copier-coller d'un arbre de chiffrage / Cost Breakdown…) il faut des **données
existantes**. Sur le même serveur PG, cloner par `TEMPLATE` est instantané — mais
exige **zéro connexion active** sur la DB source (sinon « source database is being
accessed by other users ») :

```bash
psql -h <hote-pg> -U <role-pg> -d postgres -tAc \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='<db_source>';"   # doit être 0
psql -h <hote-pg> -U <role-pg> -d postgres -c \
  "CREATE DATABASE <db_clone> WITH TEMPLATE <db_source> OWNER <role-pg>;"
```

Puis dans le clone d'app :
- `src/main/resources/axelor-config.properties` → `db.default.url = …/<db_clone>`
- `gradle.properties` → `appName = <appName-clone>`
  Attention : **Renommer `appName` change le chemin de contexte servlet** : l'URL devient
  `http://localhost:8080/<appName-clone>` (PAS la racine `/`). C'est
  le prix de l'isolation du nom de projet Gradle (sinon `rootProject.name`
  identique à la prod). Le noter dans le handover.

### 5. Build + run + vérif que le correctif est bien embarqué

```bash
cd <app-wrapper>-<branche-ticket>
JAVA_HOME=<chemin-JDK-21> ./gradlew build   # React + Java
# preuve que le fix React est dans le bundle compilé (pas juste dans les sources) :
grep -rl "<une chaîne i18n unique ajoutée par la MR>" build/webapp/*/assets/*.js
JAVA_HOME=<chemin-JDK-21> ./gradlew run
```

**Vérif HTTP = vérité terrain.** Dans un conteneur Docker, `ss`/`netstat` peut afficher 8080 « not
listening » depuis le netns alors que ça sert. Trancher au `curl` (sur le
bon chemin de contexte) :

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/<appName-clone>/   # 200 = up
```

### 6. Teardown

```bash
# arrêter l'instance (Ctrl-C de son `gradlew run`, ou arrêt de son process Java)
git -C <repo-module> worktree remove <worktree-module> --force
git -C <repo-module> branch -D <branche-ticket>
rm -rf <app-wrapper>-<branche-ticket>
psql -h <hote-pg> -U <role-pg> -d postgres -c "DROP DATABASE <db_clone>;"
```

---

## Pattern B — App dédiée (dev module → MR)

Le module est un **repo Git autonome** (`<module>-standalone`,
remote privé, 1 branche = 1 ticket). Une **app wrapper**
(`<app-wrapper>`) le **symlinke** dans `modules/` et produit un WAR
runnable.

- **Développer** : travailler/commiter dans le repo du module (`<module>-standalone`),
  pas dans l'app.
- **Tester** : l'app le voit via `modules/<nom> -> ../../<module>-standalone`
  (symlink). `./gradlew build && ./gradlew run` depuis l'app, sur sa DB
  (`<db_app>`).
- Pour une nouvelle app dédiée : **cloner une app existante qui boote** (copier
  `settings.gradle`, `build.gradle`, `gradle.properties`, `gradle/`), changer
  `appName` + `db.default.url`, refaire le symlink. Ne pas écrire le build à la main.

Le `build.gradle` de l'app consomme AOS/AOP/EE en **maven-dependencies** ; le
module en `project(":modules:<nom>")`. Le `war` utilise `findProject(...)` pour
ne dépendre du `copyReactWebapp` que si le module est présent.

---

## Variante — Version AOS/AOP spécifique (analyse de diff)

Pour comparer deux versions : un worktree par version, chacun sa DB.

1. **Vérifier la compatibilité** : le MCP `version-matcher`, s'il est disponible,
   donne l'AOP et les versions de modules EE compatibles avec l'AOS visé ; sinon
   lire `gradle.properties`, `settings.gradle` et le `build.gradle` de l'app, le
   changelog AOS et les versions publiées sur le dépôt Maven. Ne jamais deviner
   les versions EE.
2. Éditer **`gradle.properties`** : `aosVersion`, `aopVersion`, et les pins EE
   (`businessProjectVersion`, `schedulerVersion`…). Aligner aussi les versions
   hard-codées dans le bloc `dependencies` de `build.gradle` (elles shadowent
   `gradle.properties` si différentes — cause de faux-positifs de compilation).
3. DB **séparée par version** (le schéma diffère). `./gradlew clean build`.

---

## Properties & câblage à NE JAMAIS perdre (hérités, ne pas réécrire)

Ces éléments font booter AOS 9 / AOP 8. Si tu pars d'une recette qui marche, ils
sont déjà là. Si une app « refuse de booter », vérifier qu'ils n'ont pas sauté :

| Élément | Où | Pourquoi |
|---|---|---|
| `sourceSets.main.java.srcDir "${buildDir}/src-gen/java"` | `build.gradle` | guardian-plugin 1.0.0 génère `GuardianPublicKey.java` mais ne le wire pas → `LicenseException Code 1050` au boot |
| `force 'com.axelor.addons:axelor-studio:4.0.6'` + `exclude group: 'org.codehaus.groovy'` | `build.gradle` `allprojects` | conflit de capability Groovy 3 (codehaus) vs Groovy 4 attendu par AOS 9 |
| `axelorMavenUsername` / `axelorMavenPassword` | `~/.gradle/gradle.properties` | accès Nexus `maven-enterprise` (modules EE + studio) ; sans → résolution échoue |
| `axelor.platform.ee = true` | `gradle.properties` | active la plateforme EE |
| `db.default.ddl = update` | `axelor-config.properties` | crée/maj le schéma ; `create` wipe à chaque restart |
| `data.import.demo-data = false` | `axelor-config.properties` | éviter un re-seed AOS non voulu |
| `utils.api.enable = true` (ou `aos.api.enable = true`) | `axelor-config.properties` | **interrupteur global de l'API REST AOS** (`axelor-utils` `@HttpExceptionHandler`). Absent/blank ⇒ `isApiEnabled()` renvoie `false` ⇒ **tout** endpoint `/ws/aos/**` répond **403** « Les appels API AOS sont désactivés ». **Indispensable** dès qu'un micro-frontend React consomme un contrôleur custom : **project-scheduler / project-planning**, écran de chiffrage d'un module métier. Build ne le détecte pas ; ne se révèle qu'au runtime |
| `exclude group:'org.glassfish.jaxb', module:'jaxb-runtime'` + `exclude group:'com.sun.xml.bind', module:'jaxb-impl'` dans `configurations.all` | `build.gradle` | **Obligatoire dès que le périmètre embarque la facturation électronique** (`axelor-facturx`, `axelor-cii`). Sans ça : **0 menu affiché et 500 à l'ouverture de toute fiche**, sur une app qui a booté proprement. Voir « Erreurs fréquentes » |

## Module recommandé — `axelor-observability`

Recommandé (pas exigé par AOS) pour tout env **destiné à être déployé/livré**
(app dédiée, démo, env client) : `axelor-observability` apporte une vue qui lit les **logs
applicatifs directement dans l'ERP**, sans accès à une plateforme d'observabilité
externe — utile pour le support, et pour un client qui fait du Studio.

```gradle
implementation "com.axelor.addons:axelor-observability:2.0.0"
```

| Point | Valeur |
|---|---|
| Versions publiées | Au 2026-08-29 : **2.0.0** (train AOP 8.2.3) et **1.0.0** (train AOP 7.4.10). Une **2.0.1** est sortie depuis (en service mi-septembre 2026). Vérifier la dernière version sur le dépôt Maven entreprise avant de l'épingler |
| AOP 5.4 | **Aucun support**, aucun prévu |
| Alignement | `aosVersion: null` — le module suit l'**AOP**, pas l'AOS ; pas de pin à recalculer à chaque bump AOS |
| Nexus | groupId `com.axelor.addons`, `requiresAuth` → creds `maven-enterprise` (mêmes que les modules EE) |
| Config initiale | **Non reproduite ici** (source interne non exportée) : l'obtenir auprès d'Axelor ou dans la documentation du module, ne pas inventer les propriétés. Identique pour toutes les versions d'AOP, seule la version du module change |

**Où l'ajouter — et où NE PAS l'ajouter.** La règle d'or du skill tient : sur un
worktree jetable (Pattern A / A-bis, test de MR, review), on **hérite** la recette
du donneur et on ne touche pas au build. L'ajout se fait donc dans la **recette
déployée** : app dédiée (Pattern B), env de démo livré, et surtout **chez le
donneur** — un donneur qui le porte le propage à tous ses clones. Si un env livré
ne l'a pas, c'est un ajout de module ordinaire : dépendance + pin, rebuild,
redeploy.

> Cloud, à ne pas confondre : les projets **cloud** ont eu en parallèle un
> passage des logs applicatifs au **format JSON** (parsés par un outil
> d'observabilité, ce qui corrige le décalage +1/+2 h et les tracebacks
> multi-lignes perdus). Ça n'a rien à voir avec ce module et ça ne concerne pas
> un env de dev en conteneur : ça exige un
> **redéploiement avec image Docker reconstruite**, pas une relance.

## Checklist de vérification (AVANT de crier victoire)

- [ ] `git worktree list` montre le nouvel env sur la **bonne branche**
- [ ] `grep db.default.url .../axelor-config.properties` = **DB dédiée** (pas celle de l'env donneur ni celle d'une autre démo)
- [ ] La DB existe : `psql -h <hote-pg> -U <role-pg> -lqt | grep <nom_db>`
- [ ] Clone EE : si `data.upload.dir` diffère du donneur (`grep data.upload.dir` dans les deux configs), `certificate.crt` copié à la racine du nouveau dossier **avant le 1er démarrage**, puis `SELECT app_license_status FROM enterprise_app_license;` = `ACTIVE`
- [ ] `if-module` des vues == nom dans `modules/` (sinon vues fantômes)
- [ ] `~/.gradle/gradle.properties` contient les creds Nexus
- [ ] `./gradlew build` OK **avant** tout run
- [ ] Le port (8080 par défaut) est libre — plus aucun process n'écoute — avant `./gradlew run`
- [ ] Premier boot : login `admin/admin` OK + menus du module visibles
- [ ] **Un boot propre ne prouve pas une app saine.** `Ready to serve` + 0 ERROR + HTTP 200 + login OK + `/ws/rest` OK peuvent coexister avec une UI **entièrement morte** : plusieurs défauts ne se révèlent qu'à la **première ouverture d'écran** (contexte JAXB construit paresseusement, services Guice lazy). Vérifier explicitement les deux endpoints que le navigateur appelle en premier :
  Session REST d'abord (fichier de cookies `c.txt`). Le mot de passe ne passe ni par un
  argument de commande, ni par un fichier, ni par la conversation : ces trois lignes sont
  tapées par l'utilisateur dans son propre terminal, dans le dossier de travail de l'agent ;
  l'agent ne réutilise ensuite que `c.txt` (à supprimer après usage : il porte la session).
  ```bash
  read -rs AXPW   # saisie sans écho
  printf '%s' "$AXPW" | curl -s -o /dev/null -c c.txt -b c.txt -X POST "http://localhost:8080/<ctx>/callback?client_name=AxelorFormClient" \
       --data-urlencode "username=<login>" --data-urlencode "password@-"; unset AXPW
  ```
  Contrôle de la session, jeton CSRF, puis les deux endpoints :
  ```bash
  curl -s -b c.txt -H 'Accept: application/json' "http://localhost:8080/<ctx>/ws/public/app/info" \
       | python3 -c "import json,sys;print('session:',(json.load(sys.stdin).get('user') or {}).get('login'))"   # None = login raté
  CSRF=$(awk -F'\t' '$6=="CSRF-TOKEN"{print $7}' c.txt | tail -1)   # en-tête X-CSRF-Token sur tout POST/PUT/DELETE (vide si l'instance n'en pose pas)
  curl -s -b c.txt "http://localhost:8080/<ctx>/ws/action/menu/all" | python3 -c "import json,sys;d=json.load(sys.stdin);print('menus:',len(d.get('data') or []))"
  curl -s -b c.txt -X POST "http://localhost:8080/<ctx>/ws/meta/view" -H 'Content-Type: application/json' ${CSRF:+-H "X-CSRF-Token: $CSRF"} \
       -d '{"model":"com.axelor.auth.db.User","data":{"type":"form","name":"user-form"}}' | head -c 120
  ```
  0 menu ou `status: -1` = app cassée malgré un boot vert.
- [ ] `grep api.enable .../axelor-config.properties` = `utils.api.enable = true` (sinon 403 sur tout micro-frontend React `/ws/aos/**`)
- [ ] Env destiné à être **déployé/livré** : `axelor-observability` envisagé (recommandé : dépendance + pin + config initiale du module) — inutile sur un worktree jetable
- [ ] Le changement de `db.default.url` n'est PAS committé sur la branche

## Erreurs fréquentes

| Erreur | Conséquence | Fix |
|---|---|---|
| Démo sans DB dédiée | Écrase les données d'une autre démo | `db.default.url` distinct + `CREATE DATABASE` |
| `if-module` non aligné | Vues/menus absents, **aucune erreur** | aligner sur le nom de `modules/<dir>` |
| `docker run` / 2e Tomcat / `mvn` inventés | Ne marche pas, perte de temps | uniquement `./gradlew build` / `./gradlew run` (seule exception : valider le WAR sur un Tomcat standalone, ligne « Groovy 3 de Gradle ») |
| Versions EE devinées | Capability conflict / classes legacy | résoudre via `version-matcher` s'il est disponible, sinon lire `gradle.properties` / `build.gradle` / versions publiées Maven ; pins `gradle.properties` ET `build.gradle` |
| Build écrit à la main | guardian/groovy/sourceSet manquants → ne boote pas | cloner une recette qui boote |
| `host = localhost` pour psql dans un devcontainer / conteneur (PostgreSQL = service séparé) | Connexion refusée | host = nom du service PostgreSQL (celui de `db.default.url`) |
| `db.default.ddl = create` | Schéma wipé à chaque restart | `update` |
| 2 envs lancés sur le même port (8080) | Port occupé / collision | 1 env à la fois par port ; arrêter l'instance précédente et vérifier le port libre avant |
| `JAVA_HOME` = Java 11 (défaut shell) | Build AOP 8.1.2 échoue : « requires JVM 21 » | préfixer **chaque** `./gradlew` : `JAVA_HOME=<chemin-JDK-21> ./gradlew …` |
| `utils.api.enable` absent de la config | **403 « API AOS désactivés »** sur tout `/ws/aos/**` → React project-scheduler/planning, écran de chiffrage d'un module métier cassés (`getTree` 403, `Promise.all index 1`). Aucune erreur au build ; pas un problème de droits utilisateur | Ajouter `utils.api.enable = true` dans `axelor-config.properties` **puis rebuild/restart** (lu une fois au boot via `AppSettings`) |
| App framework non activé | Menu + champs gatés `isApp('x')` **invisibles** alors que le module est installé | `studio_app code='x' active=true` requis ; une DB `demo-data=false` ne crée/active PAS l'app → insérer/activer puis **restart** (cache `AppService`) |
| Apps activées par flag DB sans routine d'install | Config incomplète par app (ex. aucun `project_task_status.is_completed=true` → « Statut de tâche terminée est requis ») | poser la config manquante en base (miroir d'une base de référence) OU passer par l'install UI de l'app |
| **`./gradlew run` fuite le Groovy 3 de Gradle** | Gradle 8.14.x embarque `groovy-3.0.24` qui se retrouve sur le classpath du Tomcat **embarqué** → expressions de vue `collection.size` (propriété) font un GPath spread → `MissingPropertyException: No such property: size for class Long`. Touche ~17 actions AOS std (SaleOrder, PurchaseOrder, Project, Invoice…) | Le WAR (`./gradlew build`) embarque **uniquement Groovy 4** : le déployer sur un **Tomcat standalone** (CATALINA_BASE dédié, port isolé) élimine la fuite. Vérif : `grep groovy- /proc/$PID/maps` doit ne montrer que 4.x ; tester l'action via `POST /ws/action`. `./gradlew run` reste OK pour le dev rapide hors expressions `.size` |
| **Périmètre EE incluant la facturation électronique** (`axelor-facturx`, `axelor-cii`) | **0 menu affiché et 500 à l'ouverture de toute fiche**, sur une app qui a booté **proprement** (`Ready to serve`, 0 ERROR, login OK, `/ws/rest` OK). Log : `ExceptionInInitializerError` → `IllegalAnnotationsException: 6 counts` sur `GET /ws/action/menu/all` et `POST /ws/meta/view`. **Piège de diagnostic n°1 : on cherche en base** — or `meta_menu`/`meta_view`/`auth_permission` sont intacts et toutes les classes citées dans la pile sont du socle AOP (`ObjectViews`, `MenuItem`, `Static`, `GridView`). Cause : les classes de schéma de vues d'AOP n'acceptent que **MOXy**, qu'AOP sélectionne via `com/axelor/meta/schema/{,views,actions}/jaxb.properties` — **mécanisme supprimé en Jakarta XML Bind 4.0**, donc ignoré. La sélection retombe sur le **ServiceLoader**, où MOXy et la RI Glassfish se déclarent toutes deux : **le premier du classpath gagne**, et `jaxb-runtime` précède `org.eclipse.persistence.moxy`. La RI arrive **uniquement** par `org.glassfish.jaxb:jaxb-runtime` ← `org.mustangproject:library` ← `axelor-facturx`, et `com.sun.xml.bind:jaxb-impl:3.0.1` ← `axelor-cii-lib` ← `axelor-cii` | **Fix** : dans `build.gradle`, hors `subprojects` — `configurations.all { exclude group:'org.glassfish.jaxb', module:'jaxb-runtime'; exclude group:'com.sun.xml.bind', module:'jaxb-impl' }` puis rebuild + redeploy. Attention : `com.sun.xml.bind:jaxb-impl:3.0.1` **EST la RI Glassfish repackagée** sous un autre groupId : en exclure une seule des deux ne change rien. **Diag en 10 s sans démarrer l'app** : compiler une classe qui fait `JAXBContext.newInstance(Class.forName("com.axelor.meta.schema.ObjectViews"))` avec `-cp 'WEB-INF/lib/*'` et afficher `ctx.getClass().getName()` — `org.eclipse.persistence.jaxb.JAXBContext` = sain. Attention : Pour tester un retrait de jar, **copier les jars dans un dossier propre** : une exclusion par boucle shell sur un glob produit des faux négatifs silencieux (vécu 2×). Non testé : la génération Factur-X/CII réelle sous MOXy. Cas vécu le 2026-08-06 (AOS 9.1.3 / AOP EE 8.2.2) |
| Transposer une branche **module-only** (dépôt privé du module) sur le webapp local | `git apply` échoue (« does not exist in index ») : lignées React divergées (un composant React que la branche suppose manque en local) | Ne PAS transposer. Faire tourner le standalone tel quel → **Pattern A-bis** (worktree module + app wrapper clonée) |
| Renommer `appName` pour isoler l'app | Le **chemin de contexte servlet change** → l'app sert sur `http://localhost:8080/<appName>`, pas sur `/`. « 404 » si on teste la racine | Tester sur `/<appName>/` ; le consigner dans le handover. (Garder `appName` identique = chemin racine mais `rootProject.name` en collision avec la prod) |
| DB clonée par `TEMPLATE` (ou dump restauré) | `LicenseException Code 1053` au boot (« license in DB ≠ license file ») — **distinct du 1050** | **Non bloquant** : la licence applicative EE s'active quand même (`App license activated … Complète`), l'app atteint `Ready to serve`. Si une fonction EE coince → re-upload du fichier de licence via l'UI. Les erreurs `AuditProcessor` au 1er boot (rejeu d'audit de la DB clonée) sont bénignes |
| **DB clonée par DUMP** (pas vierge) → `LicenseException Code 1020` « Aucune licence trouvée » à **CHAQUE save** (via `AppLicenseObservers.preSave`, cause `templateApiBaseUrl manquant`) | **BLOQUANT** (rien ne se sauvegarde). Le clone amène une ligne `enterprise_app_license` pré-existante → au boot `AppLicenseServerStartupEvent.registerLicense` fait un **INSERT (pas upsert)** → collision `unique_id already exists` → enregistrement avorte → ligne **INACTIVE** + métadonnées licence jamais chargées. Re-upload UI KO (contrainte unicité + observer bloque). Attention : Distinct du 1053 (non bloquant) : le 1053 s'active quand même, le 1020 **non** | **Fix** : `pg_dump -t enterprise_app_license --data-only <db> > backup.sql` puis `DELETE FROM enterprise_app_license WHERE unique_id='<id>' AND app_license_status='INACTIVE';` puis **RESTART** → le boot ré-enregistre (INSERT sans collision) → `app_license_status=ACTIVE`. Diag : `SELECT app_license_status FROM enterprise_app_license;` (INACTIVE=cassé, comparer au jumeau ACTIVE). Un flip SQL `status=ACTIVE` seul NE suffit PAS (métadonnées chargées au registerLicense). Les clones d'une base **vierge** n'ont PAS le pb. Cas vécu le 2026-07-28. Attention : **Vaut aussi pour un clone par `TEMPLATE`** d'une base peuplée, pas seulement par dump. **Mieux que le fix curatif : traiter en PRÉVENTIF** — juste après le clone et **avant le premier boot**, sauvegarder puis supprimer la ligne (`pg_dump -t enterprise_app_license --data-only` puis `DELETE FROM enterprise_app_license WHERE unique_id='<id>';`) : le boot fait alors un INSERT sans collision et la licence sort **ACTIVE** du premier coup, sans passer par l'état cassé. Vécu le 2026-08-06. Attention : **Nuance AOP EE 8.2.4-SNAPSHOT** (clone `TEMPLATE` `<base>`, 2026-09-30) : ligne clonée gardée + certificat présent → licence ACTIVE, ligne remplacée par une neuve, sans collision. Un seul cas, et après un 1er démarrage en 1052 : pas un test propre. Garder la suppression préventive tant qu'un clone propre n'a pas prouvé le contraire. Le certificat (ligne suivante) est nécessaire partout, il ne suffit pas. Attention : **Contre-exemple propre (AOS 9.1.7 / AOP EE 8.2.3 / Guardian 3.1.1, 2026-09-26)** : base clonée par dump avec sa ligne de licence ACTIVE conservée → boot propre (0 ERROR), licence toujours ACTIVE, enregistrement réussi, aucun 1020. La collision vaut pour les versions où le démarrage fait un INSERT de la licence ; sur cette combinaison, tester d'abord un enregistrement avant de supprimer la ligne par réflexe |
| Clone dont `data.upload.dir` pointe vers un dossier neuf (pièces jointes isolées du donneur) | `LicenseException: Code 1052: Current license's certificate file not found on disk` au boot (`AppLicenses.getCurrentCertificate`) si la ligne de licence est là ; sans ligne, **aucune erreur mais aucune licence**. L'app démarre quand même (`Ready to serve`) ; enregistrements non testés dans cet état. Distinct du 1053 | Le certificat de la licence EE est **`<data.upload.dir>/certificate.crt`**, déposé par le téléversement de la licence à l'écran et référencé par **aucune** ligne de `meta_file` : copier les seuls fichiers de `meta_file` l'oublie. Copier `certificate.crt` du dossier du donneur dans celui du clone, puis redémarrer : licence réenregistrée, ligne `enterprise_app_license` ACTIVE. Copier **avant le 1er démarrage**, et avant une suppression préventive de la ligne : sans certificat, le démarrage ne recrée pas la licence et ne signale rien. Preuve : `SELECT app_license_status FROM enterprise_app_license;` = `ACTIVE` ; l'absence d'erreur au démarrage ne prouve rien. Vécu sur `<base>` 2026-09-30, AOP EE 8.2.4-SNAPSHOT |
| `CREATE DATABASE … TEMPLATE` avec connexions actives sur la source | « source database is being accessed by other users » | Vérifier `pg_stat_activity` = 0 sur la source AVANT (couper l'app qui l'utilise), ou passer par `pg_dump | psql` |
| `rsync` absent de l'environnement | clone d'app échoue silencieusement | `cp -a` sélectif item par item, en **excluant** `build/`, `.gradle/`, `node_modules/` |
| Croire `ss`/`netstat` qui dit 8080 « not listening » | Faux négatif dans le netns Docker → on croit le boot raté alors qu'il sert | Trancher au `curl http://localhost:8080/<ctx>/` ; HTTP 200/302 = up. Le log `Ready to serve` + `Running at …` fait foi |

## Seeder un env neuf avec des référentiels d'une autre DB (même serveur PG)

Cas : DB fraîche + on veut y copier produits/partenaires/référentiels métier/configuration d'app depuis une DB de dev. Pièges rencontrés (tous silencieux au build) :

1. **Noms de table** : entité ≠ table. AOS préfixe (`base_product`, `base_product_category`, et, pour un module métier, le préfixe du module : `<module>_<entité>`, `studio_app_<code>`). Sonder via `pg_class`/`information_schema`, jamais le nom d'entité.
2. **Schéma source ≠ cible** (versions de branche différentes) : un dump pleine-colonne casse (`column X does not exist`). → copier l'**intersection des colonnes** (calcul via `dblink`), les colonnes source-only sont abandonnées.
3. **FK pendant le load** : charger avec `SET session_replication_role = replica;` (désactive les triggers FK ; **nécessite superuser** — le rôle de connexion doit l'être). Transaction unique + ids d'origine préservés.
4. **FK pendouillants** vers tables non copiées (company, meta_file, auth_user…) → Hibernate lève `EntityNotFoundException`. Les **NULLer** après load, **FK off** (sinon l'`UPDATE` re-valide les autres FK de la ligne et bloque).
5. **Séquences AOP** : `id` n'a **pas** de `DEFAULT` → `pg_get_serial_sequence` renvoie NULL → reset silencieusement sauté. La séquence réelle est `<table>_seq`. **Obligatoire** : `setval('<table>_seq', (SELECT max(id) FROM <table>))` sinon collision d'id (« duplicate key ») au 1er save. `increment_by=1` ⇒ pas d'optimiseur poolé, pas besoin de restart pour ça.
6. Après seed de la configuration d'app / des menus : **restart** pour rafraîchir le cache de config (`AppService` et les services de config du module).

## Références

| Fichier | Quand le lire |
|---|---|
| `references/from-scratch.md` | Assembler une pile qu'aucun environnement ne porte (manifest d'intention, chirurgie du donneur, base neuve, probes) ou auditer la dérive d'un environnement livré |
| `references/manifest-template.properties` | Gabarit du manifest d'intention, à copier à la racine du futur environnement |
| `scripts/probe-env.sh` | Suite de probes rouge/vert (`--static`, `--db`, `--war`, `--runtime`, `--all` ; `--help`). Lecture seule ; la phase runtime exige `PROBE_USER` / `PROBE_PASSWORD` exportés par l'utilisateur dans son terminal |
| `references/elasticsearch.md` | Avant de poser la moindre propriété Elasticsearch (recette lue dans le code, non éprouvée au runtime) |
| `references/cycle-de-vie-env-jetable.md` | Environnement jetable de campagne : marquage, vie, démontage avec preuve couche par couche |

Renvois : peupler l'environnement en données → `axelor-import-export` (imports) ou `demo-data-generator` (démo) ;
profils et droits des comptes de test → `axelor-droits-expert`.
