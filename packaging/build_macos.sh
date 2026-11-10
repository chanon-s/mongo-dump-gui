#!/usr/bin/env bash
set -e

# Change directory to project root
cd "$(dirname "$0")/.."

echo "======================================================="
echo "Building Portable MongoDB Dump GUI for macOS"
echo "======================================================="

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Clean previous builds
rm -rf dist/MongoDumpGUI dist/MongoDumpGUI.app build/

echo "Installing / verifying requirements..."
pip install -r requirements.txt

echo "Running PyInstaller..."
pyinstaller --noconfirm \
    --windowed \
    --name "MongoDumpGUI" \
    --collect-all customtkinter \
    app.py

echo ""
echo "======================================================="
echo "BUILD SUCCESSFUL!"
echo "macOS Application bundle created at: dist/MongoDumpGUI.app"
echo "======================================================="
