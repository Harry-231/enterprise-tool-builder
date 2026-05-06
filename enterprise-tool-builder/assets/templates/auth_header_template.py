"""
Authentication header injection patterns.

Demonstrates how to build auth headers for different authentication methods:
- Basic Authentication (Base64 encoded username:password)
- Bearer Token (OAuth 2.0 tokens, API keys)
- OAuth 2.0 with token refresh
"""

import base64
import os
from typing import Dict, Optional


def build_basic_auth_header(username: str, password: str) -> Dict[str, str]:
    """
    Build HTTP Basic Authentication header.

    Used by: Jira Cloud, Confluence Cloud, Zendesk

    Args:
        username: The username or email.
        password: The password or API token.

    Returns:
        Dictionary with Authorization header.

    Example:
        >>> build_basic_auth_header("user@example.com", "api_token_123")
        {'Authorization': 'Basic dXNlckBleGFtcGxlLmNvbTphcGlfdG9rZW5fMTIz'}
    """
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def build_bearer_token_header(token: str) -> Dict[str, str]:
    """
    Build Bearer Token authentication header.

    Used by: Slack, GitHub, Notion, HubSpot, Google Workspace

    Args:
        token: The bearer token or API key.

    Returns:
        Dictionary with Authorization header.

    Example:
        >>> build_bearer_token_header("xoxb-1234567890")
        {'Authorization': 'Bearer xoxb-1234567890'}
    """
    return {"Authorization": f"Bearer {token}"}


def build_oauth2_headers(access_token: str, token_type: str = "Bearer") -> Dict[str, str]:
    """
    Build OAuth 2.0 Authorization header.

    Used by: Salesforce, Google Workspace, HubSpot, Microsoft Graph

    Args:
        access_token: The OAuth 2.0 access token.
        token_type: The token type (default: Bearer).

    Returns:
        Dictionary with Authorization header.

    Example:
        >>> build_oauth2_headers("ya29.a0AfH6SMBx...")
        {'Authorization': 'Bearer ya29.a0AfH6SMBx...'}
    """
    return {"Authorization": f"{token_type} {access_token}"}


def build_custom_header_auth(
    header_name: str, header_value: str
) -> Dict[str, str]:
    """
    Build custom header authentication.

    Some APIs use custom headers for authentication instead of Authorization header.

    Args:
        header_name: The custom header name (e.g., "X-API-Key").
        header_value: The custom header value (e.g., the API key).

    Returns:
        Dictionary with custom auth header.

    Example:
        >>> build_custom_header_auth("X-API-Key", "sk-1234567890")
        {'X-API-Key': 'sk-1234567890'}
    """
    return {header_name: header_value}


def get_auth_from_env(
    username_key: str, password_key: str
) -> Dict[str, str]:
    """
    Retrieve credentials from environment variables and build auth header.

    Args:
        username_key: Environment variable name for username.
        password_key: Environment variable name for password.

    Returns:
        Basic auth header dictionary.

    Raises:
        EnvironmentError: If required environment variables are not set.

    Example:
        >>> get_auth_from_env("JIRA_USERNAME", "JIRA_API_TOKEN")
        {'Authorization': 'Basic ...'}
    """
    username = os.getenv(username_key)
    password = os.getenv(password_key)

    if not username or not password:
        raise EnvironmentError(
            f"Missing required environment variables: {username_key}, {password_key}"
        )

    return build_basic_auth_header(username, password)


def get_bearer_token_from_env(token_key: str) -> Dict[str, str]:
    """
    Retrieve bearer token from environment variable.

    Args:
        token_key: Environment variable name for the token.

    Returns:
        Bearer auth header dictionary.

    Raises:
        EnvironmentError: If the environment variable is not set.

    Example:
        >>> get_bearer_token_from_env("SLACK_BOT_TOKEN")
        {'Authorization': 'Bearer xoxb-...'}
    """
    token = os.getenv(token_key)

    if not token:
        raise EnvironmentError(f"Missing required environment variable: {token_key}")

    return build_bearer_token_header(token)
