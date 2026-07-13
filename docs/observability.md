---
description: Kernel observability metrics, telemetry schema, and KHI.
audience: maintainers, kernel authors
status: stable
---

# Observability — knowledge-kernel

**Audience:** kernel maintainers. Operational telemetry, metrics framework,
and the KHI compound index.

## Metrics

### KAR — Kernel Adoption Rate

When facts are needed, how often does the agent query the Kernel?

```
KAR = kernel_queries / queries_needing_facts
Target: ≥ 80%
```

KAR measures whether the agent chooses the Kernel over inference.

### FGR — Fact Grounding Rate

Of all factual claims, what fraction is backed by Kernel facts?

```
FGR = grounded_assertions / factual_assertions
Target: ≥ 90%
```

FGR measures the rate at which claims are backed by facts.

### What FGR is NOT

- A measure of the Kernel's intelligence
- A percentage of "correct answers"
- The agent's quality score

### What FGR IS

- A measure of how often the agent chose the Kernel over inference
- The signal for when to expand the Kernel (low Coverage)
- The signal for when the agent needs better grounding guidance (low
  Reasoning Accuracy)

### Companion metrics

```
Coverage    = questions_with_kernel_data / total_questions
Quality     = entities_with_complete_metadata / total_entities
Freshness   = observations fresh / total observations
```

## Kernel Health Index (KHI)

KHI is the compound health index across four dimensions:

```
KHI = Coverage × Quality × Freshness × Adoption
```

All four must be healthy simultaneously. One failing dimension breaks the
chain:

- High Coverage + low Quality = dangerous (agents reason on undefendable facts)
- High Quality + low Freshness = stale (facts become obsolete)
- High Freshness + zero Adoption = zero value (unused knowledge)

| Level | Dimension     | KPIs                              | Question                                         |
|------:|---------------|-----------------------------------|--------------------------------------------------|
|     1 | Disponibilidad | Fact Coverage, Provenance Coverage | ¿Existe conocimiento suficiente?                  |
|     2 | Calidad       | DQS, Reproduction Rate            | ¿Podemos confiar en ese conocimiento?             |
|     3 | Operación     | FFR (Fresh Fact Ratio)            | ¿Sigue siendo válido hoy?                        |
|     4 | Adopción      | FGR (Fact Grounding Rate)         | ¿Los agentes realmente lo utilizan?              |

## Telemetry Contract

### Required fields on every grounded query

```json
{
  "question":  "<user question>",
  "kernel_query": "<cmdb call>",
  "assertion": "<agent factual claim>",
  "dataset_hash": "<sha256[:16] of dataset>",
  "engine_generation": "<monotonic counter>",
  "observed_at": "<ISO 8601>"
}
```

### Dataset hash

The `dataset_hash` is a SHA256 of the canonical YAML files. It is included
with every grounded assertion so the auditable state is reconstructable.

### Engine generation

The L2 engine increments `engine_generation` on every atomic reload.
Telemetry requests carry the generation that produced their view, so the
agent's claimed ground is traceable to a specific kernel state.

## Pilot methodology

The first operational pilot (2026-07-11) established these patterns:

1. 16 questions across 4 categories × 4 repetitions
2. Instrumentation: question → kernel query → assertion mapping
3. Latency tracking per query (P50, P95)
4. Coverage / Quality / Freshness / Adoption scoring per category

The historical results are archived in `docs/history/grounding-pilot.md`.
The methodology itself is what matters and stays in this file.

## See also

- `docs/pitfalls/observability-before-adoption.md` — adopt first, instrument second
- `docs/pitfalls/n-plus-one-queries.md` — latency cause + fix patterns
