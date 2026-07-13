---
description: SSH patterns and runtime drift detection for kernel maintenance.
audience: maintainers
status: stable
---

# Playbook — Runtime Discovery

**When:** the Kernel may be stale relative to actual infrastructure.
**Goal:** empirical verification before any Kernel mutation.

## Core principle

> The Kernel records declared reality. Runtime discovery is the feedback loop
> that detects drift between declared YAML and observed state.

## Pattern

1. **SSH to host** — `ssh user@<ip>`
2. **List processes** — `ps aux | grep <service>`
3. **List containers** — `docker ps --format` (if Docker host)
4. **List listening ports** — `ss -tlnp`
5. **List systemd services** — `systemctl list-units --type=service --state=running`
6. **List cron jobs** — `crontab -l`
7. **Compare** empirical observations against declared YAMLs

## Common checks

### Is process X running?

```bash
ssh user@host 'ps aux | grep -E "^[^C].*<service>"'
```

### What ports are open?

```bash
ssh user@host 'ss -tlnp'
```

### What containers are up?

```bash
ssh user@host 'docker ps --format "{{.Names}} {{.Image}} {{.Status}}"'
```

### What cron jobs exist?

```bash
ssh user@host 'crontab -l && ls /etc/cron.d/'
```

## Drift detection

For each `asset` in the Kernel:

1. SSH to the asset's declared IP
2. List expected processes (from `hosts/software.yaml` relations)
3. List actual processes
4. Diff

If actual ⊂ declared → YAML may be stale. If declared ⊂ actual → some
deployment happened, not reflected in YAML.

## Resolution rule

> "Eliminate first, create after." — when drift is extensive, delete and
> recreate from observed evidence; do not patch old YAMLs.

## See also

- `docs/pitfalls/registry-drift.md` — symptoms and resolution
- `docs/pitfalls/ssh-failure-vs-service-down.md` — SSH failure ≠ service down
- `docs/playbooks/duplicate-cleanup.md` — once you've found duplicates
