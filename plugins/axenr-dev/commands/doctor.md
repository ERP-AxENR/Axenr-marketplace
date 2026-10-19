---
description: Audit de sante du marketplace AxENR (versions sync, frontmatters, references, doublons, lecons stagnantes).
argument-hint: [--strict]
---

# /axenr-dev:doctor

> `<marketplace_path>` : clone de travail de la marketplace (depot git dont l'origin est
> `fbe-axenr/Axenr-marketplace`), par exemple `/Users/macbook/Desktop/Projects/Axenr-marketplace`.
> Jamais la copie d'installation `~/.claude/plugins/marketplaces/...`. Si introuvable, demander le chemin.

Lance le skill marketplace-doctor et affiche le rapport.

Usage :

```
/axenr-dev:doctor
/axenr-dev:doctor --strict
```

## EXECUTION

### Etape 1 : Exec le script

Si `scripts/marketplace-doctor.py` existe :

```bash
python3 <marketplace_path>/scripts/marketplace-doctor.py
```

Sinon, executer les checks via Bash/Read/Grep en suivant marketplace-doctor.md.

### Etape 2 : Parser la sortie JSON et presenter

```markdown
# Marketplace Doctor

- Statut : <ok | warnings | critical>
- Exit : <0 | 1>

## CRITICAL (N)
- [VER-SYNC] ...
  Fix : ...

## WARN (N)
- [ORPHAN-SKILL] ...

## INFO
- Lecons : 55 (0 promues - taux 0%)
- Agents : N, Skills : N, Commands : N
- Derniere modif : YYYY-MM-DD / Derniere version : X.Y.Z
```

### Etape 3 : Si critical present, proposer fix

Pour chaque check CRITICAL avec un `fix` disponible, proposer la correction
automatique en demandant confirmation :

```
Voulez-vous que je bumpe marketplace.json de 1.3.0 -> 1.4.0 et plugin.json
de 1.5.0 -> 1.6.0 ? (oui/non)
```
