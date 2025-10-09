"""Authentication middleware and dependency injection."""

import os
import logging
from typing import Optional
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from .models import User, Role
from .jwt_handler import get_current_user as get_user_from_jwt
from .api_key import get_api_key_user
from .mtls import extract_cert_from_request, get_cert_user

logger = logging.getLogger(__name__)

# Configuration
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
AUTH_MODE = os.getenv("AUTH_MODE", "api_key")  # api_key, jwt, mtls, oauth2

# Security schemes
security_bearer = HTTPBearer(auto_error=False)
security_api_key = APIKeyHeader(name="X-API-Key", auto_error=False)


async def auth_middleware(request: Request, call_next):
    """
    Authentication middleware.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response
    """
    # Skip auth if disabled
    if not AUTH_ENABLED:
        return await call_next(request)
    
    # Skip auth for health and metrics endpoints
    if request.url.path in ["/healthz", "/metrics", "/docs", "/openapi.json", "/"]:
        return await call_next(request)
    
    # Skip auth for static files
    if request.url.path.startswith("/static/"):
        return await call_next(request)
    
    # Try to authenticate user
    user = await get_authenticated_user(request)
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "authentication_required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Attach user to request state
    request.state.user = user
    
    return await call_next(request)


async def get_authenticated_user(request: Request) -> Optional[User]:
    """
    Get authenticated user from request.
    
    Args:
        request: FastAPI request
        
    Returns:
        User object if authenticated, None otherwise
    """
    # Try mTLS first (highest security)
    if AUTH_MODE in ["mtls", "all"]:
        cert_pem = extract_cert_from_request(dict(request.headers))
        if cert_pem:
            user = get_cert_user(cert_pem)
            if user:
                logger.info(f"Authenticated via mTLS: {user.username}")
                return user
    
    # Try API key
    if AUTH_MODE in ["api_key", "all"]:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            user = get_api_key_user(api_key)
            if user:
                logger.info(f"Authenticated via API Key: {user.username}")
                return user
    
    # Try JWT bearer token
    if AUTH_MODE in ["jwt", "oauth2", "all"]:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user = get_user_from_jwt(token)
            if user:
                logger.info(f"Authenticated via JWT: {user.username}")
                return user
    
    return None


async def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    api_key: Optional[str] = Security(security_api_key)
) -> User:
    """
    Dependency to require authentication.
    
    Args:
        request: FastAPI request
        credentials: Bearer token credentials
        api_key: API key
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException if not authenticated
    """
    if not AUTH_ENABLED:
        # Return default admin user when auth is disabled
        return User(username="admin", roles=[Role.ADMIN], disabled=False)
    
    # Check if user is already authenticated by middleware
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user
    
    # Try to authenticate
    user = await get_authenticated_user(request)
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "authentication_required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def require_role(
    required_role: Role,
    user: User = Depends(require_auth)
) -> User:
    """
    Dependency to require specific role.
    
    Args:
        required_role: Required role
        user: Authenticated user
        
    Returns:
        User if has required role
        
    Raises:
        HTTPException if insufficient permissions
    """
    # Admin has all permissions
    if Role.ADMIN in user.roles:
        return user
    
    # Check if user has required role
    if required_role not in user.roles:
        raise HTTPException(
            status_code=403,
            detail={"error": "insufficient_permissions"}
        )
    
    return user


def require_admin(user: User = Depends(require_auth)) -> User:
    """
    Dependency to require admin role.
    
    Args:
        user: Authenticated user
        
    Returns:
        User if admin
        
    Raises:
        HTTPException if not admin
    """
    if Role.ADMIN not in user.roles:
        raise HTTPException(
            status_code=403,
            detail={"error": "admin_required"}
        )
    
    return user


def optional_auth(request: Request) -> Optional[User]:
    """
    Optional authentication (does not raise exception).
    
    Args:
        request: FastAPI request
        
    Returns:
        User if authenticated, None otherwise
    """
    if not AUTH_ENABLED:
        return None
    
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user
    
    return None

