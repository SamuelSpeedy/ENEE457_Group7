#!/bin/bash
#
# Malware Scanner - Setup Script
# Run this ONCE to install all dependencies
#

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "  MALWARE SCANNER - SETUP"
echo "=================================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION found"

# Check if venv already exists
if [ -d "venv" ]; then
    echo "✓ Virtual environment already exists"
    echo ""
    read -p "Reinstall dependencies? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup complete. Run ./run.sh to start the app."
        exit 0
    fi
    rm -rf venv
fi

echo ""
echo "[1/3] Creating virtual environment..."
python3 -m venv venv

echo "[2/3] Installing dependencies (this may take 2-3 minutes)..."
./venv/bin/pip install --upgrade pip -q

# Install oscrypto fix for OpenSSL 3.x first
./venv/bin/pip install -q git+https://github.com/wbond/oscrypto.git

# Install all other dependencies
./venv/bin/pip install -q \
    fastapi uvicorn python-multipart \
    xgboost scikit-learn joblib numpy \
    signify==0.7.1 \
    git+https://github.com/FutureComputing4AI/EMBER2024.git

echo "[3/3] Verifying installation..."

# Quick verification
./venv/bin/python -c "import thrember; import xgboost; import fastapi; print('✓ All dependencies OK')"

echo ""
echo "=================================================="
echo "  SETUP COMPLETE!"
echo "=================================================="
echo ""
echo "  Run ./run.sh to start the Malware Scanner"
echo ""
