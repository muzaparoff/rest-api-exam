"""
FastAPI application for User Management API.

This module defines the main FastAPI application with all endpoints,
middleware, and configuration for the User Management system.
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from fastapi import (
    FastAPI, HTTPException, Depends, status, Query,
    Security, Request, Response
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import (
    User, UserCreate, UserUpdate, UserResponse, UserList,
    HealthResponse, ErrorResponse
)
from database import get_db, init_db, check_db_health
from auth import verify_token, authenticate_user, create_user_token
from validators import validate_israeli_id, validate_phone_number

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/api.log') if os.path.exists('/app/logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.
    """
    # Startup
    logger.info("Starting User Management API...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    logger.info("User Management API started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down User Management API...")

# Create FastAPI application
app = FastAPI(
    title="User Management API",
    description="REST API for managing users with Israeli ID and phone validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"Response: {response.status_code} - "
        f"Process time: {process_time:.3f}s"
    )
    
    return response

# Dependency for optional authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Get current user from JWT token (optional).
    
    Returns:
        Optional[str]: Username if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    payload = verify_token(credentials.credentials)
    if not payload:
        return None
    
    return payload.get("sub")

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Check the health of the API service.
    
    Returns:
        HealthResponse: Service health status
    """
    logger.info("Health check requested")
    
    # Check database connectivity
    db_healthy = check_db_health()
    
    status_code = "healthy" if db_healthy else "unhealthy"
    message = "All systems operational" if db_healthy else "Database connectivity issues"
    
    response = HealthResponse(
        status=status_code,
        message=message,
        database=db_healthy
    )
    
    if not db_healthy:
        logger.warning("Health check failed - database connectivity issues")
    
    return response

# Authentication endpoints
@app.post("/auth/login", tags=["Authentication"])
async def login(credentials: dict):
    """
    Authenticate user and return access token.
    
    Args:
        credentials: Dictionary with username and password
        
    Returns:
        dict: Access token and token type
        
    Raises:
        HTTPException: If authentication fails
    """
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        logger.warning("Login attempt with missing credentials")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )
    
    # Authenticate user
    user = authenticate_user(username, password)
    if not user:
        logger.warning(f"Failed login attempt for username: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_user_token(username)
    
    logger.info(f"User logged in successfully: {username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800  # 30 minutes
    }

# User management endpoints
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Create a new user.
    
    Args:
        user: User data to create
        db: Database session
        current_user: Current authenticated user (optional)
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    try:
        logger.info(f"Creating user with ID: {user.id} (by: {current_user or 'anonymous'})")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.id == user.id).first()
        if existing_user:
            logger.warning(f"Attempt to create duplicate user: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this ID already exists"
            )
        
        # Create new user
        db_user = User(
            id=user.id,
            name=user.name,
            phone_number=user.phone_number,
            address=user.address
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User created successfully: {user.id}")
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user {user.id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating user"
        )

@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Retrieve user by ID.
    
    Args:
        user_id: User ID to retrieve
        db: Database session
        current_user: Current authenticated user (optional)
        
    Returns:
        UserResponse: User data
        
    Raises:
        HTTPException: If user not found
    """
    try:
        logger.info(f"Retrieving user: {user_id} (by: {current_user or 'anonymous'})")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User retrieved successfully: {user_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving user"
        )

@app.get("/users", response_model=List[str], tags=["Users"])
async def list_user_ids(
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    List all user IDs.
    
    Args:
        db: Database session
        current_user: Current authenticated user (optional)
        
    Returns:
        List[str]: List of user IDs
    """
    try:
        logger.info(f"Listing all user IDs (by: {current_user or 'anonymous'})")
        
        users = db.query(User.id).all()
        user_ids = [user.id for user in users]
        
        logger.info(f"Found {len(user_ids)} users")
        return user_ids
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while listing users"
        )

@app.get("/users-detailed", response_model=UserList, tags=["Users"])
async def list_users_detailed(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Users per page"),
    search: Optional[str] = Query(None, description="Search in name or address"),
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    List users with detailed information and pagination.
    
    Args:
        page: Page number (1-based)
        per_page: Number of users per page
        search: Optional search term
        db: Database session
        current_user: Current authenticated user (optional)
        
    Returns:
        UserList: Paginated list of users
    """
    try:
        logger.info(f"Listing detailed users (page: {page}, per_page: {per_page}, search: {search}) (by: {current_user or 'anonymous'})")
        
        # Build query
        query = db.query(User)
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_term),
                    User.address.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        logger.info(f"Found {len(users)} users on page {page} (total: {total})")
        
        return UserList(
            users=users,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing detailed users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while listing users"
        )

@app.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Update an existing user.
    
    Args:
        user_id: User ID to update
        user_update: Updated user data
        db: Database session
        current_user: Current authenticated user (optional)
        
    Returns:
        UserResponse: Updated user data
        
    Raises:
        HTTPException: If user not found
    """
    try:
        logger.info(f"Updating user: {user_id} (by: {current_user or 'anonymous'})")
        
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found for update: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated successfully: {user_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating user"
        )

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Delete a user.
    
    Args:
        user_id: User ID to delete
        db: Database session
        current_user: Current authenticated user (optional)
        
    Raises:
        HTTPException: If user not found
    """
    try:
        logger.info(f"Deleting user: {user_id} (by: {current_user or 'anonymous'})")
        
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found for deletion: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete user
        db.delete(user)
        db.commit()
        
        logger.info(f"User deleted successfully: {user_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting user"
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses"""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    
    return {
        "detail": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url)
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return {
        "detail": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development"
    )
