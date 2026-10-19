# Framing the flows and choosing the vehicle

## Contents
1. Flow sheet (questions to answer)
2. What the owner decides, what the agent looks up
3. Choosing the vehicle
4. Inventory before writing code

## 1. Flow sheet

One sheet per flow, filled before reading the third-party docs. Each answer carries its source (requirements, minutes,
ticket, mail, dated decision); a missing answer becomes a question, not a silent assumption.

| Topic | Questions |
|---|---|
| Direction and master | Which side owns the data? Direction (tool → Axelor, Axelor → tool, both)? What if both sides change the same record? |
| Trigger | Scheduled (frequency, time window), event-driven (webhook, button, status change), manual? |
| Scope | Which objects, which statuses (e.g. only "approved"), which companies, establishments or branches, how much history (initial load, depth)? |
| Matching key | How a record on one side finds the other: third-party id stored in Axelor, functional code, e-mail? What to do with an unmatched record (create, report, ignore)? |
| Lifecycle | Creation, update, deletion or cancellation, archiving: which ones propagate? Does an empty third-party field erase Axelor data? |
| Effects in Axelor | Does the flow trigger an AOS workflow (validation, counters, e-mails, accounting entries) or drop read-only data? |
| Volume and quotas | Objects per run? API quota (requests per minute, shared with other integrations)? |
| Errors and retries | What does the user see when one item fails? Does the next run pick it up? Does a replay create a duplicate? |
| Security | Authentication (key, OAuth), rights of the key, personal data carried, where the secret lives? |
| Test environment | Is there a sandbox, a test key, a test data set? If not, an emulator (the default). |
| Acceptance | Who accepts it, on which data set, with which observable criterion? |
| Existing estimate | What was promised or estimated to the customer, and where (grid, ticket, offer). A gap between "native" in the offer and the actual code is a fact to raise early. |

For a file flow, add: format and version (e.g. CAMT.053, CFONB 120, CSV layout), encoding and separator, how the file
arrives (upload, SFTP, mail), and the controls the native import applies (opening and closing balance lines, signs,
continuity between statements, duplicates).

## 2. What the owner decides, what the agent looks up

- **The agent looks up**: what the third-party docs say, what the code does (existing connector, AOS, EE modules), what
  tickets and minutes contain. A question whose answer can be found is not asked.
- **The owner decides**: scope, master data, what happens to unmatched records, who bears which cost, the
  implementation path when two paths hold, delivery into a module shared with other customers.
- A non-blocking question (the code can make it a setting, default = existing behaviour) moves forward on a
  recommendation marked "provisional". A blocking question (another answer would throw work away) stops the work:
  options with consequences, a recommendation, then wait.

## 3. Choosing the vehicle

Present at least two options with their consequences. Standard features come before custom code.

| Vehicle | When | Limits |
|---|---|---|
| Native AOS import (CSV/XML import configuration, EE spreadsheet import) | one-off or periodic files, reference data, initial load | no rich business logic, no API call |
| Native accounting and banking formats (FEC import and export, bank statement import CFONB 120 / CAMT.053 / CSV) | accounting entries, statements, exchanges with an accounting firm | the third-party file often has to be converted to the expected format |
| n8n or another orchestrator | API-to-API orchestration without Java, simple transformation | AOS logic (workflows, entries) out of reach; separate monitoring |
| Studio / BPM web service connector | a simple call triggered by an Axelor event | paging, retries, quotas handled poorly |
| Java connector module (AOS batches) | recurring synchronisation, business rules, AOS objects created with their effects | development, review, version upgrades |

Check whether a connector or a standard module already exists (Git server search by the tool's name, the Axelor module
catalogue): it often does, sometimes built for another customer. Its existence does not prove it covers the flows; the
answer is in its code, flow by flow.

## 4. Inventory before writing code

1. Existing connector: repository, branches, AOS version of each branch, last commit, contributors, original customer
   (hard-coded values tuned for it: analytic axes, statuses, codes).
2. For each flow of the sheet: what the code does (third-party route called, fields read and written, AOS objects
   created, filters, matching key, error handling), with `file:line`. Verdict covered / partial / missing.
3. Compatibility with the target AOS version: each class, method, domain field and view extended, checked against that
   version's sources. Compiling settles it faster than reading (see `environment-and-proof.md`).
4. Standard AOS / EE features that would reduce development (existing object, native import, existing screen).
