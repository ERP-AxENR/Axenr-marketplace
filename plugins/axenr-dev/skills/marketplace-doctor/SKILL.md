---
name: marketplace-doctor
description: Validates marketplace integrity - version sync between marketplace.json and plugin.json, frontmatter presence, file references, JSON validity, orphan detection. Run before commit or via /axenr-dev:doctor.
---

# Marketplace Doctor

> Auditeur de sante du marketplace AxENR. Detecte les incoherences qui empechent Claude Code de charger correctement les agents/skills/commands apres un /plugin update.

## POURQUOI

Le marketplace ne valide rien. Si on oublie de bumper la version, les nouveaux agents ne sont pas detectes. Si un skill reference un fichier qui n'existe plus, le chargement echoue silencieusement.

## ROLE

Lister tous les problemes bloquants ou suspects, classes par severite, avec un code de retour exploitable par un hook Git ou la CI.

## INPUTS

| Input | Format |
|-------|--------|
| marketplace_path | Chemin absolu vers le repo marketplace |
| mode | `strict` (exit 1 sur WARN) / `lax` (exit 1 uniquement sur CRITICAL) |

## OUTPUTS

```
{
  "status": "ok" | "warnings" | "critical",
  "exit_code": 0 | 1,
  "checks": [
    { "id": "VER-SYNC", "severity": "CRITICAL|WARN|INFO", "message": "...", "fix": "..." }
  ],
  "summary": { "critical": N, "warnings": N, "info": N }
}
```

## CHECKS

### CRITICAL (bloque le chargement du plugin)

| ID | Check |
|----|-------|
| VER-SYNC | marketplace.json version == plugin.json version |
| VER-BUMP | Si fichiers agents/skills/commands modifies depuis dernier tag : version bumpee |
| JSON-VALID | marketplace.json et plugin.json parsables |
| PLUGIN-REF | Chaque plugin declare dans marketplace.json existe sur disque |
| FRONTMATTER | Chaque .md dans agents/ et skills/ a un frontmatter valide (name, description) |
| FILE-REF-AGENTS | Les agents references dans commands/*.md existent |
| FILE-REF-SKILLS | Les skills references dans agents/*.md existent |
| DUPLICATE-NAME | Pas de nom d'agent/skill/command duplique |

### WARN (fonctionne mais a risque)

| ID | Check |
|----|-------|
| ORPHAN-SKILL | Skill jamais reference dans un agent/command/CLAUDE.md |
| EMOJI-DETECTED | Emoji detecte dans .md (viole regle AxENR "NO EMOJIS") |
| FR-IN-CODE | Texte francais dans un bloc code/frontmatter |
| STALE-LESSONS | LESSONS-LEARNED.md pas mis a jour depuis 30 jours |
| LARGE-AGENT | Fichier agent > 800 lignes (candidat au split) |

### INFO

| ID | Check |
|----|-------|
| LESSONS-STATS | Nombre de lecons, promues, taux |
| COMPONENT-COUNT | Nombre d'agents / skills / commands |
| VERSION-GAP | Derniere modif vs derniere version bumpee |

## LOGIQUE

```
1. Lire .claude-plugin/marketplace.json -> v_marketplace
2. Pour chaque plugin.source declare :
   a) Lire plugins/<name>/.claude-plugin/plugin.json -> v_plugin
   b) CRITICAL VER-SYNC si v_marketplace != v_plugin pour ce plugin

3. Glob plugins/*/agents/*.md + skills/*/*.md + commands/*.md
   a) Parser frontmatter YAML
   b) CRITICAL FRONTMATTER si manquant ou incomplet
   c) WARN EMOJI-DETECTED si regex emoji match

4. Construire l'index des noms (agent/skill/command)
   a) CRITICAL DUPLICATE-NAME si collision

5. Resolver les references :
   a) Dans agents/*.md, chercher "skill:" ou noms de skills
   b) Dans commands/*.md, chercher "agent:" ou noms d'agents
   c) CRITICAL FILE-REF-* si reference pointe vers inexistant

6. git log --since="last tag" -- plugins/
   a) Si fichiers modifies ET version pas bumpee -> CRITICAL VER-BUMP

7. Agreger, trier par severite, retourner rapport
```

## USAGE LOCAL

Appele via la commande `/axenr-dev:doctor` (voir commands/doctor.md).

## USAGE CI

Le workflow `.github/workflows/ci.yml` execute l'equivalent bash :

```bash
# Strict mode pour CI
python3 scripts/marketplace-doctor.py --strict
```

## INTEGRATION PRE-COMMIT

Optionnel, hook local `.git/hooks/pre-commit` :

```bash
#!/bin/bash
python3 scripts/marketplace-doctor.py --strict || {
  echo "Marketplace doctor failed. Run /axenr-dev:doctor for details."
  exit 1
}
```
