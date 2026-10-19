# Organisateur Jira AxENR : règles de gestion et modèles

> Instance : `erp-axenr.atlassian.net`, cloudId `43c839be-4315-4f46-b5de-9be19b840556`.
> Règles de gestion arbitrées le 08/08/2026, complétées par le mail d'organisation de fin août 2026 et la pratique du Projet « Chef de projet ». La rédaction détaillée d'une spécification fonctionnelle relève du skill `jira-spec-writer` ; les contraintes techniques de l'API, du skill `jira-expert`.

---

## 0. Règles de gestion

### 0.1 Un Epic par version, rattachement obligatoire

Sur **AR** et **GMAO**, chaque version a son propre Epic (`V2.3 - DEV`, `GMAO V2.6 - Mobile`…).

- **Aucun ticket (Bug, Story, Task) sans Epic parent.** Un ticket sans parent est hors budget, hors reporting, invisible dans le suivi de version.
- Sur AR : les correctifs vont dans la version en cours (Epic `… - DEV`), les évolutions dans le WIP (Epic `… - WIP`).
- Le choix de l'Epic n'est **jamais** automatique : il conditionne le budget, la version de livraison et la facturation. En cas de doute, demander ; ne jamais deviner.
- Un Epic **fermé** ne reçoit plus de ticket, sauf demande explicite de l'utilisateur.

### 0.2 Sous-tâches : quand découper

- **Seuil : 14 h de développement maximum par ticket.** Au-delà, découper en sous-tâches. En dessous, si le sujet mélange des compétences ou des livrables indépendants (back + mobile, plusieurs écrans), **proposer** le découpage, ne jamais trancher seul.
- Le ticket parent reste un Story ou une Task rattaché à l'Epic. Chaque sous-tâche a pour `parent` la clé du ticket parent, jamais l'Epic.
- Nommage : nom du sujet parent + numéro d'ordre (`AxFlow-1`, `AxFlow-2`…), distinct de la clé Jira.
- Une Story ne se convertit pas en Sous-tâche par l'API : créer une sous-tâche neuve (détail dans `jira-expert`).

### 0.3 Projets clients (EMERAUDE, SYS, PE, IAXE3, AC…)

- Rattachement Epic obligatoire, y compris pour un simple bug signalé par le client.
- Le préfixe de l'Epic porte la nature budgétaire :

| Préfixe Epic | Nature | Facturable |
|---|---|---|
| `[REGIE] - …` | temps passé | Oui |
| `[FORFAIT] - …` | vendu au forfait | Non (inclus) |
| `Maintenance Annuelle …` | contrat annuel | Non (inclus) |
| autre ou absent | à qualifier | Demander avant de créer |

- **Un bug client n'est pas automatiquement de la régie.** Règle de base : anomalie ou dysfonctionnement vers l'Epic « anomalie » du projet s'il existe ; question ou accompagnement vers l'Epic « Assistance ». Cette règle varie selon le client :
  1. vérifier d'abord la règle propre à ce client (fichier de contexte du Projet claude.ai du client, conversations passées) ;
  2. en cas de doute, poser la question ;
  3. une fois la règle confirmée, la faire ajouter au contexte de ce client (Projet client), et proposer une fiche `skill-improvement-note` si elle est générique.
- **Anomalie client qui révèle un bug produit : deux tickets liés.** Un ticket sur le projet client, assigné au chef de projet ; un ticket sur AR ou GMAO, assigné au développeur, lié au premier (`Relates`). En cas de doute sur la nature produit, c'est le développeur produit (Fadel) qui crée le ticket produit.
- Les Epics et règles propres à chaque client ne sont pas dans ce skill : ils sont dans le contexte du Projet client.
- Le projet **AC** (Amélioration continue) est team-managed : ne pas lui appliquer les réflexes company-managed (champs custom 10507 / 10508).

### 0.4 Type des enfants d'Epic, par projet

| Projet | Type des enfants d'Epic |
|---|---|
| AR, EMERAUDE | `Story` (EMERAUDE : id `10007`) ou `Sous-tâche` selon le niveau |
| GMAO | `Tâche` |
| SYS, PE, IAXE3, AC | Non vérifié : contrôler au premier besoin réel (`getJiraProjectIssueTypesMetadata`) |

### 0.5 À la création : les champs qui bloquent

Détail et cas limites dans `jira-expert` (`references/contraintes-api-mcp.md`). Les quatre à ne jamais oublier :

| Champ | Règle courte |
|---|---|
| `duedate` | Obligatoire (AR, GMAO, EMERAUDE, PE constatés). Placeholder : date du jour + 1 mois si inconnue |
| `customfield_10507` (Version cible) | Jamais dans une requête MCP ; renseignée à la main |
| `customfield_10508` (Composant) | `Affaires / Projet`, `Maintenance` ou `Autre`, sinon vide |
| `&` dans le résumé | Refusé : reformuler |

`fixVersion` n'est pas utilisé.

### 0.6 Assignation obligatoire

**Aucun ticket sans assigné.** S'il n'est pas donné, le demander. Ne jamais assigner par défaut à l'utilisateur qui crée le ticket.

| Type de ticket | Assigné |
|---|---|
| Ticket d'un projet client (EMERAUDE, SYS, PE, IAXE3, AC) | Le chef de projet du client |
| Ticket produit (AR, GMAO) | Le développeur produit (Fadel), sauf autre consigne |
| Bug | Le développeur qui corrige, jamais le rapporteur |
| Story / Task | La personne qui implémente (développeur ou consultant fonctionnel) |
| Epic | Le responsable du périmètre |
| Sous-tâche | Peut différer du parent si les livrables sont répartis |

Toujours résoudre l'accountId avant d'assigner par nom (homonymes, noms affichés différents).

### 0.7 Vérification rapide avant création

Une seule requête JQL légère, qui sert à la fois à trouver l'Epic et à repérer un doublon :

```
project = <PROJET> AND text ~ "<mot-clé du sujet>" ORDER BY created DESC
```

`maxResults` réduit, champs limités à `summary, parent, status`. Jamais de recherche plein texte non filtrée par projet.

### 0.8 Priorité

`Medium` par défaut à la création. Ne pas déduire une urgence du ton du message : la priorité haute se décide explicitement (par l'utilisateur, ou lors d'une revue de priorisation qui applique la grille de priorité AxENR).

### 0.9 Traçabilité de la source

Quand le ticket vient d'un signalement tracé ailleurs (mail, Teams, audit, SFD, ticket repris), la référence figure dans la description : section « Références » d'une spec, « Éléments de diagnostic » d'un bug.

### 0.10 Échéances et livraison

- Pas de ticket ouvert sans échéance réaliste ; la mettre à jour dès qu'elle glisse.
- Déploiements le 15 et le 30 du mois ; si la date tombe un week-end, la recette se boucle le vendredi précédent.
- À chaque livraison, passer le ticket au statut « Livré ».
- La Version cible est remplie à la main par le responsable des livraisons (Flavien), pas par le connecteur.
- Avant une démo, vérifier avec le responsable des livraisons l'état réellement déployé : un statut Jira ne prouve pas qu'une fonctionnalité est en ligne.

### 0.11 Visuels : ce que Jira rend réellement

| Format | Rendu dans une description Jira Cloud | Utilisable ? |
|---|---|---|
| Schéma ASCII dans un bloc de code | Oui, en monospace | Oui, partout, y compris mobile |
| Tableau | Oui | Oui |
| Panel, citation | Oui | Oui |
| Mermaid | Non rendu nativement (texte brut) | Seulement si une app Mermaid est installée |
| Capture d'écran | Oui une fois attachée | Dépôt manuel : le MCP ne joint pas de fichier |

Méthode : schémas en ASCII dans le ticket ; captures marquées à leur emplacement (`[capture : liste déroulante Projet incomplète]`) puis déposées à la main ; un schéma complexe se génère à part en image, avec un renvoi dans le texte.

### 0.12 Écriture Jira : règle d'or

- **Aucune écriture (création, édition, transition, commentaire) sans GO explicite.** Le skill prépare des brouillons.
- Plusieurs tickets : les présenter en **lots nommés et numérotés** (`Lot 1 - Epics`, `Lot 2 - Tickets`…) pour permettre une validation partielle.
- Deux temps, jamais fusionnés : analyse et extraction d'abord, action ensuite.
- Si l'utilisateur modifie un fichier ou un plan en parallèle, relire sa dernière version avant d'agir ; ses modifications priment sur le plan initial et se réanalysent ligne à ligne.
- Vérifier l'identité du compte connecté avant d'écrire : le ticket est enregistré au nom de ce compte.

### 0.13 Rédaction

- Brièveté par défaut : un ticket court, au niveau fonctionnel. Le développeur décide du technique. Seule une grosse spécification justifie un texte long.
- Format court alternatif, apprécié pour les demandes simples : « Problématique » → « Solution » → « Liste des choses à faire pour le développeur ».
- Dernière passe : purger les marqueurs d'écriture IA (méthode « humanizer », https://github.com/blader/humanizer, adaptée dans `jira-spec-writer`). Pas de tiret cadratin, pas d'emoji.

### 0.14 Principes de conception à rappeler dans les tickets

- Standard d'abord, spécifique ensuite.
- Préférer un champ de typage avec un flag d'affichage (`showIf`) aux traductions ou surcharges de vues : c'est plus simple à maintenir (leçon AR-224).
- `company` plutôt que `companySet` quand un seul rattachement suffit.
- Partner est l'entité la plus risquée à modifier en SaaS : la toucher avec prudence.

---

## 1. Ticket de type Bug

### Principe
Synthétique, rapide à reproduire, simple à comprendre. Le développeur doit pouvoir reproduire en lisant.

### Quand l'utiliser
Un dysfonctionnement par rapport à un comportement attendu (standard Axelor ou spécification livrée). Un besoin non couvert est une spécification (skill `jira-spec-writer`).

### Modèle

```markdown
## Contexte
[2 à 4 lignes : ce qu'on essaie de faire, et ce qui bloque]

## Étapes pour reproduire
1. [Action] : [capture]
2. [Action] : [capture]

## Résultat obtenu
[Ce qui se passe réellement : capture]

## Résultat attendu
[Ce qui devrait se passer]

## Impact
- [Conséquence métier concrète]

## Détails techniques
- Vue : `nom-de-la-vue`
- Objet : `NomObjet`
- Blocage suspecté : [champ, domaine, action]
```

Pour un bug simple, s'arrêter après « Résultat attendu ».

### Exemple rempli

```markdown
## Contexte
Lors de la modification d'une note de frais, la liste déroulante des projets d'une ligne de
dépense ne contient pas tous les projets disponibles.

## Étapes pour reproduire
1. Ouvrir une note de frais. : [capture]
2. Modifier ou créer une ligne de frais. : [capture]
3. Ouvrir la liste du champ Projet / Affaire. : [capture]

## Résultat obtenu
La liste est incomplète : certains projets n'apparaissent pas.

## Résultat attendu
Tous les projets auxquels l'utilisateur est autorisé sont proposés.

## Impact
- Impossible d'affecter certaines dépenses au bon projet.

## Détails techniques
- Vue : `expense-form`
- Objet : `Expense`
- Blocage : domaine du champ `project` sur `expense-line-form`
```

### Champs Jira
| Champ | Valeur |
|---|---|
| Type | `Bug` |
| Epic parent | Obligatoire (§0.1, §0.3) |
| Assigné | Le développeur qui corrige (§0.6) |
| Priorité | `Medium` par défaut (§0.8) |
| Échéance | Obligatoire (§0.5) |

---

## 2. Spécification fonctionnelle : ce que l'organisateur vérifie

La rédaction (challenge, structure, exemple, passe anti-slop) suit le skill `jira-spec-writer`. L'organisateur garantit les règles du §0 et cette checklist technique, **obligatoire dans toute spécification** : si un point ne s'applique pas, écrire « sans objet » plutôt que l'omettre.

| Vérification | Ce qu'il faut prévoir |
|---|---|
| Injection règle de droit | Nouvel objet ? Script qui l'ajoute aux rôles standards du module (ex. `Intervention User`, `Intervention Manager`, `Intervention Read`), avec le menu et la création de la permission |
| Injection configuration init | Nouvelle configuration (modèle de mail, batch, séquence, paramètre) ? La faire intégrer aux **data-init**, en décrivant précisément la configuration attendue |
| Script de migration | Le modèle change ? Script pour les clients déjà en production sur une version antérieure |

Champs Jira d'une spec : type `Story` (besoin utilisateur) ou `Task` (technique) ; Epic, assigné et échéance obligatoires ; estimation en heures, découpage au-delà de 14 h.

---

## 3. Commentaire sur un ticket existant

### Principe
Synthétique. Ne pas reprendre le contexte du ticket, il est juste au-dessus.

### Règles
- **Ne jamais réécrire la description d'origine** pour y intégrer un ajustement : la description reste la version validée, le commentaire porte l'évolution.
- Un commentaire qui remet en cause le ticket le dit **dès la première ligne**, pour que personne ne développe une version périmée.
- Si le commentaire tranche un point ouvert de la description, le dire explicitement.

### Modèle

```markdown
[Première ligne : nature du commentaire et, s'il y a lieu, ce qui est remis en cause]

Décision / Avancement / Question : [contenu direct]
- [Point 1]
- [Point 2]
```

### Exemple rempli

```markdown
Changement de direction suite à l'audit client du 30/07 : ce ticket est remis en cause.

Décision : retour au standard pour la hiérarchie du parc, on abandonne les traductions
spécifiques Installation / Équipement.
- « Installation » et « Emplacement » restent des lieux standards ; ajout d'un champ
  « Type de lieu » (Installation / Emplacement) avec un flag visible sur la fiche Lieu.
- Le multi-niveaux (Installation → Lieu(x) → Équipements) fonctionne ainsi sans surcharger le standard.
- Les développements faits sur la fiche « Installation » ne sont conservés que pour les lieux
  de type Installation.
```

---

## Annexe A : Epics actifs AR et GMAO (extraction du 08/08/2026)

Liste datée : la revérifier par JQL (`project = AR AND issuetype = Epic AND statusCategory != Done`) avant de rattacher. Les Epics des projets clients sont dans le contexte de chaque Projet client.

### AR (R&D AxENR)

| Clé | Epic |
|---|---|
| AR-504 | RD 2026 AxENR |
| AR-508 | Refonte site AxENR |
| AR-510 | Suivi Méthodologie |
| AR-511 | Assistance AxENR |
| AR-527 | V2.3 - DEV |
| AR-528 | V2.4 - WIP |
| AR-529 | Backlog - Non planifié |
| AR-539 | V2.5 - Mobile (renommé « AxFlow » selon des échanges récents : à vérifier) |
| AR-540 | V3.1 - Migration Axelor |
| AR-541 | V3.2 - Améliorations diverses |
| AR-542 | Infra & Outillage |

### GMAO

| Clé | Epic |
|---|---|
| GMAO-30 | GMAO V2.1 - Contrat & Lignes de planif |
| GMAO-31 | GMAO V2.2 - Interventions |
| GMAO-32 | GMAO V2.3 - Cartographie |
| GMAO-33 | GMAO V2.4 - Qualité |
| GMAO-53 | GMAO V2.5 - Parc & Équipements |
| GMAO-54 | GMAO V2.6 - Mobile |
| GMAO-92 | GMAO V2.7 - Facturation simplifiée |
| GMAO-112 | Correctif V2 |
| GMAO-55 | GMAO V3.1 - Demandes client & GTI-GTR |
| GMAO-56 | GMAO V3.2 - Parc avancé |
| GMAO-57 | GMAO V3.3 - Interventions & Planification avancées |
| GMAO-58 | GMAO V3.4 - Mobile avancé |
| GMAO-93 | GMAO V3.5 - Facturation avancée |
| GMAO-59 | GMAO V4.0 - Excellence opérationnelle |
