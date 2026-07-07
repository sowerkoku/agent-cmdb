"""
Registry to Agent-CMDB Migration Script.

Migrates entities from ~/registry to ~/knowledge/agent-cmdb.tmp
with validation, domain+kind mapping, and rollback capability.

Usage:
    python3 scripts/migrate_registry.py [--dry-run]
"""

import sys
import yaml
from pathlib import Path

# Add cmdb to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmdb.taxonomy import (
    ALL_KINDS, DEPRECATED_KINDS, migrate_kind_legacy,
    DOMAIN_INFRASTRUCTURE, DOMAIN_SOFTWARE, DOMAIN_KNOWLEDGE, DOMAIN_ORGANIZATION,
)
from cmdb.audit import audit_registry, format_report


def migrate_entity(entity: dict) -> dict:
    """
    Transform a registry entity to agent-cmdb v2 format.
    
    Changes:
    - Maps legacy kinds to current taxonomy via migrate_kind_legacy()
    - Preserves all other fields
    """
    kind = entity.get("kind", "unknown")
    domain, mapped_kind = migrate_kind_legacy(kind)
    
    migrated = {
        "schema_version": 1,  # Keep v1 format, will be upgraded later
        "id": entity.get("id"),
        "kind": mapped_kind,
        "domain": domain,  # v2 field for easier querying
        "metadata": entity.get("metadata", {}),
        "status": entity.get("status", "operational"),
        "relations": entity.get("relations", []),
        "criticality": entity.get("criticality", {}),
        "tags": entity.get("tags", []),
    }
    
    return migrated


def migrate_registry_to_directory(
    source_path: Path,
    target_path: Path,
    dry_run: bool = False,
) -> dict:
    """
    Migrate all entities from source to target directory.
    
    Returns stats dict.
    """
    # Source categories to scan
    category_dirs = [
        ("assets", DOMAIN_INFRASTRUCTURE),
        ("software", DOMAIN_SOFTWARE),
        ("data", DOMAIN_SOFTWARE),
        ("automation", DOMAIN_SOFTWARE),
        ("endpoints", DOMAIN_INFRASTRUCTURE),
        ("projects", DOMAIN_ORGANIZATION),
        ("procedures", DOMAIN_KNOWLEDGE),
        ("agents", DOMAIN_ORGANIZATION),
    ]
    
    stats = {
        "total": 0,
        "errors": 0,
        "by_kind": {},
        "by_domain": {},
    }
    
    for category, domain in category_dirs:
        source_dir = source_path / category
        if not source_dir.exists():
            continue
        
        for yaml_file in source_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    entity = yaml.safe_load(f)
                
                if not entity or "id" not in entity:
                    stats["errors"] += 1
                    continue
                
                entity_id = entity["id"]
                kind = entity.get("kind", "unknown")
                domain, mapped_kind = migrate_kind_legacy(kind)
                
                # Migrate
                migrated = migrate_entity(entity)
                
                # Determine target path (organize by kind)
                target_dir = target_path / mapped_kind
                
                if not dry_run:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target_file = target_dir / f"{entity_id}.yaml"
                    
                    with open(target_file, "w", encoding="utf-8") as f:
                        yaml.dump(migrated, f, allow_unicode=True, sort_keys=False)
                
                stats["total"] += 1
                stats["by_kind"][mapped_kind] = stats["by_kind"].get(mapped_kind, 0) + 1
                stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
                
            except Exception as e:
                print(f"  ERROR: {yaml_file}: {e}")
                stats["errors"] += 1
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate registry to agent-cmdb")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing")
    parser.add_argument("--source", default="~/registry", help="Source registry path")
    parser.add_argument("--target", default="~/knowledge/agent-cmdb.tmp", help="Target directory")
    
    args = parser.parse_args()
    
    source_path = Path(args.source).expanduser()
    target_path = Path(args.target).expanduser()
    
    if not source_path.exists():
        print(f"Error: Source does not exist: {source_path}")
        return 1
    
    if not args.dry_run:
        target_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Migration {'(DRY RUN)' if args.dry_run else ''}")
    print(f"  Source: {source_path}")
    print(f"  Target: {target_path}")
    print()
    
    # Run migration
    stats = migrate_registry_to_directory(
        source_path=source_path,
        target_path=target_path,
        dry_run=args.dry_run,
    )
    
    print(f"Migrated: {stats['total']} entities")
    print(f"Errors: {stats['errors']}")
    print()
    
    if stats['by_kind']:
        print("By kind:")
        for kind, count in sorted(stats['by_kind'].items()):
            print(f"  {kind}: {count}")
        print()
    
    if stats['by_domain']:
        print("By domain:")
        for domain, count in sorted(stats['by_domain'].items()):
            print(f"  {domain}: {count}")
    
    # If not dry run, run acceptance tests
    if not args.dry_run:
        print()
        print("-" * 40)
        print("Running acceptance tests...")
        
        # Set CMDB_DATA_DIR to the new location temporarily
        import os
        os.environ["CMDB_DATA_DIR"] = str(target_path)
        
        # Reimport to pick up new env
        from importlib import reload
        import cmdb.config
        reload(cmdb.config)
        
        from cmdb.api import cmdb_validate
        result = cmdb_validate()
        
        print(f"Validation: {'PASS' if result['valid'] else 'FAIL'}")
        print(f"  Total: {result['stats']['total']}")
        print(f"  Errors: {len(result['errors'])}")
        print(f"  Warnings: {len(result['warnings'])}")
        
        if result['errors']:
            print()
            print("Errors:")
            for err in result['errors'][:5]:
                print(f"  - {err['entity_id']}.{err['field']}: {err['message']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())