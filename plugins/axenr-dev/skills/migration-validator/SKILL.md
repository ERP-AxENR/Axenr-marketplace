---
name: migration-validator
description: Validates migration scripts, data-init files, and AOS upgrade compatibility. Detects breaking changes between AOS versions by analyzing Axelor git repositories and signature diffs.
---

# Migration Validator

> Validates migration scripts, data-init files, and AOS upgrade compatibility. Detects breaking changes between AOS versions by analyzing the Axelor git repositories.

## ROLE

Analyze migration scripts, data-init files, and schema changes to ensure they are safe, idempotent, versioned, and compatible with AOS upgrades. This skill is the guardian of smooth version transitions for AxENR.

The fundamental problem: AxENR extends AOS. When AOS upgrades, schema changes, API modifications, and data migrations can break AxENR customizations. This skill prevents that by:
1. Validating the quality of AxENR migration scripts
2. Detecting AOS breaking changes BEFORE they hit production
3. Ensuring every migration has a rollback strategy

## INPUTS

| Input | Format |
|-------|--------|
| files_to_check | List of file paths (SQL scripts, data-init XML, changelog MD) |
| migration_context | Description of the migration (version upgrade, schema change, data fix) |
| source_version | Current AOS/AOP version (from libs.versions.toml) |
| target_version | Target AOS/AOP version (if upgrading) |
| project_path | Path to the axenr-app project |
| aos_repo_path | Path to the AOS reference repository (via /axelor:setup) |
| lessons_file_path | Path to LESSONS-LEARNED.md |

## OUTPUTS

| Output | Format |
|--------|--------|
| violations | List of `{severity, rule, file, line, message, fix, doc_ref}` |
| breaking_changes | List of AOS changes affecting AxENR (if upgrade context) |
| compatibility_report | Compatibility analysis between source and target versions |
| score | Migration safety score 0-100 |
| summary | Human-readable summary |

## SEVERITY LEVELS

| Level | Description |
|-------|-------------|
| CRITICAL | Data loss risk. Non-idempotent script. AOS breaking change not handled. |
| HIGH | No rollback. Missing changelog. Schema conflict with AOS. |
| MEDIUM | Script ordering issue. Naming convention violation. Missing comment. |
| LOW | Style suggestion. Could be optimized. |

---

## CATEGORY 1: SCRIPT QUALITY

### Rules

```
MIG-01: IDEMPOTENT SCRIPTS (CRITICAL)
  Every migration script MUST be idempotent (safe to run multiple times).

  BAD:
  ALTER TABLE axenr_installation ADD COLUMN power_kwc DECIMAL(20,2);
  -- Fails on second run: column already exists

  GOOD:
  DO $$
  BEGIN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'axenr_installation' AND column_name = 'power_kwc'
    ) THEN
      ALTER TABLE axenr_installation ADD COLUMN power_kwc DECIMAL(20,2);
    END IF;
  END $$;

  Idempotent patterns to check:
  - ADD COLUMN → IF NOT EXISTS guard
  - DROP COLUMN → IF EXISTS guard
  - CREATE TABLE → IF NOT EXISTS
  - CREATE INDEX → IF NOT EXISTS
  - INSERT → ON CONFLICT DO NOTHING / WHERE NOT EXISTS
  - UPDATE → idempotent by nature (same value applied)
  - DELETE → idempotent by nature (already gone)

  Non-idempotent red flags:
  - ALTER TABLE ADD without IF NOT EXISTS
  - ALTER TABLE RENAME without guard
  - CREATE TABLE without IF NOT EXISTS
  - INSERT without conflict handling

MIG-02: NO DIRECT DML ON AOS TABLES (CRITICAL)
  Migration scripts MUST NOT directly INSERT/UPDATE/DELETE data in AOS core tables.
  Use Axelor data-init or API calls instead.

  BAD:
  UPDATE sale_order SET custom_field = 'value' WHERE id = 1;
  INSERT INTO meta_menu (name, title) VALUES ('axenr-menu', 'AxENR');
  DELETE FROM meta_action WHERE name = 'action-old';

  GOOD:
  -- Only modify AxENR tables
  UPDATE axenr_installation SET status_select = 2 WHERE status_select = 1;
  -- For AOS tables, use data-init XML:
  <input file="data/axenr-menus.xml" />

  Exception: SELECT on AOS tables is always OK (read-only).

MIG-03: ROLLBACK SCRIPT (HIGH)
  Every migration script (.sql) MUST have a corresponding rollback script.
  Naming convention: if migration is V1.2.0__add_power_field.sql
  → rollback is R1.2.0__add_power_field.sql

  BAD:
  migrations/
    V1.2.0__add_power_field.sql
    (no rollback)

  GOOD:
  migrations/
    V1.2.0__add_power_field.sql
    R1.2.0__add_power_field.sql

  Rollback script requirements:
  - MUST undo the migration completely
  - MUST be idempotent (same as MIG-01)
  - MUST NOT lose data if possible (save to temp table before drop)

MIG-04: CHANGELOG ENTRY (HIGH)
  Every schema change MUST be documented in the module's CHANGELOG.md.

  BAD:
  (migration script created but no changelog entry)

  GOOD:
  ## [1.2.0] - 2026-02-16
  ### Changed
  - Added `powerKwc` field to `AxenrInstallation` entity
  - Migration: V1.2.0__add_power_field.sql

  Changelog format:
  - Follow Keep a Changelog (https://keepachangelog.com/)
  - Sections: Added, Changed, Deprecated, Removed, Fixed, Security
  - Each entry references the migration script

MIG-05: VERSION ORDERING (HIGH)
  Migration scripts MUST follow strict version ordering.
  Format: V<major>.<minor>.<patch>__<description>.sql

  BAD:
  V1__initial.sql
  V2__add_field.sql
  (no semantic versioning)

  GOOD:
  V1.0.0__initial_schema.sql
  V1.1.0__add_installation_fields.sql
  V1.1.1__fix_null_constraint.sql
  V1.2.0__add_power_field.sql

  Rules:
  - Version numbers MUST match project version in gradle.properties
  - No gaps in version sequence
  - Patch versions for fixes, minor for features, major for breaking changes

MIG-06: TRANSACTION WRAPPING (MEDIUM)
  Complex migration scripts SHOULD be wrapped in a transaction.

  BAD:
  ALTER TABLE t1 ADD COLUMN c1 INT;
  ALTER TABLE t1 ADD COLUMN c2 INT;
  UPDATE t1 SET c2 = c1 * 2;
  -- If UPDATE fails, c1 and c2 are added but c2 has no data

  GOOD:
  BEGIN;
    ALTER TABLE t1 ADD COLUMN c1 INT;
    ALTER TABLE t1 ADD COLUMN c2 INT;
    UPDATE t1 SET c2 = c1 * 2;
  COMMIT;

  Note: DDL in PostgreSQL IS transactional (unlike MySQL).

MIG-07: NO HARDCODED IDS (MEDIUM)
  Migration scripts MUST NOT reference hardcoded database IDs.
  Use lookups by code/name instead.

  BAD:
  UPDATE axenr_config SET company_id = 1;
  INSERT INTO axenr_mapping (product_id) VALUES (42);

  GOOD:
  UPDATE axenr_config SET company_id = (
    SELECT id FROM base_company WHERE code = 'AXENR'
  );

MIG-08: ENCODING AND FORMAT (LOW)
  - SQL files MUST be UTF-8 encoded
  - Line endings MUST be LF (Unix), not CRLF
  - File MUST end with a newline
  - SQL keywords SHOULD be UPPERCASE
```

---

## CATEGORY 2: DATA-INIT VALIDATION

### Rules

```
MIG-10: DATA-INIT STRUCTURE (HIGH)
  Data-init files MUST follow Axelor conventions:
  - Located in src/main/resources/data-init/
  - Referenced in application.properties or module config
  - Input files ordered: base data first, then dependent data

  GOOD structure:
  data-init/
    input/
      axenr-config.xml         (1: configuration)
      axenr-sequences.xml      (2: sequences)
      axenr-menus.xml          (3: menus, after sequences)
      axenr-demo-data.xml      (4: demo data, last)
    input-config.xml           (orchestrator)

MIG-11: DATA-INIT IDEMPOTENT (HIGH)
  Data-init XML MUST use search attributes to avoid duplicates.

  BAD:
  <input file="data/axenr-config.xml"/>
  <!-- Inside axenr-config.xml: -->
  <bind node="AxenrConfig">
    <bind node="code" field="code"/>
    <bind node="name" field="name"/>
  </bind>
  <!-- No search → creates duplicate on each import -->

  GOOD:
  <bind node="AxenrConfig" search="self.code = :code">
    <bind node="code" field="code"/>
    <bind node="name" field="name" update="true"/>
  </bind>
  <!-- search= makes it idempotent: update if exists, create if not -->

MIG-12: DATA-INIT NO AOS OVERRIDE (CRITICAL)
  Data-init files MUST NOT override AOS standard data.
  Only ADD new data or UPDATE AxENR-specific fields on AOS records.

  BAD:
  <!-- Overwriting AOS menu structure -->
  <bind node="MetaMenu" search="self.name = :name">
    <bind node="name" field="name" eval="'sale-order-menu'"/>
    <bind node="title" field="title" eval="'Custom Title'"/>
    <bind node="order" field="order" eval="5"/>
  </bind>

  GOOD:
  <!-- Adding AxENR menu under AOS menu -->
  <bind node="MetaMenu" search="self.name = :name" update="false">
    <bind node="name" field="name" eval="'axenr-installation-menu'"/>
    <bind node="title" field="title" eval="'Installations'"/>
    <bind node="parent" field="parent" search="self.name = 'project-menu'" />
  </bind>

MIG-13: SEQUENCE DEFINITION (MEDIUM)
  AxENR sequences MUST be defined in a dedicated data-init file.
  Never modify AOS sequences. Create AxENR-specific sequences.

  GOOD:
  <!-- data-init/input/axenr-sequences.xml -->
  <bind node="MetaSequence" search="self.name = :name" update="false">
    <bind node="name" field="name" eval="'axenrInstallation'"/>
    <bind node="prefix" field="prefix" eval="'INST'"/>
    <bind node="padding" field="padding" eval="6"/>
  </bind>

  Rules:
  - Sequence name MUST start with 'axenr' prefix
  - Prefix MUST be unique (not conflicting with AOS sequences)
  - File MUST be named axenr-sequences.xml
  - MUST use search="self.name = :name" for idempotency
  - MUST use update="false" to not overwrite if already exists
```

---

## CATEGORY 3: AOS UPGRADE COMPATIBILITY

### Principle

When upgrading AOS versions, this skill analyzes the AOS git repository to detect breaking changes that affect AxENR. It compares the source version (current) with the target version to find:
- Renamed/removed entities and fields
- Changed API signatures
- Modified domain models
- Removed or renamed views/actions
- Changed selection values

### AOS Git Analysis Process

```
STEP 1: LOCATE AOS REPOSITORY
  1. Check if /axelor:setup has been run → .axelor/ directory exists
  2. If available, use local repos:
     - .axelor/axelor-open-suite/ (AOS modules)
     - .axelor/axelor-open-platform/ (AOP framework)
  3. If not available → WARN and skip AOS analysis (report it)

STEP 2: IDENTIFY VERSION TAGS
  1. Read source_version from libs.versions.toml (current)
  2. Read target_version from user input (upgrade target)
  3. In AOS repo: git tag -l "v${source_version}" and git tag -l "v${target_version}"
  4. If tags not found, try without 'v' prefix

STEP 3: DIFF BETWEEN VERSIONS
  For each AOS module used by AxENR:

  3a. DOMAIN CHANGES:
      git diff v${source}..v${target} -- */src/main/resources/domains/*.xml

      Detect:
      - REMOVED fields (field existed in source, gone in target)
      - RENAMED fields (field name changed)
      - TYPE CHANGES (field type changed: string→integer, etc.)
      - REMOVED entities (entire entity deleted)
      - CHANGED relations (M2O→O2M, ref package changed)
      - NEW required fields (may break existing data)

  3b. VIEW CHANGES:
      git diff v${source}..v${target} -- */src/main/resources/views/*.xml

      Detect:
      - REMOVED elements (panel, button, field that AxENR extends)
      - RENAMED elements (name attribute changed → AxENR XPath breaks)
      - CHANGED view structure (element moved to different parent)
      - REMOVED actions referenced by AxENR

  3c. JAVA API CHANGES:
      git diff v${source}..v${target} -- */src/main/java/**/*.java

      Detect:
      - REMOVED methods (method AxENR calls no longer exists)
      - CHANGED signatures (parameters added/removed/retyped)
      - REMOVED classes/interfaces
      - CHANGED package (class moved)
      - DEPRECATED methods (annotated @Deprecated in target)
      - NEW abstract methods (AxENR implementations must add them)

  3d. SELECTION CHANGES:
      git diff v${source}..v${target} -- */src/main/resources/domains/*.xml
      Focus on <selection> elements

      Detect:
      - REMOVED options (value AxENR uses no longer exists)
      - CHANGED values (option value number changed)
      - RENAMED selections (selection name changed)

STEP 4: CROSS-REFERENCE WITH AXENR
  For each detected AOS change:

  1. Search AxENR codebase for references to the changed element:
     - grep for field names in AxENR domains, views, Java
     - grep for class names in AxENR Java imports
     - grep for view element names in AxENR view extensions
     - grep for action names in AxENR XML
     - grep for selection names in AxENR domains

  2. IF AxENR references the changed element → BREAKING CHANGE
  3. IF AxENR does NOT reference it → SAFE (no impact)

STEP 5: GENERATE COMPATIBILITY REPORT
  For each breaking change found:

  {
    severity: CRITICAL | HIGH | MEDIUM,
    aos_module: "axelor-sale",
    change_type: "REMOVED_FIELD" | "RENAMED_FIELD" | "CHANGED_SIGNATURE" | ...,
    aos_file: "SaleOrder.xml",
    aos_element: "field customField",
    aos_source_version: "8.5.11",
    aos_target_version: "8.6.0",
    axenr_files_affected: ["axenr-sale-order.xml:15", "SaleOrderServiceAxenrImpl.java:42"],
    description: "Field 'customField' removed from SaleOrder in AOS 8.6.0",
    migration_action: "Remove reference, migrate data to new field 'replacementField'",
    migration_script_needed: true,
    doc_ref: "MIG-AOS-FIELD-REMOVED"
  }
```

### Breaking Change Rules

```
MIG-20: FIELD REMOVAL HANDLING (CRITICAL)
  When AOS removes a field that AxENR references:
  1. AxENR domain extensions referencing this field MUST be updated
  2. AxENR views referencing this field MUST be updated
  3. AxENR Java code using the getter/setter MUST be updated
  4. A data migration script MUST handle existing data

MIG-21: FIELD RENAME HANDLING (CRITICAL)
  When AOS renames a field that AxENR references:
  1. All AxENR references MUST use the new name
  2. A data migration script MUST move data: old column → new column
  3. Views using the old field name MUST be updated

MIG-22: API SIGNATURE CHANGE (CRITICAL)
  When AOS changes a method signature that AxENR overrides:
  1. AxENR override MUST match the new signature
  2. Callers in AxENR MUST pass the new parameters
  3. If the change is in an interface → AxENR implementation MUST adapt

MIG-23: VIEW ELEMENT RENAME (HIGH)
  When AOS renames a view element (name attribute) that AxENR extends:
  1. AxENR <extend target="..."> XPath MUST use the new name
  2. Test that the extension still works after the rename

MIG-24: ENTITY REMOVAL (CRITICAL)
  When AOS removes an entire entity that AxENR references:
  1. All imports in AxENR Java MUST be removed/replaced
  2. All relations pointing to this entity MUST be updated
  3. All views for this entity MUST be migrated
  4. Data migration: move data to replacement entity or archive

MIG-25: SELECTION VALUE CHANGE (HIGH)
  When AOS changes selection option values:
  1. AxENR constants using old values MUST be updated
  2. Data migration: UPDATE records with old value → new value
  3. AxENR domain filters using old values MUST be updated

MIG-26: NEW REQUIRED FIELD (MEDIUM)
  When AOS adds a required field to an entity AxENR uses:
  1. Data migration: populate the new field for existing records
  2. AxENR forms SHOULD display the new field
  3. AxENR services creating this entity MUST set the new field

MIG-27: DEPRECATED API USAGE (MEDIUM)
  When AOS deprecates an API that AxENR uses:
  1. Plan migration to the replacement API
  2. Log a WARNING (not blocking, but tracked)
  3. Create a ticket for future migration before removal
```

---

## CATEGORY 4: AXENR SCHEMA MIGRATION PATTERNS

### Approved Patterns

```
PATTERN 1: ADD FIELD TO AXENR ENTITY
  1. Add field in domain XML (AxENR entity)
  2. Run ./gradlew generateCode → Hibernate auto-creates column
  3. If default value needed for existing data:
     → Create V<version>__add_<field>_default.sql
     → Set default: UPDATE axenr_<table> SET <field> = <default> WHERE <field> IS NULL;
  4. Add to changelog
  5. Create rollback script (optional for ADD, column can stay)

PATTERN 2: ADD FIELD TO AOS ENTITY (via track/extension)
  1. Create AxENR domain extending AOS entity (attrs or track field)
  2. Run ./gradlew generateCode
  3. NO SQL migration needed (Hibernate handles it)
  4. Data-init if default values needed
  5. Add to changelog

PATTERN 3: RENAME FIELD IN AXENR ENTITY
  NEVER rename directly. Instead:
  1. Add new field with correct name
  2. Create migration script: copy data from old → new
  3. Update all references (views, Java, actions) to new field
  4. Mark old field as deprecated (keep for 1 version)
  5. Remove old field in next version
  6. Add both steps to changelog

PATTERN 4: REMOVE FIELD FROM AXENR ENTITY
  1. Verify no code references the field (grep entire project)
  2. Remove from domain XML
  3. Create migration script: ALTER TABLE DROP COLUMN (with IF EXISTS)
  4. Update views to remove the field
  5. Add to changelog
  6. Create rollback script: ADD COLUMN back + restore data from backup

PATTERN 5: DATA CLEANUP / FIX
  1. Create versioned script V<version>__fix_<description>.sql
  2. Script MUST be idempotent
  3. Script MUST only touch AxENR tables (MIG-02)
  4. Add to changelog under "Fixed"
  5. Create rollback if data is modified (not just cleaned)

PATTERN 6: AOS VERSION UPGRADE
  1. Run CATEGORY 3 analysis (AOS git diff)
  2. For each BREAKING CHANGE:
     a. Create migration script if data needs moving
     b. Update AxENR code to match new AOS API
     c. Test with both old and new data
  3. Update libs.versions.toml with new versions
  4. Run full build: ./gradlew clean generateCode copyWebapp build
  5. Create upgrade changelog entry
  6. Test all AxENR features affected by the upgrade
```

---

## CATEGORY 5: DYNAMIC RULES FROM LESSONS

### Principle

This skill MUST read LESSONS-LEARNED.md BEFORE running checks. Lessons of type `migration`, `version`, or `build` with 2+ occurrences become reinforced rules.

### Reinforcement Logic

```
1. LOAD LESSONS:
   Read LESSONS-LEARNED.md
   Filter lessons where type IN ("migration", "version", "build", "data-init")

2. BUILD REINFORCED RULES:
   FOR each migration lesson:
     - Extract the error PATTERN
     - Map to closest static rule (MIG-XX)
     - IF occurrences >= 3 AND promu == true:
         → CRITICAL severity
     - IF occurrences >= 2:
         → severity += 1 level
     - IF occurrences == 1:
         → Keep original severity

3. MERGE with static rules

4. FEEDBACK: flag new patterns for error-learner
```

---

## EXECUTION LOGIC

```
STEP 0: LOAD CONTEXT AND REINFORCE RULES
  1. Read LESSONS-LEARNED.md → filter migration/version/build lessons
  2. Read gradle.properties → aopVersion
  3. Read libs.versions.toml → AOS version, module versions
  4. Build reinforced rules

STEP 1: DETERMINE MIGRATION TYPE
  IF target_version provided → AOS UPGRADE mode (CATEGORY 1 + 2 + 3 + 4)
  IF SQL files provided → SCRIPT VALIDATION mode (CATEGORY 1)
  IF data-init files provided → DATA-INIT VALIDATION mode (CATEGORY 2)
  IF domain changes provided → SCHEMA MIGRATION mode (CATEGORY 4)

STEP 2: RUN APPLICABLE RULES
  FOR each file in files_to_check:
    1. Determine file type:
       - *.sql → CATEGORY 1 (Script Quality: MIG-01 to MIG-08)
       - *.xml in data-init/ → CATEGORY 2 (Data-Init: MIG-10 to MIG-13)
       - *.xml in domains/ → CATEGORY 4 (Schema Patterns)
       - CHANGELOG.md → MIG-04 (Changelog Entry)
       - R*.sql → MIG-03 (Rollback existence check)

    2. Run static + reinforced rules

STEP 3: AOS UPGRADE ANALYSIS (if target_version provided)
  1. Locate AOS repository (.axelor/ directory)
  2. IF not found → WARN "AOS repo not available, skipping upgrade analysis"
     → Recommend running /axelor:setup first
  3. IF found:
     a. git diff between source and target versions
     b. Parse domain changes (fields, entities, relations)
     c. Parse view changes (elements, names, structure)
     d. Parse Java changes (methods, signatures, classes)
     e. Parse selection changes (values, names)
     f. Cross-reference with AxENR codebase
     g. Generate breaking_changes list

STEP 4: CROSS-VALIDATE
  - Every migration script has a rollback (MIG-03)
  - Every schema change has a changelog entry (MIG-04)
  - Version numbers are sequential and match project version (MIG-05)
  - No migration touches AOS tables directly (MIG-02)

STEP 5: CALCULATE SCORE
  - Start at 100
  - CRITICAL: -20 per violation
  - HIGH: -10 per violation
  - MEDIUM: -5 per violation
  - LOW: -2 per violation
  - Minimum: 0

RETURN {violations, breaking_changes, compatibility_report, score, summary}
```

---

## INTEGRATION WITH TICKET-SOLVER-AGENT

This skill is called:
- During **PHASE 3.5 (ANALYSE CRITIQUE)** when existing migration scripts are found
- During **PHASE 5 (VALIDATION)** when new migration scripts are generated
- **On demand** when a dev requests AOS upgrade analysis

### Trigger Conditions

- SQL files in the project's migration directory
- Data-init XML files modified by the ticket
- Domain XML changes that alter the schema
- Explicit request: "analyze migration" or "check AOS upgrade"
- target_version parameter provided → full AOS upgrade analysis

### Interaction with Other Skills

| Skill | Direction | Interaction |
|-------|-----------|-------------|
| error-learner | Skill → Lessons | Each violation creates/updates a lesson |
| knowledge-updater | Lessons → CLAUDE.md | Lessons with 3+ occurrences get promoted |
| axenr-dev-validator | Complementary | Dev validator checks code, migration validator checks scripts |
| enr-coherence-checker | Independent | No direct interaction |
| pre-flight-checker | Lessons → Skill | Loads migration lessons before generation |

### Bidirectional Reinforcement Loop

```
                    LESSONS-LEARNED.md
                   /                  \
          (reads before)         (writes after)
         /                              \
  migration-validator    ────→   error-learner
         |                              |
   detects violations           creates/updates lessons
         |                              |
   uses reinforced severity     increments occurrence count
         |                              |
         └──── next run uses ──────────┘
               stronger rules
```

---

## EXAMPLES

### Example 1: Validating a migration script

```
Input: V2.3.0__add_installation_power.sql

Content:
  ALTER TABLE axenr_installation ADD COLUMN power_kwc DECIMAL(20,2);
  UPDATE axenr_installation SET power_kwc = estimated_power WHERE power_kwc IS NULL;

Violations:
  [CRITICAL] MIG-01: ALTER TABLE ADD COLUMN without IF NOT EXISTS guard
    File: V2.3.0__add_installation_power.sql:1
    Fix: Wrap in DO $$ BEGIN IF NOT EXISTS (...) THEN ... END IF; END $$;

  [HIGH] MIG-03: No rollback script found (R2.3.0__add_installation_power.sql missing)
    Fix: Create rollback script that drops the column

  [HIGH] MIG-04: No CHANGELOG.md entry for version 2.3.0
    Fix: Add entry under ## [2.3.0] - Added section

Score: 50/100
```

### Example 2: AOS upgrade analysis (8.5.11 → 8.6.0)

```
Input: source_version=8.5.11, target_version=8.6.0

AOS git diff reveals:
  - SaleOrder.xml: field 'externalRef' renamed to 'externalReference'
  - InterventionService.java: method plan(Intervention) → plan(Intervention, LocalDate)
  - project-form.xml: panel 'mainPanel' renamed to 'projectMainPanel'

Cross-reference with AxENR:
  - AxENR views reference 'externalRef' in sale-order extension → BREAKING
  - AxENR overrides InterventionService.plan() → BREAKING
  - AxENR does NOT extend project-form mainPanel → SAFE

Breaking changes:
  [CRITICAL] MIG-21: Field 'externalRef' renamed to 'externalReference' in SaleOrder
    AxENR affected: axenr-sale-order-form.xml:15 (//field[@name='externalRef'])
    Migration: UPDATE sale_order SET external_reference = external_ref;
    Code: Update AxENR view to use new field name

  [CRITICAL] MIG-22: InterventionService.plan() signature changed
    AxENR affected: InterventionServiceAxenrImpl.java:42
    Migration: Update override to match new signature (add LocalDate parameter)

Compatibility report:
  - 2 CRITICAL breaking changes requiring code + data migration
  - 0 HIGH changes
  - Estimated migration effort: 2-4 hours
  - Recommendation: Create branch rm-migration-8.6.0 for isolated testing
```

### Example 3: Data-init validation

```
Input: data-init/input/axenr-sequences.xml

Content:
  <bind node="MetaSequence">
    <bind node="name" field="name" eval="'installation'"/>
    <bind node="prefix" field="prefix" eval="'INST'"/>
  </bind>

Violations:
  [HIGH] MIG-11: Missing search attribute → not idempotent
    Fix: Add search="self.name = :name" to <bind>

  [MEDIUM] MIG-13: Sequence name should start with 'axenr' prefix
    Fix: Rename to 'axenrInstallation'

  [HIGH] MIG-11: Missing update="false" → will overwrite on reimport
    Fix: Add update="false" to prevent overwriting custom values

Score: 60/100
```
