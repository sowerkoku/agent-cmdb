#!/usr/bin/env python3
"""
Initialize Agent-CMDB data directory structure.

Creates the required folder structure and empty .gitkeep files
for a fresh Agent-CMDB installation.

Usage:
    python scripts/init_cmdb.py

This is safe to run multiple times — existing files are preserved.
"""

from pathlib import Path

DATA_DIR = Path.home() / "agent-cmdb" / "data"

CATEGORIES = [
    "assets",       # Hardware, servers, devices
    "software",     # Applications, services, runtimes
    "endpoints",    # IPs, networks, ports
    "data",         # Databases, configurations, profiles
    "agents",       # AI agents, profiles
    "automation",   # Cron jobs, CI/CD, scripts
    "procedures",   # Runbooks, playbooks
    "projects",     # Active projects
    "secrets",      # Credentials (should be encrypted)
]

def init_cmdb():
    """Initialize CMDB directory structure"""
    
    print("=" * 70)
    print("INITIALIZING AGENT-CMDB DATA DIRECTORY")
    print("=" * 70)
    print(f"\nTarget: {DATA_DIR}\n")
    
    # Create directories
    for category in CATEGORIES:
        cat_dir = DATA_DIR / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep to track empty directories
        gitkeep = cat_dir / ".gitkeep"
        if not gitkeep.exists():
            with open(gitkeep, 'w') as f:
                f.write(f"# Keep this directory\n# Add {category} entities here\n")
            print(f"  ✓ Created: {category}/")
        else:
            print(f"  ✓ Exists: {category}/")
    
    # Create main README
    readme_path = DATA_DIR / "README.md"
    if not readme_path.exists():
        with open(readme_path, 'w') as f:
            f.write("""# Agent-CMDB Data Directory

This directory contains your infrastructure facts as YAML files.

## Structure

```
data/
├── assets/       # Hardware: servers, devices, routers
├── software/     # Applications, services, databases
├── endpoints/    # Network: IPs, networks, ports
├── data/         # Configurations, profiles, secrets
├── agents/       # AI agents and their profiles
├── automation/   # Cron jobs, CI/CD pipelines
├── procedures/   # Runbooks, operational procedures
├── projects/     # Active projects with dependencies
└── secrets/      # Encrypted credentials
```

## Adding Entities

Create YAML files in the appropriate category folder:

```yaml
schema_version: 1
id: my-server
kind: asset
metadata:
  name: My Server
  description: Physical server in datacenter
  hostname: server-01
  cpu: Intel Xeon
  ram: 32GB
status: operational
relations: []
criticality:
  business: high
  operational: high
  technical: medium
```

## Security

⚠️ **DO NOT commit this directory to version control**

The `data/` directory is excluded from git via `.gitignore`.
Your infrastructure data is sensitive — keep it private.

## Examples

See `../examples/entities/` for example entity formats.
""")
        print(f"  ✓ Created: README.md")
    
    print(f"\n✅ Agent-CMDB data directory initialized")
    print(f"\nNext steps:")
    print(f"  1. Copy example entities from ../examples/entities/")
    print(f"  2. Modify with your actual infrastructure data")
    print(f"  3. Run: python -m cmdb.validator to validate entities")

if __name__ == "__main__":
    init_cmdb()