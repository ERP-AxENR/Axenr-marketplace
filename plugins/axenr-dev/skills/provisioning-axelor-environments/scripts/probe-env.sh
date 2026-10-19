#!/usr/bin/env bash
# ============================================================================
# probe-env.sh — suite de probes rouge/vert pour un env Axelor
#
# Chaque probe encode UN piège documenté (voir references/from-scratch.md et la
# table « Erreurs fréquentes » de SKILL.md pour le fix détaillé de chaque piège).
# La suite se rejoue à l'identique n'importe quand : un env qui était vert
# et devient rouge a DÉRIVÉ.
#
# Usage :
#   probe-env.sh <manifest.properties> [--static] [--db] [--war [chemin.war]] [--runtime]
#   (sans option : --static seul ; --all = static+db+war+runtime)
#   probe-env.sh --help
#
# Paramètres (rien n'est en dur dans le script) :
#   - Manifest : env.dir, db.name, db.mode, app.name, runtime.url, flag.*, apps.active,
#     es.url, module.<nom> (voir references/manifest-template.properties). Clés
#     facultatives pour PostgreSQL : db.host, db.port, db.user.
#   - PostgreSQL (phase --db et probes runtime R4/R5/R6) : hôte = db.host du manifest,
#     sinon PGHOST ; utilisateur = db.user, sinon PGUSER ; port = db.port, sinon PGPORT.
#     Mot de passe : variable PGPASSWORD ou ~/.pgpass, jamais dans le manifest.
#     psql est lancé avec -w (jamais d'invite de mot de passe). Pour un PostgreSQL
#     local joint par socket Unix, PGHOST peut être le répertoire du socket
#     (ex. /var/run/postgresql).
#   - Session HTTP des probes R2/R3 : PROBE_USER et PROBE_PASSWORD, obligatoires
#     pour --runtime (aucune valeur par défaut ; sur une base neuve, le compte
#     d'origine d'Axelor est admin / admin). Saisie conseillée, dans le terminal de
#     l'utilisateur : export PROBE_USER=<login>; read -rs PROBE_PASSWORD; export PROBE_PASSWORD
#     Le mot de passe voyage par l'environnement du process et l'entrée standard de
#     curl, jamais par un argument de commande ni par un fichier.
#   - PROBE_REGISTRY_FILE : fichier texte (registre d'envs de l'équipe, noms de base
#     entre accents graves) pour la probe S8c ; sans lui, S8c est ignorée.
#   - GRADLE_USER_HOME (défaut ~/.gradle) : où chercher axelorMavenUsername (S9).
#
# Sortie : TAP-like ("ok"/"not ok" + id + message). Code retour : 0 si aucune
# probe rouge, 1 sinon ; 2 = usage incorrect.
# ============================================================================
set -u

usage() {
  sed -n '3,/^# ====/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'
}
case "${1:-}" in -h|--help) usage; exit 0 ;; esac

MANIFEST="${1:-}"
[ -f "$MANIFEST" ] || { echo "usage: probe-env.sh <manifest.properties> [--static|--db|--war [war]|--runtime|--all]  (--help pour les paramètres)" >&2; exit 2; }
shift

DO_STATIC=0; DO_DB=0; DO_WAR=0; DO_RUNTIME=0; WAR_PATH=""
while [ $# -gt 0 ]; do
  case "$1" in
    --static)  DO_STATIC=1 ;;
    --db)      DO_DB=1 ;;
    --war)     DO_WAR=1; [ $# -gt 1 ] && [[ "$2" != --* ]] && { WAR_PATH="$2"; shift; } ;;
    --runtime) DO_RUNTIME=1 ;;
    --all)     DO_STATIC=1; DO_DB=1; DO_WAR=1; DO_RUNTIME=1 ;;
    *) echo "option inconnue: $1" >&2; exit 2 ;;
  esac
  shift
done
[ $((DO_STATIC+DO_DB+DO_WAR+DO_RUNTIME)) -eq 0 ] && DO_STATIC=1

# --- lecture du manifest -----------------------------------------------------
mget() { sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$MANIFEST" | head -1; }
mkeys() { grep -o "^[[:space:]]*$1[^=[:space:]]*" "$MANIFEST" | sed 's/^[[:space:]]*//' ; }

ENV_DIR="$(mget 'env\.dir')"
DB_NAME="$(mget 'db\.name')"
DB_MODE="$(mget 'db\.mode')"
APP_NAME="$(mget 'app\.name')"
RUNTIME_URL="$(mget 'runtime\.url')"
FLAG_FE="$(mget 'flag\.facturation-electronique')"
FLAG_ES="$(mget 'flag\.elasticsearch')"
FLAG_GUARDIAN="$(mget 'flag\.guardian')"
APPS_ACTIVE="$(mget 'apps\.active')"
ES_URL="$(mget 'es\.url')"

CONFIG="$ENV_DIR/src/main/resources/axelor-config.properties"
GRADLE_PROPS="$ENV_DIR/gradle.properties"
BUILD_GRADLE="$ENV_DIR/build.gradle"

PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); echo "ok $N - $1: $2"; }
ko()  { N=$((N+1)); FAIL=$((FAIL+1)); echo "not ok $N - $1: $2"; }
skip(){ N=$((N+1)); echo "ok $N - $1: SKIP ($2)"; }

# PostgreSQL : hôte / utilisateur / port viennent du manifest (db.host, db.user, db.port)
# ou des variables libpq standard ; le mot de passe vient de PGPASSWORD ou ~/.pgpass.
PG_HOST="$(mget 'db\.host')"; [ -z "$PG_HOST" ] && PG_HOST="${PGHOST:-}"
PG_PORT="$(mget 'db\.port')"; [ -z "$PG_PORT" ] && PG_PORT="${PGPORT:-}"
PG_USER="$(mget 'db\.user')"; [ -z "$PG_USER" ] && PG_USER="${PGUSER:-}"
PG_OK=0; [ -n "$PG_HOST" ] && [ -n "$PG_USER" ] && PG_OK=1
PG_MSG="paramètres PostgreSQL absents (db.host et db.user du manifest, ou PGHOST et PGUSER ; mot de passe par PGPASSWORD ou ~/.pgpass)"
psqlx() {
  [ "$PG_OK" = 1 ] || return 0
  psql -w -h "$PG_HOST" ${PG_PORT:+-p "$PG_PORT"} -U "$PG_USER" -d "${1}" -tAc "${2}" 2>/dev/null
}

# ============================================================================
# PHASE STATIC — fichiers seuls, aucun build ni boot requis
# ============================================================================
if [ "$DO_STATIC" = 1 ]; then

  # S1 — manifest résolu : aucune valeur A-RESOUDRE, versions jamais devinées
  # (les lignes de commentaire du modèle, qui citent A-RESOUDRE, ne comptent pas)
  if grep -v '^[[:space:]]*#' "$MANIFEST" | grep -q "A-RESOUDRE"; then
    ko S1-manifest-resolu "des valeurs A-RESOUDRE subsistent (versions pas encore résolues ?)"
  else
    ok S1-manifest-resolu "toutes les clés sont résolues"
  fi

  if [ ! -d "$ENV_DIR" ]; then
    ko S0-env-dir "env.dir absent ($ENV_DIR) — env pas encore cloné (rouge attendu en début de TDD)"
  else
    ok S0-env-dir "$ENV_DIR existe"

    # S2 — pins cohérents avec le manifest.
    # Convention observée : gradle.properties porte aosVersion/aopVersion et
    # <module-sans-prefixe-axelor, camelCase>Version ; build.gradle interpole
    # (${xVersion}) ou hard-code (mod:1.2.3 — qui shadowe). On vérifie les 2.
    # Un module sans pin local (transitif) n'est PAS vérifiable ici → W1 (WAR).
    S2_BAD=""; S2_UNVERIF=""
    if [ -f "$GRADLE_PROPS" ]; then
      for pair in "aosVersion:$(mget 'target\.aos')" "aopVersion:$(mget 'target\.platform')"; do
        k="${pair%%:*}"; want="${pair#*:}"
        got=$(sed -n "s/^${k}[[:space:]]*=[[:space:]]*//p" "$GRADLE_PROPS" | head -1)
        [ -n "$got" ] && [ "$got" != "$want" ] && S2_BAD="$S2_BAD ${k}(props=${got}!=manifest=${want})"
      done
    fi
    for key in $(mkeys 'module\.'); do
      mod="${key#module.}"; want="$(mget "${key//./\\.}")"; found=0
      hard=$(grep -o "${mod}:[0-9][0-9a-zA-Z.\-]*" "$BUILD_GRADLE" 2>/dev/null | sed "s/^${mod}://" | sort -u)
      for h in $hard; do
        found=1; [ "$h" != "$want" ] && S2_BAD="$S2_BAD ${mod}(gradle=${h}!=manifest=${want})"
      done
      if [ -f "$GRADLE_PROPS" ]; then
        # axelor-business-project → businessProjectVersion
        pk=$(echo "${mod#axelor-}" | awk -F- '{o=$1; for(i=2;i<=NF;i++) o=o toupper(substr($i,1,1)) substr($i,2); print o}')Version
        pv=$(sed -n "s/^${pk}[[:space:]]*=[[:space:]]*//p" "$GRADLE_PROPS" | head -1)
        if [ -n "$pv" ]; then
          found=1; [ "$pv" != "$want" ] && S2_BAD="$S2_BAD ${mod}(${pk}=${pv}!=manifest=${want})"
        fi
      fi
      [ "$found" = 0 ] && S2_UNVERIF="$S2_UNVERIF $mod"
    done
    S2_MSG="alignés sur le manifest"
    [ -n "$S2_UNVERIF" ] && S2_MSG="$S2_MSG ; non pinnés localement (transitifs ? vérifiés par W1):$S2_UNVERIF"
    [ -z "$S2_BAD" ] && ok S2-pins-coherents "$S2_MSG" \
                     || ko S2-pins-coherents "versions divergentes:$S2_BAD"

    # S3 — tout if-module doit désigner un module RÉELLEMENT installé dans cet env.
    # Attention : un module installé n'est pas forcément un dossier de modules/ —
    # les modules AOS/EE arrivent en JAR (dépendance du build.gradle). Ne comparer
    # qu'à modules/ produit un faux positif sur, p. ex., if-module="axelor-intervention"
    # (module AOS standard, jamais présent en local). On accepte donc les deux
    # provenances : dossier local OU dépendance déclarée.
    if [ -d "$ENV_DIR/modules" ]; then
      S3_BAD=""
      for v in $(grep -rho 'if-module="[^"]*"' "$ENV_DIR"/modules/*/src/main/resources/views/ 2>/dev/null | sed 's/if-module="//;s/"//' | sort -u); do
        [ -e "$ENV_DIR/modules/$v" ] && continue
        grep -q ":${v}:" "$BUILD_GRADLE" 2>/dev/null && continue
        grep -q ":${v}:\|:${v}\"" "$BUILD_GRADLE" 2>/dev/null && continue
        S3_BAD="$S3_BAD $v"
      done
      [ -z "$S3_BAD" ] && ok S3-if-module "toutes les valeurs if-module matchent modules/" \
                       || ko S3-if-module "if-module sans module installé:$S3_BAD"
    else
      skip S3-if-module "pas de modules/ locaux"
    fi

    # S4 — excludes JAXB si facturation électronique (sinon : 0 menu + 500 partout)
    if [ "$FLAG_FE" = "true" ]; then
      if grep -q "jaxb-runtime" "$BUILD_GRADLE" 2>/dev/null && grep -q "jaxb-impl" "$BUILD_GRADLE" 2>/dev/null; then
        ok S4-jaxb-excludes "les 2 excludes (jaxb-runtime + jaxb-impl) sont posés"
      else
        ko S4-jaxb-excludes "exclude glassfish jaxb-runtime ET com.sun jaxb-impl requis (RI vs MOXy)"
      fi
    else skip S4-jaxb-excludes "flag.facturation-electronique=false"; fi

    # S5 — câblage guardian src-gen (sinon LicenseException 1050 au boot)
    if [ "$FLAG_GUARDIAN" = "true" ]; then
      grep -q "src-gen" "$BUILD_GRADLE" 2>/dev/null \
        && ok S5-guardian-srcgen "sourceSets src-gen câblé" \
        || ko S5-guardian-srcgen "sourceSets src-gen/java absent de build.gradle → 1050 au boot"
    else skip S5-guardian-srcgen "flag.guardian=false"; fi

    # S6 — bindings context.* (sinon __config__.date null → NPE différés)
    if [ -f "$CONFIG" ]; then
      S6_BAD=""
      grep -q "^context\.app" "$CONFIG" || S6_BAD="$S6_BAD context.app"
      grep -q "^context\.date" "$CONFIG" || S6_BAD="$S6_BAD context.date"
      [ -z "$S6_BAD" ] && ok S6-context-bindings "context.app + context.date présents" \
                       || ko S6-context-bindings "manquants:$S6_BAD"

      # S7 — interrupteur API AOS (sinon 403 sur tout /ws/aos/**)
      grep -Eq "^(utils|aos)\.api\.enable[[:space:]]*=[[:space:]]*true" "$CONFIG" \
        && ok S7-api-enable "utils.api.enable=true" \
        || ko S7-api-enable "utils.api.enable absent → 403 sur les micro-frontends React"

      # S8 — isolation DB : url dédiée + ddl=update + unicité dans le registre
      DBURL=$(grep "^db.default.url" "$CONFIG" | sed 's/.*=[[:space:]]*//')
      case "$DBURL" in
        */"$DB_NAME") ok S8a-db-url "db.default.url → $DB_NAME" ;;
        *) ko S8a-db-url "db.default.url=$DBURL ≠ manifest db.name=$DB_NAME" ;;
      esac
      grep -Eq "^db\.default\.ddl[[:space:]]*=[[:space:]]*update" "$CONFIG" \
        && ok S8b-ddl-update "ddl=update" \
        || ko S8b-ddl-update "ddl≠update (create wipe à chaque restart)"
      # Registre d'envs facultatif (PROBE_REGISTRY_FILE) : noms de base entre accents graves.
      if [ -n "${PROBE_REGISTRY_FILE:-}" ] && [ -f "${PROBE_REGISTRY_FILE:-}" ]; then
        OTHER=$(grep -c "\`$DB_NAME\`" "$PROBE_REGISTRY_FILE" 2>/dev/null || true)
        if [ "${OTHER:-0}" -gt 0 ] && ! grep -q "$(mget 'env\.name')" "$PROBE_REGISTRY_FILE"; then
          ko S8c-db-collision "$DB_NAME apparaît déjà dans le registre ($PROBE_REGISTRY_FILE) pour un autre env"
        else
          ok S8c-db-collision "pas de collision de DB dans le registre"
        fi
      else skip S8c-db-collision "PROBE_REGISTRY_FILE non défini ou introuvable (registre d'envs facultatif)"; fi

      # S13 — Elasticsearch : l'interrupteur exact + les clés de tuning que le
      # code lit vraiment (la doc livrée écrit global-search.* → ignoré en silence).
      # cf. references/elasticsearch.md
      if [ "$FLAG_ES" = "true" ]; then
        S13_BAD=""
        grep -Eq "^hibernate\.search\.backend\.type[[:space:]]*=[[:space:]]*elasticsearch" "$CONFIG" \
          || S13_BAD="$S13_BAD hibernate.search.backend.type≠elasticsearch(seule valeur acceptée)"
        grep -q "^hibernate\.search\.backend\.hosts" "$CONFIG" || S13_BAD="$S13_BAD hosts-absent"
        # interrupteur natif Hibernate Search, EN AMONT du backend AEP : a false,
        # il eteint tout, quel que soit backend.type (piege herite du donneur)
        grep -Eq "^hibernate\.search\.enabled[[:space:]]*=[[:space:]]*false" "$CONFIG" \
          && S13_BAD="$S13_BAD hibernate.search.enabled=false(eteint HS en amont)"
        # mapping : propriété OU ressource axelor-search.yaml — sinon index VIDE
        if ! grep -q "^global\.search\.mapping\.file" "$CONFIG" \
           && [ -z "$(find "$ENV_DIR" -name axelor-search.yaml -not -path '*/build/*' 2>/dev/null)" ]; then
          S13_BAD="$S13_BAD mapping-absent(index vide silencieux)"
        fi
        # clés de la doc, silencieusement ignorées par le code
        grep -q "^global-search\." "$CONFIG" && S13_BAD="$S13_BAD clés-global-search.*-de-la-doc(le code lit global.search.*)"
        [ -z "$S13_BAD" ] && ok S13-es-config "interrupteur + hosts + mapping présents" \
                          || ko S13-es-config "$S13_BAD"
      else skip S13-es-config "flag.elasticsearch=false"; fi

      # S12 — pas de re-seed démo AOS non voulu
      grep -Eq "^data\.import\.demo-data[[:space:]]*=[[:space:]]*false" "$CONFIG" \
        && ok S12-demo-data "data.import.demo-data=false" \
        || ko S12-demo-data "demo-data≠false → risque de re-seed AOS non voulu"
    else
      ko S6-context-bindings "axelor-config.properties introuvable ($CONFIG)"
    fi

    # S11 — appName = manifest (le context path EN DÉCOULE ; piège 404 racine)
    if [ -f "$GRADLE_PROPS" ]; then
      AN=$(grep -E "^appName" "$GRADLE_PROPS" | sed 's/.*=[[:space:]]*//')
      [ "$AN" = "$APP_NAME" ] && ok S11-appname "appName=$AN (URL: /$AN)" \
                              || ko S11-appname "appName=$AN ≠ manifest app.name=$APP_NAME"
    else
      ko S11-appname "gradle.properties introuvable"
    fi
  fi

  # S9 — creds Nexus (sans eux : résolution EE échoue)
  GRADLE_HOME_DIR="${GRADLE_USER_HOME:-$HOME/.gradle}"
  if grep -q "axelorMavenUsername" "$GRADLE_HOME_DIR/gradle.properties" 2>/dev/null \
     || [ -n "${ORG_GRADLE_PROJECT_axelorMavenUsername:-}" ]; then
    ok S9-nexus-creds "creds Nexus présents ($GRADLE_HOME_DIR/gradle.properties ou ORG_GRADLE_PROJECT_axelorMavenUsername)"
  else
    ko S9-nexus-creds "axelorMavenUsername absent de $GRADLE_HOME_DIR/gradle.properties et de ORG_GRADLE_PROJECT_axelorMavenUsername"
  fi
fi

# ============================================================================
# PHASE DB — la base, avant premier boot (et rejouable après)
# ============================================================================
if [ "$DO_DB" = 1 ]; then
  EXISTS=""
  if [ "$PG_OK" != 1 ]; then
    ko D1-db-exists "$PG_MSG"
  elif [ "$(psqlx postgres 'SELECT 1;')" != "1" ]; then
    ko D1-db-exists "connexion PostgreSQL impossible ($PG_HOST, utilisateur $PG_USER) : hôte, utilisateur ou mot de passe (PGPASSWORD / ~/.pgpass) ?"
  else
    EXISTS=$(psqlx postgres "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';")
    [ "$EXISTS" = "1" ] && ok D1-db-exists "base $DB_NAME présente" \
                        || ko D1-db-exists "base $DB_NAME absente (CREATE DATABASE ... OWNER <role-pg>)"
  fi

  # D2 — préventif licence 1020 : sur un CLONE, la ligne enterprise_app_license
  # héritée collisionne au boot (INSERT pas upsert) → à purger AVANT 1er boot.
  if [ "$EXISTS" = "1" ] && [ "$DB_MODE" = "clone" ]; then
    LIC=$(psqlx "$DB_NAME" "SELECT count(*) FROM enterprise_app_license;")
    BOOTED=$(psqlx "$DB_NAME" "SELECT count(*) FROM meta_module;" )
    if [ "${BOOTED:-0}" -gt 0 ]; then
      skip D2-licence-preventif "env déjà booté — voir R4 pour l'état de la licence"
    elif [ "${LIC:-0}" -gt 0 ]; then
      ko D2-licence-preventif "$LIC ligne(s) enterprise_app_license héritées → 1020 à chaque save. pg_dump la table puis DELETE avant 1er boot"
    else
      ok D2-licence-preventif "aucune ligne licence héritée"
    fi
  else
    skip D2-licence-preventif "db.mode=fresh ou base absente"
  fi
fi

# ============================================================================
# PHASE WAR — après ./gradlew build, avant tout boot
# ============================================================================
if [ "$DO_WAR" = 1 ]; then
  [ -z "$WAR_PATH" ] && WAR_PATH=$(ls -t "$ENV_DIR"/build/libs/*.war 2>/dev/null | head -1)
  if [ -z "$WAR_PATH" ] || [ ! -f "$WAR_PATH" ]; then
    ko W0-war "aucun WAR trouvé (build pas fait ? passer --war <chemin>)"
  else
    ok W0-war "$WAR_PATH"
    LIBLIST=$(unzip -l "$WAR_PATH" | grep "WEB-INF/lib/")

    # W1 — chaque module du manifest est DANS le WAR à la bonne version
    W1_BAD=""
    for key in $(mkeys 'module\.'); do
      mod="${key#module.}"; want="$(mget "${key//./\\.}")"
      echo "$LIBLIST" | grep -q "${mod}-${want}\.jar" || W1_BAD="$W1_BAD ${mod}-${want}"
    done
    [ -z "$W1_BAD" ] && ok W1-jars-manifest "tous les modules du manifest sont embarqués" \
                     || ko W1-jars-manifest "absents du WAR:$W1_BAD"

    # W2 — Groovy 4 seul (Groovy 3 fuité = MissingPropertyException .size)
    if echo "$LIBLIST" | grep -q "groovy-3"; then
      ko W2-groovy4-only "groovy-3.x dans le WAR"
    else
      ok W2-groovy4-only "pas de Groovy 3 embarqué"
    fi

    # W3 — RI JAXB absente si facturation électronique (MOXy doit gagner)
    if [ "$FLAG_FE" = "true" ]; then
      W3_BAD=""
      echo "$LIBLIST" | grep -q "jaxb-runtime" && W3_BAD="$W3_BAD jaxb-runtime"
      echo "$LIBLIST" | grep -q "jaxb-impl"    && W3_BAD="$W3_BAD jaxb-impl"
      echo "$LIBLIST" | grep -q "moxy"         || W3_BAD="$W3_BAD (moxy-absent!)"
      [ -z "$W3_BAD" ] && ok W3-jaxb-moxy "RI Glassfish exclue, MOXy présent" \
                       || ko W3-jaxb-moxy "problème JAXB:$W3_BAD → 0 menu + 500 sur toute fiche"
    else skip W3-jaxb-moxy "flag.facturation-electronique=false"; fi

    # W4 — jars hibernate-search/ES si elasticsearch demandé
    if [ "$FLAG_ES" = "true" ]; then
      echo "$LIBLIST" | grep -q "hibernate-search-backend-elasticsearch" \
        && ok W4-es-jars "hibernate-search-backend-elasticsearch embarqué" \
        || ko W4-es-jars "backend ES absent du WAR (plateforme EE requise)"
    else skip W4-es-jars "flag.elasticsearch=false"; fi
  fi
fi

# ============================================================================
# PHASE RUNTIME — après boot (GATE utilisateur obligatoire avant tout boot)
# ============================================================================
if [ "$DO_RUNTIME" = 1 ]; then
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$RUNTIME_URL/" 2>/dev/null)
  case "$CODE" in
    200|302) ok R1-http "HTTP $CODE sur $RUNTIME_URL/" ;;
    *)       ko R1-http "HTTP $CODE sur $RUNTIME_URL/ (ss/netstat ne font pas foi, curl si)" ;;
  esac

  # login (PROBE_USER / PROBE_PASSWORD) → cookie (un boot vert ne prouve RIEN : tester menu/all et meta/view)
  # Le JSON de login est produit par python3 (échappement correct) et passé à curl par
  # l'entrée standard : le mot de passe n'apparaît dans aucun argument de commande.
  if [ -z "${PROBE_USER:-}" ] || [ -z "${PROBE_PASSWORD:-}" ]; then
    LOGIN_MSG="PROBE_USER et PROBE_PASSWORD non définis (aucune valeur par défaut ; voir --help) : session impossible"
    ko R2-menus "$LOGIN_MSG"
    ko R3-meta-view "$LOGIN_MSG"
  else
  CJ=$(mktemp)
  python3 -c 'import json,os;print(json.dumps({"username":os.environ["PROBE_USER"],"password":os.environ["PROBE_PASSWORD"]}))' 2>/dev/null \
    | curl -s -c "$CJ" -o /dev/null -H 'Content-Type: application/json' \
           -d @- "$RUNTIME_URL/callback" 2>/dev/null
  MENUS=$(curl -s -b "$CJ" "$RUNTIME_URL/ws/action/menu/all" 2>/dev/null \
          | python3 -c "import json,sys;d=json.load(sys.stdin);print(len(d.get('data') or []))" 2>/dev/null)
  if [ -n "${MENUS:-}" ] && [ "${MENUS:-0}" -gt 0 ]; then
    ok R2-menus "$MENUS menus servis"
  else
    ko R2-menus "0 menu ou réponse illisible — app morte malgré boot vert (JAXB ? login ?)"
  fi
  VIEW=$(curl -s -b "$CJ" -X POST "$RUNTIME_URL/ws/meta/view" -H 'Content-Type: application/json' \
         -d '{"model":"com.axelor.auth.db.User","data":{"type":"form","name":"user-form"}}' 2>/dev/null \
         | python3 -c "import json,sys;print(json.load(sys.stdin).get('status'))" 2>/dev/null)
  [ "$VIEW" = "0" ] && ok R3-meta-view "user-form servi (status 0)" \
                    || ko R3-meta-view "status=$VIEW sur /ws/meta/view (status -1 = métas cassées)"
  rm -f "$CJ"
  fi

  # R4 — licence EE active (fresh : upload UI par l'utilisateur APRÈS 1er boot)
  if [ "$FLAG_GUARDIAN" = "true" ]; then
    if [ "$PG_OK" != 1 ]; then ko R4-licence "$PG_MSG"; else
      LSTATUS=$(psqlx "$DB_NAME" "SELECT app_license_status FROM enterprise_app_license LIMIT 1;")
      [ "$LSTATUS" = "ACTIVE" ] && ok R4-licence "app_license_status=ACTIVE" \
        || ko R4-licence "licence=$LSTATUS (fresh: upload via UI requis ; clone: cf. préventif 1020)"
    fi
  else skip R4-licence "flag.guardian=false"; fi

  # R5 — apps framework activées = manifest (une base vierge n'active RIEN)
  if [ -n "$APPS_ACTIVE" ]; then
    if [ "$PG_OK" != 1 ]; then ko R5-apps-actives "$PG_MSG"; else
      R5_BAD=""
      for a in $(echo "$APPS_ACTIVE" | tr ',' ' '); do
        ACT=$(psqlx "$DB_NAME" "SELECT active FROM studio_app WHERE code='$a';")
        [ "$ACT" = "t" ] || R5_BAD="$R5_BAD $a(${ACT:-absente})"
      done
      [ -z "$R5_BAD" ] && ok R5-apps-actives "toutes les apps du manifest sont actives" \
                       || ko R5-apps-actives "apps non actives:$R5_BAD (install UI = config posée ; seed SQL = config à compléter)"
    fi
  else skip R5-apps-actives "apps.active vide"; fi

  # R6 — modules du manifest présents dans meta_module (métas réellement chargées)
  if [ "$PG_OK" != 1 ]; then ko R6-meta-modules "$PG_MSG"; else
    R6_BAD=""
    for key in $(mkeys 'module\.'); do
      mod="${key#module.}"
      INMETA=$(psqlx "$DB_NAME" "SELECT count(*) FROM meta_module WHERE name='$mod';")
      [ "${INMETA:-0}" -ge 1 ] || R6_BAD="$R6_BAD $mod"
    done
    [ -z "$R6_BAD" ] && ok R6-meta-modules "tous les modules du manifest sont dans meta_module" \
                     || ko R6-meta-modules "absents de meta_module:$R6_BAD (JAR présent ≠ métas chargées)"
  fi

  # R7 — Elasticsearch joignable si demandé
  if [ "$FLAG_ES" = "true" ]; then
    if [ -n "$ES_URL" ]; then
      ESC=$(curl -s -o /dev/null -w "%{http_code}" "$ES_URL" 2>/dev/null)
      [ "$ESC" = "200" ] && ok R7-es-ping "ES répond sur $ES_URL" \
                         || ko R7-es-ping "ES injoignable ($ESC) sur $ES_URL"
    else
      ko R7-es-ping "es.url absent du manifest alors que flag.elasticsearch=true"
    fi
  else skip R7-es-ping "flag.elasticsearch=false"; fi
fi

echo "# ---------------------------------------------"
echo "# $PASS ok / $FAIL rouges sur $N probes"
exit $([ "$FAIL" -gt 0 ] && echo 1 || echo 0)
