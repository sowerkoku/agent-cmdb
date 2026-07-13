---
description: Dataset cleanup operation — duplicate cleanup audit and resolution.
status: historical
---

# Dataset Cleanup — Historical

> **Status:** Historical snapshot of a single cleanup pass. The methodology
> lives in `docs/playbooks/duplicate-cleanup.md`. Specific deltas are kept
> here for replay.

## What was cleaned

The cleanup targeted:

1. Legacy software entities from the v1 → v2 migration that had newer,
   observed replacements
2. Asset duplicates representing the same physical host under different IDs
3. Stale references pointing at deleted entities

## Why

Two parallel sources produced overlapping facts. The Kernel ended up
duplicating one and the same reality. Validation was confused.

## Resolution pattern used

This cleanup followed the playbook now stored at
`docs/playbooks/duplicate-cleanup.md`:

1. Group by `metadata.name`
2. Compare evidence (schema_version, observed_at, metadata richness)
3. **Migrate references first**, delete second
4. Final `cmdb_validate()` returns 0 errors

## Specifics from this pass

These are kept for replay only — they were true at the moment of cleanup:

- Reduced `kind=software` entity count by removing legacy duplicates and
  keeping observed replacements
- Resolved an asset duplicate where legacy ID had wrong hardware data
- Updated endpoint relations that pointed at the legacy IDs

## See also

- `docs/playbooks/duplicate-cleanup.md` — current playbook
- `docs/pitfalls/duplicate-entities.md`
- `docs/pitfalls/asset-duplicates.md`
