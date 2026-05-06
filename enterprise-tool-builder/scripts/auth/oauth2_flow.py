"""
OAuth 2.0 token handling and refresh.

Used by: Salesforce, Google Workspace, HubSpot, Microsoft Graph
"""

import os
import json
import time
from typing import Dict, Optional


class OAuth2Client:
    """Handle OAuth 2.0 token management."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        redirect_uri: str = "http://localhost:8080/callback",
    ):
        """
        Initialize OAuth2 client.

        Args:
            client_id: OAuth 2.0 client ID.
            client_secret: OAuth 2.0 client secret.
            token_url: URL to exchange authorization code for tokens.
            redirect_uri: Redirect URI for authorization flow.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None

    def build_authorization_url(self, scopes: list, state: str = "state") -> str:
        """
        Build OAuth 2.0 authorization URL.

        Args:
            scopes: List of requested scopes.
            state: CSRF protection state parameter.

        Returns:
            Authorization URL for user to visit.
        """
        scopes_str = " ".join(scopes)
        return (
            f"https://oauth.example.com/authorize?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scopes={scopes_str}&"
            f"state={state}"
        )

    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, str]:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Code received from authorization endpoint.

        Returns:
            Dictionary with access_token, refresh_token, expires_in, etc.
        """
        # TODO: Implement token exchange
        # 1. POST to token_url with code, client_id, client_secret
        # 2. Extract and store access_token and refresh_token
        # 3. Calculate token expiry time
        pass

    def refresh_access_token(self) -> Dict[str, str]:
        """
        Refresh expired access token using refresh token.

        Returns:
            New access token information.

        Raises:
            ValueError: If refresh token is not available.
        """
        if not self.refresh_token:
            raise ValueError("Refresh token not available")

        # TODO: Implement token refresh
        # 1. POST to token_url with refresh_token, client_id, client_secret
        # 2. Update access_token and token_expiry
        pass

    def get_valid_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token.

        Raises:
            ValueError: If unable to obtain valid token.
        """
        if self.access_token and not self.is_token_expired():
            return self.access_token

        if self.refresh_token:
            self.refresh_access_token()
            return self.access_token

        raise ValueError("No valid access token available")

    def is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.token_expiry:
            return False
        return time.time() > self.token_expiry

    def build_auth_header(self) -> Dict[str, str]:
        """Build OAuth 2.0 Authorization header with valid token."""
        token = self.get_valid_access_token()
        return {"Authorization": f"Bearer {token}"}


def build_oauth2_headers(access_token: str, token_type: str = "Bearer") -> Dict[str, str]:
    """
    Build OAuth 2.0 Authorization header.

    Args:
        access_token: The OAuth 2.0 access token.
        token_type: The token type (default: Bearer).

    Returns:
        Dictionary with Authorization header.
    """
    return {"Authorization": f"{token_type} {access_token}"}


def load_oauth_credentials_from_file(credentials_file: str) -> Dict:
    """
    Load OAuth credentials from JSON file.

    Useful for service account credentials from Google Workspace.

    Args:
        credentials_file: Path to JSON credentials file.

    Returns:
        Dictionary with credentials.
    """
    with open(credentials_file, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    # Example usage
    client = OAuth2Client(
        client_id="your-client-id",
        client_secret="your-client-secret",
        token_url="https://oauth.example.com/token",
    )
    print(f"Authorization URL: {client.build_authorization_url(['scope1', 'scope2'])}")
