# Measured estimate and delivery

## 1. Estimate

Two figures, kept apart:

- **Measured agent time**: real timestamps (start and end of each flow, number of rebuild-start cycles, build times),
  read from the logs when they are written. Not converted into "equivalent human days", never dated in the future.
  Reference point (real project, large model): a connector port from AOS 8.5 to 9.1 in about 45 minutes; four flows
  built, 62 tests, 44 runs checked in the database, in 2 h 16. Estimates made at human pace for the same work no longer
  apply to that part.
- **Human remainder**, task by task, only what needs a person: code review, validation on the real third-party service,
  customer decisions and settings, customer acceptance, go-live. Each task names who and gives a range in days, marked
  as an estimate.

When what was announced to the customer ("native flow", "configuration") differs from the actual code, present it flow by
flow, separating real under-estimation, features never estimated, and internal tooling costs (version port). A single
"X days against Y" total is misleading.

## 2. Deliver

- **Access first**: role on the connector repository (Developer to push), forking allowed or not. Without access: an MR
  request to a developer of the repository, with the patch series (`git format-patch base..HEAD --stdout`), the command to
  apply it, and a check that applying it reproduces the branch exactly.
- **MR in English**, short title (the repository convention: conventional commits, or a ticket prefix on a customer
  project), short description: what changes, what was checked and how, what was not. Code comments only where they
  explain a "why".
- **Split**: version port first, then one commit or MR per flow; a single MR of several thousand lines is the real
  bottleneck of the review.
- **Module shared between customers**: list each behaviour change for the other customers in the MR; the target branch is
  decided with the module maintainer.
- **Deployment**: the module is added to the customer's application dependencies, and the application is rebuilt.
- Secrets (API keys, tokens, ticketing keys) never go through the agent or into a file of the deliverable.

## 3. Final deliverable

1. Summary for the decision owner (10 lines, business language).
2. Per flow: sourced need, third-party routes, mapping, rules, edge cases, settings, proofs (tests with their output,
   database state).
3. Decisions: each with options, consequences, recommendation, status (provisional, open, settled by whom and when).
4. Estimate: measured agent time, human remainder per task.
5. To confirm on the real third-party service, with the fallback the code applies.
6. Not verified, and where it was looked for.
7. How to replay: start command of the emulator, test command, check command, all runnable from the deliverable folder.
