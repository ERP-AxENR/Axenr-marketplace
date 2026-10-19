# Architecture de la marketplace AxENR

Une seule source de verite pour toute la methode AxENR. Les skills et agents
sont ranges par **famille d'utilisateurs**, pour que chacun ne voie que ce qui
le concerne : un developpeur ne doit pas se perdre dans le marketing, un
consultant ne doit pas tomber sur l'outillage Git.

## Un depot, deux usages

La marketplace vit sur GitHub et sert a la fois :
- **claude.ai et Cowork** : Organization settings > Plugins & skills > Sync from
  GitHub ; les skills des plugins arrivent automatiquement apres chaque merge ;
- **Claude Code** : `/plugin marketplace add ERP-AxENR/Axenr-marketplace`, puis
  installation des plugins.

Seuls les skills fonctionnent des deux cotes. D'ou la regle : hors famille
technique, un plugin ne contient que des skills.

## Les quatre familles

| Famille | Pour qui | Outil principal | Plugins |
|---|---|---|---|
| **socle** | Tout le monde | claude.ai, Cowork, Claude Code | `axenr-core` |
| **technique** | Developpeurs | Claude Code | `axenr-dev`, `axelor` (partenaire) |
| **fonctionnel** | Consultants ERP et GMAO | claude.ai, Cowork | `axenr-erp`, `axenr-gmao`, `axenr-data`, `axenr-permissions` |
| **support** | Pilotage, chefs de projet, marketing | claude.ai, Cowork | `axenr-pm`, `axenr-marketing` (a venir) |
| *client* | Equipe du client concerne | Tous | `client-<nom>` (a venir) |

La famille est declaree dans `.claude-plugin/marketplace.json` (champ
`category`). Le doctor refuse un plugin sans famille valide.

## Contenu des plugins

| Plugin | Famille | Contenu |
|---|---|---|
| `axenr-core` | socle | Coherence ENR, detection du client, charte graphique (`axenr-brand`), « Note-le pour le skill » (consultant ENR en skill : a venir, fusion des 6 exemplaires) |
| `axenr-erp` | fonctionnel | `axenr-bareme-expert` : baremes et moteur Pricing |
| `axenr-gmao` | fonctionnel | Capacites reelles de la GMAO (standard, parametrage, roadmap, specifique) |
| `axenr-data` | fonctionnel | `axelor-import-export`, `axenr-template-expert`, `axelor-modeles-mail`, `axenr-bi-architect` |
| `axenr-permissions` | fonctionnel | Matrice de droits, import, audit, diagnostic |
| `axenr-dev` | technique | Ticket-solver et son consultant ENR, revue de PR, montee de version, lecons, outillage de la marketplace, integration du vendredi |
| `axelor` | technique | Plugin du partenaire Axelor, non modifie |

## Qui installe quoi

| Profil | claude.ai et Cowork (Organization settings > Plugins & skills) | Claude Code |
|---|---|---|
| Developpeur | `axenr-core` | `axenr-core`, `axenr-dev`, `axelor`, et les plugins fonctionnels utiles au ticket |
| Consultant | `axenr-core` + plugins fonctionnels | Non utilise |
| Pilotage et marketing | `axenr-core` + plugins support | Non utilise |
| Equipe d'un client | + `client-<nom>` | + `client-<nom>` dans le depot du client |

Dans Claude Code, l'activation se fait par depot (`.claude/settings.json`,
`enabledPlugins`) : `axenr-app` active les plugins AxENR, `systeko-app` active
en plus `client-systeko`.

## Ou ranger un nouveau composant

1. Le contenu est-il propre a un client ? -> `client-<nom>`.
2. Sinon, qui l'utilise ?
   - un developpeur, pour du code, du Git ou la marketplace -> `axenr-dev` ;
   - un consultant, pour parametrer ou expliquer l'ERP ou la GMAO -> plugin fonctionnel du domaine ;
   - un chef de projet ou le marketing -> plugin support ;
   - tout le monde -> `axenr-core` (rare : a justifier).
3. Skill ou agent ?
   - **skill**, toujours, hors famille technique : c'est le seul composant que
     claude.ai et Cowork chargent depuis un plugin. Claude le choisit seul, d'apres
     sa description : personne n'a d'agent ni de commande a appeler ;
   - **agent ou commande** seulement dans `axenr-dev`, pour une tache autonome de
     developpement dans Claude Code. Le doctor refuse un agent ou une commande
     ailleurs.

## Regles de forme

- Un skill = un dossier `skills/<nom>/SKILL.md`, `<nom>` en kebab-case anglais.
- Frontmatter de `SKILL.md` limite a : `name`, `description`, `license`,
  `compatibility`, `metadata`, `allowed-tools` (seules cles acceptees par la
  synchronisation claude.ai).
- Description : 1024 caracteres maximum, avec les declencheurs et un « PAS pour ».
- Les fichiers d'appui vont dans `references/`, `scripts/` ou `resources/`,
  jamais dans `agents/` ni `commands/` (ils y seraient charges comme composants).
- Aucun secret, aucune donnee personnelle de contact client.

## Process hebdomadaire

| Quand | Qui | Quoi |
|---|---|---|
| Lundi a jeudi | Tout le monde | « Note-le pour le skill » -> ticket Jira AxENR Marketplace - Notre cerveau (`skill-improvement-note`) |
| Jeudi ou vendredi | Developpeur | « Integre les notes de la semaine » -> une PR `semaine/AAAA-Sss` (`weekly-skill-integration`) |
| Vendredi | Alexis | Relecture et merge |
| Apres le merge | Automatique | Release, puis synchronisation vers claude.ai, Cowork et Claude Code |

## Feuille de route

| Plugin | Famille | Origine du contenu |
|---|---|---|
| `axenr-pm` | support | Jira (organisateur, redaction de specs, expert), annonces de version, suivi des temps et facturation, priorisation |
| `axenr-marketing` | support | Strategie marketing, CRM et leads, newsletters, LinkedIn, YouTube (lexique metier ENR, carte des douleurs), offres commerciales |
| `axenr-ai` | technique | Axelor AI, et EnergIA quand le sujet reprendra |
| `axenr-erp` (suite) | fonctionnel | Support fonctionnel AOS, modeles d'affaire, facture electronique, modules annexes |
| `axenr-gmao` (suite) | fonctionnel | Planification de tournees, interventions, contrats |
| `client-heliowatt`, `client-systeko`, `client-emeraude`, `client-planete-enr` | client | Skills et instructions propres a chaque client |

## Migration depuis la v1

Le plugin unique `axenr` (v1.x) est remplace par les plugins ci-dessus (v2.0.0).
Dans Claude Code :

```
/plugin marketplace update fbe-axenr-Axenr-marketplace
/plugin uninstall axenr@fbe-axenr-Axenr-marketplace
/plugin install axenr-core@fbe-axenr-Axenr-marketplace
/plugin install axenr-dev@fbe-axenr-Axenr-marketplace
```

Les commandes techniques changent de prefixe : `/axenr:solve-ticket` devient
`/axenr-dev:solve-ticket`. Les commandes fonctionnelles disparaissent
(`/axenr:import-help`, `/axenr:template-expert`, `/axenr:bi-architect`,
`/axenr:bareme`) : leurs agents sont devenus des skills, qui se declenchent seuls
(`axelor-import-export`, `axenr-template-expert`, `axenr-bi-architect`,
`axenr-bareme-expert`).
