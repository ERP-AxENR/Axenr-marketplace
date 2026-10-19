# Contraintes API et MCP confirmées sur erp-axenr.atlassian.net

Pièges vécus en créant ou modifiant des tickets par le connecteur Atlassian. À relire avant toute écriture. Chaque règle a été constatée sur l'instance ; sur un autre projet ou après une mise à jour Atlassian, la revérifier.

## Avant toute écriture

| Règle | Détail |
|---|---|
| Vérifier l'identité du compte connecté | `atlassianUserInfo` (puis `getJiraUser` si seul l'accountId revient). Le ticket, le commentaire ou la transition est enregistré au nom de ce compte. Si ce n'est pas l'utilisateur de la conversation : ne rien écrire, le signaler. Un connecteur reconnecté côté claude.ai n'est pris en compte qu'au redémarrage de la session Claude Code. |
| cloudId | Préférer l'UUID `43c839be-4315-4f46-b5de-9be19b840556` au nom d'hôte quand un outil refuse `erp-axenr.atlassian.net`. |
| GO explicite | Aucune création, édition, transition ou commentaire sans validation de l'utilisateur. |

## Création

| Champ ou cas | Règle |
|---|---|
| `duedate` | Obligatoire à la création sur AR ; constaté aussi sur GMAO, EMERAUDE et PE. Le passer dans `additional_fields` (`{"duedate": "AAAA-MM-JJ"}`). Placeholder si inconnue : date du jour + 1 mois, à corriger dès que la vraie date est connue. La vue compacte de `getJiraIssue` peut ne pas l'afficher : relire en vue complète (`view: full` ou `responseFields: ["fields.duedate"]`) avant de conclure qu'elle est vide. |
| `customfield_10507` (Version cible) | Ne jamais l'inclure dans `fields` d'une requête MCP : erreur « No approval received ». Il se renseigne à la main dans Jira. |
| `customfield_10508` (Composant AxENR) | Valeurs acceptées : `Affaires / Projet`, `Maintenance`, `Autre`. `Achats` et `Achats / Stock` échouent sans message : laisser vide si aucune valeur ne convient. |
| `&` dans le summary | Refusé à la création. Reformuler, ou corriger ensuite par `editJiraIssue`. |
| `fixVersion` | Non utilisé (abandonné au 08/08/2026) : ne pas le renseigner ni le synchroniser avec `customfield_10507`. |
| Date de début | `customfield_10015`. |
| Priorité | Par `additional_fields` (`{"priority": {"name": "Medium"}}`) selon le connecteur. |
| Projet team-managed (AC) | Pas de logique `customfield_10507` / `10508` : la configuration est propre au projet. |

## Hiérarchie

| Cas | Règle |
|---|---|
| Story vers Sous-tâche | La conversion par `editJiraIssue` est rejetée (erreur de hiérarchie). Créer une sous-tâche neuve avec `parent` = clé du ticket parent. |
| Parent d'une sous-tâche | Le ticket parent, jamais l'Epic directement. |

## Assignation

- Toujours résoudre la personne par `lookupJiraAccountId` ou, mieux, `listJiraIssueAssignableUsers` (filtre les personnes réellement assignables sur le projet) avant d'assigner par nom.
- Homonymes et noms affichés différents du nom usuel : un utilisateur peut apparaître dans Jira sous son seul nom de famille en majuscules. Une JQL `assignee = "Prénom Nom"` renvoie alors 0 ligne sans erreur : chercher l'accountId et requêter par accountId.

## Transitions

- Lister d'abord les transitions offertes (`getTransitionsForJiraIssue` ou `listJiraIssueTransitions`) : les identifiants dépendent du workflow du projet.
- IDs relevés sur le workflow client company-managed (à revérifier) : 21 À traiter, 22 Planifié, 23 En cours, 27 Recette client, 29 À déployer, 30 Fermé, 31 Livré. SYS : 4 Planifier vers Planifié.
- Sur SYS, renseigner le parent et l'assigné **avant** toute transition, sinon elle échoue sans message.
- Pas de suppression par l'API : passer le ticket au statut Fermé (transition 30 sur le workflow client).

## Requêtes

- Champs de temps (worklogs, `timespent`) dans une requête séparée des champs de structure (parent, statut, Epic) : les mélanger alourdit la réponse et la tronque.
- Une requête par projet plutôt qu'un `OR` inter-projets quand le volume est important.
- Réponses volumineuses : paginer petit (voir `rest-api-adf-mcp.md`).

## Liens et pièces jointes (connecteur « Atlassian MCP »)

| Besoin | Opération |
|---|---|
| Lier deux tickets | `executeWrite` avec `createJiraIssueLink`, entrées `inwardIssue`, `outwardIssue` et `linkType` (ex. `Relates`). Le paramètre s'appelle `linkType`, pas `type`. |
| Télécharger une pièce jointe | `executeRead` avec `downloadJiraIssueAttachment`. |
| Déposer une pièce jointe | Pas possible par le MCP de création : dépôt manuel, ou appel REST direct hors MCP. |

Sur le connecteur « Atlassian », le lien se fait par `createIssueLink`. Si un outil d'un connecteur échoue (session expirée, compte erroné), essayer l'autre après avoir vérifié son identité.
