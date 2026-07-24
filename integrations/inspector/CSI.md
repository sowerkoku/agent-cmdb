# Contract Stability Index — Tracking

This is a living record, not a dashboard. Each entry corresponds to a
commit that touches `integrations/inspector/`.

## Entries

| Commit | Rules | Contract changes | CSI | Notes |
|---|---|---|---|---|
| 7935cae | 1 (`stale_entity`) | 0 | ∞ | v0.1 frozen; 5 pillars codified |

## Definition

CSI = (number of rules implemented) / (number of contract changes to date)

When `contract_changes = 0`, CSI is reported as ∞. The metric is only
meaningful once at least one rule beyond the first has been
implemented cleanly. Track daily.

## Decision rule

- Adding a rule without contract change → CSI goes up.
- Modifying the contract → CSI drops to a finite number; the
  proposal MUST cite the rule that required the change.
