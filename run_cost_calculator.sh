#!/bin/bash

# AWS AI Cost Calculator Runner Script
# This script sets up the environment and runs the cost calculator

# Set AWS account IDs - replace with your actual account IDs
export AWS_SANDBOX_ACCOUNT_ID="YOUR_SANDBOX_ACCOUNT_ID"
export AWS_NONPROD_ACCOUNT_ID="YOUR_NONPROD_ACCOUNT_ID"

# Set AWS region (Cost Explorer requires us-east-1)
export AWS_DEFAULT_REGION="us-east-1"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run the cost calculator
echo "Running AWS AI Cost Calculator..."
python ai_cost_calculator.py

# Deactivate virtual environment
deactivate

echo "Cost calculation complete! Check ai_project_costs.csv for results."