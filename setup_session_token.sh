#!/bin/bash

# Helper script to set up AWS session token authentication
# Usage: source ./setup_session_token.sh

echo "AWS Session Token Setup"
echo "======================="
echo "This script will help you set up AWS session token authentication."
echo "You'll need your AWS Access Key ID, Secret Access Key, and Session Token."
echo ""

# Prompt for credentials
read -p "Enter AWS Access Key ID: " AWS_ACCESS_KEY_ID
read -s -p "Enter AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
echo ""
read -p "Enter AWS Session Token: " AWS_SESSION_TOKEN

# Prompt for account IDs
echo ""
echo "Now enter your AWS account IDs:"
read -p "Enter Sandbox Account ID: " AWS_SANDBOX_ACCOUNT_ID
read -p "Enter Non-Prod Account ID: " AWS_NONPROD_ACCOUNT_ID

# Export all variables
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
export AWS_SESSION_TOKEN
export AWS_SANDBOX_ACCOUNT_ID
export AWS_NONPROD_ACCOUNT_ID
export AWS_DEFAULT_REGION="us-east-1"

echo ""
echo "✓ AWS credentials configured successfully!"
echo "You can now run: ./run_cost_calculator.sh"