---
name: pitfalls/registry-drift
description: The Kernel records declared reality, not runtime state. Empirical verification finds drift.
applies_to:
  - runtime-discovery
  - drift
---

# Pitfall 9: Registry drift — declared ≠ running

## Symptom

`cmdb_impact(asset)` shows N dependents, but SSH + `ps aux` shows the actual
machines running none of them. The YAML is stale.

## Root cause

The Kernel records **declared reality**, not **runtime state**. Software
migrates; YAMLs that were correct become misleading.

## Resolution pattern

1. SSH to each asset → `ps aux | grep <service>` + `docker ps` + `ss -tlnp`
2. Compare empirical reality with declared YAML
3. **Eliminate obsolete YAMLs first** — when drift is extensive, delete and
   recreate from observed evidence (don't patch old YAMLs)
4. Create new YAMLs with `evidence.confidence_level: HIGH` and
   `provenance.discovered_by: <ssh|docker|...>`
5. Run `cmdb_validate()` → ensure 0 errors

## Prevention

Periodic runtime discovery (quarterly or after infrastructure changes). See
`docs/playbooks/runtime-discovery.md` for the playbook.
