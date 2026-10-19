# JQL — Jira Query Language (référence complète)

Docs : [opérateurs](https://support.atlassian.com/jira-software-cloud/docs/jql-operators/) · [fonctions](https://support.atlassian.com/jira-software-cloud/docs/jql-functions/) · [champs](https://support.atlassian.com/jira-software-cloud/docs/advanced-search-reference-jql-fields/)

## Anatomie

```
<champ> <opérateur> <valeur|fonction> [AND|OR|NOT ...] [ORDER BY <champ> ASC|DESC]
```

Une clause = champ + opérateur + valeur. On combine les clauses avec `AND` / `OR` / `NOT` et des parenthèses.

## Opérateurs

| Opérateur | Sens | Exemple |
|-----------|------|---------|
| `=` / `!=` | égal / différent | `status = "En cours"` |
| `>` `>=` `<` `<=` | comparaison (dates, nombres, priorité) | `created >= -7d` |
| `~` / `!~` | contient / ne contient pas (texte) | `summary ~ "version"` |
| `IN` / `NOT IN` | dans une liste | `project IN (AR, PE)` |
| `IS EMPTY` / `IS NOT EMPTY` | champ vide / renseigné | `assignee IS EMPTY` |
| `WAS` / `WAS IN` / `WAS NOT` | valeur historique | `status WAS "Ouvert"` |
| `CHANGED` | a changé | `assignee CHANGED` |

Prédicats d'historique (avec WAS/CHANGED) : `AFTER`, `BEFORE`, `ON`, `DURING`, `BY`, `FROM`, `TO`.
```jql
status CHANGED TO "En cours" AFTER startOfWeek() BY currentUser()
assignee WAS "<accountId>" DURING ("2026/06/01","2026/06/30")
```

## Champs fréquents

`project, issuetype (type), status, statusCategory, resolution, priority, assignee, reporter, creator, created, updated, resolved, duedate, labels, component, fixVersion, affectedVersion, parent, summary, description, text, watcher, sprint`.

Champ custom : par **nom** `"Version cible"` (ajouter `[Dropdown]`/`[Labels]`… si ambigu) ou par **id** `cf[10507]`.

## Fonctions utiles

| Fonction | Usage |
|----------|-------|
| `currentUser()` | l'utilisateur courant |
| `membersOf("groupe")` | membres d'un groupe (assignee IN membersOf(...)) |
| `now()`, `startOfDay()`, `endOfDay()`, `startOfWeek()`, `endOfWeek()`, `startOfMonth()`, `endOfMonth()` | ancres temporelles (accepte un décalage : `startOfMonth(-1)`) |
| `-7d 2w 1M 1y` | durées relatives (d=jour, w=semaine, M=mois, y=an) |
| `EMPTY` | valeur vide (avec `IS`) |
| `latestReleasedVersion(PROJ)`, `unreleasedVersions(PROJ)`, `earliestUnreleasedVersion(PROJ)` | versions |
| `linkedIssues("KEY")` | tickets liés |

## Tri

`ORDER BY duedate ASC, priority DESC` — les valeurs vides remontent en dernier en ASC (comportement voulu pour « tâches sans échéance en bas »).

## Recettes AxENR prêtes à l'emploi

```jql
# Mes tâches actives, échéance en tête
assignee = currentUser() AND statusCategory != Done ORDER BY duedate ASC

# Backlog à assainir : sans échéance OU sans assigné
(duedate IS EMPTY OR assignee IS EMPTY) AND statusCategory != Done ORDER BY created DESC

# Bugs qui traînent (pour card colors : voir boards-filters-dashboards.md)
type = Bug AND statusCategory != Done ORDER BY created ASC

# Tickets d'un jalon / version
fixVersion = "V4.0" ORDER BY status

# Ready for testing multi-projets, pour Ana/Alexis (cf AC-22)
status = "Revue en cours" AND project IN (AR, PE, EMERAUDE, SYS) ORDER BY updated DESC

# Retrouver un ticket migré par son origine Redmine
labels = redmine-1128

# Charge d'une personne
assignee = "<accountId>" AND statusCategory != Done ORDER BY priority DESC

# Activité récente d'un projet
project = SYS AND updated >= -3d ORDER BY updated DESC
```

## Pièges & bonnes pratiques

- **`statusCategory` > liste de statuts** : `statusCategory != Done` survit à l'ajout/renommage de statuts FR. Catégories : `New` (À faire), `Indeterminate` (En cours), `Done` (Terminé).
- **Statut vs résolution** : un ticket peut être en statut « Terminé » avec **résolution vide** → il ressort « non résolu » (`resolution = Unresolved`) dans les gadgets et fausse les rapports. Toujours **poser la résolution** via une post-fonction sur la transition finale (→ `workflows-statuses.md`).
- **Espaces/accents** → guillemets doubles : `"Revue en cours"`.
- **Homonymes d'utilisateurs** → préférer l'`accountId` (stable) au nom d'affichage.
- **Team-managed** : un champ « local » n'a pas d'id partagé entre projets — le requêter par nom ne cible pas forcément le même champ d'un projet à l'autre.
- **`project = AC`** dans un board/filtre : un board Kanban repose sur un **filtre** enregistré ; le JQL du board définit le périmètre, l'ordre des colonnes vient du mapping statut→colonne (pas du ORDER BY).
- **Performance** : éviter `~ "*"` en tête ; borner par `project` et une fenêtre `updated >= -Xd` sur les grosses instances.
