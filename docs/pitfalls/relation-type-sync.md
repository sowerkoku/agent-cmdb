---
name: pitfalls/relation-type-sync
description: New relation types require updates in two locations — single-file updates cause silent validation failures.
applies_to:
  - relations
  - cmdb
---

# Pitfall 2: Relation types must be added in two files

## Issue

Adding a new relation type (e.g., `exposed_by`) requires updating:

1. **`cmdb/impact.py`** — `DEPENDENCY_RELATIONS` (for graph traversal)
2. **`cmdb/rules/relations.py`** — `VALID_RELATION_TYPES` AND `RELATION_TARGET_KINDS` (for validation)

Adding to only one file causes silent validation failures. `cmdb_validate()`
returns `valid=False` and the error is `"Unknown relation type."`

## Rule

Whenever you add a relation type, always update both files in the same commit.
