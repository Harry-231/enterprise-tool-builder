"""
Bearer token authentication header builder.

Used by: Slack, GitHub, Notion, HubSpot, Google Workspace
"""

import os
from typing import Dict


def build_bearer_token_header(token: str) -> Dict[str, str]:
    """
    Build Bearer Token authentication header.

    Args:
        token: The bearer token or API key.

    Returns:
        Dictionary with Authorization header.

    Raises:
        ValueError: If token is empty.
    """
    if not token:
        raise ValueError("Token cannot be empty")

    return {"Authorization": f"Bearer {token}"}


def get_bearer_token_from_env(token_env: str) -> Dict[str, str]:
    """
    Build bearer token header from environment variable.

    Args:
        token_env: Environment variable name for the token.

    Returns:
        Authorization header dictionary.

    Raises:
        EnvironmentError: If environment variable is not set.
    """
    token = os.getenv(token_env)

    if not token:
        raise EnvironmentError(f"Environment variable {token_env} not set")

    return build_bearer_token_header(token)


if __name__ == "__main__":
    # Example usage
    header = build_bearer_token_header("xoxb-1234567890")
    print(f"Auth Header: {header}")
