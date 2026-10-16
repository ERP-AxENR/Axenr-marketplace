# AxENR Marketplace

Marketplace interne AxENR : la methode metier ENR, ERP et GMAO d'AxENR,
partagee entre les consultants (claude.ai, Cowork) et les developpeurs
(Claude Code). Architecture, regles de rangement et feuille de route :
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

**Mainteneur** : Fadel Benomar - Developer Backend & IA @ AxENR

---

## Je suis...

| Profil | Ce que j'utilise | Plugins |
|---|---|---|
| Developpeur | Claude Code | `axenr-core`, `axenr-dev`, `axelor` (+ plugins fonctionnels au besoin) |
| Consultant ERP / GMAO | claude.ai, Cowork | `axenr-core`, `axenr-erp`, `axenr-gmao`, `axenr-data`, `axenr-permissions` |
| Pilotage, chef de projet, marketing | claude.ai, Cowork | `axenr-core` (+ plugins support a venir) |

Sur claude.ai et Cowork, les plugins arrivent par la synchronisation de
l'organisation : rien a installer. La suite de ce README concerne Claude Code.

## Installation (Claude Code)

```
/plugin marketplace add fbe-axenr/Axenr-marketplace
/plugin install axenr-core@fbe-axenr-Axenr-marketplace
/plugin install axenr-dev@fbe-axenr-Axenr-marketplace
```

Puis `/plugin`, onglet **Installed**, pour verifier.

Depuis la v1 (plugin unique `axenr`) : voir la section « Migration depuis la
v1 » de [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Commandes

### Technique (`axenr-dev`)

| Commande | Description |
|----------|-------------|
| `/axenr-dev:solve-ticket` | Resoudre 1 ticket autonomement |
| `/axenr-dev:solve-batch` | Resoudre 2 tickets en parallele |
| `/axenr-dev:review-pr <url\|#N>` | Review PR AxENR (axelor:code-reviewer + checks specifiques AxENR) |
| `/axenr-dev:montee-version <version>` | Montee de version AOS/AOP |
| `/axenr-dev:doctor` | Audit de sante de la marketplace |
| `/axenr-dev:consolidate-lessons` | Fusionne les lecons dupliquees et promeut celles a 3+ occurrences |
| `/axenr-dev:sync-lessons` | Pousse les lecons locales vers le fichier partage via PR |
| `/axenr-dev:bump-version` | Bump de la version AxENR unique |

### Fonctionnel

| Commande | Description |
|----------|-------------|
| `/axenr-data:import-help` | Preparer ou corriger un import Axelor |
| `/axenr-data:template-expert` | Creer ou corriger un template Word XDocReport |
| `/axenr-data:bi-architect` | Requetes SQL et dashboards Superset |
| `/axenr-erp:bareme` | Concevoir un bareme tarifaire |

## Ameliorer un skill : le process du vendredi

1. Pendant la semaine, n'importe qui dit a Claude : **« Note-le pour le skill »**.
   Claude cree une fiche dans le projet Jira AxENR MARKETPLACE.
2. Le vendredi, le developpeur dit a Claude Code : **« Integre les notes de la semaine »**.
   Claude Code met a jour les skills et ouvre une PR.
3. Alexis relit et merge. La release et la synchronisation sont automatiques.

On ne modifie jamais un skill directement dans claude.ai.

## Usage du ticket-solver

```
/axenr-dev:solve-ticket axenr-app wip #750 | Add estimated power field | decimal field on Opportunity
/axenr-dev:solve-batch axenr-app wip #750|Add power field|decimal on Opportunity ,, #751|Add panel notes|notes panel on SaleOrder form
```

| Argument | Description | Exemples |
|----------|-------------|----------|
| project | Nom du projet | `axenr-app`, `axenr-mobile` |
| branch | Branche de travail | `dev`, `wip`, `axenr` |
| number | Numero du ticket | `#750` |
| title | Titre court | `Add estimated power field` |
| description | Description detaillee | `decimal field on Opportunity, calculated from numberOfModules * 400 / 1000` |

## Auto-apprentissage (axenr-dev)

1. **Detection** : l'agent valide son code avec les agents Axelor
2. **Correction** : il corrige les erreurs trouvees (max 3 retries)
3. **Enregistrement** : chaque erreur est enregistree via error-learner
4. **Promotion** : a 3 occurrences d'un pattern, knowledge-updater le promeut dans `CLAUDE.md`
5. **Prevention** : au prochain ticket, pre-flight-checker charge les lecons pertinentes

## Mise a jour

```
/plugin marketplace update fbe-axenr-Axenr-marketplace
/plugin update --all
```

### Auto-release (cote mainteneur)

A chaque push sur `main` qui modifie `plugins/` (hors partenaire `axelor`), le
workflow `.github/workflows/release.yml` :

1. Detecte le type de bump via conventional commits (`feat`=minor, `fix`=patch, `BREAKING`=major)
2. Bumpe `marketplace.json` et tous les `plugin.json` AxENR (version unique)
3. Commit `chore(release): bump axenr plugins to vX.Y.Z`
4. Tag et publie une GitHub Release

`.github/workflows/ci.yml` lance le doctor et refuse toute PR qui touche
`plugins/` sans bump de `marketplace.json`.

```
./scripts/bump-version.sh auto
python3 scripts/marketplace-doctor.py
```
