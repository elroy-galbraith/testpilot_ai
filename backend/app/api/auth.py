"""
FastAPI router for authentication endpoints.
"""

import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.auth.jwt_auth import jwt_auth, get_current_user, AuthUser
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Request model for user login."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "testuser",
                "password": "password123"
            }
        }


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    permissions: list


class UserInfoResponse(BaseModel):
    """Response model for user information."""
    user_id: str
    email: Optional[str] = None
    permissions: list


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    This is a simplified authentication endpoint for development.
    In production, you would integrate with a proper user management system.
    """
    try:
        # For development purposes, accept any username/password
        # In production, validate against user database
        if not request.username or not request.password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        
        # Create token data (in production, get from user database)
        token_data = {
            "sub": request.username,
            "email": f"{request.username}@example.com",
            "permissions": [
                "test:generate",
                "test:execute", 
                "test:read",
                "test:write"
            ]
        }
        
        # Create access token
        access_token = jwt_auth.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes)
        )
        
        response = TokenResponse(
            access_token=access_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user_id=request.username,
            permissions=token_data["permissions"]
        )
        
        logger.info(f"User {request.username} logged in successfully")
        return response
        
    except Exception as e:
        logger.error(f"Login failed for user {request.username}: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(current_user: AuthUser = Depends(get_current_user)):
    """
    Get current user information.
    
    Returns information about the currently authenticated user.
    """
    return UserInfoResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        permissions=current_user.permissions
    )


@router.post("/refresh")
async def refresh_token(current_user: AuthUser = Depends(get_current_user)):
    """
    Refresh the current user's access token.
    
    Returns a new access token with extended expiration.
    """
    try:
        # Create new token data
        token_data = {
            "sub": current_user.user_id,
            "email": current_user.email,
            "permissions": current_user.permissions
        }
        
        # Create new access token
        access_token = jwt_auth.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes)
        )
        
        response = TokenResponse(
            access_token=access_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user_id=current_user.user_id,
            permissions=current_user.permissions
        )
        
        logger.info(f"Token refreshed for user {current_user.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Token refresh failed for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed") 