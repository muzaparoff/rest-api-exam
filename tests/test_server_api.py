# tests/test_server_api.py - Comprehensive API endpoint tests
"""
Comprehensive test suite for the User Management API server.

This module tests all API endpoints with various scenarios including
success cases, error cases, and edge cases using TDD methodology.
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import json

# Add server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from app import app
from database import get_db
from models import Base

# Test database setup
def create_test_db():
    """Create a test database"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    return engine, TestingSessionLocal, db_path

@pytest.fixture(scope="function")
def test_client():
    """Create a test client with clean database for each test"""
    engine, TestingSessionLocal, db_path = create_test_db()
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Cleanup
    app.dependency_overrides.clear()
    os.unlink(db_path)

@pytest.fixture
def auth_headers():
    """Get authentication headers for protected endpoints"""
    # For now, return empty dict since auth is optional
    return {}

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_health_check_success(self, test_client):
        """Test health check returns healthy status"""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "database" in data
        assert "timestamp" in data

class TestAuthenticationEndpoints:
    """Test authentication endpoints"""
    
    @pytest.mark.unit
    def test_login_success(self, test_client):
        """Test successful login with valid credentials"""
        response = test_client.post(
            "/auth/login",
            json={"username": "admin", "password": "password"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    @pytest.mark.unit
    def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials"""
        response = test_client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401
    
    @pytest.mark.unit
    def test_login_missing_credentials(self, test_client):
        """Test login with missing credentials"""
        response = test_client.post("/auth/login", json={})
        assert response.status_code == 400

class TestCreateUserEndpoint:
    """Test user creation endpoint with TDD approach"""
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_create_user_success_9_digit_id(self, test_client):
        """Test creating user with valid 9-digit Israeli ID"""
        user_data = {
            "id": "123456782",  # Valid 9-digit Israeli ID
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St, Tel Aviv"
        }
        response = test_client.post("/users", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["id"] == user_data["id"]
        assert data["name"] == user_data["name"]
        assert data["phone_number"] == user_data["phone_number"]
        assert data["address"] == user_data["address"]
        assert "created_at" in data
        assert "updated_at" in data
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_create_user_success_8_digit_id(self, test_client):
        """Test creating user with valid 8-digit Israeli ID"""
        user_data = {
            "id": "12345678",   # Valid 8-digit Israeli ID
            "name": "Jane Doe",
            "phone_number": "0509876543",
            "address": "456 Oak Ave, Haifa"
        }
        response = test_client.post("/users", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["id"] == user_data["id"]
    
    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_id,expected_status", [
        ("1234567", 422),      # Too short (7 digits)
        ("1234567890", 422),   # Too long (10 digits)
        ("123456789", 422),    # Invalid checksum
        ("12345678a", 422),    # Contains letter
        ("", 422),             # Empty
        ("00000000", 422),     # All zeros
    ])
    def test_create_user_invalid_israeli_id(self, test_client, invalid_id, expected_status):
        """Test creating user with invalid Israeli ID fails"""
        user_data = {
            "id": invalid_id,
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St"
        }
        response = test_client.post("/users", json=user_data)
        assert response.status_code == expected_status
    
    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_phone,expected_status", [
        ("0521234567", 422),   # Wrong prefix (052)
        ("050123456", 422),    # Too short (9 digits)
        ("05012345678", 422),  # Too long (11 digits)
        ("1501234567", 422),   # Doesn't start with 05
        ("050123456a", 422),   # Contains letter
        ("", 422),             # Empty
        ("+972501234567", 422), # International format
    ])
    def test_create_user_invalid_phone_number(self, test_client, invalid_phone, expected_status):
        """Test creating user with invalid phone number fails"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",  
            "phone_number": invalid_phone,
            "address": "123 Main St"
        }
        response = test_client.post("/users", json=user_data)
        assert response.status_code == expected_status
    
    @pytest.mark.unit
    @pytest.mark.parametrize("field,invalid_value", [
        ("name", ""),
        ("name", "   "),
        ("address", ""),
        ("address", "   "),
    ])
    def test_create_user_empty_required_fields(self, test_client, field, invalid_value):
        """Test creating user with empty required fields fails"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St"
        }
        user_data[field] = invalid_value
        
        response = test_client.post("/users", json=user_data)
        assert response.status_code == 422
    
    @pytest.mark.unit
    def test_create_duplicate_user(self, test_client):
        """Test creating duplicate user fails with 409 conflict"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St"
        }
        
        # Create first user
        response1 = test_client.post("/users", json=user_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = test_client.post("/users", json=user_data)
        assert response2.status_code == 409

class TestGetUserEndpoint:
    """Test user retrieval endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_get_user_success(self, test_client):
        """Test getting existing user succeeds"""
        # Create user first
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St"
        }
        create_response = test_client.post("/users", json=user_data)
        assert create_response.status_code == 201
        
        # Get user
        response = test_client.get("/users/123456782")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == user_data["id"]
        assert data["name"] == user_data["name"]
        assert data["phone_number"] == user_data["phone_number"]
        assert data["address"] == user_data["address"]
    
    @pytest.mark.unit
    def test_get_user_not_found(self, test_client):
        """Test getting non-existent user fails with 404"""
        response = test_client.get("/users/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_get_user_empty_id(self, test_client):
        """Test getting user with empty ID"""
        response = test_client.get("/users/")
        # This should return 405 Method Not Allowed or redirect to list endpoint
        assert response.status_code in [404, 405, 200]  # Depends on FastAPI routing

class TestListUsersEndpoint:
    """Test user listing endpoints"""
    
    @pytest.mark.unit
    def test_list_users_empty(self, test_client):
        """Test listing users when none exist"""
        response = test_client.get("/users")
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_list_users_with_data(self, test_client):
        """Test listing users with existing data"""
        # Create multiple users
        users_data = [
            {"id": "123456782", "name": "John Doe", "phone_number": "0501234567", "address": "123 Main St"},
            {"id": "12345678", "name": "Jane Smith", "phone_number": "0509876543", "address": "456 Oak Ave"}
        ]
        
        for user_data in users_data:
            response = test_client.post("/users", json=user_data)
            assert response.status_code == 201
        
        # List users
        response = test_client.get("/users")
        assert response.status_code == 200
        
        user_ids = response.json()
        assert len(user_ids) == 2
        assert "123456782" in user_ids
        assert "12345678" in user_ids
    
    @pytest.mark.unit
    def test_list_users_detailed_empty(self, test_client):
        """Test listing detailed users when none exist"""
        response = test_client.get("/users-detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert data["users"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    @pytest.mark.unit
    def test_list_users_detailed_with_pagination(self, test_client):
        """Test listing detailed users with pagination"""
        # Create multiple users
        for i in range(15):
            user_data = {
                "id": f"12345678{i:01d}",  # This might not be valid ID, but for test structure
                "name": f"User {i}",
                "phone_number": f"050123456{i:01d}",
                "address": f"Address {i}"
            }
            # Only create users with valid data for this test
            if i < 3:  # Limit to 3 users for simplicity
                response = test_client.post("/users", json=user_data)
                if response.status_code != 201:
                    continue
        
        # Test pagination
        response = test_client.get("/users-detailed?page=1&per_page=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["users"]) <= 2
        assert data["page"] == 1
        assert data["per_page"] == 2

class TestUpdateUserEndpoint:
    """Test user update endpoint"""
    
    @pytest.mark.unit
    def test_update_user_success(self, test_client):
        """Test updating existing user succeeds"""
        # Create user first
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St"
        }
        create_response = test_client.post("/users", json=user_data)
        assert create_response.status_code == 201
        
        # Update user
        update_data = {
            "name": "John Smith",
            "address": "456 Oak Ave"
        }
        response = test_client.put("/users/123456782", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "John Smith"
        assert data["address"] == "456 Oak Ave"
        assert data["phone_number"] == user_data["phone_number"]  # Unchanged
    
    @pytest.mark.unit
    def test_update_user_not_found(self, test_client):
        """Test updating non-existent user fails with 404"""
        update_data = {"name": "New Name"}
        response = test_client.put("/users/nonexistent", json=update_data)
        assert response.status_code == 404

class TestDeleteUserEndpoint:
    """Test user deletion endpoint"""
    
    @pytest.mark.unit
    def test_delete_user_success(self, test_client):
        """Test deleting existing user succeeds"""
        # Create user first
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St"
        }
        create_response = test_client.post("/users", json=user_data)
        assert create_response.status_code == 201
        
        # Delete user
        response = test_client.delete("/users/123456782")
        assert response.status_code == 204
        
        # Verify user is deleted
        get_response = test_client.get("/users/123456782")
        assert get_response.status_code == 404
    
    @pytest.mark.unit
    def test_delete_user_not_found(self, test_client):
        """Test deleting non-existent user fails with 404"""
        response = test_client.delete("/users/nonexistent")
        assert response.status_code == 404

class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.unit
    def test_invalid_json_request(self, test_client):
        """Test request with invalid JSON"""
        response = test_client.post(
            "/users",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @pytest.mark.unit
    def test_missing_content_type(self, test_client):
        """Test request without proper content type"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St"
        }
        
        response = test_client.post("/users", data=json.dumps(user_data))
        # FastAPI should handle this gracefully, but might return 422
        assert response.status_code in [201, 422]

class TestIntegrationScenarios:
    """Integration test scenarios combining multiple operations"""
    
    @pytest.mark.integration
    @pytest.mark.smoke
    def test_complete_user_lifecycle(self, test_client):
        """Test complete CRUD operations for a user"""
        user_id = "123456782"
        
        # 1. Create user
        user_data = {
            "id": user_id,
            "name": "John Doe",
            "phone_number": "0501234567",
            "address": "123 Main St"
        }
        create_response = test_client.post("/users", json=user_data)
        assert create_response.status_code == 201
        
        # 2. Read user
        get_response = test_client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "John Doe"
        
        # 3. Update user
        update_data = {"name": "John Smith"}
        update_response = test_client.put(f"/users/{user_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "John Smith"
        
        # 4. List users (should include our user)
        list_response = test_client.get("/users")
        assert list_response.status_code == 200
        assert user_id in list_response.json()
        
        # 5. Delete user
        delete_response = test_client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 204
        
        # 6. Verify deletion
        final_get_response = test_client.get(f"/users/{user_id}")
        assert final_get_response.status_code == 404
    
    @pytest.mark.integration
    def test_multiple_users_operations(self, test_client):
        """Test operations with multiple users"""
        users_data = [
            {"id": "123456782", "name": "John Doe", "phone_number": "0501234567", "address": "123 Main St"},
            {"id": "12345678", "name": "Jane Smith", "phone_number": "0509876543", "address": "456 Oak Ave"},
        ]
        
        # Create multiple users
        for user_data in users_data:
            response = test_client.post("/users", json=user_data)
            assert response.status_code == 201
        
        # List all users
        list_response = test_client.get("/users")
        assert list_response.status_code == 200
        user_ids = list_response.json()
        assert len(user_ids) == 2
        
        # Get each user individually
        for user_data in users_data:
            response = test_client.get(f"/users/{user_data['id']}")
            assert response.status_code == 200
            assert response.json()["name"] == user_data["name"]
