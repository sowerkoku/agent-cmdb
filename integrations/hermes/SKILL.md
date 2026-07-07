---
name: agent-cmdb
description: Factual memory layer for AI agents — ground responses in verified infrastructure facts. Substitute for registry skill.
category: infrastructure
version: 1.1.0
author: Carlos Cáceres
license: MIT
tags: [grounding, cmdb, facts, infrastructure, hallucination-prevention]
---

# Agent-CMDB Skill

**Factual memory layer for AI agents.** Consulta CMDB antes de afirmar cualquier cosa sobre infraestructura.

## API Pública (congelada)

Usar siempre `from cmdb.api import ...`:

```python
from cmdb.api import (
    cmdb_exists,   # Verificar existencia antes de afirmar
    cmdb_get,      # Entidad completa con evidencia
    cmdb_search,   # Buscar por nombre/descripción/tags
    cmdb_list,     # Listar por kind/status
    cmdb_context,  # Contexto pre-empaquetado para agente
    cmdb_impact,   # Análisis de dependencias (ANTES de modificar)
    cmdb_assert,   # Validación binaria para toma de decisiones
    cmdb_validate, # Validar salud del CMDB
)
```

**Todo lo demás en el paquete `cmdb` es implementación interna** — puede cambiar sin previo aviso.

## Configuración

Variables de entorno (todas opcionales con valores sensatos):

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CMDB_DATA_DIR` | `~/.local/share/agent-cmdb` | Directorio de entidades |
| `CMDB_SCHEMA_VERSION` | `1` | Versión de schema esperada |
| `CMDB_READ_ONLY` | `0` | Si `"1"`, desactiva escrituras |
| `CMDB_CACHE_DIR` | `~/.cache/agent-cmdb` | Directorio de cache |
| `CMDB_LOG_LEVEL` | `INFO` | DEBUG/INFO/WARNING/ERROR |

## Estructura del Paquete

```
cmdb/
├── api.py              # API pública (SOLO esto es estable)
├── config.py           # Configuración centralizada
├── query.py            # cmdb_exists, cmdb_get, cmdb_search, cmdb_list
├── impact.py           # cmdb_impact
├── assertions.py       # cmdb_assert, cmdb_context
├── validator.py        # cmdb_validate
├── registry_migrator.py # migrate-registry (CLI + API)
└── models/             # Modelos internos (pueden cambiar)
```

## Comportamiento Obligatorio

### Regla 1: Consultar antes de afirmar

```python
# ❌ Incorrecto
print("MySQL corre en server-42")

# ✅ Correcto
result = cmdb_exists("mysql")
if result["exists"]:
    print(f"MySQL existe: {result['kind']}")
else:
    print("MySQL no encontrado en CMDB")
```

### Regla 2: Verificar confianza

```python
result = cmdb_get("ollama")
if result["evidence"]["confidence_level"] == "verified":
    print("Ollama runs_on server-53 (verificado)")
else:
    print(f"Confianza: {result['evidence']['confidence_level']}")
```

### Regla 3: Impacto antes de modificar

```python
impact = cmdb_impact("ollama")
if impact["risk_indicators"]["single_point_of_failure"]:
    print("⚠️ SPOF detectado — requiere mantenimiento")
```

## Separación de Responsabilidades

| Agent-CMDB provee | Agente (LLM) decide |
|-------------------|---------------------|
| Hechos: "ollama corre en server-53" | Interpretación: "esto es riesgoso" |
| Evidencia: por qué confiar | Recomendaciones |
| Confianza: nivel de calidad | Decisiones |
| Impacto: gráfico de dependencias | Acciones |

## Migración desde Registry

```bash
# Dry-run (simular)
cmdb migrate-registry --from ~/registry --to ~/knowledge/agent-cmdb --dry-run

# Aplicar migración
cmdb migrate-registry --from ~/registry --to ~/knowledge/agent-cmdb

# Verificar
cmdb migrate-registry --from ~/registry --to ~/knowledge/agent-cmdb --verify
```

## Referencias

- Paquete cmdb: `~/agent-cmdb/cmdb/`
- Documentación: `~/agent-cmdb/README.md`
- Schema v1: `~/agent-cmdb/examples/entities/`