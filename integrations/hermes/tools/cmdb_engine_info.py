"""
Get Kernel Engine Operational Info

Returns comprehensive metadata about the engine state for debugging and telemetry.

Agent usage:
  Use this to inspect the current state of the Knowledge Kernel:
  - generation: how many times indexes have been rebuilt
  - dataset_hash: content-addressed identifier of the dataset
  - last_reload_at: when indexes were last rebuilt
  - memory_estimate_kb: memory footprint of indexes
  - reload_count: total reloads since process start
  - avg_reload_ms: average reload time
  - indexes: counts of each index type

Returns:
  {
    "entities": 36,
    "generation": 3,
    "dataset_hash": "8f3b9c1d",
    "last_reload_at": "2026-07-11T23:45:00Z",
    "memory_estimate_kb": 1,
    "reload_count": 3,
    "reload_failures": 0,
    "avg_reload_ms": 428.5,
    "indexes": {
      "id": 36,
      "kind": 5,
      "forward_relation": 28,
      "reverse_relation": 28
    }
  }
"""

import os
import sys
from pathlib import Path

# Ensure repo is importable
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

# Set data dir
os.environ.setdefault("CMDB_DATA_DIR", str(Path.home() / "knowledge" / "knowledge-kernel"))

from cmdb.api import cmdb_engine_info


def cmdb_engine_info_wrapper(entities_dir: str = None) -> dict:
    """
    Get Kernel Engine operational metadata.
    
    Use for debugging, telemetry, or verifying engine state.
    
    Args:
        entities_dir: Optional override for dataset path.
        
    Returns:
        dict with engine operational metadata.
    """
    return cmdb_engine_info(entities_dir)


if __name__ == "__main__":
    import json
    result = cmdb_engine_info_wrapper()
    print(json.dumps(result, indent=2))