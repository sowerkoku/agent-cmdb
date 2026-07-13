# Dataset Gap #002 — Múltiples discrepancias críticas descubiertas por verificación de IP

**Date discovered:** 2026-07-12  
**Discovery context:** User pidió "listar perfiles Hermes en .52" → verificación ARP reveló inconsistencias masivas  
**Actor:** Hermes (verification con ping + ARP + curl)  
**Status:** OPEN — múltiples entidades requieren corrección  

---

## Hallazgos por IP (orden baja a alta)

### IP 192.168.1.1 — ✅ CORRECTO
- **ARP:** `08:33:ed:cd:7e:a0` REACHABLE
- **Modelo:** `router-192-168-1-1`
- **Discrepancia:** Ninguna
- **Acción:** ✅ Validar

---

### IP 192.168.1.2 — ❓ DESCONOCIDO EN MODELO
- **ARP:** `68:1d:ef:28:90:0d` STALE
- **Modelo:** `servidor-pos` tiene `primary_ip: 192.168.1.2` pero dice ser "Windows Server POS"
- **Discrepancia:** 
  - ¿`.2` es realmente el servidor POS, o es otro dispositivo?
  - Si `.52` es realmente el POS (ver abajo), `.2` podría ser un dispositivo no modelado
- **Acción requerida:** Identificar dispositivo en `.2` (ping + SSH + hostname)

---

### IP 192.168.1.4 — ❌ NO MODELADO
- **ARP:** `a4:a4:d3:1a:cc:1f` STALE
- **Modelo:** Ninguna entidad con IP `.4`
- **Discrepancia:** Device físico existe pero no está en el Kernel
- **Acción requerida:** Identificar + crear entidad

---

### IP 192.168.1.52 — 🔴 CRÍTICO: IDENTIDAD INCORRECTA

**Realidad verificada:**
```
IP:       192.168.1.52
Hostname: orangePizero3
OS:       Linux aarch64 (Armbian 6.12.58)
Hardware: Orange Pi Zero 3
Servicio: Hermes profiles (arquitectobi + ingenierosql)
Firebird: NO está corriendo aquí
```

**Modelo actual (`server-192-168-1-52.yaml`):**
```yaml
id: server-192-168-1-52
metadata:
  name: Server (.52)
  description: Servidor Windows
  primary_ip: 192.168.1.52
  os: Windows Server
  model: Unknown
relations: []
```

**Discrepancias:**
1. ❌ El modelo dice "Windows Server" → Realidad: **Linux (Orange Pi)**
2. ❌ El modelo dice "aloja Firebird" → Realidad: **NO tiene Firebird**
3. ❌ No menciona Hermes profiles corriendo aquí → Realidad: **2 profiles activos**
4. ❌ `servidor-pos` también apunta a este hardware (posiblemente)
5. ❌ Relaciones: `[]` → Debería tener `runs_on` desde `hermes-arquitectobi` + `hermes-ingenierosql`

**Impacto:**
- Agente podría intentar SSH Windows en un host Linux
- No podría encontrar Hermes profiles (modelados en `.53`)
- Impact analysis fallaría: preguntar "¿qué corre en .52?" daría respuesta errónea

---

### IP 192.168.1.53 — ❓ PARCIALMENTE MODELADO

**Realidad verificada:**
```
IP:       192.168.1.53
ARP MAC:  02:00:b2:1a:29:96 (STALE)
Ping:     ✅ Responde
SSH:      ❌ No responde / timeout
HTTP:     ❌ No responde
```

**Modelo actual (`server-192-168-1-53.yaml`):**
```yaml
id: server-192-168-1-53
metadata:
  name: Server (.53)
  description: Servidor auxiliar — host Hermes profiles
  primary_ip: 192.168.1.53
  os: Unknown
```

**Discrepancias:**
1. ⚠️ Modelo dice "host Hermes profiles" → Realidad: **Hermes corre en `.52`, NO en `.53`**
2. ❓ ¿Qué corre realmente en `.53`? (no responde SSH ni HTTP)
3. ⚠️ Los agentes `hermes-arquitectobi` e `hermes-ingenierosql` tienen `runs_on → server-192-168-1-53` → **INCORRECTO**

---

### IP 192.168.1.54 — 🔴 CRÍTICO: IDENTIDAD INCORRECTA

**Realidad verificada:**
```
IP:       192.168.1.54
ARP MAC:  b2:34:3a:b5:fc:26 (REACHABLE)
HTTP:     ✅ phpMyAdmin (MySQL UI) en root /
Ping:     ✅ Responde
```

**Modelo actual (`orange-pi-54.yaml`):**
```yaml
id: orange-pi-54
metadata:
  name: Orange Pi 3B (.54)
  description: Servidor principal del CIC
  primary_ip: 192.168.1.54
  os: Armbian 26.2.1 bookworm
  kernel: 6.1.115-vendor-rk35xx
  arch: aarch64
  hostname: orangePi3b
```

**Discrepancias:**
1. ❌ Modelo dice "Orange Pi 3B", "Servidor principal" → Realidad: **¿Es realmente Orange Pi?** (hostname de `.52` es `orangePizero3`, podría haber confusión)
2. ❌ No menciona phpMyAdmin → Realidad: **phpMyAdmin responde en HTTP**
3. ❌ No menciona MySQL corriendo ahí → phpMyAdmin sugiere MySQL
4. ❌ ¿Es `.54` el gateway real o es solo un host más?

**Hipótesis:** El nombre `orange-pi-54` fue asignado porque `.54` ES un Orange Pi, pero `.52` también lo es. Podría haber **DOS Orange Pis** en la red.

---

### IP 192.168.1.128 — ❌ NO MODELADO

- **ARP:** `80:20:fd:45:e0:04` STALE
- **Modelo:** Ninguna entidad
- **Discrepancia:** Device físico sin representación
- **Acción:** Identificar + modelar

---

## Root Causes

1. **Modelo construido por memoria + Kernel v1** → Sin verificación empírica de IPs/hostnames reales
2. **`servidor-pos` vs `server-192-168-1-52`** → Posible duplicación de entidad (uno heredado de v1, otrocreated en L2)
3. **`runs_on` modelado incorrectamente** → Profiles dicen `.53` pero corren en `.52`
4. **Confusión de hostnames** → `.52` hostname real es `orangePizero3`, `.54` podría ser `orangePi3b` (dos Orange Pis distintos)

---

## Acciones Requeridas (orden de prioridad)

### Prioridad 🔴 ALTA (corrección de hechos bloquantes)

1. **Corregir `server-192-168-1-52.yaml`:**
   ```yaml
   os: Armbian (Linux aarch64)
   description: Orange Pi Zero 3 — host Hermes profiles + Orange Pi OS
   hostname: orangePizero3
   ```

2. **Corregir relaciones de perfiles Hermes:**
   ```yaml
   # hermes-arquitectobi.yaml
   relations:
     - type: runs_on
       target: server-192-168-1-52    # era: server-192-168-1-53
   
   # hermes-ingenierosql.yaml
   relations:
     - type: runs_on
       target: server-192-168-1-52    # era: server-192-168-1-53
   ```

3. **Corregir `orange-pi-54.yaml`:**
   - Agregar `metadata.services: ["phpmyadmin", "mysql"]` si confirmado
   - Verificar hostname real (podría ser `orangePi3b` distinto de `orangePizero3`)

---

### Prioridad 🟡 MEDIA (identificar gaps)

4. **Identificar `.2`:**
   - ¿Qué dispositivo es?
   - ¿Es el servidor POS Eleventa (Windows)?
   - Si sí, corregir `servidor-pos.yaml` → IP `.2`, NO `.52`

5. **Identificar `.4` y `.128`:**
   - Ping + SSH + inventario

6. **Identificar `.53`:**
   - ¿Qué OS es?
   - ¿Corre algo ahí realmente?
   - ¿O está apagado/inactivo?

---

### Prioridad 🟢 BAJA (documentar)

7. **Consolidar `servidor-pos` vs `server-192-168-1-52`:**
   - Si `.2` ≠ `.52`, mantener ambas como entidades distintas
   - Si `.2` es error y debería ser `.52`, deprecar `servidor-pos`

---

## Implicaciones Arquitectónicas (OBSERVE MODE — NO IMPLEMENTAR)

Estos gaps **validan** la necesidad de:
- **Discovery automation** — escaneo activo de red (nmap, ARP scan) para descubrir IPs reales
- **Hostname verification** — SSH + `hostname` para validar identificação
- **Service detection** — HTTP probes, port scans para detectar servicios

Pero **implementar esto es arquitectura nueva**, prohibida por OBSERVE RULE 1.

La corrección es **puramente dataset**: actualizar YAMLs con hechos verificados manualmente.

---

## Estado

**Descubierto durante:** L2.1 Observation Window — Day 0  
**Tipo:** Múltiples errores de identificación de hosts + relaciones incorrectas  
**Severidad:** 🔴 ALTA (impide agents de localizar recursos correctamente)  
**Resolution:** PENDIENTE confirmación de usuario + autoridad para corregir dataset

---

## Files Afectados

- `~/knowledge/knowledge-kernel/asset/server-192-168-1-52.yaml` — OS incorrecto, servicios faltantes
- `~/knowledge/knowledge-kernel/asset/orange-pi-54.yaml` — servicios faltantes (phpMyAdmin)
- `~/knowledge/knowledge-kernel/agent/hermes-arquitectobi.yaml` — `runs_on` incorrecto
- `~/knowledge/knowledge-kernel/agent/hermes-ingenierosql.yaml` — `runs_on` incorrecto
- `~/knowledge/knowledge-kernel/asset/servidor-pos.yaml` — IP posiblemente incorrecta

---

**Status:** AWAITING USER VERIFICATION  
**Next:** Determinar si procede la corrección (dentro de OBSERVE MODE, es "dataset correction", permitido)