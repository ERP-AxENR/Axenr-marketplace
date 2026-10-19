# Tester un agent par l'API du chat

## Protocole (AI SDK UI message stream, observé sur AOP 8)

Requête : `POST /ws/ai/chat/completions`, en-têtes `Content-Type: application/json`, `Accept: */*`,
`X-CSRF-Token` (cookie `CSRF-TOKEN`), corps :

```json
{"id": "<chatId, uuid nouveau ou existant>", "agent": "<code de l'agent>",
 "messages": [{"id": "<uuid>", "role": "user", "parts": [{"type": "text", "text": "<question>"}]}],
 "options": {"sessionId": "<uuid>", "context": {}}}
```

Seul le **dernier** message est envoyé : le serveur garde l'historique du chat. Réponse : flux SSE de lignes
`data: {json}`, terminé par `data: [DONE]`.

| Événement | Contenu |
|---|---|
| `start` | `messageId` du message assistant (nécessaire pour l'approbation) |
| `text-delta` | Morceau de réponse |
| `tool-input-available` | `toolCallId`, `toolName`, `input` |
| `tool-output-available` / `tool-output-error` | Sortie de l'outil / erreur (message GraalJS pour un script) |
| `tool-approval-request` | `approvalId`, `toolCallId` : carte d'approbation affichée |
| `data-notify` « Continuing response... » | Plafond de sortie atteint : voir `maxOutputTokens` |
| `data-usage`, `data-chat-title` | Jetons, titre du chat |

**Approuver** (ce que fait le bouton) : renvoyer sur le même chat le message assistant (`id` = `messageId` de
`start`) avec, par outil en attente, la part
`{"type": "tool-<nom>", "toolCallId", "state": "approval-responded", "input", "approval": {"id": "<approvalId>", "approved": true}}`.
Le flux reprend : sortie de l'outil, puis suite de la réponse.

Historique d'un chat : `GET /ws/ai/chat/completions/<chatId>/messages?limit=40`. Liste des agents visibles :
`GET /ws/ai/chat/completions/agents`.

## Grille de tests (une ligne par scénario cadré à l'étape 1)

| Contrôle | Comment |
|---|---|
| Le bon outil est appelé, avec la bonne entrée | Lignes `->` de `chat_test.py` |
| Les chiffres cités sont ceux de l'outil (pas recomptés) | Comparer avec la sortie `<-` |
| La bonne skill **et** la bonne référence sont chargées | `use_skill` avec `reference` renseignée |
| Les sources sont citées | Lecture |
| Piège : un code qui n'existe pas ou qui n'a pas le sens supposé | L'agent doit le dire, pas inventer (exemple : Fronius 567 « c'est le ventilateur ? ») |
| Calcul technique | Formule, hypothèses, `calculate` utilisé |
| Écriture | Carte d'approbation, `version` lue avant mise à jour, champs à plat, compte rendu en une phrase |
| Ambiguïté | Désignation partielle : `ambigu` puis `ask_to_select`, ou départage correct |
| Temps de réponse | Affiché par `chat_test.py` (exemple PV : 14 à 60 s selon la profondeur) |

Lot : un fichier texte, une question par ligne, `chat_test.py <url> <agent> --batch questions.txt`.

## Après les tests d'écriture

`--approve` écrit réellement. Noter chaque enregistrement créé ou modifié (ids rendus par `create_record`),
puis supprimer les créations et restaurer les champs modifiés par REST, et vérifier qu'il ne reste rien
(recherche par code ou par sujet de message). La démo doit pouvoir rejouer les mêmes gestes.
