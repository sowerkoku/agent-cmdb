---
name: pitfalls/yaml-quoting
description: YAML fields containıng (), [], :, # must be quoted — parsers fail silently otherwise.
applies_to:
  - yaml
  - cmdb
---

# Pitfall 1: YAML quoting — parentheses break parsers silently

## Issue

Fields with perens, brackets, colons, or hashes need quoting. Without them, YAML
parsers fail silently — the file looks valid but the field is garbled or the
parser throws on that specific key.

## Pattern

```yaml
# WRONG — unquoted value with parentheses
source: Kernel v1 archive (profile: hermes-arquitectobi)

# CORRECT — quoted value
source: "Kernel v1 archive (profile: hermes-arquitectobi)"
```

## Fix

Any field containing `()`, `[]`, `:`, `#` in `source`, `description`, or other
free-text values MUST be quoted.
