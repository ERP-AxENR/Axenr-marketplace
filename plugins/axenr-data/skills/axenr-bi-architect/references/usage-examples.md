# /axenr-bi-architect

Architecte BI senior pour la stack Axelor/AxENR + Apache Superset. Produit des requetes SQL PostgreSQL pretes + la configuration Superset associee + le layout dashboard, a partir d'un besoin metier exprime en langage naturel.

Detecte automatiquement le client AxENR depuis le `cwd` (planeteenr-app / systeko-app / emeraude-solaire-app / axenr-app / etc.) pour adapter les filtres `company_id`, les champs `attrs` custom et les conventions du client.

## USAGE

### Sans fichier (mode conseil + generation)

```
/axenr-bi-architect CA par commercial sur les 12 derniers mois
/axenr-bi-architect pipeline commercial par etape avec montant pondere
/axenr-bi-architect marge par affaire (CA - achats - main d'oeuvre)
/axenr-bi-architect delai moyen depot DP vers obtention DP par gestionnaire reseau
/axenr-bi-architect puissance installee cumulee par mois depuis 2024
/axenr-bi-architect top 10 clients par CA signe cette annee
/axenr-bi-architect rotation de stock par produit sur 6 mois
/axenr-bi-architect pourquoi mon dashboard affiche plus d'affaires qu'il n'y en a en realite
/axenr-bi-architect les panneaux Regles et RLS n'apparaissent pas sur mon dashboard
/axenr-bi-architect mon graphique marche dans BI Studio mais pas dans Axelor
```

### Avec fichier (analyse / diagnostic)

```
/axenr-bi-architect analyse ce dataset | ~/Downloads/export-superset.csv
/axenr-bi-architect pourquoi cette requete est lente | ~/Downloads/ma-requete.sql
/axenr-bi-architect ameliore ce dashboard | ~/Downloads/dashboard-screenshot.png
```

## DETECTION DU CLIENT

L'agent deduit le client depuis le `cwd` :

| cwd | Client | `company_id` typique |
|-----|--------|---------------------|
| `~/Desktop/Projects/planeteenr-app` | Planete ENR | pilote BI AxENR |
| `~/Desktop/Projects/systeko-app` | Systeko | a parametrer |
| `~/Desktop/Projects/emeraude-solaire-app` | Emeraude Solaire | 101 |
| `~/Desktop/Projects/axenr-app` | AxENR (dev interne) | - |
| `~/Desktop/Projects/synambu` | Synambu | - |
| `~/Desktop/Projects/energ-ia` | Energ-IA | - |
| `~/Desktop/Projects/yooz` | Yooz | - |
| autre | demande explicite | - |

L'agent applique les filtres `company_id` et les champs `attrs` JSON propres au client detecte.

Lance depuis le dossier du client pour beneficier de la detection automatique :

```bash
cd ~/Desktop/Projects/planeteenr-app
/axenr-bi-architect CA mensuel avec comparaison N-1
```

## ETAPES

### Etape 1 : Detection client

Appel a `client-context-detector`. Banner de confirmation.

### Etape 2 : Chargement des ressources

- `references/catalog.md` (10 templates SQL + KPIs + Superset best practices)
- `references/axelor-bi-embedded.md` si le dashboard est affiche dans Axelor (droits, RLS, incidents)
- Dictionnaire de donnees : requete directe sur `meta_model` / `meta_field` / `meta_json_field` (voir SKILL.md, RESSOURCES) plutot qu'un export Excel qui vieillit
- Projet client (READ-ONLY) : lecture des extensions / champs custom `attrs` documentes si accessibles

### Etape 3 : Deleguer a l'agent

```
subagent_type: axenr-bi-architect
prompt: |
  Besoin : <besoin-parse>
  Client : <detecte>
  Project path : <chemin client>
  Fichier auxiliaire : <csv / sql / image ou "aucun">
  Output dir : ~/Downloads/

  Applique ta methodologie complete (5 etapes apres PHASE 0).
  Format de reponse obligatoire : 5 sections (Comprehension, Tables, SQL, Superset, Hypotheses).
  Respecter strictement les conventions Axelor et les bonnes pratiques BI.
```

### Etape 4 : Presenter le livrable

L'agent retourne :
- Comprehension du besoin reformule
- Diagramme des tables concernees (Mermaid si > 2 tables)
- Requete SQL complete avec CTE commentees
- Configuration Superset (dataset, metriques, dimensions, filtres, charts recommandes, layout)
- Hypotheses et limites

### Etape 5 : Proposer les suivis

```
Actions disponibles :
1. Creer les index PostgreSQL recommandes pour optimiser
2. Convertir le dataset en Materialized View si volumetrie importante
3. Generer le JSON d'import Superset (Charts + Dashboard)
4. Produire la documentation du dashboard pour la direction
5. Iterer sur un aspect (ajouter un filtre, changer la granularite, ajouter une dimension)
```

## TYPES DE SORTIES SUPPORTES

L'agent peut produire selon le besoin :

- Analyse de dataset (mode exploration sur un CSV fourni)
- Recommandation de graphique (mode conseil rapide)
- Configuration Superset complete (mode executif)
- Structure de dashboard (layout detaille)
- Requete SQL commentee (mode developpement)
- Diagnostic de donnees (mode debug : probleme + requete cible + cause + correction)

## LIVRABLES (DANS `~/Downloads/`)

- `<nom-dashboard>-query.sql` : requete SQL commentee
- `<nom-dashboard>-superset-config.md` : configuration Superset (metriques, charts, layout)
- `<nom-dashboard>-doc.md` : documentation KPI + hypotheses + responsables
- Optionnel : `<nom-dashboard>-import.json` pour import direct dans Superset

## GARDE-FOUS

- READ-ONLY sur le projet client (pas d'ecriture, pas de commit, pas de push)
- Aucune modification du code Axelor
- Filtrage `archived IS NOT TRUE` + `company_id` systematique dans les SQL generees
- Pas de `SELECT *`, pas de `company_id` hardcode
- KPI sans cible -> l'agent questionne ("quelle cible voulez-vous afficher ?")
- NO EMOJIS (regle AxENR)
