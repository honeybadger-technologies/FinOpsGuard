"""Authentication and user management endpoints."""

import os
import logging
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request

from ..auth.models import (
    User, Role, LoginRequest, TokenResponse,
    APIKeyRequest, APIKeyResponse
)
from ..auth.jwt_handler import verify_password, get_password_hash, create_user_token
from ..auth.api_key import generate_api_key, store_api_key, list_api_keys, revoke_api_key
from ..auth.middleware import require_auth, require_admin
from ..auth.oauth2 import get_oauth2_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Mock user database (in production, use PostgreSQL)
_users_db = {}

def _get_users_db():
    """Get users database with lazy password hashing."""
    global _users_db
    if not _users_db:
        _users_db = {
            "admin": {
                "username": "admin",
                "full_name": "Administrator",
                "email": "admin@finopsguard.local",
                "hashed_password": get_password_hash(os.getenv("ADMIN_PASSWORD", "admin")),
                "roles": [Role.ADMIN],
                "disabled": False
            }
        }
    return _users_db


@router.post("/login", response_model=TokenResponse)
async def login(login_req: LoginRequest):
    """
    Authenticate and get access token.
    
    Args:
        login_req: Login credentials
        
    Returns:
        Access token
    """
    users_db = _get_users_db()
    user_data = users_db.get(login_req.username)
    
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_credentials"}
        )
    
    if not verify_password(login_req.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_credentials"}
        )
    
    if user_data.get("disabled", False):
        raise HTTPException(
            status_code=403,
            detail={"error": "account_disabled"}
        )
    
    # Create user object
    user = User(
        username=user_data["username"],
        email=user_data.get("email"),
        full_name=user_data.get("full_name"),
        roles=user_data["roles"],
        disabled=user_data.get("disabled", False)
    )
    
    # Create token
    token = create_user_token(user)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int(os.getenv("JWT_EXPIRE_MINUTES", "60")) * 60
    )


@router.get("/me")
async def get_current_user_info(user: User = Depends(require_auth)):
    """
    Get current user information.
    
    Args:
        user: Authenticated user
        
    Returns:
        User information
    """
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "roles": [role.value for role in user.roles],
        "disabled": user.disabled
    }


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_request: APIKeyRequest,
    user: User = Depends(require_admin)
):
    """
    Create a new API key (admin only).
    
    Args:
        key_request: API key request
        user: Authenticated admin user
        
    Returns:
        API key response
    """
    # Generate API key
    api_key = generate_api_key()
    
    # Store metadata
    metadata = store_api_key(
        api_key=api_key,
        name=key_request.name,
        roles=key_request.roles,
        expires_days=key_request.expires_days
    )
    
    return APIKeyResponse(
        api_key=api_key,
        name=key_request.name,
        created_at=metadata["created_at"],
        expires_at=metadata["expires_at"]
    )


@router.get("/api-keys")
async def list_api_keys_endpoint(user: User = Depends(require_admin)):
    """
    List all API keys (admin only).
    
    Args:
        user: Authenticated admin user
        
    Returns:
        List of API keys (without actual key values)
    """
    return {"api_keys": list_api_keys()}


@router.delete("/api-keys/{api_key}")
async def revoke_api_key_endpoint(
    api_key: str,
    user: User = Depends(require_admin)
):
    """
    Revoke an API key (admin only).
    
    Args:
        api_key: API key to revoke
        user: Authenticated admin user
        
    Returns:
        Success message
    """
    success = revoke_api_key(api_key)
    if not success:
        raise HTTPException(status_code=404, detail={"error": "api_key_not_found"})
    
    return {"message": "API key revoked successfully"}


@router.get("/oauth2/login")
async def oauth2_login():
    """
    Initiate OAuth2 login flow.
    
    Returns:
        Authorization URL
    """
    oauth2 = get_oauth2_handler()
    
    if not oauth2.enabled:
        raise HTTPException(
            status_code=501,
            detail={"error": "oauth2_not_configured"}
        )
    
    config = oauth2.get_provider_config()
    redirect_uri = os.getenv("OAUTH2_REDIRECT_URI", "http://localhost:8080/auth/oauth2/callback")
    
    auth_url = (
        f"{config['authorization_endpoint']}"
        f"?client_id={oauth2.client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
    )
    
    return {"authorization_url": auth_url}


@router.get("/oauth2/callback")
async def oauth2_callback(code: str, state: Optional[str] = None):
    """
    OAuth2 callback handler.
    
    Args:
        code: Authorization code
        state: State parameter (for CSRF protection)
        
    Returns:
        Access token
    """
    oauth2 = get_oauth2_handler()
    
    if not oauth2.enabled:
        raise HTTPException(
            status_code=501,
            detail={"error": "oauth2_not_configured"}
        )
    
    redirect_uri = os.getenv("OAUTH2_REDIRECT_URI", "http://localhost:8080/auth/oauth2/callback")
    
    # Exchange code for user
    user = await oauth2.authenticate(code, redirect_uri)
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "oauth2_authentication_failed"}
        )
    
    # Create JWT token for the user
    token = create_user_token(user)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int(os.getenv("JWT_EXPIRE_MINUTES", "60")) * 60
    )


@router.post("/refresh")
async def refresh_token(user: User = Depends(require_auth)):
    """
    Refresh access token.
    
    Args:
        user: Authenticated user
        
    Returns:
        New access token
    """
    # Create new token
    token = create_user_token(user)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int(os.getenv("JWT_EXPIRE_MINUTES", "60")) * 60
    )


@router.get("/roles")
async def list_roles(user: User = Depends(require_auth)):
    """
    List available roles.
    
    Args:
        user: Authenticated user
        
    Returns:
        List of roles
    """
    return {
        "roles": [
            {"value": role.value, "name": role.name}
            for role in Role
        ]
    }

