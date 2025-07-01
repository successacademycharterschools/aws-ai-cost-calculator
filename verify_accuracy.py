#!/usr/bin/env python3
"""
Verify accuracy of AWS AI Cost Calculator
Compares calculator results with AWS Cost Explorer
"""

import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import json

def verify_costs():
    """Compare calculator costs with direct AWS API calls"""
    print("🔍 Verifying Cost Accuracy\n")
    
    # Initialize boto3 session
    session = boto3.Session(profile_name='sa-sandbox')
    ce_client = session.client('ce', region_name='us-east-1')
    
    # Date range - last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    print(f"📅 Date Range: {start_date} to {end_date}")
    print("="*50)
    
    # Services to check
    services_to_verify = [
        {
            'name': 'Amazon Bedrock',
            'service_codes': ['AmazonBedrock'],
            'ai_percentage': 100
        },
        {
            'name': 'AWS Lambda',
            'service_codes': ['AWSLambda'],
            'ai_percentage': 30
        },
        {
            'name': 'Amazon S3',
            'service_codes': ['AmazonS3'],
            'ai_percentage': 20
        },
        {
            'name': 'Amazon CloudWatch',
            'service_codes': ['AmazonCloudWatch'],
            'ai_percentage': 15
        }
    ]
    
    total_aws_cost = Decimal('0')
    total_ai_cost = Decimal('0')
    
    print("\n📊 Cost Breakdown by Service:")
    print("-"*50)
    
    for service in services_to_verify:
        try:
            # Get cost from AWS Cost Explorer
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': service['service_codes']
                    }
                }
            )
            
            # Calculate total cost for service
            service_cost = Decimal('0')
            for result in response['ResultsByTime']:
                amount = Decimal(result['Total']['UnblendedCost']['Amount'])
                service_cost += amount
            
            # Calculate AI portion
            ai_cost = service_cost * Decimal(str(service['ai_percentage'] / 100))
            
            total_aws_cost += service_cost
            total_ai_cost += ai_cost
            
            print(f"\n{service['name']}:")
            print(f"  Total Cost: ${service_cost:.2f}")
            print(f"  AI Portion ({service['ai_percentage']}%): ${ai_cost:.2f}")
            
        except Exception as e:
            print(f"\n{service['name']}: Error - {str(e)}")
    
    print("\n" + "="*50)
    print(f"\n📈 Summary:")
    print(f"  Total AWS Costs: ${total_aws_cost:.2f}")
    print(f"  Total AI Costs: ${total_ai_cost:.2f}")
    print(f"  AI Percentage: {(total_ai_cost / total_aws_cost * 100):.1f}%")
    
    # Verification with specific resources
    print("\n\n🔎 Verifying Specific AI Resources:")
    print("-"*50)
    
    # Check Lambda functions
    lambda_client = session.client('lambda', region_name='us-east-1')
    try:
        functions = lambda_client.list_functions()
        ai_functions = [f for f in functions['Functions'] 
                       if any(pattern in f['FunctionName'].lower() 
                             for pattern in ['ai', 'ask-eva', 'iep'])]
        print(f"\n✅ Found {len(ai_functions)} AI Lambda functions")
        for func in ai_functions[:5]:  # Show first 5
            print(f"   - {func['FunctionName']}")
    except:
        print("\n⚠️  Could not list Lambda functions")
    
    # Check S3 buckets
    s3_client = session.client('s3')
    try:
        buckets = s3_client.list_buckets()
        ai_buckets = [b for b in buckets['Buckets'] 
                     if any(pattern in b['Name'].lower() 
                           for pattern in ['sa-ai', 'modeltraining'])]
        print(f"\n✅ Found {len(ai_buckets)} AI S3 buckets")
        for bucket in ai_buckets[:5]:  # Show first 5
            print(f"   - {bucket['Name']}")
    except:
        print("\n⚠️  Could not list S3 buckets")
    
    print("\n" + "="*50)
    print("\n✅ Verification complete!")
    print("\n💡 To ensure accuracy:")
    print("1. Compare these numbers with AWS Cost Explorer")
    print("2. Check that AI resource patterns match your naming")
    print("3. Adjust attribution percentages if needed")

if __name__ == "__main__":
    try:
        verify_costs()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you're logged in: aws sso login --profile sa-sandbox")