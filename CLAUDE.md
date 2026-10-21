# CLAUDE.md - AxENR Marketplace

> Marketplace interne AxENR - Systeme d'agents auto-apprenants
> Author: Fadel Benomar - Developer Backend & IA @ AxENR

---

## ARCHITECTURE (v2)

Une marketplace, plusieurs plugins par domaine. Detail complet, regles de
rangement et feuille de route : `docs/ARCHITECTURE.md`.

```
axenr-marketplace/
├── .claude-plugin/marketplace.json   # Catalogue (version AxENR unique, source of truth)
├── .github/workflows/                # ci.yml (doctor, bump, emojis) + release.yml (auto-bump)
├── CODEOWNERS
├── docs/ARCHITECTURE.md
├── scripts/                          # bump-version.sh, marketplace-doctor.py
└── plugins/
    ├── axenr-core/                   # [socle] Pour tous : coherence ENR, client-context, charte graphique, notes d'amelioration
    ├── axenr-erp/                    # [fonctionnel] ERP : baremes
    ├── axenr-gmao/                   # [fonctionnel] GMAO : capacites reelles de la solution
    ├── axenr-data/                   # [fonctionnel] Import/export, templates XDocReport/Carbone, modeles de mail, BI Superset
    ├── axenr-permissions/            # [fonctionnel] Droits et permissions
    ├── axenr-dev/                    # [technique] Claude Code : ticket-solver, PR review, lecons, outillage
    └── axelor/                       # [technique] Partenaire Axelor (ne pas modifier)
```

## COMPOSANTS AXENR

Regle : hors famille technique, uniquement des skills (ils fonctionnent dans
claude.ai, Cowork et Claude Code). Agents et commandes : axenr-dev seulement.

| Composant | Type | Plugin | Role |
|-----------|------|--------|------|
| enr-coherence-checker | skill | axenr-core | Valide la coherence ENR (generique tous types, cycle commercial) |
| client-context-detector | skill | axenr-core | Detecte le client AxENR depuis le cwd et charge ses ressources |
| axenr-brand | skill | axenr-core | Charte graphique officielle : logos SVG/PNG, palette, polices Bruno Ace et Montserrat, regles d'usage |
| skill-improvement-note | skill | axenr-core | « Note-le pour le skill » : fiche d'amelioration -> ticket Jira AxENR Marketplace - Notre cerveau |
| axenr-bareme-expert | skill | axenr-erp | Baremes tarifaires Axelor (moteur Pricing), catalogue en reference |
| gmao-capabilities | skill | axenr-gmao | Capacites reelles GMAO : standard / parametrage / roadmap / specifique |
| seeding-axelor-intervention-surveys | skill | axenr-gmao | Questionnaires d'intervention (checklist terrain, gamme de controle, PV) en bundle d'import |
| axelor-import-export | skill | axenr-data | Imports et exports Axelor : ecran d'import, import classique (bind.xml), edition entreprise, data-init, CORE MODEL |
| axenr-template-expert | skill | axenr-data | Templates Word XDocReport et Carbone (.docx prets a l'import), catalogue et references Carbone / Groovy / edition docx |
| axelor-modeles-mail | skill | axenr-data | Modeles de mail Axelor (StringTemplate) : creation, test, pieces jointes, depannage |
| demo-data-generator | skill | axenr-data | Donnees de demo credibles : cadrage du scenario, SQL idempotent, REST ou bundle, audit |
| axenr-bi-architect | skill | axenr-data | Requetes SQL PostgreSQL + dashboards Superset, catalogue en reference |
| axelor-droits-expert | skill | axenr-permissions | Cadrage et creation de profils, matrice de droits, import, audit, diagnostic |
| erp-consultant-enr | agent | axenr-dev | Consultant ERP ENR appele par le ticket-solver (genericite, temporalite) |
| ticket-solver-agent | agent | axenr-dev | Resolution autonome de tickets avec auto-apprentissage |
| pr-reviewer-axenr | agent | axenr-dev | Review PR (axelor:code-reviewer + checks AxENR) |
| axenr-montee-version | agent | axenr-dev | Montee de version des patchs AOS/AOP |
| error-learner, lesson-deduplicator, knowledge-updater, pre-flight-checker | skills | axenr-dev | Systeme de lecons (curator model) |
| axenr-dev-validator, migration-validator | skills | axenr-dev | Validations dev et migrations |
| marketplace-doctor | skill | axenr-dev | Audit de sante de la marketplace |
| security-audit | skill | axenr-dev | Audit de securite d un codebase (skill Cloudflare vendore, MIT) : reconnaissance, chasse guidee par couverture, validation adversariale, rapport |
| weekly-skill-integration | skill | axenr-dev | « Integre les notes de la semaine » : fiches Jira -> PR hebdomadaire |
| provisioning-axelor-environments | skill | axenr-dev | Environnements Axelor isoles ou assembles de zero, sondes, audit de derive |
| building-axelor-integrations | skill | axenr-dev | Connecteurs Axelor vers outils tiers : cadrage, emulateur, client REST, chiffrage |

### Commandes (axenr-dev, Claude Code)

| Commande | Usage |
|----------|-------|
| /axenr-dev:solve-ticket | Resoudre 1 ticket autonomement |
| /axenr-dev:solve-batch | Resoudre 2 tickets en parallele |
| /axenr-dev:review-pr | Review une PR avec pr-reviewer-axenr + axelor:code-reviewer partenaire |
| /axenr-dev:doctor | Audit de sante du marketplace |
| /axenr-dev:consolidate-lessons | Fusionne les lecons dupliquees, depile REVIEW QUEUE, declenche les promotions |
| /axenr-dev:sync-lessons | Curator model : pousse les LOCAL-LESSONS-<hostname>.md vers LESSONS-LEARNED.md via PR |
| /axenr-dev:bump-version | Bump de la version AxENR unique (patch/minor/major/auto) |
| /axenr-dev:montee-version | Montee de version AOS/AOP |
| /axenr-dev:learn-review | Legacy, utiliser /axenr-dev:consolidate-lessons |

Les skills fonctionnels n'ont pas de commande : on pose la question en langage
naturel et Claude choisit le skill. Dans Claude Code, on peut aussi forcer un
skill avec `/<nom-du-skill>`.

### Agents Axelor Partenaire (plugins/axelor/) - v2.5.0

| Agent | Role |
|-------|------|
| domain-agent | Generation domains XML |
| view-agent | Generation vues XML |
| java-agent | Generation code Java |
| code-reviewer | Revue qualite code (CRITICAL/HIGH/MEDIUM/LOW) |
| code-analyzer | Conformite, optimisations, securite |
| architect | Architecture technique |
| business-analyst | Analyse des besoins |
| agile-agent | Generation EPICs et User Stories |
| test-agent | Generation tests unitaires |
| git-agent | Operations Git avec validation |
| redmine-agent | Analyse tickets Redmine |
| repo-setup-agent | Setup des repos de reference |
| cicd-agent | Configuration CI/CD |
| doc-synthesis-agent | Synthese documentation |
| functional-validator | Validation fonctionnelle |
| spec-inspector | Inspection des specifications |
| requirements-refiner | Affinage des specifications |
| aos-analyzer | Analyse gap AOS |

### Skills Axelor Partenaire (32+ skills)

axelor-xml-validator, axelor-view-semantic-validator, axelor-java-style-validator,
axelor-naming-checker, axelor-semantic-validator, axelor-view-extension-validator,
aos-documentation-fetcher, aos-entity-searcher, aos-field-comparator,
axelor-controller-method-extractor, axelor-er-diagram-generator,
commitlint-validator, commitlint-config-generator, file-safety-checker,
functional-spec-consistency-checker, functional-spec-synthesis,
git-cliff-config-generator, gitlab-ci-generator, mr-title-validator,
pipeline-troubleshooter, pr-analyzer, quality-gate-configurator,
requirements-registry-builder, technical-architecture-synthesis,
ticket-deep-analyzer, ticket-duplicate-detector, us-dependency-mapper,
us-quality-validator, ci-validation-script-generator, etc.

## PROJETS CIBLES

| Projet | Repo | Techno | Branche de travail |
|--------|------|--------|--------------------|
| axenr-app | axenr-app (+ submodule modules/axenr) | Axelor AOP 7.4.7, Java 11, Gradle | dev, wip, ou autre (passe en argument) |
| axenr-mobile | axenr-mobile | React Native 0.75.5, TypeScript, Redux | axenr |

## SEPARATION DES RESPONSABILITES

| Ce repo (marketplace) | Le projet (axenr-app / axenr-mobile) |
|------------------------|--------------------------------------|
| Agents, skills, commands | Code metier |
| LESSONS-LEARNED.md | Domains, views, Java, TSX |
| Templates | Configs, builds |
| Intelligence et memoire | Aucun fichier de l'agent |

## MODELE DE LECONS PARTAGEES (Curator Model - Option A)

Deux fichiers coexistent dans `plugins/axenr-dev/docs/lessons/` :

| Fichier | Scope | Git |
|---------|-------|-----|
| LESSONS-LEARNED.md | Equipe (source de verite) | Commite |
| LOCAL-LESSONS-<hostname>.md | Local par poste | Gitignore |

### Flow

```
1. L'agent apprend une erreur -> error-learner ecrit dans LOCAL-LESSONS-<hostname>.md
   (IDs: LESSON-LOCAL-NNN, ne conflit jamais avec les IDs globaux)

2. pre-flight-checker lit UNION(LOCAL, SHARED) pour chaque generation
   -> le dev beneficie immediatement de ses propres lecons

3. Periodiquement (ou sur demande) :
   /axenr-dev:sync-lessons [--dry-run] [--auto-pr]
   -> applique lesson-deduplicator contre SHARED
   -> fusionne / ajoute
   -> ouvre une PR sur une branche lessons/sync-<hostname>-YYYYMMDD

4. Le curateur (Fabien / toi) review la PR et merge

5. Les autres devs recuperent les lecons via /plugin update
```

### Pourquoi pas de push automatique

- Le curateur garde la main sur la qualite des lecons promues en "loi d'equipe"
- Pas de conflit Git (branches separees par hostname, append-only dans LESSONS-LEARNED.md)
- Les lecons sont testees localement avant d'etre partagees

L'agent LIT le projet pour generer du code.
L'agent ECRIT ses lecons dans le marketplace uniquement.
L'agent ne depose AUCUN fichier dans le projet sauf le code demande.

## AGENTS PARTENAIRE

Les agents Axelor (v2.5.0) sont inclus directement dans `plugins/axelor/`.
Source : Axelor AI Team (`git@git.axelor.com:ia-tools/axelor-claude-marketplace.git`)

### Mise a jour du partenaire

1. Telecharger la nouvelle version depuis le repo Axelor
2. Remplacer le contenu de `plugins/axelor/`
3. Mettre a jour la version dans `.claude-plugin/marketplace.json`
4. Commit et push

## VERSIONING ET AUTO-UPDATE

Version AxENR unique : `.claude-plugin/marketplace.json` (champ `version` et
version de chaque plugin AxENR) et tous les `plugins/axenr-*/.claude-plugin/plugin.json`
portent le meme numero. Le plugin partenaire `axelor` garde sa propre version.

### Trois facons de bumper

1. Automatique via GitHub Action (recommande) :
   A chaque push sur main avec des modifs dans `plugins/` (hors `plugins/axelor/`),
   le workflow `.github/workflows/release.yml` :
   - detecte le type de bump via conventional commits (feat=minor, fix=patch, BREAKING=major)
   - bumpe marketplace.json + tous les plugin.json AxENR
   - commit "chore(release): bump axenr plugins to vX.Y.Z"
   - tag vX.Y.Z
   - cree une GitHub Release

2. Commande Claude Code :
   `/axenr-dev:bump-version [patch|minor|major|auto]`

3. Script local :
   `./scripts/bump-version.sh [patch|minor|major|auto]`

### CI de garde-fou

`.github/workflows/ci.yml` refuse tout PR qui modifie `plugins/` (hors partenaire)
sans bumper `marketplace.json`, et lance le doctor.

### Cote utilisateur (mise a jour des plugins)

Apres un merge :
```
/plugin marketplace update fbe-axenr-Axenr-marketplace
/plugin update --all
```
Cote claude.ai et Cowork : synchronisation automatique depuis GitHub, rien a faire.

### Marketplace Doctor

`/axenr-dev:doctor` ou `python3 scripts/marketplace-doctor.py [--strict]` verifie :
- sync des versions, JSON valides, plugins declares
- famille declaree pour chaque plugin (socle / technique / fonctionnel / support)
- skills : fichier `SKILL.md`, name = dossier, description <= 1024 caracteres,
  frontmatter limite aux cles acceptees par claude.ai
- aucun secret (jetons, cles, URL avec identifiants)
- pas de doublon de nom, pas d'emoji, pas de ressource rangee sous agents/
- lecons stagnantes (>30 jours)

## REGLES

1. NO EMOJIS in code
2. ENGLISH ONLY for technical names
3. Documentation in French (user-facing) or English (code-facing)
4. Conventional commits for this repo
5. Ne jamais modifier les agents du partenaire (plugins/axelor/) - les surcharger dans un plugin axenr-*
6. Toujours incrementer la version apres ajout d'un composant
7. Ranger chaque composant dans la famille de son utilisateur (voir docs/ARCHITECTURE.md) :
   technique = developpeurs, fonctionnel = consultants, support = pilotage et marketing
8. Le contenu propre a un client va dans un plugin client-<nom>, jamais dans axenr-*
9. On ne modifie jamais un skill dans claude.ai : toute modification passe par une PR
