---
name: pitfalls/validation-strictness
description: schema_version is required for v2 entities. Unknown relation types are errors, not warnings.
applies_to:
  - validation
  - schema
---

# Pitfall 7: Validation strictness — schema_version and relation types

## Issue

Entity validation must fail when it should. Two enforcement rules:

### Rule 1: `schema_version` is REQUIRED for v2 entities

Missing `schema_version` on a v2 entity → ERROR. The message states that v2
must declare its schema version for auditability.

### Rule 2: Unknown relation types → ERROR

Valid types are enumerated in `cmdb/rules/relations.py:VALID_RELATION_TYPES`.
Any unknown type → ERROR listing valid types.

## Implementation

The enforcement lives in `cmdb/rules/schema.py`:

- `validate_schema_version()` — schema_version presence and value
- `validate_relations()` — type and target_kind enforcement

## Test corrections

When testing invalid relation types, use a genuinely invalid type (e.g.,
`magic_link`). Don't test with `depends_on` (which is valid legacy).
