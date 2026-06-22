# CMDB Rules — Validation Logic

Each rule module implements a single responsibility.
Rules return either errors (blocking) or warnings (non-blocking).

## Rule Interface

```python
def validate(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]
```

## Modules

- `schema.py` — schema_version, required fields, kind, status, criticality
- `identity.py` — id uniqueness, format validation
- `relations.py` — relation types, target existence, target kind compatibility
- `lifecycle.py` — status, deprecated dependencies, orphan entities

## Error vs Warning

**Error (blocking):**
- Schema invalid
- ID duplicates or malformed
- Unknown kind or relation type
- Missing relation target
- Relation target kind incompatible

**Warning (non-blocking):**
- Deprecated entity with active dependents
- Entity without relations
- Software without runs_on (if applicable)