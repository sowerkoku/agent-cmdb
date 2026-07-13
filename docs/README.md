# Knowledge Kernel — Documentation Index

> **Reader question → Document**
>
> Most readers arrive with a concrete need. This file maps each question
> to exactly one document. If you do not find your answer here, the
> information does NOT belong in the Kernel — it belongs elsewhere.

## I want to…

| I need to…                                       | Go to                                      |
|--------------------------------------------------|--------------------------------------------|
| Understand what the Kernel is                    | [`philosophy.md`](./philosophy.md)         |
| See how the L2 engine works                      | [`architecture.md`](./architecture.md)     |
| Look at the public API                           | [`../integrations/hermes/SKILL.md`](../integrations/hermes/SKILL.md) |
| See how entities are modeled and validated       | [`domain-model.md`](./domain-model.md) + [`schema-v1.md`](./schema-v1.md) |
| Check what belongs in the Kernel                 | [`governance.md`](./governance.md)         |
| Audit the dataset                                | [`audit-methodology.md`](./audit-methodology.md) |
| Understand endpoint identity                     | [`endpoint-identity-vs-observation.md`](./endpoint-identity-vs-observation.md) |
| See typical usage patterns                       | [`usage-patterns.md`](./usage-patterns.md) |
| Reference a documented failure mode              | [`error-log.md`](./error-log.md)           |

## I want to add / fix / clean up…

| I need to…                                               | Go to                                                                  |
|----------------------------------------------------------|------------------------------------------------------------------------|
| Resolve a duplicate entity (software or asset)           | `playbooks/duplicate-cleanup.md`                                       |
| Find drift between declared YAML and observed reality    | `playbooks/runtime-discovery.md` → `pitfalls/registry-drift.md`         |
| Migrate from a previous Kernel version                   | `playbooks/`                                                            |
| Understand a known pitfall                               | `pitfalls/` (one file per pitfall)                                      |

## I want to inspect a past experiment

| I need to…                                       | Go to                                      |
|--------------------------------------------------|--------------------------------------------|
| Read prior benchmarks                            | [`history/l2-engine-benchmark.md`](./history/l2-engine-benchmark.md) |
| Read prior validation defect fixes              | [`history/l2.1-observation-window.md`](./history/l2.1-observation-window.md) |
| Understand an earlier Grounding Pilot            | [`history/grounding-pilot.md`](./history/grounding-pilot.md) |
| Migrate from the legacy Registry                 | [`history/migration-v1-v2.md`](./history/migration-v1-v2.md) |
| Read a single dataset cleanup audit              | [`history/duplicate-cleanup.md`](./history/duplicate-cleanup.md) |
| Review an earlier architecture freeze            | [`history/architecture-freeze.md`](./history/architecture-freeze.md) |

## Releases

`releases/` is reserved for **user-facing release notes** (e.g.,
`v1.0.0.md`). Benchmark numbers, observation windows, and postmortem
snapshots are NOT releases — they live in `history/`.

## Layout

```
docs/
├── README.md                  ← this file
├── philosophy.md
├── architecture.md
├── observability.md
├── governance.md              ← includes §11: documentation size governance
├── schema-v1.md
├── domain-model.md
├── usage-patterns.md
├── audit-methodology.md
├── endpoint-identity-vs-observation.md
├── error-log.md
├── pitfalls/                  ←  one pitfall per file
├── playbooks/                 ←  one operational recipe per file
├── history/                   ←  experimental and historical snapshots
└── releases/                  ←  user-facing release notes (one per release)
```

## Scope rule

> If a topic appears here, it has a single canonical home. If the same
> idea is duplicated across two docs, one of them is wrong.
