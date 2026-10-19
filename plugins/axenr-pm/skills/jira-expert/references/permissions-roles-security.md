# Permissions, rôles & sécurité

## Les 3 niveaux de contrôle d'accès

1. **Product access / groupes** : qui a une licence Jira et appartient à quels **groupes** (jira-admins, jira-software-users…). Admin global.
2. **Permissions projet** : qui peut faire quoi DANS un projet (voir, créer, transitionner, commenter, voir les temps…).
3. **Issue security** (company-managed uniquement) : masquer des **tickets précis** à l'intérieur d'un projet via des **niveaux de sécurité**.

## Company-managed — Permission scheme + rôles de projet

- **Rôles de projet** (Administrator, Member…, + custom) : abstraction réutilisable. On met des personnes/groupes DANS un rôle, projet par projet.
- **Permission scheme** : associe chaque **permission** (Browse Projects, Create Issues, Transition Issues, Assign Issues, Assignable User, Work On Issues, Delete Own/All Worklogs, View Development Tools…) à des **rôles / groupes / champs user**.
- Avantage : on écrit le scheme une fois, on peuple les rôles par projet. Mémoire AxENR : schemes partagés entre AR/ASG/SYS/EMERAUDE/PE.

### Recette « le client ne voit PAS les temps » (R-Étanchéité, AC-24)
Les temps passés (worklogs) apparaissent si l'utilisateur a la permission **Browse Projects** ET les worklogs sont visibles. Pour masquer au client :
- Ne PAS donner au client les permissions liées aux worklogs / onglet « Temps passé ».
- Idéalement, **ne pas logguer de temps sur les projets clients** du tout (les temps vivent côté interne). Mémoire : AR déjà étanche (Browse = rôles nominatifs internes : Fadel/Alexis/Nadir/Flavien, +Ana à confirmer).
- La visibilité des **commentaires** peut être restreinte par rôle (« restrict to role ») pour les échanges internes.

### Recette « ne pas pouvoir assigner à qqn hors projet » (AC-26)
La permission **Assignable User** définit qui peut être assigné. Un ticket ne devrait proposer que les utilisateurs ayant ce droit sur le projet. Si des personnes hors projet apparaissent : elles ont *Assignable User* via un groupe trop large dans le permission scheme. Restreindre *Assignable User* aux **rôles de projet** (et peupler les rôles projet par projet) plutôt qu'à un groupe global.

## Team-managed (AC) — accès simplifié

- *Paramètres du projet → Accès* : trois niveaux natifs — **Administrateur / Membre / Visiteur** — + possibilité de créer des **rôles custom** avec un jeu de permissions coché.
- Pas de permission scheme partagé, pas d'issue security levels. L'isolation se fait par l'appartenance au projet + le niveau d'accès.
- Cas AC-24 « créer des rôles » (Client sans heures / Consultant fonctionnel junior / technique junior / Consultant / Administrateur) : en team-managed, se fait via les **rôles custom** de l'accès projet. En company-managed, via **rôles de projet + permission scheme**. Choisir selon le type de projet cible.

## Débogage permissions

- Message clé : accès refusé / « vous n'avez pas la permission ». 
- Outil admin : **Permission helper** (Jira admin → tester « est-ce que l'utilisateur X a la permission Y sur le ticket Z »).
- API : `getJiraIssue` échoue ou champ manquant selon les droits ; vérifier le rôle de l'utilisateur dans le projet.
- Reporter : « pourquoi je ne peux pas mettre X en reporteur ? » (AC-12) → X n'a pas de licence/accès au projet, ou n'est pas *Assignable/Browse*. Donner l'accès projet à la personne.
