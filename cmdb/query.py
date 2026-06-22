"""
CMDB Query API — Agent-Friendly Interface

Provides high-level query functions for AI agents to ground their responses
in verified infrastructure facts.

Design principles:
- Return structured, citable facts
- Never guess — return None for unknown
- Include source entity IDs for attribution
- Distinguish: known fact vs. relationship vs. absence of information
"""

from typing import Optional, Union
from pathlib import Path
from datetime import datetime

from .validator import load_entities, cmdb_validate


DEFAULT_ENTITIES_DIR = Path("/home/carlos/registry")


def cmdb_exists(entity_id: str, entities_dir: Optional[Path] = None) -> dict:
    """
    Check if an entity exists in the CMDB.
    
    **Agent usage:**
    ALWAYS call this before making claims about infrastructure existence.
    Prevents hallucinations at the root.
    
    ```python
    exists = cmdb_exists("redis")
    if exists["exists"]:
        print(f"Entity exists: {exists['reason']}")
    else:
        print("⚠️  Entity not found — do not assume existence")
    ```
    
    Args:
        entity_id: The entity ID to check
        entities_dir: Path to entities directory
    
    Returns:
        Existence check result.
        
        Example (exists):
        ```python
        {
            "exists": True,
            "entity_id": "ollama",
            "kind": "software",
            "status": "operational",
            "reason": "Entity found in CMDB",
            "source": {
                "type": "cmdb",
                "file": "/home/carlos/registry/software/ollama.yaml",
                "verified_at": "2026-06-22T19:45:00"
            },
            "confidence": "verified"
        }
        ```
        
        Example (not exists):
        ```python
        {
            "exists": False,
            "entity_id": "redis",
            "reason": "Entity not found in CMDB",
            "similar_entities": ["ollama", "mysql"],  # if search found matches
            "confidence": "verified_absence"
        }
        ```
    """
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    entities, paths = load_entities_with_paths(entities_dir)
    
    if entity_id in entities:
        entity = entities[entity_id]
        entity_file = paths.get(entity_id, "unknown")
        
        return {
            "exists": True,
            "entity_id": entity_id,
            "kind": entity.get("kind"),
            "status": entity.get("status"),
            "reason": "Entity found in CMDB",
            "source": {
                "type": "cmdb",
                "file": str(entity_file),
                "verified_at": datetime.now().isoformat(),
            },
            "confidence": "verified",
        }
    else:
        # Check for similar entities
        similar = []
        query_lower = entity_id.lower()
        for eid in entities.keys():
            if query_lower in eid.lower():
                similar.append(eid)
        
        return {
            "exists": False,
            "entity_id": entity_id,
            "reason": "Entity not found in CMDB",
            "similar_entities": similar[:5],  # Top 5 matches
            "confidence": "verified_absence",
        }


def cmdb_get(entity_id: str, entities_dir: Optional[Path] = None) -> Optional[dict]:
    """
    Get a single entity by ID with full context for agent reasoning.
    
    **Agent usage:**
    Use this when you need to verify specific facts about an entity.
    Always check the returned structure before making claims.
    
    ```python
    result = cmdb_get("ollama")
    if result["exists"]:
        print(f"Facts: {result['facts']}")
        print(f"Relations: {result['relations']}")
        print(f"Confidence: {result['confidence']}")
    ```
    
    Args:
        entity_id: The entity ID (e.g., "ollama", "server-53", "mysql")
        entities_dir: Path to entities directory
    
    Returns:
        Structured response with facts, relations, and confidence.
        
        Example:
        ```python
        {
            "exists": True,
            "entity": {
                "id": "ollama",
                "kind": "software",
                "status": "operational",
                "metadata": {...},
            },
            "facts": [
                "Ollama is a software entity",
                "Current status: operational",
                "Version: 0.5"
            ],
            "relations": {
                "runs_on": ["server-53"],
                "uses": ["docker"],
                "reads": [],
                "writes": [],
                "calls": [],
                "owned_by": [],
                "backs_up": [],
                "monitors_by": []
            },
            "criticality": {
                "business": "medium",
                "operational": "high",
                "technical": "low",
                "derived_classification": "IMPORTANT"
            },
            "source": {
                "type": "cmdb",
                "file": "/home/carlos/registry/software/ollama.yaml",
                "verified_at": "2026-06-22T19:45:00"
            },
            "confidence": "verified"
        }
        ```
        
        If entity not found:
        ```python
        {
            "exists": False,
            "entity_id": "redis",
            "reason": "Entity not found in CMDB",
            "similar_entities": ["ollama", "mysql"],
            "confidence": "verified_absence"
        }
        ```
    """
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    entities, paths = load_entities_with_paths(entities_dir)
    
    if entity_id not in entities:
        # Entity not found — return structured absence
        similar = []
        query_lower = entity_id.lower()
        for eid in entities.keys():
            if query_lower in eid.lower():
                similar.append(eid)
        
        return {
            "exists": False,
            "entity_id": entity_id,
            "reason": "Entity not found in CMDB",
            "similar_entities": similar[:5],
            "confidence": "verified_absence",
        }
    
    entity = entities[entity_id]
    entity_file = paths.get(entity_id, "unknown")
    
    # Extract facts from entity
    facts = []
    metadata = entity.get("metadata", {})
    
    facts.append(f"{entity.get('kind', 'unknown').title()} entity: {entity_id}")
    
    if entity.get("status"):
        facts.append(f"Status: {entity['status']}")
    
    if metadata.get("name"):
        facts.append(f"Name: {metadata['name']}")
    
    if metadata.get("version"):
        facts.append(f"Version: {metadata['version']}")
    
    if metadata.get("description"):
        facts.append(f"Description: {metadata['description'][:100]}...")
    
    # Group relations by type
    relations = {
        "runs_on": [],
        "uses": [],
        "reads": [],
        "writes": [],
        "calls": [],
        "owns": [],
        "owns_by": [],
        "backs_up": [],
        "monitors": [],
        "monitors_by": [],
    }
    
    for rel in entity.get("relations", []):
        rel_type = rel.get("type")
        rel_target = rel.get("target")
        
        if rel_type in relations:
            relations[rel_type].append(rel_target)
        
        # Reverse relations
        if rel_type == "owns" and rel_target == entity_id:
            relations["owns_by"].append(rel.get("source"))
        if rel_type == "monitors" and rel_target == entity_id:
            relations["monitors_by"].append(rel.get("source"))
    
    # Remove empty relation types
    relations = {k: v for k, v in relations.items() if v}
    
    # Derive criticality classification
    criticality = entity.get("criticality", {})
    derived_class = "MENOR"
    if criticality:
        biz = criticality.get("business", "low")
        ops = criticality.get("operational", "low")
        if biz == "high" and ops == "high":
            derived_class = "CRÍTICO"
        elif biz == "high" or ops == "high":
            derived_class = "IMPORTANTE"
    
    return {
        "exists": True,
        "entity": {
            "id": entity_id,
            "kind": entity.get("kind"),
            "status": entity.get("status"),
            "metadata": metadata,
        },
        "facts": facts,
        "relations": relations,
        "criticality": {
            **criticality,
            "derived_classification": derived_class,
        } if criticality else None,
        "source": {
            "type": "cmdb",
            "file": str(entity_file),
            "verified_at": datetime.now().isoformat(),
        },
        "confidence": "verified",
    }


def cmdb_search(query: str, entities_dir: Optional[Path] = None) -> list[dict]:
    """
    Search entities by name, description, or tags (case-insensitive).
    
    **Agent usage:**
    Use this when the user mentions something but you're not sure of the exact ID.
    Always search before assuming non-existence.
    
    ```python
    results = cmdb_search("telegram")
    if results:
        print(f"Found {len(results)} entities:")
        for r in results:
            print(f"  - {r['id']} ({r['kind']})")
    else:
        print("No entities found — ask for clarification")
    ```
    
    Args:
        query: Search term (e.g., "telegram", "mysql", "backup")
        entities_dir: Path to entities directory
    
    Returns:
        List of matching entities with match info.
        
        Example:
        ```python
        [
            {
                "id": "telegram-api",
                "kind": "endpoint",
                "metadata": {"name": "Telegram Bot API"},
                "match_field": "metadata.name",
                "score": 0.95
            },
            {
                "id": "notification-bot",
                "kind": "automation",
                "metadata": {"name": "Telegram Notification Bot"},
                "match_field": "description",
                "score": 0.85
            }
        ]
        ```
    """
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    entities, _ = load_entities_with_paths(entities_dir)
    
    query_lower = query.lower()
    results = []
    
    for entity_id, entity in entities.items():
        score = 0.0
        match_field = None
        
        # Search in ID
        if query_lower in entity_id.lower():
            score = max(score, 0.9)
            match_field = "id"
        
        # Search in metadata.name
        name = entity.get("metadata", {}).get("name", "")
        if query_lower in name.lower():
            score = max(score, 0.95)
            match_field = "metadata.name"
        
        # Search in metadata.description
        desc = entity.get("metadata", {}).get("description", "")
        if desc and query_lower in desc.lower():
            score = max(score, 0.85)
            match_field = "metadata.description"
        
        # Search in tags
        tags = entity.get("tags", [])
        if any(query_lower in tag.lower() for tag in tags):
            score = max(score, 0.80)
            match_field = "tags"
        
        # Search in relations (target IDs)
        relations = entity.get("relations", [])
        for rel in relations:
            target = rel.get("target", "")
            if query_lower in target.lower():
                score = max(score, 0.75)
                match_field = f"relations[].target ({target})"
                break
        
        if score > 0:
            results.append({
                "id": entity_id,
                "kind": entity.get("kind"),
                "metadata": entity.get("metadata", {}),
                "status": entity.get("status"),
                "match_field": match_field,
                "score": score,
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results


def cmdb_list(kind: Optional[str] = None, status: Optional[str] = None, entities_dir: Optional[Path] = None) -> list[dict]:
    """
    List entities, optionally filtered by kind and/or status.
    
    **Agent usage:**
    Use this to enumerate all entities of a type or status.
    
    ```python
    # List all software
    software = cmdb_list(kind="software")
    
    # List all operational assets
    assets = cmdb_list(kind="asset", status="operational")
    
    # List everything that's down
    down = cmdb_list(status="down")
    ```
    
    Args:
        kind: Filter by kind (asset, software, automation, data, endpoint)
        status: Filter by status (operational, degraded, down, deprecated)
        entities_dir: Path to entities directory
    
    Returns:
        List of entity dicts (without full relations for brevity).
    """
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    entities, _ = load_entities_with_paths(entities_dir)
    
    results = []
    for entity in entities.values():
        if kind and entity.get("kind") != kind:
            continue
        if status and entity.get("status") != status:
            continue
        
        # Return abbreviated entity (exclude heavy fields)
        results.append({
            "id": entity.get("id"),
            "kind": entity.get("kind"),
            "metadata": entity.get("metadata", {}),
            "status": entity.get("status"),
        })
    
    return results


def cmdb_validate(entities_dir: Optional[Path] = None) -> dict:
    """
    Validate all entities in the CMDB.
    
    **Agent usage:**
    Use this to check CMDB health before making assertions.
    If validation fails, warn the user that facts may be unreliable.
    
    ```python
    health = cmdb_validate()
    if not health["valid"]:
        print(f"⚠️  CMDB has {len(health['errors'])} errors — facts may be unreliable")
    ```
    
    Args:
        entities_dir: Path to entities directory
    
    Returns:
        Validation result with:
        - valid: bool
        - errors: list of error dicts
        - warnings: list of warning dicts
        - stats: counts by kind and status
    """
    # Import from validator to avoid circular import
    from .validator import cmdb_validate as validate_impl
    return validate_impl(entities_dir)


# Helper: load entities with paths (needed for cmdb_get)
def load_entities_with_paths(entities_dir: Path) -> tuple[dict, dict]:
    """Load entities and their file paths."""
    import yaml
    entities = {}
    entity_paths = {}
    
    if not entities_dir.exists():
        return entities, entity_paths
    
    for yaml_file in entities_dir.rglob("*.yaml"):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                entity = yaml.safe_load(f)
            
            if entity and "id" in entity:
                entities[entity["id"]] = entity
                entity_paths[entity["id"]] = yaml_file
        except:
            continue
    
    return entities, entity_paths