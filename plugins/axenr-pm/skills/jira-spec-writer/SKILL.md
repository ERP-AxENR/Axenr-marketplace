---
name: jira-spec-writer
description: >
  Redige une specification fonctionnelle detaillee AxENR pour Jira (ou Redmine
  pour les projets encore sous Redmine) a partir d'un besoin brut : challenge
  du besoin en 3 a 6 questions avec hypotheses par defaut, structure arbitree
  (objectif metier avec schema, configurations, process etape par etape,
  perimetre, recette, points ouverts, points techniques), puis passe
  anti-slop qui purge les marqueurs d'ecriture IA. Declencheurs : « redige la
  spec », « specification fonctionnelle », « transforme ce besoin en story »,
  « ecris la story », « cahier de recette du ticket », « ticket Redmine ».
  PAS pour : creer le ticket dans Jira, choisir l'Epic ou l'assigne, rediger
  un bug ou un commentaire (organisateur-jira), configurer Jira
  (jira-expert), noter une amelioration de la marketplace
  (skill-improvement-note).
metadata:
  owner: axenr
  family: support
---

# Jira Spec Writer (AxENR)

Transformer un besoin fonctionnel brut en spécification **précise, synthétique et prête à développer**, après un challenge qui expose les zones floues, et avant une passe qui purge les marqueurs d'écriture IA. La création du ticket, son Epic, son assigné et son échéance relèvent de `organisateur-jira`.

## Environnement d'exécution

| Où | Comportement |
|---|---|
| claude.ai et Cowork | Produit la spec en Markdown ; la création dans Jira passe par `organisateur-jira`, sur GO explicite. |
| Claude Code | Idem ; peut lire le code du projet pour nommer les objets et champs réels (jamais de nom inventé). |

## Philosophie

Un bon ticket n'est pas un ticket long : c'est un ticket qu'un développeur a envie de lire. La valeur métier est la valeur ajoutée d'AxENR : l'objectif doit être compréhensible par quelqu'un qui ne connaît pas le métier, avec un exemple concret. Le skill challenge d'abord, rédige ensuite, purge en dernier. Il refuse d'écrire sur des hypothèses silencieuses.

## Workflow en 4 phases

### Phase A : diagnostic (silencieux)

| Zone | Question implicite |
|---|---|
| Objet technique source | Quelle entité Axelor ? (`Project`, `SaleOrder`, `StockMove`…) |
| Objet cible | Quel objet est produit, modifié ou créé ? |
| Valeur ajoutée | Quel problème concret, pour qui, ce que ça coûte aujourd'hui ? |
| Conditions d'activation | Quand, pour quel rôle, à quel statut ? |
| Cas limites | Données absentes, valeurs extrêmes, états non prévus |
| Données existantes | Faut-il un script de migration ? |
| Critères de succès | Comment valide-t-on en recette ? |

### Phase B : challenge

3 à 6 questions ciblées, jamais 15. Prioriser ce qui change la structure du ticket ; regrouper par thème ; proposer une **hypothèse par défaut à valider** plutôt qu'une question ouverte. Si le besoin est déjà clair, le dire et passer à la rédaction.

Bonne question : « Pour `dateMiseEnService`, hypothèse : obligatoire au passage au statut `In Progress`, modifiable seulement par le rôle `ChargéAffaires`. Tu valides ? »

### Phase C : rédaction

Structure ci-dessous. S'il reste des trous après deux tours : proposer (a) de rédiger avec des `TODO : à confirmer par <nom>` explicites, ou (b) de clarifier d'abord.

### Phase D : passe anti-slop (obligatoire)

Appliquer `references/anti-slop-tickets.md` : brouillon, puis « qu'est-ce qui sonne encore généré ? », puis version finale. Ne livrer que la version finale. Contrôles bloquants : aucun tiret cadratin, aucun emoji, un objet garde le même nom tout le long, chaque règle a un acteur, aucun nom de champ inventé.

## Structure de la spécification (arbitrée le 08/08/2026)

~~~markdown
## Objectif métier
[Le problème concret aujourd'hui, avec un exemple. Ce que ça coûte au client.]

```
[Schéma ASCII : flux métier, avant / après, ou arborescence]
```

## Spécification fonctionnelle

### Configurations initiales
[Config App AxENR, champs, sélections, paramètres à créer, ou « aucune »]

### Process
1. [Étape : condition d'affichage / action au clic / règle] : [capture : écran attendu, emplacement]
2. [Étape] : [capture]

## Périmètre
[Inclus, et ce qui est explicitement renvoyé à une version ultérieure]

## Recette
- [Cas nominal]
- [Cas limite]
- [Cas d'exclusion ou d'erreur]

## Points ouverts
1. [Question + position par défaut proposée + « à trancher »]

## Points techniques
- Injection règle de droit : [rôles standards du module, menu, permission, ou « sans objet »]
- Injection configuration init : [éléments à mettre en data-init, ou « sans objet »]
- Script de migration : [nécessaire ? pour quelles versions, ou « sans objet »]
~~~

Un exemple complet est dans `references/exemple-spec.md`.

## Règles de qualité

| Critère | Règle |
|---|---|
| Résumé du ticket | Moins de 80 caractères, commence par un verbe d'action, sans point final |
| Longueur | 40 à 80 lignes, 120 au maximum |
| Objectif métier | Un visuel obligatoire ; compréhensible par un non-initié |
| Process | Une capture par étape ; si l'écran n'existe pas, décrire précisément l'emplacement attendu |
| Objets techniques | En `code inline`, toujours le même nom |
| Recette | Les cas significatifs, pas l'exhaustivité |
| Points techniques | Les trois lignes toujours présentes, « sans objet » plutôt qu'omises |
| Syntaxe | Markdown standard pour Jira ; pour Redmine, voir `references/format-redmine.md` |

## Schémas

| Cas | Format |
|---|---|
| Workflow linéaire de 5 étapes au plus, transition de 4 états au plus | ASCII |
| Structure de données plate | Tableau |
| Relations entre entités, séquence, machine à états complexe | Mermaid seulement si une app Mermaid est installée sur l'instance Jira ; sinon ASCII ou image déposée à la main |

## Détection du script de migration

1. Modification d'un champ existant : probable.
2. Suppression ou renommage : obligatoire.
3. Nouveau champ avec une valeur par défaut non triviale pour l'existant : oui.
4. Règle métier qui change pour des enregistrements existants : oui.
5. Nouvelle fonctionnalité sans effet rétroactif : non.

Si oui : volume estimé, stratégie (SQL ou Java `@Transactional`), retour arrière, environnement de test.

## Version

- 2.0.0 — 2026-10-19 — reprise dans la marketplace AxENR : structure arbitrée le 08/08/2026, format Redmine intégré en référence.
- Passe anti-slop adaptée de `blader/humanizer` v2.8.2 (licence MIT).
