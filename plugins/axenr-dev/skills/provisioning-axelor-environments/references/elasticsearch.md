# Elasticsearch / Global Search (plateforme EE)

Recette **vérifiée dans les sources de l'AEP** le 2026-08-28 (arbre au tag
`v8.2.2`, recoupé sur la version 8.2.4-rc824). Rien ici n'est deviné, mais
**aucun environnement de l'auteur ne faisait tourner ES à cette date** : c'est une
recette lue dans le code, pas une recette éprouvée au runtime. Le premier env qui
la joue doit consigner ce qu'il observe (ici, et dans la documentation de l'env).

## L'interrupteur

`com.axelor.search.GlobalSearchSupport.isEnabled()` ne regarde qu'**une** propriété :

```properties
hibernate.search.backend.type = elasticsearch
```

`SUPPORTED_BACKENDS = Set.of("elasticsearch")` — c'est la **seule** valeur acceptée,
y compris pour OpenSearch (même backend Hibernate Search). Toute autre valeur, ou
la propriété absente, laisse la recherche globale désactivée **sans un mot dans les
logs**.

Attention : **Mais cet interrupteur ne suffit pas** : Hibernate Search a le sien, en amont.
`hibernate.search.enabled` est un réglage **natif d'Hibernate Search 7.2**
(`HibernateOrmMapperSettings.ENABLED`, vérifié au bytecode du jar
`hibernate-search-mapper-orm-7.2.6.Final`) — aucun code AEP ne le lit, c'est HS
lui-même. Posé à `false`, il éteint Hibernate Search **quel que soit**
`backend.type`, et la recherche globale reste morte sans que rien ne le dise.

Or plusieurs recettes d'env de l'auteur le portaient déjà à `false` (constaté sur
une recette de démo le 2026-08-30). C'est donc un **piège de donneur** typique : on active ES chez
soi, on ne comprend pas pourquoi rien ne s'indexe, et la cause est une ligne
héritée qu'on n'a jamais écrite. Vérifier les DEUX :

```properties
hibernate.search.enabled      = true          # ou ligne absente (défaut HS = true)
hibernate.search.backend.type = elasticsearch  # interrupteur AEP
```

Propriétés compagnes (code et doc d'accord, tout en points) :

```properties
hibernate.search.backend.hosts    = localhost:9200
hibernate.search.backend.protocol = https
hibernate.search.backend.username = elastic
hibernate.search.backend.password = ...
```

## Piège n°1 — les clés de tuning de la doc livrée sont FAUSSES

`EnterpriseAvailableAppSettings` lit `global.search.*` (**points**) ; la doc livrée
(`documentation/.../global-search.adoc`) écrit `global-search.*` (**tiret**) :

| Le code lit | La doc écrit | Effet si on copie la doc |
|---|---|---|
| `global.search.indexer.batch-size` | `global-search.indexer.batch-size` | ignorée en silence |
| `global.search.indexer.threads` | `global-search.indexer.threads` | ignorée en silence |
| `global.search.indexer.timeout` | `global-search.indexer.timeout` | ignorée en silence |
| `global.search.file.max-size` | `global-search.file.max-size` | ignorée en silence |
| `global.search.file.mime-type` | `global-search.file.type.custom` | ignorée en silence |

Une propriété inconnue d'AOP n'est jamais une erreur : elle est simplement lue par
personne. Le tuning semble appliqué, il ne l'est pas. Copier depuis **cette page**,
pas depuis la doc. Les clés `hibernate.search.backend.*` de la doc, elles, sont bonnes.

## Piège n°2 — aucun mapping livré = index vide, silencieux

`GlobalSearchMapping.load()` cherche, dans l'ordre : la propriété système
`global.search.mapping.file`, puis la propriété de config du même nom, puis la
ressource de classpath `axelor-search.yaml`. Si rien n'est trouvé :

```java
private static GlobalSearchMapping load(URL resource) {
  if (resource == null) return new GlobalSearchMapping();   // mapping VIDE, pas d'exception
  ...
```

Vérifié : **aucun `axelor-search.yaml` n'est livré** — ni dans les JAR
`axelor-enterprise-edition` déployés (8.2.3-SNAPSHOT et 8.2.4-rc824), ni dans les
sources de l'AEP. Conséquence : ES branché, connexion OK, **zéro entité indexée**,
la recherche globale ne renvoie jamais rien, et rien ne le signale. C'est le motif
classique de cette famille de pièges — ça boote vert et la fonction est morte.

**Donc** : fournir son propre mapping YAML est obligatoire, pas optionnel. Le poser
soit en ressource `axelor-search.yaml` du module, soit via
`global.search.mapping.file = /chemin/absolu.yaml`.

## Piège n°3 — il n'y a pas de service ES dans l'environnement d'origine

Rien n'écoutait sur 9200 (vérifié 2026-08-28), et le `docker-compose.yml` du
devcontainer de l'auteur ne déclarait que `db` et `dev`. « Activer Elasticsearch »
sur un socle sans service ES n'est donc pas une ligne de properties : c'est une
**décision d'infra** (ajouter un service au compose puis rebuild du conteneur, ou
pointer un ES externe). À remonter à l'utilisateur comme arbitrage, jamais à
trancher seul, et à faire figurer dans le manifest (`es.url`) une fois tranché.

## Compatibilité de versions

Hibernate Search 7.2 (celui de la plateforme EE) supporte **Elasticsearch 7.10 →
8.18** et **OpenSearch 1.3 → 2.16**. Les JAR clients
(`elasticsearch-rest-client`, `hibernate-search-backend-elasticsearch`) sont déjà
embarqués par la plateforme EE — rien à ajouter au build (probe W4).

## Après la config : construire l'index

Configurer ne remplit pas l'index. Il faut un **mass indexing** initial (l'AEP
expose une CLI `SearchCommand` avec une option de mapping). Tant qu'il n'a pas
tourné, la recherche est vide même avec un mapping correct — ne pas conclure « ES
ne marche pas » avant d'avoir indexé.

## Ce que les probes couvrent

- **W4** : le backend ES est bien dans le WAR.
- **R7** : `es.url` répond.
- Ce qu'aucune probe ne couvre encore (à écrire quand un env aura réellement tourné) :
  mapping non vide, index construit, recherche qui renvoie des résultats.
