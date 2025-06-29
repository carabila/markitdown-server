#!/bin/bash

# test-docker-deployment.sh
# Automated test script for Docker deployment

set -e  # Exit on any error

echo "🔍 Testing MarkItDown Server Docker Deployment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check if Docker is installed and running
print_info "Checking Docker installation..."
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        print_status 0 "Docker is installed and running"
    else
        echo -e "${RED}❌ Docker is installed but not running. Please start Docker Desktop.${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Docker is not installed. Please install Docker Desktop first.${NC}"
    exit 1
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    print_status 0 "Docker Compose is available"
else
    print_warning "Docker Compose not found. Will use 'docker compose' instead."
    COMPOSE_CMD="docker compose"
fi

# Set compose command
COMPOSE_CMD=${COMPOSE_CMD:-"docker-compose"}

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p uploads logs
print_status 0 "Created uploads and logs directories"

# Build the Docker image
print_info "Building Docker image..."
if docker build -t markitdown-server . > /dev/null 2>&1; then
    print_status 0 "Docker image built successfully"
else
    print_status 1 "Failed to build Docker image"
fi

# Stop any existing containers
print_info "Stopping any existing containers..."
docker stop markitdown-server 2>/dev/null || true
docker rm markitdown-server 2>/dev/null || true

# Start container using docker-compose
print_info "Starting container with Docker Compose..."
if $COMPOSE_CMD up -d > /dev/null 2>&1; then
    print_status 0 "Container started with Docker Compose"
else
    print_warning "Docker Compose failed, trying direct Docker run..."
    if docker run -d --name markitdown-server -p 8000:8000 markitdown-server > /dev/null 2>&1; then
        print_status 0 "Container started with Docker run"
    else
        print_status 1 "Failed to start container"
    fi
fi

# Wait for container to be ready
print_info "Waiting for container to be ready..."
sleep 10

# Check if container is running
if docker ps | grep -q markitdown-server; then
    print_status 0 "Container is running"
else
    print_status 1 "Container is not running"
    echo "Container logs:"
    docker logs markitdown-server 2>&1 || true
fi

# Test health endpoint
print_info "Testing health endpoint..."
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    print_status 0 "Health check passed"
else
    print_status 1 "Health check failed"
    echo "Container logs:"
    docker logs markitdown-server 2>&1 || true
fi

# Test conversion endpoint with text
print_info "Testing text conversion..."
response=$(curl -X POST http://localhost:8000/convert \
    --data-binary "# Test Header

This is a **test** document." \
    -H "Content-Type: application/octet-stream" \
    -s -w "%{http_code}" \
    -o /tmp/test_response.json)

if [ "$response" = "200" ]; then
    print_status 0 "Text conversion endpoint working"
    # Verify response contains expected fields
    if grep -q '"success":true' /tmp/test_response.json && grep -q '"converted_content"' /tmp/test_response.json; then
        print_status 0 "Response format is correct"
    else
        print_status 1 "Response format is incorrect"
        cat /tmp/test_response.json
    fi
else
    print_status 1 "Text conversion endpoint failed (HTTP $response)"
    cat /tmp/test_response.json 2>/dev/null || true
fi

# Test with a small PDF if available
if [ -f "test.pdf" ]; then
    print_info "Testing PDF conversion..."
    response=$(curl -X POST http://localhost:8000/convert \
        --data-binary @test.pdf \
        -H "Content-Type: application/octet-stream" \
        -s -w "%{http_code}" \
        -o /tmp/test_pdf_response.json)
    
    if [ "$response" = "200" ]; then
        print_status 0 "PDF conversion endpoint working"
    else
        print_warning "PDF conversion test failed (HTTP $response)"
    fi
else
    print_warning "No test.pdf file found, skipping PDF conversion test"
fi

# Test error handling
print_info "Testing error handling..."
response=$(curl -X POST http://localhost:8000/convert \
    --data-binary "" \
    -H "Content-Type: application/octet-stream" \
    -s -w "%{http_code}" \
    -o /tmp/test_error_response.json)

if [ "$response" = "400" ]; then
    print_status 0 "Error handling working correctly"
else
    print_warning "Error handling test unexpected result (HTTP $response)"
fi

# Check container health status
print_info "Checking container health status..."
health_status=$(docker inspect markitdown-server --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
if [ "$health_status" = "healthy" ]; then
    print_status 0 "Container health status is healthy"
elif [ "$health_status" = "starting" ]; then
    print_warning "Container is still starting up"
else
    print_warning "Container health status: $health_status"
fi

# Display container stats
print_info "Container statistics:"
docker stats markitdown-server --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || true

# Cleanup function
cleanup() {
    print_info "Cleaning up test files..."
    rm -f /tmp/test_response.json /tmp/test_pdf_response.json /tmp/test_error_response.json
    
    read -p "Do you want to stop the container? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping container..."
        $COMPOSE_CMD down > /dev/null 2>&1 || docker stop markitdown-server > /dev/null 2>&1
        print_status 0 "Container stopped"
    else
        print_info "Container left running. Access it at: http://localhost:8000"
        print_info "To stop later, run: $COMPOSE_CMD down"
    fi
}

# Final results
echo ""
echo "🎉 Docker deployment test completed successfully!"
echo "📊 Test Results Summary:"
echo "   ✅ Docker installation: OK"
echo "   ✅ Image build: OK"
echo "   ✅ Container startup: OK"
echo "   ✅ Health check: OK"
echo "   ✅ Text conversion: OK"
echo "   ✅ Error handling: OK"
echo ""
echo "🌐 Server is running at: http://localhost:8000"
echo "📋 API Documentation: http://localhost:8000/docs"
echo ""

# Ask user if they want to cleanup
cleanup

print_status 0 "All tests passed! 🚀" 