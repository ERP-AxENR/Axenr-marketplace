> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 8.5.23 et 9.0.13 (callbacks lus dans le code) et AOP 8.2 (binder observé au runtime). AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Reference — Multi-pass business-data import (partners, trading names, accounting situations)

Anonymised case study. Field evidence comes from one real migration of customers and suppliers into a
running instance; **all client identifiers, volumes, company codes and record values below are invented
placeholders**.

**Version scope.** Callback behaviour was read in the AOS sources at tag `v8.5.23` and re-checked at
`v9.0.13` — identical in both. Binder behaviour marked "observed" comes from a runtime on **AOP 8.2**;
it is an observation on that runtime, not a universal truth. Re-test on your target version before
relying on it.

Read this before writing the binding when the payload is `Partner`, customers/suppliers, `TradingName`,
`AccountingSituation` or addresses — i.e. whenever the import needs more than one pass.

---

## 1. Real failure modes

Each of these produced an import log that a reader would have called successful.

### 1.1 `update="true"` on a root CSV input = "update only"

On a root `<input>`, `update="true"` means *update only*. Search misses → the binder returns `null` →
the row is skipped with **no insert and no exception**. The row still counts in `Réussi`.

Signature: a pass with `Réussi = N` and `Non vide = 0`. See P1 in `import-bundles-classic.md`.

This does **not** apply to a relational `<bind … update="true">` inside an input — there the attribute is
about updating the found related record, and it is a legitimate pattern.

### 1.2 Repeated rows used to express multiple children, replayed as multiple child records

A source file that repeats a partner once per agency is a *presentation* of a one-to-many, not a set of
distinct entities. Feeding it unchanged to a second `<input>` targeting a child entity replays one child
per source row.

Observed consequence: the first occurrence of each key created the child, every further occurrence
attempted a second insert with the same `import_id` and was rejected by the unique constraint
(`duplicate key value violates unique constraint … Key (import_id)=(…) already exists`). The rejected
rows were exactly the surplus agency occurrences.

### 1.3 One generic `importId` column reused across models

`CSVBinder.autoBind` maps a CSV header to any same-named field on the target model. A column named
`importId`, left unbound in a second input targeting a different model, is **auto-bound to that model's
`importId`**. The child then inherits the parent's identifier — collisions, duplicates, or orphans.

**Rule:** one explicit column per model — `partnerImportId`, `tradingNameImportId`,
`accountingSituationImportId` — and bind each one explicitly.

### 1.4 Missing `Partner.companySet` = invisible partners

Nothing in a `Partner` CSV forces a company. With AOS multi-company filtering, a partner with an empty
`companySet` is invisible to any user scoped to a single company — indistinguishable, from the business
side, from "the import created nothing". An admin sees the rows; the end user does not.

Bind the company explicitly and re-verify with a non-admin profile.

### 1.5 Delimited CSV value bound directly to a many-to-many — **observed on AOP 8.2**

Binding a delimited cell straight to a m2m collection produced a nested-list parameter and a Hibernate
type error of the shape:

```text
Parameter value [[COMPANY_CODE]] did not match expected type … (code)
```

`IN (:param)` and `IN :param` both failed on that runtime. What worked there, for a **small and stable**
reference set, was one guarded constant search per member:

```xml
<bind column="tradingNameImportIds" to="tradingNameSet"
      search="self.importId = 'bundle:trading-name:north'"
      if="tradingNameImportIds != null &amp;&amp; tradingNameImportIds.contains('bundle:trading-name:north')"/>
<bind column="tradingNameImportIds" to="tradingNameSet"
      search="self.importId = 'bundle:trading-name:south'"
      if="tradingNameImportIds != null &amp;&amp; tradingNameImportIds.contains('bundle:trading-name:south')"/>
```

This is a workaround for a closed, small referential, **not** a general rule: it hard-codes every member
in the binding. For an evolving referential, prefer a dedicated association pass after the parents are
committed — and test the chosen pattern on your target version first.

### 1.6 A corrected import can still leave the records functionally empty

A second attempt inserted every partner (`Total = Réussi = Non vide`, zero anomalies) and still left
`partnerTypeSelect`, currency, `partnerSeq`, `fullName` and `simpleFullName` empty — because neither the
UI default actions nor any callback had run. See §2 and §3.

### 1.7 An optional relational search that misses: null relation only with `update="true"`

`<bind to="customerAccount" search="self.code = :code" if="code" update="true"/>` on a code that does not
exist as an `Account` for that company binds nothing. No error, no anomaly, relation null, log green.

Without `update="true"` on the bind, the same miss does **not** leave the relation null: the binder
instantiates an empty related bean (`CSVBinder`, AOP 8.2.3, l. 178-200: the found bean is returned only
`if (update || bean != null)`, otherwise a new instance) — see P7 in `import-bundles-classic.md` for what follows.

Decide explicitly: fail the row with a `check=`, or leave it null **and emit an unresolved-references CSV**.

### 1.8 Registration number, geolocation and address roles stay incomplete

A technically successful import leaves these empty unless they are bound explicitly or produced by a
callback whose behaviour you have read. Do not expect a UI `onChange` to fill them.

---

## 2. Verified callback behaviour — `ImportPartner:importPartner`

`com.axelor.csv.script.ImportPartner:importPartner`, read at **AOS v8.5.23 and v9.0.13** (identical):

1. **Sequence** — requests a `partnerSeq` from `SequenceService` **only if**
   `partner.getPartnerSeq() == null` **and** `AppBase.generatePartnerSequence` is enabled.
2. **Display names** — calls `PartnerService.setPartnerFullName(partner)`.
3. **Registration number** — resolves a `RegistrationNumberValidator` and, when the partner carries a
   `registrationCode`, calls `setRegistrationCodeValidationValues(partner)`.
4. **Picture** — uploads `picture_fileName` resolved against `__path__`, when present.

Two consequences that matter:

- **`Partner.fullName` and `Partner.simpleFullName` are ordinary persistent columns, not computed model
  expressions.** Nothing recomputes them for you. An import that skips this callback and does not bind
  them explicitly leaves partners with empty display names everywhere they are referenced.
- **The sequence guard is on `partnerSeq == null`, not on "new bean".** So:
  - re-running the bundle against a row the `search` **finds**, and whose `partnerSeq` is already set,
    does **not** consume a new sequence value;
  - but every row that lands on a **new** bean does. Two rows for the same entity in one run — a customer
    input and a supplier input — produce two partners with two sequence values, because a search inside
    the same run does not see the row created by the earlier input (P8).

  Do not phrase this as "the callback burns a sequence on every call" — that is false for an update pass.
  Phrase it as: **one canonical row per entity, or you get one partner per row.** Treat a bundle that
  creates partners as one-shot on a given database state, and archive it with its log.

---

## 3. UI default values are not applied by the importer

`partnerTypeSelect`, currency, active company and similar fields are populated by `onNew`/`onLoad` UI
actions. The CSV importer never runs them.

Every required or business-significant value must be either:

- bound explicitly — `<bind to="partnerTypeSelect" eval="1"/>`, `<bind column="currencyCodeISO"
  to="currency" search="self.codeISO = :currencyCodeISO" update="true"/>` — or
- produced by a callback whose create/update behaviour you have **read in the sources** for the version
  you are importing on.

---

## 4. Accounting situations — the AOS callback is not an upsert

`com.axelor.csv.script.ImportPartnerAccount:importAccountingSituation`, read at **AOS v8.5.23**, iterates
`partner.getCompanySet()` and, for every company, executes `new AccountingSituation()`, sets partner,
company and `vatSystemSelect`, resolves the customer/supplier accounts by code, and appends the new
situation to `partner.getAccountingSituationList()`.

There is **no lookup of an existing situation**. Calling it twice for the same partner creates two
situations for the same company. It is also wrapped in a `catch (Exception)` that only prints the stack
trace — a missing `customerAccount_code` value throws inside, is swallowed, and the import log stays green
with no situation created at all.

**Use a separate import searched on the business key instead:**

```xml
<input file="03-accounting-situations.csv" separator=";"
       type="com.axelor.apps.account.db.AccountingSituation"
       search="self.partner.importId = :partnerImportId AND self.company.code = :companyCode">
  <bind column="accountingSituationImportId" to="importId"/>
  <bind column="partnerImportId" to="partner"
        search="self.importId = :partnerImportId" update="true"
        check="com.axelor.utils.helpers.ImportHelper.isRecordPresent('com.axelor.apps.base.db.Partner','importId',partnerImportId)"
        check-message="Partner not found"/>
  <bind column="companyCode" to="company"
        search="self.code = :companyCode" update="true"
        check="com.axelor.utils.helpers.ImportHelper.isRecordPresent('com.axelor.apps.base.db.Company','code',companyCode)"
        check-message="Target company not found"/>
  <bind to="vatSystemSelect" eval="1"/>
</input>
```

Bind `partner`, `company`, the situation's **own** `importId` and, when the business expects it,
`vatSystemSelect`.

**Limit of this key, state it in the handover:** it guarantees no second *valid* situation for the same
`(partner, company)`. It does **not** match, repair or clean an older orphan row whose `partner` is null —
such a row satisfies neither branch of the search and survives untouched.

---

## 5. Normalisation before binding

Do this in the generator script, not in the binding:

- **one canonical row per entity** — the merge key is the business key, not the source file;
- **merge the role flags** — an entity present in both the customer and the supplier source becomes a
  single row with `isCustomer` and `isSupplier` both true;
- **aggregate children into one column** — agencies/trading names collapsed into one delimited cell on the
  canonical row, never one row per child;
- **distinct id columns per model** — `partnerImportId`, `tradingNameImportId`,
  `accountingSituationImportId` (§1.3);
- **separate CSVs for rejects and unresolved references** — rows missing a mandatory business key, and
  codes that have no counterpart in the target instance, leave the importable set and stay traceable;
- **an entity must appear exactly once in any input carrying a side-effecting callback** (§2, P12).

Arithmetic sanity check, with invented figures: 120 customer rows + 60 supplier rows sharing 10 entities
must yield **170** canonical partners, not 180. Assert this in the generator and again after the import.

---

## 6. Order of dependent imports

1. **Stable referentials** — trading names, and any lookup the partners point at. Give them stable
   `importId` values first; search them afterwards by `importId`, never by `name` (case, renaming,
   homonyms).
2. **Canonical partners** — one row per entity, roles merged, children aggregated, company bound.
3. **Accounting situations** — searched on `(partner, company)` (§4).
4. **`PartnerAddress`** — a later import, after the partners are committed.
5. **`partnerAddressList`, then `mainAddress`** — only once the addresses are committed.

Each `<input>` commits before the next one starts; a `search` never sees rows created earlier in the same
input (P8). That is why the order above is a sequence of inputs, not an ordering of rows.

**Registration number:** import the concatenated value explicitly (e.g. SIREN + NIC for a French SIRET) or
call a service you have read. Do not assume a UI `onChange` will build it.
**Geolocation:** identify the persistent model and field, then bind them explicitly.
Apply the same normalisation and the same sequencing to the supplier source as to the customer source.

---

## 7. External accounts — do not create them silently

Before binding a customer/supplier account carried as an external code from the legacy system:

1. **Decide the semantics** of the external code — is it a general account, an auxiliary account, or just
   an external reference to keep for traceability?
2. **Verify it exists** as an `Account` for the target company.
3. **Distinguish** general account, auxiliary account and external reference — they are not
   interchangeable, and the legacy code often encodes a different concept.
4. **Choose one behaviour explicitly:** fail the row on absence with a `check=`, or leave the relation
   unbound and emit an unresolved-references CSV.

Never create partial `Account` rows to make the binding resolve. An invented chart of accounts is worse
than a null relation.

---

## 8. Validation gates

Run all of these before declaring the import done.

**On the bundle, before running it**

- XSD-validate the binding (`xmllint --noout --schema data-import.xsd bind.xml`);
- list the ZIP contents and assert every CSV is at the **root** (`zip -j`);
- assert `count(canonical partners) == |customer ids ∪ supplier ids|`;
- assert uniqueness of the entity key in **every input carrying a callback**;
- assert uniqueness of `(partner, company)` in the situations file;
- compare row counts before/after generation.

**On the run**

- log the ImportConfiguration id, ImportHistory id, timestamp, file names and the four counters;
- require `Non vide` to equal the expected volume **per pass**, not just overall.

**On the records, in the UI or in SQL**

- a customer-only entity, a supplier-only entity, a **mixed** entity, a **multi-child** entity, and a
  deliberately unresolved reference — check each one individually;
- per record: sequence, `fullName`/`simpleFullName`, type, currency, company, children/agencies, payment
  mode, accounting situation, registration number, geolocation, address roles;
- **re-check with a non-admin profile scoped to the target company** whenever visibility is in play;
- search for orphans left by earlier attempts and report them.

---

## 9. Stop conditions

- **Never re-run a bundle carrying a callback** without having read what that callback does to sequences
  and children on the current database state.
- **Never delete orphans** without a proven scope and an explicit authorisation. An import that
  reconciles on a business key does not clean rows that fail that key.
- **Keep every visible business deviation in the handover note, even when the log is entirely green.**
  An unresolved account, an empty geolocation, a partner without a registration number: these are results,
  not noise.
