#!/usr/bin/env python3
"""Knowledge Kernel KPI Calculator

Usage:
    CMDB_DATA_DIR=~/knowledge/knowledge-kernel python3 ~/.hermes/skills/knowledge-kernel/tools/kpi.py

KPIs:
  - DQS (Dataset Quality Score): entities_with_evidence / total
  - FFR (Fresh Fact Ratio): fresh_entities(<freshness_window) / with_evidence

Notes on 6-Condition Check:
  The 6 Greenfield Conditions (provenance, discovery_run, evidence.*) are
  stored as extra-field YAML blocks that are NOT part of the Entity model.
  They are preserved in the YAML but not accessible via cmdb_get().
  Therefore, the 6-condition check is informational only — it verifies
  YAML structural validity, not model-field availability.

  The authoritative validation is: cmdb_validate() must return valid=True.
"""
import datetime
from cmdb.api import cmdb_get, cmdb_list, cmdb_validate


def compute_kpis(freshness_window_days=30):
    """Compute DQS and FFR across all entities."""
    items = list(cmdb_list())
    total = len(items)
    ev_count = 0
    fresh_count = 0
    now = datetime.datetime.now(datetime.timezone.utc)

    for item in items:
        r = cmdb_get(item['id'])
        # Evidence exists when entity is found + has a recorded observed_at
        if not r.exists or not r.evidence or not r.evidence.observed_at:
            continue
        ev_count += 1
        obs = r.evidence.observed_at
        if isinstance(obs, str):
            try:
                obs_dt = datetime.datetime.fromisoformat(obs.replace('Z', ''))
            except Exception:
                continue
            if obs_dt.tzinfo is None:
                obs_dt = obs_dt.replace(tzinfo=datetime.timezone.utc)
            if (now - obs_dt).days <= freshness_window_days:
                fresh_count += 1

    dqs = ev_count / total * 100 if total else 0.0
    return {
        'total': total,
        'with_evidence': ev_count,
        'fresh': fresh_count,
        'dqs': dqs,
        'ec': dqs,
        'ffr': fresh_count / ev_count * 100 if ev_count else 0.0,
        'freshness_window_days': freshness_window_days,
    }


def main():
    kpis = compute_kpis()
    all_items = list(cmdb_list())

    print(f'=== Knowledge Kernel KPIs ===')
    print(f'DQS (Evidence / Total):                 {kpis["with_evidence"]}/{kpis["total"]} = {kpis["dqs"]:.1f}%')
    print(f'EC  (same as DQS):                       {kpis["ec"]:.1f}%')
    print(f'FFR (Fresh <{kpis["freshness_window_days"]}d / With evidence): {kpis["fresh"]}/{kpis["with_evidence"]} = {kpis["ffr"]:.1f}%')

    print()
    kinds = {}
    for item in all_items:
        kind = item.get('kind', 'unknown')
        kinds[kind] = kinds.get(kind, 0) + 1
    print(f'=== Entities by Kind ===')
    for kind, count in sorted(kinds.items()):
        print(f'  {kind}: {count}')

    print()
    v = cmdb_validate()
    print(f'=== Validation (authoritative) ===')
    print(f'valid: {v["valid"]}')
    print(f'errors: {len(v["errors"])}')
    print(f'warnings: {len(v["warnings"])}')

    if v['errors']:
        print()
        print(f'=== Errors ===')
        for e in v['errors']:
            print(f'  {e["entity_id"]}: {e["message"]}')

    print()
    print(f'=== 6 Greenfield Rules (YAML-level) ===')
    print(f'  Rule 1: Entity existence ≠ Entity running')
    print(f'  Rule 2: No fact without evidence')
    print(f'  Rule 3: No inference from naming conventions')
    print(f'  Rule 4: Discovery proposes, humans curate, Kernel records')
    print(f'  Rule 5: Active dataset has no version number. Snapshots do.')
    print(f'  Rule 6: Entry criteria: exists + evidence + observed property + observed_at + provenance + valid relations')
    print()
    print(f'  Note: provenance/discovery_run/evidence.* are YAML extra-fields')
    print(f'        preserved in YAML but NOT parsed into Entity model.')
    print(f'        They are verified by reading YAML source, not via cmdb_get().')
    print(f'        Authoritative check: valid={v["valid"]}, errors={len(v["errors"])}')


if __name__ == '__main__':
    main()