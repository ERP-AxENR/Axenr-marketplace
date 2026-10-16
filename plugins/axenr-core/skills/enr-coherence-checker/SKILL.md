---
name: enr-coherence-checker
description: Validates ENR business coherence - genericity across renewable energy types (PV, IRVE, wind, heat pumps), temporal coherence in commercial lifecycle, reusability of domain logic, and anti-patterns specific to ENR industry.
---

# ENR Coherence Checker

> Validates ENR business coherence: genericity across all renewable energy types, temporal coherence in the commercial lifecycle, and reusability of domain logic.

## ROLE

Analyze generated or modified code (domains, views, actions, Java, Groovy) and detect violations of AxENR business rules. This skill ensures that all code is **generic across all ENR types** (PV, PAC, IRVE, eolien, geothermie, biomasse), respects the **temporal coherence** of the ENR commercial lifecycle, and follows **reusability principles**.

## INPUTS

| Input | Format |
|-------|--------|
| files_to_check | List of file paths (domains, views, Java, Groovy) to validate |
| ticket_context | Description of the feature/fix being implemented |
| project | axenr-app or axenr-mobile |
| lessons_file_path | Path to LESSONS-LEARNED.md (for dynamic rule reinforcement) |

## OUTPUTS

| Output | Format |
|--------|--------|
| violations | List of `{severity, rule, file, line, message, fix, doc_ref}` |
| score | Coherence score 0-100 |
| summary | Human-readable summary of findings |

## SEVERITY LEVELS

| Level | Description |
|-------|-------------|
| CRITICAL | Code is PV-specific or hardcodes a single ENR type. Code accesses data from wrong lifecycle stage. |
| HIGH | Code lacks genericity mechanism. Temporal checks missing for stage-dependent data. |
| MEDIUM | Naming not generic. Missing ENR type parameter. Reusability could be improved. |
| LOW | Style/convention suggestions for better ENR coherence. |

---

## RULE 1: ENR GENERICITY

### Principle

All code MUST work for every renewable energy type. AxENR supports:

| Code | Type | Examples |
|------|------|----------|
| PV | Photovoltaique | Panneaux solaires, onduleurs, optimiseurs |
| PAC | Pompe a chaleur | Air/eau, eau/eau, geothermie |
| IRVE | Borne de recharge | Bornes AC/DC, wallbox |
| EOLIEN | Eolien | Petit eolien, grand eolien |
| GEO | Geothermie | Sonde, nappe, capteur horizontal |
| BIO | Biomasse | Chaudiere bois, poele |
| THERMO | Solaire thermique | CESI, SSC |

### Checks

```
1. HARDCODED ENR TYPE (CRITICAL)
   Pattern: Code references a specific ENR type without parameterization

   BAD:
   - field name contains "pv", "solar", "photovoltaic" without generic alternative
   - if (type == "PV") { ... } without else/switch for other types
   - domain filter: self.productCategory.code = 'PV'
   - class name: PvInstallationService (instead of EnrInstallationService)

   GOOD:
   - field name: "enrTypeSelect", "installationType"
   - switch/map covering all ENR types
   - domain filter using a parameter: self.productCategory = :_enrCategory
   - class name: EnrInstallationService with type parameter

2. MISSING ENR TYPE PARAMETER (HIGH)
   Pattern: Service/method that should accept ENR type but doesn't

   BAD:
   - computePower() with no type context
   - getEquipmentList() hardcoded to panels

   GOOD:
   - computePower(EnrType type, ...)
   - getEquipmentList(ProductCategory enrCategory, ...)

3. PV-SPECIFIC FIELD NAMES (MEDIUM)
   Pattern: Field/variable names that assume PV

   BAD:
   - numberOfModules (implies PV panels)
   - inverterCapacity (PV-specific)
   - panelOrientation (PV-specific)

   GOOD:
   - numberOfEquipments (generic)
   - mainEquipmentCapacity (generic)
   - installationOrientation (generic) or conditional per type

4. ENR-AWARE SELECTIONS (MEDIUM)
   Pattern: Selection values must cover all ENR types

   BAD:
   <selection name="installation.type.select">
     <option value="1">Rooftop</option>
     <option value="2">Ground mount</option>
   </selection>
   (PV-only options)

   GOOD:
   <selection name="installation.type.select">
     <option value="1">Rooftop PV</option>
     <option value="2">Ground mount PV</option>
     <option value="3">Air-water heat pump</option>
     <option value="4">AC charging station</option>
     ...
   </selection>
   OR use a configurable reference table instead of hardcoded selection

5. DOMAIN FILTER GENERICITY (MEDIUM)
   Pattern: Domain filters in views/actions must not assume ENR type

   BAD:
   <domain>self.productFamily.code = 'SOLAR_PANEL'</domain>

   GOOD:
   <domain>self.productFamily.enrTypeSelect = :_currentEnrType</domain>
   <context name="_currentEnrType" expr="eval: enrTypeSelect"/>
```

---

## RULE 2: TEMPORAL COHERENCE (ENR COMMERCIAL LIFECYCLE)

### ENR Business Lifecycle

The AxENR commercial lifecycle follows these stages in strict order:

```
PROSPECTION (1)
  |
QUALIFICATION (2)
  |
DEVIS (3)
  |
PASSATION_BE (4)    [Bureau d'Etudes]
  |
ADMINISTRATIF (5)   [Autorisations, Consuel, Enedis]
  |
PLANIFICATION (6)
  |
APPROVISIONNEMENT (7)
  |
CHANTIER (8)
  |
MISE_EN_SERVICE (9)
  |
FACTURATION (10)
  |
DOE_SAV (11)        [Dossier des Ouvrages Executes + SAV]
```

### Checks

```
1. WRONG LIFECYCLE ACCESS (CRITICAL)
   Pattern: Code reads/uses data that doesn't exist yet at the current stage

   BAD:
   - In PROSPECTION stage: accessing installationDate (only available after PLANIFICATION)
   - In DEVIS stage: reading consuelReference (only available after ADMINISTRATIF)
   - In QUALIFICATION: using purchaseOrderRef (only after APPROVISIONNEMENT)

   GOOD:
   - Each field access is guarded by stage check
   - Data is populated at the correct stage via workflow actions
   - Null-safety on stage-dependent fields

2. BACKWARD STAGE TRANSITION (CRITICAL)
   Pattern: Code allows moving to a previous stage without proper cancellation

   BAD:
   - Direct transition from CHANTIER back to DEVIS
   - Setting statusSelect to a lower value without validation

   GOOD:
   - Only forward transitions allowed (except explicit cancel/revert with audit trail)
   - Cancel creates a new version, doesn't modify the existing one
   - Revert requires manager approval and logs the reason

3. MISSING STAGE GUARDS (HIGH)
   Pattern: Actions/buttons visible at wrong stages

   BAD:
   <button name="generateInvoiceBtn" title="Generate invoice"/>
   (No hideIf - visible at all stages including PROSPECTION)

   GOOD:
   <button name="generateInvoiceBtn" title="Generate invoice"
     hideIf="statusSelect &lt; 9"
     readonlyIf="statusSelect != 9"/>
   (Only visible from MISE_EN_SERVICE onwards)

4. DATA INTEGRITY PER STAGE (HIGH)
   Pattern: Required fields must match the current stage

   BAD:
   - Making technicalStudyDate required at PROSPECTION stage
   - Requiring consuelNumber before ADMINISTRATIF phase

   GOOD:
   - requiredIf="statusSelect >= 4" for fields needed from PASSATION_BE
   - requiredIf="statusSelect >= 5" for ADMINISTRATIF fields
   - Progressive validation: each stage validates its own fields

5. STAGE-DEPENDENT COMPUTATIONS (MEDIUM)
   Pattern: Calculations that depend on stage-specific data

   BAD:
   - computeMargin() without checking if real costs are available (only after CHANTIER)
   - computeRoi() using estimated values when actuals exist

   GOOD:
   - computeMargin() checks stage: estimated before CHANTIER, actual after
   - Uses stage-aware data source selection
```

### Stage-Field Matrix

| Field Category | Available From | Examples |
|---------------|---------------|----------|
| Lead/contact info | PROSPECTION | partner, address, phone, source |
| Site survey data | QUALIFICATION | roofType, orientation, surface, consumption |
| Financial estimates | DEVIS | estimatedPower, estimatedPrice, primeAmount |
| Technical study | PASSATION_BE | technicalStudy, cableSection, inverterModel |
| Admin references | ADMINISTRATIF | consuelRef, enedisRef, maPrimeRenovRef |
| Planning dates | PLANIFICATION | plannedStartDate, plannedEndDate, teamAssignment |
| Purchase data | APPROVISIONNEMENT | purchaseOrders, supplierDeliveryDates |
| Execution data | CHANTIER | realStartDate, realEndDate, realQuantities |
| Commissioning | MISE_EN_SERVICE | commissioningDate, meterReading, productionTest |
| Billing | FACTURATION | invoices, payments, primePayment |
| Documentation | DOE_SAV | doeDocument, warranty, maintenanceContract |

---

## RULE 3: REUSABILITY

### Checks

```
1. DUPLICATED LOGIC (HIGH)
   Pattern: Same business logic implemented in multiple places

   BAD:
   - Power calculation in both OpportunityService and ProjectService
   - Address formatting duplicated across controllers

   GOOD:
   - Shared EnrCalculationService for power/energy computations
   - Common AddressService for formatting

2. HARDCODED BUSINESS CONSTANTS (MEDIUM)
   Pattern: Magic numbers or strings instead of configurable values

   BAD:
   - if (power > 9) (9 kWc is PV-specific threshold)
   - vatRate = new BigDecimal("0.10") (10% TVA for renovation)

   GOOD:
   - Use AxenrConfig entity for thresholds per ENR type
   - Use configurable tax rates from accounting module

3. NON-REUSABLE SERVICE DESIGN (MEDIUM)
   Pattern: Service methods that mix concerns

   BAD:
   - validateAndSaveAndNotify() - does 3 things
   - A single method handling all ENR types with massive if/else

   GOOD:
   - Separate validate(), save(), notify()
   - Strategy pattern or polymorphism for ENR-type-specific logic

4. VIEW COUPLING (LOW)
   Pattern: Views tightly coupled to a specific workflow

   BAD:
   - Form with fields only relevant to PV installations
   - Grid columns specific to one ENR type

   GOOD:
   - Dynamic visibility using showIf based on enrTypeSelect
   - Type-aware field display
```

---

## RULE 4: ENR ANTI-PATTERNS

### Known Anti-Patterns to Detect

| ID | Anti-Pattern | Detection | Fix |
|----|-------------|-----------|-----|
| ENR-AP-01 | PV-only naming | Field/class contains "solar", "panel", "module" without generic context | Rename to generic term or add ENR type qualifier |
| ENR-AP-02 | Missing lifecycle guard | Button/action without statusSelect condition | Add hideIf/readonlyIf with stage check |
| ENR-AP-03 | Hardcoded threshold | Magic number that is PV-specific (9kWc, 36kWc, 100kWc) | Move to AxenrConfig with ENR type key |
| ENR-AP-04 | Stage-skip data access | Accessing field from future stage | Add null check + stage guard |
| ENR-AP-05 | Monolithic ENR service | One service handling all types with if/else | Extract strategy per ENR type |
| ENR-AP-06 | Non-extensible selection | Hardcoded selection without option for new ENR types | Use reference table or extensible selection |
| ENR-AP-07 | Missing prime calculation | Energy subsidy (MaPrimeRenov, CEE) not considered | Add prime/subsidy computation hook |
| ENR-AP-08 | PV-specific unit | Using kWc when kW is more appropriate for non-PV | Use generic unit with ENR-type conversion |
| ENR-AP-09 | Ignoring site constraints | No check for site-specific constraints per ENR type | Add site validation per ENR type |
| ENR-AP-10 | Calendar ignoring weather | Planning without seasonal/weather considerations | Add weather-aware planning hook |

---

## RULE 5: DYNAMIC RULES FROM LESSONS (REINFORCEMENT LOOP)

### Principle

This skill MUST read LESSONS-LEARNED.md BEFORE running its checks. Lessons of type `enr` with 2+ occurrences become **reinforced rules** that are checked with HIGHER severity.

### Reinforcement Logic

```
1. LOAD LESSONS:
   Read LESSONS-LEARNED.md
   Filter lessons where type == "enr"

2. BUILD REINFORCED RULES:
   FOR each ENR lesson:
     - Extract the error PATTERN from the lesson
     - Extract the fix from the lesson
     - IF occurrences >= 3 AND promu == true:
         → CRITICAL severity (promoted to project rule)
     - IF occurrences >= 2:
         → severity += 1 level (LOW→MEDIUM, MEDIUM→HIGH, HIGH→CRITICAL)
     - IF occurrences == 1:
         → Keep original severity from static rules

3. MERGE with static rules:
   The reinforced rules are ADDED to the static rules (RULE 1 to RULE 4)
   If a reinforced lesson matches an existing static rule:
     → Use the HIGHER severity between the two
   If a reinforced lesson is NEW (not in static rules):
     → Add it as a dynamic rule with the reinforced severity

4. FEEDBACK AFTER VALIDATION:
   FOR each violation found:
     IF it matches a lesson pattern → report lesson_id in the violation output
     IF it does NOT match any lesson → flag as "new_pattern" for error-learner to create
```

### Example: Reinforcement in Action

```
LESSONS-LEARNED.md contains:
  LESSON-051: Nommage PV-specifique (ENR-AP-01) - Occurrences: 3 - Promu: true

Effect:
  → Rule ENR-AP-01 "PV-only naming" is now CRITICAL (was MEDIUM)
  → Agent MUST fix it before proceeding (cannot skip)
  → If detected again, error-learner increments to 4 occurrences
  → The rule gets progressively harder to ignore
```

---

## EXECUTION LOGIC

```
STEP 0: LOAD AND REINFORCE RULES
  1. Read LESSONS-LEARNED.md
  2. Filter type == "enr" lessons
  3. Build reinforced rules (merge with static rules, adjust severities)

STEP 1: CALL AXELOR PARTNER AGENTS
  Appeler les agents partenaire pour enrichir la detection :

  → code-reviewer : analyser le code pour detecter des patterns PV-specifiques,
    du couplage a un seul type ENR, des noms non generiques
  → code-analyzer : analyser la reutilisabilite, le couplage, les constantes hardcodees

  Collecter les violations des agents partenaire qui sont pertinentes pour la coherence ENR.

STEP 2: RUN ENR STATIC + DYNAMIC RULES
  FOR each file in files_to_check:
    1. Determine file type (domain XML, view XML, action XML, Java, Groovy)
    2. Parse content

    3. RUN GENERICITY CHECKS (Rule 1):
       - Scan for PV-specific terms (solar, panel, module, onduleur, string)
       - Check field names for ENR-type assumptions
       - Verify services accept ENR type parameter
       - Check selections cover multiple ENR types
       - Verify domain filters are parameterized

    4. RUN TEMPORAL COHERENCE CHECKS (Rule 2):
       - Map fields to their lifecycle stage
       - Check that field access is guarded by stage condition
       - Verify button/action visibility matches lifecycle stage
       - Check required conditions match stage progression
       - Verify computations use stage-appropriate data

    5. RUN REUSABILITY CHECKS (Rule 3):
       - Detect duplicated business logic patterns
       - Flag hardcoded constants
       - Check service method granularity
       - Verify view components are reusable

    6. RUN ANTI-PATTERN DETECTION (Rule 4):
       - Match against known ENR anti-patterns (ENR-AP-01 to ENR-AP-10)
       - Match against DYNAMIC rules from reinforced lessons (Rule 5)

STEP 3: MERGE AND DEDUPLICATE
  1. Merge violations from agents partenaire + ENR rules
  2. Deduplicate: if an agent and a rule detect the SAME issue → keep the one with HIGHER severity
  3. Enrich: violations code-reviewer qui matchent un pattern ENR → ajouter le ENR-AP-XX correspondant
  4. Tag each violation with its source

STEP 4: CALCULATE SCORE
  - Start at 100
  - CRITICAL: -20 per violation
  - HIGH: -10 per violation
  - MEDIUM: -5 per violation
  - LOW: -2 per violation
  - Minimum: 0

STEP 5: ENRICH WITH DOC REFERENCES
  FOR each violation:
    - Add doc_ref field linking to the rule ID (e.g., "RULE1-CHECK3", "ENR-AP-01")
    - Format: "<RULE_ID> | enr-coherence-checker"
    - This allows traceability back to the exact rule definition

RETURN {violations, score, summary, reinforced_rules_used, agents_called}
```

---

## INTEGRATION WITH TICKET-SOLVER-AGENT

This skill is called during **PHASE 5 (VALIDATION)** of the ticket-solver-agent workflow, BEFORE code is committed. If the score is below 70, the agent MUST fix the violations before proceeding.

### Trigger Conditions

- Any domain XML containing ENR-related entities
- Any view XML for ENR-related forms/grids
- Any Java service in the `fr.axenr` package
- Any action XML with `axenr-action-` prefix

### Bidirectional Reinforcement Loop

```
                    LESSONS-LEARNED.md
                   /                  \
          (reads before)         (writes after)
         /                              \
  enr-coherence-checker  ────→  error-learner
         |                              |
   detects violations           creates/updates lessons
         |                              |
   uses reinforced severity     increments occurrence count
         |                              |
         └──── next run uses ──────────┘
               stronger rules
```

**Direction 1: Lessons → Skill (REINFORCEMENT)**
- BEFORE validation, this skill reads all `type: enr` lessons from LESSONS-LEARNED.md
- Lessons with 2+ occurrences get their severity UPGRADED
- Lessons with 3+ occurrences promoted to CLAUDE.md become CRITICAL
- New patterns from lessons are added as dynamic detection rules

**Direction 2: Skill → Lessons (LEARNING)**
- AFTER validation, each violation is sent to error-learner
- error-learner creates a new lesson or increments an existing one
- When a lesson reaches 3 occurrences, knowledge-updater promotes it
- The promoted rule becomes part of the project's permanent knowledge

### Interaction with Other Skills

| Skill | Direction | Interaction |
|-------|-----------|-------------|
| error-learner | Skill → Lessons | Each violation creates/updates a lesson in LESSONS-LEARNED.md |
| knowledge-updater | Lessons → CLAUDE.md | Lessons with 3+ occurrences get promoted to permanent project rules |
| pre-flight-checker | Lessons → Skill | Loads relevant ENR lessons as context before generation |
| axenr-dev-validator | Parallel | Run simultaneously for technical validation (shares reinforcement loop) |
