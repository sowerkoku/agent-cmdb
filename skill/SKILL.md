---
name: agent-cmdb
description: Ground AI agent responses in verified infrastructure facts — consult CMDB before asserting, reduce hallucinations, cite sources.
category: agent-tooling
version: 1.0.0
---

# Agent CMDB Skill — Factual Memory Layer

**Purpose:** Provide AI agents with access to verified infrastructure facts to reduce hallucinations and ground responses in reality.

## When to Use

**Always consult CMDB when:**
- User asks about infrastructure (servers, services, databases, endpoints)
- You need to verify existence of an entity before making claims
- You need to check dependencies or impact of a change
- User mentions something that might be infrastructure-related

**Never assume:**
- Entity existence without verification
- Configuration details without checking
- Dependency relationships without evidence
- Status/health without current data

---

## Core Principle: Ground Before Asserting

> **Rule:** If a claim relates to infrastructure, consult CMDB first. If CMDB has no record, state uncertainty explicitly.

### Anti-pattern (hallucination risk)

```
User: "Where does Ollama run?"

Agent: "Ollama runs on server-53."  ❌ (assumed without verification)
```

### Correct pattern (grounded)

```
User: "Where does Ollama run?"

Agent: [consults cmdb_get("ollama")]
"According to CMDB, Ollama runs on server-53." ✅ (cited source)
```

---

## API Reference

### `cmdb_get(entity_id)` → Entity or None

**Use when:** You need full details about a specific entity.

```python
from cmdb import cmdb_get

entity = cmdb_get("ollama")
if entity:
    print(f"Found: {entity['metadata']['name']}")
    print(f"Kind: {entity['kind']}")
    print(f"Status: {entity['status']}")
    print(f"Relations: {entity['relations']}")
else:
    print("Entity not found — do not assume existence")
```

**Response pattern:**
- ✅ Entity found → cite facts with source
- ❌ Entity not found → state uncertainty, ask for clarification

---

### `cmdb_search(query)` → List[Entity]

**Use when:** User mentions something but you're unsure of exact ID.

```python
from cmdb import cmdb_search

results = cmdb_search("telegram")
if results:
    print(f"Found {len(results)} entities:")
    for r in results:
        print(f"  - {r['id']} ({r['kind']}): {r['match_field']}")
else:
    print("No matching entities found — can you clarify?")
```

**Response pattern:**
- 1 result → proceed with confidence
- Multiple results → ask user to disambiguate
- 0 results → state uncertainty, ask for clarification

---

### `cmdb_list(kind=None, status=None)` → List[Entity]

**Use when:** You need to enumerate entities by type or status.

```python
from cmdb import cmdb_list

# List all software
software = cmdb_list(kind="software")

# List everything that's down
down = cmdb_list(status="down")

# List operational assets
assets = cmdb_list(kind="asset", status="operational")
```

---

### `cmdb_validate()` → ValidationResult

**Use when:** Checking CMDB health before making assertions.

```python
from cmdb import cmdb_validate

health = cmdb_validate()
if not health["valid"]:
    print(f"⚠️  CMDB has {len(health['errors'])} errors — facts may be unreliable")
```

**Response pattern:**
- Valid → proceed with confidence
- Invalid → warn user about data quality

---

## Decision Tree

```
User question about infrastructure?
         |
    [YES]├─ Do you know the exact entity ID?
         |         ├─ [YES] → cmdb_get(id)
         |         └─ [NO]  → cmdb_search(query)
         |
         └─ [NO] → Answer from general knowledge
```

---

## Examples

### Example 1: Verify Before Answering

```
User: "Is MySQL running?"

Agent workflow:
1. cmdb_get("mysql")
2. Check entity["status"]
3. Respond with cited fact

Agent: "According to CMDB, MySQL status is 'operational'."
```

### Example 2: Handle Missing Entity

```
User: "What version of Redis is running?"

Agent workflow:
1. cmdb_search("redis")
2. No results found
3. State uncertainty

Agent: "I couldn't find any Redis instance in the CMDB. It's possible:
- Redis is not tracked in CMDB yet
- It's registered under a different name
- Redis is not deployed

Should I search for similar names, or do you have more details?"
```

### Example 3: Impact Analysis (Future)

```
User: "What happens if I restart Ollama?"

Agent workflow:
1. cmdb_get("ollama")
2. Find dependents (entities that use ollama)
3. Report impact

Agent: "According to CMDB, restarting Ollama will affect:
- Hermes agent (uses ollama for inference)
- 3 automation scripts depend on Hermes
- No redundancy registered

Risk level: HIGH — Hermes will be unable to process LLM requests until Ollama restarts."
```

---

## Pitfalls

### ❌ Don't: Assume existence

```python
# BAD
if user_mentions("mysql"):
    assert_exists("mysql")  # Hallucination risk
```

### ✅ Do: Verify first

```python
# GOOD
if user_mentions("mysql"):
    entity = cmdb_get("mysql")
    if entity:
        # Now safe to make claims
        pass
    else:
        # Express uncertainty
        pass
```

---

### ❌ Don't: Invent details

```python
# BAD
if not entity:
    return "MySQL probably runs on server-53"  # Invented fact
```

### ✅ Do: State uncertainty

```python
# GOOD
if not entity:
    return "I couldn't find MySQL in the CMDB. Can you verify the name or check if it's registered?"
```

---

### ❌ Don't: Skip CMDB for "obvious" facts

```python
# BAD
# "Everyone knows Ollama runs on port 11434"
return "Ollama runs on port 11434"
```

### ✅ Do: Always verify

```python
# GOOD
entity = cmdb_get("ollama")
port = find_port_in_entity(entity)  # Even for "known" facts
```

---

## Integration with Hermes

This skill is designed for use by Hermes agents. Example integration:

```yaml
# In Hermes skill config
skills:
  - agent-cmdb

# When user asks about infrastructure:
1. Load agent-cmdb skill
2. Consult cmdb_get() or cmdb_search()
3. Ground response in returned facts
4. Cite CMDB as source
```

---

## Future Enhancements

- [ ] `cmdb_impact(entity_id)` — Analyze blast radius of changes
- [ ] `cmdb_history(entity_id)` — Track state changes over time
- [ ] `cmdb_assert_exists(entity_id)` — Fail fast if entity missing
- [ ] Auto-discovery — Populate CMDB from running systems

---

## References

- [domain-model.md](../docs/domain-model.md) — What is an entity
- [schema-v1.md](../docs/schema-v1.md) — Entity format specification
- [Impact First Principle](../docs/domain-model.md#impact-first) — Why we track facts