"""
Identity validation rules for Agent CMDB.

Validates:
- ID uniqueness across all entities
- ID format (lowercase, kebab-case, no spaces, max 64 chars)
"""

import re
from collections import Counter

from .schema import Error, Warning


ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_ID_LENGTH = 64


def validate_id_format(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate ID format."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")

    if entity_id == "<unknown>":
        errors.append(Error("<unknown>", "id", "Field 'id' is missing"))
        return errors, warnings

    if not ID_PATTERN.match(entity_id):
        errors.append(Error(entity_id, "id", f"Invalid ID format: {entity_id!r}. Must be lowercase kebab-case (e.g., 'server-54')"))

    if len(entity_id) > MAX_ID_LENGTH:
        errors.append(Error(entity_id, "id", f"ID too long: {len(entity_id)} chars. Max {MAX_ID_LENGTH}."))

    return errors, warnings


def validate_id_uniqueness(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate ID is unique across all entities."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")

    if entity_id == "<unknown>":
        return errors, warnings

    # Count occurrences of this ID
    id_count = sum(1 for e in all_entities.values() if e.get("id") == entity_id)

    if id_count > 1:
        errors.append(Error(entity_id, "id", f"Duplicate ID: {entity_id!r} appears {id_count} times"))

    return errors, warnings


def validate_all_identity(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Run all identity validation rules."""
    all_errors = []
    all_warnings = []

    for validator in [validate_id_format, validate_id_uniqueness]:
        errors, warnings = validator(entity, all_entities)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    return all_errors, all_warnings


def check_duplicate_ids(all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Check for duplicate IDs across all entities (global validation)."""
    errors = []
    warnings = []

    ids = [e.get("id") for e in all_entities.values() if "id" in e]
    duplicates = {id_val for id_val, count in Counter(ids).items() if count > 1}

    for dup_id in duplicates:
        errors.append(Error(dup_id, "id", f"Duplicate ID: {dup_id!r} appears multiple times"))

    return errors, warnings