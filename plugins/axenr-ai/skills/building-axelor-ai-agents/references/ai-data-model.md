# Modèle de données du module Axelor AI (`com.axelor.ai.db`)

Relevé par `GET /ws/meta/fields/<modèle>` sur AOP 8.x (demo-batimat, 19/10/2026). Vérifier sur l'instance cible avec
`scripts/inspect_ai_instance.py` : le module évolue vite.

## AiAgent

| Champ | Type | Usage |
|---|---|---|
| `code` (requis), `name` (requis) | texte | Clé d'upsert : le code ne change jamais |
| `audience` (requis) | `BUSINESS` / `TECHNICAL` | `BUSINESS` pour un agent métier |
| `toolPolicy` (requis) | `OFF` / `AUTO` / `REQUIRED` | `AUTO` : le modèle choisit d'appeler ou non |
| `systemPrompt` | texte long | Rôle, règle d'or, carte des skills, gestes, forme (voir `agent-design.md`) |
| `suggestions` | texte, une par ligne | Questions proposées à l'ouverture du chat : ce sont les questions de démo |
| `model`, `utilityModel` | M2O `AiModel` | Modèle principal ; le modèle utilitaire sert au titre du chat et aux tâches annexes |
| `maxSteps` | entier | Nombre d'étapes (appels d'outils) par tour : 20 à 30 |
| `maxOutputTokens` | entier | **Vide = 1024 par étape**. Mettre 8000 |
| `temperature`, `reasoningEffort` | | Laisser vide sauf besoin mesuré |
| `tools`, `skills`, `knowledgeBases`, `subAgents` | M2M | Par id : le déploiement résout les codes |
| `allowedModels` | texte | Droits d'écriture de l'agent (voir ci-dessous) |
| `groups`, `roles`, `users` | M2M | Qui voit l'agent dans le chat |
| `isEnabled`, `isDefault`, `isTemplate`, `isInternal`, `sortOrder` | | Un seul agent `isDefault` par instance : ne pas toucher à celui en place |

### `allowedModels`

Une règle par ligne, `<modèle complet ou *> [!create] [!update] [!delete]`, la plus spécifique l'emporte.
Patron lu sur un agent Axelor existant et repris tel quel :

```
com.axelor.apps.intervention.db.Equipment !delete
com.axelor.mail.db.MailMessage !update !delete
* !create !update !delete
```

Lecture seule pour tout le reste. Un agent expert en lecture seule : `* !create !update !delete`.

## AiTool

| Champ | Usage |
|---|---|
| `code`, `name`, `type` (requis) | `type` : `SCRIPT`, `HTTP`, `ACTION`, `SYSTEM`, `CLIENT`, `MCP` |
| `description` | **Ce que lit le modèle pour décider d'appeler l'outil** : quand l'appeler, entrée, forme de la réponse, définitions |
| `inputSchema` | JSON Schema **en chaîne** |
| `script` | Pour SCRIPT : expression JavaScript (GraalJS) évaluée, variable `input` disponible |
| `requiresApproval`, `isDestructive` | Carte d'approbation ; marquage destructif |
| `actionName`, `actionModel`, `actionLabel` | Pour ACTION : appeler une action Axelor existante |
| `httpUrl`, `httpMethod`, `httpHeaders`, `httpBody`, `secrets` | Pour HTTP |
| `systemTool` | Pour SYSTEM : nom de l'outil natif |

Outils système utiles à un agent métier (présents par défaut) : `search_records`, `read_record`, `describe_model`,
`create_record` et `update_record` (approbation), `delete_record` (approbation, destructif : ne jamais le donner),
`use_skill`, `search_knowledge`, `current_user`, `calculate`. Outils client (s'exécutent dans le navigateur) :
`open_view`, `get_active_form_data`, `set_active_form_data`, `trigger_save`, `refresh_view`, `ask_to_select`,
`ask_to_input`, `ask_to_continue`, `trigger_action`.

## AiSkill et AiSkillReference

| Modèle | Champs | Usage |
|---|---|---|
| `AiSkill` | `code`, `name`, `description`, `instructions`, `isEnabled`, `sortOrder` | La `description` sert au modèle à choisir la skill (déclencheurs) ; `instructions` est chargé par `use_skill({skill})` |
| `AiSkillReference` | `skill` (M2O), `name`, `title`, `content` | Chargé par `use_skill({skill, reference: "<name>"})` : la connaissance longue |

Le catalogue des skills (code + description) est donné au modèle tant qu'aucune skill n'est chargée : le prompt
système doit contenir sa propre **carte des skills**, car le catalogue disparaît après le premier chargement.

## AiKnowledgeBase et AiKnowledgeSource (recherche sémantique)

`AiKnowledgeBase` (modèle d'embedding requis, `chunkSize`, `chunkOverlap`, `maxResults`, `minScore`, `isGlobal`) et
ses sources `AiKnowledgeSource` (`DOCUMENT` avec `metaFile`, `RECORD` avec `model` + `filter` + `template`, `TEXT`).
Statut d'indexation : `PENDING`, `INDEXING`, `INDEXED`, `FAILED`. Interrogée par l'outil `search_knowledge`.
Sur demo-batimat la seule base était restée `PENDING` (0 morceau) : vérifier l'indexation avant de compter dessus.
Pour un corpus de quelques centaines de milliers de caractères, les références de skills sont plus fiables
(chargement déterministe, pas de seuil de similarité).

## Journal et usage

- `AiUsageLog` : `agentCode`, `modelCode`, `inputTokens`, `outputTokens`, `latencyMs`, `status`, `errorMessage`.
  Une étape à **exactement 1024 jetons de sortie** signale le plafond par défaut.
- `AiChat`, `AiChatMessage` : historique, lisible par `GET /ws/ai/chat/completions/<chatId>/messages?limit=40`.
