---
description: Bump version marketplace.json + plugin.json synchronise selon conventional commits. patch/minor/major/auto.
argument-hint: [patch|minor|major|auto]
---

# /axenr-dev:bump-version

Increment synchronise de la version du marketplace pour que `/plugin update` detecte les nouveautes.

## USAGE

```
/axenr-dev:bump-version          # auto (analyse les commits depuis dernier tag)
/axenr-dev:bump-version patch    # 1.3.0 -> 1.3.1
/axenr-dev:bump-version minor    # 1.3.0 -> 1.4.0
/axenr-dev:bump-version major    # 1.3.0 -> 2.0.0
```

## LOGIQUE AUTO

```
Lire commits depuis dernier tag git :
  git log $(git describe --tags --abbrev=0 2>/dev/null)..HEAD --oneline

- Si un commit contient "BREAKING CHANGE" ou "!" -> major
- Sinon si un commit "feat:" -> minor
- Sinon -> patch
```

## ETAPES

### Etape 1 : Pre-flight

Executer `/axenr-dev:doctor --strict`. Si critical, refuser (sauf --force).

### Etape 2 : Determiner la nouvelle version

- Lire `.claude-plugin/marketplace.json` -> current_version
- Appliquer le type de bump -> new_version

### Etape 3 : Mettre a jour les versions (version unique AxENR)

Lancer `./scripts/bump-version.sh <type>`. Le script met a jour :
- `.claude-plugin/marketplace.json` : `version` et la version de chaque plugin AxENR ;
- `plugins/<plugin>/.claude-plugin/plugin.json` pour chaque plugin AxENR.

Tous les plugins AxENR partagent la meme version (une release par semaine).
Ne PAS toucher la version du plugin axelor partenaire.

### Etape 4 : Commit + tag

```bash
git add .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json
GIT_COMMITTER_NAME="fbe-axenr" GIT_COMMITTER_EMAIL="f.benomar@erp-axenr.fr" \
  git commit --author="fbe-axenr <f.benomar@erp-axenr.fr>" \
  -m "chore(release): bump axenr plugins to v<new_version>"
git tag -a "v<new_version>" -m "v<new_version>"
```

### Etape 5 : Push + tag

Demander confirmation avant :

```
git push origin main
git push origin "v<new_version>"
```

### Etape 6 : Notifier l'utilisateur

```
Version bumpee : <current> -> <new>

Pour mettre a jour tes installations Claude Code :

  /plugin marketplace update fbe-axenr-Axenr-marketplace
  /plugin update <plugin>@fbe-axenr-Axenr-marketplace   (axenr-core, axenr-dev, ...)

Ou tout d'un coup (Claude Code 0.57+) :

  /plugin update --all
```
