"""API key authentication."""

import os
import hashlib
import secrets
import logging
from typing import Optional
from datetime import datetime, timedelta

from .models import User, Role

logger = logging.getLogger(__name__)

# In-memory API key store (in production, use database)
_api_keys = {}


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        API key string
    """
    return f"fops_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for storage.
    
    Args:
        api_key: API key
        
    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def store_api_key(
    api_key: str,
    name: str,
    roles: list[Role],
    expires_days: int = 365
) -> dict:
    """
    Store API key.
    
    Args:
        api_key: API key
        name: Key name/description
        roles: User roles
        expires_days: Expiration in days
        
    Returns:
        API key metadata
    """
    hashed_key = hash_api_key(api_key)
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    metadata = {
        "name": name,
        "roles": roles,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat(),
        "last_used": None
    }
    
    _api_keys[hashed_key] = metadata
    return metadata


def verify_api_key(api_key: str) -> Optional[dict]:
    """
    Verify API key.
    
    Args:
        api_key: API key to verify
        
    Returns:
        API key metadata if valid, None otherwise
    """
    # Check environment variable API keys first
    env_api_key = os.getenv("API_KEY")
    if env_api_key and api_key == env_api_key:
        return {
            "name": "Environment API Key",
            "roles": [Role.ADMIN],
            "created_at": None,
            "expires_at": None,
            "last_used": datetime.utcnow().isoformat()
        }
    
    # Check stored API keys
    hashed_key = hash_api_key(api_key)
    if hashed_key not in _api_keys:
        return None
    
    metadata = _api_keys[hashed_key]
    
    # Check expiration
    if metadata["expires_at"]:
        expires_at = datetime.fromisoformat(metadata["expires_at"])
        if datetime.utcnow() > expires_at:
            logger.warning(f"Expired API key used: {metadata['name']}")
            return None
    
    # Update last used
    metadata["last_used"] = datetime.utcnow().isoformat()
    
    return metadata


def get_api_key_user(api_key: str) -> Optional[User]:
    """
    Get user from API key.
    
    Args:
        api_key: API key
        
    Returns:
        User object if valid, None otherwise
    """
    metadata = verify_api_key(api_key)
    if metadata is None:
        return None
    
    return User(
        username=f"api_key_{metadata['name'].replace(' ', '_').lower()}",
        full_name=metadata['name'],
        roles=metadata['roles'],
        disabled=False,
        api_key=api_key
    )


def revoke_api_key(api_key: str) -> bool:
    """
    Revoke an API key.
    
    Args:
        api_key: API key to revoke
        
    Returns:
        True if revoked, False if not found
    """
    hashed_key = hash_api_key(api_key)
    if hashed_key in _api_keys:
        del _api_keys[hashed_key]
        return True
    return False


def list_api_keys() -> list:
    """
    List all API keys (without revealing the actual keys).
    
    Returns:
        List of API key metadata
    """
    return [
        {
            "name": metadata["name"],
            "roles": [r.value for r in metadata["roles"]],
            "created_at": metadata["created_at"],
            "expires_at": metadata["expires_at"],
            "last_used": metadata["last_used"]
        }
        for metadata in _api_keys.values()
    ]

