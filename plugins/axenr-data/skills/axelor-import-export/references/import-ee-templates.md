> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3 (articles : 0 écart sur 8 420 valeurs) ; édition entreprise obligatoire, à constater avec `ee_api.py info`. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Préparer des gabarits d'import AOP EE à partir des données du client

## Ce que fait ce skill

Le client montre son logiciel actuel — des **captures d'écran**, de **vrais exports**, ou des **Excel
bruts** hors format. Tu en tires des **gabarits d'import EE** (classeurs xlsx, un onglet par modèle) :

- **vides**, avec 2 ou 3 lignes d'exemple, pour que le client les remplisse et s'approprie le format ;
- ou **remplis** avec ses données, prêts à importer.

Tu les **prouves** sur un env jetable de même plateforme, puis ils passent **une seule fois** sur la base
de recette du client. Une recette abîmée par des essais se paie en drop, recréation et temps consultant :
aucun des deux moteurs d'import n'annule, et un second essai à chaud mélange les traces des deux.

## Les six consignes maîtresses (règles du skill, à appliquer telles quelles)

1. **On se base sur l'environnement cible, et rien de plus.** L'existence d'un champ se prouve dans la
   base ou l'API de l'env cible (métadonnées, export), jamais par une doc, une autre version ou la
   mémoire. *Pourquoi : modules, versions et champs Studio diffèrent d'une instance à l'autre, et un
   champ inexistant est ignoré à l'import sans aucun message.*
2. **Si Axelor n'a pas le champ, on l'ignore.** Le chef de projet ou le consultant tranchera avec le client.
3. **L'agent ne fait JAMAIS le choix des champs Studio** : c'est fait en projet. Un champ Studio présent
   sur l'env cible se signale ; il n'entre pas dans le gabarit.
4. **Questionnement limité** : s'il faut une phase de questions, c'est **10 points au maximum, les
   ultra-ambigus** ; tout le reste, tu le tranches seul (abandon ou correspondance alternative), décision
   tracée dans le registre.
5. **Tu maîtrises la fabrication des gabarits**, en un seul classeur complet ou en plusieurs par
   domaine, selon la forme demandée.
6. **Tu es polyvalent sur l'entrée** : captures d'écran (lecture image par image), fichiers d'export ou
   Excel bruts.

## Prérequis

**Obligatoires**
- Python 3 et deux bibliothèques : `requests` (appels REST) et `openpyxl` (lecture des classeurs) —
  `pip install requests openpyxl`.
- Une instance AOP **EE** cible (module `axelor-enterprise-edition`, que `ee_api.py info` constate) et un
  compte qui lit ses métadonnées par l'API REST ; pour importer, le droit d'import explicite (`canImport`).
- Une instance **jetable** de même plateforme AOP que la cible, pour la preuve du §6. Sans elle, ne pas
  annoncer les classeurs prêts pour la recette : leur preuve n'a pas eu lieu.

**Optionnels**
- `curl` — seulement pour ouvrir la session d'une instance hébergée (« Se connecter » ci-dessous). Sans lui,
  tout moyen d'obtenir un fichier de cookies au format Netscape et la valeur du cookie `CSRF-TOKEN` convient.
- `psql` (accès à la base de l'instance jetable) — seulement pour les postconditions écrites en SQL (§6,
  ex. libellé complet non vide). Sans accès SQL, relire les mêmes valeurs par l'API (`verify_import.py`, recherche REST).
- Les sources AOS / AOP de la version cible (publiques : github.com/axelor/axelor-open-suite et
  github.com/axelor/axelor-open-platform, au tag de la version ; ou les sources des jars de l'instance) — pour
  lire le `save()` d'un repository (§4, `compute`). Sans elles, décompiler le jar de l'instance ; à défaut,
  le point reste « non vérifié » dans le rapport et la répétition du §6 en décide.

## Les outils fournis

`scripts/` (Python 3, `requests` + `openpyxl`).

### Se connecter

**Instance hébergée (recette du client) : aucun mot de passe, ni dans une commande, ni dans un fichier, ni dans
la conversation avec l'agent.** L'utilisateur ouvre lui-même la session dans son terminal (pas par l'agent), avec
`curl`, qui écrit un fichier de cookies ; les scripts ne lisent que ce fichier. HTTPS obligatoire hors
localhost ; la double authentification n'est pas gérée par cette méthode. Sous bash :

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

Le mot de passe passe par l'entrée standard de `curl` (il n'apparaît ni dans la liste des processus ni dans
l'historique). Le jeton CSRF est la valeur du cookie `CSRF-TOKEN` du fichier ; il est renvoyé en en-tête
`X-CSRF-Token` sur toute écriture (POST / PUT / DELETE).

Les scripts lisent `AOS_URL`, `AOS_COOKIE_JAR` et `AOS_CSRF` : dès que `AOS_COOKIE_JAR` est défini, ils
ignorent `--cred` et n'appellent jamais `/callback`. Chaque commande du tableau se lance alors sans `--cred`
(`python3 scripts/ee_api.py <sous-commande> …`, `python3 scripts/verify_import.py <classeur>`) ;
`--confirm-write` doit répéter `$AOS_URL` à l'identique. Session absente ou expirée : le script le dit,
l'utilisateur rouvre la session par les mêmes commandes.

**Instance locale jetable** : identifiants dans un fichier `--cred` (json `url`, `username`, `password`) gardé
dans un répertoire temporaire hors dépôt, en droits 600 — **jamais** dans un projet ni dans un skill.
`--cred` se place **avant** la sous-commande. Dans le tableau, `ee_api.py --cred C …` est cette forme locale.

| Commande | Rôle | Écrit ? |
|---|---|---|
| `ee_api.py --cred C info` | EE ou non, version AOP, modules, apps actives, plafond d'envoi, **sièges de licence libres** | non |
| `ee_api.py --cred C fields <Modèle> > fields/<Modèle>.csv` | relevé des champs de l'env (type, cible, requis, unique, Studio à part) | non |
| `ee_api.py --cred C keys <Modèle>` | pour chaque fiche d'un référentiel : la colonne et la valeur de lien | non |
| `ee_api.py --cred C plan <classeur>` | prévision ligne par ligne : création, mise à jour, **écrasement** d'une fiche existante, comptes **rebloqués** faute de siège | non |
| `ee_api.py --cred C links <classeur>` | chaque valeur de lien existe sur l'env (par sa clé) ou est créée par le classeur | non |
| `ee_api.py --cred C export …` | export technique multi-onglets | non |
| `ee_api.py --cred C parse <Modèle> <classeur>` | analyse à blanc des onglets et colonnes | **une pièce jointe** (l'envoi) |
| `ee_api.py --cred C import <Modèle> <classeur> --compute … --confirm-write <URL exacte>` | import réel | **oui** |
| `check_templates.py <classeurs> --fields-dir fields [--expected F] [--final]` | contrôle hors ligne des classeurs | non |
| `verify_import.py <classeur> --cred C` | relit en base, valeur par valeur, ce que le classeur devait écrire | non |

## Déroulé

### 1. Cadrage

Établis en cherchant d'abord toi-même : l'env cible (URL, `info` : **EE ?** version AOP ?), l'accès en
lecture, la forme d'entrée, la forme de sortie (vide ou rempli, un classeur ou un par domaine), les
modèles visés et leur ordre, et **l'env de répétition** : même plateforme AOP que la cible, jetable (on peut
l'abîmer), dump avant, restauration après. Démarrer, arrêter ou écraser une instance demande le feu vert de
l'utilisateur, une fois pour toute la séquence. Avant toute écriture, vérifie quelle base l'instance utilise
réellement (nom de la base, pas seulement l'URL) : on n'importe jamais « pour voir » ailleurs que sur l'env
jetable. Si un dump de la recette est obtenable, répéter sur une copie restaurée de la recette est la
meilleure répétition possible.

`info` sans EE : ce skill ne s'applique pas → `import-bundles-classic.md`.

### 2. Relevé des champs et des clés sur l'env cible

```
ee_api.py --cred C fields Product > fields/Product.csv      # chaque modèle visé ET chaque référentiel pointé
ee_api.py --cred C keys Unit > keys/Unit.csv                 # les clés par lesquelles tes lignes pointeront l'existant
```
C'est la seule source de vérité de l'existence d'un champ (consigne 1). Compte aussi ce qui existe déjà
(données de démo, essais antérieurs, fiches vides) : une ligne qui « met à jour » une fiche seedée au lieu
d'en créer une donne un test faussement vert, et une clé unique déjà prise **écrase** la fiche existante.

### 3. Lecture de l'entrée, champ par champ

[import-ee-entree-client.md](import-ee-entree-client.md). Relevé
(id stable, où, exemple, compréhension), classement **direct / ambigu / absent / non repris**, registre
des arbitrages, et au plus 10 questions à l'utilisateur, posées en une fois en noms métier (consigne 4). Les
arbitrages tranchés ne se rouvrent pas.

### 4. Fabrication du gabarit

Chaque règle est prouvée au runtime — détail et sources : [import-ee-moteur.md](import-ee-moteur.md).

**À partir d'un export de l'env cible** (export technique EE, lecture seule, `ee_api.py export` ; à ne pas
confondre avec les exports fournis par le client, lus au §3) : exporte chaque modèle racine
filtré sur **une ou deux fiches** qui existent (sans fiche racine, aucun onglet lié ne sort), avec exactement
les colonnes retenues. Un chemin refusé par l'export est un chemin faux : l'import l'aurait ignoré en silence.
Ensuite, par script et jamais à la main :
- retire `id`, `<rel>.id` et les colonnes d'affichage (`<rel>.fullName`, `.name`, `.label`) ;
- retire **les onglets de référentiels réduits à leur clé** (`Currency`, `Company`, `User`, `Unit`…), sauf
  celui du modèle racine du gabarit ;
- réécris les décimaux en texte à point (l'export les écrit en nombres) ;
- remplace les lignes par 2 ou 3 lignes d'exemple écrites hors ligne ;
- garde l'onglet `__config__` s'il existe (noms d'onglet longs ; lu dans le code, non rejoué).

Aucune donnée de l'env ne reste dans le classeur livré : compare ses valeurs aux données exportées. Les
fichiers bruts restent dans un répertoire de travail temporaire, hors du livrable. Détail : [import-ee-moteur.md](import-ee-moteur.md), § L'export.

- **Un onglet = un modèle**, nommé par son nom simple (`Product`, `User`), 31 caractères au plus. Un
  classeur s'importe en **un appel** avec son modèle racine : tous ses onglets-modèles sont importés,
  dépendances d'abord, et leurs liens internes se résolvent. Une liste a son onglet de liaison
  `Modèle.champ` (ex. `User.roles` : `importId`, `roles.name`). Un onglet dont le nom n'est pas un modèle
  (« Lisez-moi ») est ignoré : la légende peut y vivre.
- **Clés.** Chaque ligne a une clé d'import explicite et stable (`<CLIENT>-ART-<code client>`). **Aucune
  colonne `id` ni `<rel>.id`.** Une clé au motif `<modèle-en-tirets>-<n>` (`product-92`,
  `product-family-12`) est un id local : tolérée **uniquement** comme valeur de lien dans un classeur
  généré pour la base qui l'a produite (voir §6), jamais comme clé de ligne.
- **Liens vers l'existant** : par `<rel>.importId` ou par la **clé requise-unique** de la cible
  (`group.code`, `productFamily.code`, `saleCurrency.codeISO`) — la valeur exacte vient de `keys`. Tout
  autre champ (`unit.name`, `currency.code`, `product.code`) laisse le lien **vide, rapport vert**.
- **Valeurs.** Colonne mal nommée = ignorée en silence. Cellule vide = efface en mise à jour ; colonne
  absente = conserve. Booléen : `true` / `false` seulement (`1`, `oui` valent faux ; vide = NULL, et la
  fiche échappe aux filtres « = faux »). Codes en **texte** (zéros de tête). **Décimaux en texte avec un
  point** : en cellule numérique, un décimal ≥ 1000 (`1074.623`) est relu « 1074,623 » et la ligne est
  rejetée — un essai sur des articles à bas prix passe, le vrai fichier perd ses articles chers.
- **Lignes d'exemple** (gabarit vide) : clé `EXEMPLE-…`, premier libellé « EXEMPLE – … », légende qui dit
  de les supprimer ; pas de colonne de marquage (elle serait ignorée).

Particularités par modèle : [import-ee-referentiels.md](import-ee-referentiels.md) — **Article**
(filtre `dtype = 'Product'`, `compute` indispensable) et **Utilisateur** (**jamais de colonne mot de
passe**, `blocked` explicite, sièges de licence, **un login existant écrase le compte**).

Contrôle : `check_templates.py <classeurs> --fields-dir fields --expected colonnes-attendues.csv` →
0 bloquant. `colonnes-attendues.csv` (`classeur;onglet;colonne;source;consigne`) se déduit du registre :
il prouve qu'aucune colonne retenue n'a été oubliée.

### 5. Remplissage (gabarit rempli)

Écris le classeur **par un script de génération** (le tien, gardé avec le livrable) qui prend : les
données client normalisées, les tables de correspondance de valeurs (libellé client → libellé Axelor), et
le fichier `keys` **de la base visée**. Normalise : une ligne par entité (doublons et rôles fusionnés),
dates ISO, décimaux **en texte** à point, booléens `true`/`false` explicites, codes en texte. Profile chaque
colonne numérique avant de la mapper : elle peut être dérivée d'une autre (un « coefficient » qui vaut
PV HT × 1,2 est un TTC) ou correspondre à un champ natif peu évident (coefficient de gestion →
`managPriceCoef`) ; la formule se vérifie sur toutes les lignes, pas sur un exemple. Une référence
introuvable dans `keys` va dans **rejets.csv** avec sa raison — jamais une fiche créée à la volée, jamais
un lien laissé vide en silence.

### 6. Preuve sur l'env jetable

Génère le classeur **pour l'env jetable** (ses `keys`) avec un préfixe `TEST-` sur la clé d'import **et**
les clés métier uniques (code article, login) — sinon l'import met à jour des fiches existantes et le
test sort faussement vert. Puis :

1. `plan` — la prévision (créations, mises à jour, écrasements, comptes rebloqués) est celle que tu attends ;
   `links` — chaque valeur de lien est retrouvée ;
2. `parse` — onglets et colonnes reconnus (un « ok » ne prouve pas l'écriture) ;
3. `import … --compute <onglets principaux>` — lis Statistics **et** Errors ;
4. `verify_import.py` → **0 écart** ; chaque écart est expliqué ou corrigé dans le générateur ;
5. rejeu du même classeur : `plan` = mises à jour seulement, aucun doublon (lignes par société comprises) ;
6. postconditions métier écrites **avant** l'import (libellé complet, fiche visible dans un sélecteur,
   connexion d'un utilisateur test après redémarrage…).

Une colonne n'est acquise que si sa valeur est relue en base. Deux corrections successives qui échouent :
arrête-toi et dis-le.

### 7. Passage unique en recette

Le classeur de recette sort du **même générateur, mêmes données**, avec deux différences seulement : sans
préfixe `TEST-`, et les `keys` relevés **sur la recette**. **Utilisateurs : pas de verdict « prêt » tant que
les comptes à ouvrir dépassent les sièges libres de la recette** (`info`, `plan`) — c'est au client de
choisir qui ouvrir, pas à l'ordre des lignes. Check-list, ordre et règle d'arrêt :
[import-ee-passage-en-recette.md](import-ee-passage-en-recette.md). En bref : `info` (sièges) et `plan` sur la recette
(lecture) montrent exactement les créations et mises à jour attendues et aucun compte rebloqué, go de l'utilisateur, puis `parse`,
`import --confirm-write <URL de la recette>`, `verify_import.py` aussitôt, **arrêt au premier écart**.

### 8. Livraison

Classeurs (+ onglet `Lisez-moi`), registre des arbitrages, colonnes attendues et sortie de
`check_templates.py`, `rejets.csv` s'il y a lieu, script de génération, et un rapport : ce qui est prouvé,
les écarts, ce qui n'a pas pu être vérifié (et où tu as cherché). Remets les fichiers à l'utilisateur par le
canal convenu avec lui. Ce que tu établis au runtime et qui n'est pas dans ce skill (version testée,
condition de validité) va dans le rapport, pour que l'utilisateur le capitalise ; une capacité de la plateforme
que tu n'as pas testée sur la version cible n'est jamais promise.

**Remise au client : ce qui part chez lui n'est pas ce que tu livres à l'utilisateur.** Le paquet client contient
les classeurs et leur légende, rien d'autre ; le registre, le rapport et les preuves restent internes. Avant
de le préparer, par script, avec le résultat dans le rapport :
- les commentaires d'en-tête ne gardent que le libellé et la consigne. Sortent la nature de la colonne, les
  identifiants d'inventaire, les renvois d'arbitrage (`P21`), les noms de l'équipe projet (intégrateur) et les décisions
  en attente ;
- les lignes d'exemple ne portent aucune personne réelle : ni salarié, ni contact, ni login, ni e-mail, ni
  code de paie. Mets des noms fictifs et mets à jour la clé dans **tous** les onglets qui la citent (un login
  peut vivre dans un autre classeur) ;
- contrôle : une liste de motifs fixée pour le chantier, à partir des formats de ses codes internes (sur
  une reprise ERP, par exemple : `\bP\d{2}\b`, `\b[A-Z]{2}-\d{2}\b`, `nature :`, `source :`, noms remplacés), recherchés sur le texte
  des commentaires **et** des cellules, en mots entiers, avec 0 occurrence. Un motif qui touche une vraie
  donnée du client s'ajuste, il ne se force pas. En-têtes identiques avant et après.

## Pièges qui ont déjà coûté

| Piège | Effet | Parade |
|---|---|---|
| Colonne `password` sur User | mot de passe en clair en base, connexion impossible, rejeu qui écrase le chiffré | aucune colonne ; mot de passe par l'API REST ou « mot de passe oublié » |
| Clé unique déjà prise (login `admin`) | la fiche existante est écrasée et perd sa clé d'import, rapport vert | `plan` avant tout import |
| Import sans `compute` | articles sans libellé complet ni n° de série : invisibles dans les sélecteurs | `compute` sur chaque onglet principal |
| `compute` = seconde passe | logique « à la création » et champs transitoires perdus (langue d'un utilisateur) | lire le `save()` du repository, fournir ces champs en colonne |
| Export Article non filtré | lignes par société exportées comme articles vides | `self.dtype = 'Product'` |
| Utilisateur importé | bloqué par défaut ; débloqué au-delà des sièges libres, **rebloqué dès l'enregistrement**, rapport vert | `blocked` explicite, `info` + `plan` avant import, liste des comptes à ouvrir fixée par le client |
| Décimal ≥ 1000 en cellule numérique | ligne rejetée (cause dans Errors, seul le compteur se voit) | décimaux en texte avec un point ; `check_templates.py` |
| Rapport « success », `parse` « ok » | ne disent rien de ce qui est écrit | `verify_import.py`, postconditions |
| Commentaires d'en-tête rédigés avec les notes de travail (nature, source d'inventaire, arbitrages), exemples tirés des données du client | livrés tels quels au client (reprise ERP du 26/09/2026 : des centaines de commentaires avec renvois internes, deux salariés réels dans les exemples) | nettoyage et anonymisation par script avant la remise (§8) |
