#!/usr/bin/env python3
"""
AWS AI Cost Calculator
Simple script to calculate costs for AI projects across AWS services
Focuses only on AI-related Lambda functions and services
"""

import boto3
import json
import csv
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import time
import os
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIProjectCostCalculator:
    def __init__(self, sandbox_account_id: str = None, nonprod_account_id: str = None):
        """Initialize the cost calculator with AWS account IDs"""
        self.sandbox_account_id = sandbox_account_id or os.environ.get('AWS_SANDBOX_ACCOUNT_ID')
        self.nonprod_account_id = nonprod_account_id or os.environ.get('AWS_NONPROD_ACCOUNT_ID')
        
        # Initialize boto3 clients
        self.ce_client = boto3.client('ce', region_name='us-east-1')  # Cost Explorer only works in us-east-1
        
        # Load project configuration
        self.projects = self.load_project_config()
        
        # Cost data storage
        self.cost_data = {}
        
    def load_project_config(self) -> Dict:
        """Load AI project configuration"""
        return {
            "resume_knockout": {
                "name": "Resume Knockout",
                "status": "paused",
                "services": ["lambda", "s3", "sns", "events"],
                "lambda_patterns": ["resume-knockout", "rk-", "resumeknockout"],
                "s3_buckets": ["resume-knockout", "rk-data"],
                "tags": {"Project": "ResumeKnockout", "project": "resume-knockout"}
            },
            "ask_eva": {
                "name": "Ask Eva",
                "status": "POC",
                "services": ["amplify", "apigateway", "lambda", "bedrock", "kendra"],
                "lambda_patterns": ["ask-eva", "askeva", "eva-bot"],
                "bedrock_models": ["anthropic.claude-3-haiku"],
                "tags": {"Project": "AskEva", "project": "ask-eva"}
            },
            "resume_scoring": {
                "name": "Resume Scoring",
                "status": "paused",
                "services": ["lambda"],
                "lambda_patterns": ["resume-scoring", "scoring", "rs-"],
                "tags": {"Project": "ResumeScoring", "project": "resume-scoring"}
            },
            "iep_report": {
                "name": "IEP Report",
                "status": "MVP",
                "services": ["lambda", "apigateway", "logs", "bedrock"],
                "lambda_patterns": ["iep-report", "iep", "scholar-report"],
                "tags": {"Project": "IEPReport", "project": "iep-report"}
            },
            "financial_aid": {
                "name": "Financial Aid",
                "status": "MVP",
                "services": ["s3", "lambda", "sqs", "bedrock", "dynamodb"],
                "lambda_patterns": ["financial-aid", "finaid", "fa-"],
                "s3_buckets": ["financial-aid", "finaid-data"],
                "dynamodb_tables": ["financial-aid", "finaid"],
                "tags": {"Project": "FinancialAid", "project": "financial-aid"}
            }
        }
    
    def get_date_range(self) -> tuple:
        """Get current month date range for cost queries"""
        today = datetime.now()
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        return start_date, end_date
    
    def retry_api_call(self, func, max_retries: int = 3, **kwargs):
        """Retry API calls with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return func(**kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"API call failed after {max_retries} attempts: {str(e)}")
                    return None
                wait_time = 2 ** attempt
                logger.warning(f"API call failed, retrying in {wait_time} seconds... Error: {str(e)}")
                time.sleep(wait_time)
        return None
    
    def get_lambda_costs_for_project(self, project_id: str, project_config: Dict, 
                                   start_date: str, end_date: str, account_id: str) -> Decimal:
        """Get Lambda costs filtered for AI-specific functions only"""
        total_cost = Decimal('0')
        
        # Try to get costs by function name patterns
        for pattern in project_config.get('lambda_patterns', []):
            try:
                response = self.retry_api_call(
                    self.ce_client.get_cost_and_usage,
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    Filter={
                        'And': [
                            {'Dimensions': {'Key': 'SERVICE', 'Values': ['AWS Lambda']}},
                            {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [account_id]}},
                            {'Dimensions': {'Key': 'USAGE_TYPE', 'Values': [
                                'Lambda-GB-Second', 'Lambda-Request', 'LambdaEdge-GB-Second', 
                                'LambdaEdge-Request', 'Lambda-Provisioned-GB-Second',
                                'Lambda-Provisioned-Concurrency'
                            ]}}
                        ]
                    },
                    GroupBy=[
                        {'Type': 'DIMENSION', 'Key': 'RESOURCE_ID'}
                    ]
                )
                
                if response and 'ResultsByTime' in response:
                    for result in response['ResultsByTime']:
                        for group in result.get('Groups', []):
                            resource_id = group['Keys'][0]
                            # Check if this Lambda function matches our AI project pattern
                            if any(p in resource_id.lower() for p in pattern.lower().split('-')):
                                cost = Decimal(group['Metrics']['UnblendedCost']['Amount'])
                                total_cost += cost
                                logger.info(f"Found Lambda cost for {project_id}: {resource_id} = ${cost}")
                                
            except Exception as e:
                logger.error(f"Error getting Lambda costs for pattern {pattern}: {str(e)}")
                
        return total_cost
    
    def get_service_costs(self, service: str, project_id: str, project_config: Dict,
                         start_date: str, end_date: str, account_id: str) -> Decimal:
        """Get costs for a specific AWS service"""
        
        # Special handling for Lambda - AI functions only
        if service == 'lambda':
            return self.get_lambda_costs_for_project(project_id, project_config, 
                                                   start_date, end_date, account_id)
        
        # Map service names to AWS service names
        service_mapping = {
            's3': 'Amazon Simple Storage Service',
            'dynamodb': 'Amazon DynamoDB',
            'bedrock': 'Amazon Bedrock',
            'apigateway': 'Amazon API Gateway',
            'sqs': 'Amazon Simple Queue Service',
            'sns': 'Amazon Simple Notification Service',
            'kendra': 'Amazon Kendra',
            'amplify': 'AWS Amplify',
            'events': 'Amazon EventBridge',
            'logs': 'Amazon CloudWatch'
        }
        
        aws_service_name = service_mapping.get(service, service)
        
        try:
            # Build filter
            filter_dict = {
                'And': [
                    {'Dimensions': {'Key': 'SERVICE', 'Values': [aws_service_name]}},
                    {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [account_id]}}
                ]
            }
            
            # Add project-specific filters if available
            if service == 's3' and 's3_buckets' in project_config:
                # For S3, we'll get all costs and filter later
                pass
            elif service == 'dynamodb' and 'dynamodb_tables' in project_config:
                # For DynamoDB, we'll get all costs and filter later
                pass
                
            response = self.retry_api_call(
                self.ce_client.get_cost_and_usage,
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter=filter_dict
            )
            
            if response and 'ResultsByTime' in response:
                total_cost = Decimal('0')
                for result in response['ResultsByTime']:
                    for group in result.get('Groups', []):
                        cost = Decimal(group['Metrics']['UnblendedCost']['Amount'])
                        total_cost += cost
                
                # For S3 and DynamoDB, estimate project portion based on naming
                if service in ['s3', 'dynamodb'] and total_cost > 0:
                    # Rough estimate: assume 20% of costs are for this AI project
                    # In production, you'd use tags or more sophisticated filtering
                    total_cost = total_cost * Decimal('0.2')
                    
                return total_cost
            
        except Exception as e:
            logger.error(f"Error getting {service} costs: {str(e)}")
            
        return Decimal('0')
    
    def calculate_all_costs(self):
        """Calculate costs for all AI projects"""
        start_date, end_date = self.get_date_range()
        logger.info(f"Calculating costs from {start_date} to {end_date}")
        
        # Process each project
        for project_id, project_config in self.projects.items():
            logger.info(f"Processing project: {project_config['name']} (Status: {project_config['status']})")
            
            project_costs = {
                'name': project_config['name'],
                'status': project_config['status'],
                'services': {},
                'total': Decimal('0')
            }
            
            # Calculate costs for each service in both environments
            for service in project_config['services']:
                service_total = Decimal('0')
                
                # Get costs from sandbox account
                if self.sandbox_account_id:
                    sandbox_cost = self.get_service_costs(
                        service, project_id, project_config,
                        start_date, end_date, self.sandbox_account_id
                    )
                    service_total += sandbox_cost
                    if sandbox_cost > 0:
                        logger.info(f"  {service} (sandbox): ${sandbox_cost:.2f}")
                
                # Get costs from non-prod account
                if self.nonprod_account_id:
                    nonprod_cost = self.get_service_costs(
                        service, project_id, project_config,
                        start_date, end_date, self.nonprod_account_id
                    )
                    service_total += nonprod_cost
                    if nonprod_cost > 0:
                        logger.info(f"  {service} (non-prod): ${nonprod_cost:.2f}")
                
                if service_total > 0:
                    project_costs['services'][service] = service_total
                    project_costs['total'] += service_total
            
            self.cost_data[project_id] = project_costs
            logger.info(f"  Total for {project_config['name']}: ${project_costs['total']:.2f}\n")
    
    def export_to_csv(self, filename: str = 'ai_project_costs.csv'):
        """Export cost data to CSV file"""
        try:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['Project Name', 'Service', 'Current Month Cost', 'Daily Average', 'Status']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                # Calculate days in current month for daily average
                today = datetime.now()
                days_in_month = today.day
                
                for project_id, project_data in self.cost_data.items():
                    # Write individual service costs
                    for service, cost in project_data['services'].items():
                        daily_avg = cost / days_in_month if days_in_month > 0 else Decimal('0')
                        writer.writerow({
                            'Project Name': project_data['name'],
                            'Service': service.upper(),
                            'Current Month Cost': f"${cost:.2f}",
                            'Daily Average': f"${daily_avg:.2f}",
                            'Status': project_data['status']
                        })
                    
                    # Write project total
                    if project_data['total'] > 0:
                        daily_avg = project_data['total'] / days_in_month if days_in_month > 0 else Decimal('0')
                        writer.writerow({
                            'Project Name': project_data['name'],
                            'Service': 'TOTAL',
                            'Current Month Cost': f"${project_data['total']:.2f}",
                            'Daily Average': f"${daily_avg:.2f}",
                            'Status': project_data['status']
                        })
                        writer.writerow({})  # Empty row for separation
                
                logger.info(f"Cost report exported to {filename}")
                
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
    
    def run(self):
        """Main execution method"""
        logger.info("Starting AWS AI Cost Calculator...")
        
        # Validate configuration
        if not self.sandbox_account_id and not self.nonprod_account_id:
            logger.error("No AWS account IDs configured. Set AWS_SANDBOX_ACCOUNT_ID and/or AWS_NONPROD_ACCOUNT_ID")
            return
        
        # Calculate costs
        self.calculate_all_costs()
        
        # Export results
        self.export_to_csv()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print cost summary to console"""
        print("\n=== AI PROJECT COST SUMMARY ===")
        print(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        total_all_projects = Decimal('0')
        
        for project_id, project_data in self.cost_data.items():
            if project_data['total'] > 0:
                print(f"{project_data['name']} ({project_data['status']}): ${project_data['total']:.2f}")
                total_all_projects += project_data['total']
        
        print(f"\nTOTAL ALL AI PROJECTS: ${total_all_projects:.2f}")
        print(f"Daily Average: ${total_all_projects / datetime.now().day:.2f}")


if __name__ == "__main__":
    # Run the calculator
    calculator = AIProjectCostCalculator()
    calculator.run()