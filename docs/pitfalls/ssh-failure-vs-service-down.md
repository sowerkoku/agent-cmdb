---
name: pitfalls/ssh-failure-vs-service-down
description: SSH failure does NOT mean the service is down. Test from the correct network context.
applies_to:
  - runtime-discovery
  - ssh
---

# Pitfall 8: SSH failure ≠ service down

## Issue

When SSH fails, do not conclude the service is down. The block may be
network/policy, not a missing service.

## Distinction

```
"Permission denied (publickey,password)" → SSH server IS running, access is blocked
"No route to host"                       → SSH server may or may not be running
"Connection timed out"                   → SSH server may or may not be running
```

## Resolution

Test from the correct network context. If a host rejects SSH but has SSH fully
configured and running, the block is network/policy.

## Action

When SSH fails from one context, try alternate paths or mark the entity as
`unverified` — never mark it as `down` based on SSH failure alone.

See `docs/playbooks/runtime-discovery.md` for verification patterns.
