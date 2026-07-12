"""
Schema validation rules for Agent CMDB v2.

Validates:
- schema_version presence and value (1 = legacy, 2 = domain+kind)
- Required fields (id, kind, metadata.name, status)
- Domain + Kind hierarchy
- Field types and formats
"""

from typing import Any
from ..taxonomy import (
    ALL_KINDS, VALID_DOMAINS, KIND_TO_DOMAIN,
    DOMAIN_INFRASTRUCTURE, DOMAIN_SOFTWARE, DOMAIN_KNOWLEDGE, DOMAIN_ORGANIZATION,
)


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


# Required fields for all entities
REQUIRED_FIELDS = ["id", "kind", "metadata", "status"]

# Valid statuses (universal)
VALID_STATUSES = {"operational", "degraded", "down", "deprecated"}

# Valid criticality levels
VALID_CRITICALITY_LEVELS = {"low", "medium", "high"}


def validate_schema_version(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate schema_version is present and valid."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")

    if "schema_version" not in entity:
        errors.append(Error(entity_id, "schema_version", 
            "Missing schema_version — v2 entities must declare schema_version: 2"))
    elif entity["schema_version"] not in (1, 2):
        errors.append(Error(entity_id, "schema_version", 
            f"Unsupported schema_version: {entity['schema_version']}. Expected 1 or 2."))

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
    """
    Validate kind using domain+kind taxonomy (v2) or legacy flat kind (v1).
    
    v2 format: domain + kind fields
    v1 format: only kind field (legacy)
    """
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    schema_version = entity.get("schema_version", 1)
    
    # v2: explicit domain + kind
    domain = entity.get("domain")
    kind = entity.get("kind")
    
    if schema_version >= 2 and domain:
        # v2 format: validate domain + kind pair
        if domain not in VALID_DOMAINS:
            errors.append(Error(entity_id, "domain", 
                f"Unknown domain: {domain!r}. Valid domains: {sorted(VALID_DOMAINS)}"))
        elif kind not in ALL_KINDS:
            errors.append(Error(entity_id, "kind",
                f"Unknown kind: {kind!r}. Valid kinds: {sorted(ALL_KINDS)}"))
        elif KIND_TO_DOMAIN.get(kind) != domain:
            errors.append(Error(entity_id, "domain/kind",
                f"Kind {kind!r} does not belong to domain {domain!r}. "
                f"Expected domain: {KIND_TO_DOMAIN.get(kind)!r}"))
    elif kind:
        # v1 format (legacy): flat kind only, infer domain
        if kind not in ALL_KINDS:
            errors.append(Error(entity_id, "kind",
                f"Unknown kind: {kind!r}. Valid kinds: {sorted(ALL_KINDS)}"))
        else:
            warnings.append(Warning(entity_id, "kind",
                f"Entity uses legacy format (v1). Consider migrating to v2 with explicit domain."))
    else:
        errors.append(Error(entity_id, "kind", "Missing required field 'kind'"))

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
        errors.append(Error(entity_id, "status", 
            f"Unknown status: {status!r}. Valid statuses: {sorted(VALID_STATUSES)}"))

    return errors, warnings


def validate_criticality(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate criticality levels if present."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    criticality = entity.get("criticality", {})

    if not isinstance(criticality, dict):
        errors.append(Error(entity_id, "criticality", "Field 'criticality' must be an object"))
        return errors, warnings

    for level_name, level_value in criticality.items():
        if level_value not in VALID_CRITICALITY_LEVELS:
            errors.append(Error(entity_id, f"criticality.{level_name}",
                f"Invalid criticality level: {level_value!r}. Valid: {sorted(VALID_CRITICALITY_LEVELS)}"))

    return errors, warnings


def validate_relations(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate relations structure and referential integrity."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    relations = entity.get("relations", [])

    if not isinstance(relations, list):
        errors.append(Error(entity_id, "relations", "Field 'relations' must be a list"))
        return errors, warnings

    valid_relation_types = {
        "runs_on", "uses", "reads", "writes", "calls",
        "owns", "backs_up", "monitors", "part_of", "depends_on",
        "assigned_to", "belongs_to", "uses_profile", "listens_on",
    }

    for i, rel in enumerate(relations):
        if not isinstance(rel, dict):
            errors.append(Error(entity_id, f"relations[{i}]", "Relation must be an object"))
            continue

        rel_type = rel.get("type")
        rel_target = rel.get("target")

        if not rel_type:
            errors.append(Error(entity_id, f"relations[{i}].type", "Missing relation type"))
        elif rel_type not in valid_relation_types:
            errors.append(Error(entity_id, f"relations[{i}].type",
                f"Unknown relation type: {rel_type!r}. Valid types: {sorted(valid_relation_types)}"))

        if not rel_target:
            errors.append(Error(entity_id, f"relations[{i}].target", "Missing relation target"))

    return errors, warnings


def validate_all_schema(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Run all schema validations."""
    errors = []
    warnings = []

    for validator in [
        validate_schema_version,
        validate_required_fields,
        validate_kind,
        validate_status,
        validate_criticality,
        validate_relations,
    ]:
        e, w = validator(entity, all_entities)
        errors.extend(e)
        warnings.extend(w)

    return errors, warnings