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
"""

from .query import cmdb_exists, cmdb_get, cmdb_search, cmdb_list, cmdb_validate
from .impact import cmdb_impact
from .assertions import cmdb_assert, cmdb_context

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