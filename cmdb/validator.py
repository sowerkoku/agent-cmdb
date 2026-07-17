"""
CMDB Validator — Knowledge Kernel Entity Validation

Validates all entities in the CMDB against schema v2 rules.
Returns errors (blocking) and warnings (non-blocking) without raising exceptions.

API:
    cmdb_validate() -> dict
        {
            "valid": bool,
            "errors": [{"entity_id", "field", "message"}, ...],
            "warnings": [{"entity_id", "field", "message"}, ...],
            "stats": {"total": int, "by_domain": dict, "by_kind": dict}
        }
"""

import os
import yaml
from pathlib import Path
from typing import Optional

from .rules.schema import validate_all_schema, Error as SchemaError, Warning as SchemaWarning
from .rules.identity import validate_all_identity, check_duplicate_ids
from .rules.relations import validate_all_relations
from .rules.lifecycle import validate_all_lifecycle
from .config import get_config
from .taxonomy import KIND_TO_DOMAIN, DOMAIN_DISPLAY


def get_default_entities_dir() -> Path:
    """Get default entities directory from centralized config."""
    return get_config().data_dir


# Directorio de entidades (por defecto: ~/knowledge-kernel/data/)
DEFAULT_ENTITIES_DIR = get_default_entities_dir()


def load_entities_with_paths(entities_dir: Optional[Path] = None) -> tuple[dict, dict]:
    """
    Load all YAML entities and return both entity data and file paths.
    
    Returns:
        (entities_dict, entity_paths_dict) — entity data keyed by ID, and file paths keyed by ID
    """
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    entities = {}
    entity_paths = {}
    
    if not entities_dir.exists():
        return entities, entity_paths
    
    for yaml_file in entities_dir.rglob("*.yaml"):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                entity = yaml.safe_load(f)
            
            if entity and "id" in entity:
                entity_id = entity["id"]
                entities[entity_id] = entity
                entity_paths[entity_id] = yaml_file
        except yaml.YAMLError:
            continue
        except Exception:
            continue
    
    return entities, entity_paths


def load_entities(entities_dir: Optional[Path] = None) -> dict:
    """
    Load all YAML entities from the entities directory.
    
    Returns dict keyed by entity ID for fast lookup.
    Note: If duplicate IDs are found, the last one wins. Use cmdb_validate()
    to detect duplicates via check_duplicate_ids().
    """
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    entities = {}
    
    if not entities_dir.exists():
        return entities
    
    # Search recursively in all subdirectories
    for yaml_file in entities_dir.rglob("*.yaml"):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                entity = yaml.safe_load(f)
            
            if entity and "id" in entity:
                entities[entity["id"]] = entity
        except yaml.YAMLError as e:
            # Skip invalid YAML files
            continue
        except Exception as e:
            # Skip files that can't be read
            continue
    
    return entities


def load_entities_with_duplicates(entities_dir: Optional[Path] = None) -> tuple[dict, list]:
    """
    Load all YAML entities and detect duplicates during load.
    
    Returns:
        (entities_dict, duplicate_ids) — dict of entities and list of duplicate IDs found
    """
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    entities = {}
    seen_ids = {}
    duplicates = []
    
    if not entities_dir.exists():
        return entities, duplicates
    
    for yaml_file in entities_dir.rglob("*.yaml"):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                entity = yaml.safe_load(f)
            
            if entity and "id" in entity:
                entity_id = entity["id"]
                if entity_id in seen_ids:
                    duplicates.append(entity_id)
                else:
                    seen_ids[entity_id] = True
                    entities[entity_id] = entity
        except yaml.YAMLError:
            continue
        except Exception:
            continue
    
    return entities, duplicates


def validate_entity(entity: dict, all_entities: dict) -> tuple[list, list]:
    """
    Validate a single entity against all rules.
    
    Returns:
        (errors, warnings) — lists of Error and Warning objects
    """
    all_errors = []
    all_warnings = []
    
    # Run all validation rule sets
    for validator in [
        validate_all_schema,
        validate_all_identity,
        validate_all_relations,
        validate_all_lifecycle,
    ]:
        errors, warnings = validator(entity, all_entities)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
    
    return all_errors, all_warnings


def cmdb_validate(entities_dir: Optional[Path] = None) -> dict:
    """
    Validate all entities in the CMDB.
    
    Args:
        entities_dir: Path to entities directory (default: ~/knowledge-kernel/data/)
    
    Returns:
        dict with:
            - valid: bool (True if no errors)
            - errors: list of error dicts
            - warnings: list of warning dicts
            - stats: validation statistics
    """
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    
    # Load all entities and detect duplicates during load
    entities, duplicate_ids = load_entities_with_duplicates(entities_dir)
    
    all_errors = []
    all_warnings = []
    
    # Add errors for duplicate IDs found during load
    for dup_id in duplicate_ids:
        all_errors.append({
            "entity_id": dup_id,
            "field": "id",
            "message": f"Duplicate ID: {dup_id!r} found in multiple files",
        })
    
    # Also run check_duplicate_ids for safety (should be empty now)
    dup_errors, _ = check_duplicate_ids(entities)
    all_errors.extend([e.to_dict() for e in dup_errors])
    
    # Validate each entity
    for entity_id, entity in entities.items():
        errors, warnings = validate_entity(entity, entities)
        
        # Convert Error/Warning objects to dicts
        all_errors.extend([e.to_dict() for e in errors])
        all_warnings.extend([w.to_dict() for w in warnings])
    
    # Calculate stats
    stats = {
        "total": len(entities),
        "by_domain": {},
        "by_kind": {},
        "by_status": {},
    }
    
    for entity in entities.values():
        kind = entity.get("kind", "unknown")
        domain = KIND_TO_DOMAIN.get(kind, "unknown")
        status = entity.get("status", "unknown")
        
        stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
        stats["by_kind"][kind] = stats["by_kind"].get(kind, 0) + 1
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
    
    return {
        "valid": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": all_warnings,
        "stats": stats,
    }


def cmdb_get(entity_id: str, entities_dir: Optional[Path] = None) -> Optional[dict]:
    """
    Get a single entity by ID.
    
    Args:
        entity_id: The entity ID to retrieve
        entities_dir: Path to entities directory
    
    Returns:
        Entity dict or None if not found
    """
    entities = load_entities(entities_dir or DEFAULT_ENTITIES_DIR)
    return entities.get(entity_id)


def cmdb_list(kind: Optional[str] = None, domain: Optional[str] = None, entities_dir: Optional[Path] = None) -> list:
    """
    List entities, optionally filtered by kind and/or domain.
    
    Args:
        kind: Filter by kind (asset, software, procedure, etc.)
        domain: Filter by domain (infrastructure, software, knowledge, organization)
        entities_dir: Path to entities directory
    
    Returns:
        List of entity dicts
    """
    from .taxonomy import ALL_KINDS, VALID_DOMAINS
    
    entities = load_entities(entities_dir or DEFAULT_ENTITIES_DIR)
    
    if kind is None and domain is None:
        return list(entities.values())
    
    if kind is not None and kind not in ALL_KINDS:
        raise ValueError(f"Unknown kind: {kind!r}. Valid kinds: {sorted(ALL_KINDS)}")
    
    if domain is not None and domain not in VALID_DOMAINS:
        raise ValueError(f"Unknown domain: {domain!r}. Valid domains: {sorted(VALID_DOMAINS)}")
    
    result = entities.values()
    
    if kind is not None:
        result = [e for e in result if e.get("kind") == kind]
    
    if domain is not None:
        result = [e for e in result if KIND_TO_DOMAIN.get(e.get("kind")) == domain]
    
    return list(result)


# CLI entry point
if __name__ == "__main__":
    import json
    
    result = cmdb_validate()
    
    print(f"Valid: {result['valid']}")
    print(f"Total entities: {result['stats']['total']}")
    print(f"By kind: {result['stats']['by_kind']}")
    print(f"By status: {result['stats']['by_status']}")
    
    if result["errors"]:
        print(f"\nErrors ({len(result['errors'])}):")
        for err in result["errors"][:10]:  # Show first 10
            print(f"  - {err['entity_id']}.{err['field']}: {err['message']}")
        if len(result["errors"]) > 10:
            print(f"  ... and {len(result['errors']) - 10} more")
    
    if result["warnings"]:
        print(f"\nWarnings ({len(result['warnings'])}):")
        for warn in result["warnings"][:10]:
            print(f"  - {warn['entity_id']}.{warn['field']}: {warn['message']}")
        if len(result["warnings"]) > 10:
            print(f"  ... and {len(result['warnings']) - 10} more")
    
    # Exit with error code if validation failed
    exit(0 if result["valid"] else 1)