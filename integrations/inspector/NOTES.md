# Inspector — implementation notes (technical observations)

This file is **not** part of the Inspector contract. It records
observations made during rule implementation that are useful to the
next implementer but do not change v0.1.

## Confidence granularity (2026-07-24)

**Observation**: the public Knowledge Kernel API exposes confidence
for an **entity's evidence** (`cmdb_get(...).evidence.confidence_level`)
but not for **individual relations** (`entity.relations[].confidence`
does not exist).

**Consequence** for rule candidates:

- `low_confidence_dependency` (inspects per-relation confidence) is
  **not implementable** under v0.1. Renamed to
  `low_confidence_entity` — the rule inspects per-entity
  confidence only.
- Any future rule that wants per-relation evidence will need the
  Kernel API to grow that field. Until then, the rule is parked.

**Status of the parked candidates**:

| Candidate | Reason parked |
|---|---|
| `low_confidence_dependency` | Needs per-relation confidence |
| `cycles_invalid` | Needs graph traversal API surfaces; not yet attempted |
| `missing_runs_on` | Has analogous issue: must inspect relation absence per kind |

These are technical observations, **not** architectural proposals.
No PI is opened for them. If the Kernel grows the required public
API later, the candidates return to the backlog.
