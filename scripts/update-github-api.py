#!/usr/bin/env python3
"""
Update GitHub repository description and topics using GitHub API.
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'sowerkoku'
REPO_NAME = 'agent-cmdb'

DESCRIPTION = "A factual grounding layer that helps AI agents query verified reality before reasoning or acting."

TOPICS = [
    "ai-agents",
    "agentic-ai",
    "grounding",
    "cmdb",
    "knowledge-graph",
    "dependency-graph",
    "agent-memory",
    "llm",
    "reasoning",
    "infrastructure",
    "facts",
    "hallucination-prevention",
    "factual-memory",
]

# Headers
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28'
}

def update_description():
    """Update repository description."""
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}'
    data = {'description': DESCRIPTION}
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"✅ Description updated successfully")
        print(f"   {DESCRIPTION}")
        return True
    else:
        print(f"❌ Failed to update description")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return False

def update_topics():
    """Update repository topics."""
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/topics'
    data = {'names': TOPICS}
    
    # GitHub requires this specific accept header for topics
    headers_with_topics = headers.copy()
    headers_with_topics['Accept'] = 'application/vnd.github+json; charset=utf-8'
    
    response = requests.put(url, headers=headers_with_topics, json=data)
    
    if response.status_code == 200:
        print(f"✅ Topics updated successfully ({len(TOPICS)} topics)")
        for topic in TOPICS:
            print(f"   • {topic}")
        return True
    else:
        print(f"❌ Failed to update topics")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return False

def main():
    print(f"Repository: {REPO_OWNER}/{REPO_NAME}")
    print()
    
    desc_success = update_description()
    print()
    topics_success = update_topics()
    
    print()
    if desc_success and topics_success:
        print("✅ GitHub metadata updated successfully!")
        print(f"View: https://github.com/{REPO_OWNER}/{REPO_NAME}")
        return 0
    else:
        print("❌ Some updates failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())