# Docker Deployment Guide for MarkItDown Server

## 🐳 **Prerequisites**

### Install Docker
- **macOS**: Download and install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Windows**: Download and install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- **Linux**: Install Docker Engine following [official instructions](https://docs.docker.com/engine/install/)

### Verify Docker Installation
```bash
docker --version
docker-compose --version
```

## 🚀 **Quick Start with Docker**

### Option 1: Using Docker Compose (Recommended)
```bash
# Start the server in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down
```

### Option 2: Using Docker Run
```bash
# Build the image
docker build -t markitdown-server .

# Run the container
docker run -d \
  --name markitdown-server \
  -p 8000:8000 \
  --restart unless-stopped \
  markitdown-server

# View logs
docker logs -f markitdown-server

# Stop the container
docker stop markitdown-server
docker rm markitdown-server
```

## 📁 **File Upload Support**

To enable file uploads to the container:

### Create uploads directory
```bash
mkdir -p uploads
chmod 755 uploads
```

### Copy files to uploads directory
```bash
# Copy your test files
cp test.pdf uploads/

# Now the container can access files in /app/uploads/
```

### Test with uploaded file
```bash
curl -X POST http://localhost:8000/convert \
  --data-binary @uploads/test.pdf \
  -H "Content-Type: application/octet-stream"
```

## 🔧 **Configuration Options**

### Environment Variables
Create a `.env` file for custom configuration:

```bash
# .env file
PYTHONUNBUFFERED=1
MARKITDOWN_LOG_LEVEL=INFO
MARKITDOWN_MAX_FILE_SIZE=100MB
```

### Custom docker-compose with environment file
```yaml
version: '3.8'
services:
  markitdown-server:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads:ro
      - ./logs:/app/logs
```

## 🏥 **Health Monitoring**

### Check container health
```bash
# Check health status
docker ps

# View health check logs
docker inspect markitdown-server | grep Health -A 10

# Test health endpoint directly
curl http://localhost:8000/
```

### Health check responses
- ✅ **Healthy**: Returns `{"message": "MarkItDown Server is running", "status": "healthy"}`
- ❌ **Unhealthy**: Container will restart automatically

## 📊 **Performance Tuning**

### Resource Limits
```yaml
# docker-compose.yml
services:
  markitdown-server:
    build: .
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Multi-replica Deployment
```yaml
# docker-compose.yml
services:
  markitdown-server:
    build: .
    ports:
      - "8000-8002:8000"
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
```

## 🔍 **Troubleshooting**

### Common Issues

#### 1. Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000

# Use different port
docker run -p 8001:8000 markitdown-server
```

#### 2. Permission Denied
```bash
# Fix permissions
sudo chown -R $USER:$USER uploads logs
chmod -R 755 uploads logs
```

#### 3. Container Won't Start
```bash
# Check logs
docker logs markitdown-server

# Run interactively for debugging
docker run -it --entrypoint /bin/bash markitdown-server
```

#### 4. Memory Issues
```bash
# Check container stats
docker stats markitdown-server

# Increase memory limit
docker run -m 2g markitdown-server
```

### Debug Mode
```bash
# Run with debug output
docker run -e PYTHONUNBUFFERED=1 -e LOG_LEVEL=DEBUG markitdown-server
```

## 🚀 **Production Deployment**

### Using Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml markitdown

# Scale service
docker service scale markitdown_markitdown-server=3
```

### Using Kubernetes
```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: markitdown-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: markitdown-server
  template:
    metadata:
      labels:
        app: markitdown-server
    spec:
      containers:
      - name: markitdown-server
        image: markitdown-server:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: markitdown-service
spec:
  selector:
    app: markitdown-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 🔐 **Security Considerations**

### 1. Non-root User
The container runs as a non-root user (`appuser`) for security.

### 2. Read-only Volumes
```yaml
volumes:
  - ./uploads:/app/uploads:ro  # Read-only mount
```

### 3. Network Security
```yaml
networks:
  markitdown-network:
    driver: bridge
    internal: true  # No external access
```

### 4. Secrets Management
```bash
# Use Docker secrets for sensitive data
echo "my-secret-key" | docker secret create markitdown-key -
```

## 📈 **Monitoring & Logging**

### Centralized Logging
```yaml
# docker-compose.yml
services:
  markitdown-server:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Prometheus Metrics (Optional)
Add metrics endpoint to your FastAPI application and expose on port 9090.

## 🎯 **Testing the Deployment**

### Automated Testing Script
```bash
#!/bin/bash
# test-docker-deployment.sh

echo "🔍 Testing Docker deployment..."

# Check if container is running
if docker ps | grep -q markitdown-server; then
    echo "✅ Container is running"
else
    echo "❌ Container is not running"
    exit 1
fi

# Test health endpoint
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Test conversion endpoint
if curl -X POST http://localhost:8000/convert \
    --data-binary "# Test" \
    -H "Content-Type: application/octet-stream" \
    -o /dev/null -s -w "%{http_code}" | grep -q "200"; then
    echo "✅ Conversion endpoint working"
else
    echo "❌ Conversion endpoint failed"
    exit 1
fi

echo "🎉 All tests passed! Docker deployment is working correctly."
```

Run the test:
```bash
chmod +x test-docker-deployment.sh
./test-docker-deployment.sh
``` 