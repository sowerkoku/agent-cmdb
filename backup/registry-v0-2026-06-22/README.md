# Registry del CIC
# Taxonomy: assets · software · data · automation · projects · procedures · endpoints
# Autor: Hermes Agent
# Mantenedor: Carlos Caceres

## Estructura

```
registry/
├── assets/        # Hardware físico
├── software/      # Programas ejecutables
├── data/          # Persistencia estructurada
├── automation/    # Procesos programados
├── projects/      # Agrupadores lógicos
├── procedures/    # Conocimiento operativo
├── secrets/       # (futuro) Referencias a credenciales
└── endpoints/     # URLs y puertos de servicios (ACTIVADO 2026-06-20)
```

## Reglas

- IDs globalmente únicos
- Un archivo por entidad (`id.yaml`)
- Relations: `runs_on`, `depends_on`, `part_of` — nada más
- TYPE A (queda): existencia, ubicación, relaciones, acceso
- TYPE B (sale): configuración interna — vive en `.env`, `config.yaml`, etc.

## Relaciones transitivas

```
Hermes → depends_on → Ollama
Ollama → runs_on → OrangePi

Si OrangePi cae:
  → Ollama abajo
  → Hermes sin LLM
```

El agente puede inferir esto sin almacenar la relación directamente.