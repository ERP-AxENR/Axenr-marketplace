> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3 (bout en bout une fois : près de 200 000 valeurs comparées, 0 écart). AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Figer l'état d'une instance Axelor en paquet data-init

## Ce que fait ce skill

On part de fiches qui **existent déjà** sur une instance (souvent la recette d'un client, construite par
imports successifs et corrections à la main) et on produit un **paquet de chargement au premier démarrage**
(`data-init/input-config.xml` + CSV, moteur classique `com.axelor.data`) qui les recrée **à l'identique** sur
une base neuve. Le paquet est **généré depuis l'état relu par l'API**, jamais depuis les fichiers du client :
l'instance a presque toujours divergé de ses fichiers d'origine (corrections, mises à jour, défauts réparés).

Cas prouvé de bout en bout : une recette client, septembre 2026, AOS 9.1.6 / AOP EE 8.2.3 — 15 modèles,
plus de 1 700 fiches, près de 200 000 valeurs comparées, 0 écart ; faits et preuves dans
[import-data-init-preuves.md](import-data-init-preuves.md).

## Prérequis

**Obligatoires**
- Python 3 et `requests` (`pip install requests`) — `lire_etat.py`, `ee_api.py`, `jouer_import_config.py`.
  (`ee_api.py` charge `openpyxl` seulement pour ses sous-commandes `plan`, `links` et `import`, que ce skill
  n'utilise pas.)
- `xmllint` (libxml2-utils) et le `data-import.xsd` de la plateforme cible (dans le jar ou les sources
  d'`axelor-core`) — `controles_statiques.py --xsd <data-import.xsd>`.
- Un compte qui **lit** les modèles du périmètre par l'API REST de l'instance source (lecture seule : aucune
  écriture sur la source, jamais).
- Pour la preuve du §4 : une instance **jetable** de même plateforme et mêmes modules que la cible, sur une
  base PostgreSQL jetable, le moyen de construire et démarrer l'application qui porte le paquet (WAR
  dépaqueté sous Tomcat, par exemple) et le fichier de licence EE (sans lui, aucun enregistrement : code 1020).
- `psql` et l'accès SQL à la base de cet env de preuve — `controle_sql.py` (cases NULL, empreinte), copie de
  base, preuves (d) et (e) du §5. Sans accès SQL, ces preuves ne se jouent pas et le skill n'a pas
  d'équivalent : ne pas déclarer le paquet prouvé.
- Le journal de démarrage de l'application (`catalina.out` ou équivalent), lu par `verifier_journal.py`, au
  format de log par défaut d'AOP (lignes « date heure.ms NIVEAU pid --- [thread] logger »). Avec un autre
  format (comportement déduit du code du script, jamais essayé sur un autre format), il peut classer à tort des erreurs d'autres modules comme
  erreurs du paquet : relire alors le journal à la main.

**Optionnels**
- `curl` — seulement pour ouvrir la session d'une instance hébergée (« Se connecter », §1). Sans lui, tout
  moyen d'obtenir un fichier de cookies au format Netscape et la valeur du cookie `CSRF-TOKEN` convient.

## Les deux erreurs irrattrapables — à tenir avant tout le reste

1. **Le paquet joue sur une base existante.** Un data-init joue à la **première installation** de son module
   sur la base. Posé dans un module jamais installé sur la recette ou la prod, il y jouerait au prochain
   démarrage et réécrirait les fiches. **Le poser dans le module application** (`application = true`, celui qui
   porte `appName`) : il est installé partout, il dépend de tout donc passe **en dernier**, et il ne rejoue
   jamais — sauf si quelqu'un retire sa ligne de `meta_module` (prouvé : il rejoue alors et écrase).
2. **Il charge à moitié, en silence.** Au démarrage le moteur journalise les erreurs et continue ; le module
   est marqué installé et ne rejouera jamais. Seules preuves : le journal (0 erreur **pendant la lecture des
   fichiers du paquet**) et la base relue contre l'oracle.

## Déroulé

Ordre non négociable : **périmètre et oracle → questions → paquet → contrôles statiques → sonde → base neuve →
rejeu → base déjà chargée + témoin → kit → nettoyage.**

### 1. Périmètre puis oracle (lecture seule sur la source)

Écrire le **périmètre** (`perimetre.json`, format dans [import-data-init-perimetre.md](import-data-init-perimetre.md) ;
exemple : `assets/perimetre-exemple.json`, structure du cas prouvé) : pour chaque modèle, le domaine qui isole les
fiches à reprendre, la clé de ligne, la clé métier des cibles de liens. Puis :

```bash
python3 scripts/lire_etat.py --cred acces.json --perimetre perimetre.json --out etat-source --meta
```

`acces.json` (url, identifiant, mot de passe) ne vaut que pour une instance locale jetable. Sur une instance
**hébergée**, aucun mot de passe dans un fichier, dans une commande ni dans la conversation avec l'agent
(« Se connecter » ci-dessous) : la commande devient
`python3 scripts/lire_etat.py --perimetre perimetre.json --out etat-source --meta` (sans `--cred`, avec
`AOS_URL`, `AOS_COOKIE_JAR` et `AOS_CSRF` exportés). Même règle pour `ee_api.py`. `jouer_import_config.py`
n'écrit que sur un env de preuve local (il refuse une URL qui ne contient pas `localhost`) et garde son `--cred`.

#### Se connecter

L'utilisateur ouvre lui-même la session dans son terminal (pas par l'agent), avec `curl`, qui écrit un fichier
de cookies ; les scripts ne lisent que ce fichier. HTTPS obligatoire hors localhost ; la double
authentification n'est pas gérée par cette méthode. Sous bash :

```bash
export AOS_URL="https://<instance>"                  # sans « / » final
export AOS_COOKIE_JAR="$HOME/.aos-session.jar"          # fichier de cookies, hors de tout dépôt
( umask 077; read -r -s -p "Mot de passe : " PW; echo
  printf '%s' "$PW" | curl -sS -o /dev/null -w '%{http_code}\n' -c "$AOS_COOKIE_JAR" -b "$AOS_COOKIE_JAR" \
    -X POST "$AOS_URL/callback?client_name=AxelorFormClient" \
    --data-urlencode "username=<login>" --data-urlencode "password@-"
  unset PW )
curl -sS -b "$AOS_COOKIE_JAR" -c "$AOS_COOKIE_JAR" "$AOS_URL/ws/public/app/info"   # contrôle : "user":{"login":"<login>", …}
export AOS_CSRF=$(awk -F'\t' '$6=="CSRF-TOKEN"{print $7}' "$AOS_COOKIE_JAR" | tail -1)
```

Le mot de passe passe par l'entrée standard de `curl` (ni liste des processus, ni historique). Le jeton CSRF est
la valeur du cookie `CSRF-TOKEN` du fichier ; il est renvoyé en en-tête `X-CSRF-Token` sur toute écriture
(POST / PUT / DELETE). Les scripts (`lire_etat.py`, `ee_api.py`) lisent `AOS_URL`, `AOS_COOKIE_JAR` et
`AOS_CSRF` ; dès que `AOS_COOKIE_JAR` est défini, ils ignorent `--cred` et n'appellent jamais `/callback`.
Session absente ou expirée : le script le dit, l'utilisateur rouvre la session par les mêmes commandes.

Photographier aussi la source avant/après la session (nombre de fiches, dernier id, dernière mise à jour,
pièces jointes) : c'est la preuve qu'elle n'a subi aucune écriture. **Profiler chaque CSV** (valeurs
distinctes par colonne) : c'est là qu'apparaissent les fiches de démo accrochées (société avec ses
configurations, groupes avec leurs rôles), les liens vers des doublons sans clé, les cases vides.

### 2. Questions (10 au plus, en une fois, chacune avec une proposition)

Ce qu'il faut presque toujours trancher : périmètre de la société (identité seule, ou configurations ?),
groupes avec ou sans leurs rôles, configuration de la cible (`studio.apps.install`, `application.locale`,
`data.import.demo-data`), dépôt et branche de l'application qui portera le paquet, informations réelles du
client à substituer aux valeurs de démo, dump disponible, retrait du paquet après usage. Une architecture ou
un périmètre se font trancher (AskUserQuestion), le reste se propose par défaut.

### 3. Paquet

```bash
python3 scripts/generer_paquet.py --perimetre perimetre.json --oracle etat-source --out data-init
python3 scripts/controles_statiques.py --perimetre perimetre.json --oracle etat-source --xsd <data-import.xsd> data-init
```

Le générateur applique les règles prouvées (pourquoi chacune : [import-data-init-preuves.md](import-data-init-preuves.md)) :
aucun `call=` ; recherche par clé sur chaque input ; liens par clé métier + `update="true"` + `if=` ;
booléens toujours explicites (case vide de la source → `false`, tracé) ; plusieurs-à-plusieurs à membres
multiples → une recherche par membre ; champs « non_ecrits » du périmètre exclus et tracés dans
`ecarts-attendus.json`. **Ne jamais retoucher le paquet à la main** : corriger le périmètre, régénérer.

Les contrôles statiques bloquent sur : XSD, `call=`, `self.id =`, `update="true"` sur un input, BOM, clé vide ou
répétée, colonne de mot de passe, booléen ni true ni false, décimal à virgule, **valeur de lien introuvable**
(ni créée par le paquet, ni listée dans « base_neuve » — à vérifier sur une vraie base neuve, pas à supposer).

### 4. Env de preuve — le go de l'utilisateur, une fois pour toute la séquence

Même plateforme, **mêmes modules** (relever la liste par `ee_api.py info`, comparer au WAR construit), le
module application **au même nom**, `data.import.demo-data = false`, pièces jointes isolées, bases jetables.
Déployer le WAR en dossier dépaqueté : on échange alors `WEB-INF/classes/data-init` (sonde ↔ complet) et
l'URL de base entre deux démarrages sans reconstruire. **Charger la licence de démonstration** (Administration >
Gestion des licences) après le premier démarrage : sans elle, aucun enregistrement (code 1020) — le data-init,
lui, passe. Avant chaque démarrage avec le paquet, vérifie quelle base l'instance utilise réellement (nom de la
base dans sa configuration, pas seulement l'URL) : un paquet démarré sur une base existante est la première
des deux erreurs irrattrapables.

### 5. Preuves, dans cet ordre

| # | Démarrage / geste | Attendu |
|---|---|---|
| a | **Sonde** (`--sonde` : échantillon + fermeture de ses liens) sur base neuve | 0 erreur, 0 écart |
| b | Paquet complet sur base neuve | `verifier_journal.py` OK ; `comparer_etat.py` 0 écart bloquant ; `controle_sql.py` 0 case NULL |
| c | **Rejeu** par configuration d'import (`jouer_import_config.py`) | journal « Not null » = lignes, 0 anomalie ; `controle_sql.py --empreinte` identique avant/après |
| d | Copie de la base chargée, **modifiée** (quelques fiches) et **amputée** (une fiche), redémarrée avec le paquet | journal : application **non** installée ; empreintes identiques |
| e | **Témoin** : même copie, ligne de l'application retirée de `meta_module` | le paquet rejoue et écrase — le test (d) est discriminant |
| f | Gestes après démarrage (compteurs de séquence, etc.) | valeur relue, puis usage (ex. : 1er tiers créé = numéro attendu) |

```bash
python3 scripts/verifier_journal.py catalina.out --config data-init/input-config.xml --application <app>
python3 scripts/lire_etat.py --cred acces-preuve.json --perimetre perimetre.json --out etat-base
python3 scripts/comparer_etat.py --oracle etat-source --base etat-base --ecarts ecarts-attendus.json --out comparaison
python3 scripts/controle_sql.py --perimetre perimetre.json --base <base>
```

Une copie de base par `TEMPLATE` emporte la ligne de licence : la retirer **avant** le démarrage (piège 1020 de
collision, la procedure de montage d'environnement jetable).

### 6. Livrables

- `data-init/` à copier dans `src/main/resources/` **de l'application** ;
- gestes après démarrage (ex. `assets/geste-compteur-sequence-tiers.xml` : prochain numéro des tiers,
  `update="true"`, ne crée jamais) ;
- **kit de contrôle après la vraie recréation** : oracle, `ecarts-attendus.json`, `lire_etat.py`,
  `comparer_etat.py`, `verifier_journal.py`, `ee_api.py`, `perimetre.py`, mode d'emploi — tester le kit en
  autonome (relire la source avec lui : fichiers identiques à l'oracle) ;
- notice développeur : emplacement, pourquoi il ne rejoue pas et ce qui le ferait rejouer, configuration
  requise, gestes après démarrage dans l'ordre (licence, kit, compteurs, mots de passe, redémarrage), écarts
  décidés, **retrait du paquet au commit suivant**, avertissement données personnelles (comptes, e-mails dans
  un dépôt de code) ;
- rapport : prouvé / écarts / non vérifié (et où on a cherché) / décisions attendues.

### 7. Nettoyage

Arrêter l'env de preuve, supprimer ses bases jetables (garder un dump de la base neuve chargée, utile en
référence), retirer l'env de votre inventaire d'environnements s'il y en a un, supprimer les fichiers d'accès
de la session (fichier de cookies, `acces*.json`). Refaire la photographie de la source : identique à celle du
début.

## Ce qui manque toujours au bout d'un data-init (et comment le traiter)

Pendant le data-init, aucune app Studio n'est installée : **pas de configuration de l'app Base, pas de
séquences d'init-data**. Et le moteur fait `JPA.manage` : **aucun `save()` de repository**. Donc, sans
geste :
- libellés calculés (`fullName`, `simpleFullName`, « [code] nom ») → à poser en colonne (l'oracle les porte) ;
- séquences : le paquet porte les numéros explicites ; le **compteur** est créé après, à 1 → geste après
  démarrage (sinon il réémet des numéros déjà pris) ;
- codes-barres, images, situations comptables, traductions formatées → hors paquet (le dire) ;
- seuls les listeners JPA tournent (ex. `MainActivityListener` calcule `fullName`).

## Pièges déjà payés

| Piège | Effet | Parade |
|---|---|---|
| Paquet dans un module non installé sur les bases existantes | rejoue sur la recette/prod et écrase | module application ; prouver (d) + (e) |
| `call=ImportPartner` / `ImportProduct` au data-init | NPE (AppBase absente) → fichier entier perdu | aucun `call=` ; valeurs calculées en colonne |
| Journal filtré sur « ERROR » global | faux positifs (vues, autres modules) ou faux négatifs | `verifier_journal.py` : erreurs **pendant** les fichiers du paquet |
| Case vide dans la source (`archived` NULL partout) | reproduite, la fiche échappe aux filtres « = faux » | booléens explicites ; écart tracé |
| Lien vers une fiche sans clé (doublon créé par un enregistrement) | lien vide sur la base recréée | clé métier de la cible (`cles_cibles`), ex. e-mail par adresse |
| Société de démo gardée comme « société id 1 » | configurations, tiers, banque, logos de démo pointés | décider « identité seule » ; lister le reste |
| Base neuve sans licence | tout enregistrement refusé (1020) | licence chargée à l'écran avant rejeu et gestes |
| Kit dépendant du poste | inutilisable chez le développeur | tout copier dans le kit, le rejouer depuis un dossier qui ne contient que le kit |
| Lien vers une fiche créée par un input SUIVANT (ex. la société vers l'adresse de son siège) | lien vide, journal propre | parents d'abord dans `ordre_paquet` ; `controles_statiques.py` le bloque |

## Voir aussi

`import-bundles-classic.md` (moteur classique, P1-P13 ; étude de cas tiers) ;
`import-ee-templates.md` (`ee_api.py`, import EE) ; la procedure de montage d'environnement jetable (env de
preuve, licence, clones) ; `demo-data-generator` (`references/methode-rejouabilite.md` pour le cas SQL).
Pour l'env de preuve : une instance jetable, reproduire avant de corriger, rendre l'instance à l'état initial.
