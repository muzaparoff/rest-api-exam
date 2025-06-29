# conftest.py - Global pytest configuration and fixtures
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.app import app
from server.database import get_db
from server.models import Base
from client.client import UserAPIClient

# Test database configuration
@pytest.fixture(scope="function")
def test_db_engine():
    """Create a fresh test database for each test function"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Create engine for test database
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    os.unlink(db_path)

@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a database session for testing"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()

@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create a test client with clean database"""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass  # Session cleanup handled by test_db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up override
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def api_client(test_client):
    """Create Python API client for integration testing"""
    # Mock the base URL to use test client
    client = UserAPIClient("http://testserver")
    client.session = test_client  # Replace requests session with test client
    return client

# Common test data fixtures
@pytest.fixture
def valid_israeli_ids():
    """Valid Israeli ID test data"""
    return [
        "123456782",  # 9 digits
        "12345678",   # 8 digits  
        "87654321",   # 8 digits
        "320780694",  # Another valid 9 digit
    ]

@pytest.fixture
def invalid_israeli_ids():
    """Invalid Israeli ID test data"""
    return [
        "1234567",      # Too short (7 digits)
        "1234567890",   # Too long (10 digits)
        "123456789",    # Invalid checksum
        "12345678a",    # Contains letter
        "",             # Empty
        "00000000",     # All zeros (invalid)
    ]

@pytest.fixture
def valid_phone_numbers():
    """Valid Israeli phone number test data"""
    return [
        "0501234567",
        "0509876543",
        "0507654321",
        "0506543210",
        "050-123-4567",  # With dashes
        "050 123 4567",  # With spaces
    ]

@pytest.fixture
def invalid_phone_numbers():
    """Invalid Israeli phone number test data"""
    return [
        "0521234567",   # Wrong prefix (052)
        "050123456",    # Too short (9 digits)
        "05012345678",  # Too long (11 digits)
        "1501234567",   # Doesn't start with 05
        "050123456a",   # Contains letter
        "",             # Empty
        "+972501234567", # International format (not supported)
    ]

@pytest.fixture
def sample_users():
    """Sample user data for testing"""
    return [
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

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower, with I/O)"
    )
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests (critical functionality)"
    )
    config.addinivalue_line(
        "markers", "regression: marks tests as regression tests"
    )
