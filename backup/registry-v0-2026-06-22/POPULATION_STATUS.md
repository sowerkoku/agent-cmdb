# Registry v1.0 — Estado de población

## Entidades cargadas: 20

### assets (5)
- orange-pi-54 ✓ (OS: Armbian, hostname: orangepi3b)
- pc-oficina ✓ (OS: Linux)
- servidor-pos ✓ (OS: Windows, IP: 192.168.1.2)
- server-192-168-1-52 ✓ (Orange Pi Zero 3, OS: Armbian 6.12.58)
- server-192-168-1-53 ✓ (Orange Pi Zero 3, OS: Armbian 6.12.58)

### software (8)
- mysql ✓
- firebird ✓ (IP: 192.168.1.2, puerto: 3050)
- ollama ✓
- hermes ✓
- docker ✓
- portainer ✓
- open-webui ✓
- espocrm ✓

### data (3)
- firebird-eleventa ✓
- mysql-db-raw ✓
- mysql-db-cic ✓

### automation (2)
- sync-firebird-mysql ✓
- backup-mysql-job ✓

### projects (1)
- cic ✓

### procedures (1)
- backup-mysql-runbook ✓

---

## Pendientes de población

### Access Points
- [ ] AP #1 — IP desconocida
- [ ] AP #2 — IP desconocida
- [ ] Total: ¿cuántos hay?

### GPU Server
- [ ] 192.168.1.77 — NO RESPONDE al ping
- [ ] ¿GPU modelo? ¿Está en otra IP?

### Servicios Docker
- [ ] Listar contenedores corriendo (`docker ps`)
- [ ] Agregar como software/ o automation/ según corresponda

### Bases de datos MySQL
- [ ] Listar databases reales (`SHOW DATABASES;`)
- [ ] Currently known: mysql-db-raw, mysql-db-cic

---

## Consultas que fallan actualmente

| Pregunta | Razón |
|---|---|
| ¿Cuántos APs tenemos? | No hay assets con `type: access-point` |
| ¿IPs de APs? | Idem |
| ¿GPU en 192.168.1.77? | Asset no existe + IP no responde |
| ¿Servicios Docker corriendo? | Requiere `docker ps` o población manual |
| ¿SO de .52/.53/.54? | ✅ RESUELTO — todos Armbian/Linux |
| ¿IP del POS? | ✅ RESUELTO — 192.168.1.2 |

---

## Notas

- Hostname real de orange-pi-54: `orangepi3b`
- Hostname de .52 y .53: `orangepizero3` (mismo hostname, diferente IP)
- Firebird corre en 192.168.1.2 (Windows)