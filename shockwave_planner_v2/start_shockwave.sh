#!/bin/bash
#
# SHOCKWAVE PLANNER v2.0 - Startup Script
# Quick launcher for Linux/macOS systems
#

echo "========================================="
echo "  SHOCKWAVE PLANNER v2.0"
echo "  Launch Operations Planning System"
echo "========================================="
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "WARNING: Python version $PYTHON_VERSION detected"
    echo "Python 3.9+ recommended"
    echo ""
fi

# Check dependencies
echo "Checking dependencies..."

python3 -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "PyQt6 not found. Installing..."
    pip install PyQt6 --break-system-packages
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install PyQt6"
        exit 1
    fi
fi

python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "requests library not found. Installing..."
    pip install requests --break-system-packages
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install requests"
        exit 1
    fi
fi

echo "Dependencies OK"
echo ""

# Check database
if [ ! -f "shockwave_planner.db" ]; then
    echo "Database not found. Will create new database..."
fi

# Launch application
echo "Starting SHOCKWAVE PLANNER v2.0..."
echo ""

python3 main.py

# Exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Application exited with error code: $EXIT_CODE"
    echo "Check the output above for error messages"
fi

exit $EXIT_CODE
