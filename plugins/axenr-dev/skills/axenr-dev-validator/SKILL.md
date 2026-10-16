---
name: axenr-dev-validator
description: Validates code against Axelor best practices, AxENR conventions and official Axelor docs. Covers domains, views, actions, Java services/controllers, Guice bindings, translations, extensions, and the 8 AxENR golden rules.
---

# AxENR Dev Validator

> Validates code against Axelor development best practices, AxENR project conventions, and the official Axelor documentation. Covers domains, views, actions, Java services/controllers, Guice bindings, translations, extensions, and the 8 AxENR golden rules.

## ROLE

Analyze generated or modified code and detect violations of Axelor/AxENR development rules. This skill combines rules from:
- The 8 Golden Rules of AxENR
- Axelor official documentation and e-learning
- AxENR project CLAUDE.md conventions
- Axelor Open Platform (AOP) 7.4.7 / AOS 8.5.11 standards

## INPUTS

| Input | Format |
|-------|--------|
| files_to_check | List of file paths to validate |
| ticket_context | Description of the change |
| project | axenr-app or axenr-mobile |
| check_categories | Optional filter: domains, views, actions, java, all (default: all) |
| lessons_file_path | Path to LESSONS-LEARNED.md (for dynamic rule reinforcement) |

## OUTPUTS

| Output | Format |
|--------|--------|
| violations | List of `{severity, category, rule, file, line, message, fix, doc_ref}` |
| score | Quality score 0-100 |
| summary | Human-readable summary |

## SEVERITY LEVELS

| Level | Description |
|-------|-------------|
| CRITICAL | Build will fail. AOS code modified. Security vulnerability. |
| HIGH | Runtime error likely. Extension breaking. Data integrity risk. |
| MEDIUM | Convention violation. Maintenance concern. Missing best practice. |
| LOW | Style suggestion. Could be improved. |

---

## CATEGORY 1: DOMAIN XML VALIDATION

### Rules

```
DOM-01: PACKAGE COMPLET (CRITICAL)
  All ref= attributes on relational fields MUST use full package path.

  BAD:  <many-to-one name="company" ref="Company"/>
  GOOD: <many-to-one name="company" ref="com.axelor.apps.base.db.Company" title="Company"/>

DOM-02: MAPPEDBY ON ONE-TO-MANY (CRITICAL)
  All one-to-many fields MUST have mappedBy attribute.

  BAD:  <one-to-many name="lineList" ref="fr.axenr.db.OrderLine"/>
  GOOD: <one-to-many name="lineList" ref="fr.axenr.db.OrderLine" mappedBy="order" title="Lines"/>

DOM-03: EXTRA-CODE FOR SELECTIONS (HIGH)
  Every integer field with selection= MUST have corresponding constants in extra-code.

  BAD:  <integer name="statusSelect" selection="order.status.select"/>
        (no extra-code)
  GOOD: <integer name="statusSelect" selection="order.status.select" default="1"/>
        <extra-code><![CDATA[
          public static final int STATUS_DRAFT = 1;
          public static final int STATUS_CONFIRMED = 2;
        ]]></extra-code>

DOM-04: TITLE ON ALL FIELDS (HIGH)
  Every field MUST have a title attribute (except boolean - see DOM-05).

  BAD:  <string name="code"/>
  GOOD: <string name="code" title="Code"/>

DOM-05: BOOLEAN WITHOUT TITLE (HIGH)
  Boolean fields MUST NOT have a title attribute. Axelor auto-generates the label.
  Boolean fields MUST have default="true" or default="false".

  BAD:  <boolean name="isActive" title="Active"/>
  GOOD: <boolean name="isActive" default="true"/>

DOM-06: NAMECOLUMN (MEDIUM)
  At least one field should have namecolumn="true" for display in relational fields.

DOM-07: PACKAGE CONVENTION (MEDIUM)
  AxENR entities: package MUST be "fr.axenr.db"
  Module name MUST be "axenr"

  BAD:  <module package="com.axenr.db" name="axenr"/>
  GOOD: <module package="fr.axenr.db" name="axenr"/>

DOM-08: TRACK ON IMPORTANT ENTITIES (LOW)
  Entities with statusSelect SHOULD have <track> for audit trail.

DOM-09: SCHEMA VERSION (MEDIUM)
  XSD schemaLocation MUST match AOP version (7.1 for AOP 7.4.x).
  schemaLocation MUST be on a single line.

  BAD:  xsi:schemaLocation="http://axelor.com/xml/ns/domain-models
          https://axelor.com/xml/ns/domain-models/domain-models_7.1.xsd">
  GOOD: xsi:schemaLocation="http://axelor.com/xml/ns/domain-models https://axelor.com/xml/ns/domain-models/domain-models_7.1.xsd">

DOM-10: COPY ATTRIBUTE (LOW)
  Fields that should not be copied (status, sequence, computed totals) SHOULD have copy="false".

DOM-11: RELATION DIRECTION AXENR→AOS (HIGH)
  Relations from AxENR entities to AOS entities MUST be ManyToOne (AxENR → AOS).
  NEVER create relations from AOS entities pointing to AxENR (would require modifying AOS).

  BAD:
  <!-- In an AOS entity extension: adding a relation TO AxENR -->
  <one-to-many name="axenrInstallations" ref="fr.axenr.db.AxenrInstallation" mappedBy="project"/>
  <!-- This forces AOS entity to "know" AxENR → breaks independence -->

  GOOD:
  <!-- In AxENR entity: ManyToOne pointing TO AOS -->
  <many-to-one name="project" ref="com.axelor.apps.project.db.Project" title="Project"/>
  <!-- AxENR knows AOS, but AOS doesn't know AxENR → clean dependency -->

  Exceptions:
  - Track fields on AOS entities (managed by Axelor framework, not relations)
  - Custom fields via attrs (JSON storage, no schema dependency)

DOM-12: NO BUSINESS LOGIC IN DOMAINS (MEDIUM)
  Domain XML MUST NOT contain business logic. Use formula fields or Java services.
  Domains define DATA STRUCTURE, not behavior.

  BAD:
  <string name="fullAddress" expression="CONCAT(street, ' ', city, ' ', zip)"/>
  <!-- SQL expression with business logic in domain -->

  BAD:
  <extra-code><![CDATA[
    public BigDecimal computeTotal() {
      return this.quantity.multiply(this.unitPrice);
    }
  ]]></extra-code>
  <!-- Business logic in extra-code instead of service -->

  GOOD:
  <!-- Domain: just the field -->
  <decimal name="totalAmount" title="Total" readonly="true"/>
  <!-- Service: the computation -->
  // In AxEnrOrderLineService.java:
  public BigDecimal computeTotal(OrderLine line) {
    return line.getQuantity().multiply(line.getUnitPrice());
  }

  Allowed in extra-code:
  - Constants (STATUS_DRAFT, TYPE_PV, etc.)
  - Simple getters for display (getFullName for namecolumn)
  - Enum-like static final fields

DOM-13: SEQUENCES IN DEDICATED CONFIG (MEDIUM)
  AxENR sequences MUST be defined in dedicated data-init files, not inline in domains.
  Sequence names MUST be prefixed with 'axenr'.

  BAD:
  <!-- Sequence defined nowhere, or hardcoded in Java -->
  order.setReference("INST-" + String.format("%06d", id));

  BAD:
  <!-- Sequence in random data-init file mixed with other data -->
  <bind node="MetaSequence">
    <bind node="name" field="name" eval="'installation'"/>
  </bind>

  GOOD:
  <!-- Dedicated file: data-init/input/axenr-sequences.xml -->
  <bind node="MetaSequence" search="self.name = :name" update="false">
    <bind node="name" field="name" eval="'axenrInstallation'"/>
    <bind node="prefix" field="prefix" eval="'INST'"/>
    <bind node="padding" field="padding" eval="6"/>
  </bind>
  <!-- And in Java: use SequenceService to get the next value -->
```

---

## CATEGORY 2: VIEW XML VALIDATION

### Rules

```
VIEW-01: NAME ON ALL ELEMENTS (CRITICAL)
  Every panel, button, field, menu, item MUST have a name attribute.
  This enables extensions to target elements via XPath.

  Exceptions: <toolbar/>, <menubar/>, <panel-mail/>, <mail-messages/>, <mail-followers/>

  BAD:  <panel title="Info">
          <button title="Confirm" onClick="..."/>
        </panel>
  GOOD: <panel name="infoPanel" title="Info">
          <button name="confirmBtn" title="Confirm" onClick="..."/>
        </panel>

VIEW-02: FORM-VIEW AND GRID-VIEW (CRITICAL)
  All relational fields (many-to-one, many-to-many, one-to-many) MUST specify form-view and grid-view.

  BAD:  <field name="partner"/>
  GOOD: <field name="partner" form-view="partner-form" grid-view="partner-grid"/>

VIEW-03: PANEL-RELATED FOR O2M (HIGH)
  One-to-many fields SHOULD use <panel-related> instead of <field> for better control.

  BAD:  <field name="lineList"/>
  GOOD: <panel-related name="linesPanel" field="lineList"
          form-view="order-line-form" grid-view="order-line-grid"/>

VIEW-04: EXTENSION FORMAT (CRITICAL)
  Extensions of existing views MUST have:
  - id="axenr-<original-name>" (unique)
  - extension="true"
  - Same name as original view
  - Same model as original view

  BAD:  <form name="opportunity-form" title="Opportunity" model="...">
  GOOD: <form id="axenr-opportunity-form" name="opportunity-form" title="Opportunity"
          model="com.axelor.apps.crm.db.Opportunity" extension="true">

VIEW-05: EXTEND XPATH VALIDITY (HIGH)
  XPath expressions in <extend target="..."> MUST reference existing elements.
  Common patterns:
  - //field[@name='fieldName']
  - //panel[@name='panelName']
  - //button[@name='btnName']
  - / (root)

VIEW-06: NAMING CONVENTIONS (MEDIUM)
  - Grid: <object>-grid (sale-order-grid)
  - Form: <object>-form (sale-order-form)
  - Panel: <context>Panel (mainPanel, linesPanel)
  - Button: <verb>Btn (confirmBtn, cancelBtn)
  - Dummy fields: $_x<Name> ($\_xTargetPrice)

VIEW-07: WIDTH ON FORMS (MEDIUM)
  Business forms SHOULD use width="large".

VIEW-08: TOOLBAR/MENUBAR ORDER (MEDIUM)
  In grid and form: toolbar MUST come before menubar, menubar before content.

VIEW-09: MAIN PANEL WITHOUT TITLE (LOW)
  The first/main panel SHOULD NOT have a title attribute.

  BAD:  <panel name="mainPanel" title="Main">
  GOOD: <panel name="mainPanel">

VIEW-10: HILITE ORDER (LOW)
  Hilite conditions are evaluated in order. Last one with if="true" serves as default.

VIEW-11: COLSPAN ON LARGE FIELDS (LOW)
  Large text fields, O2M, M2M SHOULD use colSpan="12".

VIEW-12: SIDEBAR FOR METADATA (LOW)
  Dates (createdOn, updatedOn), status, and metadata SHOULD be in sidebar panels.
```

---

## CATEGORY 3: ACTION XML VALIDATION

### Rules

```
ACT-01: EVAL PREFIX (CRITICAL)
  All expr= attributes MUST start with "eval: " prefix.

  BAD:  <field name="date" expr="__date__"/>
  GOOD: <field name="date" expr="eval: __date__"/>

ACT-02: NULL SAFETY (CRITICAL)
  All expressions accessing nested properties MUST use ?. operator.

  BAD:  <field name="city" expr="eval: partner.address.city"/>
  GOOD: <field name="city" expr="eval: partner?.address?.city"/>

ACT-03: XML ESCAPING (CRITICAL)
  Special characters in XML attributes MUST be escaped.
  - & -> &amp;
  - < -> &lt;
  - > -> &gt;
  - " -> &quot;

  BAD:  expr="eval: a > 5 && b < 10"
  GOOD: expr="eval: a &gt; 5 &amp;&amp; b &lt; 10"

ACT-04: REPOSITORY CONSTANTS (HIGH)
  Selection values MUST use __repo__(Model).CONSTANT, not magic numbers.

  BAD:  expr="eval: 1"  (for statusSelect)
  GOOD: expr="eval: __repo__(Order).STATUS_DRAFT"

ACT-05: NAMING CONVENTION (HIGH)
  AxENR actions MUST be prefixed: axenr-action-<object>-<type>-<function>
  Types: record, attrs, validate, method, group, view

  BAD:  action-opportunity-record-default
  GOOD: axenr-action-opportunity-record-default

ACT-06: CDATA ON DOMAINS (MEDIUM)
  Multi-line domain filters SHOULD use CDATA to prevent formatting issues.

  GOOD: <domain><![CDATA[
          self.statusSelect = :_status AND self.company = :_company
        ]]></domain>

ACT-07: CONTEXT VARIABLE NAMING (MEDIUM)
  Context variables MUST be prefixed with _ (underscore).

  BAD:  <context name="statusDraft" expr="..."/>
  GOOD: <context name="_statusDraft" expr="..."/>

ACT-08: DOMAIN FILTER ESCAPING (MEDIUM)
  Domain filters with dynamic values MUST use proper escaping.

  BAD:  expr="eval: 'self.category = ' + category.id"
  GOOD: expr="eval: &quot;self.category.id = ${category?.id}&quot;" if="category != null"

ACT-09: ACTION-GROUP STRUCTURE (LOW)
  onNew/onLoad/onSave SHOULD call action-groups, not individual actions.

  BAD:  onNew="action-record-default, action-attrs-readonly"
  GOOD: onNew="action-order-group-onnew"
        <action-group name="action-order-group-onnew">
          <action name="action-order-record-default"/>
          <action name="action-order-attrs-readonly"/>
        </action-group>

ACT-10: SAVE BEFORE METHOD (MEDIUM)
  Transactional action-methods SHOULD be preceded by "save" in the onClick sequence.

  BAD:  onClick="action-method-finalize"
  GOOD: onClick="save, action-method-finalize"
        OR via action-group: save + action-method
```

---

## CATEGORY 4: JAVA VALIDATION

### Rules

```
JAVA-01: NEVER MODIFY AOS (CRITICAL)
  No file outside fr.axenr.* package should be modified.
  No file in com.axelor.apps.* should be created (except extensions).

  Detection: Check file path is within modules/axenr/src/main/java/fr/axenr/

JAVA-02: TRACEBACK IN CONTROLLERS (CRITICAL)
  Every controller method MUST have try-catch with TraceBackService.trace(response, e).

  BAD:
  public void confirm(ActionRequest request, ActionResponse response) {
      Order order = request.getContext().asType(Order.class);
      orderService.confirm(order);
      response.setReload(true);
  }

  GOOD:
  public void confirm(ActionRequest request, ActionResponse response) {
      try {
          Order order = request.getContext().asType(Order.class);
          orderService.confirm(order);
          response.setReload(true);
      } catch (Exception e) {
          TraceBackService.trace(response, e);
      }
  }

JAVA-03: TRANSACTIONAL ANNOTATION (CRITICAL)
  Any method calling repo.save() or repo.remove() MUST be annotated @Transactional.

  BAD:
  public void confirm(Order order) {
      order.setStatus(STATUS_CONFIRMED);
      orderRepo.save(order);
  }

  GOOD:
  @Transactional(rollbackOn = {Exception.class})
  public void confirm(Order order) throws AxelorException {
      order.setStatus(STATUS_CONFIRMED);
      orderRepo.save(order);
  }

JAVA-04: INJECT PATTERN (HIGH)
  Services MUST use @Inject (field or constructor). Beans.get() only in controllers.

  BAD (in service):
  OtherService other = Beans.get(OtherService.class);

  GOOD (in service):
  @Inject private OtherService otherService;
  OR constructor injection with @Inject

JAVA-05: CONTEXT VS DATABASE (HIGH)
  Objects from request.getContext().asType() are NOT managed by Hibernate.
  MUST call repo.find(id) before save operations.

  BAD:
  Order order = request.getContext().asType(Order.class);
  orderRepo.save(order); // DANGER: can create duplicate

  GOOD:
  Order order = request.getContext().asType(Order.class);
  order = orderRepo.find(order.getId()); // Reload from DB
  orderService.confirm(order);
  response.setReload(true);

JAVA-06: I18N FOR MESSAGES (HIGH)
  All user-facing messages MUST use I18n.get().
  Error constants MUST use /*$$(*/  /*)*/  pattern.

  BAD:
  throw new AxelorException(TraceBackRepository.CATEGORY_INCONSISTENCY,
      "Order already confirmed");

  GOOD:
  throw new AxelorException(TraceBackRepository.CATEGORY_INCONSISTENCY,
      I18n.get(AxenrExceptionMessage.ORDER_ALREADY_CONFIRMED));

  With constant:
  public static final String ORDER_ALREADY_CONFIRMED =
      /*$$(*/ "Order already confirmed" /*)*/;

JAVA-07: GUICE BINDING (HIGH)
  Every new service/repository override MUST be registered in AxEnrModule.configure().

  Patterns:
  - bind(Interface.class).to(Implementation.class);           // New service
  - bind(ExistingImpl.class).to(AxEnrOverrideImpl.class);     // Override
  - bind(Observer.class);                                       // Observer

JAVA-08: VISIBILITY RULES (MEDIUM)
  - Service attributes: protected (NOT private) for extensibility
  - Service internal methods: protected (NOT private)
  - Transactional methods: public or protected (NOT private - Guice limitation)

  BAD:
  private final OrderRepository orderRepo;
  private void computeInternal() { ... }

  GOOD:
  protected final OrderRepository orderRepo;
  protected void computeInternal() { ... }

JAVA-09: NAMING CONVENTIONS (MEDIUM)
  - AxENR services: AxEnr<Object>Service / AxEnr<Object>ServiceImpl
  - Override suffix: <Service><Module>Impl (e.g., InterventionServiceAxenrImpl)
  - Controller: <Object>Controller
  - Constant: UPPER_SNAKE_CASE
  - Package: fr.axenr.<layer> (service, action, db, module, exception)

JAVA-10: NO COMMENTS IN CODE (MEDIUM)
  Code MUST be self-documenting. No inline comments except for complex algorithms.
  No TODO comments. No commented-out code.

JAVA-11: SINGLE RESPONSIBILITY (MEDIUM)
  - Max 1000 lines per class
  - Methods should do one thing
  - Separate validate/save/notify into distinct methods
  - No Beans.get() in services (circular dependency smell)

JAVA-12: SENIOR CODING PATTERNS (MEDIUM)
  - Use stream + orElse instead of if/else for lookups
  - Use Locale.ROOT for toLowerCase()/toUpperCase()
  - Avoid switch when expression suffices
  - Use Optional + map/orElse

  BAD:
  DayPlanning found = null;
  for (DayPlanning dp : weeklyPlanning.getWeekDays()) {
    if (dayName.equals(dp.getNameSelect())) { found = dp; break; }
  }

  GOOD:
  weeklyPlanning.getWeekDays().stream()
      .filter(dp -> dayName.equals(dp.getNameSelect()))
      .findFirst()
      .map(DayPlanning::getMorningFrom)
      .orElse(DEFAULT_START_TIME);

JAVA-13: NO WILDCARD IMPORTS (LOW)

  BAD:  import com.axelor.apps.base.db.*;
  GOOD: import com.axelor.apps.base.db.Company;

JAVA-14: INTERFACE FOR EVERY SERVICE (LOW)
  Every service implementation MUST have a corresponding interface.
```

---

## CATEGORY 5: TRANSLATION VALIDATION

### Rules

```
I18N-01: ENGLISH KEYS (HIGH)
  All title, help, message attributes MUST be in English.
  French goes only in messages_fr.csv.

I18N-02: BOOLEAN NO TITLE (HIGH)
  Boolean fields MUST NOT have title in domain XML.
  Axelor auto-generates from camelCase field name.

I18N-03: CUSTOM VS MESSAGES (MEDIUM)
  Keys present in code go in messages_fr.csv (auto-generated by ./gradlew i18n).
  Keys NOT in code go in custom_fr.csv.
  NEVER manually add to messages.csv (it is generated).

I18N-04: NAMING ONLY ENGLISH (MEDIUM)
  All technical names (panels, actions, fields, variables) MUST be in English.

  BAD:  name="panneauPrincipal", name="action-facture-calculer"
  GOOD: name="mainPanel", name="action-invoice-compute"
```

---

## CATEGORY 6: EXTENSION/OVERRIDE VALIDATION

### Rules

```
EXT-01: NEVER RENAME EXISTING (CRITICAL)
  Never rename an existing panel, action, field, or element.
  Extensions referencing the old name will break.

  BAD:  Renaming extraPanel to technicalSpecsPanel
  GOOD: Keep extraPanel name, change only the title

EXT-02: NEVER DELETE EXISTING ACTION (CRITICAL)
  Never delete an existing action to replace it.
  Other buttons/menus may reference it.

  BAD:  Delete action-contract-view-interventions, create axenr-action-contract-view-interventions
  GOOD: Keep original action AND create new axenr- prefixed action

EXT-03: NEVER DELETE DUPLICATES (HIGH)
  Never remove existing duplicate elements in the codebase.
  The ticket should contain ONLY the requested changes.

EXT-04: PRESERVE ONCHANGE (HIGH)
  When adding an onChange, NEVER overwrite the existing one.

  BAD:  <attribute name="onChange" value="axenr-action-compute"/>
        (overwrites original onChange)
  GOOD: <attribute name="onChange" value="original-action, axenr-action-compute"/>

EXT-05: EXTEND VS REDEFINE (MEDIUM)
  Prefer extension="true" over full redefinition for grid/form views.
  Full redefinition only when the view is completely different.

EXT-06: OVERRIDE CHAIN (MEDIUM)
  When overriding a service, always extend the LAST implementation in the chain.

  BAD:  class AxEnrService extends OriginalServiceImpl (skipping intermediate override)
  GOOD: class AxEnrService extends LatestModuleServiceImpl
```

---

## CATEGORY 7: GIT/WORKFLOW VALIDATION

### Rules

```
GIT-01: AUTHOR CONFIG (CRITICAL)
  Git author MUST be fbe-axenr / f.benomar@erp-axenr.fr
  Never fb2001 or other personal accounts.

GIT-02: NO CO-AUTHOR (HIGH)
  Commits MUST NOT contain Co-Authored-By headers.

GIT-03: CONVENTIONAL COMMITS (HIGH)
  Format: <type>(#<ticket>): <description in english, lowercase, imperative>
  Max 72 characters for first line.
  Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci, revert

GIT-04: BRANCH FROM CORRECT BASE (HIGH)
  Always verify current branch before creating a new one.
  Always git checkout <base> && git pull before branching.

GIT-05: SUBMODULE SYNC (HIGH)
  Both repos (axenr-app + modules/axenr) MUST be on the same branch.
  Pull submodule FIRST, then parent.
```

---

## CATEGORY 8: DYNAMIC RULES FROM LESSONS (REINFORCEMENT LOOP)

### Principle

This skill MUST read LESSONS-LEARNED.md BEFORE running its checks. Lessons matching the checked categories (domain, view, action, java, build, version, naming, i18n) with 2+ occurrences become **reinforced rules** checked with HIGHER severity.

### Reinforcement Logic

```
1. LOAD LESSONS:
   Read LESSONS-LEARNED.md
   Filter lessons by type matching check_categories:
     - domain → type: domain
     - views → type: view
     - actions → type: action
     - java → type: java, build, version, naming
     - all → all types except enr (enr-coherence-checker handles those)

2. BUILD REINFORCED RULES:
   FOR each relevant lesson:
     - Extract the error PATTERN from the lesson
     - Map to the closest static rule (DOM-XX, VIEW-XX, ACT-XX, JAVA-XX, etc.)
     - IF occurrences >= 3 AND promu == true:
         → CRITICAL severity (promoted to project rule)
     - IF occurrences >= 2:
         → severity += 1 level (LOW→MEDIUM, MEDIUM→HIGH, HIGH→CRITICAL)
     - IF occurrences == 1:
         → Keep original severity from static rules

3. MERGE with static rules:
   IF reinforced lesson matches a static rule:
     → Use the HIGHER severity between the two
   IF reinforced lesson is NEW (not covered by any static rule):
     → Add it as a dynamic rule

4. FEEDBACK AFTER VALIDATION:
   FOR each violation found:
     IF it matches a lesson → report lesson_id in violation output
     IF it is NEW → flag as "new_pattern" for error-learner
```

### Type-to-Category Mapping

| Lesson Type | Validator Category | Static Rules |
|-------------|-------------------|--------------|
| domain | CATEGORY 1 | DOM-01 to DOM-13 |
| view | CATEGORY 2 | VIEW-01 to VIEW-12 |
| action | CATEGORY 3 | ACT-01 to ACT-10 |
| java | CATEGORY 4 | JAVA-01 to JAVA-14 |
| i18n | CATEGORY 5 | I18N-01 to I18N-04 |
| naming | CATEGORY 6 | EXT-01 to EXT-06 |
| build, version | CATEGORY 7 | GIT-01 to GIT-05 |
| rest | CATEGORY 4 | JAVA-XX (extended) |
| migration | migration-validator | MIG-01 to MIG-27 |
| mobile | Skipped | Handled by mobile-specific checks |

---

## EXECUTION LOGIC

```
STEP 0: LOAD AND REINFORCE RULES
  1. Read LESSONS-LEARNED.md
  2. Filter lessons by applicable types (exclude type: enr)
  3. Build reinforced rules (merge with static rules, adjust severities)

STEP 1: CALL AXELOR PARTNER AGENTS
  Appeler les agents partenaire et collecter leurs violations :

  FOR domain XML files:
    → axelor-xml-validator (XSD validation)
    → axelor-naming-checker (naming conventions)

  FOR view XML files:
    → axelor-xml-validator (XSD validation)
    → axelor-view-semantic-validator (field/action coherence)
    → axelor-naming-checker (naming conventions)

  FOR Java files:
    → axelor-java-style-validator (code style)
    → axelor-naming-checker (naming conventions)

  FOR ALL files:
    → code-reviewer (quality review CRITICAL/HIGH/MEDIUM/LOW)
    → code-analyzer (security, performance, best practices)

  Collecter TOUTES les violations des agents partenaire.

STEP 2: RUN AXENR STATIC + DYNAMIC RULES
  FOR each file in files_to_check:
    1. Determine file type from extension and path:
       - *.xml in domains/ -> DOMAIN validation (DOM-01 to DOM-13)
       - *.xml in views/  -> VIEW + ACTION validation (VIEW-01 to VIEW-12, ACT-01 to ACT-10)
       - *.java in action/ -> JAVA CONTROLLER validation (JAVA-01 to JAVA-14)
       - *.java in service/ -> JAVA SERVICE validation (JAVA-01 to JAVA-14)
       - *.java in module/ -> GUICE MODULE validation (JAVA-07)
       - *.csv in i18n/ -> TRANSLATION validation (I18N-01 to I18N-04)

    2. RUN applicable category rules (static + reinforced from lessons)

    3. Cross-validate:
       - Domain fields referenced in views exist
       - Actions referenced in views/buttons exist
       - Java methods referenced in action-method exist
       - Bindings match interfaces to implementations

STEP 3: MERGE AND DEDUPLICATE
  1. Merge violations from agents partenaire + AxENR rules
  2. Deduplicate: if an agent and a rule detect the SAME issue → keep the one with HIGHER severity
  3. Tag each violation with its source (agent name or rule ID)

STEP 4: CALCULATE SCORE
  - Start at 100
  - CRITICAL: -15 per violation
  - HIGH: -8 per violation
  - MEDIUM: -3 per violation
  - LOW: -1 per violation
  - Minimum: 0

STEP 5: ENRICH WITH DOC REFERENCES
  FOR each violation:
    - Add doc_ref field linking to the rule ID (e.g., "DOM-11", "JAVA-01")
    - Format: "<CATEGORY>-<RULE_ID> | axenr-dev-validator"
    - This allows traceability back to the exact rule definition

RETURN {violations, score, summary, reinforced_rules_used, agents_called}
```

---

## INTEGRATION WITH TICKET-SOLVER-AGENT

This skill is called during **PHASE 5 (VALIDATION)** of the ticket-solver-agent workflow, in parallel with enr-coherence-checker. If the score is below 70, the agent MUST fix the violations before proceeding.

### Bidirectional Reinforcement Loop

```
                    LESSONS-LEARNED.md
                   /                  \
          (reads before)         (writes after)
         /                              \
  axenr-dev-validator   ────→   error-learner
         |                              |
   detects violations           creates/updates lessons
         |                              |
   uses reinforced severity     increments occurrence count
         |                              |
         └──── next run uses ──────────┘
               stronger rules
```

**Direction 1: Lessons → Skill (REINFORCEMENT)**
- BEFORE validation, this skill reads all relevant lessons from LESSONS-LEARNED.md
- Filters by type: domain, view, action, java, build, version, naming, i18n, rest, migration
- Lessons with 2+ occurrences get severity UPGRADED
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
| pre-flight-checker | Lessons → Skill | Loads relevant dev lessons as context before generation |
| enr-coherence-checker | Parallel | Run simultaneously for ENR coherence (shares reinforcement loop) |

### Quick Reference: The 8 Golden Rules

| # | Rule | Key Check |
|---|------|-----------|
| 1 | Never modify Axelor core | JAVA-01 |
| 2 | Always form-view + grid-view | VIEW-02 |
| 3 | Use __repo__(Model).CONSTANT | ACT-04 |
| 4 | Name ALL XML elements | VIEW-01 |
| 5 | Generic ENR code | (enr-coherence-checker) |
| 6 | English translation keys | I18N-01 |
| 7 | Test with full gradle command | (pre-commit) |
| 8 | No comments in code | JAVA-10 |
