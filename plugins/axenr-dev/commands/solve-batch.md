Resolve multiple tickets in parallel using the ticket-solver-agent workflow.

## ARGUMENTS

$ARGUMENTS

Expected format: `<project> <branch> #<n1>|<title1>|<desc1> ,, #<n2>|<title2>|<desc2>`

The separator between tickets is ` ,, ` (space-comma-comma-space).

Maximum 2 tickets in parallel.

Examples:
- `axenr-app wip #750|Add power field|decimal on Opportunity ,, #751|Add panel notes|notes panel on SaleOrder form`
- `axenr-mobile axenr #801|Duration filter|filter TimesheetListScreen ,, #802|Fix crash|Android navigation crash`

## PARSING

Parse $ARGUMENTS to extract:
1. **project**: first word (shared for all tickets)
2. **branch**: second word (shared for all tickets)
3. **tickets**: split by ` ,, ` then parse each as `#number|title|description`

If more than 2 tickets: process only the first 2, inform the developer.
If any required field is missing: ASK the developer.

## WORKFLOW

### STEP 1 : GIT PULL (once for all tickets)
- If axenr-app: `git pull origin <branch>` in modules/axenr THEN in axenr-app
- If axenr-mobile: `git pull origin axenr`

### STEP 2 : PRE-FLIGHT (once for all tickets)
- Call pre-flight-checker to load shared context
- Read LESSONS-LEARNED.md, CLAUDE.md, versions, i18n

### STEP 3 : PARALLEL PROCESSING
- Launch 2 ticket-solver-agent instances in parallel using the Task tool
- Each instance receives:
  - The shared context from pre-flight
  - Its own ticket (number, title, description)
- Each instance runs PHASES 3, 3.5, 4, 5, 6, 7 independently (toutes les phases, dans l'ordre, avec checkpoints)
- CRITICAL : chaque instance DOIT executer PHASE 3.5 (analyse critique du code existant) - elle ne peut PAS etre sautee

### STEP 4 : CONSOLIDATION
- Collect results from both instances
- Merge new lessons (avoid duplicates in LESSONS-LEARNED.md)
- Generate combined report:
  - Per-ticket summary
  - Combined TEST PLAN
  - Combined file list
  - Combined version compatibility report
- If either ticket failed: show the error report for that ticket

## CRITICAL RULES

- Same rules as solve-ticket apply to each parallel instance
- Git pull happens ONCE at the start, not per ticket
- Pre-flight happens ONCE, shared between tickets
- Lessons are written sequentially (not in parallel) to avoid file conflicts
- Maximum 2 tickets in parallel to avoid overload
