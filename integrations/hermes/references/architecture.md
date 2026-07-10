# Arquitectura agent-cmdb

## Principios Fundamentales

1. **Código ≠ Datos** — separación absoluta
2. **API pública congelada** — `cmdb.api` es lo único estable
3. **Evidencia sobre memoria** — consultar antes de afirmar
4. **Facts ≠ Evidence ≠ Reasoning** — tres capas distintas, nunca mezcladas
   - **Facts**: `Entity(id, kind, status, metadata)` — *qué existe*. No source, no trust.
   - **Evidence**: `source, validation, hash, confidence.{level,basis}, observed_at, expires_at` — *por qué lo creemos*.
   - **Reasoning**: interpretación del LLM — vive en el agente, nunca en el CMDB.
   - Invariante: dos agentes con el mismo estado del Kernel producen exactamente la misma respuesta factual. Si difieren, la diferencia está en reasoning/policy, nunca en facts.

## Estructura de archivos

```
~/agent-cmdb/                   ← repos git (CÓDIGO)
├── cmdb/                       ← paquete Python
│   ├── api.py                 ← API PÚBLICA (congelada)
│   ├── config.py              ← configuración centralizada
│   ├── query.py               ← implementación interna
│   ├── impact.py              ← implementación interna
│   ├── assertions.py          ← implementación interna
│   ├── validator.py           ← implementación interna
│   └── registry_migrator.py   ← tool de migración
├── integrations/hermes/        ← archivos para skill Hermes
└── data/                      ← DATOS DE DESARROLLO (no usar en prod)

~/.local/share/agent-cmdb/      ← datos por defecto
~/knowledge/agent-cmdb/         ← dataset de producción (RECOMENDADO)

~/.hermes/skills/agent-cmdb/    ← skill copiada aquí
```

## Por qué separar código y datos

```
                  git checkout
                  ────────────
                  Código      Datos
                  ──────      ────
Actualización:    Sí          No
Cambio de rama:   Sí          No
Backup:           Separado    Separado
Reinstalar:       pip install Reposicionar CMDB_DATA_DIR
```

## Configuración por entorno

```bash
# Desarrollo
export CMDB_DATA_DIR=~/agent-cmdb/data

# Producción
export CMDB_DATA_DIR=~/knowledge/agent-cmdb
```

## Kinds válidos (schema v1)

```
asset, software, automation, data, endpoint, agent
```

## Relación con registry

- registry fue el prototipo original
- agent-cmdb es el rediseño con modelo de datos más sólido
- coexisten durante la migración
- registry se retira cuando agent-cmdb tiene paridad funcional

## Validación de paridad

```python
from cmdb.api import cmdb_list, cmdb_get, cmdb_search, cmdb_impact
from registry import registry_list, registry_get, registry_search

# Comparar salida de cada función
reg_list = registry_list()
cmdb_list = cmdb_list()
assert len(reg_list) == len(cmdb_list)  # Paridad de conteo
```