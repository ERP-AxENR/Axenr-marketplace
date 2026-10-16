# Contributing to AxENR Marketplace

Guide pour ajouter des skills, agents et commandes. Avant tout ajout, lire
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) : chaque composant va dans la
famille de son utilisateur (socle, technique, fonctionnel, support, client).

Pour une simple amelioration d'un skill existant, pas besoin de ce guide :
dire « Note-le pour le skill » a Claude, la fiche sera integree le vendredi.

---

## Ajouter un Skill (cas par defaut)

### 1. Choisir le plugin

Arbre de decision dans `docs/ARCHITECTURE.md`, section « Ou ranger un nouveau
composant ». Un contenu propre a un client va dans `plugins/client-<nom>/`.

### 2. Creer le dossier

```bash
mkdir -p plugins/<plugin>/skills/<nom-skill>
$EDITOR plugins/<plugin>/skills/<nom-skill>/SKILL.md
```

Le fichier s'appelle **toujours** `SKILL.md`. Sinon le skill n'est jamais charge.

### 3. Frontmatter

```markdown
---
name: <nom-skill>
description: >
  Ce que fait le skill, quand le charger. Declencheurs : « ... », « ... ».
  PAS pour : <cas voisins> (<autre-skill>).
metadata:
  owner: axenr
---
```

- `name` = nom du dossier, kebab-case anglais, 64 caracteres maximum.
- `description` : 1024 caracteres maximum.
- Cles autorisees uniquement : `name`, `description`, `license`, `compatibility`,
  `metadata`, `allowed-tools`. Toute autre information va sous `metadata`.

### 4. Fichiers d'appui

`references/` (documentation longue), `scripts/` (code), `resources/`
(exemples). Le `SKILL.md` reste court et renvoie vers eux.

---

## Ajouter un Agent (Claude Code uniquement)

Un agent ne fonctionne pas dans claude.ai ni Cowork. Ne creer un agent que pour
une tache autonome en plusieurs etapes ; sinon, faire un skill.

```bash
plugins/<plugin>/agents/<nom-agent>.md
```

```markdown
---
name: <nom-agent>
description: MUST BE USED pour ... Declencheurs ...
---

# <Nom Agent>

## ROLE
## INPUTS
## WORKFLOW
## CRITICAL RULES
```

Les exemples et ressources de l'agent vont dans `plugins/<plugin>/resources/`,
jamais dans un sous-dossier de `agents/` (ils seraient charges comme agents).

---

## Ajouter une Commande

```bash
plugins/<plugin>/commands/<nom-command>.md
```

Elle s'appelle ensuite `/<plugin>:<nom-command>`.

---

## Ajouter un Plugin

1. `plugins/<plugin>/.claude-plugin/plugin.json` (name, version courante, description, author).
2. Declaration dans `.claude-plugin/marketplace.json` avec `category` :
   `socle`, `technique`, `fonctionnel` ou `support`.
3. Mise a jour de `docs/ARCHITECTURE.md` et de `.github/CODEOWNERS`.

---

## Conventions

| Element | Convention |
|---------|------------|
| Noms de fichiers et de composants | kebab-case, anglais |
| Documentation | Francais pour user-facing, anglais pour code |
| Commits | Conventional commits : `feat(<plugin>): ...`, `fix(<plugin>): ...` |
| Emojis | Interdits partout |
| Secrets | Interdits : variables d'environnement uniquement |

## Checklist avant PR

- [ ] Composant range dans la bonne famille et le bon plugin
- [ ] Skill : fichier `SKILL.md`, frontmatter conforme
- [ ] `python3 scripts/marketplace-doctor.py` sans CRITICAL
- [ ] `./scripts/bump-version.sh auto` lance
- [ ] Teste localement dans Claude Code
