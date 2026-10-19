---
name: building-axelor-ai-agents
description: >-
  Concevoir, creer par API, tester et livrer des agents du module Axelor AI (AOP 8.x) :
  agent specialise metier avec outils serveur en lecture, base de connaissance en skills
  sourcees, ecritures bornees par carte d'approbation, deploiement idempotent depuis un
  fichier de specification et tests automatises par l'API du chat. Declencheurs :
  « cree un agent IA Axelor », « agent Axelor AI », « AiAgent », « skill de l'agent »,
  « outil script de l'agent », « base de connaissance de l'agent », « tester l'agent »,
  « deployer les agents sur une autre instance », « agent technicien / expert ».
  PAS pour : les agents Claude Code de la marketplace (axenr-dev), un connecteur vers un
  outil tiers (building-axelor-integrations), les donnees de demo que l'agent lira
  (demo-data-generator), les droits d'acces (axelor-droits-expert).
metadata:
  owner: axenr
  family: technique
  tested-on: "AOP 8.x demo-batimat, 19/10/2026 (3 agents PV, 11 scenarios)"
---

# Créer un agent Axelor AI par API

Un agent Axelor AI utile répond juste, cite ses sources et n'écrit que ce qu'on l'autorise à écrire. Il repose sur
quatre briques, toutes des enregistrements du module `com.axelor.ai.db` créés par API :

| Brique | Modèle | Rôle | Règle |
|---|---|---|---|
| Outils serveur | `AiTool` type SCRIPT | Lire et **calculer** les données métier (totaux, jours restants, statuts) | Lecture seule (GraalJS, JPA interdit) |
| Base de connaissance | `AiSkill` + `AiSkillReference` | Savoir métier sourcé, chargé à la demande par `use_skill` | Sources citées, « (à vérifier) » sinon |
| Agent | `AiAgent` | Prompt système, carte des skills, outils, modèle, plafonds, droits d'écriture | `allowedModels` restrictif, `maxOutputTokens` relevé |
| Écritures | outils système `create_record` / `update_record` | Gestes métier avec **carte d'approbation** | Jamais de suppression |

Exemple complet, déployé et testé : `resources/examples/pv-maintenance/` (technicien de maintenance PV,
expert onduleurs, expert modules : 4 outils, 6 skills, 11 références, 130 000 caractères de connaissance).

## Prérequis

- Instance **AOP 8.x avec le module AI** (menu IA, `GET /ws/ai/chat/completions/agents` répond). AOP 7.4 n'a pas ce module.
- Instance **jetable ou de démo** pour construire et tester. Recette client : écriture sur feu vert explicite écrit.
  Production : jamais sans GO d'Alexis.
- Session ouverte **par l'utilisateur dans son terminal** (le mot de passe ne passe jamais par la conversation) :
  `! python3 -I <skill>/scripts/axelor_session.py login <url> <login>` puis `axelor_session.py check <url>`.

## Méthode en 8 étapes

1. **Cadrer** avec l'utilisateur, en une seule question groupée : qui parle à l'agent (technicien, chargé d'affaires,
   direction), les 5 à 10 questions qu'il doit réussir, les données qu'il lit, les gestes qu'il peut écrire, la langue.
   Une question = un scénario de test à l'étape 7.
2. **Inspecter l'instance** : `scripts/inspect_ai_instance.py <url>` (modèles LLM réellement utilisés, outils système,
   agents existants). Exporter un agent existant bien fait comme patron : `--agent <code> --out <dossier>`.
   Choisir un modèle **qui a des appels SUCCESS** dans le journal d'usage.
3. **Vérifier les données** que l'agent lira : champs, longueurs (texte standard souvent 255 caractères), champs
   personnalisés (`attrs`), journal (`MailMessage`). Si les données de démo sont pauvres, les enrichir d'abord
   (`demo-data-generator`). Les recouper ensuite avec la base de connaissance : un code d'alarme faux dans la démo
   ridiculise l'agent devant le client.
4. **Écrire les outils SCRIPT** de lecture (`references/script-tools.md`) : un outil par grande question
   (synthèse, fiche détaillée, échéances, anomalies), recherche tolérante, réponses `ambigu` / `introuvable`,
   `date_du_jour`, totaux et regroupements **déjà calculés**. Le modèle ne recompte jamais lui-même.
5. **Construire la base de connaissance** (`references/knowledge-base.md`) : une skill par domaine, des références
   de 10 à 15 000 caractères, sourcées (manuels, normes, forums), avec une skill « méthode » qui contient les **pièges
   de raisonnement** observés en test.
6. **Écrire l'agent** (`references/agent-design.md`) : prompt avec la règle d'or (faits du parc = outils, faits
   techniques = skills, sources citées), carte des skills, gestes d'écriture, forme des réponses ; `allowedModels`,
   `maxOutputTokens: 8000`, groupes, suggestions. Tout va dans un `spec.json` (modèle : `resources/spec-template.json`).
7. **Déployer et tester** : `scripts/deploy_ai_spec.py <url> spec.json --dry-run`, puis sans `--dry-run`
   (idempotent, par code, ne supprime rien). Tester chaque scénario par `scripts/chat_test.py`
   (`references/testing.md`) : lire les appels d'outils, pas seulement la réponse. Corriger la **cause**
   (outil qui ne calcule pas, skill qui manque d'un piège, plafond trop bas), redéployer, retester.
8. **Nettoyer et livrer** : supprimer ce que les tests d'écriture ont créé, remettre les fiches dans leur état,
   versionner la spec (exemple dans cette skill ou plugin `client-<nom>`), lister les questions de démo validées.

## Pièges qui coûtent une heure

Détail et symptômes : `references/pitfalls.md`.
- `maxOutputTokens` vide = **1024 jetons par étape** : réponse longue coupée, « Continuing response... », réponse vide.
- Script : `com.axelor.db.JPA` interdit (« Access to host class ... is not allowed ») ; `com.axelor.db.Query` autorisé.
- `create_record` avec un objet `attrs` : « argument type mismatch ». Les champs personnalisés se passent **à plat**.
- En REST brut, `attrs` est une **chaîne** JSON, pas un objet.
- AOP 8 : connexion par formulaire ; le login JSON d'AOP 7.4 renvoie 401.
- Un même nom de référence chargé dans `skill` au lieu de `reference` : le modèle charge la skill sans le contenu.

## Fichiers

| Fichier | Contenu |
|---|---|
| `references/ai-data-model.md` | Modèles `com.axelor.ai.db`, champs utiles, valeurs, outils système |
| `references/agent-design.md` | Prompt système, `allowedModels`, skills, suggestions, choix du modèle |
| `references/script-tools.md` | Bac à sable GraalJS, squelette d'outil, recherche tolérante, contrat de sortie |
| `references/knowledge-base.md` | Construire et sourcer la connaissance, recherche web, recoupement avec les données |
| `references/testing.md` | Protocole de l'API du chat, approbation, grille de tests, nettoyage |
| `references/pitfalls.md` | Symptômes, causes et correctifs constatés |
| `scripts/axelor_session.py` | Session (formulaire puis JSON), jarre de cookies partagée, appels REST et SSE |
| `scripts/inspect_ai_instance.py` | Inventaire du module AI et export d'un agent patron |
| `scripts/deploy_ai_spec.py` | Déploiement idempotent outils, skills, références, agents |
| `scripts/chat_test.py` | Question unique ou lot, approbation automatique optionnelle |
| `resources/spec-template.json` | Squelette de spécification commenté |
| `resources/examples/pv-maintenance/` | Exemple complet et rejouable |
