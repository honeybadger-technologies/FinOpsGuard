"""JWT token handling for authentication."""

import os
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional, List

from jose import JWTError, jwt
from passlib.context import CryptContext

from .models import User, TokenData, Role

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches
    """
    try:
        # Truncate to 72 bytes for bcrypt compatibility
        password_bytes = plain_password.encode('utf-8')[:72]
        return pwd_context.verify(password_bytes, hashed_password)
    except ValueError as e:
        if "72 bytes" in str(e):
            # Handle bcrypt length limit gracefully
            logger.warning(f"Password too long for bcrypt: {e}")
            return False
        raise


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    # Truncate to 72 bytes for bcrypt compatibility
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "iss": "finopsguard"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles_str: List[str] = payload.get("roles", [])
        
        if username is None:
            return None
        
        # Convert role strings to Role enum
        roles = [Role(r) for r in roles_str if r in [role.value for role in Role]]
        
        return TokenData(username=username, roles=roles)
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def get_current_user(token: str) -> Optional[User]:
    """
    Get current user from token.
    
    Args:
        token: JWT token string
        
    Returns:
        User object if valid, None otherwise
    """
    token_data = verify_token(token)
    if token_data is None:
        return None
    
    # In production, this would query the user database
    # For now, return a user object from token data
    return User(
        username=token_data.username,
        roles=token_data.roles,
        disabled=False
    )


def create_user_token(user: User, expires_minutes: int = None) -> str:
    """
    Create token for a user.
    
    Args:
        user: User object
        expires_minutes: Token expiration in minutes
        
    Returns:
        JWT token
    """
    expires = timedelta(minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    
    token_data = {
        "sub": user.username,
        "roles": [role.value for role in user.roles],
        "email": user.email,
        "full_name": user.full_name
    }
    
    return create_access_token(token_data, expires_delta=expires)

