# Project types — team-managed vs company-managed

C'est la distinction la plus structurante de Jira Cloud. Elle détermine **où** se trouve chaque réglage et **ce qui est possible**.

## Identifier le type

| Méthode | Team-managed | Company-managed |
|---------|--------------|-----------------|
| API `getVisibleJiraProjects` | `style: "next-gen"`, `simplified: true` | `style: "classic"`, `simplified: false` |
| UI | *Paramètres du projet* → bas de la sidebar : « Projet géré par l'équipe » | « Projet géré par l'entreprise » |
| Qui peut le créer | N'importe quel utilisateur autorisé | Admin Jira |

## Modèle de configuration

**Team-managed** = autonomie. Chaque projet possède SON workflow, SES types de tickets, SES champs, SES accès. Rien n'est partagé. Un admin de projet (pas forcément admin Jira) configure tout depuis *Paramètres du projet*. Idéal pour une équipe qui veut aller vite (c'est le cas d'**AC — Amélioration continue**).

**Company-managed** = gouvernance. La config passe par des **schemes** (gabarits) réutilisables entre projets :

| Scheme | Rôle |
|--------|------|
| Issue type scheme | Quels types de tickets |
| Workflow scheme | Quel workflow par type |
| Screen scheme + Issue type screen scheme | Quels écrans (create/edit/view) par type |
| Field configuration scheme | Quels champs requis/masqués par type |
| Permission scheme | Qui peut faire quoi |
| Notification scheme | Qui est notifié |
| Issue security scheme | Niveaux de sécurité (visibilité par ticket) |

Modifier un scheme partagé impacte **tous** les projets qui l'utilisent. Dans l'instance AxENR, les projets clients partagent des schemes (ex. schemes 10373/10370 partagés AR/ASG/SYS/EMERAUDE/PE) → changement = impact multi-projets, à annoncer.

## Champs custom : la différence qui pique

- **Company-managed** : un champ custom est **global** (un seul `customfield_XXXXX`) et s'active projet par projet / type par type via un **contexte**. C'est le modèle des champs AxENR (cf_10507 Version cible, etc.). Un même champ, plusieurs contextes.
- **Team-managed** : les champs sont **locaux** au projet. Deux projets team-managed « Version cible » = deux champs différents, non partagés, non requêtables ensemble par un id commun de façon fiable.

## Ce qui n'existe QUE d'un côté (repères, à revérifier)

| Capacité | Team-managed | Company-managed |
|----------|--------------|-----------------|
| Schemes réutilisables | Non | Oui |
| Champ requis conditionnel par transition | via **règles de transition** du workflow projet | via **validateur** de transition (souvent app) |
| Issue security levels (masquer un ticket précis) | Non (pas de niveaux de sécurité) | Oui |
| Rôles de projet classiques + permission scheme | Non (accès simplifié + rôles custom) | Oui |
| Partage de workflow entre projets | Non | Oui |
| Sous-tâches, hiérarchie | Oui | Oui |

Attention : Team-managed évolue vite côté Atlassian (des capacités s'ajoutent). **Ne jamais affirmer une absence sans vérifier dans l'instance.**

## Migrer un projet d'un type à l'autre

Il n'y a pas de bouton « convertir ». Il faut **créer** le projet cible du bon type puis **déplacer les tickets** (Bulk Change → Move), en re-mappant statuts, types et champs. Les champs locaux team-managed doivent être re-créés/mappés vers les champs globaux (ou l'inverse). Prévoir : mapping des statuts, des types, des champs custom, et re-tester les automations/filtres/boards qui référencent l'ancien projet.

## Conséquence pratique pour AxENR

- **AC (team-managed)** : pour « rendre un champ obligatoire au passage En cours », « ajouter un statut », « créer un rôle » → tout se fait dans *Paramètres du projet AC*. Ne pas chercher un scheme.
- **Projets clients (company-managed)** : mêmes besoins → passer par les schemes (et donc attention à l'impact partagé). Voir `workflows-statuses.md`, `fields-screens-config.md`, `permissions-roles-security.md`.
