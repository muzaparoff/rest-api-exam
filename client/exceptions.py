"""
Custom exceptions for the User API client.

This module defines custom exception classes for better error handling
and debugging in the Python client library.
"""
from typing import Optional

class APIError(Exception):
    """
    Base exception for API errors.
    
    This is the base class for all API-related exceptions.
    """
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
    
    def __str__(self):
        if self.status_code:
            return f"API Error ({self.status_code}): {self.message}"
        return f"API Error: {self.message}"

class ValidationError(APIError):
    """
    Exception for validation errors (400 Bad Request).
    
    Raised when the API returns validation errors for input data.
    """
    pass

class AuthenticationError(APIError):
    """
    Exception for authentication errors (401 Unauthorized).
    
    Raised when authentication fails or token is invalid.
    """
    pass

class AuthorizationError(APIError):
    """
    Exception for authorization errors (403 Forbidden).
    
    Raised when user doesn't have permission for the requested resource.
    """
    pass

class NotFoundError(APIError):
    """
    Exception for not found errors (404 Not Found).
    
    Raised when the requested resource doesn't exist.
    """
    pass

class ConflictError(APIError):
    """
    Exception for conflict errors (409 Conflict).
    
    Raised when there's a conflict with the current state (e.g., duplicate user).
    """
    pass

class ServerError(APIError):
    """
    Exception for server errors (500+ status codes).
    
    Raised when the server encounters an internal error.
    """
    pass

class ConnectionError(APIError):
    """
    Exception for connection errors.
    
    Raised when there are network connectivity issues.
    """
    pass

class TimeoutError(APIError):
    """
    Exception for timeout errors.
    
    Raised when a request times out.
    """
    pass

def create_exception_from_response(status_code: int, message: str, response_data: Optional[dict] = None) -> APIError:
    """
    Create an appropriate exception based on HTTP status code.
    
    Args:
        status_code: HTTP status code
        message: Error message
        response_data: Response data from the API
        
    Returns:
        APIError: Appropriate exception instance
    """
    if status_code == 400:
        return ValidationError(message, status_code, response_data)
    elif status_code == 401:
        return AuthenticationError(message, status_code, response_data)
    elif status_code == 403:
        return AuthorizationError(message, status_code, response_data)
    elif status_code == 404:
        return NotFoundError(message, status_code, response_data)
    elif status_code == 409:
        return ConflictError(message, status_code, response_data)
    elif status_code >= 500:
        return ServerError(message, status_code, response_data)
    else:
        return APIError(message, status_code, response_data)
