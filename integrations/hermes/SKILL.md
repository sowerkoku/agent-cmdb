---
name: agent-cmdb
description: Ground AI agent responses in verified infrastructure facts — consult CMDB before asserting, reduce hallucinations, cite sources.
category: agent-tooling
version: 1.0.1
author: Carlos Cáceres
license: MIT
tags: [grounding, cmdb, facts, infrastructure, hallucination-prevention]

---

# Agent-CMDB Skill Interface

**Factual memory layer for AI agents** — provides grounding with verified infrastructure facts.

## Purpose

Prevent AI agents from:
- Inventing servers that don't exist
- Forgetting critical dependencies
- Assuming outdated configurations
- Repeating questions across sessions
- Losing knowledge between conversations

## Core Principle

> An agent should not **remember** infrastructure; it should **query** a verifiable representation of reality before reasoning.

## Storage Location

**Default:** `~/agent-cmdb/data/` (internal to the skill, independent of external registries)

```
~/agent-cmdb/data/
├── assets/           # Hardware, servers, devices
├── software/         # Applications, services, runtimes
├── endpoints/        # IPs, networks, ports
├── data/             # Databases, configurations, secrets
├── agents/           # AI agents, profiles
├── automation/       # Cron jobs, CI/CD, scripts
├── procedures/       # Runbooks, playbooks
├── projects/         # Active projects
└── secrets/          # Credentials (encrypted)
```

Configurable via `AGENT_CMDB_DATA_DIR` environment variable.

## Contract: What This Skill Provides

### 1. Factual Grounding (NOT Opinions)

```python
# Returns facts WITH evidence, never bare assertions
{
  "exists": true,
  "entity": {"id": "ollama", "kind": "software", "status": "operational"},
  "evidence": {
    "source_file": "software/ollama.yaml",
    "validated": true,
    "confidence_level": "verified",
    "entity_hash": "sha256:abc123..."
  }
}
```

**NEVER returns:** `{"answer": "Ollama is critical"}` — that's an opinion, not a fact.

### 2. Explicit Uncertainty

Agents know **why** to trust facts:
- `confidence_level`: `verified` | `declared` | `discovered` | `inferred` | `unknown`
- `evidence.source_type`: `declared` (human YAML) vs `discovered` (scanner) vs `inferred` (reasoning)
- `observed_at` / `expires_at`: Freshness with TTL by source type

### 3. Temporal Awareness

```python
if not evidence.is_fresh():
    print(f"⚠️ Fact is {evidence.age_hours()}h old — consider re-verifying")
```

### 4. Change Detection

```python
hash_before = result.evidence.entity_hash
# ... time passes ...
hash_after = new_result.evidence.entity_hash
if hash_before != hash_after:
    print("Entity changed — re-evaluate assumptions")
```

## Available Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cmdb_exists(entity_id)` | Check if entity exists | Before making ANY factual claim |
| `cmdb_get(entity_id)` | Full entity + evidence | When reasoning about specific entity |
| `cmdb_assert(entity_id, kind, status)` | Binary validation | When decision requires specific state |
| `cmdb_search(query)` | Find entities by name/description | When entity ID unknown |
| `cmdb_list(kind, status)` | List entities by filter | Discovery, enumeration |

### Context (Avoid 20 Sequential Queries)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cmdb_context(agent_id)` | Pre-packaged agent context | On agent startup |

### Impact Analysis (Before Actions)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cmdb_impact(entity_id)` | Dependency graph analysis | BEFORE modifying anything |

## Behavioral Rules (MANDATORY)

### Rule 1: Never Invent Infrastructure
```python
# WRONG
print("MySQL runs on server-42")

# CORRECT
result = cmdb_exists("mysql")
if result.exists:
    print(f"MySQL is in CMDB: {result}")
else:
    print("MySQL not found in CMDB — cannot verify this claim")
```

### Rule 2: Always Check Confidence
```python
result = cmdb_get("ollama")
if result.evidence.confidence_level == "verified":
    print("Ollama runs_on server-53 (verified)")
else:
    print(f"Confidence: {result.evidence.confidence_level} — express uncertainty")
```

### Rule 3: Cite Sources
```python
# WRONG
print("The database is MySQL")

# CORRECT
print("According to `data/mysql-db.yaml` (validated), the database is MySQL")
```

### Rule 4: Check Impact Before Modifying
```python
impact = cmdb_impact("ollama")
if impact["risk_indicators"]["single_point_of_failure"]:
    print("⚠️ No redundancy — recommend maintenance window")
```

## Separation of Concerns

| Agent-CMDB (This Skill) | Agent (LLM) |
|------------------------|-------------|
| Facts: "ollama runs_on server-53" | Interpretation: "This is a single point of failure" |
| Evidence: Why we trust it | Weigh risks |
| Confidence: Quality level | Make recommendations |
| Impact: Dependency graph | Decide actions |

**Agent-CMDB NEVER provides:** Recommendations, opinions, decisions.

## Initialization

```bash
cd agent-cmdb
pip install -e .
python scripts/init_cmdb.py  # Creates directory structure
```

## Quick Start

```python
from cmdb import cmdb_exists, cmdb_get, cmdb_impact

# 1. Verify before claiming
if cmdb_exists("ollama").exists:
    # 2. Get full context
    result = cmdb_get("ollama")
    print(f"Ollama: {result.entity.status} (confidence: {result.evidence.confidence_level})")
    
    # 3. Check impact before changes
    impact = cmdb_impact("ollama")
    if impact["risk_indicators"]["single_point_of_failure"]:
        print("⚠️ SPOF detected")
```

## References

- **Full Documentation:** `README.md` — installation, entity formats, relations, confidence levels
- **Entity Examples:** `examples/entities/` — complete working examples
- **CLI Reference:** `scripts/cmdb --help` — `cmdb exists/get/search/impact/list`
- **Hermes Integration:** `integrations/hermes/tools/` — `cmdb_exists`, `cmdb_get`, `cmdb_assert`, `cmdb_impact`, `cmdb_context`, `cmdb_search`

## Testing

```bash
cd integrations/hermes/tests
python -m pytest
```

## Version History

- **v1.0.1** (2026-06-30): Independent storage at `~/agent-cmdb/data/`, configurable via `AGENT_CMDB_DATA_DIR`, `pyproject.toml` for `pip install -e .`, thin SKILL.md (~100 lines)
- **v1.0.0** (2026-06-22): Initial release — grounding tools, evidence, confidence, impact analysis