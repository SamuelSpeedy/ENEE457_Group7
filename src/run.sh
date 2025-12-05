#!/bin/bash
#
# Malware Scanner - Run Script
# Just starts the app (run setup.sh first if needed)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found."
    echo "   Run ./setup.sh first to install dependencies."
    exit 1
fi

echo "=================================================="
echo "  MALWARE SCANNER - EMBER 2024"
echo "=================================================="
echo ""
echo "  Open browser to: http://localhost:8000"
echo "  Press Ctrl+C to stop"
echo ""
echo "=================================================="

./venv/bin/python standalone_app/app.py
