"""OAuth2 authentication handler."""

import os
import logging
from typing import Optional
import httpx

from .models import User, Role

logger = logging.getLogger(__name__)

# OAuth2 Configuration
OAUTH2_ENABLED = os.getenv("OAUTH2_ENABLED", "false").lower() == "true"
OAUTH2_PROVIDER = os.getenv("OAUTH2_PROVIDER", "")  # github, google, azure
OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID", "")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET", "")
OAUTH2_ISSUER = os.getenv("OAUTH2_ISSUER", "")


class OAuth2Handler:
    """OAuth2 authentication handler."""
    
    def __init__(self):
        """Initialize OAuth2 handler."""
        self.enabled = OAUTH2_ENABLED
        self.provider = OAUTH2_PROVIDER
        self.client_id = OAUTH2_CLIENT_ID
        self.client_secret = OAUTH2_CLIENT_SECRET
        self.issuer = OAUTH2_ISSUER
        
        if self.enabled and not all([self.provider, self.client_id, self.client_secret]):
            logger.warning("OAuth2 enabled but missing configuration. Disabling.")
            self.enabled = False
    
    def get_provider_config(self) -> dict:
        """
        Get OAuth2 provider configuration.
        
        Returns:
            Provider configuration dict
        """
        providers = {
            "github": {
                "authorization_endpoint": "https://github.com/login/oauth/authorize",
                "token_endpoint": "https://github.com/login/oauth/access_token",
                "userinfo_endpoint": "https://api.github.com/user"
            },
            "google": {
                "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_endpoint": "https://oauth2.googleapis.com/token",
                "userinfo_endpoint": "https://www.googleapis.com/oauth2/v2/userinfo"
            },
            "azure": {
                "authorization_endpoint": f"https://login.microsoftonline.com/{self.issuer}/oauth2/v2.0/authorize",
                "token_endpoint": f"https://login.microsoftonline.com/{self.issuer}/oauth2/v2.0/token",
                "userinfo_endpoint": "https://graph.microsoft.com/v1.0/me"
            }
        }
        
        return providers.get(self.provider, {})
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[str]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code
            redirect_uri: Redirect URI
            
        Returns:
            Access token or None
        """
        if not self.enabled:
            return None
        
        config = self.get_provider_config()
        if not config:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config["token_endpoint"],
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret
                    },
                    headers={"Accept": "application/json"}
                )
                
                response.raise_for_status()
                token_data = response.json()
                return token_data.get("access_token")
        except Exception as e:
            logger.error(f"OAuth2 token exchange failed: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[dict]:
        """
        Get user information from OAuth2 provider.
        
        Args:
            access_token: OAuth2 access token
            
        Returns:
            User information dict or None
        """
        if not self.enabled:
            return None
        
        config = self.get_provider_config()
        if not config:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    config["userinfo_endpoint"],
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"OAuth2 user info failed: {e}")
            return None
    
    async def authenticate(self, code: str, redirect_uri: str) -> Optional[User]:
        """
        Authenticate user via OAuth2.
        
        Args:
            code: Authorization code
            redirect_uri: Redirect URI
            
        Returns:
            User object if authenticated, None otherwise
        """
        # Exchange code for token
        access_token = await self.exchange_code_for_token(code, redirect_uri)
        if not access_token:
            return None
        
        # Get user info
        user_info = await self.get_user_info(access_token)
        if not user_info:
            return None
        
        # Convert provider-specific user info to our User model
        username = self._extract_username(user_info)
        email = self._extract_email(user_info)
        full_name = self._extract_full_name(user_info)
        
        # Determine roles (in production, lookup in database)
        roles = [Role.USER]
        
        return User(
            username=username,
            email=email,
            full_name=full_name,
            roles=roles,
            disabled=False
        )
    
    def _extract_username(self, user_info: dict) -> str:
        """Extract username from provider user info."""
        if self.provider == "github":
            return user_info.get("login", "unknown")
        elif self.provider == "google":
            return user_info.get("email", "unknown")
        elif self.provider == "azure":
            return user_info.get("userPrincipalName", "unknown")
        return "unknown"
    
    def _extract_email(self, user_info: dict) -> Optional[str]:
        """Extract email from provider user info."""
        return user_info.get("email")
    
    def _extract_full_name(self, user_info: dict) -> Optional[str]:
        """Extract full name from provider user info."""
        if self.provider == "github":
            return user_info.get("name")
        elif self.provider == "google":
            return user_info.get("name")
        elif self.provider == "azure":
            return user_info.get("displayName")
        return None


# Global instance
_oauth2_handler = None


def get_oauth2_handler() -> OAuth2Handler:
    """
    Get global OAuth2 handler instance.
    
    Returns:
        OAuth2Handler instance
    """
    global _oauth2_handler
    if _oauth2_handler is None:
        _oauth2_handler = OAuth2Handler()
    return _oauth2_handler

