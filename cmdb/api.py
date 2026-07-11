"""
CMDB Public API — Stable interface for AI agents.

This module exposes the official public API. Everything else in the cmdb package
should be considered internal implementation details, subject to change.

Public API (frozen):
    cmdb_exists()   — Check entity existence before making claims
    cmdb_get()      — Get entity with full evidence
    cmdb_search()   — Search entities by name/description/tags
    cmdb_list()     — List entities by kind/status
    cmdb_context()  — Pre-packaged agent context (single call at startup)
    cmdb_impact()   — Dependency graph analysis (before modifying anything)
    cmdb_assert()   — Binary validation for decision-making
    cmdb_validate() — Validate CMDB health

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
]