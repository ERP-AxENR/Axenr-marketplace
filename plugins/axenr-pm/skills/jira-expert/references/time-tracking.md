# Suivi des temps, worklogs & Tempo

## Natif Jira

- **Time tracking** : chaque ticket a *Original Estimate*, *Remaining Estimate*, *Time Spent*. Le temps passé est saisi via des **worklogs** (log work : durée + date + commentaire + auteur).
- Format de saisie : `2w 3d 4h 30m` (config *Working hours/day* et *days/week* dans les réglages admin — par défaut 8h/jour, 5j/semaine ; à aligner sur la réalité sinon les conversions j/semaine sont fausses).
- JQL : `timespent > 0`, `worklogAuthor = currentUser()`, `worklogDate >= startOfMonth()`.

### Limite majeure pour la facturation / pilotage mensuel
Les **gadgets natifs** (Time Tracking, Pie Chart) agrègent le **temps total du ticket**, PAS les worklogs d'une **période** (mois en cours). Pour « combien chaque personne a loggué ce mois, par projet » → natif insuffisant. Deux options :
1. **Tempo Timesheets** (app Marketplace) : feuilles de temps par personne/période/projet, rapports, exports — la solution robuste (cf besoin AC-16 « plugin feuilles d'heures », AC-9/AC-10/AC-11 « dashboard de temps »).
2. **Export CSV** des worklogs + traitement externe (skills AxENR `jira-timelog-facturation`).

## Étanchéité (R-Étanchéité — critique)

Les temps ne doivent **jamais** être visibles côté client. Leviers :
- Permissions : ne pas accorder au client la visibilité des worklogs (voir `permissions-roles-security.md`).
- Politique : **ne pas logguer** de temps sur les projets clients ; centraliser le temps côté interne.
- Gadgets/temps : réservés aux dashboards internes, filtres partagés uniquement avec l'équipe (Fadel/Alexis/Nadir/Flavien, +Ana à confirmer).

## Facturation au temps (AxENR)

Chaîne cible **post-migration** : worklogs Jira → skill **`jira-timelog-facturation`** → XLSX « SUIVI DES TEMPS — JIRA » structuré par client puis par **Epic** (poste budgétaire), TJM par **profil de facturation** (déduit de l'activité du worklog), sous-totaux par Epic + total mensuel. (Successeur du `redmine-timelog-facturation` utilisé pendant la migration.)

Pré-requis pour que la facturation soit juste :
- Chaque ticket facturable est rattaché à son **Epic/poste budgétaire**.
- L'**activité** du worklog (ou un champ) permet de déduire le profil/TJM.
- La fenêtre = mois civil (`worklogDate DURING (startOfMonth(), endOfMonth())`).

## Tempo — à trancher avant de promettre (AC-21)
Si Tempo est installé → vues de temps mensuelles + camembert par projet faisables nativement dans Tempo. Sinon → rester sur l'export CSV + skill, et sortir « camembert temps du mois » du périmètre des dashboards natifs. **Décision Tempo = prérequis bloquant** du cockpit AC-21 : la trancher (installé OU acté CSV) avant de livrer les vues de temps.
