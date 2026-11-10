#!/usr/bin/env bash
set -e

# Change directory to project root
cd "$(dirname "$0")/.."

echo "======================================================="
echo "Building Portable MongoDB Dump GUI for Linux"
echo "======================================================="

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Clean previous builds
rm -rf dist/MongoDumpGUI build/

echo "Installing / verifying requirements..."
pip install -r requirements.txt

echo "Running PyInstaller..."
pyinstaller --noconfirm \
    --onefile \
    --windowed \
    --name "MongoDumpGUI" \
    --collect-all customtkinter \
    app.py

echo ""
echo "======================================================="
echo "BUILD SUCCESSFUL!"
echo "Linux standalone binary created at: dist/MongoDumpGUI"
echo "======================================================="
