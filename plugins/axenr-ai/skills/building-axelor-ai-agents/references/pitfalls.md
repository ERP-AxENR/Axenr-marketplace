# Pièges constatés (AOP 8.x, demo-batimat, 19/10/2026)

| Symptôme | Cause | Correctif |
|---|---|---|
| Réponse vide après des appels d'outils, « Continuing response... » répété | `maxOutputTokens` vide : 1024 jetons par étape ; `AiUsageLog.outputTokens` = 1024 | `maxOutputTokens: 8000` sur l'agent |
| `TypeError: Access to host class com.axelor.db.JPA is not allowed` | Bac à sable GraalJS : pas d'écriture depuis un script | Écrire par `create_record` / `update_record` (approbation) |
| `Entrée d'outil invalide : argument type mismatch` sur `create_record` | Objet `attrs` envoyé pour des champs personnalisés | Champs personnalisés à plat : `{"name": ..., "pvFabricant": "Huawei"}` |
| `argument type mismatch` en REST brut (`PUT /ws/rest/...`) | `attrs` envoyé en objet | `attrs` en **chaîne** JSON (`json.dumps`) |
| `value too long for type character varying(255)` | Champ texte standard limité (ex. `Equipment.comments`) | Texte long dans un champ personnalisé de type `text` ou dans le journal (`MailMessage.body`) |
| Login API refusé (401) alors que le navigateur fonctionne | AOP 8 : login JSON refusé ; formulaire attendu | `axelor_session.py` essaie formulaire puis JSON ; `error=` dans `Location` = mauvais identifiants |
| Le modèle charge une skill mais répond sans son contenu | Nom de référence passé dans `skill` | Prompt : « le nom de la référence va dans `reference`, jamais dans `skill` » |
| Chiffre faux dans une synthèse (9 au lieu de 10, « toute la centrale ») | Le modèle recompte une liste | L'outil rend totaux et regroupements ; règle d'or « tu cites, tu ne recalcules pas » |
| « onduleur 2 » rend 3 candidats | Le mot « 2 » se trouve dans « SUN2000 » | Départage par mots entiers dans la recherche tolérante |
| Erreur technique crédible dans la réponse (mesure sans lumière, 1/3 de string au lieu de 1/3 de module) | Raisonnement, pas la base | Section « Pièges de raisonnement » dans la skill méthode, chargée avant toute réponse technique |
| L'agent contredit la fiche de démo | Données de démo fausses (codes inventés) | Recouper données et base avant la démo (`knowledge-base.md` étape 3) |
| `indicatorSelect` refusé ou ignoré | Champ calculé en lecture seule (Equipment) | Ne pas l'écrire ; il se recalcule (inService, contrat) |
| Agent absent du chat pour un utilisateur | `groups` vide ou sans le groupe de l'utilisateur | Renseigner les groupes ; vérifier `GET /ws/ai/chat/completions/agents` |
| Base de connaissance sémantique muette | Source restée `PENDING` (0 morceau) | Vérifier `status` / `chunkCount` ; sinon passer par des références de skills |
| Commande refusée par le garde-fou de Claude Code en ajoutant des outils d'écriture | Ajout d'outils d'écriture génériques couplé à une suppression dans la même commande | Séparer les étapes, borner par `allowedModels`, expliquer le besoin |
