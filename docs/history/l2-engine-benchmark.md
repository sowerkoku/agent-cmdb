---
description: L2 in-memory index engine benchmark — methodology and outcome.
status: historical
---

# L2 Engine Benchmark — Historical

> **Status:** Historical snapshot. The methodology lives in `docs/architecture.md`.
> Specific numbers (benchmark, speedup) are kept here for replay and
> traceability. Do NOT cite as current.

## Goal

Eliminate N+1 query latency without breaking API stability.

## Methodology

1. Measure baseline latency against the pre-L2 implementation (cold + warm)
2. Implement L2 engine (deterministic in-memory indexes, read-only, rebuildable)
3. Re-measure against the same benchmark, same dataset
4. Establish a real SLO — `p95_post << p95_pre` (not arbitrary)
5. Commit with before/after data attached

## Outcome

The L2 engine delivered the expected sub-millisecond steady-state behavior
on a small dataset. Specific numbers are not preserved here because the
benchmark configuration, machine load, and dataset size have all changed
since this capture.

```
# Read these numbers from the original benchmark tooling, not from this file.
```

## Architecture constraints honored

- YAML = canonical factual store
- Memory = deterministic derived indexes (rebuildable)
- API = stable contract (`cmdb.api` unchanged by L2)
- Telemetry = observes usage
- Discovery = proposes changes
- Humans = curate facts
- Agents = reason on top

## Non-goals (intentionally out of scope)

- No proposal queues
- No evidence engines
- No distributed caches
- No mutation APIs
- No complex evidence levels (DECLARED → DISCOVERED → VERIFIED → CORROBORATED)

## See also

- `docs/architecture.md` — current architecture
- `docs/observability.md` — telemetry contract
