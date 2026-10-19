# Migration Redmine → Jira (AxENR)

Contexte : reprise des projets Redmine vers Jira company-managed. Des **sous-agents dédiés** existent (`agent-migration-redmine-jira:*` : audits + `migration-executor`). Ce fichier = repères transverses.

## Principes non négociables

- **Lecture seule par défaut** ; **écriture sur GO explicite** uniquement.
- **Idempotence** via label **`redmine-<id>`** sur chaque ticket Jira : c'est la clé pour ne jamais recréer/dupliquer. Toujours vérifier `labels = redmine-<id>` avant de créer.
- **Pilote puis vague** : traiter 1 ticket, vérifier, puis lot.
- **Cause racine du chaos AR** = **double migration** (tickets importés deux fois). Leçon : contrôler l'inventaire source vs cible AVANT d'importer.

## Mapping Redmine → Jira

| Redmine | Jira |
|---------|------|
| Issue | Issue (Story/Tâche/Bug selon tracker) |
| Tracker | Issue type |
| Module / regroupement budgétaire | **Epic** (poste budgétaire) — souvent déjà créés, NE PAS recréer |
| Statuts Redmine | 12 statuts FR (catégories À faire/En cours/Terminé) |
| Version cible | `cf_10507` (la bascule vers `fixVersion` a été abandonnée au 08/08/2026) |
| Parent/enfant, relations | Parent (Epic link) + liens `relates` |
| Champs perso | champs custom AxENR (cf_10508 Composant, 10509 Loom, 10511 PR, 10512 Ticket AOS, 10513 Version AOS, 10500 SQL, 10456 Drive, 10510 Lien Redmine) |
| Temps passés | worklogs (Attention : jamais exposés au client) |
| Pièces jointes | attachments (auditer présence/intégrité) |

## Pièges vécus (à ne pas répéter)

- **Bulk Delete embarque les Epics** : un delete de masse mal filtré a supprimé les Epics budget → recréation manuelle. Leçon : exclure `issuetype != Epic` des suppressions de masse.
- **Auto-assign Component Lead** écrase l'assignee importé → désactiver pendant la migration.
- **Règle Epic rollback** (« Epic repasse En cours quand un enfant bouge ») : by design mais gênante → désactivée chez les clients.
- **Doublons de champs** custom (Version cible ×2…) : purgés, 1 exemplaire/champ.
- **Orphelins / sans assigné** : à reventiler après import (ne pas laisser sous un ticket « fourre-tout » par défaut).

## Audits disponibles (sous-agents, lecture seule)

`audit-idempotence-dedup` (labels, doublons, couverture) · `audit-links-hierarchy` (liens + Epic + hiérarchie) · `audit-status-workflow` · `audit-custom-fields` · `audit-components` · `audit-version-fields` · `audit-worklogs-budget` (temps + étanchéité) · `audit-attachments` · `audit-automations-security`. Les lancer AVANT toute prod pour croiser fichiers × base.

## État de complétude (repère mémoire, à revérifier)
AR ~269 (dédoublonné) · PE 474 · EMERAUDE 266 · SYS 136 (le plus propre : 0 doublon, 0 sans assigné). Toujours revérifier en direct plutôt que se fier à un chiffre figé.
