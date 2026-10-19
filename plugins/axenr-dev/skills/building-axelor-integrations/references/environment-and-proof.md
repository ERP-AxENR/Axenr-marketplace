# Disposable environment, build loop and database proof

## Contents
1. Compile first
2. Set up the disposable environment
3. Build loop
4. Database proof
5. Hand the environment back

## 1. Compile first

Compiling against the target AOS version settles in seconds what reading estimates in days.
- Target version = the version of the **customer's application** (its `gradle.properties`), not the version of the test
  environment. A delivered module does not pin AOS module versions (`api "com.axelor.apps:axelor-base:9.1.7"` in a
  module forces 9.1.7 on an application running 9.1.6); pin them in the test application only.
- Compatible versions come from the Axelor version catalogue (a `version-matcher` MCP server if you have one; otherwise
  `gradle.properties`, `settings.gradle` and the `build.gradle` of the application, the Axelor changelog and the versions
  published on Maven), never from a guess. An EE module may pull an older AOS version transitively: `gradlew dependencies`
  shows what is resolved.
- AOS 9 / AOP 8: Java 21, AOP Gradle plugin 8.x, Gradle 8.14, `javax.*` → `jakarta.*`. EE modules come from the
  enterprise Maven repository; credentials are Gradle properties, never read or printed.
- Build with `--no-daemon`, with a bounded heap (`-Dorg.gradle.jvmargs=-Xmx1g`) when an application is running; avoid
  `gradlew --stop`, which stops every application run by Gradle on the machine.

## 2. Set up the disposable environment

Starting an environment needs the owner's go-ahead. Use the workspace's own environment tooling and inventory when it has
some. What matters for an interface:
- start from a sacrificial environment whose stack contains every module the connector depends on (check the jars in
  `WEB-INF/lib`), copy its application and **clone its database** (`CREATE DATABASE … TEMPLATE …`, no connection on the
  source); do not work on a database delivered to anyone;
- cloned EE database: back up then delete the `enterprise_app_license` row before the first start, copy the licence
  certificate (`certificate.crt` in the attachments folder) next to the new attachments folder; then check
  `app_license_status = ACTIVE`;
- **a module that extends AOS entities is not dropped into a built WAR**: the application ships its own merged entity
  classes (`WEB-INF/classes`), which win over the jar → Hibernate "mappedBy … does not exist". Publish the module
  (`publishToMavenLocal`), add it to the application dependencies, `clean war`, redeploy: `scripts/rebuild_and_deploy.sh`;
- startup errors: the useful stack trace is in `logs/localhost.<date>.log`, not only `catalina.out`; an HTTP 404 while
  Tomcat says "started" means the context failed.

## 3. Build loop (one flow at a time)

1. Unit tests first (JUnit 5; a module without tests gets the test structure) on the pure logic: mapping, grouping,
   rules, request building. Red, code, green (`scripts/junit_summary.py`).
2. Emulator updated for the flow (routes, data sets, request validation, failures).
3. Publish, rebuild, redeploy, start; configure through the REST API (`scripts/axelor_rest.py`); run the batch.
4. Check the database (`scripts/db_check.py`); read the batch summary and the error traces.
5. Fix, replay **the same scenario**; keep a baseline (the state before the change).
6. Move to the next flow only when this one is green; replay all flows at the end.

Run tests and checks with absolute paths in a single command (`python3 -I /abs/path/test_x.py`) rather than
`cd … && …`: restricted shells often allow a command by its first word only. Paste the actual output in the report.

Write configuration through the application REST API rather than SQL: it applies the same controls as the screens, and
direct SQL writes may be blocked by local guard-rails.

## 4. Database proof

"Processed = N" proves nothing. The proof is the expected AOS object read back from the database with the right values:
employee attached to the right company, leave request with the right status and dates, accounting entry on the right
accounts, line reported when its reference is missing. Each edge case of the emulator has its check. Expectations live
in a replayable JSON file (`scripts/db_check.py`), one step per scenario.

A batch says what it did not do and why (batch summary, named error per item): an item skipped silently is a defect
even when the counter is green.

## 5. Hand the environment back

Stop the application and the emulator, check that no Gradle daemon survives, record in the environment's notes what the
tests wrote into the database. Destroying the environment is the owner's call.
