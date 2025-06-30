#!/usr/bin/env python3
"""
Test the offline cost processing with sample data
This demonstrates how the system works without needing AWS access
"""

import json
import os
from decimal import Decimal

# Create sample cost data files (simulating AWS CLI export)
def create_sample_data():
    """Create sample JSON files that simulate AWS Cost Explorer output"""
    
    # Sample Bedrock costs (100% AI)
    bedrock_data = {
        "ResultsByTime": [{
            "TimePeriod": {"Start": "2025-06-01", "End": "2025-06-26"},
            "Total": {
                "UnblendedCost": {"Amount": "45.23", "Unit": "USD"}
            }
        }]
    }
    
    # Sample Lambda costs (will apply 30% for AI)
    lambda_data = {
        "ResultsByTime": [{
            "TimePeriod": {"Start": "2025-06-01", "End": "2025-06-26"},
            "Total": {
                "UnblendedCost": {"Amount": "125.60", "Unit": "USD"}
            }
        }]
    }
    
    # Sample S3 costs (will apply 20% for AI)
    s3_data = {
        "ResultsByTime": [{
            "TimePeriod": {"Start": "2025-06-01", "End": "2025-06-26"},
            "Total": {
                "UnblendedCost": {"Amount": "89.45", "Unit": "USD"}
            }
        }]
    }
    
    # Sample DynamoDB costs (will apply 25% for AI)
    dynamodb_data = {
        "ResultsByTime": [{
            "TimePeriod": {"Start": "2025-06-01", "End": "2025-06-26"},
            "Total": {
                "UnblendedCost": {"Amount": "67.20", "Unit": "USD"}
            }
        }]
    }
    
    # Sample Kendra costs (100% AI)
    kendra_data = {
        "ResultsByTime": [{
            "TimePeriod": {"Start": "2025-06-01", "End": "2025-06-26"},
            "Total": {
                "UnblendedCost": {"Amount": "150.00", "Unit": "USD"}
            }
        }]
    }
    
    # Write sample files
    with open('bedrock_costs.json', 'w') as f:
        json.dump(bedrock_data, f, indent=2)
    with open('lambda_costs.json', 'w') as f:
        json.dump(lambda_data, f, indent=2)
    with open('s3_costs.json', 'w') as f:
        json.dump(s3_data, f, indent=2)
    with open('dynamodb_costs.json', 'w') as f:
        json.dump(dynamodb_data, f, indent=2)
    with open('kendra_costs.json', 'w') as f:
        json.dump(kendra_data, f, indent=2)
    
    print("Sample cost data files created:")
    print("  - bedrock_costs.json")
    print("  - lambda_costs.json")
    print("  - s3_costs.json")
    print("  - dynamodb_costs.json")
    print("  - kendra_costs.json")

if __name__ == "__main__":
    print("Creating sample AWS cost data for testing...")
    create_sample_data()
    
    print("\nNow you can run: python process_cost_exports.py")
    print("This will process the sample data and generate a cost report.")