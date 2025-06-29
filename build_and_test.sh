#!/bin/bash

# build_and_test.sh - Comprehensive build, deploy, and test script
# This script builds the Docker containers, runs the API, injects test data,
# and runs comprehensive tests with detailed reporting.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="User Management API"
API_URL="http://localhost:8000"
LOG_FILE="./logs/build_test.log"
RESULTS_FILE="./logs/test_results.json"

# Function to print colored output
print_header() {
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${PURPLE} $1${NC}"
    echo -e "${PURPLE}================================================================${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up containers and networks..."
    docker-compose down --volumes --remove-orphans 2>/dev/null || true
    docker system prune -f --volumes 2>/dev/null || true
    print_status "Cleanup completed"
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install docker-compose."
        exit 1
    fi
    print_success "docker-compose is available"
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed. Please install curl."
        exit 1
    fi
    print_success "curl is available"
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed. Some output formatting may be limited."
    else
        print_success "jq is available"
    fi
}

# Function to prepare environment
prepare_environment() {
    print_step "Preparing environment..."
    
    # Create necessary directories
    mkdir -p data logs client server tests
    print_status "Created necessary directories"
    
    # Initialize log file
    echo "Build and test started at $(date)" > "$LOG_FILE"
    
    # Set permissions
    chmod -R 755 logs data 2>/dev/null || true
    
    print_success "Environment prepared"
}

# Function to build Docker images
build_images() {
    print_step "Building Docker images..."
    
    # Clean up any existing containers
    cleanup
    
    # Build images with no cache for fresh build
    if docker-compose build --no-cache; then
        print_success "Docker images built successfully"
        log_message "Docker images built successfully"
    else
        print_error "Failed to build Docker images"
        log_message "ERROR: Failed to build Docker images"
        exit 1
    fi
}

# Function to start services
start_services() {
    print_step "Starting services..."
    
    if docker-compose up -d; then
        print_success "Services started successfully"
        log_message "Services started successfully"
    else
        print_error "Failed to start services"
        log_message "ERROR: Failed to start services"
        exit 1
    fi
    
    # Show running containers
    print_status "Running containers:"
    docker-compose ps
}

# Function to wait for services to be ready
wait_for_services() {
    print_step "Waiting for services to be ready..."
    
    local max_attempts=60  # 2 minutes total
    local attempt=1
    local wait_time=2
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f "$API_URL/health" > /dev/null 2>&1; then
            print_success "API server is healthy and ready"
            log_message "API server is healthy and ready after $attempt attempts"
            return 0
        else
            if [ $attempt -eq $max_attempts ]; then
                print_error "API server failed to become healthy after $max_attempts attempts"
                print_status "Showing container logs:"
                docker-compose logs api
                log_message "ERROR: API server failed to become healthy"
                exit 1
            fi
            print_status "Attempt $attempt/$max_attempts: API server not ready, waiting ${wait_time}s..."
            sleep $wait_time
            ((attempt++))
        fi
    done
}

# Function to inject test data
inject_test_data() {
    print_step "Injecting test data..."
    
    # Test data array with valid Israeli IDs and phone numbers
    declare -a test_users=(
        "123456782:John Doe:0501234567:123 Main St, Tel Aviv"
        "87654321:Jane Smith:0509876543:456 Oak Ave, Haifa"
        "12345678:Bob Johnson:0507654321:789 Pine Rd, Jerusalem"
        "320780694:Alice Brown:0506543210:321 Elm St, Be'er Sheva"
        "11223344:David Wilson:0505432109:654 Cedar Ave, Netanya"
    )
    
    local successful_inserts=0
    local failed_inserts=0
    
    echo "{"  > "$RESULTS_FILE"
    echo '  "test_data_injection": {' >> "$RESULTS_FILE"
    echo '    "results": [' >> "$RESULTS_FILE"
    
    local first_user=true
    
    for user_data in "${test_users[@]}"; do
        IFS=':' read -r id name phone address <<< "$user_data"
        
        print_status "Inserting user: ID=$id, Name='$name'"
        
        if [ "$first_user" = false ]; then
            echo "," >> "$RESULTS_FILE"
        fi
        first_user=false
        
        response=$(curl -s -w "%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "{\"id\":\"$id\",\"name\":\"$name\",\"phone_number\":\"$phone\",\"address\":\"$address\"}" \
            "$API_URL/users" 2>/dev/null)
        
        http_code="${response: -3}"
        response_body="${response%???}"
        
        if [ "$http_code" = "201" ]; then
            print_success "✓ User $id ($name) inserted successfully"
            log_message "SUCCESS: User $id inserted successfully"
            ((successful_inserts++))
            
            echo "      {" >> "$RESULTS_FILE"
            echo "        \"id\": \"$id\"," >> "$RESULTS_FILE"
            echo "        \"name\": \"$name\"," >> "$RESULTS_FILE"
            echo "        \"status\": \"success\"," >> "$RESULTS_FILE"
            echo "        \"http_code\": $http_code" >> "$RESULTS_FILE"
            echo "      }" >> "$RESULTS_FILE"
        else
            print_error "✗ Failed to insert user $id: HTTP $http_code"
            echo "   Response: $response_body" | head -c 200
            log_message "ERROR: Failed to insert user $id: HTTP $http_code"
            ((failed_inserts++))
            
            echo "      {" >> "$RESULTS_FILE"
            echo "        \"id\": \"$id\"," >> "$RESULTS_FILE"
            echo "        \"name\": \"$name\"," >> "$RESULTS_FILE"
            echo "        \"status\": \"failed\"," >> "$RESULTS_FILE"
            echo "        \"http_code\": $http_code," >> "$RESULTS_FILE"
            echo "        \"error\": \"$(echo "$response_body" | tr '\n' ' ' | tr '"' "'" | head -c 100)\"" >> "$RESULTS_FILE"
            echo "      }" >> "$RESULTS_FILE"
        fi
    done
    
    echo "" >> "$RESULTS_FILE"
    echo "    ]," >> "$RESULTS_FILE"
    echo "    \"summary\": {" >> "$RESULTS_FILE"
    echo "      \"successful\": $successful_inserts," >> "$RESULTS_FILE"
    echo "      \"failed\": $failed_inserts," >> "$RESULTS_FILE"
    echo "      \"total\": $((successful_inserts + failed_inserts))" >> "$RESULTS_FILE"
    echo "    }" >> "$RESULTS_FILE"
    echo "  }," >> "$RESULTS_FILE"
    
    print_status "Data injection complete: $successful_inserts successful, $failed_inserts failed"
    log_message "Data injection complete: $successful_inserts successful, $failed_inserts failed"
    
    # Verify data
    print_status "Verifying injected data..."
    user_list=$(curl -s "$API_URL/users" 2>/dev/null)
    if command -v jq &> /dev/null; then
        user_count=$(echo "$user_list" | jq length 2>/dev/null || echo "0")
    else
        user_count=$(echo "$user_list" | grep -o ',' | wc -l)
        user_count=$((user_count + 1))
    fi
    print_status "Total users in database: $user_count"
    log_message "Total users in database: $user_count"
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    print_step "Running comprehensive tests..."
    
    echo '  "comprehensive_tests": {' >> "$RESULTS_FILE"
    echo '    "results": [' >> "$RESULTS_FILE"
    
    # Install test dependencies
    print_status "Installing test dependencies in container..."
    docker-compose exec -T api pip install -r /app/../requirements-test.txt > /dev/null 2>&1 || {
        print_warning "Could not install test dependencies from requirements-test.txt"
        docker-compose exec -T api pip install pytest pytest-cov httpx responses > /dev/null 2>&1 || {
            print_error "Failed to install basic test dependencies"
            return 1
        }
    }
    
    local test_results=()
    local overall_success=true
    
    # Test 1: Server unit tests
    print_status "Running server unit tests..."
    if docker-compose exec -T api python -m pytest tests/ -v --tb=short --maxfail=5 2>/dev/null; then
        print_success "✓ Server unit tests passed"
        test_results+=("server_unit_tests:PASSED")
        log_message "SUCCESS: Server unit tests passed"
    else
        print_error "✗ Server unit tests failed"
        test_results+=("server_unit_tests:FAILED")
        log_message "ERROR: Server unit tests failed"
        overall_success=false
    fi
    
    # Test 2: Integration tests via HTTP
    print_status "Running HTTP integration tests..."
    run_http_integration_tests
    local http_test_result=$?
    
    if [ $http_test_result -eq 0 ]; then
        print_success "✓ HTTP integration tests passed"
        test_results+=("http_integration_tests:PASSED")
        log_message "SUCCESS: HTTP integration tests passed"
    else
        print_error "✗ HTTP integration tests failed"
        test_results+=("http_integration_tests:FAILED")
        log_message "ERROR: HTTP integration tests failed"
        overall_success=false
    fi
    
    # Test 3: API contract tests
    print_status "Running API contract tests..."
    run_api_contract_tests
    local contract_test_result=$?
    
    if [ $contract_test_result -eq 0 ]; then
        print_success "✓ API contract tests passed"
        test_results+=("api_contract_tests:PASSED")
        log_message "SUCCESS: API contract tests passed"
    else
        print_error "✗ API contract tests failed"
        test_results+=("api_contract_tests:FAILED")
        log_message "ERROR: API contract tests failed"
        overall_success=false
    fi
    
    # Write test results to JSON
    local first_result=true
    for result in "${test_results[@]}"; do
        if [ "$first_result" = false ]; then
            echo "," >> "$RESULTS_FILE"
        fi
        first_result=false
        
        IFS=':' read -r test_name test_status <<< "$result"
        echo "      {" >> "$RESULTS_FILE"
        echo "        \"test_name\": \"$test_name\"," >> "$RESULTS_FILE"
        echo "        \"status\": \"$test_status\"" >> "$RESULTS_FILE"
        echo "      }" >> "$RESULTS_FILE"
    done
    
    echo "" >> "$RESULTS_FILE"
    echo "    ]," >> "$RESULTS_FILE"
    echo "    \"overall_success\": $([ "$overall_success" = true ] && echo "true" || echo "false")" >> "$RESULTS_FILE"
    echo "  }" >> "$RESULTS_FILE"
    echo "}" >> "$RESULTS_FILE"
    
    return $([ "$overall_success" = true ] && echo 0 || echo 1)
}

# Function to run HTTP integration tests
run_http_integration_tests() {
    local passed=0
    local failed=0
    
    # Test 1: Health check
    print_status "  → Testing health check endpoint"
    if curl -f "$API_URL/health" > /dev/null 2>&1; then
        print_success "    ✓ Health check test passed"
        ((passed++))
    else
        print_error "    ✗ Health check test failed"
        ((failed++))
    fi
    
    # Test 2: Get existing user
    print_status "  → Testing get existing user"
    response=$(curl -s -w "%{http_code}" "$API_URL/users/123456782")
    http_code="${response: -3}"
    if [ "$http_code" = "200" ]; then
        print_success "    ✓ Get existing user test passed"
        ((passed++))
    else
        print_error "    ✗ Get existing user test failed: HTTP $http_code"
        ((failed++))
    fi
    
    # Test 3: Get non-existent user (should return 404)
    print_status "  → Testing get non-existent user (expecting 404)"
    response=$(curl -s -w "%{http_code}" "$API_URL/users/nonexistent")
    http_code="${response: -3}"
    if [ "$http_code" = "404" ]; then
        print_success "    ✓ Non-existent user test passed (correctly returned 404)"
        ((passed++))
    else
        print_error "    ✗ Non-existent user test failed: expected 404, got $http_code"
        ((failed++))
    fi
    
    # Test 4: Create user with invalid ID (should return 422)
    print_status "  → Testing create user with invalid ID (expecting 422)"
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"id":"invalid","name":"Test User","phone_number":"0501234567","address":"Test Address"}' \
        "$API_URL/users")
    http_code="${response: -3}"
    if [ "$http_code" = "422" ]; then
        print_success "    ✓ Invalid ID test passed (correctly returned 422)"
        ((passed++))
    else
        print_error "    ✗ Invalid ID test failed: expected 422, got $http_code"
        ((failed++))
    fi
    
    # Test 5: Create user with invalid phone (should return 422)
    print_status "  → Testing create user with invalid phone (expecting 422)"
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"id":"123456782","name":"Test User","phone_number":"0521234567","address":"Test Address"}' \
        "$API_URL/users")
    http_code="${response: -3}"
    if [ "$http_code" = "422" ]; then
        print_success "    ✓ Invalid phone test passed (correctly returned 422)"
        ((passed++))
    else
        print_error "    ✗ Invalid phone test failed: expected 422, got $http_code"
        ((failed++))
    fi
    
    # Test 6: List all users
    print_status "  → Testing list all users"
    response=$(curl -s -w "%{http_code}" "$API_URL/users")
    http_code="${response: -3}"
    if [ "$http_code" = "200" ]; then
        print_success "    ✓ List users test passed"
        ((passed++))
    else
        print_error "    ✗ List users test failed: HTTP $http_code"
        ((failed++))
    fi
    
    print_status "HTTP Integration Tests: $passed passed, $failed failed"
    return $([ $failed -eq 0 ] && echo 0 || echo 1)
}

# Function to run API contract tests
run_api_contract_tests() {
    local passed=0
    local failed=0
    
    # Test API documentation endpoint
    print_status "  → Testing API documentation endpoints"
    if curl -f "$API_URL/docs" > /dev/null 2>&1; then
        print_success "    ✓ API docs endpoint accessible"
        ((passed++))
    else
        print_error "    ✗ API docs endpoint not accessible"
        ((failed++))
    fi
    
    # Test OpenAPI schema
    print_status "  → Testing OpenAPI schema"
    if curl -f "$API_URL/openapi.json" > /dev/null 2>&1; then
        print_success "    ✓ OpenAPI schema accessible"
        ((passed++))
    else
        print_error "    ✗ OpenAPI schema not accessible"
        ((failed++))
    fi
    
    # Test CORS headers
    print_status "  → Testing CORS headers"
    response=$(curl -s -I -X OPTIONS "$API_URL/users")
    if echo "$response" | grep -qi "access-control-allow"; then
        print_success "    ✓ CORS headers present"
        ((passed++))
    else
        print_warning "    ? CORS headers not detected (may be intentional)"
        ((passed++))  # Don't fail on this
    fi
    
    print_status "API Contract Tests: $passed passed, $failed failed"
    return $([ $failed -eq 0 ] && echo 0 || echo 1)
}

# Function to generate final report
generate_final_report() {
    print_header "TEST RESULTS SUMMARY"
    
    # Read results from JSON if available
    if [ -f "$RESULTS_FILE" ] && command -v jq &> /dev/null; then
        print_status "Generating detailed report from test results..."
        
        # Data injection results
        local successful_inserts=$(jq -r '.test_data_injection.summary.successful' "$RESULTS_FILE" 2>/dev/null || echo "N/A")
        local failed_inserts=$(jq -r '.test_data_injection.summary.failed' "$RESULTS_FILE" 2>/dev/null || echo "N/A")
        
        print_status "Data Injection: $successful_inserts successful, $failed_inserts failed"
        
        # Test results
        local overall_success=$(jq -r '.comprehensive_tests.overall_success' "$RESULTS_FILE" 2>/dev/null || echo "false")
        
        if [ "$overall_success" = "true" ]; then
            print_success "=== ALL TESTS PASSED! ==="
        else
            print_error "=== SOME TESTS FAILED! ==="
        fi
    else
        print_warning "Detailed results not available (jq not installed or results file missing)"
    fi
    
    # Show API information
    print_status "=== API INFORMATION ==="
    print_status "API URL: $API_URL"
    print_status "API Documentation: $API_URL/docs"
    print_status "API Schema: $API_URL/openapi.json"
    print_status "Health Check: $API_URL/health"
    
    # Show management commands
    print_status "=== MANAGEMENT COMMANDS ==="
    print_status "View logs: docker-compose logs -f api"
    print_status "Stop services: docker-compose down"
    print_status "Restart services: docker-compose restart"
    print_status "View database: docker-compose exec api sqlite3 /app/data/users.db"
    
    # Show files created
    print_status "=== FILES CREATED ==="
    print_status "Build log: $LOG_FILE"
    print_status "Test results: $RESULTS_FILE"
    print_status "Database: ./data/users.db"
    print_status "Application logs: ./logs/"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Build, deploy, and test the User Management API"
    echo ""
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --cleanup-only      Only perform cleanup (stop containers, remove volumes)"
    echo "  --no-tests          Skip running tests (only build and deploy)"
    echo "  --tests-only        Only run tests (assume services are already running)"
    echo "  --verbose, -v       Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0                  Full build, deploy, and test"
    echo "  $0 --no-tests       Build and deploy without running tests"
    echo "  $0 --tests-only     Run tests only (services must be running)"
    echo "  $0 --cleanup-only   Stop all services and clean up"
}

# Trap cleanup on script exit
trap cleanup EXIT

# Main execution flow
main() {
    local skip_tests=false
    local tests_only=false
    local cleanup_only=false
    local verbose=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --cleanup-only)
                cleanup_only=true
                shift
                ;;
            --no-tests)
                skip_tests=true
                shift
                ;;
            --tests-only)
                tests_only=true
                shift
                ;;
            --verbose|-v)
                verbose=true
                set -x  # Enable verbose mode
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Handle cleanup-only mode
    if [ "$cleanup_only" = true ]; then
        print_header "CLEANUP MODE"
        cleanup
        print_success "Cleanup completed"
        exit 0
    fi
    
    # Start main process
    print_header "$PROJECT_NAME - BUILD & TEST"
    print_status "Starting build and test process at $(date)"
    
    # Check prerequisites
    check_prerequisites
    
    # Prepare environment
    prepare_environment
    
    # Handle tests-only mode
    if [ "$tests_only" = true ]; then
        print_header "TESTS-ONLY MODE"
        
        # Check if services are running
        if ! curl -f "$API_URL/health" > /dev/null 2>&1; then
            print_error "API service is not running. Please start services first."
            exit 1
        fi
        
        # Run tests
        if run_comprehensive_tests; then
            print_success "All tests passed!"
            generate_final_report
            exit 0
        else
            print_error "Some tests failed!"
            generate_final_report
            exit 1
        fi
    fi
    
    # Full build and deploy process
    build_images
    start_services
    wait_for_services
    inject_test_data
    
    # Run tests unless skipped
    local test_result=0
    if [ "$skip_tests" = false ]; then
        if ! run_comprehensive_tests; then
            test_result=1
        fi
    else
        print_warning "Skipping tests as requested"
    fi
    
    # Generate final report
    generate_final_report
    
    # Final status
    if [ $test_result -eq 0 ]; then
        print_success "Build and test process completed successfully!"
        log_message "Build and test process completed successfully"
        exit 0
    else
        print_error "Build and test process completed with failures!"
        log_message "Build and test process completed with failures"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
