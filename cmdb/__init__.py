# CMDB — Agent Configuration Management Database
# Factual memory layer for AI agents

# Public API (stable, frozen)
# Use: from cmdb.api import cmdb_get, cmdb_exists, cmdb_impact, etc.
from .api import (
    cmdb_exists,
    cmdb_get,
    cmdb_search,
    cmdb_list,
    cmdb_validate,
    cmdb_impact,
    cmdb_assert,
    cmdb_context,
)

# Configuration
from .config import CMDBConfig, get_config, reset_config

__all__ = [
    # Public API (use these)
    "cmdb_exists",
    "cmdb_get",
    "cmdb_search",
    "cmdb_list",
    "cmdb_validate",
    "cmdb_impact",
    "cmdb_assert",
    "cmdb_context",
    
    # Configuration
    "CMDBConfig",
    "get_config",
    "reset_config",
]