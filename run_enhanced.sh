#!/bin/bash
# Enhanced AWS AI Cost Calculator Startup Script
# This ensures the virtual environment is properly activated

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🚀 Starting Enhanced AWS AI Cost Calculator..."

# Change to the project directory
cd "$DIR"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Verify we're using the venv Python
echo "🐍 Using Python: $(which python)"
echo "🐍 Python version: $(python --version)"

# Change to web-interface directory
cd web-interface

# Start the Flask app
echo "✨ Starting Flask application..."
echo "📊 Open your browser to: http://localhost:5001"
echo "Press Ctrl+C to stop the server"
echo ""

# Run the app
python app.py