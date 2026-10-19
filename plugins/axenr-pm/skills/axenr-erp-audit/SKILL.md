---
name: axenr-erp-audit
description: >
  Méthode d'audit client ERP / GMAO AxENR en 5 phases : préparation, séance d'audit avec le
  client, SFD, plan Jira, exécution par le connecteur Atlassian. Produit une grille Excel
  dédoublonnée avec provenance et qualification de chaque besoin (Standard, Standard-RoadMap,
  Paramétrage, Spécifique, Indisponible, À qualifier), une SFD, puis un plan Jira validé avant
  toute écriture. Déclencheurs : « audit client », « audit ERP », « audit GMAO », « préparer
  l'audit », « grille d'audit », « compte rendu d'audit », « qualifier les besoins », « plan
  Jira de l'audit », « transformer l'audit en tickets ». PAS pour : vérifier si un champ ou une
  fonction existe dans le code ou la base d'une app Axelor (axelor-audit-ecart), qualifier une
  seule capacité GMAO (gmao-capabilities), rédiger un ticket isolé (organisateur-jira).
metadata:
  owner: axenr
  family: support
---

# Audit client ERP / GMAO AxENR

## Environnement d'exécution

| Où | Comportement |
|---|---|
| claude.ai et Cowork | Méthode complète. Lecture libre (fichiers fournis, Drive, Jira). Toute écriture Jira passe par un plan validé et un GO explicite. |
| Claude Code | Idem ; peut aussi croiser le dépôt et la base par `axelor-audit-ecart`. Livrables écrits dans `~/Downloads`. |

## Principes

- **Analyse d'abord, action ensuite**, jamais fusionnées : aucune écriture Jira (création, édition, transition, commentaire) sans plan validé et GO explicite.
- **Toujours relire la dernière version** d'un fichier que l'utilisateur a pu modifier en parallèle (grille, SFD, plan) avant d'agir.
- **Les modifications de l'utilisateur priment** sur le plan initial : les réanalyser ligne à ligne avant toute exécution.
- **Jamais « absent du produit »** sans avoir vérifié Jira (ticket ou roadmap existant) ET le low-code (champ ou paramétrage Studio en base) : voir `axelor-audit-ecart`.
- **Vérifier un compte rendu produit par une IA tierce** (outil de prise de notes, transcription) : il peut inventer ou déformer un terme métier. Confronter chaque point douteux à l'utilisateur.
- Fichiers Drive « en ligne seulement » : passer par le connecteur Google Drive, pas par le disque local.

## Phase 1 : préparation

1. Rassembler la matière : cahier des charges, comptes rendus, échanges, exports, captures de l'outil actuel.
2. Construire la **grille d'audit Excel** : une ligne par besoin, **dédoublonnée**, avec la **provenance** de chaque ligne (document, page, intervenant, date).
3. Pré-qualifier chaque besoin (voir les qualifications) et préparer les questions de séance pour les lignes « À qualifier ».
4. Pour la cohérence métier ENR (bon moment du cycle, généricité multi-ENR) : `enr-coherence-checker`. Pour une capacité GMAO : `gmao-capabilities`.

### Qualifications

| Qualification | Sens |
|---|---|
| Standard | Couvert par le produit tel quel |
| Standard-RoadMap | Prévu dans la roadmap produit (ticket ou Epic existant à citer) |
| Paramétrage | Couvert par configuration ou low-code, sans développement |
| Spécifique | Développement propre au client |
| Indisponible | Non couvert et non prévu |
| À qualifier | Information manquante : question à poser en séance |

## Phase 2 : séance d'audit

- Dérouler la grille avec le client, trancher les « À qualifier », noter les règles métier actées et les décisions.
- Mettre à jour la grille en séance ou juste après, en gardant la provenance (« acté en séance du JJ/MM »).
- Les règles métier actées sont des faits du client : elles vont dans le Projet du client, pas dans ce skill.

## Phase 3 : SFD

- Rédiger la SFD dans un **nouveau fichier** (ne pas écraser la grille ni un document client).
- Une section par périmètre, avec objectif métier, process, règles de gestion, points ouverts et position par défaut.
- **Chiffrage seulement sur les lignes Spécifique (DEV) et seulement sur demande** de l'utilisateur.

## Phase 4 : plan Jira

- Produire le **plan Jira en Excel avant toute écriture** : Epics, tickets, commentaires sur tickets existants, re-parentages, avec pour chaque ligne le projet, le type, l'Epic, l'assigné proposé, l'échéance et la source dans la grille.
- Découpage des Epics à partir de la V3 : **par périmètre** fonctionnel.
- **Web avant mobile** : le développement web précède le mobile dans l'ordonnancement.
- Règles de rattachement, d'assignation, de découpage et de rédaction : `organisateur-jira` (et `jira-spec-writer` pour les spécifications détaillées).
- Faire valider le plan par l'utilisateur ; intégrer ses modifications ligne à ligne.

## Phase 5 : exécution par le connecteur Atlassian

- Après GO explicite seulement, et par **lots nommés et numérotés** pour permettre une validation partielle.
- Ordre d'exécution : **Epics, puis tickets, puis commentaires, puis re-parentages.**
- Après chaque lot : relire ce qui a été créé (clés, Epic, assigné, échéance) et rendre la liste des liens.
- Vérifier l'identité du compte connecté avant la première écriture : les tickets doivent porter le nom de l'utilisateur.

## Livrables

| Phase | Livrable |
|---|---|
| 1-2 | Grille d'audit Excel dédoublonnée, provenance et qualification par ligne |
| 3 | SFD (nouveau fichier) ; chiffrage DEV sur demande |
| 4 | Plan Jira Excel validé |
| 5 | Liste des tickets créés, avec liens |
