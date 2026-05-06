"""
Environment variable loader for credentials.

Loads authentication credentials from .env files or environment.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv


class CredentialLoader:
    """Load and manage credentials from environment."""

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize credential loader.

        Args:
            env_file: Path to .env file. If None, uses environment variables.
        """
        if env_file:
            load_dotenv(env_file)

    def get_credentials(self, service: str) -> Dict[str, str]:
        """
        Get credentials for a service.

        Args:
            service: Service name (e.g., 'jira', 'slack', 'github').

        Returns:
            Dictionary with credentials for the service.

        Raises:
            EnvironmentError: If required credentials are not found.
        """
        credentials = {}

        if service.lower() == "jira":
            credentials = {
                "username": self._get_required_env("JIRA_USERNAME"),
                "api_token": self._get_required_env("JIRA_API_TOKEN"),
                "cloud_id": self._get_required_env("JIRA_CLOUD_ID"),
            }
        elif service.lower() == "slack":
            credentials = {
                "bot_token": self._get_required_env("SLACK_BOT_TOKEN"),
                "app_token": self._get_optional_env("SLACK_APP_TOKEN"),
            }
        elif service.lower() == "github":
            credentials = {
                "pat": self._get_required_env("GITHUB_PAT"),
                "username": self._get_required_env("GITHUB_USERNAME"),
            }
        elif service.lower() == "hubspot":
            credentials = {
                "private_app_token": self._get_required_env("HUBSPOT_PRIVATE_APP_TOKEN"),
            }
        elif service.lower() == "zendesk":
            credentials = {
                "email": self._get_required_env("ZENDESK_EMAIL"),
                "api_token": self._get_required_env("ZENDESK_API_TOKEN"),
                "subdomain": self._get_required_env("ZENDESK_SUBDOMAIN"),
            }
        else:
            raise ValueError(f"Unknown service: {service}")

        return credentials

    def _get_required_env(self, var_name: str) -> str:
        """Get required environment variable."""
        value = os.getenv(var_name)
        if not value:
            raise EnvironmentError(f"Required environment variable {var_name} not set")
        return value

    def _get_optional_env(self, var_name: str, default: str = None) -> Optional[str]:
        """Get optional environment variable."""
        return os.getenv(var_name, default)

    def validate_credentials(self, service: str, credentials: Dict) -> bool:
        """
        Validate that required credentials are present.

        Args:
            service: Service name.
            credentials: Credentials dictionary.

        Returns:
            True if valid.

        Raises:
            ValueError: If credentials are invalid.
        """
        required_fields = self._get_required_fields(service)
        missing_fields = [f for f in required_fields if f not in credentials or not credentials[f]]

        if missing_fields:
            raise ValueError(
                f"Missing required credentials for {service}: {missing_fields}"
            )

        return True

    def _get_required_fields(self, service: str) -> list:
        """Get required credential fields for a service."""
        service_fields = {
            "jira": ["username", "api_token", "cloud_id"],
            "slack": ["bot_token"],
            "github": ["pat", "username"],
            "hubspot": ["private_app_token"],
            "zendesk": ["email", "api_token", "subdomain"],
        }
        return service_fields.get(service.lower(), [])


def load_env_file(env_file: str = ".env"):
    """Load environment variables from .env file."""
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        print(f"Warning: {env_file} not found")


if __name__ == "__main__":
    # Example usage
    loader = CredentialLoader(env_file=".env")
    try:
        jira_creds = loader.get_credentials("jira")
        print(f"Jira credentials loaded: {list(jira_creds.keys())}")
    except EnvironmentError as e:
        print(f"Error: {e}")
