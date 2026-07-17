"""
CMDB Migrator — Agent CMDB v0 → v1 Migration

Migrates entities from legacy v0 format (depends_on, runs_on, no schema_version)
to schema v1 format with typed relations and explicit criticality.

API:
    cmdb_migrate_dry_run(entities_dir) -> MigrationPlan
    cmdb_migrate_apply(entities_dir) -> MigrationResult

CLI:
    python -m cmdb.migrator --dry-run
    python -m cmdb.migrator --apply
"""

import os
import yaml
import json
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from .validator import load_entities_with_paths, cmdb_validate


# =============================================================================
# Migration Rules
# =============================================================================

# Kind inference from folder name
FOLDER_TO_KIND = {
    "assets": "asset",
    "software": "software",
    "automation": "automation",
    "data": "data",
    "endpoints": "endpoint",
    "agents": "software",  # Pending: agent as separate kind
    "projects": "software",  # TBD
    "procedures": "automation",  # Runbooks as automation
}

# Status migration table
STATUS_MIGRATION = {
    "operational": {"new_status": "operational", "criticality": None},
    "ATIVO": {"new_status": "operational", "criticality": None},
    "degraded": {"new_status": "degraded", "criticality": None},
    "down": {"new_status": "down", "criticality": None},
    "deprecated": {"new_status": "deprecated", "criticality": None},
    "powered-off": {"new_status": "down", "criticality": None},
    "stopped": {"new_status": "down", "criticality": None},
    "construction": {"new_status": "deprecated", "criticality": None, "warning": "manual_review_required"},
    "critical": {"new_status": "operational", "criticality": {"business": "high", "operational": "high", "technical": "medium"}},
}

# Relation migration: legacy field → v1 relation type
RELATION_MIGRATION = {
    "depends_on": "uses",
    "runs_on": "runs_on",
    "reads": "reads",
    "writes": "writes",
    "calls": "calls",
    "owns": "owns",
    "backs_up": "backs_up",
    "monitors": "monitors",
}


class MigrationPlan:
    """Represents a planned migration (dry-run)."""
    
    def __init__(self):
        self.entities_to_migrate = []  # List of MigrationEntity
        self.errors = []
        self.warnings = []
        self.stats = {
            "total_entities": 0,
            "kind_inferred": 0,
            "status_migrated": 0,
            "relations_migrated": 0,
            "manual_review_required": 0,
        }
    
    def to_dict(self) -> dict:
        return {
            "entities": [e.to_dict() for e in self.entities_to_migrate],
            "errors": self.errors,
            "warnings": self.warnings,
            "stats": self.stats,
        }
    
    def to_markdown(self) -> str:
        lines = [
            "# Migration Plan — v0 → v1",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            "## Summary",
            "",
            f"- Total entities: {self.stats['total_entities']}",
            f"- Kind inferred: {self.stats['kind_inferred']}",
            f"- Status migrated: {self.stats['status_migrated']}",
            f"- Relations migrated: {self.stats['relations_migrated']}",
            f"- Manual review required: {self.stats['manual_review_required']}",
            "",
        ]
        
        if self.errors:
            lines.extend([
                "## Errors (blocking)",
                "",
            ])
            for err in self.errors[:20]:
                lines.append(f"- {err}")
            if len(self.errors) > 20:
                lines.append(f"- ... and {len(self.errors) - 20} more")
            lines.append("")
        
        if self.warnings:
            lines.extend([
                "## Warnings",
                "",
            ])
            for warn in self.warnings[:20]:
                lines.append(f"- {warn}")
            if len(self.warnings) > 20:
                lines.append(f"- ... and {len(self.warnings) - 20} more")
            lines.append("")
        
        return "\n".join(lines)


class MigrationEntity:
    """Represents a single entity migration."""
    
    def __init__(self, entity_id: str, source_path: Path, target_path: Path):
        self.entity_id = entity_id
        self.source_path = source_path
        self.target_path = target_path
        self.original = None  # Original v0 entity dict
        self.migrated = None  # Migrated v1 entity dict
        self.changes = []  # List of change descriptions
        self.errors = []
        self.warnings = []
    
    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "source_path": str(self.source_path),
            "target_path": str(self.target_path),
            "changes": self.changes,
            "errors": self.errors,
            "warnings": self.warnings,
            "migrated_entity": self.migrated,
        }


def infer_kind_from_path(entity_path: Path) -> Optional[str]:
    """Infer kind from folder structure."""
    # Check parent folder name
    parent = entity_path.parent.name
    
    if parent in FOLDER_TO_KIND:
        return FOLDER_TO_KIND[parent]
    
    # Check if any ancestor folder matches
    for ancestor in entity_path.parents:
        if ancestor.name in FOLDER_TO_KIND:
            return FOLDER_TO_KIND[ancestor.name]
    
    return None


def migrate_status(original_status: str, entity_id: str) -> tuple[str, Optional[dict], list]:
    """
    Migrate status from v0 to v1.
    
    Returns: (new_status, criticality, warnings)
    """
    warnings = []
    
    if original_status in STATUS_MIGRATION:
        rule = STATUS_MIGRATION[original_status]
        new_status = rule["new_status"]
        criticality = rule.get("criticality")
        
        if rule.get("warning"):
            warnings.append(f"Status '{original_status}' → '{new_status}' ({rule['warning']})")
        
        return new_status, criticality, warnings
    
    # Unknown status — keep as-is but warn
    warnings.append(f"Unknown status '{original_status}' — keeping unchanged (manual review required)")
    return original_status, None, warnings


def migrate_relations(original: dict, all_entities: dict, entity_id: str) -> tuple[list, list, list]:
    """
    Migrate legacy relations (depends_on, runs_on, etc.) to v1 typed relations.
    
    Handles both formats:
    - v0 flat fields: depends_on: [x, y], runs_on: server
    - v0 nested: relations: {runs_on: [x], depends_on: [y]}
    
    Returns: (relations, errors, warnings)
    """
    relations = []
    errors = []
    warnings = []
    
    # Check for nested relations format (v0.5)
    if "relations" in original and isinstance(original["relations"], dict):
        v0_relations = original["relations"]
        
        for legacy_field, targets in v0_relations.items():
            if legacy_field not in RELATION_MIGRATION:
                warnings.append(f"Unknown relation type '{legacy_field}' — skipping")
                continue
            
            relation_type = RELATION_MIGRATION[legacy_field]
            
            # Handle list (runs_on: [x, y])
            if isinstance(targets, list):
                for target in targets:
                    if isinstance(target, str):
                        # Validate target exists
                        if target not in all_entities:
                            warnings.append(f"Unresolved relation: {relation_type} → {target} (target does not exist)")
                        
                        relations.append({
                            "type": relation_type,
                            "target": target,
                        })
            
            # Handle string (runs_on: server)
            elif isinstance(targets, str):
                target = targets
                
                # Validate target exists
                if target not in all_entities:
                    warnings.append(f"Unresolved relation: {relation_type} → {target} (target does not exist)")
                
                relations.append({
                    "type": relation_type,
                    "target": target,
                })
    
    # Also check for flat fields (legacy v0)
    for legacy_field, relation_type in RELATION_MIGRATION.items():
        # Skip if already processed from nested relations
        if "relations" in original and isinstance(original["relations"], dict) and legacy_field in original["relations"]:
            continue
        
        if legacy_field not in original:
            continue
        
        legacy_value = original[legacy_field]
        
        # Handle list (depends_on: [x, y])
        if isinstance(legacy_value, list):
            for target in legacy_value:
                if isinstance(target, str):
                    # Validate target exists
                    if target not in all_entities:
                        warnings.append(f"Unresolved relation: {relation_type} → {target} (target does not exist)")
                    
                    relations.append({
                        "type": relation_type,
                        "target": target,
                    })
        
        # Handle string (runs_on: server)
        elif isinstance(legacy_value, str):
            target = legacy_value
            
            # Validate target exists
            if target not in all_entities:
                warnings.append(f"Unresolved relation: {relation_type} → {target} (target does not exist)")
            
            relations.append({
                "type": relation_type,
                "target": target,
            })
    
    return relations, errors, warnings


def migrate_entity(entity: dict, entity_path: Path, all_entities: dict, output_dir: Path) -> MigrationEntity:
    """Migrate a single entity from v0 to v1."""
    entity_id = entity.get("id", "<unknown>")
    
    # Infer kind from folder
    inferred_kind = infer_kind_from_path(entity_path)
    
    mig_entity = MigrationEntity(
        entity_id=entity_id,
        source_path=entity_path,
        target_path=output_dir / entity_path.relative_to(output_dir.parent),
    )
    mig_entity.original = entity.copy()
    
    # Error if kind cannot be inferred
    if inferred_kind is None:
        mig_entity.errors.append(f"Cannot infer kind from path {entity_path.parent} — manual classification required")
        return mig_entity
    
    mig_entity.changes.append(f"kind: (none) → {inferred_kind!r}")
    
    # Build migrated entity
    migrated = {
        "schema_version": 1,
        "id": entity_id,
        "kind": inferred_kind,
        "metadata": {},
        "status": "operational",
        "relations": [],
    }
    
    # Migrate metadata
    if "name" in entity:
        migrated["metadata"]["name"] = entity["name"]
        mig_entity.changes.append(f"metadata.name: {entity['name']!r}")
    elif "metadata" in entity and isinstance(entity["metadata"], dict):
        migrated["metadata"] = entity["metadata"].copy()
        mig_entity.changes.append("metadata: preserved from v0")
    else:
        # Generate name from id
        migrated["metadata"]["name"] = entity_id.replace("-", " ").title()
        mig_entity.changes.append(f"metadata.name: generated from id")
    
    if "description" in entity:
        migrated["metadata"]["description"] = entity["description"]
        mig_entity.changes.append(f"metadata.description: preserved")
    
    # Migrate status
    original_status = entity.get("status", "operational")
    new_status, criticality, status_warnings = migrate_status(original_status, entity_id)
    migrated["status"] = new_status
    mig_entity.changes.append(f"status: {original_status!r} → {new_status!r}")
    mig_entity.warnings.extend(status_warnings)
    
    if criticality:
        migrated["criticality"] = criticality
        mig_entity.changes.append(f"criticality: added {criticality}")
    
    # Migrate criticality from v0 (if exists)
    if "criticality" in entity:
        v0_criticality = entity["criticality"]
        if isinstance(v0_criticality, dict):
            # Migrate v0 criticality (may have invalid values like "critical")
            migrated_criticality = {}
            for dim in ["business", "operational", "technical"]:
                if dim in v0_criticality:
                    v0_value = v0_criticality[dim]
                    # Map "critical" → "high"
                    if v0_value == "critical":
                        migrated_criticality[dim] = "high"
                        mig_entity.changes.append(f"criticality.{dim}: 'critical' → 'high'")
                    elif v0_value in ["high", "medium", "low"]:
                        migrated_criticality[dim] = v0_value
                    else:
                        migrated_criticality[dim] = "medium"  # Default
                        mig_entity.warnings.append(f"Unknown criticality.{dim} value '{v0_value}' → 'medium'")
            
            if migrated_criticality and not criticality:  # Don't override status-based criticality
                migrated["criticality"] = migrated_criticality
    
    # Migrate relations
    relations, rel_errors, rel_warnings = migrate_relations(entity, all_entities, entity_id)
    migrated["relations"] = relations
    mig_entity.errors.extend(rel_errors)
    mig_entity.warnings.extend(rel_warnings)
    
    if relations:
        mig_entity.changes.append(f"relations: {len(relations)} relations migrated")
    
    # Remove legacy fields from metadata (they're now in relations)
    for legacy_field in RELATION_MIGRATION.keys():
        if legacy_field in migrated.get("metadata", {}):
            del migrated["metadata"][legacy_field]
    
    mig_entity.migrated = migrated
    
    return mig_entity


def cmdb_migrate_dry_run(entities_dir: Optional[Path] = None) -> MigrationPlan:
    """
    Plan a migration from v0 to v1 without applying changes.
    
    Args:
        entities_dir: Path to entities directory (default: ~/knowledge-kernel/data/)
    
    Returns:
        MigrationPlan with full details of what would change
    """
    entities_dir = entities_dir or Path.home() / "agent-cmdb" / "data"
    plan = MigrationPlan()
    
    if not entities_dir.exists():
        plan.errors.append(f"Entities directory does not exist: {entities_dir}")
        return plan
    
    # Load all v0 entities with their file paths
    v0_entities, v0_paths = load_entities_with_paths(entities_dir)
    plan.stats["total_entities"] = len(v0_entities)
    
    # Migrate each entity
    for entity_id, entity in v0_entities.items():
        # Get the entity file path from the loaded paths
        entity_file = v0_paths.get(entity_id)
        
        if entity_file is None:
            plan.errors.append(f"Entity {entity_id!r}: file not found")
            continue
        
        mig_entity = migrate_entity(entity, entity_file, v0_entities, entities_dir)
        plan.entities_to_migrate.append(mig_entity)
        plan.errors.extend([f"{entity_id}: {e}" for e in mig_entity.errors])
        plan.warnings.extend([f"{entity_id}: {w}" for w in mig_entity.warnings])
        
        # Update stats
        if mig_entity.migrated:
            plan.stats["kind_inferred"] += 1
            if mig_entity.migrated.get("status") != entity.get("status"):
                plan.stats["status_migrated"] += 1
            if mig_entity.migrated.get("relations"):
                plan.stats["relations_migrated"] += len(mig_entity.migrated["relations"])
        
        if mig_entity.warnings:
            plan.stats["manual_review_required"] += 1
    
    return plan


def cmdb_migrate_apply(entities_dir: Optional[Path] = None, backup_dir: Optional[Path] = None) -> dict:
    """
    Apply migration from v0 to v1.
    
    Args:
        entities_dir: Path to entities directory
        backup_dir: Path to backup directory (default: creates timestamped backup)
    
    Returns:
        dict with migration results
    """
    entities_dir = entities_dir or Path.home() / "agent-cmdb" / "data"
    
    # Create backup
    if backup_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = entities_dir.parent / f"registry-v0-backup-{timestamp}"
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup all entities
    for yaml_file in entities_dir.rglob("*.yaml"):
        rel_path = yaml_file.relative_to(entities_dir)
        target_path = backup_dir / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(yaml_file, target_path)
    
    # Run dry-run first
    plan = cmdb_migrate_dry_run(entities_dir)
    
    if plan.errors:
        # Block migration if there are errors
        return {
            "success": False,
            "error": "Migration blocked due to errors. Run with --dry-run to review.",
            "errors": plan.errors,
            "backup_path": str(backup_dir),
        }
    
    # Apply migration
    migrated_count = 0
    for mig_entity in plan.entities_to_migrate:
        if mig_entity.migrated:
            # Write migrated entity
            mig_entity.target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(mig_entity.target_path, "w", encoding="utf-8") as f:
                yaml.dump(mig_entity.migrated, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            migrated_count += 1
    
    # Validate after migration
    validation = cmdb_validate(entities_dir)
    
    return {
        "success": validation["valid"],
        "entities_migrated": migrated_count,
        "backup_path": str(backup_dir),
        "validation": validation,
    }


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CMDB Migrator — v0 → v1")
    parser.add_argument("--dry-run", action="store_true", help="Plan migration without applying")
    parser.add_argument("--apply", action="store_true", help="Apply migration (creates backup first)")
    parser.add_argument("--entities-dir", type=Path, default=Path.home() / "agent-cmdb" / "data", help="Entities directory")
    parser.add_argument("--output", type=Path, help="Output directory for migration plan (dry-run only)")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        parser.print_help()
        print("\nError: Must specify --dry-run or --apply")
        exit(1)
    
    if args.dry_run:
        print("Running migration dry-run...")
        plan = cmdb_migrate_dry_run(args.entities_dir)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Migration Plan Summary")
        print(f"{'='*60}")
        print(f"Total entities: {plan.stats['total_entities']}")
        print(f"Kind inferred: {plan.stats['kind_inferred']}")
        print(f"Status migrated: {plan.stats['status_migrated']}")
        print(f"Relations migrated: {plan.stats['relations_migrated']}")
        print(f"Manual review required: {plan.stats['manual_review_required']}")
        print(f"{'='*60}")
        
        if plan.errors:
            print(f"\n❌ Errors ({len(plan.errors)}) — must fix before migration:")
            for err in plan.errors[:10]:
                print(f"  - {err}")
            if len(plan.errors) > 10:
                print(f"  ... and {len(plan.errors) - 10} more")
        
        if plan.warnings:
            print(f"\n⚠️  Warnings ({len(plan.warnings)}):")
            for warn in plan.warnings[:10]:
                print(f"  - {warn}")
            if len(plan.warnings) > 10:
                print(f"  ... and {len(plan.warnings) - 10} more")
        
        # Write migration plan files
        output_dir = args.output or Path("migration")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON plan
        plan_json_path = output_dir / "migration-plan.json"
        with open(plan_json_path, "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"\n✅ Migration plan written to: {plan_json_path}")
        
        # Markdown report
        plan_md_path = output_dir / "migration-plan.md"
        with open(plan_md_path, "w", encoding="utf-8") as f:
            f.write(plan.to_markdown())
        print(f"✅ Migration report written to: {plan_md_path}")
        
        if plan.errors:
            print(f"\n❌ Migration cannot proceed. Fix errors and re-run.")
            exit(1)
        else:
            print(f"\n✅ Ready to migrate. Run with --apply to proceed.")
            exit(0)
    
    elif args.apply:
        print("Applying migration...")
        result = cmdb_migrate_apply(args.entities_dir)
        
        if result["success"]:
            print(f"\n{'='*60}")
            print(f"✅ Migration COMPLETE")
            print(f"{'='*60}")
            print(f"Entities migrated: {result['entities_migrated']}")
            print(f"Backup location: {result['backup_path']}")
            print(f"Validation: {result['validation']['valid']}")
            print(f"Remaining errors: {len(result['validation']['errors'])}")
            print(f"Remaining warnings: {len(result['validation']['warnings'])}")
            exit(0)
        else:
            print(f"\n{'='*60}")
            print(f"❌ Migration FAILED")
            print(f"{'='*60}")
            print(f"Error: {result['error']}")
            if "errors" in result:
                for err in result["errors"][:10]:
                    print(f"  - {err}")
            exit(1)