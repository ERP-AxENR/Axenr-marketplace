---
name: organisateur-jira
description: >
  Organise et cree les tickets Jira AxENR (AR, GMAO, EMERAUDE, SYS, PE, IAXE3,
  AC) en appliquant les regles de gestion : Epic parent obligatoire jamais
  devine, prefixes [REGIE] / [FORFAIT] / Maintenance Annuelle, anomalie client
  vs bug produit (deux tickets lies), assignation obligatoire, decoupage au-dela
  de 14 h, anti-doublon par JQL, priorite Medium, echeance, ecriture en lots
  sur GO explicite. Redige les bugs et les commentaires. Declencheurs : « cree
  un ticket », « redige un bug », « ajoute un commentaire sur AR-xx »,
  « organise ce besoin en tickets », « sur quel Epic », « a qui l'assigner »,
  « decoupe en sous-taches ». A utiliser AVANT toute creation Jira, meme
  simple. PAS pour : rediger une specification fonctionnelle detaillee
  (jira-spec-writer), configurer Jira ou deboguer une erreur d'API
  (jira-expert), prioriser la charge d'une personne ou facturer des temps
  (skills de pilotage), noter une amelioration de la marketplace
  (skill-improvement-note, projet AMNC).
metadata:
  owner: axenr
  family: support
---

# Organisateur Jira (AxENR)

Transformer un besoin brut (bug, besoin, avancement, décision) en ticket ou commentaire Jira **conforme aux règles de gestion AxENR**, sur `erp-axenr.atlassian.net` (cloudId `43c839be-4315-4f46-b5de-9be19b840556`).

Le détail des règles (§0), les modèles Bug et Commentaire, la checklist des spécifications et la liste datée des Epics AR / GMAO sont dans `references/regles-et-modeles.md` : le lire avant de générer un ticket.

## Environnement d'exécution

| Où | Comportement |
|---|---|
| claude.ai et Cowork | Connecteur Atlassian de l'utilisateur. Lecture libre ; création ou modification sur GO explicite, après vérification du compte connecté. Sans connecteur : livrer le ticket en Markdown, prêt à coller. |
| Claude Code | Mêmes règles. Les règles propres à un client se lisent dans le contexte du client (Projet claude.ai, fichiers fournis), jamais dans ce skill. |

## Règles non négociables

1. **Epic parent obligatoire**, jamais deviné : vérifié par JQL ou demandé. Sur AR, correctifs dans la version en cours (DEV), évolutions dans le WIP. Un Epic fermé ne reçoit plus de ticket.
2. **Nature budgétaire** sur les projets clients : `[REGIE]` facturable, `[FORFAIT]` et `Maintenance Annuelle` inclus, autre préfixe à qualifier avant de créer. Un bug client n'est pas automatiquement de la régie.
3. **Anomalie client qui révèle un bug produit** : deux tickets liés, l'un sur le projet client (chef de projet), l'autre sur AR ou GMAO (développeur).
4. **Assignation obligatoire** : tickets clients au chef de projet, tickets produit au développeur ; un bug au développeur qui corrige, jamais au rapporteur. Résoudre l'accountId avant d'assigner.
5. **14 h maximum** par ticket : au-delà, sous-tâches `<Sujet>-1`, `<Sujet>-2` (parent = ticket, pas l'Epic). En dessous, proposer le découpage si c'est complexe.
6. **Une seule JQL légère** avant création, qui trouve l'Epic et détecte le doublon.
7. **Priorité `Medium`** par défaut ; **échéance réaliste** obligatoire ; source du signalement tracée dans la description.
8. **Écriture sur GO explicite**, en lots nommés et numérotés quand il y a plusieurs tickets. Analyse d'abord, action ensuite.

## Workflow

1. **Identifier le type** :
   - Bug : dysfonctionnement par rapport à l'attendu → modèle §1 de la référence.
   - Spécification fonctionnelle : besoin nouveau ou évolution → rédaction par `jira-spec-writer` ; l'organisateur contrôle les règles et la **checklist technique** (§2 : injection de droits, data-init, script de migration, « sans objet » plutôt qu'omis).
   - Commentaire : avancement, décision, question → modèle §3. Ne jamais réécrire la description d'origine ; une remise en cause se signale dès la première ligne.
2. **Lancer la JQL** de vérification (Epic + doublon).
3. **Appliquer les règles** : Epic, assigné, découpage, priorité, échéance, champs bloquants (§0.5).
4. **Lister les points ouverts** avec une position par défaut, plutôt que de trancher en silence.
5. **Présenter le brouillon** : résumé, description, Epic, assigné, priorité, échéance. Attendre le GO.
6. **Créer**, puis relire le ticket créé (y compris l'échéance, en vue complète) et donner le lien.

## Rédaction

- Court et fonctionnel par défaut ; le développeur décide du technique.
- Schémas en ASCII, captures marquées à leur emplacement et déposées à la main (le connecteur ne joint pas de fichier).
- Dernière passe anti-slop : pas de tiret cadratin, pas d'emoji, pas de phrase qui sonne générée (méthode détaillée dans `jira-spec-writer`).
