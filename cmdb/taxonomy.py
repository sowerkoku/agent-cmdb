"""
Domain-Kind Taxonomy —两层分类法 for Knowledge Kernel.

Domains: high-level grouping (infrastructure, software, knowledge, organization)
Kinds: specific entity type within domain

Design principles:
- domains are mutually exclusive (entity belongs to ONE domain)
- kinds are specific (no overlap between domains)
- Query by domain when you want breadth, by kind when you want precision
"""

# =============================================================================
# Domain definitions
# =============================================================================

DOMAIN_INFRASTRUCTURE = "infrastructure"      # Physical/virtual hosts, networks
DOMAIN_SOFTWARE = "software"                  # Applications, services, automation
DOMAIN_KNOWLEDGE = "knowledge"                # Procedures, policies, decisions, capabilities
DOMAIN_ORGANIZATION = "organization"          # Agents, projects, teams

VALID_DOMAINS = {
    DOMAIN_INFRASTRUCTURE,
    DOMAIN_SOFTWARE,
    DOMAIN_KNOWLEDGE,
    DOMAIN_ORGANIZATION,
}

# =============================================================================
# Kind definitions by domain
# =============================================================================

KINDS_BY_DOMAIN = {
    DOMAIN_INFRASTRUCTURE: [
        "asset",      # Physical servers, VMs, devices
        "endpoint",   # Network endpoints, IPs, ports
        "network",    # Networks, subnets, VLANs
    ],
    DOMAIN_SOFTWARE: [
        "software",   # Applications, services
        "automation", # Scripts, cron jobs, CI/CD
    ],
    DOMAIN_KNOWLEDGE: [
        "procedure",  # How-to, runbooks, operational docs
        "policy",     # Rules, SLAs, governance
        "decision",   # Architectural decisions (with status!)
        "capability", # What a system can do
    ],
    DOMAIN_ORGANIZATION: [
        "agent",      # AI agents, profiles
        "project",    # Active projects
        "team",       # Teams (internal or external)
    ],
}

# Flat list for validation
ALL_KINDS = set()
for kinds in KINDS_BY_DOMAIN.values():
    ALL_KINDS.update(kinds)

# Reverse lookup: kind -> domain
KIND_TO_DOMAIN = {}
for domain, kinds in KINDS_BY_DOMAIN.items():
    for kind in kinds:
        KIND_TO_DOMAIN[kind] = domain


def get_domain_for_kind(kind: str) -> str | None:
    """Return the domain for a given kind, or None if invalid."""
    return KIND_TO_DOMAIN.get(kind)


def get_kinds_for_domain(domain: str) -> list[str]:
    """Return all valid kinds for a domain."""
    return KINDS_BY_DOMAIN.get(domain, [])


def is_valid_kind(kind: str) -> bool:
    """Check if kind is valid in any domain."""
    return kind in ALL_KINDS


def is_valid_domain(domain: str) -> bool:
    """Check if domain is valid."""
    return domain in VALID_DOMAINS


# =============================================================================
# Domain display names (for UI/reporting)
# =============================================================================

DOMAIN_DISPLAY = {
    DOMAIN_INFRASTRUCTURE: "Infraestructura",
    DOMAIN_SOFTWARE: "Software",
    DOMAIN_KNOWLEDGE: "Conocimiento",
    DOMAIN_ORGANIZATION: "Organización",
}

# =============================================================================
# Deprecated kinds from v1 (CMDB era) — map to current domain+kind
# =============================================================================

# Legacy kinds that existed in registry but need mapping
DEPRECATED_KINDS = {
    # data -> software (databases are a type of software)
    "data": "software",
    # hardware -> asset (physical devices)
    "hardware": "asset",
    # configuration profiles -> agent (Hermes profiles)
    "configuration": "agent",
    # team -> organization (external teams)
    "team": "team",
}


def migrate_kind_legacy(kind: str) -> tuple[str, str]:
    """
    Convert legacy kind to (domain, kind) tuple.
    
    For backwards compatibility with old entities.
    """
    # First check if kind is already valid
    if kind in KIND_TO_DOMAIN:
        return KIND_TO_DOMAIN[kind], kind
    
    # Then check deprecated mapping
    if kind in DEPRECATED_KINDS:
        mapped = DEPRECATED_KINDS[kind]
        return KIND_TO_DOMAIN.get(mapped, DOMAIN_SOFTWARE), mapped
    
    # Unknown kinds default to software
    return DOMAIN_SOFTWARE, "software"