#!/bin/bash

# push-to-dockerhub.sh
# Script to tag and push markitdown-server to Docker Hub

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🐳 Docker Hub Push Script for MarkItDown Server${NC}"
echo "=================================================="

# Get Docker Hub username
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <docker-hub-username> [tag]${NC}"
    echo ""
    echo "Example:"
    echo "  $0 myusername"
    echo "  $0 myusername v1.0.0"
    echo ""
    echo "If no tag is provided, 'latest' will be used."
    exit 1
fi

DOCKER_USERNAME="$1"
IMAGE_TAG="${2:-latest}"
LOCAL_IMAGE="markitdown-server:latest"
REMOTE_IMAGE="$DOCKER_USERNAME/markitdown-server:$IMAGE_TAG"

echo -e "${YELLOW}Docker Hub Username:${NC} $DOCKER_USERNAME"
echo -e "${YELLOW}Local Image:${NC} $LOCAL_IMAGE"
echo -e "${YELLOW}Remote Image:${NC} $REMOTE_IMAGE"
echo ""

# Check if local image exists
if ! docker images | grep -q "markitdown-server.*latest"; then
    echo -e "${RED}❌ Local image 'markitdown-server:latest' not found!${NC}"
    echo "Please build the image first with: docker build -t markitdown-server ."
    exit 1
fi

# Check if logged into Docker Hub
if ! docker info | grep -q "Username:"; then
    echo -e "${YELLOW}⚠️  Not logged into Docker Hub. Please login first:${NC}"
    echo "docker login"
    echo ""
    read -p "Press Enter after logging in, or Ctrl+C to cancel..."
fi

# Tag the image
echo -e "${YELLOW}🏷️  Tagging image...${NC}"
if docker tag "$LOCAL_IMAGE" "$REMOTE_IMAGE"; then
    echo -e "${GREEN}✅ Successfully tagged: $REMOTE_IMAGE${NC}"
else
    echo -e "${RED}❌ Failed to tag image${NC}"
    exit 1
fi

# Push the image
echo -e "${YELLOW}📤 Pushing to Docker Hub...${NC}"
if docker push "$REMOTE_IMAGE"; then
    echo -e "${GREEN}✅ Successfully pushed to Docker Hub!${NC}"
    echo ""
    echo -e "${GREEN}🎉 Your image is now available at:${NC}"
    echo "   https://hub.docker.com/r/$DOCKER_USERNAME/markitdown-server"
    echo ""
    echo -e "${GREEN}📋 Others can pull your image with:${NC}"
    echo "   docker pull $REMOTE_IMAGE"
    echo "   docker run -d -p 8000:8000 $REMOTE_IMAGE"
else
    echo -e "${RED}❌ Failed to push image${NC}"
    exit 1
fi

# Also tag as latest if not already
if [ "$IMAGE_TAG" != "latest" ]; then
    echo ""
    echo -e "${YELLOW}🏷️  Also tagging as 'latest'...${NC}"
    LATEST_IMAGE="$DOCKER_USERNAME/markitdown-server:latest"
    if docker tag "$LOCAL_IMAGE" "$LATEST_IMAGE" && docker push "$LATEST_IMAGE"; then
        echo -e "${GREEN}✅ Also pushed as: $LATEST_IMAGE${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: Failed to push 'latest' tag${NC}"
    fi
fi

# Display image info
echo ""
echo -e "${YELLOW}📊 Image Information:${NC}"
docker images | grep "$DOCKER_USERNAME/markitdown-server" || echo "No local tagged images found"

echo ""
echo -e "${GREEN}🚀 Deployment commands for others:${NC}"
echo "# Quick start"
echo "docker run -d -p 8000:8000 --name markitdown-server $REMOTE_IMAGE"
echo ""
echo "# With docker-compose (create docker-compose.yml with your image)"
echo "# Replace 'build: .' with 'image: $REMOTE_IMAGE'"

echo ""
echo -e "${GREEN}✨ Done! Your MarkItDown Server is now on Docker Hub!${NC}" 