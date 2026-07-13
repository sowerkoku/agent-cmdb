# Dataset Gap #001 — Duplicate Asset: servidor-pos vs server-192-168-1-52

**Date discovered:** 2026-07-12
**Discovery context:** OBSERVE MODE — User query "listar los perfiles Hermes en .52"
**Actor:** Hermes (verification request)
**Status:** OPEN — awaiting resolution

---

## Gap Description

Two entities model what appears to be the **same physical hardware** (Windows Server hosting Firebird POS Eleventa + sync-bridge):

### Entity A: `servidor-pos`
- **IP:** `192.168.1.2` ❌ (incorrect, should be `.52`)
- **OS:** Windows Server
- **Description:** "Servidor que aloja Firebird — sistema de ventas Eleventa"
- **Tags:** `pos-infrastructure`, `firebird-host`
- **Provenance:** Memory (Kernel v1 legacy)
- **Relations:** `[]`

### Entity B: `server-192-168-1-52`
- **IP:** `192.168.1.52` ✅
- **OS:** Windows Server
- **Description:** "Servidor Windows — aloja Firebird POS Eleventa y sync-bridge"
- **Tags:** `sync-bridge-host`, `pos-infrastructure`
- **Provenance:** Memory + hermes-session
- **Relations:** `[]`

---

## Impact

1. **Split-brain query results:** Queries for "firebird host" return both entities
2. **Ambiguous impact analysis:** `cmdb_impact("firebird")` points to `servidor-pos`, but the modern addressable identity is `.52`
3. **Wrong IP in old entity:** `servidor-pos` has `192.168.1.2` instead of `.52`
4. **Risk of stale truth:** If a probe targets `.2` (from `servidor-pos`), it could hit a non-existent or unintended host

---

## Possible Resolutions

### Option A — Merge: consolidate into `server-192-168-1-52` (RECOMMENDED)
- Archive `servidor-pos` as deprecated/merged
- Migrate any relations pointing to `servidor-pos` → `server-192-168-1-52`
- Update tags + description to be identical
- **Pros:** Single source of truth, modern naming convention
- **Cons:** Renaming may break external scripts referencing the old ID

### Option B — Fix IP only: update servidor-pos → 192.168.1.52
- Keep both entities as aliases for the same hardware
- Add reverse implication link
- **Pros:** No renames
- **Cons:** Two entities for one physical host, requires alias logic

### Option C — Verify reality first
- Confirm whether .2 is a different IP than .52
- Could be a historic or duplicate IP assignments
- **Pros:** May reveal additional infrastructure
- **Cons:** Delays resolution

---

## Recommended Action (within OBSERVE MODE)

**Step 1:** Confirm `.2` and `.52` are NOT in use simultaneously:
```bash
ping 192.168.1.2     # fails? → Entity A is stale
ping 192.168.1.52    # succeeds? → Entity B is correct
```

**Step 2:** If both fail (or only B responds):
- Choose **Option A** (merge to modern ID)
- Update `firebird.yaml` relation from `runs_on: servidor-pos` → `runs_on: server-192-168-1-52`
- Mark `servidor-pos` as `status: deprecated` + add note

**Step 3:** Re-run coverage pilot to confirm gap resolved

---

## Sub-finding

`server-192-168-1-53` description claims to be "Servidor auxiliar — host Hermes profiles" but:
- This claim comes from a hostname/IP-based naming convention
- **If `.53` doesn't actually exist** (e.g., `.52` was the real host), then Hermes profiles' `runs_on` could also point to wrong infrastructure
- This gap was confirmed by user message: "Existe un error, verificalo tú mismo!"
- Suggests: **Some Hermes profiles may actually run on `.52`, not `.53`**

---

## Root Cause Hypothesis

The `servidor-pos.yaml` entity was created during **Kernel v1** (legacy) with IP `192.168.1.2` — possibly from an early SSH probe that returned the wrong network, or from notes predating the current network schema.

When `server-192-168-1-52` was added later (during L2 recon), the duplicate was NOT detected because **no de-duplication logic existed** in the merge process.

---

## Architectural Implications (DO NOT IMPLEMENT)

This gap **supports** deferred indicator: "Reverse-relation necessity"  
(Multi-traversal queries that hunt for "where does Firebird run?" currently return both entities instead of the single right one.)

However, **implementing reverse-relation indexes is forbidden** in OBSERVE MODE (Rule 1).

The fix is **dataset-level only**: merge and deprecate.

---

## Files

- `~/knowledge/knowledge-kernel/asset/servidor-pos.yaml` — Entity to deprecate or fix
- `~/knowledge/knowledge-kernel/asset/server-192-168-1-52.yaml` — Modern identity
- `~/knowledge/knowledge-kernel/software/firebird.yaml` — Has `runs_on: servidor-pos` (wrong target!)

---

## Resolution (Proposed, NOT YET APPLIED)

```yaml
# In software/firebird.yaml, change:
relations:
  - type: runs_on
    target: server-192-168-1-52    # was: servidor-pos
```

```yaml
# In asset/servidor-pos.yaml, mark deprecated:
status: deprecated
metadata:
  ...
  deprecated_at: 2026-07-12
  deprecated_reason: "Duplicate of server-192-168-1-52. Use that ID instead."
  superseded_by: server-192-168-1-52
```

---

**Filed as:** Dataset Gap #001  
**Type:** Duplicate entity + incorrect IP + wrong runbook target  
**Severity:** HIGH (lead agents to wrong physical host)  
**Resolution:** AWAITING USER CONFIRMATION (would require hostname verification + asset merge)