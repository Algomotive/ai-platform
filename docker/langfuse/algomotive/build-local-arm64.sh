#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)"

SOURCE_ROOT="${LANGFUSE_SOURCE_ROOT:-/tmp/langfuse-algomotive-v4.38.0}"
IMAGE_TAG="${LANGFUSE_CUSTOM_IMAGE:-aiplatform/langfuse:4.38.0-local}"
PLATFORM="${LANGFUSE_BUILD_PLATFORM:-linux/arm64}"

if [ ! -f "$SOURCE_ROOT/web/Dockerfile" ]; then
  echo "Missing Langfuse web Dockerfile: $SOURCE_ROOT/web/Dockerfile" >&2
  exit 1
fi

if [ ! -f "$SOURCE_ROOT/ALGOMOTIVE-BRANDING-MANIFEST.txt" ]; then
  echo "Algomotive source patch has not been applied: $SOURCE_ROOT" >&2
  exit 1
fi

if ! grep -q 'Rebranded title: Algomotive Observability' \
  "$SOURCE_ROOT/ALGOMOTIVE-BRANDING-MANIFEST.txt"; then
  echo "Algomotive browser-title patch is missing from the manifest" >&2
  exit 1
fi

if ! grep -q 'Algomotive Observability' \
  "$SOURCE_ROOT/web/src/components/layouts/app-layout/hooks/useLayoutMetadata.ts"; then
  echo "Algomotive browser-title source patch is missing" >&2
  exit 1
fi

echo "SOURCE_ROOT=$SOURCE_ROOT"
echo "IMAGE_TAG=$IMAGE_TAG"
echo "PLATFORM=$PLATFORM"
echo "BUILD_SCOPE=LANGFUSE_WEB_ONLY"
echo "WORKER_IMAGE_UNCHANGED=YES"

docker build \
  --platform "$PLATFORM" \
  --file "$SOURCE_ROOT/web/Dockerfile" \
  --tag "$IMAGE_TAG" \
  "$SOURCE_ROOT"

docker image inspect "$IMAGE_TAG" \
  --format 'BUILT_IMAGE={{.RepoTags}}{{println}}IMAGE_ID={{.Id}}{{println}}ARCH={{.Architecture}}{{println}}OS={{.Os}}'

echo "ALGOMOTIVE_LANGFUSE_ARM64_IMAGE_BUILT"
