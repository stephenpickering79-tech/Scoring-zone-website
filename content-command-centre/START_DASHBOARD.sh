#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# ScoringZone Content Command Centre — Startup Script
# ─────────────────────────────────────────────────────────────────────────────
# Run this from the content-command-centre/ folder:
#   chmod +x START_DASHBOARD.sh
#   ./START_DASHBOARD.sh
#
# Then open: http://localhost:5050

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ⬤  SCORING ZONE — Content Command Centre"
echo "  ─────────────────────────────────────────"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  ✗ Python 3 not found. Install from https://python.org"
    exit 1
fi

# Install deps if needed
echo "  Checking dependencies..."
python3 -c "import flask" 2>/dev/null || pip3 install flask -q
python3 -c "import dotenv" 2>/dev/null || pip3 install python-dotenv -q
python3 -c "import PIL" 2>/dev/null    || pip3 install Pillow -q

echo "  ✓ Dependencies OK"
echo ""
echo "  Starting server on http://localhost:5050"
echo "  Press Ctrl+C to stop."
echo ""

python3 dashboard.py
