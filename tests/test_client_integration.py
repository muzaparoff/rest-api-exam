# tests/test_client_integration.py - Python client integration tests
"""
Integration tests for the Python client library.

These tests verify that the Python client works correctly with the API server,
testing both success and failure scenarios in a real environment.
"""
import pytest
import sys
import os
import responses
import json
from unittest.mock import Mock, patch

# Add client directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'client'))

from client import UserAPIClient, TestData, create_client, create_authenticated_client
from exceptions import (
    APIError, ValidationError, AuthenticationError, NotFoundError,
    ConflictError, ServerError, ConnectionError, TimeoutError
)

class TestUserAPIClientBasics:
    """Test basic client functionality"""
    
    def setup_method(self):
        """Set up test client"""
        self.base_url = "http://test-server:8000"
        self.client = UserAPIClient(self.base_url)
    
    def teardown_method(self):
        """Clean up test client"""
        self.client.close()
    
    @pytest.mark.unit
    def test_client_initialization(self):
        """Test client initialization with various parameters"""
        client = UserAPIClient(
            base_url="http://localhost:8000",
            timeout=60,
            max_retries=5,
            retry_delay=2.0,
            log_level="DEBUG"
        )
        
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 60
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
        
        client.close()
    
    @pytest.mark.unit
    def test_token_management(self):
        """Test token setting and clearing"""
        token = "test-token"
        
        # Set token
        self.client.set_token(token)
        assert "Authorization" in self.client.session.headers
        assert self.client.session.headers["Authorization"] == f"Bearer {token}"
        
        # Clear token
        self.client.clear_token()
        assert "Authorization" not in self.client.session.headers
    
    @pytest.mark.unit
    def test_context_manager(self):
        """Test client as context manager"""
        with UserAPIClient("http://test-server:8000") as client:
            assert client.base_url == "http://test-server:8000"
        # Client should be closed after context exit

class TestUserAPIClientMockedRequests:
    """Test client with mocked HTTP requests"""
    
    def setup_method(self):
        """Set up test client"""
        self.base_url = "http://test-server:8000"
        self.client = UserAPIClient(self.base_url)
    
    def teardown_method(self):
        """Clean up test client"""
        self.client.close()
    
    @responses.activate
    @pytest.mark.unit
    def test_health_check_success(self):
        """Test successful health check"""
        responses.add(
            responses.GET,
            f"{self.base_url}/health",
            json={
                "status": "healthy",
                "message": "All systems operational",
                "database": True,
                "timestamp": "2023-12-01T10:00:00"
            },
            status=200
        )
        
        result = self.client.health_check()
        assert result["status"] == "healthy"
        assert result["database"] is True
    
    @responses.activate
    @pytest.mark.unit
    def test_health_check_failure(self):
        """Test health check failure"""
        responses.add(
            responses.GET,
            f"{self.base_url}/health",
            json={"detail": "Service unavailable"},
            status=503
        )
        
        with pytest.raises(APIError):
            self.client.health_check()
    
    @responses.activate
    @pytest.mark.unit
    def test_login_success(self):
        """Test successful login"""
        responses.add(
            responses.POST,
            f"{self.base_url}/auth/login",
            json={
                "access_token": "test-token",
                "token_type": "bearer",
                "expires_in": 1800
            },
            status=200
        )
        
        token = self.client.login("admin", "password")
        assert token == "test-token"
        assert "Authorization" in self.client.session.headers
    
    @responses.activate
    @pytest.mark.unit
    def test_login_failure(self):
        """Test login failure"""
        responses.add(
            responses.POST,
            f"{self.base_url}/auth/login",
            json={"detail": "Invalid credentials"},
            status=401
        )
        
        with pytest.raises(AuthenticationError):
            self.client.login("admin", "wrong-password")
    
    @responses.activate
    @pytest.mark.unit
    def test_create_user_success(self):
        """Test successful user creation"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St"
        }
        
        responses.add(
            responses.POST,
            f"{self.base_url}/users",
            json={
                **user_data,
                "created_at": "2023-12-01T10:00:00",
                "updated_at": "2023-12-01T10:00:00"
            },
            status=201
        )
        
        result = self.client.create_user(**user_data)
        assert result["id"] == user_data["id"]
        assert result["name"] == user_data["name"]
    
    @responses.activate
    @pytest.mark.unit
    def test_create_user_validation_error(self):
        """Test user creation with validation error"""
        responses.add(
            responses.POST,
            f"{self.base_url}/users",
            json={"detail": "Invalid Israeli ID"},
            status=422
        )
        
        with pytest.raises(ValidationError, match="Invalid Israeli ID"):
            self.client.create_user("invalid", "John Doe", "0501234567", "123 Main St")
    
    @responses.activate
    @pytest.mark.unit
    def test_create_user_conflict(self):
        """Test user creation conflict (duplicate)"""
        responses.add(
            responses.POST,
            f"{self.base_url}/users",
            json={"detail": "User with this ID already exists"},
            status=409
        )
        
        with pytest.raises(ConflictError):
            self.client.create_user("123456782", "John Doe", "0501234567", "123 Main St")
    
    @responses.activate
    @pytest.mark.unit
    def test_get_user_success(self):
        """Test successful user retrieval"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St",
            "created_at": "2023-12-01T10:00:00",
            "updated_at": "2023-12-01T10:00:00"
        }
        
        responses.add(
            responses.GET,
            f"{self.base_url}/users/123456782",
            json=user_data,
            status=200
        )
        
        result = self.client.get_user("123456782")
        assert result["id"] == "123456782"
        assert result["name"] == "John Doe"
    
    @responses.activate
    @pytest.mark.unit
    def test_get_user_not_found(self):
        """Test getting non-existent user"""
        responses.add(
            responses.GET,
            f"{self.base_url}/users/nonexistent",
            json={"detail": "User not found"},
            status=404
        )
        
        with pytest.raises(NotFoundError):
            self.client.get_user("nonexistent")
    
    @responses.activate
    @pytest.mark.unit
    def test_list_users_success(self):
        """Test successful user listing"""
        user_ids = ["123456782", "12345678", "87654321"]
        
        responses.add(
            responses.GET,
            f"{self.base_url}/users",
            json=user_ids,
            status=200
        )
        
        result = self.client.list_users()
        assert result == user_ids
        assert len(result) == 3
    
    @responses.activate
    @pytest.mark.unit
    def test_list_users_empty(self):
        """Test listing users when none exist"""
        responses.add(
            responses.GET,
            f"{self.base_url}/users",
            json=[],
            status=200
        )
        
        result = self.client.list_users()
        assert result == []
    
    @responses.activate
    @pytest.mark.unit
    def test_update_user_success(self):
        """Test successful user update"""
        updated_user = {
            "id": "123456782",
            "name": "John Smith",
            "phone_number": "0501234567",
            "address": "456 Oak Ave",
            "created_at": "2023-12-01T10:00:00",
            "updated_at": "2023-12-01T11:00:00"
        }
        
        responses.add(
            responses.PUT,
            f"{self.base_url}/users/123456782",
            json=updated_user,
            status=200
        )
        
        result = self.client.update_user("123456782", name="John Smith", address="456 Oak Ave")
        assert result["name"] == "John Smith"
        assert result["address"] == "456 Oak Ave"
    
    @responses.activate
    @pytest.mark.unit
    def test_delete_user_success(self):
        """Test successful user deletion"""
        responses.add(
            responses.DELETE,
            f"{self.base_url}/users/123456782",
            status=204
        )
        
        # Should not raise any exception
        self.client.delete_user("123456782")
    
    @responses.activate
    @pytest.mark.unit
    def test_delete_user_not_found(self):
        """Test deleting non-existent user"""
        responses.add(
            responses.DELETE,
            f"{self.base_url}/users/nonexistent",
            json={"detail": "User not found"},
            status=404
        )
        
        with pytest.raises(NotFoundError):
            self.client.delete_user("nonexistent")

class TestErrorHandlingAndRetries:
    """Test error handling and retry logic"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = UserAPIClient(
            "http://test-server:8000",
            max_retries=2,
            retry_delay=0.1  # Fast retries for tests
        )
    
    def teardown_method(self):
        """Clean up test client"""
        self.client.close()
    
    @responses.activate
    @pytest.mark.unit
    def test_retry_on_server_error(self):
        """Test retry logic on server errors"""
        # First two requests fail, third succeeds
        responses.add(responses.GET, f"{self.client.base_url}/health", status=500)
        responses.add(responses.GET, f"{self.client.base_url}/health", status=500)
        responses.add(
            responses.GET,
            f"{self.client.base_url}/health",
            json={"status": "healthy", "database": True},
            status=200
        )
        
        result = self.client.health_check()
        assert result["status"] == "healthy"
        assert len(responses.calls) == 3  # Should have made 3 requests
    
    @responses.activate
    @pytest.mark.unit
    def test_no_retry_on_client_error(self):
        """Test no retry on client errors (4xx)"""
        responses.add(
            responses.POST,
            f"{self.client.base_url}/users",
            json={"detail": "Validation error"},
            status=400
        )
        
        with pytest.raises(ValidationError):
            self.client.create_user("invalid", "name", "phone", "address")
        
        assert len(responses.calls) == 1  # Should only make 1 request
    
    @pytest.mark.unit
    def test_connection_error_handling(self):
        """Test handling of connection errors"""
        # Use invalid URL to simulate connection error
        client = UserAPIClient("http://invalid-host:9999", max_retries=1, retry_delay=0.1)
        
        with pytest.raises(ConnectionError):
            client.health_check()
        
        client.close()
    
    @responses.activate
    @pytest.mark.unit
    def test_timeout_handling(self):
        """Test handling of timeout errors"""
        # Mock timeout by not adding any response
        client = UserAPIClient("http://test-server:8000", timeout=0.1, max_retries=1)
        
        with pytest.raises((TimeoutError, ConnectionError)):
            client.health_check()
        
        client.close()

class TestConvenienceFunctions:
    """Test convenience functions and helpers"""
    
    @pytest.mark.unit
    def test_create_client(self):
        """Test create_client convenience function"""
        client = create_client("http://localhost:8000")
        assert isinstance(client, UserAPIClient)
        assert client.base_url == "http://localhost:8000"
        client.close()
    
    @responses.activate
    @pytest.mark.unit
    def test_create_authenticated_client(self):
        """Test create_authenticated_client convenience function"""
        responses.add(
            responses.POST,
            "http://localhost:8000/auth/login",
            json={"access_token": "test-token", "token_type": "bearer"},
            status=200
        )
        
        client = create_authenticated_client("http://localhost:8000", "admin", "password")
        assert isinstance(client, UserAPIClient)
        assert "Authorization" in client.session.headers
        client.close()

class TestTestDataHelpers:
    """Test the TestData helper class"""
    
    @pytest.mark.unit
    def test_valid_israeli_ids(self):
        """Test valid Israeli IDs helper"""
        ids = TestData.valid_israeli_ids()
        assert isinstance(ids, list)
        assert len(ids) > 0
        for id_str in ids:
            assert isinstance(id_str, str)
            assert len(id_str) in [8, 9]
    
    @pytest.mark.unit
    def test_invalid_israeli_ids(self):
        """Test invalid Israeli IDs helper"""
        ids = TestData.invalid_israeli_ids()
        assert isinstance(ids, list)
        assert len(ids) > 0
    
    @pytest.mark.unit
    def test_valid_phone_numbers(self):
        """Test valid phone numbers helper"""
        phones = TestData.valid_phone_numbers()
        assert isinstance(phones, list)
        assert len(phones) > 0
        for phone in phones:
            assert isinstance(phone, str)
            assert phone.startswith("05")
    
    @pytest.mark.unit
    def test_invalid_phone_numbers(self):
        """Test invalid phone numbers helper"""
        phones = TestData.invalid_phone_numbers()
        assert isinstance(phones, list)
        assert len(phones) > 0
    
    @pytest.mark.unit
    def test_sample_user(self):
        """Test sample user helper"""
        user = TestData.sample_user(0)
        assert isinstance(user, dict)
        assert "id" in user
        assert "name" in user
        assert "phone_number" in user
        assert "address" in user
        
        # Test different indices
        user1 = TestData.sample_user(1)
        user2 = TestData.sample_user(2)
        assert user1["id"] != user2["id"]

class TestIntegrationScenarios:
    """Integration test scenarios for client"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = UserAPIClient("http://test-server:8000")
    
    def teardown_method(self):
        """Clean up test client"""
        self.client.close()
    
    @responses.activate
    @pytest.mark.integration
    def test_complete_user_workflow(self):
        """Test complete user management workflow"""
        user_data = TestData.sample_user(0)
        
        # Mock all API calls
        responses.add(
            responses.POST,
            f"{self.client.base_url}/users",
            json={**user_data, "created_at": "2023-12-01T10:00:00", "updated_at": "2023-12-01T10:00:00"},
            status=201
        )
        
        responses.add(
            responses.GET,
            f"{self.client.base_url}/users/{user_data['id']}",
            json={**user_data, "created_at": "2023-12-01T10:00:00", "updated_at": "2023-12-01T10:00:00"},
            status=200
        )
        
        responses.add(
            responses.GET,
            f"{self.client.base_url}/users",
            json=[user_data["id"]],
            status=200
        )
        
        responses.add(
            responses.PUT,
            f"{self.client.base_url}/users/{user_data['id']}",
            json={**user_data, "name": "Updated Name", "updated_at": "2023-12-01T11:00:00"},
            status=200
        )
        
        responses.add(
            responses.DELETE,
            f"{self.client.base_url}/users/{user_data['id']}",
            status=204
        )
        
        # 1. Create user
        created_user = self.client.create_user(**user_data)
        assert created_user["id"] == user_data["id"]
        
        # 2. Get user
        retrieved_user = self.client.get_user(user_data["id"])
        assert retrieved_user["id"] == user_data["id"]
        
        # 3. List users
        user_ids = self.client.list_users()
        assert user_data["id"] in user_ids
        
        # 4. Update user
        updated_user = self.client.update_user(user_data["id"], name="Updated Name")
        assert updated_user["name"] == "Updated Name"
        
        # 5. Delete user
        self.client.delete_user(user_data["id"])  # Should not raise exception
    
    @responses.activate
    @pytest.mark.integration
    def test_authentication_workflow(self):
        """Test authentication workflow"""
        # Mock login
        responses.add(
            responses.POST,
            f"{self.client.base_url}/auth/login",
            json={"access_token": "test-token", "token_type": "bearer"},
            status=200
        )
        
        # Mock authenticated request
        responses.add(
            responses.GET,
            f"{self.client.base_url}/users",
            json=["123456782"],
            status=200
        )
        
        # Login
        token = self.client.login("admin", "password")
        assert token == "test-token"
        
        # Make authenticated request
        users = self.client.list_users()
        assert "123456782" in users
        
        # Check that Authorization header was sent
        assert len(responses.calls) == 2
        auth_header = responses.calls[1].request.headers.get("Authorization")
        assert auth_header == "Bearer test-token"
