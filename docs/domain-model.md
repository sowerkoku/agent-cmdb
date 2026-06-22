# Domain Model — Agent CMDB

**Version:** draft (pending LOCK v2.0 validation)  
**Status:** Active design document

---

## 1. ¿Qué es una entidad?

> "Una entidad existe si posee identidad propia y genera valor al responder consultas operativas o análisis de impacto."

### Criterios de inclusión

| Criterio | Descripción | Ejemplo ✅ | Ejemplo ❌ |
|----------|-------------|------------|------------|
| **Identidad única** | Tiene `id` estable y consultable | `server-52`, `mysql` | `prompt-20260622` |
| **Consulta operativa** | Responde preguntas de operación en producción | "¿Dónde corre X?", "¿Qué versión tiene?" | README, documentación |
| **Análisis de impacto** | Participa en cadenas de fallo — su estado afecta a otros | "¿Qué se afecta si cae?" | Configuración efímera |

### Principio: Impact First

> **Toda entidad nueva debe justificar qué consulta o análisis de impacto no puede resolverse sin ella.**
>
> Si no mejora consultas ni impacto, es configuración y no entidad.

**Ejemplos de aplicación:**

| Objeto | ¿Entidad? | Justificación |
|--------|-----------|---------------|
| `sync-firebird-mysql` | ✅ Sí | "¿Qué se afecta si el sync falla?" requiere rastrear origen/destino |
| `server-52` | ✅ Sí | "¿Qué software corre aquí?" — impacto de fallo físico |
| `hermes-devon`, `hermes-webon` | ❌ No (por ahora) | ¿Qué consulta requiere distinguirlos individualmente? Si ninguna → metadata de `hermes` |
| `prompt-20260622` | ❌ No | Efímero, sin consulta de impacto operacional |

---

## 2. Tipos de entidad (core)

| Tipo | Descripción | Ejemplos |
|------|-------------|----------|
| `asset` | Hardware físico o virtual (servidores, routers, PCs) | `server-52`, `router-mikrotik`, `pc-cico` |
| `software` | Servicios, daemons, CLIs, librerías ejecutables | `mysql`, `ollama`, `firebird`, `hermes`, `docker` |
| `automation` | Scripts, jobs programados, pipelines, tareas automatizadas | `sync-firebird-mysql`, `backup-nocturno`, `ci-pipeline` |
| `data` | Bases de datos, backups, datasets, repositorios de información | `cic_db`, `firebird_db`, `backup-20260621`, `ml-training-set` |
| `endpoint` | URLs, interfaces HTTP, puntos de acceso a servicios | `api.telegram.org`, `ollama:11434`, `webhook-github` |

### Tipos pendientes de investigación

| Tipo | Estado | Pregunta abierta | Decisión pendiente |
|------|--------|------------------|-------------------|
| `agent` | 🔍 En investigación | ¿Es software con rol especial o categoría fundamental del dominio? | Se decidirá cuando exista una consulta que requiera distinguir `agent` de `software` |

**Regla:** No agregar nuevos tipos hasta que exista un caso de uso operacional justificado (Impact First).

---

## 3. Relaciones tipadas

| Relación | Semántica | Transitiva | Ejemplo |
|----------|-----------|------------|---------|
| `runs_on` | Ubicación física o host donde se ejecuta | ❌ No | `ollama` runs_on `server-53` |
| `uses` | Dependencia funcional — requiere para operar | ✅ Sí | `hermes` uses `ollama` |
| `reads` | Lectura de datos desde una fuente | ✅ Sí | `sync-firebird` reads `firebird_db` |
| `writes` | Escritura de datos hacia un destino | ✅ Sí | `sync-firebird` writes `mysql_cic` |
| `calls` | Invocación HTTP/RPC directa a un endpoint | ❌ No | `automation` calls `telegram_api` |
| `owns` | Propiedad, gestión o responsabilidad operacional | ❌ No | `cico` owns `server-52` |
| `backs_up` | Backup, replicación o copia de seguridad | ❌ No | `backup-nightly` backs_up `firebird_db` |
| `monitors` | Monitoreo, alertas o health checks | ❌ No | `watchdog` monitors `ollama` |

### Reglas de transitividad (propuesta)

| Relación | BFS | Transitivo | Justificación |
|----------|-----|------------|---------------|
| `runs_on` | No | No | La ubicación es 1-hop — no se propaga |
| `uses` | Sí | Sí | Cadena de dependencias funcionales — se propaga el impacto |
| `reads` / `writes` | Sí | Sí | El impacto en datos fluye transitivamente a lo largo del pipeline |
| `calls` | No | No | Endpoint directo — no hay cadena de invocaciones |
| `owns` | No | No | Relación de propiedad — no se transfiere |
| `backs_up` | No | No | Backup es relación directa origen-destino |
| `monitors` | No | No | Monitoreo es observación directa — no se propaga |

**Nota:** Estas reglas se convertirán en **LOCK v2.0** cuando el código y tests las validen formalmente.

---

## 4. Criticidad estructural

```yaml
criticality:
  business: high      # Impacto en operación core del negocio (CIC)
  operational: medium # Impacto en automatización o procesos internos
  technical: low      # Complejidad de recuperación — tiempo/costo técnico
```

### Matriz de clasificación

| business | operational | technical | Clasificación | Acción requerida |
|----------|-------------|-----------|---------------|------------------|
| high | high | any | **CRÍTICO** | Redundancia obligatoria, monitoreo 24/7, runbook documentado |
| high | medium | low | **IMPORTANTE** | Monitoreo activo, backup programado, alertas configuradas |
| low | any | any | **MENOR** | Mantenimiento reactivo, documentación básica |

### Ejemplos de aplicación

| Entidad | business | operational | technical | Clasificación |
|---------|----------|-------------|-----------|---------------|
| `firebird_db` | high | high | medium | **CRÍTICO** — datos core del CIC |
| `sync-firebird-mysql` | high | high | low | **CRÍTICO** — pipeline de sincronización |
| `ollama` | medium | high | low | **IMPORTANTE** — infraestructura de agentes |
| `backup-nocturno` | high | medium | low | **IMPORTANTE** — seguridad de datos |
| `pc-cico` | low | low | high | **MENOR** — workstation individual |

---

## 5. Consultas de impacto (casos de uso)

### Escenario 1: ¿Qué se afecta si cae Ollama?

```python
impact = cmdb_impact("ollama")
# → {
#      software: ["hermes", "devon-proxy"],
#      automation: ["agent-orchestrator"],
#      data: []
#    }
```

### Escenario 2: ¿Dónde corre el software X?

```python
entity = cmdb_get("ollama")
host = [r for r in entity["relations"] if r["type"] == "runs_on"][0]["target"]
# → "server-53"
```

### Escenario 3: ¿Qué lee/escribe el sync?

```python
sync = cmdb_get("sync-firebird-mysql")
reads = [r["target"] for r in sync["relations"] if r["type"] == "reads"]
writes = [r["target"] for r in sync["relations"] if r["type"] == "writes"]
# → reads: ["firebird_db"], writes: ["mysql_cic"]
```

### Escenario 4: ¿Qué es CRÍTICO en server-52?

```python
critical = [
    e for e in cmdb_list()
    if any(r["target"] == "server-52" and r["type"] == "runs_on"
           for r in e.get("relations", []))
    and e.get("criticality", {}).get("business") == "high"
]
# → Lista de entidades críticas corriendo en server-52
```

### Escenario 5: Análisis de fallo en cascada

```python
# Si falla mysql_cic, ¿qué automatizaciones se afectan?
impact = cmdb_impact("mysql_cic")
affected_automation = [
    e["id"] for e in cmdb_list(kind="automation")
    if any(r["target"] == "mysql_cic" and r["type"] in ["reads", "writes"]
           for r in e.get("relations", []))
]
```

---

## 6. Out of scope

**No son entidades CMDB por defecto:**

- prompts
- conversaciones
- mensajes
- logs de ejecución
- commits de Git
- documentos (README, wikis, manuales)
- configuraciones internas de software
- ejecuciones temporales (runs, jobs completados)
- sesiones de usuario
- tokens o credenciales

**Excepción:** Estos objetos **pueden convertirse en entidades** solo si existe un caso de consulta operacional o análisis de impacto justificado (Impact First).

**Ejemplos de excepción válida:**

| Objeto | ¿Cuándo es entidad? | Justificación |
|--------|---------------------|---------------|
| `backup-20260621` | ✅ Sí | "¿Cuál es el último backup válido de firebird_db?" — requiere trazabilidad |
| `ci-run-456` | ❌ No | Efímero, sin consulta de impacto operacional |
| `log-error-20260622` | ❌ No | Los logs son eventos, no entidades consultables |

---

## 7. Anti-patrones

| Anti-patrón | Síntoma | Corrección |
|-------------|---------|------------|
| **Entidad sin consulta** | "¿Para qué sirve esto?" — no hay pregunta operacional que responda | Eliminar o convertir en metadata de otra entidad |
| **Relación genérica** | `depends_on: [...]` sin tipar semántica | Usar `uses`, `reads`, `writes`, `runs_on` según corresponda |
| **Criticidad binaria** | `criticality: high` — sin matices | Desglosar: `business`, `operational`, `technical` |
| **Entidades efímeras** | `prompt-YYYYMMDD`, `run-123`, `session-abc` | Solo si hay consulta de impacto justificada (raro) |
| **Carpetas por tipo hardcoded** | `agents/`, `software/`, etc. como única forma de clasificación | Usar `kind:` en YAML — las carpetas son conveniencia, no schema |
| **Transitividad implícita** | Asumir que todas las relaciones se propagan | Respetar tabla de transitividad — `runs_on` nunca es transitivo |

---

## 8. Referencias

- [`schema-v1.md`](./schema-v1.md) — Especificación técnica del formato YAML (pendiente)
- [`audit-methodology.md`](./audit-methodology.md) — Metodología de auditoría en 9 niveles
- [`governance.md`](../GOVERNANCE.md) — Regla 0, evolución y gobernanza del CMDB

---

## Historial de cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-06-22 | draft | Documento inicial — contrato semántico base |

---

**Próximos pasos:**

1. ✅ `domain-model.md` (este documento)
2. 🔲 `schema-v1.md` — Especificación técnica YAML
3. 🔲 Migración gradual de entidades existentes
4. 🔲 Implementar `cmdb_validate()` con reglas estrictas
5. 🔲 Implementar `cmdb_impact()` — feature estrella