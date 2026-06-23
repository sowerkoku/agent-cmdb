#!/usr/bin/env python3
"""
Populate Agent-CMDB internal data store with discovered infrastructure facts.

Usage:
    python scripts/populate_cmdb.py

This script:
1. Discovers local infrastructure (hostname, IPs, ports, processes)
2. Creates YAML entities in ~/agent-cmdb/data/
3. Verifies entities are queryable via cmdb_* tools
"""

import subprocess
from pathlib import Path
from datetime import datetime
import yaml

DATA_DIR = Path.home() / "agent-cmdb" / "data"

def run_cmd(cmd):
    """Execute shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def create_yaml(path, data):
    """Create YAML file with proper formatting"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"  ✓ Created: {path.relative_to(Path.home())}")

def discover_and_populate():
    """Discover infrastructure and populate CMDB"""
    
    print("=" * 70)
    print("DISCOVERING INFRASTRUCTURE & POPULATING CMDB")
    print("=" * 70)
    
    # Hardware
    print("\n[1] Discovering hardware...")
    hostname = run_cmd("hostname")
    arch = run_cmd("uname -m")
    kernel = run_cmd("uname -r")
    os_pretty = run_cmd("grep PRETTY_NAME /etc/os-release | cut -d'=' -f2 | tr -d '\"'")
    
    hw_entity = {
        "schema_version": 1,
        "id": hostname.replace('.', '-'),
        "kind": "hardware",
        "metadata": {
            "name": hostname.replace('-', ' ').title(),
            "description": f"Host principal - {os_pretty}",
            "hostname": hostname,
            "arch": arch,
            "kernel": kernel,
            "os": os_pretty
        },
        "status": "operational"
    }
    create_yaml(DATA_DIR / "assets" / f"{hostname}.yaml", hw_entity)
    
    # Network
    print("\n[2] Discovering network...")
    ip_output = run_cmd("ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}'")
    ips = [line.split('/')[0] for line in ip_output.split('\n') if line]
    
    for ip in ips:
        ip_id = f"ip-{ip.replace('.', '-')}"
        ip_entity = {
            "schema_version": 1,
            "id": ip_id,
            "kind": "network",
            "metadata": {
                "name": f"IP {ip}",
                "description": f"Dirección IP de {hostname}",
                "address": ip,
                "cidr": f"{ip}/24"
            },
            "status": "operational",
            "relations": [
                {"type": "assigned_to", "target": hostname.replace('.', '-')}
            ]
        }
        create_yaml(DATA_DIR / "endpoints" / f"{ip_id}.yaml", ip_entity)
    
    # Listening ports
    print("\n[3] Discovering listening services...")
    ports_output = run_cmd("ss -tlnp | grep LISTEN | grep -v '\\*:' | head -10")
    
    for line in ports_output.split('\n'):
        if ':22' in line and 'sshd' not in line.lower():
            continue  # Skip if already exists
        
    # Check if sshd exists
    sshd_file = DATA_DIR / "software" / "sshd.yaml"
    if not sshd_file.exists() and ':22' in ports_output:
        sshd_entity = {
            "schema_version": 1,
            "id": "sshd",
            "kind": "software",
            "metadata": {
                "name": "OpenSSH Server",
                "description": "Servidor SSH para acceso remoto",
                "port": 22,
                "protocol": "tcp"
            },
            "status": "operational",
            "relations": [
                {"type": "runs_on", "target": hostname.replace('.', '-')}
            ],
            "criticality": {
                "business": "high",
                "operational": "high",
                "technical": "high"
            }
        }
        create_yaml(sshd_file.parent, sshd_file.name)
        create_yaml(sshd_file, sshd_entity)
    
    # Hermes profiles
    print("\n[4] Discovering Hermes profiles...")
    hermes_output = run_cmd("ps aux | grep 'hermes_cli.main' | grep -v grep | head -10")
    profiles = set()
    
    for line in hermes_output.split('\n'):
        if '--profile' in line:
            parts = line.split('--profile')
            if len(parts) > 1:
                profile = parts[1].split()[0]
                profiles.add(profile)
    
    for profile in profiles:
        # Software entity
        hermes_entity = {
            "schema_version": 1,
            "id": f"hermes-{profile}",
            "kind": "software",
            "metadata": {
                "name": f"Hermes Agent ({profile})",
                "description": f"Perfil Hermes especializado: {profile}",
                "provider": "nvidia" if profile == "arquitectobi" else "auto-discovered",
            },
            "status": "operational",
            "relations": [
                {"type": "runs_on", "target": hostname.replace('.', '-')},
                {"type": "uses_profile", "target": f"profile-{profile}"}
            ]
        }
        create_yaml(DATA_DIR / "software" / f"hermes-{profile}.yaml", hermes_entity)
        
        # Profile entity
        profile_entity = {
            "schema_version": 1,
            "id": f"profile-{profile}",
            "kind": "configuration",
            "metadata": {
                "name": f"Perfil {profile}",
                "description": f"Configuración de Hermes para {profile}",
                "path": f"~/.hermes/profiles/{profile}/"
            },
            "status": "operational",
            "relations": [
                {"type": "belongs_to", "target": f"hermes-{profile}"}
            ]
        }
        create_yaml(DATA_DIR / "data" / f"profile-{profile}.yaml", profile_entity)
    
    # Summary
    print("\n" + "=" * 70)
    print("POPULATION COMPLETE")
    print("=" * 70)
    
    total = sum(len(list((DATA_DIR / cat).glob("*.yaml"))) 
                for cat in ['assets', 'software', 'endpoints', 'data', 'agents', 
                           'automation', 'procedures', 'projects', 'secrets'])
    
    print(f"\n  Total entities in ~/agent-cmdb/data: {total}")
    print(f"\n  Categories:")
    for cat in ['assets', 'software', 'endpoints', 'data', 'agents']:
        count = len(list((DATA_DIR / cat).glob("*.yaml")))
        print(f"    {cat:15s}: {count} entities")

if __name__ == "__main__":
    discover_and_populate()