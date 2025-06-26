#!/bin/bash

# AWS AI Cost Calculator Runner Script
# This script sets up the environment and runs the cost calculator

# Set AWS account IDs - replace with your actual account IDs
export AWS_SANDBOX_ACCOUNT_ID="YOUR_SANDBOX_ACCOUNT_ID"
export AWS_NONPROD_ACCOUNT_ID="YOUR_NONPROD_ACCOUNT_ID"

# AWS Authentication Options:
# Option 1: Use AWS Session Token (temporary credentials)
# Uncomment and fill in these if using session tokens:
# export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID"
# export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_ACCESS_KEY"
# export AWS_SESSION_TOKEN="YOUR_SESSION_TOKEN"

# Option 2: Use AWS CLI configured credentials (default)
# Make sure you've run 'aws configure' first

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