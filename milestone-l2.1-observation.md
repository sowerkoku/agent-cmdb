# L2.1 Observation Window

**Status:** Active
**Triggered:** 2026-07-12 (immediately after L2.1 freeze)
**Target:** 100–500 real Hermes queries
**Architecture status:** Frozen

---

## Objectives

Measure five primary indicators during normal Hermes operation:

- KAR
- FGR
- Fact Miss Rate
- API Distribution
- Dataset Churn

---

## Exit Criterion

At least one observed pattern contradicts an architectural assumption.

---

## What constitutes sufficient evidence for L3

Not sufficient:
- "We could make it cleaner."
- "We could make it faster."
- "We could add a graph database."

Sufficient:
1. 60%+ of queries require reverse traversals.
2. Fact Miss Rate remains >30% after dataset expansion attempts.
3. `dataset_hash` changes 40+ times/day.
4. Multiple agents need concurrent mutation workflows.
5. P95 degrades under real usage.

L3 must emerge from evidence like the above.

---

## Permitted during this window

- Run Hermes normally
- Expand factual dataset (empirical learning only)
- Fix bugs (defects only)
- Improve documentation
- Performance tuning that preserves public contracts and architectural boundaries

## Not permitted

- New public APIs
- New indexes not triggered by observed patterns
- New engines or layers
- Proposal queues
- Evidence engines
- Auto-reload or file watchers
- Architectural redesign

---

## How to open this milestone remotely

If you have `gh` authenticated:

```bash
gh issue create \
  --title "L2.1 Observation Window — accumulate 100 real queries" \
  --label "milestone,observation,frozen-architecture" \
  --body "$(cat milestone-l2.1-observation.md)"
```

Or convert this file to a GitHub Milestone manually with the contents above.
