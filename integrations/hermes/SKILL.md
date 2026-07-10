---
name: knowledge-kernel
description: Knowledge Kernel for AI agents — deterministic grounding layer. Stores verified facts, evidence, relationships, freshness. A shared source of truth that multiple agents can query before reasoning or acting. Owns "Knowledge Kernel" (identity) and "Deterministic Grounding" (capability) as differentiated concepts.
category: infrastructure
version: 1.2.0
author: Carlos Cáceres
license: MIT
tags: [grounding, knowledge-kernel, deterministic-factual-substrate, facts, infrastructure, hallucination-prevention, endpoint-identity]
---

# knowledge-kernel Skill

**A Knowledge Kernel that provides deterministic grounding for AI agents.**

Three layers: `cmdb_get()` describes the entity, `.entity.runs_on` is computed from relations, and `[references/endpoint-identity-vs-observation.md](references/endpoint-identity-vs-observation.md)` is the key mental model: endpoint ID = stable identity, `host`/`port`/`protocol` = observed facts that may change without breaking the link.

**Core positioning:** "LLMs infer; knowledge-kernel provides a shared, evidence-backed source of truth so multiple agents can reason from the same verifiable reality."

## Arquitectura (principio fundamental: código ≠ datos)

```
~/knowledge-kernel/                   ← código (repo git)
~/.local/share/knowledge-kernel/      ← datos por defecto (CMDB_DATA_DIR)
~/knowledge/knowledge-kernel/         ← dataset de producción (RECOMENDADO)
```

**Código y datos VAN EN DIRECTORIOS SEPARADOS.** El skill vive en `~/.hermes/skills/knowledge-kernel/`, el código en `~/knowledge-kernel/` (repo git, `sowerkoku/knowledge-kernel`). El dataset de producción está en `~/knowledge/agent-cmdb/` (NO se muda — los datos tienen vida distinta al branding). Esto permite:
- Actualizar el paquete sin tocar los datos
- Cambiar de rama git sin perder datos
- Backups independientes
- Reutilizar el mismo código con datasets distintos

## API Pública (congelada)

Usar SIEMPRE `from cmdb.api import ...`:

```python
from cmdb.api import (
    cmdb_exists,    # Verificar existencia antes de afirmar
    cmdb_get,       # Entidad completa con evidencia
    cmdb_search,    # Buscar por nombre/descripción/tags
    cmdb_list,      # Listar por kind/status/domain
    cmdb_context,   # Contexto pre-empaquetado para agente
    cmdb_impact,    # Análisis de dependencias (ANTES de modificar)
    cmdb_assert,    # Validación binaria para toma de decisiones
    cmdb_validate,  # Validar salud del CMDB
)
```

**Todo lo demás en el paquete `cmdb` es implementación interna** — puede cambiar sin previo aviso.

## Taxonomía v2 (domain + kind)

El modelo usa **dos niveles**: dominio (alto) + kind (específico).

```python
from cmdb.taxonomy import VALID_DOMAINS, ALL_KINDS, KIND_TO_DOMAIN

# Dominios (4):
# - infrastructure: asset, endpoint, network
# - software: software, automation
# - knowledge: procedure, policy, decision, capability
# - organization: agent, project, team
```

**Criterio de inclusión:** Una entidad pertenece al Kernel si:
1. Es un hecho objetivo
2. Tiene única fuente de verdad
3. Cambia relativamente poco
4. Múltiples agentes la consultan

**NO incluye:** conversaciones, brainstorming, notas temporales, RFC en discusión, documentación extensa, razonamientos (eso va a RAG, Git o memoria de Hermes).

### cmdb_list() con dominio

```python
# Listar toda la infraestructura operacional
infra = cmdb_list(domain="infrastructure", status="operational")

# Listar todos los proyectos
projects = cmdb_list(domain="organization", kind="project")

# Listar todos los procedures
procedures = cmdb_list(kind="procedure")
```

## Modelo de entidades y relaciones

### Jerarquía

```
Asset  (orange-pi-54)
   ▲
   │ runs_on
   │
Software  (ollama)
   │
   │ exposes
   ▼
Endpoint  (ollama-api: 192.168.1.54:11434)
```

Cada nivel tiene responsabilidad clara:

| Entidad | Responsabilidad | Ejemplo |
|---|---|---|
| `asset` | Dónde se ejecuta | `orange-pi-54` |
| `software` | El proceso o servicio | `ollama`, `mysql` |
| `endpoint` | Un punto de acceso observable | `ollama-api`, `portainer-ui` |

### Tipos de relación soportados

| Relación | De | Hacia | ¿Se almacena? |
|---|---|---|---|
| `runs_on` | software | asset | Sí |
| `exposes` | software | endpoint | Sí |
| `exposed_by` | endpoint | software | Sí (dual de `exposes`) |
| `uses` / `calls` | software | software | Sí |
| `reads` / `writes` | software | data | Sí |

**Nota sobre `Endpoint`:** Un endpoint representa una **identidad de comunicación**, no una URL. El ID es estable (`ollama-api`) pero `host`/`port`/`protocol` en metadata son hechos observados que pueden cambiar sin alterar la identidad. Esto permite que un endpoint migre de IP/puerto/protocolo/TLS/balanceador sin cambiar su ID lógico.

### Consultar la jerarquía

```python
# ¿Dónde corre Ollama? → propiedad computada
r = cmdb_get("ollama")
print(r.entity.runs_on)  # → "orange-pi-54"

# ¿Qué endpoints expone Ollama?
impact = cmdb_impact("ollama")
print([d for d in impact['depends_on_me']['direct'] if d.get('kind') == 'endpoint'])
# → [{'id': 'ollama-api', 'kind': 'endpoint', 'relation': 'exposes'}]

# ¿Qué pasa si cierra ollama-api (puerto 11434)?
impact = cmdb_impact("ollama-api")
print(f"SPOF: {impact['risk_indicators']['single_point_of_failure']}")
print(f"Afecta a: {[d['id'] for d in impact['depends_on_me']['direct']]}")
# → SPOF=True, afecta a: ['ollama'] (el software que lo expone)
# → y a su vez: open-webui (que usa ollama)
```

**Nota:** `endpoint` es `kind: endpoint` en la taxonomía. Su `metadata` contiene `host`, `port`, `protocol` — no son atributos del software, son del punto de acceso.

## FGR — How to Measure Kernel Quality

FGR (Fact Grounding Rate) measures how often agents use Kernel facts vs inferring. But it has nuances:

**Old (wrong) formula:** FGR = assertions backed by Kernel / total assertions

**Correct decomposition — three separate metrics:**

| Metric | Measures | Formula |
|---|---|---|
| **Kernel Coverage** | Does the Kernel have data for the question? | Questions where Kernel has data / Total questions |
| **Agent Reasoning Accuracy** | Did the agent reason correctly on the data? | Correct reasonings / Questions with Kernel data |
| **Dataset Quality** | Does the data have the right properties? | Entities with required metadata / Total entities |

**The 12-question test (2026-07-07) revealed:**

```
Kernel Coverage:    11/12  (92%) — 1 gap: metadata.ip
Agent Reasoning:   10/12  (83%) — 2 errors: string-match counting, ID inference
Dataset Quality:   ~90%    — needs: metadata.ip, manufacturer, model on assets
```

**What FGR is NOT:**
- A measure of the Kernel's intelligence
- A percentage of "correct answers"
- The agent's quality score

**What FGR IS:**
- A measure of how often the agent chose the Kernel over inference
- The signal for when to expand the Kernel (low Coverage)
- The signal for when the agent needs better grounding guidance (low Reasoning Accuracy)

### How to Measure FGR in Practice

```python
# After each agent session, track:
assertions = agent.get_assertions()
grounded = [a for a in assertions if a.source == "cmdb_api"]
fgr = len(grounded) / len(assertions) if assertions else 0
```

### Why Dataset Gaps Are Not Kernel Failures

| Gap type | Example | Owner |
|---|---|---|
| Missing `metadata.ip` | No IP on asset entities | Dataset population (Runtime Discovery) |
| Missing `manufacturer` | Can't query "all Orange Pis" by model | Dataset population |
| Missing `kind` taxonomy | Entity has no kind | Governance / dataset design |

The Kernel's schema is correct. The dataset has population gaps. These are closed by Runtime Discovery (SSH → observe → propose → human approval → add to Kernel) — not by redesigning the model.

## Configuración

```bash
# Directorio de datos — PRODUCCIÓN (dataset real en ~/knowledge/agent-cmdb/)
# El branding del repo cambió a knowledge-kernel pero los datos NO se mudan
export CMDB_DATA_DIR=~/knowledge/agent-cmdb

# Instalación del paquete (repo clonado en ~/agent-cmdb/)
~/.hermes/hermes-agent/venv/bin/python3 -m pip install -e ~/agent-cmdb

#验证安装
python3 -c "from cmdb.api import cmdb_get; print('✓')"

# Otros paths de datos (no son producción — para testing o desarrollo)
export CMDB_DATA_DIR=~/knowledge/knowledge-kernel    # alternativa — si se muda algún día
export CMDB_DATA_DIR=~/.local/share/knowledge-kernel # fallback por defecto del paquete
```

## Comportamiento Obligatorio

### Regla 1: Consultar antes de afirmar

```python
# ❌ Incorrecto
print("MySQL corre en server-42")

# ✅ Correcto
result = cmdb_exists("mysql")
if result["exists"]:
    print(f"MySQL existe: {result['kind']} ({result['confidence']})")
else:
    print("MySQL no encontrado en CMDB")
```

`cmdb_exists()` retorna `{exists, entity_id, kind, status, reason, source, confidence}` — el agente decide si la confianza es suficiente.

### Regla 2: Verificar confianza antes de afirmar con certeza

```python
# ❌ Incorrecto (asume confianza sin verificar)
if result["evidence"]["confidence_level"] == "verified":
    ...

# ✅ Correcto (usa el contrato real de la API)
r = cmdb_get("ollama")
level = r.evidence.confidence_level  # ConfidenceLevel enum: HIGH | MEDIUM | LOW | UNKNOWN
basis = r.evidence.confidence_basis  # list[EvidenceBasis]: SCHEMA_VALIDATED, HUMAN_DECLARED, ...
if level.value == "high":
    print(f"Ollama corre en {r.entity.runs_on} (alto)")  # → "orange-pi-54"
else:
    print(f"Confianza insuficiente: {level.value} / base={basis}")
```

### Regla 3: Impacto antes de modificar

```python
impact = cmdb_impact("ollama")
if impact["risk_indicators"]["single_point_of_failure"]:
    print("⚠️ SPOF detectado — requiere mantenimiento")
print(f"Direct dependents: {[d['id'] for d in impact['depends_on_me']['direct']]}")
```

### Sobre `expires_at`

`evidence.expires_at` forma parte del contrato público y **no debe eliminarse**, aunque se compute derivando `observed_at + ttl`. Es una propiedad observable de la Evidence — los agentes ya la consultan. Sustituirla por fórmula obligaría a cambiar todas las integraciones.

## How to Answer Questions Using the Kernel

The Kernel rarely answers a question directly. Most questions require reasoning after getting facts. Three patterns:

### Pattern 1: Fact-Backed Answer (direct)

The Kernel has the complete fact. The agent reports it.

```
Question: ¿Dónde corre MySQL?
Answer:   cmdb_get("mysql") → runs_on = "orange-pi-54"
Agent:    "MySQL corre en orange-pi-54 (HIGH confidence, schema_validated)"
```

### Pattern 2: Grounded Answer (Kernel + tool execution)

The Kernel provides the endpoint/facts. The agent uses them to observe something external.

```
Question: ¿Qué tablas tiene DB_CIC?
Kernel:   mysql-db-cic exists, runs_on=orange-pi-54, endpoint=mysql-cic
          → Agent has credentials and host
Tool:     SELECT table_name FROM information_schema.tables WHERE table_schema='DB_CIC'
Agent:    "DB_CIC tiene las siguientes tablas: fact_ventas_v3, fact_reposicion..."
```

The Kernel does NOT contain table schemas. But it contains the endpoint, credentials, and location — enough to drive the query. **"Outside the Kernel's domain" does not mean "cannot answer." It means "use the Kernel's facts to observe."**

### Pattern 3: Composite Answer (multiple queries)

```
Question: ¿Qué pasa si cierro el puerto 11434?
Kernel:   cmdb_impact("ollama-api") → SPOF=True, affects: open-webui
Agent:    "Cerrar 11434 afecta a ollama-api (su único endpoint de LL inference)."
          "open-webui pierde su backend de LLM. No hay fallback configurado."
```

### Decision Tree: How to Approach Any Question

```
Question arrives
    │
    ├─ Can the Kernel answer this directly?
    │   ├─ Yes (cmdb_get / cmdb_list / cmdb_search):
    │   │   → Use Kernel. Report fact with confidence level.
    │   │
    │   └─ No (requires external observation):
    │       ├─ Does the Kernel provide the path to observe? (endpoint, credentials, host)
    │       │   ├─ Yes: Grounded answer — use Kernel facts → execute tool → report
    │       │   └─ No: "I don't have enough facts in the Kernel to answer this."
    │       │
    │       └─ Is the missing fact within the Kernel's domain?
    │           ├─ Yes (asset, software, endpoint, relationship): → the dataset has a gap
    │           └─ No (table schemas, logs, runtime metrics): → correctly outside the Kernel
```

### Critical: What "Outside the Kernel's Domain" Really Means

**Does NOT mean:** "I cannot answer."
**Does mean:** "The answer requires external observation, and I need to use the Kernel's facts to drive it."

| Question type | Kernel's role | Example |
|---|---|---|
| Where does X run? | Complete answer | `cmdb_get → runs_on` |
| How many assets? | Complete answer | `cmdb_list(kind=asset)` |
| What tables in DB_CIC? | Partial: provides endpoint + credentials | Agent executes SQL |
| Is X stale? | Complete answer | `cmdb_get → evidence.is_fresh()` |
| What logs on .54? | Provides hostname | Agent SSH + journalctl |
| What broke after restart? | Provides software list | Agent SSH + health checks |

### How to Avoid the Three Common Mistakes

**Mistake 1: Counting entities by string-matching the ID**
```
❌ "How many servers?" → count entities with "server" in id
✅ "How many servers?" → cmdb_list(kind="asset") → count all
```
The ID format is arbitrary. The `kind` and `domain` taxonomies are the stable categories.

**Mistake 2: Inferring facts from the ID**
```
❌ "server-192-168-1-52" → infer IP = 192.168.1.52
✅ cmdb_get("server-192-168-1-52") → metadata.ip
```
The ID encodes no facts. Metadata holds observed properties. If `metadata.ip` is missing, the dataset has a gap — not a reason to infer.

**Mistake 3: Stopping at "the Kernel doesn't have this"**
```
❌ "Table schemas are not in the Kernel" → "I cannot answer"
✅ "The Kernel has the DB endpoint" → use it to query information_schema
```
The Kernel is a grounding layer, not a complete encyclopedia. Its job is to provide enough facts to enable observation.

## Contrato de API (estable)

Funciones públicas en `cmdb.api`:

| Función | Retorna |
|---|---|
| `cmdb_exists(id)` | `dict` con `{exists, entity_id, kind, status, reason, source, confidence}` |
| `cmdb_get(id)` | objeto con `.exists`, `.entity`, `.evidence` | Ver tabla detallada abajo |

### Objeto `cmdb_get()` — estructura completa

Retorna un objeto `CMDBResult` con tres miembros:

#### `.entity` — hechos puros (qué existe)

| Miembro | Tipo | Descripción |
|---|---|---|
| `.id` | `str` | Identificador único |
| `.kind` | `str` | Tipo: asset, software, automation, data, endpoint, procedure, ... |
| `.status` | `str \| None` | operational, degraded, down, deprecated |
| `.metadata` | `dict` | name, description, version, etc. (no incluye `runs_on`) |
| `.relations` | `list` | relaciones declaradas en YAML: `[{type, target}, ...]` |
| `.runs_on` | `Property[str\|None]` | **Propiedad computada.** Busca la primera relación `type: runs_on` y retorna su `target`. Si no existe, retorna `None`. Filosofía: misma que `freshness` — calculada en acceso, no almacenada. |

**Acceso correcto:**
```python
r = cmdb_get("ollama")
if r.entity.runs_on:
    print(f"Ollama corre en {r.entity.runs_on}")  # → "orange-pi-54"
```

`cmdb_impact()["i_depend_on"]["direct"]` sigue disponible para quien necesite el grafo completo de dependencias inversas.

#### `.evidence` — por qué confiamos (inmutable, separado del hecho)

| Miembro | Tipo | Observaciones |
|---|---|---|
| `.confidence_level` | `Property[ConfidenceLevel]` | Enum: `HIGH \| MEDIUM \| LOW \| UNKNOWN` |
| `.confidence_basis` | `Property[list[EvidenceBasis]]` | Lista de enums: `SCHEMA_VALIDATED`, `HUMAN_DECLARED`, `RUNTIME_CHECKED`, `INFERRED`, `DISCOVERED` |
| `.observed_at` | `Property[datetime]` | Momento de la observación |
| `.expires_at` | `Property[datetime \| None]` | Caducidad calculada desde TTL; `None` si no hay política |
| `.is_fresh()` | `Method → bool \| None` | Calcula frescura en tiempo de ejecución |
| `.time_to_expiry_seconds()` | `Method → float \| None` | Segundos restantes o `None` |
| `.source_file` | `str` | Ruta del archivo YAML fuente |
| `.validated` | `bool` | Si pasó validación de schema |
| `.entity_hash` | `str` | Hash SHA256[:16] del hecho |
| `.schema_version` | `int` | Versión del schema |

**Ejemplo de acceso correcto:**
```python
r = cmdb_get("ollama")
level = r.evidence.confidence_level        # ConfidenceLevel.HIGH
basis = r.evidence.confidence_basis       # [SCHEMA_VALIDATED, HUMAN_DECLARED]
is_fresh = r.evidence.is_fresh()         # True / False / None (llamar con paréntesis)
ttl = r.evidence.time_to_expiry_seconds()  # 3520.5 | None (llamar con paréntesis)
```
| `cmdb_search(query)` | `list[dict]` items con `{id, kind, domain, metadata, status}` |
| `cmdb_list(...)` | `list[dict]` items con `{id, kind, domain, metadata, status}` |
| `cmdb_validate()` | `dict` con `{valid, errors, warnings, stats}` |
| `cmdb_impact(id)` | `dict` con `{target, exists, depends_on_me, i_depend_on, affected_layers, risk_indicators}` |
| `cmdb_assert(id, kind, status)` | validación binaria para toma de decisiones |
| `cmdb_context(agent_id)` | `dict` con `{identity, known_environment, dependents, warnings, evidence}` |

**Regla para futuros cambios:** Si modificás una firma existente, hacé `cmdb.api.cmap_*` con nuevo nombre de función — no rompas compatibilidad. v1.x es API congelada.

## Separación de Responsabilidades

|| knowledge-kernel provee | Agente (LLM) decide |
|-------------------|---------------------|
| Hechos: "ollama corre en server-53" | Interpretación: "esto es riesgoso" |
| Evidencia: por qué confiar | Recomendaciones |
| Confianza: nivel de calidad | Decisiones |
| Impacto: gráfico de dependencias | Acciones |

## Contrato de Consumo del Knowledge Kernel

### Principio fundamental

> **If a fact exists in the Knowledge Kernel, prefer it over inference.**
> **If a fact is not in the Knowledge Kernel, treat it as unverified.**

The Knowledge Kernel may provide the facts necessary to perform additional observations or tool execution.

### Cuándo consultar el Kernel

Consult the Knowledge Kernel whenever a question involves:
- Infrastructure (assets, servers, network)
- Software locations and versions
- Endpoints (host, port, protocol, credentials)
- Dependencies between components
- Agent identities and their running environments
- Projects, procedures, and policies
- Configuration facts with evidence

### Qué NO hacer

```
✗ Infer facts from entity IDs
     Incorrect:  server-192-168-1-52 → IP = 192.168.1.52
     Correct:   metadata.primary_ip = 192.168.1.52

✗ Infer network addresses from naming conventions
     Incorrect:  "orangepizero3" has IP .53 because the ID ends in 3
     Correct:    metadata.primary_ip = 192.168.1.53

✗ Assume relationships not present in the Kernel
     Incorrect:  "mysql probably runs on the same server as ollama"
     Correct:    cmdb_impact("mysql") → read runs_on from Kernel

✗ Treat missing facts as false
     Incorrect:  "There is no endpoint for DB_CIC"
     Correct:    cmdb_get("mysql-db-cic") → if no endpoint found, say "unverified"
```

### Dos tipos de respuestas

#### Fact-backed answer
```
Question
    ↓
Knowledge Kernel (cmdb_get, cmdb_list, cmdb_search)
    ↓
Answer
```

Example: *"¿Dónde corre Hermes?"*
```python
r = cmdb_get("hermes")
answer = f"Hermes corre en {r.entity.runs_on}"
```

#### Grounded answer
```
Question
    ↓
Knowledge Kernel (cmdb_get, cmdb_list)
    ↓
Need external observation?
    ↓
Yes → Tool execution (SSH, SQL query, HTTP probe)
    ↓
Answer
```

Example: *"¿Qué tablas tiene DB_CIC?"*
```python
# Step 1: Get DB_CIC endpoint from Kernel
r = cmdb_get("mysql-db-cic")
# Step 2: Connect to the endpoint
# Step 3: SELECT table_name FROM information_schema.tables
# Step 4: Return answer
```

The Kernel does not need to know the table names. The Kernel knows **where DB_CIC is** and **how to reach it**. That is still grounding.

### Decision flow

```
User Question
      ↓
Need facts?  ─No→  Reason normally
      │
     Yes
      ↓
Knowledge Kernel (cmdb_*)
      ↓
Enough information to answer?
      │
     Yes → Fact-backed answer
      │
     No → Can additional observation be performed?
              │
             Yes → Execute tools (SSH, SQL, HTTP)
              │         ↓
              │    Answer (grounded)
              │
             No → "I don't have verified information about X"
```

### Anti-patterns

**Wrong:**
```
entity.id = "server-192-168-1-52"
      ↓
infer IP = 192.168.1.52
```
Reason: Inference from naming convention, not observed fact.

**Correct:**
```
entity.metadata.primary_ip = "192.168.1.52"
entity.evidence.observed_at = "2026-07-07T..."
```
Reason: Observed fact with evidence, TTL, and source.

---

## Workflow de Migración (AUDIT ANTES de migrar)

**Regla dorada:** La auditoría es más valiosa que la migración. Nunca migrar sin auditar primero.

```bash
# 1. AUDIT dry-run — análisis sin escribir archivos
~/.hermes/hermes-agent/venv/bin/python3 -m cmdb.audit --from ~/registry

# 2. Validar criterios de éxito:
#    ✅ 100% schema valid
#    ✅ 0 duplicate IDs  
#    ✅ 0 broken relations
#    ✅ 0 unknown kinds
#    ✅ Acceptance readiness >= 95%

# 3. Solo si audit pasa → migrar
cmdb migrate-registry --from ~/registry --to ~/knowledge/knowledge-kernel

# 4. post-migration: acceptance tests en verde
cd ~/knowledge-kernel && ~/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/test_acceptance.py
```

**Criterio de éxito de migración:**
- 100% de entidades con schema válido
- 0 IDs duplicados
- 0 relaciones rotas
- Acceptance Tests en verde
- 0 errores críticos

El audit tool se convierte en regression test: cada vez que evoluciones el schema, ejecutás audit dry-run y sabés inmediatamente si rompés compatibilidad con el conocimiento existente.

## Instalación

```bash
# REQUISITO: Hermes usa Python 3.11, NO instalar en Python del sistema (3.12)
~/.hermes/hermes-agent/venv/bin/python3 -m pip install -e ~/knowledge-kernel

# Verificar
python3 -c "from cmdb.api import cmdb_get; print('✓')"
```

**Pitfall conocido:** Si instalás con `pip install -e` (sin path completo al venv), se instala en Python del sistema (3.12) y no en el venv de Hermes (3.11). Siempre usar el path completo.

## Testing

El proyecto tiene DOS niveles de tests:

### Core Tests (siempre pasan, 14/14)
Verifican que el **sistema funciona**, no que existen datos específicos.
```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel \
  ~/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/test_acceptance.py -v -k "Core"
```
- API: cmdb_exists/get/search/list/validate retornan estructura correcta
- Schema: entidades tienen campos requeridos, sin IDs duplicados
- Relations: cmdb_impact funciona para entidades existentes
- Config: CMDB_DATA_DIR se carga correctamente

### Dataset Tests (CIC-specific)
Verifican que un **dataset concreto** contiene las entidades esperadas.
```bash
CMDB_DATA_DIR=~/knowledge/knowledge-kernel \
  ~/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/test_acceptance.py -v -k "Dataset"
```
Esta separación hace el proyecto reutilizable: otros usuarios con otros datasets tendrían sus propios Dataset tests.

**Regla:** Core Tests deben pasar 100% antes de cualquier release. Dataset Tests son específicos del deployment.

**Documentation structure (3 levels — canonical homes):**

```
README.md
 ├── philosophy.md       ← why it exists, principles, KPIs (FGR/Coverage/Freshness)
 └── architecture.md    ← how the pieces connect (code vs data, lazy integration)

 domain-model.md    ← what entities represent
 schema-v1.md        ← how entities are serialized
 usage-patterns.md   ← how to query it
 governance.md       ← what belongs to the Kernel
 audit-methodology.md ← how to verify quality
 error-log.md        ← how it fails
 github-metadata.md  ← repo metadata (positioning, topics, description)
```

**Canonical homes per concept:**

| Concept | Document |
|---------|----------|
| Six principles + KPIs (FGR/Coverage/Freshness) | `philosophy.md` |
| Pipeline Kernel → Facts → Reasoning | `architecture.md` |
| Asset/Software/Endpoint/Evidence | `domain-model.md` |
| YAML schema + validation rules | `schema-v1.md` |
| Inclusion criteria (Survival Test) | `governance.md` |
| Why Not RAG / Why Not Memory | `philosophy.md` (section 9) |

**Rule: each document answers one dominant question.**

## Posicionamiento (para cuando necesites comunicar el proyecto)

**Frase canonical:** "knowledge-kernel is a Knowledge Kernel that provides deterministic grounding for AI agents."

**Lead paragraph:** "A Knowledge Kernel — a shared source of truth that stores verified facts, evidence, relationships, and freshness so multiple agents can reason consistently from the same verifiable reality."

**GitHub description:** "Deterministic grounding layer and shared source of truth for AI agents. Store verified facts, evidence, relationships and freshness."

**Lo que almacena (4 componentes):**
- `facts` → qué sabemos (entidades verificadas, no inferidas)
- `evidence` → por qué lo creemos (source, confidence, observed_at)
- `relationships` → cómo se conecta (runs_on, exposes, uses...)
- `freshness` → qué tan vigente es (computed, not stored)

**Propietarios de dos conceptos diferenciados:**
- **Knowledge Kernel** → identidad del proyecto (no compite con CMDB)
- **Deterministic Grounding** → capacidad que proporciona (no compite con RAG ni memory)

**Qué NO es (evitar ambigüedad):**
- No es RAG ni vector DB → respuestas exactas, no búsqueda por similitud
- No es Agent Memory → almacena hechos verificados, no conversaciones
- No es CMDB → no es inventario IT para humanos; es capa factual para agentes
- No es monitoring → no tiene métricas en tiempo real

**Why Not RAG / Why Not Memory (argumentos de venta):**
- RAG: similarity search vs deterministic lookup; documents vs facts; probabilistic vs exact
- Memory: experiences vs facts; subjective vs objective; personal vs shared; mutable vs evidence-backed

**Cuando usar:**
✓ Múltiples agentes necesitan los mismos hechos
✓ Los hechos deben estar respaldados por evidencia
✓ La frescura importa (facts cambian, freshness importa)
✓ Retrieval determinístico > búsqueda semántica
✓ Necesitas una shared source of truth

**Keywords para descubrimiento:** ai-agents, grounding, knowledge-kernel, deterministic-ai, shared-source-of-truth, context-engineering, structured-memory, facts, evidence, knowledge-graph