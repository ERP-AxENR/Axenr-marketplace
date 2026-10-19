> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3 (bout en bout ; moteur lu dans le code AOP 8.2.3), quelques pièges sur AOP 8.2.x. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Skill: Creating Axelor Data Import Bundles

## Mission

Build, debug and validate a `bind.xml` (csv-inputs / xml-inputs) + CSV/XML/ZIP bundle run through
*Administration > Import Configurations*, for two families of payload:

1. **Metadata** — views, actions, translations deployed to a partner instance without rebuilding the WAR.
2. **Business and reference data** — `Partner`, `TradingName`, `AccountingSituation`, addresses and the
   like, loaded into an existing instance.

Capture the non-obvious gotchas that make imports "succeed" silently while inserting zero rows — **and**
those that make an all-green import produce functionally wrong records.

## When this applies

- Shipping form extensions / custom views / charts / actions / i18n to an instance where you cannot push a Gradle module
- Loading business or reference data (customers, suppliers, trading names, accounting situations) into a live instance
- Versioning content via stable `importId` for idempotent re-imports
- Diagnosing an import that completed cleanly but produced no DB rows
- Diagnosing an import whose counters are all green but whose records are wrong: missing `partnerSeq`,
  empty display name, missing type/currency, records invisible to non-admin profiles, duplicated
  children, orphan rows, silently unresolved relations

> **Importing `Partner`, customers/suppliers, trading names, accounting situations or addresses in
> several passes? Read [import-bundles-partner-case-study.md](import-bundles-partner-case-study.md)
> BEFORE writing the binding.** It carries the multi-pass architecture, the callback semantics and the
> normalisation rules that the generic pitfalls below do not cover.

**When NOT to use:**
- You can ship a Gradle module → ship the module (cleaner versioning, future-proof, restoreAll handles the merge automatically — and, as for a bundle, restart Tomcat immediately after any restoreAll, see P5). Use this skill only when the partner refuses a rebuild.
- The content includes Java code, listeners, or services → must be a module
- Content depends on schema changes (new fields, new tables) → must be a module

## Prerequisites

**Required**
- An Axelor instance where your user can open *Administration > Import Configurations* (create an
  ImportConfiguration, upload a bind file and a data file, run it). The pitfalls below were observed at
  runtime or read in the code, mainly on AOP 8.2 / AOS 9.1; re-test on your version. Do the live test of the
  verification protocol on a **disposable** instance, never first on the target.
- `xmllint` (libxml2-utils) — XSD validation of `bind.xml` (Pattern A, verification step 1).
- `zip` — packing the data ZIP (Pattern D).
- Python 3 with `lxml` (`pip install lxml`) — extracting source XML views into CSV rows and the round-trip
  check (Pattern E, verification step 2).
- The AOP / AOS sources of the **target version** (paths below start at `aop/` = Axelor Open Platform,
  `aos/` = Axelor Open Suite, `axelor-utils/` = the Axelor utils library used by AOS — public repositories
  github.com/axelor/axelor-open-platform, github.com/axelor/axelor-open-suite and
  github.com/axelor/axelor-utils, at the tag of your version), or the equivalent jars. Callback and
  binder behaviour must be read on the version you import on, not assumed from this document.

**Optional**
- A SQL client (`psql`) on the database of a disposable instance — only for the SQL checks of the
  verification protocol (reading back the `xml` column of `meta_view`, the cleanup of `meta_*` rows by
  import id). Without database access, run the same checks from the UI (grids filtered on the import id)
  or from the REST search API.
- The `linting-axelor-views` skill, if you have it: run it on the source view XML before packaging.
  Without it: validate each source view file with `xmllint --noout --schema
  aop/axelor-core/src/main/resources/object-views.xsd <file>.xml` and apply the merged-view rules of
  "See also" (the XSD alone does not check the merged view).

## Pitfall catalog

### P1 — `update="true"` is "UPDATE ONLY", not "upsert"

**Most common silent failure.** Source: `aop/axelor-core/src/main/java/com/axelor/data/csv/CSVBinder.java:196-209`:

```java
} else if (this.query != null) {
  Object bean = JPA.all(...).filter(query).bind(params).fetchOne();
  if (update || bean != null) {
    newBean = false;
    return bean;        // returns NULL when search misses AND update=true
  }
}
// fall through to new instance ONLY if update=false
```

`update="true"` + search returns null → bean = null → row silently skipped (no insert, no exception). Import log shows `Réussi : N / Non vide : 0`.

**Fix:** drop `update="true"` entirely. The AOS-standard pattern uses `search` alone, which gives true upsert: existing row found → updated, no row → inserted. Confirmed in `aos/axelor-account/src/test/resources/data/account-config-input.xml`.

### P2 — `Réussi` is not the success counter, `Non vide` is

Source: `aos/axelor-base/.../listener/ImporterListener.java:66-70`:

```java
public void imported(Model bean) {
  if (bean != null) {
    ++notNull;   // "Non vide"
  }
}
```

- `Total` = rows read from CSV
- `Réussi` = rows that did not throw an exception (includes silent skips)
- `Non vide` = rows where the binder actually produced a non-null bean (the only reliable signal)
- `Anomalies` = exceptions caught (e.g., unique-key violations)

Always check `Non vide` first. If `Non vide = 0` with no Anomalies, suspect P1.

### P3 — `meta_translation` has unique key on `(message_key, language)`

Searching by `self.importId = :importId` will fail with `duplicate key value violates unique constraint "uk_pbctly1brqdvtyvo5tikjuibf"` on any common term already translated by AOS (e.g., Amount, Cost, Period, Reporting…).

**Fix:** search by the natural key `self.key = :key AND self.language = :language`. This gives true upsert against the existing AOS translations. Note: this WILL overwrite the message_value, so only use this for keys you actually own. For shared terms, drop them from the bundle (they're already translated).

### P4 — `<extend><attribute>` replaces, never appends

Source: `aop/axelor-core/src/main/java/com/axelor/meta/loader/ComputedViewXmlProcessor.java:558`:

```java
if (StringUtils.isEmpty(value)) {
  targetElement.removeAttribute(name);
} else {
  targetElement.setAttribute(name, value);   // REPLACES
}
```

If you extend a form with `<extend target="/"><attribute name="onLoad" value="action-mine"/></extend>` and another module (e.g. BTP) already set `onLoad` on the same target, the last-merged extension wins (yours, if your `module` value is unknown to the partner's Gradle resolution — extensions with unknown modules merge LAST). The other module's `onLoad` action chain is silently lost.

**Fix options:**
- Extend the action-group instead (if base form uses one, e.g. `action-business-project-project-group-on-load`)
- Inline visibility logic via `showIf=` Groovy on each panel/field instead of running an action-attrs on form load
- Accept the side-effect if the target attribute is documented unused on the partner's instance

### P5 — Form extensions need `restoreAll` AFTER import

Source: `aop/axelor-core/.../meta/loader/ViewLoader.java:152` (`initialize`), `ViewGenerator.java:142-162` (`findExtensionMetaViews`).

Importing an `extension=true` row into `meta_view` is necessary but not sufficient. The merged "computed" view (the one actually served to the client) is regenerated at boot or via `MetaController.restoreAll`.

The regeneration triggers when the base view's name is in `computedViews` (populated from DB at `ViewLoader.initialize()` from rows where `computed=TRUE`). For views with native AOS extensions (e.g., `business-project-form`), the name is always in the set → restoreAll picks up your imported extension correctly. For pristine base views with no prior extension, your first restoreAll won't trigger the merge — you'd need to manually mark a stub `computed=TRUE` row first.

**Operational step:** add to install notice → AFTER import, run the metadata reload: *Administration >
View Management > All Views* (French UI: *Administration > Gestion des vues > Les Vues*; menu path read
in AOP 8.2.3, an AOS menu may place it elsewhere), toolbar button with the eraser icon, tooltip
**"Restore all…"** (« Tout restaurer… »), which asks "All the customizations will be lost. Are you sure?"
and calls `action-meta-restore-all` → `MetaController.restoreAll` → `ModuleManager.restoreMeta()`. There
is no menu entry named "Reload application configuration" in AOP 8.2.3. **Then restart Tomcat
immediately, before any acceptance test or demo.** Reason: measured on AOP 8.2.2,
the reload leaves about one web thread in ten running under the `admin` identity until the application
server is restarted (10 responses out of 120 answered as `admin` after the reload, 0 out of 60 before) —
an intermittent fault that lets a test pass nine times out of ten. Read in the AOP 8.2.3 code
(12/10/2026): `ModuleManager.restoreMeta()` still runs under `admin`. Never describe this reload as
"without interruption": plan the restart in the installation window. "At boot" above means when a
module is installed for the first time: a plain restart of an instance whose modules are already
installed does not recompute the merged view (`ModuleManager.initialize` loads pending modules only,
read in AOP 8.2.3; a patched extension was not served after a restart, observed on AOP EE 8.2.3), so the
restart does not replace the reload.

### P6 — `xmlId` is unique, `xml` cell stores inner element only

`MetaView.xmlId` and `MetaAction.xmlId` have `@Column(unique = true)`. Two rows with the same `xmlId` value violate the constraint. NULL is allowed and doesn't violate.

The `xml` column stores the **inner element only**, no `<object-views>` wrapper, no `xmlns` declaration. Verify by `SELECT LEFT(xml, 200) FROM meta_view WHERE name = '...' LIMIT 1`. If you serialize with lxml, strip the namespace declarations after `etree.tostring`:

```python
raw = etree.tostring(elem, pretty_print=False, encoding="unicode")
raw = raw.replace(' xmlns="http://axelor.com/xml/ns/object-views"', "")
raw = raw.replace(' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', "")
```

### P7 — Empty m2o column + `<bind search>` creates an EMPTY bean (validated 2026-07-08)

A CSV `<bind to="parent" column="parent_name" search="self.name = :parent_name"/>`
on a row where `parent_name` is empty does NOT skip the bind: the search misses,
the binder instantiates an empty related bean → `ConstraintViolationException`
(name null) on the RELATED entity, and the whole batch rolls back. Symptom in the
log: violations on an entity you didn't think you were importing (e.g. empty
`MetaAction` rows while importing `MetaMenu`).

**Fix:** guard every optional m2o bind with `if`:
`<bind to="action" column="action_name" search="self.name = :action_name" if="action_name"/>`

The `if` only covers the EMPTY cell. A non-empty value that does not exist in the referential takes the
same path (search miss → new empty bean) unless the bind carries `update="true"`: then the miss leaves
the relation null instead (`CSVBinder`, AOP 8.2.3, l. 178-200). Whether the empty bean rolls the batch
back depends on the related entity: it fails on a required field (the `name` above), so do not read
"no violation" as "no empty row created".

### P8 — Same-file parent references are NOT visible to `search`

Within one CSV input, `search` does not see rows persisted earlier in the same
run (no flush before the relational search). A self-referencing hierarchy
(MetaMenu.parent) imported in one file → every child's parent-search misses →
empty parent beans (see P7) → all rows fail. Topological row order does NOT help.

**Fix:** split the hierarchy into one CSV per depth level (`meta-menu-l0.csv`,
`l1`, `l2`…), one `<input>` per file — each input commits before the next starts.

### P9 — XMLBinder (`xml-inputs`) is a TRUE upsert, unlike CSVBinder

`XMLBinder.bind` (aop 8.2, XMLBinder.java:90-101): search miss + `update="true"`
still CREATES the bean (only `create="false"` prevents it). So the P1 trap is
CSV-ONLY. Studio EE module exports ship an `input-config.xml` whose
`update="true"` bindings are safe to reuse as an ImportConfiguration type `xml`.

### P10 — MetaJsonField of a json model needs `model`/`modelField` constants

Importing `MetaJsonField` rows attached to a `MetaJsonModel` (custom model
fields) fails NotNull validation unless `model='com.axelor.meta.db.MetaJsonRecord'`
and `modelField='attrs'` are set — normally done by the studio repository, bypassed
by the importer. In xml-inputs: `<bind to="model" eval="'com.axelor.meta.db.MetaJsonRecord'"/>`
+ `<bind to="modelField" eval="'attrs'"/>`. Also: the Studio EE export
(`exportModule`) omits the `jsonModel` attribute on SOME `<field>` elements of
`custom-models.xml` (observed on json-m2m fields and last-listed models) —
normalize the data first by copying the parent `<model name>` into the missing
`jsonModel` attributes, otherwise those fields import as ORPHANS (jsonModel null)
while the log says `Non vide` = 100%.

### P11 — A green import log does not prove business completeness

`Total = Réussi = Non vide` proves one thing only: the binder produced non-null beans and persisted them.
It proves **nothing** about:

- UI default values (`partnerTypeSelect`, currency, active company…) — those come from `onNew`/`onLoad`
  actions that the CSV importer never runs;
- repository hooks and business callbacks — the CSV importer persists through `JPA.manage`
  (`CSVImporter.importRow`, AOP 8.2.3), **not** through the repository: logic in a repository `save()`
  override is not run, and neither is any `onChange` action or controller. Put that logic in a callback;
- sequences (`partnerSeq`) and persistent display names (`fullName`, `simpleFullName`) — see the case study;
- relations: an optional `<bind search=… update="true">` that finds nothing leaves the relation **null**
  and keeps the log green (without `update="true"` it creates an empty related bean instead, P7);
- children collections: rows may exist but be attached to nothing;
- visibility: a record with an empty `companySet` is invisible to any user scoped to a single company,
  which looks exactly like "the import created nothing".

**Rule: for every business import, write down the expected business postconditions BEFORE running it, then
verify them on representative records** (one simple case, one mixed-role case, one multi-child case, one
deliberately unresolved reference). Never close an import on counters alone.

### P12 — Never call a side-effecting callback once per source role

An entity present in several source files (a customer input **and** a supplier input, an entity listed once
per agency…) is bound once per row. Each row fires the input's `call=` callback. If that callback has side
effects — consuming a sequence, creating children, uploading a file — you pay it as many times as the
entity appears, and, because a search inside the same run does not see rows created earlier in that run
(P8), you may end up with **two records for one entity** instead of one updated record.

**Fix, in order of preference:**

1. Normalise upstream: merge the roles into **one canonical row per entity** (`isCustomer` and `isSupplier`
   flags merged, children aggregated into one column), and put the callback on that single input.
2. If you cannot merge, read the callback source and **prove it is idempotent** before re-running it — then
   split the work into a creation pass and a finalisation pass.

Corollary: a bundle carrying a non-idempotent callback is a **one-shot** artefact. Archive it with its log;
do not re-run it "just to be sure".

### P13 — `csv-inputs`: collection binds only add; `if-empty` protects a filled field

Read in AOP 8.2.3 `CSVBinder.bind` and `CSVBind` (`csv-inputs` only — `xml-inputs` behaves differently, P9):

- A collection column (M2M or O2M, pipe list or `eval`) is bound with `addAll`/`add`: re-importing **adds**
  the listed items and never removes one that is no longer listed. It does not overwrite items set by another
  bundle either. Removing a link needs an explicit operation.
- `if-empty="true"` on a `<bind>` skips it when the found (existing) record already has a value in that field:
  the native way to set a value at creation only — a password, a default, a label the client may have edited
  since. `if="<groovy>"` skips the bind when the expression is false.
- Reminder (P1): `search` without `update` = upsert; the found record is rewritten with the row's values,
  which is how a re-run resets a password.

## Patterns

### Pattern A — Canonical bind.xml shape

```xml
<?xml version="1.0" encoding="UTF-8"?>
<csv-inputs xmlns="http://axelor.com/xml/ns/data-import"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://axelor.com/xml/ns/data-import http://axelor.com/xml/ns/data-import/data-import_7.4.xsd">

  <input file="meta-view.csv" separator=";" type="com.axelor.meta.db.MetaView"
    search="self.importId = :importId"/>

  <input file="meta-action.csv" separator=";" type="com.axelor.meta.db.MetaAction"
    search="self.importId = :importId"/>

  <input file="meta-translation.csv" separator=";" type="com.axelor.meta.db.MetaTranslation"
    search="self.key = :key AND self.language = :language"/>

</csv-inputs>
```

XSD-validate before delivery:
```bash
xmllint --noout --schema /path/to/aop/axelor-core/src/main/resources/data-import.xsd bind.xml
```

### Pattern B — CSV column → Java field auto-mapping

`CSVBinder.autoBind` (line 129+) auto-maps CSV header column names to Java field names via the entity's `Mapper`. **Use Java field names, not DB column names.**

| Entity | CSV headers |
|---|---|
| `com.axelor.meta.db.MetaView` | `importId;name;title;type;priority;model;module;xmlId;extension;xml` |
| `com.axelor.meta.db.MetaAction` | `importId;name;type;model;module;xmlId;xml` |
| `com.axelor.meta.db.MetaTranslation` | `importId;key;message;language` (NOT `message_key`/`message_value`) |

Type coercion: `BooleanAdapter` accepts `true`/`false` (and `0/1/yes/no/y/n/f`). Empty cell → `Boolean.FALSE`. Integer fields auto-coerce from string.

### Pattern C — Stable importId for re-imports

Format: `<bundle-id>:<entity>:<natural-key>[:<discriminator>]`

Examples:
- `dashboard-project:view:business-project-form:dashboard-project-business-project-form` (extension form, discriminator = xmlId)
- `dashboard-project:action:action-dashboard-project-attrs-visibility` (action)
- `dashboard-project:i18n:fr:Bilan d'Affaire` (translation)

This makes v2 deliveries idempotent: same importId → row updated, new importId → new row. Cleanup is trivial: `DELETE FROM meta_* WHERE import_id LIKE 'dashboard-project:%'`.

### Pattern D — Data file as ZIP

`ImporterCSV` accepts a ZIP data file (`Importer.java:177` `isZip()`). Bundle multiple CSVs at root level of the zip (no subfolder). The `bind.xml` references files by name only:

```
data.zip
├── meta-view.csv
├── meta-action.csv
└── meta-translation.csv
```

Pack via:
```bash
zip -j data.zip meta-view.csv meta-action.csv meta-translation.csv
```

`-j` flag is critical — strips paths so files land at zip root.

### Pattern E — Extract source XML to one row per element

Use lxml with `strip_cdata=False, remove_comments=False`:

```python
parser = etree.XMLParser(strip_cdata=False, remove_blank_text=False, remove_comments=False)
tree = etree.parse(path, parser)
for elem in tree.getroot():
    if not isinstance(elem.tag, str):  # skip comments/PIs
        continue
    name = elem.get("name")
    title = elem.get("title") or name
    xml_id = elem.get("id")
    extension = elem.get("extension") == "true"
    xml_body = serialize_element(elem)   # see P6 for namespace strip
    # → emit CSV row
```

Roundtrip-validate each cell:
```python
for r in csv.DictReader(...):
    etree.fromstring(r["xml"].encode("utf-8"))   # must not raise
```

## Reference — Key source files

Paths are relative to the source trees named in Prerequisites (`aop/` = Axelor Open Platform, `aos/` = Axelor Open Suite, `axelor-utils/` = Axelor utils library). Line numbers are indicative and do not match every version (in AOP 8.2.3 they are shifted by a few to about twenty lines): locate the method by name.

| File | What |
|---|---|
| `aop/axelor-core/src/main/resources/data-import.xsd` | XSD for `<csv-inputs>` binding |
| `aop/axelor-core/.../data/csv/CSVImporter.java` | Entry point, transaction handling |
| `aop/axelor-core/.../data/csv/CSVBinder.java:186-218` | `find()` method — the `update` trap lives here |
| `aop/axelor-core/.../data/adapter/BooleanAdapter.java` | true/false coercion rules |
| `aos/axelor-base/.../imports/listener/ImporterListener.java` | The `Total/Réussi/Non vide` counters |
| `aos/axelor-base/.../imports/importer/Importer.java:177` | ZIP data file support |
| `aop/axelor-core/.../meta/loader/ViewLoader.java` | Extension merge trigger on restoreAll |
| `aop/axelor-core/.../meta/loader/ViewGenerator.java:142-162` | `findExtensionMetaViews` — JPA query, ignores Gradle modules |
| `aop/axelor-core/.../meta/loader/ComputedViewXmlProcessor.java:558` | `<extend><attribute>` replace semantics |
| `aos/axelor-account/src/test/resources/data/account-config-input.xml` | AOS-standard upsert pattern (no update attribute) |
| `axelor-utils/src/test/resources/data/meta-actions-input.xml` | Minimal MetaAction example |
| `aos/axelor-base/.../csv/script/ImportPartner.java` | `importPartner` callback — sequence, `setPartnerFullName`, registration-number validation |
| `aos/axelor-account/.../csv/script/ImportPartnerAccount.java` | `importAccountingSituation` callback — creates a NEW situation per company on every call |
| `axelor-utils/.../utils/helpers/ImportHelper.java` | `isValuePresent`, `isRecordPresent`, `checkUniqueConstraint`, `checkSelection` — usable in `check=` |

## Verification protocol

Before declaring the bundle ready for partner delivery:

1. **XSD-validate `bind.xml`** with `xmllint --noout --schema data-import.xsd bind.xml`
2. **Roundtrip every XML cell** in the generated CSVs: parse with `csv.DictReader`, feed each `xml` cell to `etree.fromstring` — none should raise
3. **Test live on local instance**: create ImportConfiguration, upload bind + data, Run, check `Non vide` matches the expected row count (NOT just `Réussi`)
4. **Trigger the metadata reload** (*All Views* grid → **"Restore all…"** button, i.e. restoreAll — see P5) post-import for any `extension="true"` rows, **then restart Tomcat immediately, before any further test** (the reload leaves ~1 web thread in 10 running as `admin` until restart — see P5)
5. **Verify on the actual model**: open the target form → look for your panel/field/dashlet → click drill-downs
6. **Clean up**: `DELETE FROM meta_* WHERE import_id LIKE '<bundle-id>:%'` + restoreAll + immediate Tomcat restart (P5) → confirms reversibility
7. **Document the post-install step in INSTALL.md**: if you forget to tell the partner about restoreAll **and the Tomcat restart that must follow it immediately (P5)**, form extensions appear not to work — or work while some requests silently run as `admin`
8. **Business-data gate** (business/reference imports only — metadata bundles stop at step 7). On
   representative records, in the UI or in SQL, verify:
   - sequence and persistent display names (`partnerSeq`, `fullName`, `simpleFullName`) are populated;
   - fields normally supplied by UI default actions (type, currency, active company) are populated;
   - company scoping (`companySet`) is set — then **re-check with a non-admin profile scoped to that company**;
   - role flags are merged, not split across two records (one mixed customer/supplier record, not two);
   - many-to-many collections actually contain their members (agencies/trading names), not an empty set;
   - child records exist exactly once per business key (e.g. one `AccountingSituation` per `(partner, company)`);
   - references deliberately left unresolved are listed in a rejects/unresolved CSV, not silently null;
   - orphans left by earlier attempts are searched for and reported — never deleted without an explicitly
     authorised scope.
   Any deviation stays in the handover note **even when the log is entirely green**.

## Anti-patterns

| Ne pas faire | Faire |
|---|---|
| Add `update="true"` thinking it enables upsert | Use `search` alone for upsert; AOS pattern |
| Trust `Réussi : N` as success indicator | Check `Non vide : N` |
| Search `meta_translation` by `importId` for common terms | Search by `(key, language)` natural key, or exclude shared terms from bundle |
| Wrap the `<form>`/`<custom>`/`<chart>` in `<object-views>` in the CSV xml cell | Strip wrapper, emit inner element only |
| Use DB column names (`message_key`, `xml_id`) as CSV headers | Use Java field names (`key`, `xmlId`) |
| Ship a bundle for content that has Java code or schema changes | Ship a Gradle module instead |
| Forget the `restoreAll` step in install notice | First line of partner notice after "Run import", immediately followed by "restart Tomcat before any test or demo" (P5) |
| Run `restoreAll` and keep testing or demoing without a restart | Restart Tomcat immediately after the reload: until then ~1 web thread in 10 answers as `admin` (P5) |
| Set `module = <real_existing_gradle_module>` for safety | Use a clear ad-hoc label (`bundle-name`); no AOS job purges by module |
| Skip live test on local instance because "the CSV looks right" | Always run a full create-import-verify-cleanup cycle |
| Close a business import on `Total = Réussi = Non vide` | Verify business postconditions on representative records (P11) |
| Repeat an entity once per role/agency in an input carrying a `call=` callback | One canonical row per entity, roles and children merged (P12) |
| Re-run a bundle whose callback consumes sequences or creates children | Treat it as one-shot; archive it with its log, or prove idempotence first |
| Leave a business record without `companySet` | Bind the company explicitly and re-test with a non-admin profile |
| Reuse one generic `importId` column across several models in the same file | One explicit column per model (`partnerImportId`, `accountingSituationImportId`…) |
| Silently create partial `Account` rows to satisfy a missing external code | Leave the relation null and emit an unresolved-references CSV |
| Re-run a bundle expecting it to remove links, or to keep values edited since | Collections only grow; guard creation-only fields with `if-empty="true"` (P13) |

## See also

- [import-bundles-partner-case-study.md](import-bundles-partner-case-study.md) — multi-pass business-data import (partners, trading names, accounting situations)
- **View XML shipped in a bundle.** Validating the extension file against the object-views XSD checks its
  static structure, not the view resolved after the merge. A bare `<field>` inserted before or after a
  form-level `<panel>` becomes a direct child of `<form>` once merged and fails at view load
  (`UnmarshalException`): wrap it in a `<panel>` (rule recorded after two incidents; not re-tested for
  this export). A `<field>` carrying an inline `<grid>` or `<form>` inside a `<panel>` is not allowed by the XSD (a
  panel field accepts only `hilite` / `tooltip` / `viewer` / `editor` children, read in the object-views XSD of AOP 8.2.3): use
  `<panel-related>` with `grid-view` / `form-view`. After the import, `restoreAll` and the immediate Tomcat
  restart (P5), open the merged view on a disposable instance.
- **`<custom>` views** (React JSX templates, SQL datasets) fail silently at runtime — an empty value, an
  ignored style, a non-clickable element, with no build error and no console warning. This skill only
  covers how to ship them (one `meta_view` row); test each custom view on a disposable instance.

