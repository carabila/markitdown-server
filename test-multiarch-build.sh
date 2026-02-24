#!/bin/bash

# test-multiarch-build.sh
# Test multi-architecture build capabilities without pushing to Docker Hub

set -e

echo "🧪 Testing Multi-Architecture Build Capabilities"
echo "=============================================="

# Check buildx availability
echo "🔍 Checking Docker buildx..."
if command -v docker &> /dev/null && docker buildx version &> /dev/null; then
    echo "✅ Docker buildx is available"
    docker buildx version
else
    echo "❌ Docker buildx is not available"
    exit 1
fi

echo ""
echo "🔍 Available builders and platforms:"
docker buildx ls

echo ""
echo "🏗️  Testing multi-platform build (dry run - no push)..."

# Create a test builder if needed
BUILDER_NAME="test-builder"
if ! docker buildx inspect $BUILDER_NAME >/dev/null 2>&1; then
    echo "Creating test builder..."
    docker buildx create --name $BUILDER_NAME --driver docker-container
fi

docker buildx use $BUILDER_NAME

# Test build for multiple platforms (but don't push)
echo "Building for linux/amd64,linux/arm64 (this may take a few minutes)..."

if docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag markitdown-server:multiarch-test \
    --progress=plain \
    .; then
    
    echo ""
    echo "✅ Multi-architecture build test SUCCESSFUL!"
    echo ""
    echo "📋 You can now build for:"
    echo "   ✅ linux/amd64 (Intel/AMD processors)"
    echo "   ✅ linux/arm64 (Apple Silicon, Raspberry Pi 4+)"
    echo ""
    echo "🚀 Ready to push to Docker Hub with:"
    echo "   ./scripts/push-docker-variants.sh --namespace yourusername"
    
else
    echo ""
    echo "❌ Multi-architecture build test FAILED"
    echo "Check the error messages above for troubleshooting."
    exit 1
fi

# Cleanup
echo ""
echo "🧹 Cleaning up test builder..."
docker buildx use default
docker buildx rm $BUILDER_NAME

echo ""
echo "✨ Multi-architecture build test completed successfully!" 
