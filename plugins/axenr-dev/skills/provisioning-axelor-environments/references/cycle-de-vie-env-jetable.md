# Cycle de vie d'un environnement JETABLE de campagne de qualification

Procédure générique et réutilisable. N'écrit sur aucun environnement réel —
aucun nom d'env, de base ou de port ci-dessous n'est vivant : ce sont des
gabarits `<PLACEHOLDER>`. Ce document est la référence à suivre **la prochaine
fois** qu'une campagne de qualification de capacités (injection de cas de test
pour établir ce que la plateforme sait réellement faire) a besoin d'un terrain
d'injection.

Rédigé le 2026-08-30 : aucun environnement de ce type n'était monté à cette date,
la liste blanche des sacrifiables (§1.3 a) était vide. Ce document prépare le
prochain, il n'en démonte aucun au jour de sa rédaction.

## 0. Portée et principe directeur

Un env jetable = worktree (ou app) dédié + base PostgreSQL dédiée + Tomcat
dédié, monté pour qu'une campagne y injecte des cas de test (SQL, Studio, WS
de création, import, champ custom, thème, vue), le casse éventuellement, puis
le jette. Trois textes gouvernent déjà cette matière et ce document ne les
duplique pas, il les enchaîne :

| Question | Référence |
|---|---|
| Comment monter la pile (versions, build, boot) | `references/from-scratch.md` ou `SKILL.md` (patterns A / A-bis) du skill `provisioning-axelor-environments`, selon l'origine (voir §1.2) |
| Pourquoi et quand un env doit être jetable | règle non négociable d'une campagne de qualification : « on n'injecte jamais hors d'un env explicitement marqué sacrifiable » |
| Où vit le marquage officiel | la liste blanche des envs sacrifiables tenue par l'équipe (§1.3 a) |

**Principe directeur du démontage** : la casse d'un env Axelor ne passe pas
par la donnée métier, elle passe par la couche méta, les caches et les
séquences. « Il ne reste rien » ne se prouve donc pas en regardant si des
lignes métier subsistent — ça se prouve couche par couche : processus, WAR,
disque, base, git, registre documentaire. Le §3 ci-dessous est construit
comme cette liste de couches, pas comme une checklist de confort.

---

## 1. Naissance — ce qu'il faut faire à la création pour que l'env soit identifié comme jetable

### 1.1 Nommage

Choisir un nom court et distinctif (`<ENV>`), jamais réutilisé par un env
vivant du registre. Règle héritée du provisioning (`SKILL.md` et `references/from-scratch.md`) : le nom
du **module** ne doit jamais être identique à `appName` (sinon dépendance
circulaire au boot, piège rencontré le 2026-08-20 sur une app dont le module
et l'`appName` portaient le même nom) — appliquer la
même prudence ici : `appName = axelor-<env>`, module `axelor-<domaine>`,
jamais les deux identiques.

### 1.2 Provisioning — choisir le bon skill selon l'origine

| Origine de la pile | Skill |
|---|---|
| Cible = une combinaison AOS/EE/modules qui n'existe nulle part dans le parc | `references/from-scratch.md` (manifest d'intention + probes rouge/vert) |
| Cible = reproduire une recette déjà vivante (worktree d'un monorepo qui boote) | `SKILL.md` Pattern A ou A-bis |

Dans les deux cas, les **3 axes d'isolation** sont non négociables et doivent
être vérifiables en une commande chacun :

1. **Branche** dédiée (jamais HEAD détachée sur l'arbre principal).
2. **Base de données** dédiée, vierge (`CREATE DATABASE <db> OWNER <role-pg>;`,
   `ddl=update`, `data.import.demo-data=false`).
3. **`if-module`** aligné sur le nom du module réellement installé dans cet
   env (`grep -rho 'if-module="[^"]*"' modules/*/src/main/resources/views/`).

Et un **Tomcat dédié**, jamais `./gradlew run` sur le port partagé 8080 :
un `CATALINA_BASE` propre par env (`<TOMCAT_ENV>`), son propre
`bin/setenv.sh` (ne pas hériter du `bin/setenv.sh` de l'installation Tomcat
partagée, sinon un ajustement mémoire pour cet env affecte les autres), un port
HTTP et un port shutdown non utilisés par le registre des envs, un script
de pilotage `run.sh {start|stop|restart|status|redeploy|logs}` qui **vérifie
le HTTP 200** avant de déclarer le start réussi. Ce script n'est pas livré avec
le skill : à défaut, piloter le Tomcat directement
(`CATALINA_BASE=<TOMCAT_ENV> <CATALINA_HOME>/bin/catalina.sh start` ou `stop`)
et vérifier le HTTP 200 par `curl` sur l'URL de l'app avant de déclarer le
démarrage réussi.

Si l'env clone une base existante (TEMPLATE ou dump) plutôt qu'une base
vierge : traitement licence EE **préventif**, avant le premier boot —
`pg_dump -t enterprise_app_license --data-only` puis `DELETE FROM
enterprise_app_license WHERE unique_id='<id>';` (évite le code 1020 bloquant
à chaque save, voir la ligne 1020 des « Erreurs fréquentes » de
`SKILL.md`). Sur une
base vierge ce traitement ne s'applique pas — la licence se charge par l'UI
au premier boot (sauf si un `certificate.crt` est déjà présent dans le dossier
de pièces jointes : voir `references/from-scratch.md`, phase 3 point 2 ; la probe R4 fait foi).

### 1.3 Marquage explicite jetable — 3 endroits obligatoires, aucun optionnel

Un env n'est identifié comme jetable que si les trois marquages suivants
existent **avant** toute injection. Manque un seul = l'env n'est pas
sacrifiable au sens d'une campagne de qualification, quelle que soit
l'intention.

**a) La liste blanche des envs sacrifiables** (un tableau dans le registre
d'envs de l'équipe).
C'est le marquage qui autorise l'injection ; sans lui la règle non négociable
d'une campagne de qualification interdit d'y toucher.

```
| Env sacrifiable | Depuis | Jusqu'à | Qui l'a marqué |
|---|---|---|---|
| <ENV> | <date création> | <date fin de campagne prévue> | <utilisateur> |
```

Attention : **La décision appartient à l'utilisateur, jamais à un agent** (rappel
explicite attaché à cette liste). Un agent peut *proposer* la ligne (env
candidat, justification, date de fin envisagée) mais ne l'ajoute pas de sa
propre initiative — c'est un GATE utilisateur au même titre que le boot.
Annoncer aussi la création dans l'historique du registre.

**b) Le registre des environnements runnables**, avec
un tag explicite qui saute aux yeux à la relecture (ex. `JETABLE —
campagne qualification, à démonter le <date>`) plutôt qu'une ligne muette
indiscernable d'un env permanent. Sans ce tag, un lecteur pressé (agent ou
humain) traite l'env comme n'importe quel autre du parc et hésite à le
supprimer six mois plus tard.

**c) Un journal de campagne** (fichier versionné hors de l'env, par exemple
`campaign-journal.yaml` dans le dossier de capitalisation de la campagne) —
consigne l'identifiant d'env, la version réellement atteignable, et surtout
**le SQL rejouable des cas injectés au fil des lots**. C'est ce qui permet à
une reprise de campagne après un teardown de ré-injecter l'état plutôt que de
constater du vide et d'en tirer une conclusion fausse.

### 1.4 Gate utilisateur

Comme tout provisioning : **jamais de boot sans feu vert explicite** (ni
`gradlew run`, ni `<TOMCAT_ENV>/run.sh start`, ni script maison). Le gate de
fin de phase de préparation de la campagne couvre explicitement *aussi* « tous
les restarts nécessaires pendant la campagne » — le dire en toutes lettres
au moment de la demande de validation, pour ne pas transformer chaque
redémarrage en nouvelle interruption.

---

## 2. Vie — pendant la campagne

- Chaque lot de cas de test part en sous-agent avec un identifiant d'env
  explicite ; le contexte principal ne porte jamais les corps de réponse
  bruts, seulement les verdicts.
- Cas témoin en début et fin de lot. Si le témoin de fin casse alors qu'il
  passait au début : l'env a dérivé — le lot entier bascule `BLOCKED_ENV`,
  rien n'en est capitalisé, et c'est un signal qu'un teardown/reprovisioning
  anticipé peut être nécessaire plutôt que de continuer sur un env pollué.
- Capitalisation (résultats, journal de campagne) **au fil des
  lots**, jamais reportée à la fin — un crash à 80 % de la campagne ne doit
  rien perdre, y compris le SQL rejouable qui permettrait de reconstruire
  l'état sans l'env original.
- Ne jamais faire déborder la campagne sur un autre env du parc : le
  périmètre du gate est cet env précis, pas « un Tomcat qui traîne ».
- Aucun `action-meta-restore-all` — quel que soit l'env, ce n'est pas
  spécifique aux jetables (piège documenté sur un env de reporting) : ça pollue
  l'identité du thread pour ~10 % des requêtes de façon indétectable. Si un
  rechargement des métadonnées (bouton « Restore all… » / « Tout restaurer… » de
  Administration > Gestion des vues > Les Vues, restoreAll) a été lancé malgré tout : **redémarrer Tomcat immédiatement après,
  avant toute recette ou démonstration** — mesuré sur AOP 8.2.2, environ 1 thread
  web sur 10 reste sous l'identité admin jusqu'au redémarrage (10 réponses sur
  120 en admin après le rechargement, 0 sur 60 avant) ; lu dans le code AOP 8.2.3,
  le rechargement tourne toujours sous admin.

---

## 3. Mort — démontage de fin de campagne, avec preuve qu'il n'en reste rien

### 3.0 Avant de commencer

- Vérifier que la capitalisation est à jour : dernier lot enregistré dans le
  dossier de capitalisation de la campagne (résultats, preuves, journal), et
  que le SQL rejouable des cas injectés y est bien présent — après le
  teardown, la base n'existe plus, ce fichier est la seule trace de ce qui a
  été injecté.
- Décider si un dump de sauvegarde a de la valeur avant destruction. Par
  défaut **non** : le principe même de l'env jetable est que le SQL rejouable
  du journal suffit à reconstruire l'état utile. Ne dumper que si un verdict
  reste à trancher (ex. un `BLOCKED_ENV` à investiguer plus tard) — sinon
  c'est une donnée dormante de plus à devoir tracer.

### 3.1 Séquence d'arrêt et de suppression (ordre : processus → disque → base → git → registre)

```bash
# 1. Arrêter le Tomcat dédié (jamais un kill aveugle avant d'avoir tenté le stop propre)
<TOMCAT_ENV>/run.sh stop
<TOMCAT_ENV>/run.sh status        # doit répondre "stopped" / connexion refusée
# (sans run.sh : CATALINA_BASE=<TOMCAT_ENV> <CATALINA_HOME>/bin/catalina.sh stop,
#  puis curl sur l'URL de l'app : connexion refusée attendue)

# 2. Purger tout daemon Gradle éventuellement resté (si un ./gradlew build/run
#    a été utilisé pendant la campagne, même ponctuellement) — vérifier d'abord
#    qu'aucun AUTRE env n'a un build en cours, --stop est global à la machine
./gradlew --stop        # depuis le répertoire de l'env, ou celui du monorepo

# 3. Libérer le port si un résidu traîne (rare si run.sh stop a réussi)
fuser -k <PORT_HTTP>/tcp <PORT_SHUTDOWN>/tcp 2>/dev/null

# 4. Supprimer le CATALINA_BASE dédié
rm -rf <TOMCAT_ENV>

# 5. Supprimer l'app / le worktree applicatif
#    Cas from-scratch (app dédiée + module symlinké vers un worktree) :
rm -rf <APP_DIR>
git -C <repo-module> worktree remove <worktree-module> --force
git -C <repo-module> worktree prune
git -C <repo-module> branch -D <branche-module>

#    Cas worktree simple (Pattern A de SKILL.md) :
git -C <repo-monorepo> worktree remove .worktrees/<ENV> --force
git -C <repo-monorepo> worktree prune
git -C <repo-monorepo> branch -D <branche>

# 6. Détruire la base — vérifier zéro connexion active avant le DROP
psql -h <hote-pg> -U <role-pg> -d postgres -tAc \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='<DB>';"   # doit valoir 0
psql -h <hote-pg> -U <role-pg> -d postgres -c "DROP DATABASE <DB>;"
```

Attention : Ne **jamais** utiliser `docker compose down -v` pour « repartir propre » :
ça détruit le volume PostgreSQL du compose, donc **toutes** les bases du
parc, pas seulement `<DB>`. Le DROP ciblé est la seule opération correcte.

### 3.2 Mise à jour documentaire — dans le même geste, pas « plus tard »

```text
# Registre des envs : supprimer la ligne de <ENV> (le dossier/l'app n'existe plus)
# Liste blanche des sacrifiables : soit renseigner "Jusqu'à" = date du teardown
#   puis retirer la ligne (l'env détruit n'a plus de statut "actuellement
#   sacrifiable" à afficher), soit la retirer directement — dans les deux
#   cas la trace vit dans l'historique du registre, pas dans une table qui doit
#   rester un instantané de l'état courant.
# Historique : une entrée datée (un seul bloc) qui documente création +
#   teardown, avec renvoi vers le journal de campagne qui porte le détail et
#   la preuve.
# Fiche de l'env, si elle existe : noter le démontage (sinon elle présente
#   encore l'env comme actif).
```

Puis lancer le contrôle de cohérence de l'équipe (registre ↔ bases réellement
présentes sur le serveur ↔ ports) : il doit confirmer l'absence de dérive. Retirer
d'abord la ligne de `<ENV>` du registre, puis lancer le contrôle. Sans outil de
contrôle dans l'équipe, le faire à la main : chaque base listée par
`psql -h <hote-pg> -U <role-pg> -d postgres -lqt` (hors `postgres`, `template0`,
`template1`) correspond à une ligne du registre (et réciproquement), et aucun port du registre n'est tenu par un env
absent du registre.

Si des fichiers ont transité par une zone d'échange pendant la campagne
(exports de preuve, captures d'écran) : les nettoyer ou les supprimer
ciblément, pour ne pas laisser une trace hors du dossier de capitalisation
officiel de la campagne.

### 3.3 La preuve qu'il n'en reste rien — checklist exécutable, couche par couche

Chaque ligne doit produire une sortie **vide** (ou explicitement « non
trouvé » / connexion refusée). Coller ces sorties telles quelles dans le
journal de campagne (section teardown) : une preuve non collée n'est
qu'une affirmation.

Attention : **Le piège de la preuve creuse.** Dans une table qui prouve par sortie
vide, une commande **absente** produit exactement le même vide qu'un succès :
`command not found` part sur stderr, stdout reste vide, et la ligne se lit
« rien à signaler ». Avant de conclure, vérifier que chaque outil existe
(`command -v <outil>`) — c'est ainsi qu'on a découvert que `ss` n'était pas
installé dans le conteneur de dev de l'auteur. Une preuve dont on n'a pas
vérifié qu'elle pouvait échouer ne prouve rien.

| Couche | Commande de preuve | Résultat attendu |
|---|---|---|
| Processus applicatif | `curl -s -o /dev/null -w '%{http_code}\n' http://localhost:<PORT>/<appName>/` | connexion refusée / timeout, jamais 200 |
| Port | `fuser <PORT>/tcp` | rien (Attention : `ss` n'était PAS installé dans le conteneur de l'auteur — vérifier `command -v` avant de l'utiliser) |
| Daemons Gradle orphelins | `ps aux \| grep -i '[g]radle.*<ENV>'` | rien |
| CATALINA_BASE | `ls <TOMCAT_ENV> 2>&1` | `No such file or directory` |
| App / worktree applicatif | `ls <APP_DIR> 2>&1` (ou `.worktrees/<ENV>`) | `No such file or directory` |
| Worktree git déclaré | `git -C <repo> worktree list \| grep <ENV>` | rien |
| Branche git | `git -C <repo> branch --list '*<ENV>*'` | rien |
| Base PostgreSQL | `psql -h <hote-pg> -U <role-pg> -d postgres -lqt \| grep <DB>` | rien |
| Registre des envs | `grep -n '<ENV>' <registre>` | aucune ligne du registre courant (une entrée d'historique est normale) |
| Liste blanche | lecture de la table des sacrifiables dans le registre | `<ENV>` absent de la table active |
| Contrôle de cohérence de l'équipe | lancer le contrôle (registre ↔ bases ↔ ports), ou la comparaison manuelle du §3.2 | 0 dérive rapportée |
| Volume Docker global | *(aucune commande — c'est une non-action)* | confirmer qu'aucun `docker compose down -v` n'a été exécuté : les autres bases du parc doivent être intactes, `psql -lqt` doit encore lister les bases des autres envs vivants |

Un teardown n'est déclaré terminé que lorsque **toutes** les lignes du
tableau ont été exécutées et leur sortie collée dans le journal — pas
lorsque « ça a l'air propre ».

### 3.4 Ce que le teardown NE supprime PAS (et pourquoi)

- **Le dossier de capitalisation de la campagne (résultats, preuves, journal de
  campagne, SQL rejouable)** — c'est le livrable de la campagne, il survit à
  l'env qui l'a produit. Le teardown détruit le terrain d'expérimentation,
  jamais la connaissance qu'il a permis d'écrire.
- **L'entrée d'historique du registre d'envs** (puis son archive quand elle sort
  de la fenêtre courante) — trace permanente de l'existence et de la
  destruction de l'env, par symétrie avec toute autre opération consignée sur
  ce registre. La fiche de l'env, si elle existe, reste aussi, avec le
  démontage noté (§3.2).

---

## 4. Gabarit de rapport de démontage (à coller dans le journal de campagne)

```yaml
teardown:
  env: <ENV>
  campagne: <id campagne / lien vers campaign.md>
  date: <YYYY-MM-DD>
  decide_par: <utilisateur>
  sequence_executee:
    - tomcat_stop: <sortie run.sh stop>
    - gradle_daemons: <sortie --stop ou "aucun daemon">
    - port_libere: <sortie curl / ss>
    - catalina_base_supprime: <sortie ls>
    - app_worktree_supprime: <sortie ls>
    - worktree_git_retire: <sortie worktree list>
    - branche_supprimee: <sortie branch --list>
    - db_droppee: <sortie psql -lqt>
  documentation_mise_a_jour:
    - registre_envs: ligne retiree
    - liste_blanche_sacrifiables: ligne retiree
    - historique: ligne ajoutee
    - fiche_env: <demontage note | pas de fiche>
    - controle_coherence: 0 derive
  preuve_complete: true   # false tant qu'une ligne du tableau §3.3 manque
```
