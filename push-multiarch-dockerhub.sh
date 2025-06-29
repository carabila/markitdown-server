#!/bin/bash

# push-multiarch-dockerhub.sh
# Script to build and push multi-architecture markitdown-server to Docker Hub

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏗️  Multi-Architecture Docker Hub Push Script${NC}"
echo "=================================================="

# Get Docker Hub username
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <docker-hub-username> [tag] [platforms]${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 myusername                                    # Build for linux/amd64,linux/arm64"
    echo "  $0 myusername v1.0.0                             # With custom tag"
    echo "  $0 myusername latest linux/amd64                 # AMD64 only"
    echo "  $0 myusername latest linux/arm64                 # ARM64 only"
    echo "  $0 myusername latest linux/amd64,linux/arm64     # Both platforms"
    echo ""
    echo "Available platforms: linux/amd64, linux/arm64, linux/arm/v7"
    exit 1
fi

DOCKER_USERNAME="$1"
IMAGE_TAG="${2:-latest}"
PLATFORMS="${3:-linux/amd64,linux/arm64}"
IMAGE_NAME="$DOCKER_USERNAME/markitdown-server"
FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"

echo -e "${YELLOW}Docker Hub Username:${NC} $DOCKER_USERNAME"
echo -e "${YELLOW}Image Tag:${NC} $IMAGE_TAG"
echo -e "${YELLOW}Target Platforms:${NC} $PLATFORMS"
echo -e "${YELLOW}Full Image Name:${NC} $FULL_IMAGE_NAME"
echo ""

# Check if logged into Docker Hub
if ! docker info | grep -q "Username:"; then
    echo -e "${YELLOW}⚠️  Not logged into Docker Hub. Please login first:${NC}"
    echo "docker login"
    echo ""
    read -p "Press Enter after logging in, or Ctrl+C to cancel..."
fi

# Create or use existing buildx builder
BUILDER_NAME="markitdown-builder"
echo -e "${YELLOW}🔧 Setting up buildx builder...${NC}"

if ! docker buildx inspect $BUILDER_NAME >/dev/null 2>&1; then
    echo "Creating new buildx builder: $BUILDER_NAME"
    docker buildx create --name $BUILDER_NAME --driver docker-container --bootstrap
else
    echo "Using existing buildx builder: $BUILDER_NAME"
fi

# Use the builder
docker buildx use $BUILDER_NAME

# Build and push multi-architecture image
echo -e "${YELLOW}🏗️  Building and pushing multi-architecture image...${NC}"
echo "This may take several minutes as it builds for multiple platforms..."
echo ""

if docker buildx build \
    --platform $PLATFORMS \
    --tag $FULL_IMAGE_NAME \
    --push \
    --progress=plain \
    .; then
    
    echo -e "${GREEN}✅ Successfully built and pushed multi-architecture image!${NC}"
    echo ""
    echo -e "${GREEN}🎉 Your image is now available at:${NC}"
    echo "   https://hub.docker.com/r/$IMAGE_NAME"
    echo ""
    echo -e "${GREEN}📋 Platform-specific pull commands:${NC}"
    echo "   # Any platform (Docker will choose the right one automatically)"
    echo "   docker pull $FULL_IMAGE_NAME"
    echo ""
    echo "   # Specific AMD64 (Intel/AMD processors)"
    echo "   docker pull --platform linux/amd64 $FULL_IMAGE_NAME"
    echo ""
    echo "   # Specific ARM64 (Apple Silicon, Raspberry Pi 4+)"
    echo "   docker pull --platform linux/arm64 $FULL_IMAGE_NAME"
    echo ""
else
    echo -e "${RED}❌ Failed to build and push multi-architecture image${NC}"
    exit 1
fi

# Also tag as latest if not already
if [ "$IMAGE_TAG" != "latest" ]; then
    echo ""
    echo -e "${YELLOW}🏷️  Also building and pushing as 'latest'...${NC}"
    LATEST_IMAGE="$IMAGE_NAME:latest"
    if docker buildx build \
        --platform $PLATFORMS \
        --tag $LATEST_IMAGE \
        --push \
        .; then
        echo -e "${GREEN}✅ Also pushed as: $LATEST_IMAGE${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: Failed to push 'latest' tag${NC}"
    fi
fi

# Display image information
echo ""
echo -e "${YELLOW}📊 Image Information:${NC}"
echo "Image: $FULL_IMAGE_NAME"
echo "Platforms: $PLATFORMS"
echo "Size: Multi-platform manifest (varies by platform)"

echo ""
echo -e "${GREEN}🚀 Deployment commands for different architectures:${NC}"
echo ""
echo "# AMD64 (Intel/AMD processors - most cloud providers)"
echo "docker run -d -p 8000:8000 --platform linux/amd64 --name markitdown-server $FULL_IMAGE_NAME"
echo ""
echo "# ARM64 (Apple Silicon, Raspberry Pi 4+)"
echo "docker run -d -p 8000:8000 --platform linux/arm64 --name markitdown-server $FULL_IMAGE_NAME"
echo ""
echo "# Auto-detect (recommended - Docker chooses the right platform)"
echo "docker run -d -p 8000:8000 --name markitdown-server $FULL_IMAGE_NAME"

echo ""
echo -e "${GREEN}🔍 Verify multi-architecture build:${NC}"
echo "docker buildx imagetools inspect $FULL_IMAGE_NAME"

echo ""
echo -e "${GREEN}✨ Multi-architecture build complete! Your image works on:${NC}"
echo "   ✅ Intel/AMD processors (linux/amd64)"
echo "   ✅ Apple Silicon (linux/arm64)"
echo "   ✅ Raspberry Pi 4+ (linux/arm64)"
echo "   ✅ Cloud platforms (AWS, Google Cloud, Azure)"
echo ""
echo -e "${GREEN}🌍 Your MarkItDown Server is now universally compatible!${NC}" 