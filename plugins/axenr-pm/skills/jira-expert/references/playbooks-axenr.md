# Playbooks AxENR — besoins récurrents (projet AC)

Recettes actionnables mappées sur les tickets d'Amélioration continue. Toujours : identifier le **type de projet** cible, puis appliquer. Écriture = **GO explicite**.

## PB-1 — Champ obligatoire seulement au passage « En cours » (AC-15, AC-17)
Objectif : création = échéance (+ priorité) requise ; Version cible / Parent / autres → requis au passage En cours.
1. Field Configuration : ces champs **facultatifs** (création libre).
2. Validateur « champ requis » sur **chaque** transition entrant dans un statut *En cours* (app JSU/JMWE en company-managed ; règle de transition en team-managed ; repli **automation** qui renvoie + commente).
3. Vérifier les **transitions de retour** (souvent oubliées).
Détail : `workflows-statuses.md`.

## PB-2 — Versionnage par projet (AC-3, AC-13, AC-19, AC-20, AC-23)
Attention : bascule vers `fixVersion` abandonnée au 08/08/2026, `customfield_10507` reste la référence (voir `versions-components.md`). Recette conservée pour mémoire.
1. Définir le schéma de versions **par projet** (SYS = jalons ; PE/EMERAUDE à définir — **bloquant**).
2. Créer les **fixVersion** dans *Paramètres → Versions* de chaque projet.
3. Basculer `cf_10507` → `fixVersion` (pilote AR fait, 1:1).
4. Retirer `cf_10507` des **validateurs**/écrans/boards/filtres, puis le retirer quand la bascule est complète partout.
Détail : `versions-components.md`.

## PB-3 — Cockpit dashboards + board Bugs à code couleur (AC-21)
1. Filtres testés + partagés (voir `jql.md`).
2. Dashboard 1 « Mon pilotage » ; Dashboard 2 « Management équipe » (3 personnes + orphelins).
3. Board Bugs séparé avec **card colors** rouge/orange/vert par ancienneté.
4. **Trancher Tempo** (prérequis bloquant) avant les vues de temps.
Détail : `boards-filters-dashboards.md`, `time-tracking.md`.

## PB-4 — Rôles / le client ne voit pas les heures (AC-24)
- Team-managed : rôles custom dans *Accès*. Company-managed : rôles de projet + permission scheme.
- Rôles cibles : Client (aucune visibilité temps), Consultant fonctionnel junior, Consultant technique junior, Consultant, Administrateur.
- Étanchéité temps : pas de permission worklog au client + ne pas logguer sur projets clients.
Détail : `permissions-roles-security.md`, `time-tracking.md`.

## PB-5 — Assignation restreinte aux membres du projet (AC-26)
Restreindre la permission **Assignable User** aux **rôles de projet** (pas à un groupe global). Peupler les rôles projet par projet.
Détail : `permissions-roles-security.md`.

## PB-6 — Auto-assigner le créateur + Version cible sur GMAO (AC-27)
- Automation : *Issue created* → *Assign* = `{{issue.reporter}}` (si vide), modifiable ensuite.
- Remplacer le champ « version d'amélioration » par **Version cible / fixVersion** sur l'écran de création GMAO.
- Attention : Pas de règle « Component Lead » concurrente.
Détail : `automation.md`, `versions-components.md`.

## PB-7 — Filtres / vues transverses (AC-11, AC-22, AC-25)
- 2 vues « Ready for testing » (statut Revue en cours) pour Ana et Alexis, multi-projets.
- Filtre « masquer les tickets fermés » : `statusCategory != Done`.
- Migrer les filtres « à signer par personne » de Redmine → filtres JQL partagés.
Détail : `jql.md`, `boards-filters-dashboards.md`.

## PB-8 — Reporteur indisponible (AC-12)
Une personne n'apparaît pas comme reporteur/assignable → lui donner l'**accès projet** (licence + rôle Browse/Assignable). Détail : `permissions-roles-security.md`.

---
### Rappel process
Cadrer (Architecte) → challenger le besoin (Consultant ENR) → spec testable → **GO** → exécuter (idempotent, pilote-puis-vague) → auditer avant prod. Rien d'irréversible sans GO manager.
