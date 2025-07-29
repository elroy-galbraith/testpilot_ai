"""
JWT-based authentication middleware and utilities for TestPilot AI Backend.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

import jwt
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token data model."""
    user_id: str
    email: Optional[str] = None
    permissions: list = []


class AuthUser(BaseModel):
    """Authenticated user model."""
    user_id: str
    email: Optional[str] = None
    permissions: list = []


class JWTAuth:
    """JWT authentication handler."""
    
    def __init__(self):
        """Initialize JWT authentication."""
        self.secret_key = settings.jwt_secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a new JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            email: Optional[str] = payload.get("email")
            permissions: list = payload.get("permissions", [])
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(user_id=user_id, email=email, permissions=permissions)
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Global JWT auth instance
jwt_auth = JWTAuth()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthUser:
    """Get the current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = jwt_auth.verify_token(credentials.credentials)
    return AuthUser(
        user_id=token_data.user_id,
        email=token_data.email,
        permissions=token_data.permissions
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthUser]:
    """Get the current authenticated user from JWT token (optional)."""
    if not credentials:
        return None
    
    try:
        token_data = jwt_auth.verify_token(credentials.credentials)
        return AuthUser(
            user_id=token_data.user_id,
            email=token_data.email,
            permissions=token_data.permissions
        )
    except HTTPException:
        return None


def require_permissions(required_permissions: list):
    """Decorator to require specific permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: AuthUser = Depends(get_current_user), **kwargs):
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            # Check if user has all required permissions
            for permission in required_permissions:
                if permission not in current_user.permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required: {permission}"
                    )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_any_permission(required_permissions: list):
    """Decorator to require any of the specified permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: AuthUser = Depends(get_current_user), **kwargs):
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            # Check if user has any of the required permissions
            has_permission = any(
                permission in current_user.permissions 
                for permission in required_permissions
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required one of: {required_permissions}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# Common permission constants
PERMISSIONS = {
    "TEST_GENERATE": "test:generate",
    "TEST_EXECUTE": "test:execute",
    "TEST_READ": "test:read",
    "TEST_WRITE": "test:write",
    "ADMIN": "admin"
} 