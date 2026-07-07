"""
Registry Audit Tool — Pre-migration analysis for agent-cmdb v2.

Does NOT write any files. Only analyzes and reports.

Usage:
    from cmdb.audit import audit_registry
    
    report = audit_registry(
        source_path="~/registry",
        target_schema_version=2,
        verbose=True
    )
    
    print(report.summary())
    print(report.detailed_report())

CLI:
    cmdb audit-registry --from ~/registry --verbose
"""

import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class AuditResult:
    """Result of auditing a single entity."""
    entity_id: str
    source_file: Path
    status: str  # "ok", "warning", "error", "skipped"
    schema_version: int | None
    domain: str | None
    kind: str | None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    relations_count: int = 0
    relations_broken: list[str] = field(default_factory=list)
    
    # Quality metrics
    has_owner: bool = False
    has_status: bool = True
    has_capability: bool = False
    is_duplicate: bool = False


@dataclass 
class AuditReport:
    """Complete audit report for the registry."""
    total_entities: int = 0
    by_domain: dict[str, int] = field(default_factory=dict)
    by_kind: dict[str, int] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)
    
    # Migration classification
    auto_migratable: int = 0
    requires_intervention: int = 0
    skipped: int = 0
    
    # Quality issues
    duplicate_ids: list[str] = field(default_factory=list)
    orphaned_entities: list[str] = field(default_factory=list)
    broken_relations: list[tuple[str, str]] = field(default_factory=list)  # (entity, missing_target)
    circular_dependencies: list[list[str]] = field(default_factory=list)
    missing_required_fields: list[tuple[str, str]] = field(default_factory=list)  # (entity, field)
    missing_owner: list[str] = field(default_factory=list)
    missing_status: list[str] = field(default_factory=list)
    missing_capability: list[str] = field(default_factory=list)
    
    # Schema analysis
    entities_v1: int = 0
    entities_v2: int = 0
    unknown_kinds: list[tuple[str, str]] = field(default_factory=list)  # (entity_id, kind)
    invalid_statuses: list[tuple[str, str]] = field(default_factory=list)
    
    # Per-entity results
    entity_results: list[AuditResult] = field(default_factory=list)
    
    # All entity IDs seen (for duplicate detection)
    _all_ids: set = field(default_factory=set)
    
    def register_id(self, entity_id: str) -> bool:
        """Register an entity ID. Returns True if duplicate."""
        if entity_id in self._all_ids:
            return True
        self._all_ids.add(entity_id)
        return False


def audit_entity(
    entity_id: str,
    entity: dict,
    source_file: Path,
    all_entity_ids: set[str],
    target_schema_version: int = 2,
) -> AuditResult:
    """Audit a single entity against schema v2."""
    from .taxonomy import (
        ALL_KINDS, VALID_DOMAINS, KIND_TO_DOMAIN, DEPRECATED_KINDS,
        migrate_kind_legacy,
        DOMAIN_INFRASTRUCTURE, DOMAIN_SOFTWARE, DOMAIN_KNOWLEDGE, DOMAIN_ORGANIZATION,
    )
    
    result = AuditResult(
        entity_id=entity_id,
        source_file=source_file,
        status="ok",
        schema_version=entity.get("schema_version"),
        domain=None,
        kind=entity.get("kind"),
    )
    
    # Detect schema version
    if entity.get("schema_version") == 2:
        result.domain = entity.get("domain")
    else:
        result.schema_version = 1  # legacy
    
    # Check kind validity — use migrate_kind_legacy for backwards compatibility
    kind = entity.get("kind", "unknown")
    domain, mapped_kind = migrate_kind_legacy(kind)
    
    result.kind = mapped_kind
    result.domain = domain
    
    # Only error if kind is truly unknown (not just legacy)
    if kind not in ALL_KINDS and kind not in DEPRECATED_KINDS:
        result.errors.append(f"Unknown kind: {kind!r}")
        result.status = "error"
    
    # Check required fields
    if "id" not in entity:
        result.errors.append("Missing 'id'")
        result.status = "error"
    
    if "metadata" not in entity:
        result.errors.append("Missing 'metadata'")
        result.status = "error"
    elif not isinstance(entity.get("metadata"), dict):
        result.errors.append("'metadata' must be an object")
        result.status = "error"
    elif "name" not in entity.get("metadata", {}):
        result.errors.append("Missing 'metadata.name'")
        result.status = "error"
    
    if "status" not in entity:
        result.warnings.append("Missing 'status'")
        result.status = "warning" if result.status == "ok" else result.status
    
    # Check status values
    status = entity.get("status")
    valid_statuses = {"operational", "degraded", "down", "deprecated"}
    if status and status not in valid_statuses:
        result.warnings.append(f"Unknown status: {status!r}")
        result.status = "warning" if result.status == "ok" else result.status
    
    # Quality checks based on domain/kind
    relations = entity.get("relations", [])
    result.relations_count = len(relations)
    
    if result.domain == DOMAIN_KNOWLEDGE:
        # Check for owner (recommended)
        if "owner" not in entity.get("metadata", {}) and "owned_by" not in str(entity.get("relations", [])):
            result.warnings.append("Knowledge entity without owner")
            result.has_owner = False
        else:
            result.has_owner = True
        
        # Check for capability (for agents)
        if kind == "agent" and "capability" not in entity.get("metadata", {}):
            result.warnings.append("Agent without capability metadata")
            result.has_capability = False
        else:
            result.has_capability = True
    
    if result.domain == DOMAIN_ORGANIZATION:
        if kind == "project":
            if "owner" not in entity.get("metadata", {}):
                result.warnings.append("Project without owner")
                result.has_owner = False
    
    # Validate relations
    for rel in relations:
        if not isinstance(rel, dict):
            continue
        
        rel_type = rel.get("type")
        rel_target = rel.get("target")
        
        if rel_target and rel_target not in all_entity_ids:
            result.relations_broken.append(f"{rel_type} -> {rel_target}")
            result.warnings.append(f"Broken relation: {rel_type} -> {rel_target}")
    
    return result


def audit_registry(
    source_path: str,
    target_schema_version: int = 2,
    verbose: bool = False,
) -> AuditReport:
    """
    Audit registry entities without writing anything.
    
    Returns AuditReport with detailed findings.
    """
    from .taxonomy import ALL_KINDS, KIND_TO_DOMAIN, DEPRECATED_KINDS, migrate_kind_legacy
    
    source_path = Path(source_path).expanduser()
    report = AuditReport()
    
    if not source_path.exists():
        print(f"Error: Source path does not exist: {source_path}")
        return report
    
    # Collect all entity IDs first (for relation validation)
    all_entity_ids = set()
    raw_entities = []
    
    category_dirs = [
        ("assets", "infrastructure"),
        ("software", "software"),
        ("data", "software"),
        ("automation", "software"),
        ("endpoints", "infrastructure"),
        ("projects", "organization"),
        ("procedures", "knowledge"),
        ("agents", "organization"),
    ]
    
    for category, _ in category_dirs:
        category_dir = source_path / category
        if not category_dir.exists():
            continue
        
        for yaml_file in category_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    entity = yaml.safe_load(f)
                
                if not entity or "id" not in entity:
                    continue
                
                entity_id = entity["id"]
                raw_entities.append((entity_id, entity, yaml_file))
                all_entity_ids.add(entity_id)
                
            except Exception as e:
                report.skipped += 1
    
    # First pass: detect duplicates
    seen_ids = set()
    for entity_id, entity, yaml_file in raw_entities:
        if entity_id in seen_ids:
            report.duplicate_ids.append(entity_id)
        seen_ids.add(entity_id)
    
    # Second pass: audit each entity
    for entity_id, entity, yaml_file in raw_entities:
        is_duplicate = entity_id in report.duplicate_ids
        
        # Audit
        result = audit_entity(
            entity_id=entity_id,
            entity=entity,
            source_file=yaml_file,
            all_entity_ids=all_entity_ids,
            target_schema_version=target_schema_version,
        )
        result.is_duplicate = is_duplicate
        
        report.entity_results.append(result)
        report.total_entities += 1
        
        # Schema version stats
        if entity.get("schema_version") == 2:
            report.entities_v2 += 1
        else:
            report.entities_v1 += 1
        
        # Domain/kind stats — use migrate_kind_legacy for legacy kinds
        kind = entity.get("kind", "unknown")
        domain, mapped_kind = migrate_kind_legacy(kind)
        
        report.by_domain[domain] = report.by_domain.get(domain, 0) + 1
        report.by_kind[mapped_kind] = report.by_kind.get(mapped_kind, 0) + 1
        report.by_status[entity.get("status", "unknown")] = report.by_status.get(entity.get("status"), 0) + 1
        
        # Classification
        if result.errors:
            report.requires_intervention += 1
        elif result.warnings:
            report.auto_migratable += 1
        else:
            report.auto_migratable += 1
        
        # Collect issues
        if result.warnings:
            if "without owner" in str(result.warnings):
                report.missing_owner.append(entity_id)
            if "without status" in str(result.warnings):
                report.missing_status.append(entity_id)
            if "without capability" in str(result.warnings):
                report.missing_capability.append(entity_id)
        
        for broken in result.relations_broken:
            report.broken_relations.append((entity_id, broken))
        
        if kind not in ALL_KINDS and kind not in DEPRECATED_KINDS:
            report.unknown_kinds.append((entity_id, kind))
        
        if result.is_duplicate:
            # Already tracked in duplicate_ids, just mark
            pass
    
    return report


def format_report(report: AuditReport, verbose: bool = False) -> str:
    """Format audit report as human-readable text."""
    from .taxonomy import DOMAIN_DISPLAY
    
    lines = []
    
    lines.append("=" * 60)
    lines.append("REGISTRY AUDIT REPORT")
    lines.append("=" * 60)
    lines.append("")
    
    # Overview
    lines.append(f"Total entities:     {report.total_entities}")
    lines.append(f"Auto-migratable:    {report.auto_migratable}")
    lines.append(f"Requires干预:        {report.requires_intervention}")
    lines.append(f"Skipped:            {report.skipped}")
    lines.append("")
    
    # Acceptance readiness
    error_count = len(report.duplicate_ids) + len(report.broken_relations)
    warning_count = (
        len(report.missing_owner) + 
        len(report.missing_status) + 
        len(report.missing_capability)
    )
    
    if report.total_entities > 0:
        readiness = (report.auto_migratable / report.total_entities) * 100
    else:
        readiness = 0
    
    lines.append(f"Acceptance readiness: {readiness:.0f}%")
    lines.append("")
    
    # Schema version distribution
    lines.append("Schema versions:")
    lines.append(f"  v1 (legacy):    {report.entities_v1}")
    lines.append(f"  v2 (current):   {report.entities_v2}")
    lines.append("")
    
    # By domain
    lines.append("By domain:")
    for domain in sorted(report.by_domain.keys()):
        count = report.by_domain[domain]
        display = DOMAIN_DISPLAY.get(domain, domain)
        lines.append(f"  {domain:15} ({display:15}): {count:3}")
    lines.append("")
    
    # By kind
    lines.append("By kind:")
    for kind in sorted(report.by_kind.keys()):
        count = report.by_kind[kind]
        dots = "." * (20 - len(kind))
        lines.append(f"  {kind}{dots} {count:3}")
    lines.append("")
    
    # Errors
    if report.duplicate_ids:
        lines.append("ERRORS:")
        lines.append(f"  Duplicate IDs: {len(report.duplicate_ids)}")
        for dup in report.duplicate_ids[:5]:
            lines.append(f"    - {dup}")
        if len(report.duplicate_ids) > 5:
            lines.append(f"    ... and {len(report.duplicate_ids) - 5} more")
        lines.append("")
    
    if report.broken_relations:
        lines.append(f"  Broken relations: {len(report.broken_relations)}")
        for entity, rel in report.broken_relations[:5]:
            lines.append(f"    - {entity}: {rel}")
        lines.append("")
    
    # Warnings
    if report.missing_owner:
        lines.append(f"Warnings:")
        lines.append(f"  Missing owner: {len(report.missing_owner)}")
        for eid in report.missing_owner[:5]:
            lines.append(f"    - {eid}")
        lines.append("")
    
    if report.missing_status:
        lines.append(f"  Missing status: {len(report.missing_status)}")
        for eid in report.missing_status[:5]:
            lines.append(f"    - {eid}")
        lines.append("")
    
    if report.missing_capability:
        lines.append(f"  Missing capability (agents): {len(report.missing_capability)}")
        for eid in report.missing_capability[:5]:
            lines.append(f"    - {eid}")
        lines.append("")
    
    if report.unknown_kinds:
        lines.append(f"  Unknown kinds: {len(report.unknown_kinds)}")
        for eid, kind in report.unknown_kinds[:5]:
            lines.append(f"    - {eid}: {kind!r}")
        lines.append("")
    
    # Success criteria
    lines.append("-" * 60)
    lines.append("SUCCESS CRITERIA")
    lines.append("-" * 60)
    
    criteria = [
        ("100% schema valid", report.requires_intervention == 0),
        ("0 duplicate IDs", len(report.duplicate_ids) == 0),
        ("0 broken relations", len(report.broken_relations) == 0),
        ("0 unknown kinds", len(report.unknown_kinds) == 0),
    ]
    
    all_passed = True
    for desc, passed in criteria:
        status = "✅" if passed else "❌"
        lines.append(f"  {status} {desc}")
        if not passed:
            all_passed = False
    
    lines.append("")
    if all_passed:
        lines.append("✅ READY FOR MIGRATION")
    else:
        lines.append("❌ NOT READY — fix issues above")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Audit registry without migrating")
    parser.add_argument("--from", dest="source_path", required=True, help="Registry source path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    report = audit_registry(
        source_path=args.source_path,
        verbose=args.verbose,
    )
    
    print(format_report(report, verbose=args.verbose))