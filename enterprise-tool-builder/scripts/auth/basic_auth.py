"""
Basic authentication header builder.

Used by: Jira, Confluence, Zendesk, ServiceNow
"""

import base64
import os
from typing import Dict


def build_basic_auth_header(username: str, password: str) -> Dict[str, str]:
    """
    Build HTTP Basic Authentication header.

    Args:
        username: The username or email.
        password: The password or API token.

    Returns:
        Dictionary with Authorization header.

    Raises:
        ValueError: If username or password is empty.
    """
    if not username or not password:
        raise ValueError("Username and password cannot be empty")

    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def get_basic_auth_from_env(
    username_env: str,
    password_env: str,
) -> Dict[str, str]:
    """
    Build basic auth header from environment variables.

    Args:
        username_env: Environment variable name for username.
        password_env: Environment variable name for password.

    Returns:
        Authorization header dictionary.

    Raises:
        EnvironmentError: If environment variables are not set.
    """
    username = os.getenv(username_env)
    password = os.getenv(password_env)

    if not username:
        raise EnvironmentError(f"Environment variable {username_env} not set")
    if not password:
        raise EnvironmentError(f"Environment variable {password_env} not set")

    return build_basic_auth_header(username, password)


if __name__ == "__main__":
    # Example usage
    header = build_basic_auth_header("user@example.com", "api_token_123")
    print(f"Auth Header: {header}")
