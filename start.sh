#!/bin/bash
# AWS AI Cost Calculator - Mac/Linux Quick Start

echo "🚀 Starting AWS AI Cost Calculator..."

# Check if setup has been run
if [ ! -d "venv" ]; then
    echo "📦 First time setup detected..."
    python3 setup_and_run.py
else
    # Activate virtual environment and run
    source venv/bin/activate
    cd web-interface
    python app.py
fi