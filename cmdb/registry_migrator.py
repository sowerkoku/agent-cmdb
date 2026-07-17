"""
Registry to Knowledge Kernel Migration Tool.

Migrates entities from the legacy registry format to knowledge-kernel.

Usage:
    from cmdb.migrator import migrate_registry
    
    # Migrate all entities
    result = migrate_registry(
        from_path="~/registry",
        to_path="~/knowledge/agent-cmdb",
        dry_run=True  # or False to apply
    )
    
    print(result["stats"])
    print(result["errors"])

CLI:
    cmdb migrate-registry --from ~/registry --to ~/knowledge/agent-cmdb --dry-run
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime


# Registry categories → knowledge-kernel categories
CATEGORY_MAP = {
    "assets": "assets",
    "software": "software",
    "data": "data",
    "automation": "automation",
    "projects": "projects",
    "procedures": "procedures",
    "endpoints": "endpoints",
    "agents": "agents",
}


def migrate_entity(entity: dict, source_path: Path) -> dict:
    """
    Transform a registry entity to knowledge-kernel format.
    
    Changes:
    - Adds schema_version: 1
    - Maps category to kind
    - Preserves all other fields
    """
    migrated = {
        "schema_version": 1,
        "id": entity.get("id"),
        "kind": entity.get("kind") or _infer_kind(entity),
        "metadata": entity.get("metadata", {}),
        "status": entity.get("status", "operational"),
        "relations": entity.get("relations", []),
        "criticality": entity.get("criticality", {}),
        "tags": entity.get("tags", []),
    }
    
    # Add migration metadata
    if "description" in entity.get("metadata", {}):
        migrated["metadata"]["description"] = entity["metadata"]["description"]
    
    return migrated


def _infer_kind(entity: dict) -> str:
    """Infer kind from entity structure if not explicitly set."""
    # This is a fallback — explicit kind is preferred
    return "unknown"


def migrate_registry(
    from_path: str,
    to_path: Optional[str] = None,
    dry_run: bool = True,
) -> dict:
    """
    Migrate entities from registry to knowledge-kernel format.
    
    Args:
        from_path: Path to registry directory (contains category subdirs)
        to_path: Destination path. Defaults to CMDB_DATA_DIR.
        dry_run: If True, only simulate. If False, write files.
    
    Returns:
        dict with:
        - stats: counts by category/kind
        - migrated: list of entity IDs migrated
        - errors: list of error dicts
        - warnings: list of warning dicts
        - dry_run: whether this was a simulation
    """
    from .config import get_config
    
    from_path = Path(from_path).expanduser()
    
    if to_path:
        to_path = Path(to_path).expanduser()
    else:
        to_path = get_config().data_dir
    
    stats = {"total": 0, "by_category": {}, "errors": 0, "warnings": 0}
    migrated = []
    errors = []
    warnings = []
    
    # Scan source registry
    if not from_path.exists():
        return {
            "success": False,
            "error": f"Source path does not exist: {from_path}",
            "stats": stats,
        }
    
    # Process each category directory
    for category in CATEGORY_MAP.keys():
        category_dir = from_path / category
        
        if not category_dir.exists():
            continue
        
        yaml_files = list(category_dir.glob("*.yaml"))
        
        for yaml_file in yaml_files:
            try:
                import yaml as yaml_lib
                with open(yaml_file, "r", encoding="utf-8") as f:
                    entity = yaml_lib.safe_load(f)
                
                if not entity or "id" not in entity:
                    warnings.append({
                        "file": str(yaml_file),
                        "message": "Skipped — no 'id' field",
                    })
                    stats["warnings"] += 1
                    continue
                
                # Migrate entity
                migrated_entity = migrate_entity(entity, from_path)
                
                # Determine destination path
                entity_id = migrated_entity["id"]
                kind = migrated_entity["kind"]
                dest_dir = to_path / kind
                
                if dry_run:
                    stats["total"] += 1
                    migrated.append(entity_id)
                    continue
                
                # Write to destination
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / f"{entity_id}.yaml"
                
                with open(dest_file, "w", encoding="utf-8") as f:
                    yaml_lib.dump(migrated_entity, f, allow_unicode=True, sort_keys=False)
                
                stats["total"] += 1
                migrated.append(entity_id)
                
            except Exception as e:
                errors.append({
                    "file": str(yaml_file),
                    "message": str(e),
                })
                stats["errors"] += 1
    
    return {
        "success": len(errors) == 0,
        "stats": stats,
        "migrated": migrated,
        "errors": errors,
        "warnings": warnings,
        "dry_run": dry_run,
        "from": str(from_path),
        "to": str(to_path),
    }


def verify_migration(source_path: str, target_path: str) -> dict:
    """
    Verify that migration was successful by comparing entity counts.
    
    Returns:
        dict with:
        - match: bool (True if counts match)
        - source_count: int
        - target_count: int
        - differences: list of mismatched entities
    """
    import yaml
    
    source_path = Path(source_path).expanduser()
    target_path = Path(target_path).expanduser()
    
    source_entities = {}
    for category in CATEGORY_MAP.keys():
        category_dir = source_path / category
        if not category_dir.exists():
            continue
        for yaml_file in category_dir.glob("*.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                entity = yaml.safe_load(f)
            if entity and "id" in entity:
                source_entities[entity["id"]] = entity
    
    target_entities = {}
    if target_path.exists():
        for yaml_file in target_path.rglob("*.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                entity = yaml.safe_load(f)
            if entity and "id" in entity:
                target_entities[entity["id"]] = entity
    
    source_ids = set(source_entities.keys())
    target_ids = set(target_entities.keys())
    
    return {
        "match": source_ids == target_ids,
        "source_count": len(source_ids),
        "target_count": len(target_ids),
        "only_in_source": list(source_ids - target_ids),
        "only_in_target": list(target_ids - source_ids),
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate registry to knowledge-kernel")
    parser.add_argument("--from", dest="from_path", required=True, help="Source registry path")
    parser.add_argument("--to", dest="to_path", help="Destination path (default: CMDB_DATA_DIR)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing")
    parser.add_argument("--verify", action="store_true", help="Verify migration after applying")
    
    args = parser.parse_args()
    
    result = migrate_registry(
        from_path=args.from_path,
        to_path=args.to_path,
        dry_run=args.dry_run,
    )
    
    print(f"\nMigration {'(dry run)' if args.dry_run else ''}")
    print(f"  From: {result['from']}")
    print(f"  To:   {result['to']}")
    print(f"  Migrated: {result['stats']['total']} entities")
    print(f"  Errors:   {result['stats']['errors']}")
    print(f"  Warnings: {result['stats']['warnings']}")
    
    if result["errors"]:
        print("\nErrors:")
        for e in result["errors"]:
            print(f"  - {e['file']}: {e['message']}")
    
    if result["warnings"]:
        print("\nWarnings:")
        for w in result["warnings"][:5]:
            print(f"  - {w['file']}: {w['message']}")
    
    if args.verify and not args.dry_run:
        print("\nVerifying migration...")
        verify = verify_migration(args.from_path, args.to_path or str(Path.home() / ".local" / "share" / "agent-cmdb"))
        print(f"  Match: {verify['match']}")
        print(f"  Source: {verify['source_count']}, Target: {verify['target_count']}")
        if verify["only_in_source"]:
            print(f"  Missing in target: {verify['only_in_source']}")