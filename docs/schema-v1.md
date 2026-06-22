# Schema v1 — Agent CMDB Entity Specification

**Status:** Draft (pending implementation)  
**Compatibility:** Backward incompatible with pre-v1 YAML (migration required)  
**Implementation:** `cmdb/validator.py`, `cmdb/indexer.py`

---

## 1. Envelope base obligatorio

Toda entidad DEBE tener esta estructura mínima:

```yaml
schema_version: 1

id: <unique-identifier>
kind: <entity-type>

metadata:
  name: <human-readable-name>
  description: <optional-description>

status: <operational-status>

relations:
  - type: <relation-type>
    target: <target-entity-id>

criticality:
  business: <low|medium|high>
  operational: <low|medium|high>
  technical: <low|medium|high>
```

### Ejemplo completo

```yaml
schema_version: 1

id: mysql
kind: software

metadata:
  name: MySQL
  description: Database engine for CIC operations
  version: "8.0"

status: operational

relations:
  - type: runs_on
    target: server-54
  - type: uses
    target: docker
  - type: reads
    target: cic_db

criticality:
  business: high
  operational: high
  technical: medium

tags:
  - database
  - core-infra
```

---

## 2. Separación: Identidad vs Metadata

### Campos obligatorios (identidad)

| Campo | Tipo | Inmutable | Descripción |
|-------|------|-----------|-------------|
| `schema_version` | `integer` | N/A | Versión del schema — siempre `1` por ahora |
| `id` | `string` | ✅ Sí | Identificador único — nunca cambia durante la vida de la entidad |
| `kind` | `string` | ❌ No | Tipo de entidad — puede cambiar si se reclasifica |

**Regla:** `id` es la clave primaria. No se modifica, no se reusa, no se elimina (se marca `status: deprecated`).

### Campos opcionales (metadata)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `metadata.name` | `string` | Nombre legible para humanos |
| `metadata.description` | `string` | Descripción opcional (máx 200 chars) |
| `metadata.version` | `string` | Versión del software/componente |
| `status` | `enum` | Estado operacional (`operational`, `degraded`, `down`, `deprecated`) |
| `tags` | `list[string]` | Etiquetas para búsqueda/filtrado |
| `criticality` | `object` | Matriz de criticidad (ver sección 5) |
| `relations` | `list[object]` | Relaciones tipadas (ver sección 4) |

---

## 3. `kind` es la verdad semántica

Aunque las entidades estén organizadas físicamente en carpetas:

```
entities/
├── software/
│   └── mysql.yaml
├── assets/
│   └── server-54.yaml
```

**La fuente de verdad es el campo `kind`:**

```yaml
kind: software  # ← Esto define el tipo, no la carpeta
```

### Tipos válidos (catálogo cerrado)

| Kind | Descripción | Ejemplo |
|------|-------------|---------|
| `asset` | Hardware físico o virtual | `server-54`, `router-mikrotik`, `pc-cico` |
| `software` | Servicios, daemons, CLIs | `mysql`, `ollama`, `docker`, `hermes` |
| `automation` | Scripts, jobs, pipelines | `sync-firebird-mysql`, `backup-nightly` |
| `data` | Bases de datos, backups, datasets | `cic_db`, `firebird_db`, `backup-20260621` |
| `endpoint` | URLs, interfaces HTTP | `api.telegram.org`, `ollama:11434` |

**Regla:** Agregar nuevos `kind` requiere justificación por "Impact First" (ver `domain-model.md`).

---

## 4. Relaciones tipadas (schema estricto)

### Formato obligatorio

```yaml
relations:
  - type: <relation-type>
    target: <target-entity-id>
    metadata:          # opcional
      reason: <justificación>
      since: <fecha>
```

### ❌ No aceptar (legacy)

```yaml
# RECHAZADO por validator
depends_on:
  - mysql
  - ollama

runs_on: server-54
```

### ✅ Aceptar (v1)

```yaml
relations:
  - type: uses
    target: mysql
  - type: uses
    target: ollama
  - type: runs_on
    target: server-54
```

**Ventaja:** El formato v1 permite extender con metadata sin cambiar el modelo:

```yaml
relations:
  - type: uses
    target: mysql
    metadata:
      reason: "primary database backend"
      since: "2025-01-15"
```

---

## 5. Catálogo de relaciones (cerrado)

| Relación | Target válido | Descripción | Transitiva |
|----------|---------------|-------------|------------|
| `runs_on` | `asset` | Host donde se ejecuta | ❌ No |
| `uses` | Cualquier kind | Dependencia funcional | ✅ Sí |
| `reads` | `data`, `software` | Lectura de datos | ✅ Sí |
| `writes` | `data`, `software` | Escritura de datos | ✅ Sí |
| `calls` | `endpoint`, `software` | Invocación HTTP/RPC | ❌ No |
| `owns` | Cualquier kind | Propiedad/gestión | ❌ No |
| `backs_up` | `data` | Backup/replicación | ❌ No |
| `monitors` | Cualquier kind | Monitoreo/alertas | ❌ No |

**Regla:** Agregar nuevas relaciones requiere justificación de consulta operacional.

### Restricciones de validez

| Relación | Target debe ser | Validación |
|----------|-----------------|------------|
| `runs_on` | `kind: asset` | `validator` rechaza si target no es asset |
| `reads` / `writes` | `kind: data` o `software` | Solo bases de datos o servicios que exponen datos |
| `calls` | `kind: endpoint` o `software` | Endpoints HTTP o servicios con API |
| `backs_up` | `kind: data` | Solo datasets/backups |

---

## 6. Criticidad estructural

### Schema obligatorio (si se declara)

```yaml
criticality:
  business: <low|medium|high>
  operational: <low|medium|high>
  technical: <low|medium|high>
```

**Regla:** Si se declara `criticality`, los tres campos son obligatorios. No se permite parcialidad.

### Valores válidos

| Nivel | Descripción |
|-------|-------------|
| `low` | Impacto localizado, recuperación rápida (< 1 hr) |
| `medium` | Impacto operacional moderado, recuperación en horas |
| `high` | Impacto core del negocio, requiere redundancia |

### Clasificación automática (derivada)

| business | operational | technical | Clasificación |
|----------|-------------|-----------|---------------|
| high | high | any | **CRÍTICO** |
| high | medium | low | **IMPORTANTE** |
| low | any | any | **MENOR** |

---

## 7. Estado operacional (`status`)

### Valores válidos

| Status | Descripción | Cuándo usar |
|--------|-------------|-------------|
| `operational` | Funcionando normalmente | Estado por defecto |
| `degraded` | Funcionando con limitaciones | Performance reducido, fallback activo |
| `down` | Fuera de servicio | Fallo total, mantenimiento programado |
| `deprecated` | Obsoleto, programado para eliminación | Entidad en retirada, no crear nuevas dependencias |

**Regla:** Entidades con `status: deprecated` no deben tener nuevas relaciones entrantes.

---

## 8. Validaciones del schema v1

### ID

| Regla | Expresión | Ejemplo ✅ | Ejemplo ❌ |
|-------|-----------|------------|------------|
| Único en todo el CMDB | — | `mysql`, `server-54` | `mysql` duplicado |
| lowercase | `^[a-z0-9-]+$` | `server-54`, `firebird-db` | `Server-54`, `FirebirdDB` |
| kebab-case | sin underscores | `backup-nightly` | `backup_nightly` |
| sin espacios | — | `cic-db` | `cic db` |
| máximo 64 chars | `len(id) <= 64` | — | `sync-firebird-mysql-backup-verification-script-...` |

### Relations

| Regla | Validación |
|-------|------------|
| `target` debe existir | El ID referenced debe existir en el CMDB |
| `type` debe pertenecer al catálogo | Solo relaciones de la sección 5 |
| `runs_on` solo apunta a `asset` | Validator rechaza `runs_on: mysql` |
| Sin duplicados | No repetir `type + target` en la misma entidad |

### Kind

| Regla | Validación |
|-------|------------|
| Debe pertenecer al catálogo | Solo `asset`, `software`, `automation`, `data`, `endpoint` |
| No cambiar sin justificación | `kind` puede cambiar, pero requiere commit con justificación |

### Criticality

| Regla | Validación |
|-------|------------|
| Si se declara, debe ser completo | No permitir `criticality: { business: high }` aislado |
| Valores válidos | Solo `low`, `medium`, `high` |

---

## 9. Reglas de migración (v0 → v1)

### Migración de `depends_on`

**Antes (v0):**
```yaml
id: hermes
depends_on:
  - ollama
  - mysql
runs_on: server-53
```

**Después (v1):**
```yaml
schema_version: 1
id: hermes
kind: software

metadata:
  name: Hermes Agent

status: operational

relations:
  - type: uses
    target: ollama
  - type: uses
    target: mysql
  - type: runs_on
    target: server-53
```

### Migración de carpetas

**Antes (v0):**
```
entities/
├── agents/devon.yaml
├── software/ollama.yaml
```

**Después (v1):**
```
entities/
├── devon.yaml          # kind: software (o agent, TBD)
├── ollama.yaml         # kind: software
```

**Opción transitoria:** Mantener carpetas por conveniencia, pero `kind` es la verdad:

```yaml
# entities/software/mysql.yaml
schema_version: 1
id: mysql
kind: software  # ← La carpeta es irreversible, el campo kind es la verdad
```

---

## 10. Ejemplos por tipo

### Asset

```yaml
schema_version: 1
id: server-54
kind: asset

metadata:
  name: Server 54
  description: Proxmox VM for AI services
  specs:
    cpu: 8 vCPU
    ram: 32 GB
    disk: 500 GB SSD

status: operational

criticality:
  business: high
  operational: high
  technical: medium

tags:
  - proxmox
  - ai-infra
```

### Software

```yaml
schema_version: 1
id: ollama
kind: software

metadata:
  name: Ollama
  description: Local LLM inference server
  version: "0.5"

status: operational

relations:
  - type: runs_on
    target: server-54
  - type: uses
    target: docker

criticality:
  business: medium
  operational: high
  technical: low

tags:
  - llm
  - inference
```

### Automation

```yaml
schema_version: 1
id: sync-firebird-mysql
kind: automation

metadata:
  name: Firebird → MySQL Sync
  description: Nightly CDC synchronization pipeline
  schedule: "0 2 * * *"

status: operational

relations:
  - type: reads
    target: firebird_db
  - type: writes
    target: mysql_cic
  - type: runs_on
    target: pc-cico

criticality:
  business: high
  operational: high
  technical: medium

tags:
  - cdc
  - sync
  - nightly
```

### Data

```yaml
schema_version: 1
id: firebird_db
kind: data

metadata:
  name: Firebird CIC Database
  description: Core transactional database
  engine: Firebird 3.0
  size: "2.3 GB"

status: operational

relations:
  - type: runs_on
    target: server-52
  - type: backs_up
    target: backup-firebird-nightly

criticality:
  business: high
  operational: high
  technical: high

tags:
  - transactions
  - core
  - firebird
```

### Endpoint

```yaml
schema_version: 1
id: telegram-api
kind: endpoint

metadata:
  name: Telegram Bot API
  url: https://api.telegram.org
  method: HTTPS

status: operational

relations:
  - type: calls
    target: telegram-api

criticality:
  business: medium
  operational: medium
  technical: low

tags:
  - messaging
  - external
```

---

## 11. Checklist de validación (pre-commit)

Antes de mergear un cambio al CMDB:

- [ ] `schema_version: 1` presente
- [ ] `id` único, lowercase, kebab-case, ≤64 chars
- [ ] `kind` pertenece al catálogo
- [ ] `metadata.name` presente
- [ ] `status` es valor válido
- [ ] `relations[].type` pertenece al catálogo
- [ ] `relations[].target` existe en el CMDB
- [ ] `runs_on` apunta solo a `asset`
- [ ] `criticality` (si se declara) tiene los 3 campos
- [ ] No hay dependencias hacia entidades `deprecated`
- [ ] `cmdb_validate()` pasa sin errores

---

## Historial de cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-06-22 | 1.0-draft | Schema inicial — pendiente implementación en validator |

---

## Referencias

- [`domain-model.md`](./domain-model.md) — Contrato semántico
- [`governance.md`](../GOVERNANCE.md) — Regla 0, gobernanza
- `cmdb/validator.py` — Implementación de validación (pendiente)