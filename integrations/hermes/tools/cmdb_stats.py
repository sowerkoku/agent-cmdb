"""
Get Dataset Summary Statistics

Returns a concise summary of the Knowledge Kernel dataset for operational queries.

Agent usage:
  Use this for quick operational queries:
  - Total entity count
  - Entity counts by kind (asset, software, endpoint, etc.)
  - Total relation count
  - Dataset hash (for correlation with telemetry)

Returns:
  {
    "entities": 36,
    "relations": 28,
    "dataset_hash": "8f3b9c1d",
    "agent": 5,
    "asset": 3,
    "automation": 1,
    "endpoint": 9,
    "network": 1,
    "software": 16,
    "capability": 1
  }

This is lighter than cmdb_engine_info() — it omits index-level details and
reload statistics, focusing on dataset composition.
"""

import os
import sys
from pathlib import Path

# Ensure repo is importable
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

# Set data dir
os.environ.setdefault("CMDB_DATA_DIR", str(Path.home() / "knowledge" / "knowledge-kernel"))

from cmdb.api import cmdb_stats


def cmdb_stats_wrapper() -> dict:
    """
    Get dataset summary statistics.
    
    Use for quick operational queries about dataset composition.
    
    Returns:
        dict with entity counts by kind, total relations, and dataset_hash.
    """
    return cmdb_stats()


if __name__ == "__main__":
    import json
    result = cmdb_stats_wrapper()
    print(json.dumps(result, indent=2))