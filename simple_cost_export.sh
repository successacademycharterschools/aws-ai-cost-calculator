#!/bin/bash

# Simple AWS Cost Export Script
# This script uses AWS CLI to export cost data without complex API calls

echo "AWS AI Cost Export Script"
echo "========================"

# Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    exit 1
fi

# Set date range
START_DATE=$(date -v-1m +%Y-%m-01)  # First day of current month
END_DATE=$(date +%Y-%m-%d)          # Today

echo "Date range: $START_DATE to $END_DATE"
echo ""

# Export total costs by service
echo "Exporting total costs by service..."
aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --group-by Type=DIMENSION,Key=SERVICE \
    --output json > total_costs_by_service.json

# Export costs for specific services
echo "Exporting AI service costs..."

# Bedrock costs (100% AI)
aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --filter '{"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Bedrock"]}}' \
    --output json > bedrock_costs.json

# Lambda costs
aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --filter '{"Dimensions": {"Key": "SERVICE", "Values": ["AWS Lambda"]}}' \
    --output json > lambda_costs.json

# Kendra costs (100% AI)
aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --filter '{"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Kendra"]}}' \
    --output json > kendra_costs.json

# S3 costs
aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --filter '{"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Simple Storage Service"]}}' \
    --output json > s3_costs.json

# DynamoDB costs
aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --filter '{"Dimensions": {"Key": "SERVICE", "Values": ["Amazon DynamoDB"]}}' \
    --output json > dynamodb_costs.json

echo ""
echo "Cost data exported to JSON files:"
echo "- total_costs_by_service.json"
echo "- bedrock_costs.json (100% AI)"
echo "- lambda_costs.json"
echo "- kendra_costs.json (100% AI)"
echo "- s3_costs.json"
echo "- dynamodb_costs.json"
echo ""
echo "You can now process these files locally without API calls."