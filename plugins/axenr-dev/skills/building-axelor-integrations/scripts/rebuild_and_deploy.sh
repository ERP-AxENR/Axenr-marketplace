#!/bin/bash
# Publish a module, rebuild the app that embeds it, redeploy it unpacked into a standalone Tomcat env.
#
#   rebuild_and_deploy.sh --module <dir> --app <dir> --tomcat <dir> --context <name> \
#       --config <saved axelor-config.properties> [--war <file>] [--skip-build] [--dry-run]
#
# Why each step:
#  - a module that extends an AOS entity cannot be dropped into an already built WAR: the app ships
#    its own merged entity classes (WEB-INF/classes) that win over the jar -> Hibernate "mappedBy ...
#    does not exist". Publish the module (mavenLocal) and rebuild the app with it as a dependency.
#  - the app is built with "clean": without it the app code generation can stay UP-TO-DATE when only
#    the module jar changed, and an entity extended only by the module is not regenerated.
#  - never build while the app runs (shared memory), never put a .war in webapps/, never gradlew --stop
#    (it kills every app run by Gradle on the machine).
#  - the env config is restored after unpacking (the WAR carries the donor app config).
set -euo pipefail
MODULE= APP= TOMCAT= CONTEXT= CONFIG= WAR= SKIP_BUILD=0 DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --module) MODULE=$2; shift 2 ;; --app) APP=$2; shift 2 ;; --tomcat) TOMCAT=$2; shift 2 ;;
    --context) CONTEXT=$2; shift 2 ;; --config) CONFIG=$2; shift 2 ;; --war) WAR=$2; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;; --dry-run) DRY=1; shift ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown option $1 (see --help)"; exit 2 ;;
  esac
done
for v in APP TOMCAT CONTEXT CONFIG; do [ -n "${!v}" ] || { echo "X --$(printf %s "$v" | tr "[:upper:]" "[:lower:]") is required"; exit 2; }; done
[ "$SKIP_BUILD" = 1 ] || [ -n "$MODULE" ] || { echo "X --module is required unless --skip-build"; exit 2; }
: "${JAVA_HOME:?set JAVA_HOME to a Java 21 JDK (AOP 8 / AOS 9 build with Java 21)}"
export JAVA_HOME
WEBAPP=$TOMCAT/webapps/$CONTEXT
run() { if [ "$DRY" = 1 ]; then echo "  [dry-run] $*"; else eval "$@"; fi; }
stamp() { date -u '+%H:%M:%SZ'; }

if pgrep -f "catalina.base=$TOMCAT" >/dev/null; then
  echo "X the app of $TOMCAT is running: stop it first"; exit 1
fi
[ -f "$CONFIG" ] || { echo "X saved env config not found: $CONFIG"; exit 1; }

if [ "$SKIP_BUILD" != 1 ]; then
  echo "$(stamp) publish module ($MODULE)"
  run "(cd '$MODULE' && ./gradlew publishToMavenLocal --no-daemon -q)"
  echo "$(stamp) rebuild app ($APP, clean war)"
  run "(cd '$APP' && ./gradlew clean war --no-daemon -q)"
fi
[ -n "$WAR" ] || WAR=$(ls -t "$APP"/build/libs/*.war 2>/dev/null | head -1 || true)
[ "$DRY" = 1 ] || [ -f "$WAR" ] || { echo "X no WAR in $APP/build/libs"; exit 1; }
echo "$(stamp) deploy ${WAR:-<war>} -> $WEBAPP (previous kept in $TOMCAT/webapps.prev)"
run "rm -rf '$TOMCAT/webapps.prev' && mkdir -p '$TOMCAT/webapps.prev'"
run "[ ! -d '$WEBAPP' ] || mv '$WEBAPP' '$TOMCAT/webapps.prev/$CONTEXT'"
run "mkdir -p '$WEBAPP' && (cd '$WEBAPP' && unzip -q '$WAR')"
run "cp '$CONFIG' '$WEBAPP/WEB-INF/classes/axelor-config.properties'"
run "rm -rf '$TOMCAT/work/Catalina/localhost/$CONTEXT'"
if pgrep -f "[G]radleDaemon" >/dev/null; then echo "! a Gradle daemon is still alive (memory): find it with pgrep -fa GradleDaemon"; fi
echo "$(stamp) done; start the env, then read logs/localhost.<date>.log as well as catalina.out"
