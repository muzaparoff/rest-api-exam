"""
JWT Authentication module for the User API.

This module provides JWT token creation, validation, and authentication
middleware for protecting API endpoints.
"""
import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from passlib.context import CryptContext

# Configure logging
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"Created access token for: {data.get('sub', 'unknown')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Optional[Dict]: Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token has expired")
            return None
        
        logger.debug(f"Successfully verified token for: {payload.get('sub', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_user_from_token(token: str) -> Optional[str]:
    """
    Extract username from a valid JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Optional[str]: Username if token is valid, None otherwise
    """
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None

# Simple in-memory user store for demo purposes
# In production, this would be in a database
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("password"),
        "is_active": True
    },
    "testuser": {
        "username": "testuser", 
        "hashed_password": hash_password("testpass"),
        "is_active": True
    }
}

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        Optional[Dict]: User data if authenticated, None otherwise
    """
    user = DEMO_USERS.get(username)
    if not user:
        logger.warning(f"User not found: {username}")
        return None
    
    if not verify_password(password, user["hashed_password"]):
        logger.warning(f"Invalid password for user: {username}")
        return None
    
    if not user.get("is_active", False):
        logger.warning(f"Inactive user attempted login: {username}")
        return None
    
    logger.info(f"User authenticated successfully: {username}")
    return user

def create_user_token(username: str) -> str:
    """
    Create an access token for a user.
    
    Args:
        username: Username
        
    Returns:
        str: JWT access token
    """
    token_data = {"sub": username, "type": "access"}
    return create_access_token(token_data)
