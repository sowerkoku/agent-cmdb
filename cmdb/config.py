"""
CMDB Configuration — Centralized configuration management.

All configuration is read from environment variables with sensible defaults.
This module provides a single source of truth for all CMDB settings.

Environment variables:
    CMDB_DATA_DIR       — Path to entities directory (default: ~/knowledge/knowledge-kernel)
    CMDB_SCHEMA_VERSION — Expected schema version (default: 1)
    CMDB_READ_ONLY      — If "1", disable write operations (default: "0")
    CMDB_CACHE_DIR      — Path to cache directory (default: ~/.cache/agent-cmdb)
    CMDB_LOG_LEVEL      — Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CMDBConfig:
    """Immutable configuration object. All fields are read-only."""
    
    data_dir: Path
    schema_version: int
    read_only: bool
    cache_dir: Path
    log_level: str
    
    @classmethod
    def from_env(cls) -> "CMDBConfig":
        """Build config from environment variables with sensible defaults."""
        # CMDB_DATA_DIR: entities directory
        data_dir = os.environ.get("CMDB_DATA_DIR")
        if data_dir:
            data_dir = Path(data_dir).expanduser()
        else:
            # Default: ~/knowledge/knowledge-kernel (Knowledge Kernel dataset)
            data_dir = Path.home() / "knowledge" / "knowledge-kernel"
        
        # CMDB_SCHEMA_VERSION: expected schema version
        schema_version_str = os.environ.get("CMDB_SCHEMA_VERSION", "1")
        try:
            schema_version = int(schema_version_str)
        except ValueError:
            schema_version = 1
        
        # CMDB_READ_ONLY: disable write operations
        read_only = os.environ.get("CMDB_READ_ONLY", "0") == "1"
        
        # CMDB_CACHE_DIR: cache directory
        cache_dir = os.environ.get("CMDB_CACHE_DIR")
        if cache_dir:
            cache_dir = Path(cache_dir).expanduser()
        else:
            # Default: ~/.cache/agent-cmdb
            cache_dir = Path.home() / ".cache" / "agent-cmdb"
        
        # CMDB_LOG_LEVEL: logging level
        log_level = os.environ.get("CMDB_LOG_LEVEL", "INFO").upper()
        if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            log_level = "INFO"
        
        return cls(
            data_dir=data_dir,
            schema_version=schema_version,
            read_only=read_only,
            cache_dir=cache_dir,
            log_level=log_level,
        )
    
    def ensure_dirs(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Global config instance (lazily initialized)
_config: Optional[CMDBConfig] = None


def get_config() -> CMDBConfig:
    """Get the global config instance, reading from environment once."""
    global _config
    if _config is None:
        _config = CMDBConfig.from_env()
        _config.ensure_dirs()
    return _config


def reset_config() -> None:
    """Reset the global config (useful for testing)."""
    global _config
    _config = None