# Boards, filtres, dashboards & card colors

## Filtres (la fondation)

Un **filtre** = une requête JQL enregistrée + un partage. Boards et gadgets de dashboard s'appuient sur des filtres.
- Créer : *Filtres → Recherche avancée* (JQL) → *Enregistrer sous*.
- **Partage** : privé / projet / groupe / organisation. Attention : Un board ou gadget ne fonctionnera pour autrui que si le **filtre sous-jacent est partagé** avec lui. Erreur classique : « le board est vide pour Fadel » = filtre non partagé, pas un bug de droits.
- Mémoire : filtres nommés par projet (11041 PE, 11042 EMERAUDE, 11043 SYS…), filtre cross-projet 10972 + board 740.

## Boards

- **Kanban** (flux continu) vs **Scrum** (sprints). Les projets AxENR migrés de Redmine → Kanban en général.
- Le board a un **filtre** (périmètre) + un **mapping colonnes ↔ statuts**. Un statut non mappé → tickets invisibles sur le board.
- **Company-managed** : board créé depuis un filtre, colonnes = statuts, indépendant du projet (peut être cross-projets). **Team-managed** : un board par projet, lié au tableau.
- Colonnes en 12 statuts : possible mais lourd ; regrouper plusieurs statuts par colonne est souvent préférable.
- **Priorité manuelle** : l'ordre vertical des cartes (drag & drop) = rang, non piloté par JQL et **non automatisable** proprement. Le `ORDER BY` du filtre ne fixe pas le rang du board.

## Card colors (couleur des cartes) — recette bugs (AC-21)

Sur un board, *Paramètres du board → Card colors → par requête (JQL)*. **L'ordre compte** : Jira applique la **première règle qui matche**.

```
1. Rouge   : created <= -14d
2. Orange  : created <= -7d
3. Vert    : created > -7d
```
Filtre du board Bugs : `type = Bug AND statusCategory != Done AND project NOT IN (IAXE3) ORDER BY created ASC`. Objectif : un bug qui traîne vire orange puis rouge sans intervention. Card colors = **feature de board**, impossible dans un gadget de dashboard (d'où le board séparé).

## Dashboards & gadgets

Un **dashboard** = grille de **gadgets**, partageable, chacun branché sur un filtre.

Gadgets utiles :
- **Filter Results** : liste de tickets d'un filtre, colonnes au choix (le cheval de bataille).
- **Two Dimensional Filter Statistics** : tableau croisé (ex. statut × assigné).
- **Pie Chart / Created vs Resolved / Average Age** : synthèses.
- **Assigned to Me**, **Activity Stream**.

### Cockpit AxENR (spec AC-21)
- **Dashboard 1 « Mon pilotage »** : gadget Filter Results `assignee = currentUser() AND statusCategory != Done ORDER BY duedate ASC` (colonnes Projet, Type, Statut, fixVersion, Parent, Échéance).
- **Dashboard 2 « Management équipe »** : 3 gadgets Filter Results (un par personne) + gadget « tâches orphelines » `(duedate IS EMPTY OR assignee IS EMPTY) AND statusCategory != Done`.
- **Temps** : Attention : prérequis bloquant — le gadget camembert Jira somme le **temps total** des tickets, pas les **worklogs du mois**. Vue temps mensuelle fiable = **Tempo Timesheets** (ou export CSV). Trancher Tempo AVANT de promettre les vues de temps (voir `time-tracking.md`).

## Ordre de construction recommandé
1. Écrire et **tester le JQL** en recherche avancée.
2. Enregistrer comme **filtre** + le **partager** correctement.
3. Brancher board/gadget sur le filtre.
4. Vérifier le rendu avec un compte non-admin (droits réels).
