---
name: pitfalls/default-path-drift
description: All modules must read the data directory from get_config().data_dir. Never hardcode.
applies_to:
  - config
  - paths
---

# Pitfall 6: Default dataset path — config.py is the single source

## Symptom

Tests fail with "No assets in dataset" even though the asset directory has
files.

## Root cause

The default data path must be consistent across all modules. When
`config.py` differs from `api.py`:

- `config.py` may default to `~/.local/share/<x>` (XDG-style, often empty)
- `api.py` hardcodes `<dataset-root>`
- `cmdb_list()` uses `config.py` → empty directory
- `cmdb_engine_info()` may use `api.py` → works

## Rule

All modules must read from `get_config().data_dir`. Never hardcode paths in
`api.py` or elsewhere. `config.py` is the single source of truth.
