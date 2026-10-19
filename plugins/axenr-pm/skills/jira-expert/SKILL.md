---
name: jira-expert
description: >
  Expert Jira Cloud pour l'instance erp-axenr.atlassian.net : JQL, workflows et
  statuts, champs, contextes et ecrans, permissions et roles, versions et
  composants, boards, filtres, dashboards, automation, suivi des temps, REST
  API v3 et ADF, connecteurs MCP Atlassian et leurs pieges (champs custom
  10507/10508, duedate, transitions, liens, identite du compte). Declencheurs :
  « requete JQL », « filtre Jira », « workflow », « statut », « transition qui
  echoue », « champ obligatoire », « dashboard », « board », « automation »,
  « permission Jira », « erreur de l'API Jira », « No approval received »,
  « pourquoi je ne vois pas ce champ ». A utiliser AVANT d'affirmer qu'une
  option Jira existe : identifier d'abord le type de projet (team-managed ou
  company-managed). PAS pour : rediger ou organiser un ticket
  (organisateur-jira), ecrire une spec fonctionnelle (jira-spec-writer),
  prioriser la charge ou facturer les temps (skills de pilotage), noter une
  amelioration de la marketplace (skill-improvement-note).
metadata:
  owner: axenr
  family: support
---

# Skill — Jira Expert (AxENR / Atlassian Cloud)

## Environnement d'exécution

| Où | Comportement |
|---|---|
| claude.ai et Cowork | Connecteur Atlassian de l'utilisateur : lecture libre, écriture sur GO explicite, identité du compte vérifiée avant toute écriture. Sans connecteur, répondre et livrer JQL ou procédure à appliquer à la main. |
| Claude Code | Mêmes règles ; deux connecteurs peuvent coexister (« Atlassian » et « Atlassian MCP ») avec des noms d'outils différents (voir `references/rest-api-adf-mcp.md`). |

Consultant Jira senior pour l'instance **erp-axenr.atlassian.net**. Ce skill sert à répondre précisément sur l'administration et l'usage de Jira, à écrire du JQL fiable, à configurer workflows / champs / permissions / boards / dashboards / automation, et à cadrer les améliorations (projet **AC — Amélioration continue**) sans jamais inventer une option qui n'existe pas dans le bon type de projet.

> Ce fichier est un **routeur**. Il contient les réflexes et les antisèches les plus utilisés. Pour le détail d'un domaine, ouvrir le fichier `references/` correspondant (table de navigation plus bas).

---

## Réflexe n°1 — QUEL TYPE DE PROJET ?

Avant toute réponse de config, déterminer si le projet est **team-managed** ou **company-managed**. C'est LA source d'erreur : la même fonctionnalité se configure à des endroits totalement différents, et certaines n'existent que d'un côté.

Comment trancher (par ordre de fiabilité) :

1. **API** : `getVisibleJiraProjects` → le champ `"style"` vaut `"next-gen"` (team-managed) ou `"classic"` (company-managed). `"simplified": true` = team-managed.
2. **UI** : Paramètres du projet → en bas à gauche, mention « Projet géré par l'équipe » (team-managed) ou « Projet géré par l'entreprise » (company-managed).

Dans l'instance AxENR, à ce jour :

| Projet(s) | Type présumé | Config |
|-----------|--------------|--------|
| **AC — Amélioration continue** (clé AC, business/next-gen) | **team-managed** | Tout dans *Paramètres du projet* (workflow, champs, accès, versions) — propre au projet |
| **AR, PE, EMERAUDE, SYS, ASG, GMAO, ENERGIA** (projets clients migrés de Redmine) | **company-managed** | Via **schemes partagés** (workflow scheme, field config scheme, screen scheme, permission scheme…) + champs custom globaux (cf_10507 Version cible, cf_10508 Composant…) |

Attention : **Toujours revérifier** dans l'instance avant d'affirmer — ne pas se fier à cette table comme à une vérité gravée (cf. règle d'or R-Anti-hallucination). En cas de doute, appeler l'API.

Différences structurantes (détail complet → `references/project-types.md`) :

| Sujet | Team-managed (AC) | Company-managed (clients) |
|-------|-------------------|---------------------------|
| Où se configure ? | *Paramètres du projet* (autonome) | **Schemes** réutilisables entre projets |
| Champs custom | Propres au projet | **Globaux** avec **contextes** par projet/type |
| Workflow | Éditeur intégré, propre au projet | Workflow + Workflow scheme partageables |
| Champ obligatoire à une transition | Règle de transition **dans** le workflow du projet | **Validateur** sur la transition (souvent app JSU/JMWE) ou champ requis dans la Field Configuration |
| Rôles/accès | Accès projet (Administrateur/Membre/Visiteur) + rôles custom | **Permission scheme** + **rôles de projet** |
| Versions / Composants | Oui, propres au projet | Oui, propres au projet (mais champs Version pilotés par les schemes) |

---

## Contexte instance erp-axenr

- **Base** : `https://erp-axenr.atlassian.net`
- **cloudId** : `43c839be-4315-4f46-b5de-9be19b840556`
- **Champs custom AxENR connus** (company-managed, IDs figés — source mémoire projet) :
  - `customfield_10507` — **Version cible** : reste la référence, renseignée à la main. La bascule vers `fixVersion` (option B) a été abandonnée au 08/08/2026 (voir `references/versions-components.md`)
  - `customfield_10508` — **Composant AxENR**
  - `customfield_10509` — Loom · `10511` — PR · `10512` — Ticket AOS · `10513` — Version AOS · `10500` — SQL · `10456` — Drive · `10510` — Lien Redmine
- **Statuts FR migrés** (workflow client) : cycle 12 statuts, catégories *À faire / En cours / Terminé*.
- **Statuts observés sur AC** (team-managed) : `Ouvert`, `Planifié`, `En cours`, `Revue en cours`, `Terminé(e)`, `Rejeté`.
- **Labels de migration** : `redmine-<id>` (clé d'idempotence — ne jamais recréer un ticket déjà porteur de son label).

---

## Navigation — quand ouvrir quel fichier

| J'ai besoin de… | Ouvrir |
|-----------------|--------|
| Comprendre team vs company managed, migrer de l'un à l'autre | `references/project-types.md` |
| Écrire / déboguer une requête (recherche, filtre, board, gadget) | `references/jql.md` |
| Statuts, transitions, validateurs, conditions, post-fonctions, « champ requis au passage En cours » | `references/workflows-statuses.md` |
| Créer/rendre obligatoire un champ, field configuration, contextes, écrans | `references/fields-screens-config.md` |
| Versionnage par projet, fix versions, composants, leads | `references/versions-components.md` |
| Rôles, permission scheme, sécurité (masquer les temps au client), assignation restreinte | `references/permissions-roles-security.md` |
| Board Kanban/Scrum, colonnes, **card colors**, filtres partagés, **dashboards & gadgets** | `references/boards-filters-dashboards.md` |
| Règles d'automation (auto-assign, notifications, transitions auto) | `references/automation.md` |
| Suivi des temps, worklogs, config time tracking, Tempo, facturation | `references/time-tracking.md` |
| Appeler la REST API v3, écrire du contenu ADF, gotchas du MCP Atlassian | `references/rest-api-adf-mcp.md` |
| Migrer Redmine → Jira (mapping, idempotence, pièges) | `references/migration-redmine-jira.md` |
| Recettes prêtes pour les besoins récurrents AC (rôles, dashboards, filtres…) | `references/playbooks-axenr.md` |
| Pièges confirmés à la création / édition par le MCP (10507, 10508, `duedate`, `&`, transitions, liens, identité du compte) | `references/contraintes-api-mcp.md` |

---

## Antisèche JQL (les 90 % du quotidien)

Structure : `champ  opérateur  valeur(s)  [ORDER BY champ ASC|DESC]`

```jql
project = AC AND statusCategory != Done ORDER BY duedate ASC
assignee = currentUser() AND resolution = Unresolved
project in (AR, PE, EMERAUDE) AND status CHANGED TO "En cours" AFTER -7d
type = Bug AND created <= -14d AND statusCategory != Done
fixVersion = "V4.0" AND labels = redmine-1128
"Version cible[Dropdown]" = "V4.0"            # champ custom par son nom (crochets = type si ambigu)
cf[10507] = "V4.0"                             # champ custom par son id
duedate IS EMPTY OR assignee IS EMPTY
reporter WAS "Alexis Delhomme" BEFORE -30d
parent = AC-21                                 # enfants d'un ticket parent
```

Opérateurs clés : `=  !=  >  >=  <  <=  ~ (contient)  !~  IN  NOT IN  IS EMPTY  IS NOT EMPTY  WAS  WAS IN  CHANGED`.
Mots-clés : `AND  OR  NOT  ORDER BY`. Fonctions fréquentes : `currentUser()  now()  startOfDay()  endOfWeek()  membersOf("groupe")  -7d / 2w / 1M` (relatif).

Pièges :
- Utiliser `statusCategory` (New/Indeterminate/Done) plutôt que lister tous les statuts FR — robuste à l'ajout de statuts.
- `status = Done` ≠ `resolution IS NOT EMPTY`. Un ticket « Terminé » sans **résolution** ressort comme non résolu dans beaucoup de gadgets. Fixer la résolution à la transition finale.
- Valeurs avec espaces/accents → guillemets : `status = "Revue en cours"`.
- Nom d'affichage ambigu → préférer l'**accountId** (`assignee = "<accountId>"`) ou `cf[10507]`.

Détail complet (WAS/CHANGED, toutes les fonctions, tri, sous-requêtes) → `references/jql.md`.

---

## Règles d'or

- **R-Anti-hallucination** — Ne JAMAIS affirmer qu'une option/champ/statut existe ou non sans l'avoir vérifié dans l'instance (API ou UII), en tenant compte du **type de projet**. En low-code/config, l'absence dans un export ≠ absence réelle. Dire « je vérifie » puis vérifier.
- **R-Lecture seule par défaut** — Les tools de lecture (`searchJiraIssuesUsingJql`, `getJiraIssue`, `getVisibleJiraProjects`, `getTransitionsForJiraIssue`) sont libres. Toute **écriture** (créer/éditer un ticket, transition, commentaire, modif de config) attend un **GO explicite** du manager.
- **R-Idempotence** — Sur migration/traitement de masse : s'appuyer sur `labels = redmine-<id>` pour ne rien dupliquer. Piloter d'abord (1 ticket), vérifier, puis vague.
- **R-Étanchéité temps** — Les temps passés ne doivent JAMAIS être visibles côté client. Vérifier permissions *Browse* + *Work On/View worklogs* avant d'exposer un gadget temps (→ `references/permissions-roles-security.md`).
- **R-Sources** — Citer ses sources : clé du ticket (AC-xx), URL Jira, fichier de référence, ou lien doc Atlassian.

---

## Méthode de diagnostic d'un « bug » Jira

Beaucoup de « bugs » sont en réalité de la config ou une confusion de type de projet.

1. **Reproduire** et lire le message exact (souvent la clé est dedans : champ requis manquant, permission, transition invalide).
2. **Type de projet ?** (réflexe n°1). Si team-managed, ne pas chercher dans les schemes globaux — tout est dans *Paramètres du projet*.
3. **Palier config** : champ requis (Field Configuration / règle de transition) ? permission (Permission scheme / accès projet) ? contexte de champ absent sur ce projet/type ?
4. **Palier données** : filtrer en JQL pour isoler (ex. `project = X AND <champ> IS EMPTY`).
5. **Palier API** : `getJiraIssue` avec `fields=*all` pour voir la valeur réelle d'un champ custom ; `getTransitionsForJiraIssue` pour voir les transitions offertes à l'état courant.
6. Ne conclure « c'est un bug produit » qu'après avoir écarté droits → config → contexte → données.

---

## Sources officielles (à jour, à citer)

- JQL — opérateurs : https://support.atlassian.com/jira-software-cloud/docs/jql-operators/
- JQL — fonctions : https://support.atlassian.com/jira-software-cloud/docs/jql-functions/
- JQL — champs : https://support.atlassian.com/jira-software-cloud/docs/advanced-search-reference-jql-fields/
- Recherche avancée (JSM) : https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/
- REST API v3 : https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- ADF (Atlassian Document Format) : https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/

## Version
- 1.1.0 — 2026-10-19 — reprise dans la marketplace AxENR, contraintes MCP de l'inventaire Chef de projet
