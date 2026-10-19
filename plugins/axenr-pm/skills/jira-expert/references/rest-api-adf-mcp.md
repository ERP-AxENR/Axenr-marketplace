# REST API v3, ADF & MCP Atlassian

## REST API v3 (Cloud)

Base : `https://erp-axenr.atlassian.net/rest/api/3/`. Auth : email + **API token** (Basic) ou OAuth. Docs : https://developer.atlassian.com/cloud/jira/platform/rest/v3/

Endpoints clés :
| Besoin | Endpoint |
|--------|----------|
| Chercher (JQL) | `POST /rest/api/3/search/jql` (nouvelle recherche paginée par `nextPageToken`) |
| Lire un ticket | `GET /rest/api/3/issue/{key}?fields=*all` |
| Créer / éditer | `POST /rest/api/3/issue` · `PUT /rest/api/3/issue/{key}` |
| Transitions dispo / exécuter | `GET|POST /rest/api/3/issue/{key}/transitions` |
| Champs (dont custom) | `GET /rest/api/3/field` |
| Métadonnées création | `GET /rest/api/3/issue/createmeta` |
| Worklogs | `GET|POST /rest/api/3/issue/{key}/worklog` |
| Versions / composants | `/rest/api/3/project/{key}/versions` · `/components` |

Attention : Migration en cours côté Atlassian : les anciens `search` avec `startAt/total` sont dépréciés au profit de la **pagination par token** (`nextPageToken`) et le **total** n'est plus renvoyé par défaut (il faut le demander explicitement / le calculer).

## ADF — Atlassian Document Format

Les champs riches (description, commentaires, environment) ne sont **pas** du Markdown : c'est du **JSON ADF**. Docs : https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/

Squelette minimal :
```json
{ "type": "doc", "version": 1, "content": [
  { "type": "paragraph", "content": [ { "type": "text", "text": "Bonjour" } ] }
] }
```
Nœuds courants : `paragraph`, `heading` (attrs.level), `bulletList`/`orderedList`+`listItem`, `codeBlock`, `table`, `mediaSingle`, `mention`, `emoji`, marks `strong`/`em`/`code`/`link`.
- En **lecture**, demander le format lisible si l'outil le permet (`responseContentFormat: "markdown"`), sinon parser l'ADF.
- En **écriture** via API brute, fournir de l'ADF valide (pas du texte Markdown, qui s'afficherait littéralement).

## MCP Atlassian

Deux connecteurs coexistent selon les postes : « Atlassian » (outils `getVisibleJiraProjects`, `createIssueLink`…) et « Atlassian MCP » (outils primaires + `discover` / `executeRead` / `executeWrite`). Les noms d'outils diffèrent : si un appel échoue sur l'un, essayer l'autre. Tools principaux du premier :
- `getAccessibleAtlassianResources` → cloudId (`43c839be-4315-4f46-b5de-9be19b840556`).
- `getVisibleJiraProjects` → liste projets + `style`/`simplified` (⇒ type de projet), issue types.
- `searchJiraIssuesUsingJql` → recherche JQL (params : `cloudId`, `jql`, `fields`, `maxResults` 50–100, `nextPageToken`, `responseContentFormat`, `computeIssueCount`).
- `getJiraIssue`, `getTransitionsForJiraIssue`, `getJiraProjectIssueTypesMetadata`, `getJiraIssueTypeMetaWithFields`.
- Écriture (GO requis) : `createJiraIssue`, `editJiraIssue`, `transitionJiraIssue`, `addCommentToJiraIssue`, `addWorklogToJiraIssue`, `createIssueLink`.

### Gotchas MCP (vécus)
1. **Réponses volumineuses** : la réponse embarque des objets lourds (project, avatarUrls…) **même si on restreint `fields`**. ~3–4 k caractères/ticket. Au-delà de ~25–30 tickets, la réponse **dépasse la limite** et est **sauvegardée dans un fichier** au lieu d'être renvoyée.
   - Parade : **paginer petit** (`maxResults` 7–8) ou borner par plages de clés (`key >= AC-9 AND key <= AC-15`), et lancer plusieurs requêtes **en parallèle**.
   - `responseContentFormat: "markdown"` allège le corps des champs riches mais ne supprime pas les objets système.
2. **`computeIssueCount`** : le total n'est pas renvoyé par défaut ; le demander explicitement (et le réutiliser plutôt que recompter).
3. **Champs custom** : pour lire une **valeur** de champ custom, `getJiraIssue` avec `fields` incluant `customfield_10507` (ou `*all`). Le nom lisible du champ vient de `GET /field`.
4. **Type de projet d'abord** : `getVisibleJiraProjects` donne `style` — l'utiliser avant tout conseil de config (réflexe n°1 du SKILL.md).
5. **accountId** : les utilisateurs sont identifiés par `accountId` (format `712020:<uuid>`). Les noms d'affichage ne sont pas fiables comme clés : toujours résoudre par `lookupJiraAccountId` ou `listJiraIssueAssignableUsers`.

Contraintes de création et d'édition confirmées sur l'instance (champs custom, `duedate`, transitions, liens, pièces jointes, identité du compte) : voir `contraintes-api-mcp.md`.
