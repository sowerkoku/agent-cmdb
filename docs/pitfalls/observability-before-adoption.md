---
name: pitfalls/observability-before-adoption
description: Optimizing observability for something nobody uses is waste. Adopt first, instrument second.
applies_to:
  - kar
  - fgr
  - telemetry
---

# Pitfall 4: Measuring observability before adoption

## Issue

It's tempting to build the evidence ledger, failure injection, alerting before
proving that anyone uses the Kernel. That's inverted.

## Wrong sequence

1. Build evidence ledger
2. Add failure injection tests
3. Create alerting dashboards
4. Then check if agents use the Kernel

## Right sequence

1. Instrument minimal telemetry (question → kernel query → assertion)
2. Measure KAR/FGR on real usage
3. Only after KAR ≥ 80%, invest in observability depth

## Why

Optimizing observability for something nobody uses is waste. First prove
adoption (KAR/FGR), then invest in diagnostics.

See `docs/observability.md` for the metrics framework.
