# Registry v1.0 — Reglas de gobernanza

## Regla 0

> No se modifica la estructura del Registry hasta que una consulta real falle.

---

## Estructura congelada

```
registry/
├── assets/
├── software/
├── data/
├── automation/
├── projects/
├── procedures/
├── secrets/      # futuro, solo si falla una consulta real
└── endpoints/    # ACTIVADO 2026-06-20 (13 endpoints)
```

**No se agrega:**
- Categoría nueva
- Campo nuevo
- Subcarpeta nueva

**Solo se agrega:**
- Entidades reales nuevas

---

## TYPE A vs TYPE B

```
TYPE A (Registry):     Existencia · Ubicación · Relaciones · Acceso
TYPE B (config files):  Configuración interna · Parámetros · Contenido mutable
```

El Registry describe qué existe. No cómo funciona internamente.

---

## Relaciones mínimas

```yaml
relations:
  runs_on:     # infraestructura que aloja
  depends_on:  # requiere para funcionar
  part_of:     # proyecto al que pertenece
```

Las demás relaciones se infieren.

---

## Validación automática

Cada YAML debe pasar:

1. ID globalmente único
2. Campos obligatorios: `id`, `category`, `type`, `name`, `description`
3. Todas las `relations` apuntan a IDs existentes
4. `category` coincide con la carpeta

---

## Criterio de éxito

Cuando Hermes pueda responder sin consultar fuentes externas:

| Pregunta | Requiere |
|---|---|
| ¿Dónde corre X? | `runs_on` |
| ¿De qué depende X? | `depends_on` |
| ¿Qué depende de X? | recursión sobre `depends_on` |
| ¿Qué pertenece al CIC? | `part_of: cic` |
| ¿Cuál es la IP de X? | `network.ip` en assets |
| ¿Qué usa la DB? | `runs_on` de la DB + `depends_on` |

---

## Extensión futura

Solo cuando una consulta real falle, se evalúa:

1. ¿Falta una entidad? → Agregar YAML
2. ¿Falta un campo en el esquema? → Proponer cambio con justificación
3. ¿Falta una categoría? → Evaluar si todas las existentes ya no alcanzan

**Nunca** extender por anticipación.

---

## Historial

- v1.0: Diseño congelado — 17 entidades
- Extensión: Solo mediante consulta real que falle
- v1.1: Campo criticality agregado (business/operational/technical)
- v1.2: Corrección modelo — docker/mysql/firebird no son hosts, son depends_on
- Git inicializado: 2026-06-12
- v1.3: SSH access configurado, GitHub remote activo (sowerkoku/registry-cic)

---

## Control de Cambios

### Regla de hierro

**Todo cambio estructural requiere commit con mensaje.**

```
Cambio estructural = cualquier modificación en:
- relations (runs_on, depends_on, part_of)
- criticality
- status (especialmente → stopped/construction)
-新建 entidad nueva
```

**Mensaje de commit obligatorio:**

```
[entity] Descripción corta del cambio
- Qué cambió
- Por qué cambió
- Issue/ticket si existe
```

### Política de branch

- `main`: único branch, protegido
- Commits directos a main para cambios menores
- Branch separado solo para refactors estructurales que afecten >5 entidades

### Backup

El repo Git en `/home/carlos/registry/` debe tener:
1. ✅ Push a GitHub (github.com/sowerkoku/registry-cic) — CONFIGURADO
2. El repo .git en sí es el control de cambios, no es backup
3. Disaster recovery: cualquier equipo con la key SSH puede clonar desde GitHub

---

## Acceso SSH

### Llave SSH
- Tipo: ed25519
- fingerprint: SHA256:XMDpmRbKWamTijUXFfo4ps8QjdvFoQHAzmJuFgdYix0
- Ubicación: `~/.ssh/id_ed25519` en este equipo (.52)

### Equipos con acceso verificado

| Equipo | IP | Estado |
|---|---|---|
| orange-pi-54 | 192.168.1.54 | ✅ Working |
| server-192-168-1-53 | 192.168.1.53 | ✅ Working |
| servidor-pos | 192.168.1.2 | ❌ Windows, SSH no requerido |

### Equipos Windows (no requieren SSH)
- `.2` — servidor-pos: caja Windows
- `.4` — caja POS cliente: terminal

---

## Clasificación de Entidades por Recuperabilidad

| Tipo | Descripción | Entidades | Acción |
|---|---|---|---|
| **A — Reinstalable** | docker-compose / apt-get en minutos | metabase, portainer, searxng, open-webui, etc. | Ninguna documentación extra |
| **B — Restaurable** | Backup + runbook necesario | mysql, mysql-db-raw, mysql-db-cic, sync-firebird-mysql | Documentar restore procedure |
| **C — Fuente de verdad** | Irremplazable, pérdida = datos perdidos | **firebird-eleventa** | Estrategia de recuperación prioritaria |
| **D — Infraestructura fundacional** | Base sobre la que todo corre | **orange-pi-54**, **servidor-pos** | Disaster recovery plan |

---

## Gap Log (Acumulado)

| ID | Fecha | Pregunta | Tipo | Estado |
|---|---|---|---|---|
| 1 | 2026-06-12 | ¿Qué dashboards quedan obsoletos si sync falla? | Data Flow | **Abierto — requiere data flow graph** |
| 2 | 2026-06-12 | ¿Qué pasa si pierdo servidor-pos? | Business Impact | **Pendiente: RPO/RTO no definidos** |
| 3 | 2026-06-12 | ¿Qué debo respaldar primero? | Priorización | **Prioridad: firebird > mysql** |
| 4 | 2026-06-12 | ¿Cuál es el mayor SPOF? | Risk Assessment | **Pendiente: analizar con criticidad real** |
| 5 | 2026-06-12 | ¿Cómo recupero orange-pi-54? | DR | **Abierto — plan no documentado** |
| 6 | 2026-06-12 | ¿Cómo recupero firebird-eleventa? | CRÍTICO | **CORREGIDO: backup existe en PC(.2) + PC personal** |
| 7 | 2026-06-12 | ¿Quién tiene acceso SSH a servidor-pos? | Access | **Abierto** |
| 8 | 2026-06-12 | ¿Dónde están las credenciales reales? | Access | **Abierto — en vault externo** |
| 9 | 2026-06-12 | ¿Cómo reinicio sync si se detiene? | Operations | **Abierto — no hay runbook** |
| 10 | 2026-06-12 | ¿Cuál es el RTO aceptable? | SLA | **Abierto — sin definir** |

**Resueltos:**
- sync_CICO → Histórico, descartado (sync_bridge es la versión operativa)
- OpenClaw → Exagente, no operativo, descartado
- Hermes profiles → Son perfiles de trabajo, no entidades separadas
- firebird-eleventa backup → Corregido: backup manual existe