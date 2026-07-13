---
description: Detect and remove duplicate entities — software or assets — from the Kernel.
audience: maintainers
status: stable
---

# Playbook — Duplicate Cleanup

**When:** two `cmdb_list()` results describe the same reality.

## Detect duplicates

### Software duplicates

```python
from cmdb.api import cmdb_list
from collections import defaultdict

by_name = defaultdict(list)
for e in cmdb_list():
    name = e['metadata'].get('name', '').lower().strip()
    by_name[name].append(e)

for name, ents in by_name.items():
    if len(ents) > 1:
        print(f"Duplicate: {name}")
        for ent in ents:
            print(f"  - {ent['id']} (kind={ent['kind']}, host={ent['metadata'].get('host', '—')})")
```

### Asset duplicates

Same host, different IDs:

```python
by_ip = defaultdict(list)
for e in cmdb_list(kind='asset'):
    ip = e['metadata'].get('primary_ip')
    if ip:
        by_ip[ip].append(e)

for ip, ents in by_ip.items():
    if len(ents) > 1:
        print(f"Same host {ip}: {[e['id'] for e in ents]}")
```

## Decide which to keep

| Criterion | Prefer |
|-----------|--------|
| `schema_version` | newer (2 > 1) |
| `provenance.discovered_by` | `direct_observation` over `memory` |
| `provenance.discovery_run` | more recent |
| `metadata` richness | more detailed (ports, versions, interfaces) |
| `evidence.confidence_level` | higher |

## Migrate references first

```bash
# Find all references to the legacy ID
grep -r "<legacy-id>" <dataset-root>

# Update them — exactly \btarget: legacy\b or any occurrence
sed -i 's/<legacy-id>/<new-id>/g' <file>.yaml
```

After updates, run `cmdb_validate()` and confirm references resolve.

## Delete legacy

Only after:

1. All references migrated
2. `cmdb_validate()` returns 0 errors related to the deletion
3. The new entity already has the equivalent metadata

Then:

```bash
rm <dataset-root>/sw/<legacy-id>.yaml
```

And re-validate.

## Why this order matters

> Migrate first, delete second. Deleting first breaks relations and creates
> validation errors that hide the real issues.

## See also

- `docs/pitfalls/duplicate-entities.md`
- `docs/pitfalls/asset-duplicates.md`
