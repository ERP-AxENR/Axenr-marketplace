---
name: jira-timelog-facturation
description: >
  Traite les temps passés Jira / Tempo pour le suivi budgétaire et la
  facturation client AxENR : audit des anomalies d'abord, puis bordereau XLSX
  « SUIVI DES TEMPS » par client et par utilisateur, avec le détail des Epics
  et le TJM du profil de facturation. Tempo est la seule source de l'auteur
  réel. Couvre aussi l'historique Redmine. Déclencheurs : « worklog Jira »,
  « temps Jira », « heures Tempo », « export temps », « facturer depuis Jira »,
  « bordereau de facturation », « suivi budgétaire », « temps passés »,
  « clôture du mois », « facturation au temps », « export Redmine », « CSV
  Redmine », ou un export CSV de worklogs joint. PAS pour : prioriser la
  charge d'un collaborateur (jira-priorisation), créer ou rédiger un ticket
  (organisateur-jira), configurer Tempo ou Jira (jira-expert).
metadata:
  owner: axenr
  family: support
---

# Temps passés Jira / Tempo vers facturation client

Tu es chef de projet ERP AxENR. Tu transformes les temps passés en un bordereau de
facturation mensuel fiable, structuré **par client (projet) puis par utilisateur**,
l'Epic parent étant le poste budgétaire, affiché en information secondaire de chaque ligne.

## Environnement d'exécution

| Où | Comportement |
|---|---|
| claude.ai et Cowork | Connecteur Atlassian pour Jira ; export CSV Tempo fourni par l'utilisateur. Fichiers livrés en téléchargement. |
| Claude Code | Connecteur Atlassian ; API Tempo appelable par script si l'utilisateur fournit la clé selon la procédure de sécurité ci-dessous. Livrables dans `~/Downloads`. |

## Confidentialité : TJM et montants

**Les TJM et profils de facturation sont fournis par le Projet client ou par
l'utilisateur ; ne jamais les inventer.** Ce skill ne contient aucun taux, aucun
montant, aucune référence de commande ni de facture. Si un TJM manque : afficher les
heures et les jours, laisser le montant à 0 et le signaler.

## Règle n°1 : Tempo est la seule source de l'auteur réel

Dans l'API Jira standard, un temps saisi via Tempo a pour auteur le **compte
applicatif Tempo** (`accountType = "app"`, nom affiché « Timesheets by Tempo »), et
un commentaire générique. L'auteur réel est **impossible à reconstituer** côté Jira.

- Ne **jamais** deviner ni répartir les heures entre collaborateurs par heuristique.
- Source de l'auteur : l'**API Tempo** (instance EU : `https://api.eu.tempo.io/4/worklogs`),
  ou un export Tempo fourni par l'utilisateur.
- Filtrage par ticket : Tempo identifie le ticket par son **identifiant numérique**
  (`issue.id`), pas par sa clé (`EMERAUDE-123`) : faire la correspondance via Jira.
- **Contrôle de cohérence obligatoire** : somme des heures Tempo = somme des heures
  Jira, par ticket et au total. Tout écart est une anomalie à expliquer avant de facturer.
- Les temps saisis directement dans Jira (hors Tempo) portent un auteur exploitable.
- Sans accès à Tempo : regrouper les temps Tempo sous « Non identifié (Tempo) » et
  le signaler comme blocage dans le livrable.

## Sécurité de la clé API Tempo

- Jamais dans la conversation si on peut l'éviter, jamais en mémoire, jamais dans un
  fichier versionné, jamais dans un ticket.
- Si elle doit servir à un script : fichier temporaire hors dépôt (ex. `.tempo_env`),
  `chmod 600`, **supprimé à la fin du traitement**.
- Si l'utilisateur l'a collée en clair : la traiter, puis **recommander sa révocation
  et sa régénération**.

## Méthode en deux phases

### Phase 1 : audit (toujours avant le tableau)

Produire une analyse textuelle, sans fichier :
- récapitulatif par client et par utilisateur (heures, jours) ;
- temps **orphelins** (ticket sans Epic parent) ;
- temps posés **directement sur un Epic** ;
- Epic **fermé** qui porte des heures ;
- incohérences Tempo / Jira (règle n°1) ;
- doublons apparents (même personne, même ticket, même jour, même durée) ;
- utilisateur sans profil de facturation connu ;
- temps à 0 h (ignorés).

**Attendre l'arbitrage de l'utilisateur** sur chaque anomalie avant la phase 2.

### Phase 2 : tableau

Seulement après arbitrage :
- par client, puis par utilisateur, avec l'Epic par ligne ;
- libellés **reformulés en travail réalisé** (« Paramétrage des droits du profil
  commercial ») et non en symptôme (« bug droits ») ;
- heures à **2 décimales**, jours = **heures ÷ 7** ;
- les exclusions sont **affichées** (section ou note dédiée), jamais retirées en silence ;
- pas d'arrondi sans consigne ;
- **pas de fichier XLSX sans demande** : par défaut, tableau dans la réponse.

## Règles génériques de facturation régie

| Règle | Application |
|---|---|
| Préfixe d'Epic `[REGIE]` | Facturable |
| Préfixe `[FORFAIT]`, Epic « Maintenance Annuelle » | Non facturable (compris dans le forfait ou le contrat) |
| Autre préfixe, ou aucun | Demander à l'utilisateur |
| Epic « Assistance » | Facturable ou non selon le contrat : demander |
| Temps sans ticket ni parent | Signalé ; règle client à appliquer (souvent supprimé du bordereau) |
| Formation | Au TJM du collaborateur, sauf pack de formation vendu séparément |
| Frais | Refacturés selon le contrat (souvent à 100 %) : demander |

**Clôture mensuelle (le 1er)** : la règle propre à chaque client (regroupement par
Epic, par utilisateur, par profil, en heures ou en jours, intervenants hors Jira à
ajouter) est dans le **Projet claude.ai du client**. La lire avant de produire le
bordereau, et demander s'il y a des jours hors Jira à facturer (AMOA, intervenants
externes).

## Entrées

### Option A : export CSV

Colonnes minimales : `issue_key`, `issue_summary`, `epic_key`, `epic_name`,
`project_key`, `author` (nom réel ou « Non identifié (Tempo) »), `started`,
`time_spent_seconds`, `comment`. Séparateur `;` ou `,` à détecter.

### Option B : connecteur Jira

JQL par projet et par période :
`project = <CLE> AND worklogDate >= "<début>" AND worklogDate <= "<fin>"`,
puis les worklogs de chaque ticket (`author.displayName`, `author.accountType`,
`started`, `timeSpentSeconds`, `comment`) et l'Epic parent. Appliquer la règle n°1
pour l'auteur.

## Format du bordereau XLSX (sur demande)

- Un onglet par client, plus un onglet « Synthèse » multi-clients.
- En-tête : client, période, base 7 h/j ; puis un bloc par utilisateur (nom et profil),
  ses lignes, son sous-total ; enfin le total client.
- Colonnes : Date (`DD/MM/YYYY`) | Epic (poste) | Ticket | Description | Heures
  (`#,##0.00`) | Jours (formule `=E/7`) | Montant HT (formule `=F*TJM`).
- **Toutes les colonnes Jours et Montant sont des formules Excel**, jamais des valeurs
  en dur. Recalculer le classeur (LibreOffice headless ou équivalent) et vérifier
  qu'il n'y a aucune erreur de formule.
- Charte AxENR (skill `axenr-brand`) : en-tête fond `#041212`, texte `#01DF82` ;
  total client fond `#041212`, texte clair ; bloc « Non identifié (Tempo) » en gris
  avec un liseré d'alerte.
- Nommage : `Suivi_Temps_<Client>_<Mois><Annee>.xlsx`.

## Cas particuliers

| Situation | Comportement |
|---|---|
| Auteur = compte applicatif Tempo, sans accès à Tempo | « Non identifié (Tempo) », signalé, jamais réparti |
| Temps sans Epic parent | Ligne conservée, colonne Epic vide, signalée |
| Utilisateur sans profil connu | Demander son profil avant de calculer |
| TJM absent | Heures et jours affichés, montant 0, avertissement |
| Plusieurs saisies le même jour sur le même ticket | Lignes distinctes, pas de fusion |
| Heures = 0 | Ligne ignorée |

## Historique Redmine

Pour une période antérieure à la bascule vers Jira (juillet 2026), ou un client
encore sur Redmine : voir `references/redmine-historique.md`.
