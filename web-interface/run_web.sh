#!/bin/bash

# AWS AI Cost Calculator Web Interface Startup Script

echo "=========================================="
echo "AWS AI Cost Calculator - Web Interface"
echo "Success Academies"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Check if SSO calculator is accessible
if [ ! -d "../aws-ai-cost-calculator-sso" ]; then
    echo "WARNING: SSO calculator not found in parent directory!"
    echo "Please ensure aws-ai-cost-calculator-sso is in the parent directory."
fi

# Start the web server
echo ""
echo "Starting web server..."
echo "=========================================="
echo "Access the calculator at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

python app.py