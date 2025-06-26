#!/usr/bin/env python3
"""
Process exported AWS cost JSON files to calculate AI project costs
This works offline without making any API calls
"""

import json
import csv
from decimal import Decimal
from datetime import datetime
import os

# AI Project Configuration
AI_PROJECTS = {
    "ask_eva": {
        "name": "Ask Eva",
        "status": "POC",
        "lambda_functions": [
            "sa-ai-ask-eva-Lamda",
            "sa-ai-ask-eva-list-conv-history"
        ],
        "s3_buckets": [
            "sa-ai-ask-eva",
            "sa-ai-ask-eva-frontend"
        ],
        "dynamodb_tables": [
            "sa_ai_ask_eva_conversation_history"
        ]
    },
    "resume_knockout": {
        "name": "Resume Knockout",
        "status": "paused",
        "lambda_functions": ["Resume-Knockout-batch"]
    },
    "iep_report": {
        "name": "IEP Report",
        "status": "MVP",
        "lambda_functions": []  # Add when known
    },
    "financial_aid": {
        "name": "Financial Aid",
        "status": "MVP",
        "lambda_functions": []  # Add when known
    }
}

def load_json_file(filename):
    """Load JSON cost data from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found")
        return None

def extract_cost_amount(cost_data):
    """Extract cost amount from AWS Cost Explorer response"""
    if not cost_data or 'ResultsByTime' not in cost_data:
        return Decimal('0')
    
    total = Decimal('0')
    for result in cost_data['ResultsByTime']:
        amount = result.get('Total', {}).get('UnblendedCost', {}).get('Amount', '0')
        total += Decimal(amount)
    
    return total

def calculate_ai_costs():
    """Calculate AI costs from exported JSON files"""
    costs = {}
    
    # Load cost data
    bedrock_data = load_json_file('bedrock_costs.json')
    kendra_data = load_json_file('kendra_costs.json')
    lambda_data = load_json_file('lambda_costs.json')
    s3_data = load_json_file('s3_costs.json')
    dynamodb_data = load_json_file('dynamodb_costs.json')
    
    # Calculate 100% AI service costs
    bedrock_cost = extract_cost_amount(bedrock_data)
    kendra_cost = extract_cost_amount(kendra_data)
    
    # Calculate partial AI service costs
    lambda_total = extract_cost_amount(lambda_data)
    s3_total = extract_cost_amount(s3_data)
    dynamodb_total = extract_cost_amount(dynamodb_data)
    
    # Estimate AI portion (you can adjust these percentages)
    ai_lambda_percentage = Decimal('0.3')  # 30% of Lambda is AI
    ai_s3_percentage = Decimal('0.2')      # 20% of S3 is AI
    ai_dynamodb_percentage = Decimal('0.25') # 25% of DynamoDB is AI
    
    # Calculate AI costs
    costs['bedrock'] = bedrock_cost
    costs['kendra'] = kendra_cost
    costs['lambda'] = lambda_total * ai_lambda_percentage
    costs['s3'] = s3_total * ai_s3_percentage
    costs['dynamodb'] = dynamodb_total * ai_dynamodb_percentage
    
    # Total AI costs
    costs['total'] = sum(costs.values())
    
    return costs

def generate_report(costs):
    """Generate cost report"""
    print("\n=== AWS AI COST REPORT ===")
    print(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("AI Service Costs:")
    print(f"  Bedrock (100% AI): ${costs['bedrock']:.2f}")
    print(f"  Kendra (100% AI): ${costs['kendra']:.2f}")
    print(f"  Lambda (30% est.): ${costs['lambda']:.2f}")
    print(f"  S3 (20% est.): ${costs['s3']:.2f}")
    print(f"  DynamoDB (25% est.): ${costs['dynamodb']:.2f}")
    print(f"\nTOTAL AI COSTS: ${costs['total']:.2f}")
    
    # Daily average
    today = datetime.now()
    days_in_month = today.day
    daily_avg = costs['total'] / days_in_month
    print(f"Daily Average: ${daily_avg:.2f}")
    
    # Export to CSV
    with open('ai_costs_summary.csv', 'w', newline='') as csvfile:
        fieldnames = ['Service', 'Cost', 'Calculation Method']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerow({'Service': 'Bedrock', 'Cost': f"${costs['bedrock']:.2f}", 'Calculation Method': '100% AI Service'})
        writer.writerow({'Service': 'Kendra', 'Cost': f"${costs['kendra']:.2f}", 'Calculation Method': '100% AI Service'})
        writer.writerow({'Service': 'Lambda', 'Cost': f"${costs['lambda']:.2f}", 'Calculation Method': '30% Estimated'})
        writer.writerow({'Service': 'S3', 'Cost': f"${costs['s3']:.2f}", 'Calculation Method': '20% Estimated'})
        writer.writerow({'Service': 'DynamoDB', 'Cost': f"${costs['dynamodb']:.2f}", 'Calculation Method': '25% Estimated'})
        writer.writerow({'Service': 'TOTAL', 'Cost': f"${costs['total']:.2f}", 'Calculation Method': 'Sum of above'})
    
    print("\nReport saved to: ai_costs_summary.csv")

if __name__ == "__main__":
    print("Processing AWS cost exports...")
    costs = calculate_ai_costs()
    generate_report(costs)