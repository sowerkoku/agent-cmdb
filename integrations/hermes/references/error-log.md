# Error Log: agent-cmdb Acceptance Tests

## 2026-07-06 — Acceptance Test Suite creada

Suite: `tests/test_acceptance.py` (23 tests)

**Estado inicial:** 18 PASSED, 5 FAILED

### Fallos esperados (datos no migrados)

Los tests fallan porque las entidades existen en `~/agent-cmdb/data/` pero NO en `~/knowledge/agent-cmdb/` (dataset limpio con 1 entidad).

```
FAILED test_donde_corre_metabase — Metabase no encontrado
FAILED test_que_depende_de_firebird — firebird-server no existe
FAILED test_que_software_esta_en_device53 — empty depends_on_me
FAILED test_hay_puntos_simples_de_falla — SPOF detection requiere datos
FAILED test_que_proyectos_usan_metabase — proyectos no migrados
```

**Lección**: Los tests de aceptación revelan QUÉ entidades necesitamos migrar, no bugs en el código.

### Patrón de uso

```bash
# Ejecutar tests contra dataset actual
cd ~/agent-cmdb
python3 -m pytest tests/test_acceptance.py -v

# Migrar entidad faltante y re-ejecutar
cmdb migrate-registry --from ~/registry --to ~/knowledge/agent-cmdb --dry-run
```

---

## Acceptance Test Categories

### Infraestructura (4 tests)
- ¿Dónde corre X?
- ¿Qué depende de Y?
- ¿Qué software está en Z?
- ¿Está X operacional?

### Organización (4 tests)
- ¿Qué proyectos existen?
- ¿Qué agentes forman el sistema?
- ¿Quién es el propietario?

### Operación (3 tests)
- Procedimientos de reinicio
- Validación de ETL
- Recuperación de Firebird

### Gobernanza (3 tests)
- Políticas de margen
- Decisiones estratégicas
- SLA por servicio

### Relaciones (4 tests)
- Impact analysis (¿qué se rompe si X falla?)
- SPOF detection
- Dependencias transitivas

### Capabilities (2 tests)
- Servicios por host
- Herramientas por agente

### Integridad (3 tests)
- cmdb_validate()
- IDs únicos
- Estados contradictorios

---

## Cómo agregar nuevo test

```python
class TestMiCategoria:
    """Pertenece: sí — hecho objetivo, única fuente, cambia poco, multi-agente."""
    
    def test_pregunta_especifica(self):
        """Descripción clara de la pregunta que responde."""
        result = cmdb_get("entity-id")
        assert result.exists
        # Validar que la respuesta es consultable sin LLM
```