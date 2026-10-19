# Versions (Releases) & Composants

## Versions natives Jira

Une **version** appartient à **un projet** (pas globale). Deux champs système la référencent :
- **fixVersion** (« Version corrigée / cible ») : la version où le travail est livré. C'est le champ de pilotage des releases.
- **affectedVersion** (« Version affectée ») : la version où un bug a été constaté.

États : *unreleased* → *released* (date de sortie) ; option *archived*. JQL : `fixVersion = "V4.0"`, `fixVersion IN unreleasedVersions(SYS)`, `earliestUnreleasedVersion(PROJ)`.

Où : *Paramètres du projet → Versions* (aussi vue « Releases » du projet). Créer/renommer/released/archiver s'y font.

## Le sujet AxENR — versionnage PAR PROJET (AC-3, AC-13, AC-19, AC-20, AC-23)

> **État au 08/08/2026 (fait foi)** : la bascule vers `fixVersion` (option B ci-dessous) a été abandonnée. `fixVersion` n'est pas utilisé ; `customfield_10507` (Version cible) reste la référence et n'est renseigné qu'à la main (jamais via `fields` d'une requête MCP). L'historique de l'option B est conservé pour comprendre les données du pilote AR. Revérifier dans l'instance avant toute nouvelle décision de versionnage.

Historique : un **champ custom global** « Version cible » (cf_10507) mutualisé → mêmes valeurs (V1, V2, Backlog…) pour tous les projets, impossible de versionner par client, et multi-select → doublons.

**Décision (option B)** : abandonner le champ global cf_10507 au profit des **fix versions natives, définies par projet**. Bénéfices : chaque projet a ses versions, une version = un projet, single-value natif, releases pilotables. Pilote fait sur AR (269 tickets cf_10507 → fixVersion en 1:1). cf_10507 est **conservé** tant que la bascule n'est pas complète partout.

Attention : Points de vigilance repris de la mémoire projet :
- **Bloquant** : définir le schéma de versionnage par projet AVANT de reporter la bascule (SYS déjà versionné par jalon ; PE/EMERAUDE à définir avec Alexis+Nadir). Ne pas reporter en aveugle.
- Si on abandonne cf_10507, le **retirer des validateurs de transition** qui l'exigent (sinon transition « En cours » bloquée par un champ mort) — voir `workflows-statuses.md`.
- Migrer les **filtres/boards/gadgets** qui référencent `cf[10507]` vers `fixVersion`.

### Cas AC-19 / AC-20 — « un ticket = UNE version »
- Doublons de version = créés en double dans *Paramètres → Versions*, ou champ multi-select. Solution : nettoyer la liste des versions du projet + utiliser **fixVersion** (nativement multi mais on cadre l'usage à une seule) ou verrouiller via automation si besoin d'un vrai single.
- « Impossible de sélectionner les versions en vue liste » : la colonne éditable en vue liste dépend du type de champ et du type de projet ; vérifier que **fixVersion** est bien la colonne (pas le vieux custom), et que le champ est sur l'écran/​la config.

## Composants

Un **composant** = sous-partie d'un projet (module, équipe). Propre au projet. Peut avoir un **Component Lead** et une règle d'**assignation par défaut** (par lead / inchangé). 

Attention : Piège vécu (mémoire) : une automation « auto-assign Component Lead » **écrase l'assignee** choisi → à désactiver si on veut respecter l'assignation manuelle. Vérifier ce comportement quand un ticket « se réassigne tout seul ».

Référentiel AxENR : ensemble de composants (ex. Achat, Stock…) audités par projet migré (présence, leads, doublons, tickets sans composant). JQL : `component = "Achat"`, `component IS EMPTY`.

## Composant vs Version vs Epic — ne pas confondre
- **Composant** = *où / quelle brique* (structure fonctionnelle stable).
- **Version (fixVersion)** = *quand / quel lot livré* (temporel).
- **Epic / Processus** = *regroupement de tickets* (poste budgétaire chez AxENR). Un « Module » Redmine a souvent été porté en **Epic** côté Jira, pas en composant. Ne pas re-créer un Epic qui existe déjà (anti-hallucination).
