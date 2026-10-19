# Axelor BI embarque (BI Studio / Superset dans Axelor)

> Specificites du module Axelor BI (add-on `axelor-bi`, Superset embarque dans
> Axelor). A lire des qu'un dashboard est affiche dans Axelor et pas seulement
> dans Superset : droits, RLS, incidents connus.

## 0. Version : la verifier avant d'affirmer

La documentation officielle Axelor BI est en version 4.0. Les instances clients
peuvent tourner sur une version anterieure (3.4.x, 3.5). Avant de citer un
ecran, un menu ou un comportement, demander ou lire la version du module BI de
l'instance. Une difference de comportement entre deux instances vient souvent
de la version ou des roles, rarement de la configuration du dashboard.

## 1. Droits et visibilite

| Regle | Detail |
|---|---|
| Panneaux Regles et RLS reserves au role BI admin | Sur la fiche d'un dashboard (BI > Dashboards), les panneaux Regles et RLS sont masques (`id="_isBiAdmin"`, `hidden="true"`). Un utilisateur bi.user ou bi.viewer ne les voit pas, meme s'il est admin Axelor. |
| Diagnostic « panneaux absents » | Si les panneaux manquent sur une instance et pas sur une autre a version identique, la cause est le role BI admin manquant, pas la version ni la configuration. |
| Droits a chaque menu de dashboard | A chaque creation de menu de dashboard, associer systematiquement les roles et/ou groupes autorises dans la section Regles. Un menu sans regle n'est pas un oubli anodin. |
| Liste des dashboards | Seuls les dashboards accessibles a l'utilisateur BI lecteur configure apparaissent dans BI > Dashboards. |
| Plein ecran | L'iframe embarquee n'autorise pas le plein ecran. Contournement cote utilisateur : F11 (plein ecran du navigateur). |

Les droits Axelor generaux (roles, groupes, menus) relevent du skill
`axelor-droits-expert`.

## 2. RLS (Row Level Security)

### 2.1 La RLS s'applique sur la couche externe

Superset encapsule le SQL du dataset virtuel dans une sous-requete et applique
le filtre RLS sur la requete externe. Toute colonne filtree par RLS doit donc
etre exposee dans le SELECT du dataset, avec l'alias exact attendu par le
filtre :

```sql
-- Le filtre RLS porte sur user_id : la colonne doit sortir du dataset
SELECT
  opp.id        AS opportunity_id,
  opp.user_id   AS user_id,      -- obligatoire pour la RLS
  opp.amount    AS montant
FROM crm_opportunity opp
WHERE opp.archived IS NOT TRUE;
```

### 2.2 Limite majeure en BI embarque : un seul compte lecteur

En BI embarque, Axelor se connecte a la base avec un seul compte lecteur. La
variable `__user__.id` ne resout donc pas l'utilisateur Axelor individuel : une
RLS « par utilisateur » ne fonctionne pas.

Contournement : scinder le dataset (une version globale et une version filtree
pour l'usage personnel, chacune derriere un menu dont les Regles limitent
l'acces). Le dire explicitement au client plutot que de promettre une RLS par
utilisateur.

### 2.3 Regles de configuration des filtres RLS

- Un filtre RLS s'applique au dataset du graphique cible, donc a tous les
  graphiques qui partagent ce dataset.
- Jamais deux graphiques de meme nom sur un dashboard qui utilise la RLS.
- Le nom du graphique dans le filtre doit etre identique au titre dans BI
  Studio.
- Les filtres utilisant `__parent__` ne s'appliquent que lorsque le dashboard
  est integre en panel-dashlet.
- Variables disponibles : `__user__`, `__parent__`, `__date__`, `__time__`,
  `__datetime__` ; operateur logique AND / OR entre filtres.

## 3. Incidents connus et correctifs

| Symptome | Cause | Correctif |
|---|---|---|
| Erreur 422 a l'activation de la configuration BI | Port de la base ferme cote serveur | Ouvrir le port ; escalader a l'equipe infra avec le diagnostic (voir section 4) |
| « Guest user cannot modify chart payload », souvent apres une montee de version | `query_context` du graphique nul ou perime | Rouvrir chaque graphique dans Explore, lancer la requete, reenregistrer |
| Graphique correct dans BI Studio, en erreur dans Axelor | Les controles du guest token (validation du `query_context`) ne tournent pas en mode admin Studio | Toujours tester le rendu embarque dans Axelor, pas seulement dans Studio |
| HTTP 500 a l'import d'un dashboard complexe | L'add-on corrompt les bundles complexes (cross-filtering, mixed timeseries, nombreux filtres natifs) | Simplifier le bundle, importer par morceaux ou reconstruire le dashboard dans Studio |
| La RLS ne s'enregistre pas | Contrainte NOT NULL sur `bi_bi_dashboard_filter.field` dans certaines versions du schema | Correctif de schema par un developpeur (suppression de la contrainte ou de la colonne), a valider sur une copie |
| Timeout a l'ouverture d'un dashboard | Requete trop lourde ou sans filtre temps par defaut | Filtre temps par defaut, index, vue materialisee (voir `catalog.md` section 3) |

## 4. Escalade infra : diagnostic attendu

Ne jamais escalader un « ca ne marche pas ». Fournir :

- l'instance et la version du module BI ;
- le type d'erreur exact (code HTTP, message) ;
- le port et l'IP concernes si c'est une erreur de connexion ;
- les etapes de reproduction ;
- ce qui a deja ete verifie (SQL direct, rendu Studio vs embarque).
