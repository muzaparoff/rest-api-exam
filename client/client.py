"""
Python client for User Management API.

This module provides a comprehensive Python client for interacting with
the User Management API. It's designed for test automation engineers
and provides a simple, intuitive interface.
"""
import requests
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin
import time
import json
from datetime import datetime

from exceptions import (
    APIError, ValidationError, AuthenticationError, NotFoundError,
    ConflictError, ServerError, ConnectionError, TimeoutError,
    create_exception_from_response
)

class UserAPIClient:
    """
    Python client for User Management API.
    
    Provides a simple interface for test automation engineers to interact
    with the User Management API.
    
    Features:
    - Automatic authentication handling
    - Retry logic for network issues
    - Structured error handling
    - Request/response logging
    - Connection pooling
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        log_level: str = "INFO"
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API server
            token: JWT authentication token (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Setup HTTP session with connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "UserAPIClient/1.0.0"
        })
        
        # Set authentication token if provided
        if token:
            self.set_token(token)
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def set_token(self, token: str):
        """
        Set the JWT authentication token.
        
        Args:
            token: JWT token
        """
        self.session.headers["Authorization"] = f"Bearer {token}"
        self.logger.info("Authentication token set")
    
    def clear_token(self):
        """Clear the authentication token."""
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
            self.logger.info("Authentication token cleared")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data (for POST/PUT)
            params: Query parameters
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response: Response object
            
        Raises:
            APIError: For various API-related errors
        """
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        
        # Prepare request data
        json_data = None
        if data is not None:
            json_data = data
        
        # Log request
        self.logger.debug(f"Making {method} request to {url}")
        if json_data:
            self.logger.debug(f"Request data: {json.dumps(json_data, indent=2)}")
        
        last_exception = None
        
        # Retry logic
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Log response
                self.logger.debug(f"Response: {response.status_code} - {response.reason}")
                
                # Handle different status codes
                if response.status_code < 400:
                    return response
                
                # Parse error response
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", f"HTTP {response.status_code}")
                except (ValueError, KeyError):
                    error_message = f"HTTP {response.status_code}: {response.reason}"
                
                # Create appropriate exception
                exception = create_exception_from_response(
                    response.status_code,
                    error_message,
                    error_data if 'error_data' in locals() else None
                )
                
                # Don't retry client errors (4xx), except for 429 (rate limiting)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    raise exception
                
                # For server errors (5xx) and rate limiting, try again
                if attempt < self.max_retries:
                    self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                
                raise exception
                
            except requests.exceptions.Timeout as e:
                last_exception = TimeoutError(f"Request timeout after {self.timeout}s")
            except requests.exceptions.ConnectionError as e:
                last_exception = ConnectionError(f"Connection error: {str(e)}")
            except requests.exceptions.RequestException as e:
                last_exception = APIError(f"Request error: {str(e)}")
            
            # Retry for network-related errors
            if attempt < self.max_retries:
                self.logger.warning(f"Network error (attempt {attempt + 1}), retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
            else:
                raise last_exception
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the API server is healthy.
        
        Returns:
            Dict: Health status information
            
        Raises:
            APIError: If health check fails
        """
        try:
            self.logger.info("Performing health check")
            response = self._make_request("GET", "/health")
            result = response.json()
            
            self.logger.info(f"Health check result: {result['status']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            raise APIError(f"Health check failed: {str(e)}")
    
    def login(self, username: str, password: str) -> str:
        """
        Authenticate with the API and get access token.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            str: Access token
            
        Raises:
            AuthenticationError: If login fails
        """
        try:
            self.logger.info(f"Attempting login for user: {username}")
            
            response = self._make_request(
                "POST",
                "/auth/login",
                data={"username": username, "password": password}
            )
            
            result = response.json()
            token = result["access_token"]
            
            # Set token for future requests
            self.set_token(token)
            
            self.logger.info(f"Login successful for user: {username}")
            return token
            
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise AuthenticationError(f"Login failed: {str(e)}")
    
    def create_user(
        self,
        user_id: str,
        name: str,
        phone_number: str,
        address: str
    ) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            user_id: Israeli ID (8-9 digits)
            name: User's full name
            phone_number: Israeli phone number (05XXXXXXXX)
            address: User's address
            
        Returns:
            Dict: Created user data
            
        Raises:
            ValidationError: If input data is invalid
            ConflictError: If user already exists
            APIError: For other errors
        """
        user_data = {
            "id": user_id,
            "name": name,
            "phone_number": phone_number,
            "address": address
        }
        
        try:
            self.logger.info(f"Creating user: {user_id}")
            
            response = self._make_request("POST", "/users", data=user_data)
            result = response.json()
            
            self.logger.info(f"User created successfully: {user_id}")
            return result
            
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create user: {str(e)}")
            raise APIError(f"Failed to create user: {str(e)}")
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to retrieve
            
        Returns:
            Dict: User data
            
        Raises:
            NotFoundError: If user doesn't exist
            APIError: For other errors
        """
        try:
            self.logger.info(f"Retrieving user: {user_id}")
            
            response = self._make_request("GET", f"/users/{user_id}")
            result = response.json()
            
            self.logger.info(f"User retrieved successfully: {user_id}")
            return result
            
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get user: {str(e)}")
            raise APIError(f"Failed to get user: {str(e)}")
    
    def list_users(self) -> List[str]:
        """
        List all user IDs.
        
        Returns:
            List[str]: List of user IDs
            
        Raises:
            APIError: If request fails
        """
        try:
            self.logger.info("Listing all user IDs")
            
            response = self._make_request("GET", "/users")
            result = response.json()
            
            self.logger.info(f"Found {len(result)} users")
            return result
            
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to list users: {str(e)}")
            raise APIError(f"Failed to list users: {str(e)}")
    
    def list_users_detailed(
        self,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List users with detailed information and pagination.
        
        Args:
            page: Page number (1-based)
            per_page: Number of users per page
            search: Optional search term
            
        Returns:
            Dict: Paginated user list with metadata
            
        Raises:
            APIError: If request fails
        """
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        
        try:
            self.logger.info(f"Listing detailed users (page: {page}, per_page: {per_page})")
            
            response = self._make_request("GET", "/users-detailed", params=params)
            result = response.json()
            
            self.logger.info(f"Found {result['total']} users total, {len(result['users'])} on page {page}")
            return result
            
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to list detailed users: {str(e)}")
            raise APIError(f"Failed to list detailed users: {str(e)}")
    
    def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        phone_number: Optional[str] = None,
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing user.
        
        Args:
            user_id: User ID to update
            name: New name (optional)
            phone_number: New phone number (optional)
            address: New address (optional)
            
        Returns:
            Dict: Updated user data
            
        Raises:
            NotFoundError: If user doesn't exist
            ValidationError: If input data is invalid
            APIError: For other errors
        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if phone_number is not None:
            update_data["phone_number"] = phone_number
        if address is not None:
            update_data["address"] = address
        
        if not update_data:
            raise ValidationError("At least one field must be provided for update")
        
        try:
            self.logger.info(f"Updating user: {user_id}")
            
            response = self._make_request("PUT", f"/users/{user_id}", data=update_data)
            result = response.json()
            
            self.logger.info(f"User updated successfully: {user_id}")
            return result
            
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update user: {str(e)}")
            raise APIError(f"Failed to update user: {str(e)}")
    
    def delete_user(self, user_id: str) -> None:
        """
        Delete a user.
        
        Args:
            user_id: User ID to delete
            
        Raises:
            NotFoundError: If user doesn't exist
            APIError: For other errors
        """
        try:
            self.logger.info(f"Deleting user: {user_id}")
            
            self._make_request("DELETE", f"/users/{user_id}")
            
            self.logger.info(f"User deleted successfully: {user_id}")
            
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete user: {str(e)}")
            raise APIError(f"Failed to delete user: {str(e)}")
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        self.logger.info("API client session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

# Convenience functions for test automation
def create_client(base_url: str = "http://localhost:8000", **kwargs) -> UserAPIClient:
    """
    Create a UserAPIClient instance.
    
    Args:
        base_url: Base URL of the API server
        **kwargs: Additional arguments for UserAPIClient
        
    Returns:
        UserAPIClient: Client instance
    """
    return UserAPIClient(base_url, **kwargs)

def create_authenticated_client(
    base_url: str = "http://localhost:8000",
    username: str = "admin",
    password: str = "password",
    **kwargs
) -> UserAPIClient:
    """
    Create an authenticated UserAPIClient instance.
    
    Args:
        base_url: Base URL of the API server
        username: Username for authentication
        password: Password for authentication
        **kwargs: Additional arguments for UserAPIClient
        
    Returns:
        UserAPIClient: Authenticated client instance
        
    Raises:
        AuthenticationError: If authentication fails
    """
    client = UserAPIClient(base_url, **kwargs)
    client.login(username, password)
    return client

# Test data helpers
class TestData:
    """Helper class for generating test data."""
    
    @staticmethod
    def valid_israeli_ids() -> List[str]:
        """Get list of valid Israeli IDs for testing."""
        return [
            "123456782",  # 9 digits
            "12345678",   # 8 digits
            "87654321",   # 8 digits
            "320780694",  # 9 digits
        ]
    
    @staticmethod
    def invalid_israeli_ids() -> List[str]:
        """Get list of invalid Israeli IDs for testing."""
        return [
            "1234567",      # Too short
            "1234567890",   # Too long
            "123456789",    # Invalid checksum
            "12345678a",    # Contains letter
            "",             # Empty
        ]
    
    @staticmethod
    def valid_phone_numbers() -> List[str]:
        """Get list of valid Israeli phone numbers for testing."""
        return [
            "0501234567",
            "0509876543",
            "0507654321",
            "0506543210",
        ]
    
    @staticmethod
    def invalid_phone_numbers() -> List[str]:
        """Get list of invalid Israeli phone numbers for testing."""
        return [
            "0521234567",   # Wrong prefix
            "050123456",    # Too short
            "05012345678",  # Too long
            "1501234567",   # Wrong start
            "050123456a",   # Contains letter
            "",             # Empty
        ]
    
    @staticmethod
    def sample_user(index: int = 0) -> Dict[str, str]:
        """
        Get sample user data for testing.
        
        Args:
            index: Index of the sample user (0-based)
            
        Returns:
            Dict: Sample user data
        """
        samples = [
            {
                "id": "123456782",
                "name": "John Doe",
                "phone_number": "0501234567",
                "address": "123 Main St, Tel Aviv"
            },
            {
                "id": "12345678",
                "name": "Jane Smith",
                "phone_number": "0509876543",
                "address": "456 Oak Ave, Haifa"
            },
            {
                "id": "87654321",
                "name": "Bob Johnson",
                "phone_number": "0507654321",
                "address": "789 Pine Rd, Jerusalem"
            }
        ]
        
        return samples[index % len(samples)]
