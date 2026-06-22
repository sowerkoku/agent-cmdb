# Migration Pre-Check Report — Registry v0 → Schema v1

**Generated:** 2026-06-22  
**Validator Version:** 1.0-draft  
**Schema Target:** v1

---

## Summary

| Metric | Value |
|--------|-------|
| Entities scanned | 72 |
| Validation status | ❌ Invalid (pre-migration) |
| Total errors | 347 |
| Total warnings | 14 |

---

## Errors by Category

| Error type | Count | Notes |
|------------|-------|-------|
| `schema_version` missing | 72 | Todas las entidades |
| `kind` missing | 72 | Todas las entidades |
| `metadata` missing | 72 | Todas las entidades |
| `status` invalid | ~30 | Valores no estándar (`critical`, `ATIVO`, `construction`, etc.) |
| `relations` format invalid | ~99 | Formato legacy (`depends_on`, `runs_on` directo) |

---

## Status Migrations Required

| Current value | Count | Target v1 | Notes |
|---------------|-------|-----------|-------|
| `critical` | ~10 | `operational` + `criticality.business: high` | `critical` no es status válido en v1 |
| `ATIVO` | 6 | `operational` | Portugués → inglés |
| `construction` | 1 | `operational` o `deprecated` | ¿En desarrollo o cancelado? |
| `powered-off` | 2 | `down` | Estado operacional |
| `stopped` | 5 | `down` | Estado operacional |
| `operational` | 25 | `operational` | ✅ Sin cambio |

**Decisión pendiente:** ¿Qué hacer con `construction`?
- Opción A: `status: operational` (asumiendo que está en producción)
- Opción B: `status: deprecated` (si está en desarrollo y será reemplazado)
- Opción C: Crear `status: building` (requiere extender catálogo)

---

## Relations Migrations Required

| Legacy format | Count | Target v1 |
|---------------|-------|-----------|
| `depends_on: [x, y]` | ~50 | `relations: [{type: uses, target: x}, ...]` |
| `runs_on: server` | ~20 | `relations: [{type: runs_on, target: server}]` |
| `reads: db` | ~10 | `relations: [{type: reads, target: db}]` |
| `writes: db` | ~10 | `relations: [{type: writes, target: db}]` |

---

## Kind Inference Rules (propuesta)

Para migrar, necesitaremos inferir `kind` basado en:

| Carpeta actual | Kind v1 | Notas |
|----------------|---------|-------|
| `assets/` | `asset` | Directo |
| `software/` | `software` | Directo |
| `automation/` | `automation` | Directo |
| `data/` | `data` | Directo |
| `endpoints/` | `endpoint` | Directo |
| `agents/` | `software` (tentativo) | Pending: ¿`agent` como kind propio? |
| `projects/` | TBD | ¿`software` o nuevo kind `project`? |
| `procedures/` | TBD | ¿Documentación o entidad operacional? |

---

## sample_errors (first 20)

```json
[
  {"entity_id": "backup-mysql-runbook", "field": "schema_version", "message": "Missing required field 'schema_version'"},
  {"entity_id": "backup-mysql-runbook", "field": "kind", "message": "Missing required field 'kind'"},
  {"entity_id": "backup-mysql-runbook", "field": "metadata", "message": "Missing required field 'metadata'"},
  {"entity_id": "backup-mysql-runbook", "field": "status", "message": "Missing required field 'status'"},
  {"entity_id": "firebird-eleventa", "field": "criticality.business", "message": "Invalid value: 'critical'. Valid: ['high', 'low', 'medium']"},
  ...
]
```

---

## Next Steps

1. [ ] Definir reglas de inferencia de `kind` para carpetas no estándar (`agents/`, `projects/`, `procedures/`)
2. [ ] Decidir tratamiento de `construction`
3. [ ] Implementar `cmdb-migrate --dry-run`
4. [ ] Revisar dry-run con dueño del CMDB
5. [ ] Ejecutar `cmdb-migrate --apply`
6. [ ] Validar: `cmdb_validate()` = 0 errores

---

## Backup Location

```
backup/registry-v0-2026-06-22/
├── entities/           # Copia exacta de /home/carlos/registry/
└── validation-report.json
```