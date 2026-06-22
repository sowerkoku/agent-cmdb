"""
Lifecycle validation rules for Agent CMDB.

Validates:
- Deprecated entities with active dependents (warning)
- Entities without relations (warning)
- Software without runs_on (warning, if applicable)
"""

from .schema import Error, Warning


def validate_deprecated_dependencies(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Warn if this entity depends on a deprecated entity."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    relations = entity.get("relations", [])

    if not isinstance(relations, list):
        return errors, warnings

    for rel in relations:
        if not isinstance(rel, dict):
            continue

        rel_target = rel.get("target")
        if rel_target is None or rel_target not in all_entities:
            continue

        target_entity = all_entities[rel_target]
        if target_entity.get("status") == "deprecated":
            warnings.append(Warning(
                entity_id,
                "relations",
                f"Depends on deprecated entity: {rel_target!r}"
            ))

    return errors, warnings


def validate_entity_without_relations(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Warn if an entity has no relations (may indicate incomplete modeling)."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    relations = entity.get("relations", [])

    # Endpoints may not have relations
    kind = entity.get("kind")
    if kind == "endpoint":
        return errors, warnings

    if not relations or len(relations) == 0:
        warnings.append(Warning(
            entity_id,
            "relations",
            "Entity has no relations — may indicate incomplete modeling"
        ))

    return errors, warnings


def validate_software_runs_on(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Warn if software entity has no runs_on relation."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    kind = entity.get("kind")
    relations = entity.get("relations", [])

    if kind != "software":
        return errors, warnings

    has_runs_on = any(
        isinstance(rel, dict) and rel.get("type") == "runs_on"
        for rel in (relations or [])
    )

    if not has_runs_on:
        warnings.append(Warning(
            entity_id,
            "relations",
            "Software entity has no 'runs_on' relation — consider adding if it runs on a host"
        ))

    return errors, warnings


def validate_all_lifecycle(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Run all lifecycle validation rules."""
    all_errors = []
    all_warnings = []

    for validator in [
        validate_deprecated_dependencies,
        validate_entity_without_relations,
        validate_software_runs_on,
    ]:
        errors, warnings = validator(entity, all_entities)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    return all_errors, all_warnings