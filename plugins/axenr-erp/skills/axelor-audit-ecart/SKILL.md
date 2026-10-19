---
name: axelor-audit-ecart
description: >
  Audit d'écart entre des spécifications (SFD, cahier des charges) et le code RÉEL d'une
  application Axelor AxENR, en croisant le dépôt ET la base SQL (low-code Studio). À utiliser dès
  qu'on doit affirmer la présence ou l'absence d'un champ, d'une sélection, d'un objet, d'une vue,
  d'une action ou d'un batch, savoir ce qui est « fait / à faire » avant une mise en production,
  transformer un retour d'audit (ex. Claude Code) en tickets fiables, ou cartographier
  l'avancement d'un module. Déclencheurs : « gap analysis Axelor », « est-ce que ce champ existe »,
  « audit SFD », « qu'est-ce qui reste à développer », « vérifier dans le code Axelor »,
  « low-code Studio », « reste à faire avant la prod ». Piège n°1 : conclure « absent » alors que
  la chose existe en low-code dans la base. PAS pour : l'audit des besoins d'un client en séance
  et son plan Jira (axenr-erp-audit), la qualification d'une capacité GMAO (gmao-capabilities).
metadata:
  owner: axenr
  family: fonctionnel
---

# Audit d'écart SFD ↔ code Axelor (AxENR)

## Environnement d'exécution

| Où | Comportement |
|---|---|
| Claude Code | Lecture du dépôt (cwd) et de la base en SELECT seul ; livrables écrits dans `~/Downloads`. |
| claude.ai et Cowork | Pas d'accès au dépôt ni à la base : fournir les requêtes SQL et les recherches à lancer, demander les résultats, puis rendre les verdicts. Sans résultat, le verdict est « INDÉTERMINÉ ». |

## Pourquoi cette compétence existe

Chez AxENR, une application Axelor a **deux sources de vérité**, pas une :

1. **Les fichiers du dépôt** (`modules/*/src/main/resources/domains/*.xml`, `views/*.xml`, `*.java`…) : le code versionné.
2. **La base de données** (tables `meta_field`, `meta_select`, `meta_view`, `meta_action`, `meta_menu`, `meta_model`…), où vivent **tous les éléments créés avec Studio (low-code)**.

Un champ, une sélection, une vue ou une action peut exister **uniquement en base** (créé avec Studio) et n'apparaître dans **aucun fichier** du dépôt. C'est très courant sur les projets clients AxENR.

**Le piège, vérifié sur le terrain :** un audit qui ne regarde que les fichiers (un `grep` dans le dépôt, un sous-agent limité au dépôt) conclut « ABSENT » à tort. À l'inverse, il peut aussi rater un développement déjà fait. Une fausse conclusion « à créer » gonfle un chiffrage de plusieurs jours sur une fonctionnalité qui existe déjà ; une fausse conclusion « fait » envoie un développeur recetter du vide.

Règle d'or : **ne jamais affirmer qu'une chose existe ou n'existe pas dans une app Axelor sans avoir croisé fichiers ET base.**

## La méthode en 4 temps

### 1. Établir l'accès à la base AVANT tout

C'est le prérequis non négociable. Sans accès base, l'audit est aveugle au low-code et ne vaut pas mieux qu'un `grep`.

- Récupérer la connexion dans `axelor-config.properties` (`db.default.url`, `db.default.user`, `db.default.password`). C'est ce fichier, **pas** `application.properties`.
- Ouvrir une connexion **en lecture seule** : `psql` en direct, ou par Docker si la base tourne en conteneur (`docker exec -it <conteneur_pg> psql -U <user> -d <db>`). Pour une base distante, utiliser l'hôte et le port de `db.default.url`.
- **Toujours en SELECT seul.** Jamais d'INSERT, UPDATE ou DELETE sur la base d'un client.

Si l'accès base est réellement impossible : le dire, et marquer les points incertains « INDÉTERMINÉ (base inaccessible) » plutôt que d'inventer un verdict « absent ». Une non-réponse honnête vaut mieux qu'une fausse certitude.

### 2. Calibrer sur un cas témoin

Avant de statuer, **prouver que la méthode voit le low-code** en cherchant un élément dont on SAIT qu'il existe (idéalement visible à l'écran sur une fiche), par exemple un champ custom connu.

Si la requête ne retrouve pas ce témoin en base, c'est l'accès ou la requête qui est en cause : **corriger avant de continuer**. Ce réflexe distingue un audit fiable d'un audit qui se croit fiable. Requêtes de calibrage : `references/requetes-sql.md`.

### 3. Croiser fichiers × base pour CHAQUE point

Pour chaque champ, objet, vue ou action, chercher dans les **deux** sources et rendre un verdict explicite :

| Verdict | Signification |
|---|---|
| `EXISTE (fichier + base)` | Présent dans le dépôt ET en base : état nominal |
| `EXISTE (base seule)` | **Low-code Studio** : présent en base, absent du dépôt. Attention : dette technique (voir plus bas) |
| `EXISTE (fichier seul)` | Déclaré en fichier (la base suit au démarrage si `ddl=update`) |
| `ABSENT (fichiers + base)` | Réellement à créer, vérifié des deux côtés |
| `INDÉTERMINÉ` | Accès base impossible, à lever |

Toujours accompagner le verdict d'une **preuve** : `chemin/fichier.xml:ligne` et/ou le résultat de la requête SQL. Un verdict sans preuve ne vaut rien.

Dans les fichiers, ignorer `build/`, `.cache/`, `src-gen/`, `expanded/`, `.gradle/` : du code généré ou tiers qui donne de faux positifs. La source de vérité fichier est `modules/*/src/main/`.

Requêtes par type d'objet (champ, sélection, vue, menu, action) : `references/requetes-sql.md`.

### 4. Qualifier l'écart pour l'action

Pour chaque écart, qualifier :

- **Création ou extension** : « à créer » (rien n'existe) ou « à étendre » (une base existe déjà, par exemple un import CSV générique à spécialiser). Cette distinction change le chiffrage : l'expliciter.
- **Spécifique / config low-code / natif AOS** : un besoin couvert par du natif Axelor non câblé, ou par de la config Studio, n'est pas un développement. Ne pas facturer du développement pour de la config.
- **Effort réaliste** : recaler les charges sur ces natures réelles. Se méfier des estimations héritées d'un audit non vérifié.

## La dette technique low-code (à toujours signaler)

Quand un audit révèle des champs `EXISTE (base seule)` (colonnes réelles en base, `is_json=false`, absentes des fichiers du dépôt), c'est un **risque concret** :

- au prochain rebuild ou à la prochaine migration, selon `db.default.ddl`, ces colonnes et leurs données peuvent être **perdues ou désynchronisées**, car le code ne les déclare pas ;
- action de fond : **verser ces champs dans les domains** (mêmes nom et type que la colonne) pour que `ddl=update` les reconnaisse au lieu de les recréer.

C'est souvent le risque le plus important qu'un audit révèle avant une mise en production. Le remonter systématiquement, idéalement dans un ticket dédié.

## Ordre de surcharge AxENR

**dépôt du client > AxENR (socle) > AOS (natif)**. Un même objet (Product, Invoice, SaleOrder, StockMove…) peut être enrichi à plusieurs niveaux. Quand on conclut « ce champ existe », préciser **dans quel dépôt** il vit, et **ne jamais proposer de modifier `axenr-app` (socle mutualisé) pour un besoin propre à un client** : le correctif va dans le dépôt du client.

## Restituer un audit

1. **Méthode** (1 ligne) : « vérification croisée fichiers × base SQL, accès confirmé, calibré sur <témoin> », pour que le lecteur sache que ce n'est pas un simple grep.
2. **Tableau d'audit** par chapitre ou exigence : Exigence | Statut | Preuve | Type | Reste à faire.
3. **Ce qui est FAIT** et **ce qui est à CRÉER** (vérifié des deux côtés), séparés sans ambiguïté.
4. **Dette low-code** : les champs en base non versés, en alerte.
5. **Restes à faire qualifiés** : création ou extension, effort, dépendances bloquantes (formats clients, accès, validations métier).

## Transformer l'audit en tickets

Si l'audit doit produire des tickets pour un développeur : `references/tickets-dev.md`. Un développeur a besoin du **contexte et du but** (la logique métier) ET de **repères techniques** (points d'accroche existants), sans qu'on lui dicte le code. Pour les règles de rattachement et d'assignation Jira : `organisateur-jira`.

## Erreurs à ne pas reproduire (vécu de terrain)

- **Conclure depuis le seul dépôt.** Un sous-agent ou un `grep` qui ne voit que les fichiers manque tout le low-code.
- **Faire confiance à un audit externe non vérifié.** Un rapport d'audit (même de Claude Code) peut halluciner des noms de classes ou de champs, ou sous-estimer l'existant. Le confronter au code réel avant d'en faire des tickets ou un chiffrage.
- **Lire `build/` ou les caches.** Faux positifs garantis. S'en tenir à `src/main/`.
- **Affirmer sans preuve.** Chaque verdict porte son `chemin:ligne` ou son résultat SQL.
