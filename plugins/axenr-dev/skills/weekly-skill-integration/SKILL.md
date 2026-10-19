---
name: weekly-skill-integration
description: >
  Integration hebdomadaire des fiches d'amelioration de skills : lit les tickets
  Jira « AxENR Marketplace - Notre cerveau » etiquetes amelioration-skill, met a jour les skills de la
  marketplace AxENR sur une branche de la semaine, lance le doctor et ouvre une
  seule PR pour relecture d'Alexis. Declencheurs : « integre les notes de la
  semaine », « integration du vendredi », « traite les fiches d'amelioration ».
  Claude Code uniquement. PAS pour : rediger une fiche (skill-improvement-note).
compatibility: Claude Code, avec git, gh et le connecteur Atlassian.
metadata:
  owner: axenr
  process: on apprend, on note, on publie le vendredi
---

# Integre les notes de la semaine

Une branche, une PR par semaine. On ne merge jamais : Alexis relit et merge.

## 0. Preparer le depot

- Travailler dans un **clone** de `ERP-AxENR/Axenr-marketplace`, jamais dans
  `~/.claude/plugins/marketplaces/...` (copie d'installation, ecrasee a chaque
  mise a jour).
- `git switch main && git pull --ff-only`, puis
  `git switch -c semaine/$(date +%G-S%V)`.

## 1. Recuperer les fiches

Projet Jira `AMNC` (« AxENR Marketplace - Notre cerveau ») :

```
project = AMNC AND labels = amelioration-skill AND statusCategory != Done ORDER BY created ASC
```

Afficher le tableau : ticket, skill cible, type, portee. Si aucune fiche : le
dire et s'arreter.

## 2. Traiter chaque fiche

1. Lire le skill cible **en entier** (`plugins/<plugin>/skills/<nom>/SKILL.md`
   et ses `references/`).
2. Appliquer la modification minimale dans la section indiquee. Ne pas
   reecrire ce qui n'est pas concerne.
3. Portee client : le contenu va dans `plugins/client-<nom>/`. Si ce plugin
   n'existe pas, le creer (`.claude-plugin/plugin.json`, declaration dans
   `.claude-plugin/marketplace.json` avec la version courante).
4. Nouveau skill : dossier `skills/<nom>/SKILL.md`, frontmatter limite a
   name, description, license, compatibility, metadata, allowed-tools ;
   description de 1024 caracteres maximum, avec declencheurs et « PAS pour ».
5. Fiche floue ou sans preuve : commenter le ticket avec la question, ne pas
   la traiter, passer a la suivante.
6. Un commit par fiche :
   `feat(<plugin>): <titre> (<CLE-n>)` ou `fix(<plugin>): ...`.

## 3. Controler

```bash
python3 scripts/marketplace-doctor.py
./scripts/bump-version.sh auto
```

Le doctor doit etre au vert (aucun CRITICAL). Si des suites `claude plugin
eval` existent pour les skills modifies, les lancer.

## 4. Ouvrir la PR

- `git push -u origin semaine/<AAAA-Sss>`
- `gh pr create --base main` avec : le tableau ticket -> skill -> modification,
  les fiches ignorees et pourquoi, le resultat du doctor.
- Demander la relecture d'Alexis. **Ne jamais merger.**

## 5. Apres le merge (le vendredi)

- Commenter chaque ticket traite avec la version publiee, puis le passer a
  Termine.
- Rediger la note « Quoi de neuf cette semaine » (5 lignes, une par
  amelioration notable) pour l'equipe.
