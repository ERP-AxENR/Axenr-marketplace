# Third-party contract and emulator

## Contents
1. Per-route contract from the public documentation
2. Field-by-field mapping
3. Emulator: what it has to do
4. What the emulator does not prove

## 1. Per-route contract

Without access to the tool, its public documentation is the only source of the contract. Each item cites its page (URL).

| Item | What to record |
|---|---|
| Authentication | scheme (key in a header, OAuth2), exact header, rights the key needs |
| Route | method, path, filter, sort and field-selection parameters, paging (offset/limit, page, cursor) |
| Envelope | response shape: `{"data": {"items": [...]}}`, `{"items": [...]}`, bare array… one route may differ from the others |
| Schema | fields, types, nullability, formats (dates, durations, amounts), enumerations |
| Request body | required and optional fields for creation, update and actions (e.g. a cancellation that requires a reason) |
| Errors | codes returned (400, 401, 403, 404, 409, 422, 429, 5xx) and the shape of the error body |
| Quotas | limit, scope (per key, per account, shared), retry headers |
| Writes | idempotency, answer to a duplicate |

When two pages disagree ("isAm" here, "isAM" there; a date here, a date-time there): record both, read tolerantly, and
add the point to the "to confirm with real access" list. A field not found in the docs is marked "to confirm" and the
code tolerates its absence.

For a browser flow such as punch-out (OCI or cXML), the contract also covers the setup request and response, the
browser round trip back to Axelor, the cart message, and session or CSRF constraints on the return URL.

## 2. Field-by-field mapping

One table per flow, filled before the code:

| Third-party field (route, name, type) | Doc source | Axelor field (entity.field, type) | AOS source (`file:line`) | Transformation rule | Edge cases |
|---|---|---|---|---|---|

Rules that prevent the most frequent defects:
- an empty third-party field does not erase Axelor data unless a written decision says so;
- an unmatched reference (project, employee, company) is **reported**, never silently replaced by a default value;
- customer-specific values (axis numbers, statuses, establishment codes) are **settings**, with the existing behaviour
  as default;
- amounts and durations are rounded to the precision the AOS validation accepts;
- for a file flow, the generated file passes the controls of the native import (balance lines, signs, continuity).

## 3. Emulator

`scripts/mock_api.py` with a scenario file (template: `scripts/mock_scenario_example.py`). It:
- serves exactly the routes the connector calls, with the documented envelope and paging;
- validates requests the way the docs describe (required fields, allowed status transitions, content type) and answers
  with the documented error, so that a connector bug shows up against the emulator rather than in production;
- carries several data sets (`SCENARIOS`): a base set, then one per family of edge cases (missing or null field, unknown
  reference, duplicate, rare status, several establishments, multi-page paging);
- simulates failures through `/__admin/inject`: 429 then recovery, 400 with a reason, 5xx, silent server (`hang`);
- journals every call: the journal proves what the connector sends (creation bodies, filters, authentication header
  present).

The deliverable is self-contained: `mock_api.py` copied next to the scenario, the start command written down, and the
tests runnable from the deliverable folder alone.

Known traps: a lock held during a network wait froze an emulator for 13 minutes (the provided script never holds its
lock while waiting); an exception in a handler answers 500 and shows in the journal rather than leaving the call hanging.

## 4. What the emulator does not prove

A flow tested against the emulator is "validated against the emulator built from the docs", never "validated on
<tool>". The specification lists the points to confirm on the real service (undocumented field, ambiguous format, key
rights, shared quota), each with the fallback the code applies. Real validation is part of the human remainder.
