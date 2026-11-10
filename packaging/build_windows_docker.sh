#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "======================================================="
echo "Building Windows .exe from macOS via Docker"
echo "======================================================="

# Check if docker daemon is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker daemon is not running."
    echo "Please start Docker Desktop on your Mac first, then re-run this script."
    exit 1
fi

echo "Building Docker build-environment image..."
docker build -t mongodump-gui-winbuilder -f packaging/Dockerfile.windows .

echo "Compiling MongoDumpGUI.exe inside container..."
docker run --rm -v "$(pwd):/src" mongodump-gui-winbuilder

echo ""
echo "======================================================="
echo "SUCCESS: Windows executable built at dist/MongoDumpGUI.exe"
echo "======================================================="
