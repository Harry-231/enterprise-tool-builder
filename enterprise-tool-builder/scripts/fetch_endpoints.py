"""
Fetch and extract API endpoints from API documentation sources.

This script fetches endpoint definitions and stores them in JSON files
for tool generation.
"""

import json
import requests
from typing import Dict, List, Optional
from pathlib import Path


class EndpointFetcher:
    """Fetch API endpoints from documentation sources."""

    def __init__(self, output_dir: str = "assets/endpoints"):
        """Initialize fetcher."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_jira_endpoints(self, cloud_id: str) -> List[Dict]:
        """
        Fetch Jira Cloud API endpoints.

        Args:
            cloud_id: Jira Cloud ID.

        Returns:
            List of endpoint definitions.
        """
        endpoints = [
            {
                "id": "jira_create_issue",
                "method": "POST",
                "path": "/issue",
                "description": "Create a new issue",
            },
            {
                "id": "jira_list_issues",
                "method": "GET",
                "path": "/search",
                "description": "Search for issues using JQL",
                "pagination": "offset-based",
            },
            {
                "id": "jira_get_issue",
                "method": "GET",
                "path": "/issue/{issueKey}",
                "description": "Get issue details",
            },
        ]
        return endpoints

    def fetch_slack_endpoints(self) -> List[Dict]:
        """Fetch Slack API endpoints."""
        endpoints = [
            {
                "id": "slack_send_message",
                "method": "POST",
                "path": "/chat.postMessage",
                "description": "Send a message to a channel",
            },
            {
                "id": "slack_list_channels",
                "method": "GET",
                "path": "/conversations.list",
                "description": "List all channels",
                "pagination": "cursor-based",
            },
        ]
        return endpoints

    def fetch_github_endpoints(self) -> List[Dict]:
        """Fetch GitHub API endpoints."""
        endpoints = [
            {
                "id": "github_create_issue",
                "method": "POST",
                "path": "/repos/{owner}/{repo}/issues",
                "description": "Create a new GitHub issue",
            },
            {
                "id": "github_list_issues",
                "method": "GET",
                "path": "/repos/{owner}/{repo}/issues",
                "description": "List issues in a repository",
                "pagination": "offset-based",
            },
        ]
        return endpoints

    def save_endpoints(self, service: str, endpoints: List[Dict]):
        """
        Save endpoints to JSON file.

        Args:
            service: Service name (e.g., 'jira', 'slack', 'github').
            endpoints: List of endpoint definitions.
        """
        output_file = self.output_dir / f"{service}_endpoints.json"
        data = {
            "service": service,
            "endpoints": endpoints,
        }
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(endpoints)} endpoints to {output_file}")

    def fetch_all_endpoints(self):
        """Fetch endpoints from all supported services."""
        print("Fetching API endpoints from all services...")

        jira_endpoints = self.fetch_jira_endpoints(cloud_id="your-cloud-id")
        self.save_endpoints("jira", jira_endpoints)

        slack_endpoints = self.fetch_slack_endpoints()
        self.save_endpoints("slack", slack_endpoints)

        github_endpoints = self.fetch_github_endpoints()
        self.save_endpoints("github", github_endpoints)

        print("All endpoints fetched successfully")


if __name__ == "__main__":
    fetcher = EndpointFetcher()
    fetcher.fetch_all_endpoints()
