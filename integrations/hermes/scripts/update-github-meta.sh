#!/bin/bash
# Update GitHub repository metadata (description + topics) via gh CLI
# Requires: authenticated gh CLI (gh auth login)
#
# Usage:
#   ./update-github-meta.sh
#
# This script is part of the knowledge-kernel maintenance tooling,
# not the core package. Keep separately from runtime code.

set -e

REPO="sowerkoku/knowledge-kernel"
DESCRIPTION="A governed, deterministic and reproducible factual substrate for AI agents."

TOPICS=(
    "knowledge-kernel"
    "ai-agents"
    "grounding"
    "deterministic-grounding"
    "shared-source-of-truth"
    "knowledge-graph"
    "context-engineering"
    "structured-memory"
    "agentic-ai"
    "ai"
    "agent-memory"
    "llm"
    "reasoning"
    "infrastructure"
    "facts"
)

echo "=== Updating GitHub Repository Metadata ==="
echo "Repository: $REPO"
echo ""

# Update description
echo "Setting description..."
gh repo edit "$REPO" --description "$DESCRIPTION"

# Update topics
echo "Setting topics..."
gh repo edit "$REPO" --topics "${TOPICS[@]}"

echo ""
echo "✅ Repository metadata updated"
echo ""
echo "Current metadata:"
gh repo view "$REPO" --json description,topics --jq '"Description: " + .description + "\n\nTopics: " + (.topics | join(", "))'