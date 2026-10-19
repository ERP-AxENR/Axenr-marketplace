Audit and consolidate the lessons in LESSONS-LEARNED.md.

This command is OPTIONAL. The auto-learning is built into solve-ticket (automatic promotion at 3 occurrences). Use this command periodically to review, clean up, and reorganize the knowledge base.

## ARGUMENTS

$ARGUMENTS

Optional. If empty, processes the default LESSONS-LEARNED.md in the marketplace.
If a path is provided, processes that specific file.

## WORKFLOW

### STEP 1 : READ
- Read LESSONS-LEARNED.md from the marketplace
- Read CLAUDE.md from the marketplace
- Count total lessons, promoted lessons, and pending lessons

### STEP 2 : AUDIT
For each lesson:
1. Check if it has reached the promotion threshold (3+ occurrences)
   - If YES and not yet promoted: promote it now
2. Check if a similar lesson already exists (deduplication)
   - If YES: merge the two, combine occurrence counts and ticket lists
3. Check if the lesson contradicts a rule in CLAUDE.md
   - If YES: flag it for review, do not promote
4. Check if the lesson is still relevant (old lessons for fixed issues)
   - If the fix is now in CLAUDE.md as a permanent rule: mark as archived

### STEP 3 : CONSOLIDATE
- Remove exact duplicates
- Merge similar lessons (same error pattern, different tickets)
- Re-number lessons sequentially (LESSON-001, LESSON-002, ...)
- Update the stats section at the top of LESSONS-LEARNED.md

### STEP 4 : PROMOTE
For each lesson with 3+ occurrences and not yet promoted:
- Call knowledge-updater to add the rule to CLAUDE.md
- Mark the lesson as promoted in LESSONS-LEARNED.md

### STEP 5 : REPORT
Display:
- Total lessons: N
- New promotions: N
- Duplicates merged: N
- Archived: N
- Current promotion rate: X%
- List of newly promoted rules

## CRITICAL RULES

- NEVER delete a lesson that has fewer than 3 occurrences (it might recur)
- NEVER modify CLAUDE.md rules that were written by a human (only add auto-learned rules)
- ALWAYS preserve the original ticket references in merged lessons
- ALWAYS update the stats section after consolidation
