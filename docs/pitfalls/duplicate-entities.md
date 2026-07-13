---
name: pitfalls/duplicate-entities
description: Two entities can describe the same reality. Compare evidence, keep the observed one, migrate references.
applies_to:
  - cleanup
  - duplicates
---

# Pitfall 10: Duplicate entities — legacy vs observed

## Symptom

`cmdb_list()` returns more entities than reality: two with the same `name`
or describing the same service.

## Root cause

Migration from a previous Kernel version left legacy entities (e.g.,
`mariadb` from v1) alongside newly observed ones (`mariadb-54` from runtime
discovery). Both were valid when entered. They represent the same reality.

## Resolution

1. **Group by `metadata.name`** (not by ID — the ID format is arbitrary)
2. **Compare evidence:**
   - Keep one with `provenance.discovered_by: direct_observation`
   - Keep one with more recent `evidence.observed_at`
   - Keep one with the richest metadata (versions, ports, interfaces)
3. **List references** before deleting:
   ```bash
   grep -r "target: <legacy-id>\b" <dataset-root>
   ```
4. **Update references** in endpoints / assets / automations
5. **Delete legacy entries**

Validation check: run `cmdb_validate()` → 0 errors.

## See also

- `docs/playbooks/duplicate-cleanup.md` — full playbook.
