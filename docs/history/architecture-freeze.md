---
description: Architecture freeze — L1+L2 boundaries, what was deferred.
status: historical
---

# Architecture Freeze — Historical

> **Status:** Historical snapshot. The frozen state remains the contract
> at the time of writing. Anything that came after is in `docs/architecture.md`.

## What was frozen

The boundary between L1 (factual store) and L2 (derived views):

- L1 entities: declared in YAML, versioned, evidence-tracked
- L2 engine: read-only derived indexes, deterministic, rebuildable

## What was deliberately not introduced

Architectural commitments that the project said NO to (still NO):

- No proposal queues
- No evidence engines in the core
- No distributed caches
- No mutation APIs (everything is human-curated YAML)
- No complex evidence levels
  (DECLARED → DISCOVERED → VERIFIED → CORROBORATED)

## Why these constraints matter

Each "no" is a rejection of accidental complexity. L2 stays small,
predictable, and rebuildable.

## See also

- `docs/architecture.md` — current architecture
