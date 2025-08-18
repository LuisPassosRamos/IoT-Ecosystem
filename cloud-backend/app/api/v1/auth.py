from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from ..models.schemas import LoginRequest, LoginResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "default-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Demo user credentials (in production, use proper user management)
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "admin")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "password123")

def create_access_token(data: dict) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@router.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """Authenticate user and return JWT token."""
    try:
        # Validate credentials (demo implementation)
        if login_request.username != DEMO_USERNAME or login_request.password != DEMO_PASSWORD:
            logger.warning(f"Failed login attempt for user: {login_request.username}")
            raise HTTPException(
                status_code=401, 
                detail="Incorrect username or password"
            )
        
        # Create JWT token
        token_data = {
            "sub": login_request.username,
            "iat": datetime.utcnow(),
            "type": "access_token"
        }
        
        access_token = create_access_token(token_data)
        
        logger.info(f"Successful login for user: {login_request.username}")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,  # Convert to seconds
            user=login_request.username
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/verify")
async def verify_auth(current_user: dict = Depends(verify_token)):
    """Verify current authentication token."""
    try:
        return {
            "authenticated": True,
            "user": current_user.get("sub"),
            "token_type": current_user.get("type", "access_token"),
            "expires": current_user.get("exp"),
            "issued_at": current_user.get("iat")
        }
    except Exception as e:
        logger.error(f"Error verifying auth: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout")
async def logout(current_user: dict = Depends(verify_token)):
    """Logout user (token-based auth doesn't require server-side logout)."""
    try:
        logger.info(f"User logged out: {current_user.get('sub')}")
        return {
            "message": "Successfully logged out",
            "user": current_user.get("sub")
        }
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user-info")
async def get_user_info(current_user: dict = Depends(verify_token)):
    """Get current user information."""
    try:
        return {
            "username": current_user.get("sub"),
            "authenticated": True,
            "token_issued": current_user.get("iat"),
            "token_expires": current_user.get("exp"),
            "permissions": ["read_sensors", "view_dashboard"]  # Demo permissions
        }
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Optional: Protected route example
@router.get("/protected")
async def protected_route(current_user: dict = Depends(verify_token)):
    """Example protected route that requires authentication."""
    return {
        "message": f"Hello {current_user.get('sub')}, this is a protected route!",
        "timestamp": datetime.utcnow().isoformat(),
        "user_data": current_user
    }