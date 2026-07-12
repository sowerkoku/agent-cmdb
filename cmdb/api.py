"""
CMDB Public API — Stable interface for AI agents.

This module exposes the official public API. Everything else in the cmdb package
should be considered internal implementation details, subject to change.

Public API (frozen):
    cmdb_exists()      — Check entity existence before making claims
    cmdb_get()         — Get entity with full evidence
    cmdb_search()      — Search entities by name/description/tags
    cmdb_list()        — List entities by kind/status
    cmdb_validate()    — Validate CMDB health
    cmdb_impact()      — Dependency graph analysis (before modifying anything)
    cmdb_assert()      — Binary validation for decision-making
    cmdb_context()     — Pre-packaged agent context (single call at startup)
    cmdb_engine_info() — Operational metadata (debugging, telemetry)
    cmdb_stats()       — Dataset summary statistics (entity counts, hash)

Operational tools (cmdb_engine_info, cmdb_stats) are for introspection and
debugging — they do not change system behavior, only improve observability.

All functions accept optional `entities_dir` parameter to override the default
location (configured via CMDB_DATA_DIR environment variable).

Telemetry:
    Automatic query logging is enabled by default.
    Set CMDB_TELEMETRY_DISABLED=1 to disable.
"""

import os

from .query import cmdb_exists, cmdb_get, cmdb_search, cmdb_list, cmdb_validate
from .impact import cmdb_impact
from .assertions import cmdb_assert, cmdb_context
from .engine import get_engine


def cmdb_engine_info(entities_dir=None) -> dict:
    """Return operational metadata for debugging and telemetry.
    
    Use this to inspect engine state: generation, dataset_hash, index counts,
    reload statistics, memory footprint.
    
    Args:
        entities_dir: Optional override for dataset path.
        
    Returns:
        dict with: entities, generation, dataset_hash, last_reload_at,
        memory_estimate_kb, reload_count, reload_failures, avg_reload_ms, indexes.
    """
    from pathlib import Path
    if entities_dir is None:
        entities_dir = Path(os.environ.get("CMDB_DATA_DIR", Path.home() / "knowledge" / "knowledge-kernel"))
    else:
        entities_dir = Path(entities_dir)
    
    engine = get_engine(entities_dir)
    return engine.get_engine_info()


def cmdb_stats(entities_dir=None) -> dict:
    """Return dataset summary statistics.
    
    Convenience function for operational queries: entity counts by kind,
    total relations, dataset hash.
    
    Args:
        entities_dir: Optional override for dataset path.
        
    Returns:
        dict with: entities (total), {kind}: count, relations (total), dataset_hash.
    """
    from pathlib import Path
    if entities_dir is None:
        entities_dir = Path(os.environ.get("CMDB_DATA_DIR", Path.home() / "knowledge" / "knowledge-kernel"))
    else:
        entities_dir = Path(entities_dir)
    
    engine = get_engine(entities_dir)
    info = engine.get_engine_info()
    stats = engine.get_stats()
    
    # Build summary
    result = {
        "entities": info["entities"],
        "relations": info["indexes"]["forward_relation"],
        "dataset_hash": info["dataset_hash"],
    }
    # Add counts by kind
    for kind, count in stats.by_kind.items():
        result[kind] = count
    
    return result

# ---- Telemetry wrapper (optional) ----

def _wrap_with_telemetry():
    """Wrap API functions with telemetry logging."""
    if os.environ.get("CMDB_TELEMETRY_DISABLED", "0") == "1":
        return  # Telemetry disabled

    try:
        from pathlib import Path
        import sys
        # Add repo root to path if not already there
        repo_root = Path(__file__).parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        
        from integrations.telemetry.grounding_logger import wrap_cmdb_api
        wrap_cmdb_api()
    except ImportError as e:
        # Telemetry not installed, skip silently
        pass


# Apply wrappers on import
_wrap_with_telemetry()

__all__ = [
    # Query API
    "cmdb_exists",
    "cmdb_get",
    "cmdb_search",
    "cmdb_list",
    "cmdb_validate",
    
    # Impact analysis
    "cmdb_impact",
    
    # Assertions
    "cmdb_assert",
    "cmdb_context",
    
    # Operational introspection (debugging/telemetry)
    "cmdb_engine_info",
    "cmdb_stats",
]