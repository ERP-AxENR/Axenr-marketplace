---
description: Review une Pull Request AxENR avec le reviewer AxENR + Axelor partner code-reviewer. Produit un rapport structure avec verdict et severites.
argument-hint: <pr-url>
---

# /axenr-dev:review-pr

> `<marketplace_path>` : clone de travail de la marketplace (depot git dont l'origin est
> `fbe-axenr/Axenr-marketplace`), par exemple `/Users/macbook/Desktop/Projects/Axenr-marketplace`.
> Jamais la copie d'installation `~/.claude/plugins/marketplaces/...`. Si introuvable, demander le chemin.

Usage :

```
/axenr-dev:review-pr https://github.com/ERP-AxENR/axenr-app/pull/47
```

Ou avec un numero si repo courant :

```
/axenr-dev:review-pr #47
```

## ARGUMENT PARSING

1. Si l'argument est un numero (#NN ou NN) et le cwd est dans un repo AxENR :
   - pr_url = `https://github.com/ERP-AxENR/<repo-courant>/pull/NN`
2. Si URL GitHub complete : extraire owner/repo/number
3. Detecter le projet :
   - repo=axenr-app -> project=axenr-app
   - repo=axenr-mobile -> project=axenr-mobile

## ETAPES

### Etape 1 : Recuperer le diff

Executer en parallele :

```bash
gh pr view <N> --repo <owner>/<repo> --json title,headRefName,baseRefName,author,body,files,commits
gh pr diff <N> --repo <owner>/<repo>
```

Extraire :
- titre PR -> pour meta checks
- branche source -> extraire #NNN du ticket
- liste des fichiers modifies
- diff complet
- commits

### Etape 2 : Deleguer au pr-reviewer-axenr

Appeler l'agent via Agent tool :

```
subagent_type: pr-reviewer-axenr
prompt: |
  Review la Pull Request suivante selon ton GATE SYSTEM complet.

  PR URL: <pr_url>
  Project: <project>
  Project Path: <auto-detect : /Users/macbook/Desktop/Projects/<repo>>
  Marketplace Path: <marketplace_path>
  Ticket Number: <extracted>

  Titre PR: <title>
  Branche: <head_ref_name>
  Base: <base_ref_name>
  Auteur: <author>

  Description:
  <body>

  Fichiers modifies:
  <files_list>

  Commits:
  <commits_list>

  Diff:
  <full_diff>

  Produis un rapport Markdown structure selon ton FORMAT RAPPORT.
  En PHASE 4, invoque obligatoirement axelor:code-reviewer et les
  validateurs Axelor partenaire pertinents selon le type de fichiers.
```

### Etape 3 : Afficher le rapport

Le rapport Markdown retourne par l'agent est affiche tel quel dans la conversation.

### Etape 4 : Proposer actions de suivi

A la fin du rapport, proposer :

```
Actions disponibles :
1. Creer un commentaire recapitulatif sur la PR -> gh pr review <N> --comment -b "<rapport>"
2. Demander des changements -> gh pr review <N> --request-changes -b "<rapport>"
3. Approuver -> gh pr review <N> --approve -b "<rapport>"
4. Enregistrer les violations dans LESSONS-LEARNED (auto si CRITICAL/HIGH)
```

NE PAS executer ces actions automatiquement. Demander confirmation de l'utilisateur.

## FALLBACK

Si `gh` n'est pas installe ou non authentifie :
- Demander a l'utilisateur d'exporter le diff : `gh pr diff <N> > /tmp/pr-<N>.diff`
- Puis relancer avec le chemin local

## EXEMPLE DE SORTIE

Voir agents/pr-reviewer-axenr.md section FORMAT RAPPORT.
