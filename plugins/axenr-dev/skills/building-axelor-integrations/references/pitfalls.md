# Pitfalls met on real work

Each line cost time at least once. Two real connector projects, both on AOS 9.1.7: the first on AOP EE 8.2.3
(2026-10-13), the second on an AOP EE 8.2.4 build of 2026-09-21 (2026-10-14). The rows on the duplicated cart, the
`502` refusal, the tracking run stopped by a `404`, the polling order, the reused third-party number, the fee line, the
`files()` jar, `joins can have at most 32767 columns`, the RESTEasy 400 and the metadata that is not reloaded were
established on the second project; the project of origin of the other rows is not recorded. Both connectors were run
against an emulator, never against the real third-party service.

## Connector code

| Symptom | Cause | Remedy |
|---|---|---|
| Batch "successful" with 0 item while the tool refused the read | a 4xx answer treated as success, the error body read as an empty list | any 4xx/5xx raises a named error; only 429 goes to the retry loop |
| Batch frozen forever | HTTP client without timeouts, silent server | connect and read timeouts (e.g. 10 s / 60 s), tested with `hang` in the emulator |
| Axelor data erased by the sync | empty or hidden third-party field copied as is | an empty field does not erase, unless a written decision says so |
| Item skipped and nobody knows | unmatched reference (establishment, project, employee) skipped silently or replaced by a default | named error per item and a line in the batch summary |
| Archived or closed objects pushed to the tool | no filter on the Axelor state | configurable filter, archived excluded by default |
| Accounts created with a guessable password, or a secret stored in clear | password derived from the e-mail, or a secret kept in clear | never derive a password from the e-mail and never store a secret in clear; check this point in any connector taken over (random hashed password via `AuthService.encrypt`, change forced at first login) |
| Record refused by AOS validation | decimal precision (duration with 2 decimals refused) | round to the precision of the AOS field |
| Accounting entry refused | journal and functional origin inconsistent | journal as a setting, "payment" origin for a payment entry |
| Analytic distribution at 0 | computed before amounts and date | compute after |
| Values tuned for another customer | axis numbers, statuses, codes hard-coded | settings, default = existing behaviour |
| Customer name in the code or tests of a shared module | habit of the current project | no customer name in a shared module, tests included (`example.<tool>.net`) |
| Emulator accepts what the real service refuses | happy-path emulator | validate required fields and transitions as documented (e.g. cancellation requires a reason) |
| Same cart imported twice from two browser tabs | duplicate check on a hash of the whole message, which includes the session token | fingerprint the business content only (lines, quantities, prices, units) |
| A documented refusal treated as "outcome unknown" (blocked resend, needless checks) | every 5xx on a write taken as "maybe processed" | read the error page of the docs: e.g. a 502 "account authentication error" is a refusal; keep "unknown" for timeouts and undocumented 5xx |
| The whole tracking run stops on one object | a 404 on one record raised as a batch error | per-object 404 = message on that object, the run goes on; quota or 5xx still stop it |
| Polling "by number" never reaches some records | fixed order with a per-run cap | least recently polled first, so every record gets its turn |
| Tracking updates the wrong Axelor record | match on the third-party number alone; numbers reused (emulator restarted, test numbers met again in production) | match the third-party number AND our own reference echoed back |
| A fee line (e.g. WEEE) shows up in the receipt | the company receives services (`hasInSmForNonStorableProduct`) | flag the fee product as shipping cost (`isShippingCostsProduct`): AOS leaves it out of receipts, no code |

## Build and environment

| Symptom | Cause | Remedy |
|---|---|---|
| Context fails, `AnnotationException … mappedBy … does not exist in the target entity` | module jar dropped into a built WAR: the application's merged entity class hides the extension | publish the module, rebuild the application with it |
| Extended entity without its new fields after a rebuild | application code generation stayed UP-TO-DATE | `clean war` |
| The module forces an AOS version on the application | AOS dependencies pinned in the module for a test | no AOS pinning in the delivered module |
| Does not compile on AOS 9 | `javax.ws.rs` | `jakarta.ws.rs` (the only code line changed on a real 8.5 → 9.1 port) |
| `spotlessJavaCheck` fails after an import change | import order | `spotlessApply`, then check again |
| Application killed without a trace | `gradlew --stop`, out of memory, another session freeing a port | avoid `--stop`; check free memory before a build; do not build and run when memory is short |
| EE licence inactive, error 1020 or 1052 on a cloned database | cloned licence row, certificate missing in the new attachments folder | delete the row (after a backup) and copy `certificate.crt` before the first start |
| Extended entities lack the fields of a module added as a jar | `implementation files("x.jar")` is not read as an Axelor module by the application code generation | republish the jar in a recipe-local Maven repository (`libs/m2` + `.pom`); check with `javap -p` on `WEB-INF/classes` |
| `joins can have at most 32767 columns` after calling an AOS service | the service cleared the persistence context (e.g. `createStockMoveFromPurchaseOrder`); saving a detached entity merges the whole cascaded graph | reload with `find(id)` every entity held across an AOS service call |
| An HTML error page of a module endpoint shows raw markup | RESTEasy escapes a `text/html` entity sent with status 400 | answer 422 (or 409, 410) |
| New views or translations missing after a redeploy | metadata of an already installed module are not reloaded at startup | surgical reload: delete the module row in `meta_module` and its `meta_module_depends` (after a backup), then start; never restore-all. This restart also replays the data-init of that module (AOP EE 8.2.4, `ModuleManager.installOne`: the data-init is loaded for a module that is not installed): a badly bound data-init creates duplicates or empty rows at every replay |
| Start refused although memory is enough | the environment tooling of the workspace, if it has some, caps the number of running environments (e.g. 2), sometimes held by an environment restarted by mistake | ask its owner to stop it; never bypass the cap |

## Tooling and delivery

| Symptom | Cause | Remedy |
|---|---|---|
| The shell dies when stopping the emulator | `pkill -f <pattern>` also kills the shell whose command line contains the pattern | `pgrep -f "^python3 -I .*mock_api.py"`, then `kill <pid>` |
| A "wait while the process runs" never ends | `while pgrep -f "<pattern>"` finds itself: its own command line contains the pattern | wait for an end-marker file, or anchor the pattern on the awaited command (`^python3 …`) |
| A command refused in a restricted shell | the shell allows commands by their first word; `cd x && python3 …` starts with `cd` | absolute paths in a single command |
| Emulator frozen for 13 minutes | lock held during a network wait | `scripts/mock_api.py` (re-entrant lock, never held while waiting) |
| Deliverable emulator does not start elsewhere | scenario written for a script left outside the deliverable | copy `mock_api.py` into the deliverable, write the start command, run the tests from there |
| Push refused: "make sure you have the correct access rights" | Reporter role on the repository, forking disabled | check access during the inventory (`git push --dry-run`, project members); otherwise an MR request to a repository developer, with the patch series |
| `glab` answers 401 or creates nothing | run outside the repository: default host gitlab.com | `glab api --hostname <git server> …` |
| `git am` fails on CSV files | CRLF line endings in translation files | `git am --keep-cr`; check the resulting tree equals the branch |
| A "measured" time that has not happened yet | the end of the writing was dated in advance | timestamp at the moment of writing; nothing dated in the future |
| Times off by two hours | files and logs in UTC, database and people in local time | write the time zone next to every time |
