---
description: First operational grounding pilot — methodology + seed questions.
status: historical
---

# First Grounding Pilot — Historical

> **Status:** Historical snapshot. The pilot methodology is preserved in
> `docs/observability.md`. Specific run results are kept here for replay
> and traceability. Do NOT cite as current.

## Why this pilot existed

Before investing in full observability depth, the kernel needed to prove
adoption — that agents actually query the Kernel when facts are needed,
and ground their assertions in those queries. See
`docs/pitfalls/observability-before-adoption.md`.

## What the pilot measured

For each of the four KPI dimensions in `docs/observability.md`:

| Dimension | What gets measured in a pilot |
|-----------|-------------------------------|
| Coverage  | Does the Kernel have data for the question? |
| Quality   | Are the fields complete and accurate? |
| Freshness | Are observations from the current epoch? |
| Adoption  | Does the agent consult the Kernel, and back assertions? |

## Replay instructions

1. Select N seed questions across the dimensions
2. Instrument: question → kernel query → assertion
3. Score per question across all four dimensions
4. Compare against the targets in `docs/observability.md`

Specific historical numbers from this pilot are NOT preserved here. They
depend on dataset state, machine load, and agent behavior at the time.
Run a fresh pilot to recover them.

## Lesson

The pilot found an N+1 query pattern that caused catastrophic p95 latency
on endpoint questions. That became `docs/pitfalls/n-plus-one-queries.md`.

## See also

- `docs/observability.md` — current metrics framework
- `docs/pitfalls/observability-before-adoption.md`
- `docs/pitfalls/n-plus-one-queries.md`
