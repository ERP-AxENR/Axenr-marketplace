Resolve the following ticket using the ticket-solver-agent workflow.

## ARGUMENTS

$ARGUMENTS

Expected format: `<project> <branch> #<number> | <title> | <description>`

Examples:
- `axenr-app wip #750 | Add estimated power field | decimal field on Opportunity, calculated from numberOfModules * 400 / 1000`
- `axenr-app dev #733 | Fix project start date | Use current date instead of null in ProjectService`
- `axenr-mobile axenr #801 | Add timesheet duration filter | Filter by duration on TimesheetListScreen`

## PARSING

Parse $ARGUMENTS to extract:
1. **project**: first word (axenr-app or axenr-mobile)
2. **branch**: second word (dev, wip, axenr, or other)
3. **ticket_number**: the #XXX part
4. **title**: text between first and second |
5. **description**: text after second |

If any required field is missing, ASK the developer. Do not guess.

## DELEGATION

Pass ALL parsed fields to the **ticket-solver-agent**. The agent handles the ENTIRE workflow (9 phases) autonomously with its own gate system.

DO NOT describe phases, steps, or checkpoints here. DO NOT repeat any phase logic. The agent is the SINGLE SOURCE OF TRUTH for the workflow.
