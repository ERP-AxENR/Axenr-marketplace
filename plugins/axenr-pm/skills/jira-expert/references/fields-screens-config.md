# Champs, Field Configuration, contextes & écrans

## Types de champs

Système (summary, assignee, priority, duedate, fixVersion, components…) vs **custom** (créés). Types custom courants : texte court/long, liste déroulante (single/multi), cases, cascade, date, nombre, user picker, labels, URL, version picker.

## Company-managed — la chaîne complète

Pour qu'un champ apparaisse et se comporte bien sur un projet, 4 briques doivent s'aligner :

1. **Le champ existe** (global). Un `customfield_XXXXX` unique.
2. **Contexte** : le champ est activé pour ce **projet** et ces **types de tickets**, avec ses options (pour une liste). Un champ peut avoir plusieurs contextes (options différentes selon le projet). Attention : Si un champ « n'apparaît pas » sur un projet → 9 fois sur 10 c'est un **contexte manquant**, pas un bug.
3. **Écran** (Screen) : le champ est ajouté à l'écran *Create* / *Edit* / *View* utilisé par ce type (via screen scheme + issue type screen scheme). Absent de l'écran = invisible même si le contexte existe.
4. **Field Configuration** : le champ y est *visible* (pas *hidden*) et *obligatoire* ou *facultatif*.

Résumé du diagnostic « je ne vois pas mon champ » : **Contexte → Écran → Field Configuration (visible)**.

### Rendre un champ obligatoire (company-managed)
- Dans la **Field Configuration** du projet/type : passer le champ en *Required*. Attention : Requis = requis à la **création** ET partout où l'écran l'exige.
- Pour « requis seulement à une transition » → **validateur de transition**, PAS la Field Configuration (voir `workflows-statuses.md`).
- La **Field Configuration** peut être **dédiée par projet** (via field configuration scheme). Mémoire AxENR : Field Config dédiée ×7 (une par projet), ce qui permet des exigences différentes par client sans impacter les autres.

## Team-managed (AC)
- *Paramètres du projet → Champs* : on ajoute/masque des champs **par type de ticket**, on coche *obligatoire* directement. Les champs sont **locaux** au projet.
- Écrans : pas de screen scheme ; on gère l'ordre et la présence des champs par type dans la même UI.
- Pour « requis à une transition » → règle de transition du workflow projet (ou automation en repli).

## Doublons de champs — piège vécu

Créer un champ « Version cible » deux fois donne deux `customfield` différents → confusion, requêtes JQL qui pointent le mauvais, données éparpillées. Mémoire AxENR : 9 doublons déjà purgés, **1 seul exemplaire par champ** conservé (Version cible cf_10507, Composant cf_10508, Loom 10509, PR 10511, Ticket AOS 10512, Version AOS 10513, SQL 10500, Drive 10456, Lien Redmine 10510). Avant de créer un champ → **chercher s'il existe déjà** (Paramètres Jira → Champs personnalisés, filtrer par nom).

## Écrans (Screens) — company-managed

- **Screen** : liste ordonnée de champs.
- **Screen scheme** : associe des écrans aux opérations Create/Edit/View.
- **Issue type screen scheme** : associe un screen scheme à chaque type de ticket.
- **Écran de transition** : écran affiché pendant une transition (ex. demander « Résolution » + « commentaire » au passage Terminé).

## Bonnes pratiques
- Nommer les champs sans ambiguïté (éviter « Version » seul : préciser « Version cible »).
- Grouper les champs techniques (PR, SQL, Loom, Ticket/Version AOS) dans un bloc dédié de la sidebar (limite Jira : pas de « groupe nommé » custom en company-managed → utiliser l'ordre + « Plus de champs »).
- Multi-select vs single-select : un « une seule version par ticket » impose un champ **single** (cf AC-19 : le multi-select a créé des doublons de version — voir `versions-components.md`).
