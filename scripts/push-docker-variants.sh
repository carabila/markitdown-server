#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="carabila"
IMAGE="markitdown-server"
BUILDER="${BUILDER:-}"
CPU_MULTIARCH_PLATFORMS="linux/amd64,linux/arm64"

usage() {
  cat <<'EOF'
Push MarkItDown Server container variants to Docker Hub using an existing buildx builder.

Usage:
  scripts/push-docker-variants.sh [options]

Options:
  --namespace <name>   Docker Hub namespace/user (default: carabila)
  --image <name>       Image name (default: markitdown-server)
  --builder <name>     Existing buildx builder to use (default: active builder)
  -h, --help           Show this help

Published tags:
  <namespace>/<image>:latest         (CPU multi-arch: amd64, arm64)
  <namespace>/<image>:cpu            (CPU multi-arch: amd64, arm64)
  <namespace>/<image>:cpu-amd64      (CPU amd64)
  <namespace>/<image>:cpu-arm64      (CPU arm64)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    --image)
      IMAGE="$2"
      shift 2
      ;;
    --builder)
      BUILDER="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$BUILDER" ]]; then
  BUILDER="$(docker buildx ls | awk '$1 ~ /\*/ { gsub(/\*/, "", $1); print $1; exit }')"
fi

if [[ -z "$BUILDER" ]]; then
  echo "No active buildx builder found. Pass one with --builder." >&2
  exit 1
fi

IMAGE_BASE="${NAMESPACE}/${IMAGE}"

echo "Using builder: ${BUILDER}"
echo "Target image: ${IMAGE_BASE}"

echo "Pushing CPU multi-arch (latest, cpu)..."
docker buildx build \
  --builder "${BUILDER}" \
  --platform "${CPU_MULTIARCH_PLATFORMS}" \
  -t "${IMAGE_BASE}:latest" \
  -t "${IMAGE_BASE}:cpu" \
  --push .

echo "Pushing CPU amd64..."
docker buildx build \
  --builder "${BUILDER}" \
  --platform linux/amd64 \
  -t "${IMAGE_BASE}:cpu-amd64" \
  --push .

echo "Pushing CPU arm64..."
docker buildx build \
  --builder "${BUILDER}" \
  --platform linux/arm64 \
  -t "${IMAGE_BASE}:cpu-arm64" \
  --push .

echo "Done."
