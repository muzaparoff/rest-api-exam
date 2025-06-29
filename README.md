# REST API Automation Infrastructure

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

A comprehensive REST API server with Python client for automated testing infrastructure, designed for efficient testing of software components with proper Israeli ID and phone number validation.

## 🚀 Quick Start

### Prerequisites
- **Docker** and **Docker Compose** installed
- **Bash shell** (macOS/Linux) or **Git Bash** (Windows)
- **curl** and **jq** (for testing and output formatting)

### One-Command Setup
```bash
# Clone and navigate to the project
git clone <repository-url>
cd rest-api-exam

# Make build script executable and run
chmod +x build_and_test.sh
./build_and_test.sh
```

This script will:
1. ✅ Build Docker images
2. 🚀 Start services 
3. 💾 Inject test data with valid Israeli IDs
4. 🧪 Run comprehensive TDD tests
5. 📊 Display detailed results with color coding

## 📋 Features

### 🔧 Server Features
- **User Management**: Create, retrieve, update, delete, and list users
- **Israeli ID Validation**: 8-9 digits with official checksum algorithm
- **Israeli Phone Validation**: Must start with "05", exactly 10 digits total
- **Health Check**: Service health monitoring with database connectivity
- **SQLite Database**: Persistent storage with WAL mode for concurrency
- **Structured Logging**: Comprehensive request/error logging with timestamps
- **Input Validation**: Robust data validation with detailed error messages
- **JWT Authentication**: Token-based authentication (bonus feature)
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Error Handling**: Structured error responses with proper HTTP status codes

### 🐍 Python Client Features  
- **Simple Interface**: Intuitive API for test automation engineers
- **Error Handling**: Custom exceptions with retry logic and detailed messages
- **Authentication Support**: JWT token handling with auto-refresh
- **Connection Pooling**: HTTP session reuse for better performance
- **Request/Response Logging**: Built-in logging for debugging
- **Context Manager**: Automatic cleanup with `with` statement
- **Test Data Helpers**: Pre-built valid/invalid data for testing

### 🧪 Testing Features
- **TDD Methodology**: Red-Green-Refactor cycle implementation
- **Comprehensive Coverage**: Unit, integration, and contract tests
- **Pytest Framework**: Industry-standard testing with advanced features
- **Mock Testing**: HTTP request mocking with responses library
- **Parametrized Tests**: Data-driven testing for edge cases
- **Performance Benchmarks**: Speed and memory usage testing
- **CI/CD Ready**: Automated testing pipeline support

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     REST API Ecosystem                         │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Python Client │   FastAPI       │   SQLite Database           │
│                 │   Server        │                             │
│   - HTTP Client │   - Validation  │   - Users Table             │
│   - Auth        │   - Logging     │   - Indexes                 │
│   - Retry Logic │   - JWT Auth    │   - WAL Mode                │
│   - Error Handling│ - CORS        │   - Transactions            │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

## 📖 API Documentation

### Core Endpoints

#### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "message": "All systems operational", 
  "database": true,
  "timestamp": "2023-12-01T10:00:00"
}
```

#### Authentication
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

#### Create User
```http
POST /users
Content-Type: application/json
Authorization: Bearer <token> (optional)

{
  "id": "123456782",           # Israeli ID (8-9 digits, valid checksum)
  "name": "John Doe",          # Required, 2+ characters
  "phone_number": "0501234567", # Must start with "05", exactly 10 digits
  "address": "123 Main St"     # Required, non-empty
}
```

#### Get User
```http
GET /users/{user_id}
Authorization: Bearer <token> (optional)
```

#### List Users (IDs only)
```http
GET /users
Authorization: Bearer <token> (optional)
```

#### List Users (Detailed with Pagination)
```http
GET /users-detailed?page=1&per_page=10&search=john
Authorization: Bearer <token> (optional)
```

#### Update User
```http
PUT /users/{user_id}
Content-Type: application/json
Authorization: Bearer <token> (optional)

{
  "name": "Updated Name",      # Optional
  "phone_number": "0509876543", # Optional
  "address": "New Address"     # Optional
}
```

#### Delete User
```http
DELETE /users/{user_id}
Authorization: Bearer <token> (optional)
```

## 🧪 Validation Rules

### Israeli ID Validation
- ✅ Must be 8 or 9 digits only
- ✅ Must pass official Israeli ID checksum algorithm
- ✅ 8-digit IDs are internally padded with leading zero
- ✅ Examples: `123456782`, `12345678`, `87654321`
- ❌ Invalid: `1234567` (too short), `1234567890` (too long), `123456789` (invalid checksum)

### Phone Number Validation
- ✅ Must start with "05" exactly
- ✅ Exactly 10 digits total
- ✅ Accepts formatting (dashes, spaces) but normalizes to digits
- ✅ Examples: `0501234567`, `050-123-4567`, `050 123 4567`
- ❌ Invalid: `0521234567` (wrong prefix), `050123456` (too short), `05012345678` (too long)

## 🐳 Docker Usage

### Quick Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

### Manual Docker Commands
```bash
# Build image
docker build -t user-api .

# Run container
docker run -p 8000:8000 -v $(pwd)/data:/app/data user-api

# Interactive shell
docker run -it user-api /bin/bash
```

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./data/users.db

# Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
SQL_DEBUG=false
```

## 🧪 Testing & TDD

### Test Structure
```
tests/
├── test_validators_tdd.py      # TDD validator tests (Red-Green-Refactor)
├── test_server_api.py          # API endpoint tests 
├── test_client_integration.py  # Python client tests
└── conftest.py                 # Pytest configuration and fixtures
```

### TDD Methodology Implementation
Our tests follow the **Red-Green-Refactor** cycle:

1. **🔴 Red**: Write failing tests first
2. **🟢 Green**: Write minimal code to pass tests  
3. **🔵 Refactor**: Improve code quality while keeping tests green

### Running Tests

#### Automated Testing (Recommended)
```bash
# Full test suite with reporting
./build_and_test.sh

# Tests only (services must be running)
./build_and_test.sh --tests-only

# Build without tests
./build_and_test.sh --no-tests
```

#### Manual Testing
```bash
# All tests with coverage
docker-compose exec api python -m pytest tests/ -v --cov=. --cov-report=html

# Specific test categories
docker-compose exec api python -m pytest tests/ -m "unit"      # Unit tests only
docker-compose exec api python -m pytest tests/ -m "smoke"     # Smoke tests only
docker-compose exec api python -m pytest tests/ -m "integration" # Integration tests

# Specific test files
docker-compose exec api python -m pytest tests/test_validators_tdd.py -v
docker-compose exec api python -m pytest tests/test_server_api.py -v

# With detailed output
docker-compose exec api python -m pytest tests/ -v --tb=long --show-capture=all
```

### Test Categories & Markers
```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Tests with I/O operations
@pytest.mark.smoke         # Critical functionality tests
@pytest.mark.regression    # Previously failing scenarios
@pytest.mark.slow          # Long-running tests
```

### Test Data & Fixtures
The test suite includes comprehensive fixtures for:
- ✅ Valid Israeli IDs: `["123456782", "12345678", "87654321"]`
- ❌ Invalid Israeli IDs: `["1234567", "1234567890", "123456789"]`
- ✅ Valid phone numbers: `["0501234567", "0509876543"]`
- ❌ Invalid phone numbers: `["0521234567", "050123456"]`
- 🧪 Sample user data for integration tests

## 🔧 Python Client Usage

### Basic Usage
```python
from client.client import UserAPIClient

# Create client
client = UserAPIClient("http://localhost:8000")

# Health check
health = client.health_check()
print(f"API Status: {health['status']}")

# Create user
user = client.create_user(
    user_id="123456782",
    name="John Doe", 
    phone_number="0501234567",
    address="123 Main St, Tel Aviv"
)

# Get user
user = client.get_user("123456782")
print(f"User: {user['name']}")

# List users
user_ids = client.list_users()
print(f"Total users: {len(user_ids)}")

# Update user
updated = client.update_user("123456782", name="John Smith")

# Delete user
client.delete_user("123456782")

# Always close the client
client.close()
```

### Authentication
```python
from client.client import create_authenticated_client

# Create authenticated client
with create_authenticated_client(
    "http://localhost:8000", 
    "admin", 
    "password"
) as client:
    # All requests will include JWT token
    users = client.list_users()
```

### Error Handling
```python
from client.exceptions import ValidationError, NotFoundError, ConflictError

try:
    client.create_user("invalid-id", "Name", "0501234567", "Address")
except ValidationError as e:
    print(f"Validation failed: {e.message}")
except ConflictError as e:
    print(f"User already exists: {e.message}")
except NotFoundError as e:
    print(f"User not found: {e.message}")
```

### Test Data Helpers
```python
from client.client import TestData

# Get test data
valid_ids = TestData.valid_israeli_ids()
invalid_phones = TestData.invalid_phone_numbers()
sample_user = TestData.sample_user(0)

# Use in tests
for user_id in valid_ids:
    client.create_user(user_id, "Test User", "0501234567", "Test Address")
```

## 📊 Build Script Features

The `build_and_test.sh` script provides comprehensive automation:

### Command Options
```bash
./build_and_test.sh --help              # Show help
./build_and_test.sh                     # Full build and test
./build_and_test.sh --no-tests          # Build without testing
./build_and_test.sh --tests-only        # Run tests only
./build_and_test.sh --cleanup-only      # Clean up containers
./build_and_test.sh --verbose           # Enable debug output
```

### Features
- 🎨 **Colorized Output**: Green for success, red for errors, blue for info
- 📝 **Detailed Logging**: All actions logged to `./logs/build_test.log`
- 📊 **JSON Results**: Test results saved to `./logs/test_results.json`
- 🔄 **Retry Logic**: Automatic retries for network-related failures
- 🏥 **Health Checks**: Waits for services to be ready before testing
- 🧪 **Test Data Injection**: Inserts valid test users automatically
- 📈 **Progress Tracking**: Step-by-step progress indication
- 🧹 **Auto Cleanup**: Automatic cleanup on script exit

### Sample Output
```bash
================================================================
 User Management API - BUILD & TEST
================================================================
[INFO] Starting build and test process at 2023-12-01 10:00:00
[STEP] Checking prerequisites...
[SUCCESS] Docker is running
[SUCCESS] docker-compose is available
[STEP] Building Docker images...
[SUCCESS] Docker images built successfully
[STEP] Starting services...
[SUCCESS] Services started successfully
[STEP] Waiting for services to be ready...
[SUCCESS] API server is healthy and ready
[STEP] Injecting test data...
[SUCCESS] ✓ User 123456782 (John Doe) inserted successfully
[SUCCESS] ✓ User 87654321 (Jane Smith) inserted successfully
[INFO] Data injection complete: 5 successful, 0 failed
[STEP] Running comprehensive tests...
[SUCCESS] ✓ Server unit tests passed
[SUCCESS] ✓ HTTP integration tests passed
[SUCCESS] ✓ API contract tests passed
================================================================
 TEST RESULTS SUMMARY
================================================================
[SUCCESS] === ALL TESTS PASSED! ===
```

## 🚀 Future Improvements & Roadmap

### 🎯 Short-term Improvements (Next Sprint)
- [ ] **Enhanced Database Support**
  - [ ] PostgreSQL migration for production environments
  - [ ] Database connection pooling optimization
  - [ ] Advanced indexing strategies for large datasets
  
- [ ] **Performance Optimizations**
  - [ ] Redis caching for frequently accessed data
  - [ ] Request/response compression
  - [ ] Database query optimization with explain plans
  
- [ ] **Security Enhancements**
  - [ ] Rate limiting per IP address
  - [ ] Input sanitization improvements
  - [ ] SQL injection prevention validation
  - [ ] HTTPS enforcement and TLS configuration

- [ ] **API Enhancements**
  - [ ] API versioning support (v1, v2)
  - [ ] Bulk operations (create/update multiple users)
  - [ ] Advanced search and filtering capabilities
  - [ ] Pagination improvements with cursor-based navigation

### 🎯 Medium-term Enhancements (Next Quarter)
- [ ] **Microservices Architecture**
  - [ ] Split into user service, auth service, validation service
  - [ ] Service mesh implementation with Istio
  - [ ] Inter-service communication with gRPC
  - [ ] Circuit breaker pattern implementation
  
- [ ] **Advanced Authentication & Authorization**
  - [ ] OAuth 2.0 / OpenID Connect integration
  - [ ] Role-based access control (RBAC)
  - [ ] Multi-factor authentication (MFA)
  - [ ] Integration with external identity providers (LDAP, Active Directory)
  
- [ ] **Event-Driven Architecture**
  - [ ] Event sourcing for user state changes
  - [ ] Apache Kafka for event streaming
  - [ ] CQRS (Command Query Responsibility Segregation) pattern
  - [ ] Asynchronous processing with Celery
  
- [ ] **Advanced Validation & Business Rules**
  - [ ] Rule engine for complex validation scenarios
  - [ ] Custom validation plugins
  - [ ] Machine learning for fraud detection
  - [ ] Real-time ID verification with external APIs

### 🎯 Long-term Vision (Next Year)
- [ ] **Cloud-Native Deployment**
  - [ ] Kubernetes deployment with Helm charts
  - [ ] Auto-scaling based on metrics (HPA/VPA)
  - [ ] Multi-region deployment for high availability
  - [ ] GitOps deployment pipeline with ArgoCD
  
- [ ] **Scalability & Performance**
  - [ ] Database sharding for horizontal scaling
  - [ ] Read replicas for query optimization  
  - [ ] CDN integration for static content
  - [ ] Edge computing deployment
  
- [ ] **Advanced Monitoring & Observability**
  - [ ] OpenTelemetry for distributed tracing
  - [ ] Prometheus + Grafana monitoring stack
  - [ ] ELK stack for centralized logging
  - [ ] Custom dashboards and alerting rules
  
- [ ] **Machine Learning Integration**
  - [ ] AI-powered user verification
  - [ ] Anomaly detection for suspicious activities
  - [ ] Predictive analytics for user behavior
  - [ ] Automated fraud prevention

### 🛠️ DevOps & Infrastructure Improvements
- [ ] **CI/CD Pipeline Enhancement**
  - [ ] GitHub Actions / GitLab CI integration
  - [ ] Automated security scanning (SAST/DAST)
  - [ ] Infrastructure as Code with Terraform
  - [ ] Blue-green deployment strategy
  
- [ ] **Quality Assurance**
  - [ ] Mutation testing for test quality validation
  - [ ] Property-based testing with Hypothesis
  - [ ] Contract testing with Pact
  - [ ] Performance testing with Locust
  
- [ ] **Documentation & Developer Experience**
  - [ ] Interactive API documentation with code examples
  - [ ] SDK generation for multiple programming languages
  - [ ] Developer portal with guides and tutorials
  - [ ] Postman collection auto-generation

### 🔧 Technical Debt & Maintenance
- [ ] **Code Quality Improvements**
  - [ ] Type hints coverage to 100%
  - [ ] Code complexity reduction (cyclomatic complexity < 10)
  - [ ] Dependency vulnerability scanning
  - [ ] License compliance checking
  
- [ ] **Testing Infrastructure**
  - [ ] Contract testing between services
  - [ ] End-to-end testing with Playwright
  - [ ] Visual regression testing
  - [ ] Accessibility testing automation
  
- [ ] **Performance Optimization**
  - [ ] Memory usage profiling and optimization
  - [ ] Database query performance analysis
  - [ ] API response time optimization (< 100ms)
  - [ ] Resource usage monitoring and alerting

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 🔧 Docker Build Issues
```bash
# Problem: Docker build fails with permission errors
# Solution: Clean Docker cache and rebuild
docker system prune -a -f
docker-compose build --no-cache

# Problem: Port 8000 already in use
# Solution: Stop conflicting services or change port
sudo lsof -ti:8000 | xargs kill -9
# Or modify docker-compose.yml to use different port
```

#### 🔧 Database Issues
```bash
# Problem: Database connection errors
# Solution: Check container logs and reset database
docker-compose logs api
rm -rf data/users.db
docker-compose restart api

# Problem: Database locked errors
# Solution: Stop all connections and restart
docker-compose down
docker-compose up -d
```

#### 🔧 Test Failures
```bash
# Problem: Tests failing due to timing issues
# Solution: Increase wait times in build script
# Edit build_and_test.sh and increase max_attempts

# Problem: Specific test failing
# Solution: Run individual test with verbose output
docker-compose exec api python -m pytest tests/test_server_api.py::test_create_user_success -v -s

# Problem: Test database issues
# Solution: Reset test environment
docker-compose down -v
docker-compose up -d
```

#### 🔧 Network Connectivity Issues
```bash
# Problem: Cannot connect to API
# Solution: Check if containers are running and healthy
docker-compose ps
docker-compose exec api curl http://localhost:8000/health

# Problem: DNS resolution issues
# Solution: Use IP address instead of hostname
curl http://127.0.0.1:8000/health
```

#### 🔧 Performance Issues
```bash
# Problem: Slow API responses
# Solution: Check resource usage and optimize
docker stats
docker-compose exec api top

# Problem: High memory usage
# Solution: Monitor and restart if needed
docker-compose restart api
```

### 📞 Getting Help

1. **Check the logs first:**
   ```bash
   # Application logs
   docker-compose logs -f api
   
   # Build script logs
   cat logs/build_test.log
   
   # Test results
   cat logs/test_results.json
   ```

2. **Verify system requirements:**
   ```bash
   docker --version        # Should be 20.10+
   docker-compose --version # Should be 1.29+
   curl --version          # For API testing
   ```

3. **Run health checks:**
   ```bash
   # API health
   curl http://localhost:8000/health
   
   # Container health
   docker-compose ps
   ```

4. **Reset everything:**
   ```bash
   ./build_and_test.sh --cleanup-only
   ./build_and_test.sh
   ```

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd rest-api-exam

# Install development dependencies
pip install -r requirements-test.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v
```

### Code Standards
- **Python**: Follow PEP 8 style guide
- **Type Hints**: Required for all functions
- **Documentation**: Docstrings for all modules, classes, and functions
- **Testing**: Minimum 80% code coverage
- **Security**: No hardcoded secrets or credentials

### Pull Request Process
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality (TDD approach)
4. Ensure all tests pass (`./build_and_test.sh`)
5. Update documentation if needed
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request with detailed description

### Testing Guidelines
- Follow TDD methodology (Red-Green-Refactor)
- Write tests for both success and failure scenarios
- Use descriptive test names that explain the scenario
- Group related tests in classes
- Use appropriate pytest markers (@pytest.mark.unit, etc.)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Pytest** - Testing framework that makes it easy to write simple tests
- **Docker** - Platform for developing, shipping, and running applications
- **Pydantic** - Data validation and settings management using Python type annotations

---

**Built with ❤️ for automated testing infrastructure and TDD methodology**

*For questions, issues, or contributions, please create an issue in the repository.*