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

The L2 engine delivered sub-millisecond steady-state behavior on a small dataset.

### Benchmarks (2026-07-13, 53 entities)

| Operation | Cold (ms) | Warm (ms/op) | Ops/sec |
|-----------|----------:|-------------:|--------:|
| Index build (one-time) | 816 | — | — |
| `list_all_ids` | — | 0.021 | 46,000 |
| `get_by_id` | — | 0.003 | 360,000 |
| `get_by_kind` | — | 0.020 | 49,000 |
| Full scan (53 entities) | — | 0.16 total | — |
| N+1 endpoints (10 calls) | — | 0.04 total | — |

**N+1 speedup:** Pre-L2 pattern was ~4600 ms (37 sequential YAML loads).
Post-L2: 0.04 ms. **~4600x improvement.**

**Cold/warm ratio:** Once indexes are built, operations are ~50,000x faster
than the one-time index build cost.

### Interpretation

- **Index build:** ~800 ms to read 53 YAMLs, validate schema, build dicts
- **Warm path:** Sub-millisecond lookups (dictionary access, not disk I/O)
- **N+1 fix:** The classic query pattern that caused 4.6s latency now costs
  0.04 ms — the indexes enable single-pass resolution

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
