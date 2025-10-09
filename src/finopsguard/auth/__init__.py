"""Authentication and authorization module for FinOpsGuard."""

from .jwt_handler import create_access_token, verify_token, get_current_user
from .api_key import verify_api_key, get_api_key_user
from .mtls import verify_client_cert, get_cert_user
from .oauth2 import OAuth2Handler
from .models import User, Role
from .middleware import auth_middleware, require_auth, require_role

__all__ = [
    'create_access_token',
    'verify_token',
    'get_current_user',
    'verify_api_key',
    'get_api_key_user',
    'verify_client_cert',
    'get_cert_user',
    'OAuth2Handler',
    'User',
    'Role',
    'auth_middleware',
    'require_auth',
    'require_role',
]

