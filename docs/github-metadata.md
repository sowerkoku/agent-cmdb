# GitHub Repository Metadata

## Description (copy/paste esto en About)

```
A deterministic factual substrate for AI agents.
```

**Why this description:**
- 45 characters — GitHub muestra ~120, deja espacio para contexto
- "Deterministic factual substrate" comunica inmediatamente que no es una CMDB clásica ni una base de datos
- "For AI agents" define la audiencia — no hay ambigüedad
- No menciona CMDB, inventory, monitoring — las cosas que NO es

---

## Topics (agregar estos 14 tags)

```
ai-agents agentic-ai grounding cmdb knowledge-graph dependency-graph agent-memory llm reasoning infrastructure facts hallucination-prevention factual-memory
```

**Por qué estos topics:**
- `ai-agents`, `agentic-ai` — Audiencia principal
- `grounding`, `hallucination-prevention` — Problema que resuelve
- `cmdb` — Implementación técnica (no el producto)
- `knowledge-graph`, `dependency-graph` — Estructura de datos
- `agent-memory`, `factual-memory` — Patrón de uso
- `llm`, `reasoning` — Contexto de uso
- `infrastructure`, `facts` — Dominio

---

## Cómo actualizar (manual)

1. Ir a: https://github.com/sowerkoku/agent-cmdb
2. Click en ⚙️ (gear icon) junto a "About"
3. Pegar descripción
4. Agregar topics (uno por uno o copy/paste)
5. Guardar

---

## Alternativa: Con GitHub CLI

Si tienes `gh` instalado:

```bash
# Descripción
gh repo edit sowerkoku/agent-cmdb --description "A deterministic factual substrate for AI agents."

# Topics
gh repo edit sowerkoku/agent-cmdb --topics "ai-agents,agentic-ai,grounding,cmdb,knowledge-graph,dependency-graph,agent-memory,llm,reasoning,infrastructure,facts,hallucination-prevention,factual-memory"
```

---

## Por qué esto importa

La descripción corta aparece en:
- Búsquedas de GitHub
- Perfil del usuario
- Previews de enlaces
- Herramientas de IA que indexan repositorios

**Descripción vaga:**
> "CMDB for AI agents"

→ La gente piensa en NetBox, ServiceNow, inventario IT tradicional.

**Descripción precisa:**
> "A deterministic factual substrate for AI agents."

→ La gente entiende inmediatamente: no es inventario IT, es una capa factual determinista para agentes.

El 80% del descubrimiento del proyecto depende de estas 7 palabras.