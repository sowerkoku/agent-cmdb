"""
Schema validation rules for Agent CMDB.

Validates:
- schema_version presence and value
- Required fields (id, kind, metadata.name, status)
- Field types and formats
"""

from typing import Any


class Error:
    def __init__(self, entity_id: str, field: str, message: str):
        self.entity_id = entity_id
        self.field = field
        self.message = message

    def __repr__(self):
        return f"Error({self.entity_id!r}, {self.field!r}: {self.message})"

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "field": self.field,
            "message": self.message,
        }


class Warning:
    def __init__(self, entity_id: str, field: str, message: str):
        self.entity_id = entity_id
        self.field = field
        self.message = message

    def __repr__(self):
        return f"Warning({self.entity_id!r}, {self.field!r}: {self.message})"

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "field": self.field,
            "message": self.message,
        }


REQUIRED_FIELDS = ["id", "kind", "metadata", "status"]
VALID_KINDS = {"asset", "software", "automation", "data", "endpoint"}
VALID_STATUSES = {"operational", "degraded", "down", "deprecated"}
VALID_CRITICALITY_LEVELS = {"low", "medium", "high"}


def validate_schema_version(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate schema_version is present and equals 1."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")

    if "schema_version" not in entity:
        errors.append(Error(entity_id, "schema_version", "Missing required field 'schema_version'"))
    elif entity["schema_version"] != 1:
        errors.append(Error(entity_id, "schema_version", f"Unsupported schema_version: {entity['schema_version']}. Expected 1."))

    return errors, warnings


def validate_required_fields(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate all required fields are present."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")

    for field in REQUIRED_FIELDS:
        if field not in entity:
            errors.append(Error(entity_id, field, f"Missing required field '{field}'"))

    # Validate metadata.name specifically
    if "metadata" in entity:
        if not isinstance(entity["metadata"], dict):
            errors.append(Error(entity_id, "metadata", "Field 'metadata' must be an object"))
        elif "name" not in entity["metadata"]:
            errors.append(Error(entity_id, "metadata.name", "Missing required field 'metadata.name'"))

    return errors, warnings


def validate_kind(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate kind is in the catalog."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    kind = entity.get("kind")

    if kind is None:
        pass  # Already caught by validate_required_fields
    elif kind not in VALID_KINDS:
        errors.append(Error(entity_id, "kind", f"Unknown kind: {kind!r}. Valid kinds: {sorted(VALID_KINDS)}"))

    return errors, warnings


def validate_status(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate status is a valid value."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    status = entity.get("status")

    if status is None:
        pass  # Already caught by validate_required_fields
    elif status not in VALID_STATUSES:
        errors.append(Error(entity_id, "status", f"Unknown status: {status!r}. Valid statuses: {sorted(VALID_STATUSES)}"))

    return errors, warnings


def validate_criticality(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate criticality structure if present."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    criticality = entity.get("criticality")

    if criticality is None:
        # Criticality is optional
        return errors, warnings

    if not isinstance(criticality, dict):
        errors.append(Error(entity_id, "criticality", "Field 'criticality' must be an object"))
        return errors, warnings

    required_dims = ["business", "operational", "technical"]
    for dim in required_dims:
        if dim not in criticality:
            errors.append(Error(entity_id, f"criticality.{dim}", f"Missing required dimension 'criticality.{dim}'"))
        elif criticality[dim] not in VALID_CRITICALITY_LEVELS:
            errors.append(Error(entity_id, f"criticality.{dim}", f"Invalid value: {criticality[dim]!r}. Valid: {sorted(VALID_CRITICALITY_LEVELS)}"))

    return errors, warnings


def validate_all_schema(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Run all schema validation rules."""
    all_errors = []
    all_warnings = []

    for validator in [
        validate_schema_version,
        validate_required_fields,
        validate_kind,
        validate_status,
        validate_criticality,
    ]:
        errors, warnings = validator(entity, all_entities)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    return all_errors, all_warnings