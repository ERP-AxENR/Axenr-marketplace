# Delegating: who does what, and the execution prompt

## 1. Split by model size

Framing makes the quality; execution delegates well once it is framed. Observed on a real project: the builder (large
model, maximum effort) built four flows in 2 h 16; the errors it did not see (AOS versions forced by its test settings, a
customer name in the code, an end time dated in the future) were caught by the coordinator's **review**, not by the
builder. In a with/without trial of this skill (two cases, blind grading), a mid-size model met 95 % of the criteria with
the skill against 68 % without, for the same time and cost.

| Work | Model | Why |
|---|---|---|
| Flow sheets, vehicle choice, decisions, work split | coordinator (large model) | judgment, business consequences, dialogue with the owner |
| Reading an existing connector, verdict per flow | large or mid-size | long code reading, verdicts proven by `file:line` |
| One route contract from one doc page; transfer objects; mapping rows; emulator data sets; database expectation files | small model, one batch per agent | bounded units, fixed input and output, mechanically checkable |
| Building one flow (tests, code, emulator, environment run, database proof) | mid-size or large | long iterations, runtime diagnosis |
| Adversarial review of the deliverable, re-check of the figures | large model with a fresh context | sees what the builder no longer sees |

Workspace rules usually apply on top: an explicit model for each sub-agent, a cap on simultaneous agents, one agent per
git working tree, one agent driving an environment at a time.

## 2. Cutting work for smaller models

A unit delegated to a small model has one input (one doc page, one list of fields), an exact output format (JSON or
table), and a check the coordinator runs afterwards (a script rather than eyeballing). Examples:
- "Read this doc page and return the route contract in format X; a field absent from the page gets `"source": null`";
- "For these 12 fields, write the mapping rows; each row cites the URL and the AOS `file:line` given";
- "Write the `edge` data sets of the emulator for these 6 edge cases, in the format of the existing scenario".

The coordinator assembles, checks with scripts, and keeps the decisions.

## 3. Execution prompt template (one flow or a batch of flows)

Blocks that made the difference on real work:

```
<instructions_for_use> Files to read first (framing, mapping, existing report, code rules, environment notes). Paths to
check; if one is missing, say so at the top of the deliverable and substitute nothing. </instructions_for_use>
<mission> Specify AND build autonomously flow(s) X: mapping, code, tests, environment run, database proof. </mission>
<scope> Flows in priority order; what is out of scope, and why. </scope>
<allowed_actions> Writes only in: <working tree>, <tools folder>, <deliverables folder>, environment <name> and its
database. No commit, no push, no other environment; no `gradlew --stop`; no build while the application runs. No access
to the real service: contract = public docs cited by URL; report "validated against the emulator", never "validated on". </allowed_actions>
<stakes> What the deliverable commits (fixed price, cost, customer); the unrecoverable error = claiming a flow works on the
real service, or inventing a field. </stakes>
<decisions> Arbitration file; non-blocking = recommended default as a setting, marked "provisional"; blocking = stop and
hand back 2-4 options in business language, grouped. </decisions>
<sources> Status of each source: established fact (dated) / hypothesis to re-check. Build and deployment recipe. </sources>
<method> Framing → mapping → emulator (with request validation) → tests first → environment → database check → fix →
next flow; replay all flows at the end. </method>
<resources_and_pitfalls> Free memory, how to stop processes (pgrep then kill), guard-rails, useful logs. </resources_and_pitfalls>
<false_positives> Decisions already taken, facts already proven: not to be reported again. </false_positives>
<done_when> For each flow: sourced mapping, tests green with their output pasted, expected objects IN THE DATABASE (not a
counter), edge cases, measured agent time and human remainder; deliverable runnable from its own folder. Do not stop
before, unless handing back on a blocking decision, saying exactly where the work stands. </done_when>
<deliverables> Exact paths: specification, decisions, patch, replayable tools. Final answer of 8 lines at most. </deliverables>
<reminder> The 3-4 critical instructions, repeated. </reminder>
```

During execution, follow progress through the files the agent writes (logs, test reports), not its transcript. On
hand-back, re-check the key figures (test counts, timestamps, environment state, database objects) before reporting them.
