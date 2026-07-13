---
description: Migration notes from v1 (Registry) to v2 (Knowledge Kernel).
status: historical
---

# Migration Notes — Registry (v1) → Kernel (v2)

> **Status:** Historical snapshot from the v1 → v2 migration. The state at
> the time of writing, the steps that worked, and the lessons learned.

## Source

The legacy Registry existed as an in-memory data structure used by the
original agent-cmdb. The destination is the YAML-backed v2 Kernel.

## Migration outcome

The migration removed a flat, in-memory entity list and replaced it with
a versioned, evidence-tracked YAML store. This is what made Runtime
Discovery and provenance-tracking possible.

## Why we did not preserve v1

A snapshot archive was kept at `<archive-root>/knowledge-kernel-v1/`. The
v1 data is **read-only**. v2 does not point at v1 entities — v2 owns ID
naming and structure.

## Lessons captured

These are now permanent principles living in `docs/`:

- Code ≠ Data explicit separation → `docs/architecture.md`
- Single Responsibility per source of truth
- Evidence-based reasoning required
- Why Not RAG / Why Not Memory → `docs/philosophy.md`

## See also

- `docs/philosophy.md` — permanent principles
- `docs/architecture.md` — current state
- `docs/greenfield-rebuild.md` — v2 dataset rebuild rules
