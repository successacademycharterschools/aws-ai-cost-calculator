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
        
        # Validate account IDs
        self.valid_accounts = []
        if self._is_valid_account_id(self.sandbox_account_id):
            self.valid_accounts.append(('sandbox', self.sandbox_account_id))
        if self._is_valid_account_id(self.nonprod_account_id):
            self.valid_accounts.append(('nonprod', self.nonprod_account_id))
        
        # Initialize boto3 clients with session token support
        self.session = self._create_boto3_session()
        self.ce_client = self.session.client('ce')
        self.lambda_client = self.session.client('lambda')
        
        # Load project configuration
        self.projects = self.load_project_config()
        
        # Cost data storage
        self.cost_data = {}
        self.lambda_function_counts = {}
    
    def _is_valid_account_id(self, account_id: str) -> bool:
        """Check if account ID is valid (12 digits)"""
        if not account_id:
            return False
        if account_id in ['YOUR_SANDBOX_ACCOUNT_ID', 'YOUR_NONPROD_ACCOUNT_ID']:
            return False
        if not account_id.isdigit() or len(account_id) != 12:
            return False
        return True
    
    def _create_boto3_session(self):
        """Create boto3 session with session token support"""
        # Check for session token authentication
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        session_token = os.environ.get('AWS_SESSION_TOKEN')
        
        if session_token:
            # Use session token authentication
            logger.info("Using AWS session token authentication")
            return boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token,
                region_name='us-east-1'  # Cost Explorer only works in us-east-1
            )
        else:
            # Use default authentication (IAM role, credentials file, etc.)
            logger.info("Using default AWS authentication")
            return boto3.Session(region_name='us-east-1')
        
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
    
    def get_ai_lambda_functions(self) -> Dict[str, List[str]]:
        """List all Lambda functions and categorize by AI project"""
        ai_functions = {project_id: [] for project_id in self.projects}
        total_functions = 0
        
        try:
            # List all Lambda functions
            paginator = self.lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page.get('Functions', []):
                    function_name = function['FunctionName'].lower()
                    total_functions += 1
                    
                    # Check which AI project this function belongs to
                    for project_id, project_config in self.projects.items():
                        for pattern in project_config.get('lambda_patterns', []):
                            if pattern.lower() in function_name:
                                ai_functions[project_id].append(function['FunctionName'])
                                break
            
            # Store counts for reporting
            self.lambda_function_counts['total'] = total_functions
            for project_id, functions in ai_functions.items():
                self.lambda_function_counts[project_id] = len(functions)
                
            logger.info(f"Found {total_functions} total Lambda functions")
            for project_id, functions in ai_functions.items():
                if functions:
                    logger.info(f"  {self.projects[project_id]['name']}: {len(functions)} functions")
                    
        except Exception as e:
            logger.error(f"Error listing Lambda functions: {str(e)}")
            
        return ai_functions
    
    def get_lambda_costs_for_project(self, project_id: str, project_config: Dict, 
                                   start_date: str, end_date: str, account_id: str) -> Decimal:
        """Get Lambda costs using percentage-based allocation"""
        try:
            # Get total Lambda costs for the account
            response = self.retry_api_call(
                self.ce_client.get_cost_and_usage,
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'And': [
                        {'Dimensions': {'Key': 'SERVICE', 'Values': ['AWS Lambda']}},
                        {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [account_id]}}
                    ]
                }
            )
            
            if response and 'ResultsByTime' in response:
                total_lambda_cost = Decimal('0')
                for result in response['ResultsByTime']:
                    amount = result['Total']['UnblendedCost']['Amount']
                    total_lambda_cost += Decimal(amount)
                
                # Calculate AI percentage if we have function counts
                if hasattr(self, 'lambda_function_counts') and 'total' in self.lambda_function_counts:
                    total_functions = self.lambda_function_counts.get('total', 0)
                    project_functions = self.lambda_function_counts.get(project_id, 0)
                    
                    if total_functions > 0 and project_functions > 0:
                        ai_percentage = Decimal(project_functions) / Decimal(total_functions)
                        ai_cost = total_lambda_cost * ai_percentage
                        logger.info(f"Lambda cost for {project_id}: ${ai_cost:.2f} ({project_functions}/{total_functions} functions = {ai_percentage:.1%})")
                        return ai_cost
                
                # Fallback: use configured percentage
                default_percentage = Decimal('0.2')  # 20% default
                ai_cost = total_lambda_cost * default_percentage
                logger.info(f"Lambda cost for {project_id}: ${ai_cost:.2f} (estimated {default_percentage:.0%})")
                return ai_cost
                
        except Exception as e:
            logger.error(f"Error getting Lambda costs: {str(e)}")
            
        return Decimal('0')
    
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
        
        # Services that are 100% AI-related
        ai_only_services = ['bedrock', 'kendra']
        
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
                    amount = result.get('Total', {}).get('UnblendedCost', {}).get('Amount', '0')
                    total_cost += Decimal(amount)
                
                # Handle different service types
                if service in ai_only_services:
                    # 100% of costs for AI-only services
                    logger.info(f"{service.upper()} cost (100% AI): ${total_cost:.2f}")
                    return total_cost
                elif service in ['s3', 'dynamodb'] and total_cost > 0:
                    # Estimate based on project allocation
                    ai_percentage = Decimal('0.2')  # 20% default
                    ai_cost = total_cost * ai_percentage
                    logger.info(f"{service.upper()} cost (estimated {ai_percentage:.0%} AI): ${ai_cost:.2f}")
                    return ai_cost
                else:
                    # Other services - return full cost for now
                    return total_cost
            
        except Exception as e:
            logger.error(f"Error getting {service} costs: {str(e)}")
            
        return Decimal('0')
    
    def calculate_all_costs(self):
        """Calculate costs for all AI projects"""
        start_date, end_date = self.get_date_range()
        logger.info(f"Calculating costs from {start_date} to {end_date}")
        
        # First, get Lambda function inventory
        logger.info("Analyzing Lambda functions...")
        self.get_ai_lambda_functions()
        
        # Check if we have valid accounts
        if not self.valid_accounts:
            logger.error("No valid AWS account IDs configured!")
            logger.error("Please set AWS_SANDBOX_ACCOUNT_ID and/or AWS_NONPROD_ACCOUNT_ID")
            return
        
        # Process each project
        for project_id, project_config in self.projects.items():
            logger.info(f"\nProcessing project: {project_config['name']} (Status: {project_config['status']})")
            
            project_costs = {
                'name': project_config['name'],
                'status': project_config['status'],
                'services': {},
                'total': Decimal('0')
            }
            
            # Calculate costs for each service in both environments
            for service in project_config['services']:
                service_total = Decimal('0')
                
                # Process each valid account
                for env_name, account_id in self.valid_accounts:
                    try:
                        cost = self.get_service_costs(
                            service, project_id, project_config,
                            start_date, end_date, account_id
                        )
                        service_total += cost
                        if cost > 0:
                            logger.info(f"  {service} ({env_name}): ${cost:.2f}")
                    except Exception as e:
                        logger.warning(f"  Failed to get {service} costs for {env_name}: {str(e)}")
                        continue
                
                if service_total > 0:
                    project_costs['services'][service] = service_total
                    project_costs['total'] += service_total
            
            self.cost_data[project_id] = project_costs
            logger.info(f"  Total for {project_config['name']}: ${project_costs['total']:.2f}\n")
    
    def export_to_csv(self, filename: str = 'ai_project_costs.csv'):
        """Export cost data to CSV file"""
        try:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['Project Name', 'Service', 'Current Month Cost', 'Daily Average', 'Status', 'Calculation Method']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                # Calculate days in current month for daily average
                today = datetime.now()
                days_in_month = today.day
                
                for project_id, project_data in self.cost_data.items():
                    # Write individual service costs
                    for service, cost in project_data['services'].items():
                        daily_avg = cost / days_in_month if days_in_month > 0 else Decimal('0')
                        
                        # Determine calculation method
                        if service in ['bedrock', 'kendra']:
                            calc_method = "100% AI Service"
                        elif service == 'lambda':
                            func_count = self.lambda_function_counts.get(project_id, 0)
                            total_funcs = self.lambda_function_counts.get('total', 0)
                            if func_count > 0 and total_funcs > 0:
                                calc_method = f"{func_count}/{total_funcs} functions"
                            else:
                                calc_method = "Estimated 20%"
                        elif service in ['s3', 'dynamodb']:
                            calc_method = "Estimated 20%"
                        else:
                            calc_method = "Full cost"
                        
                        writer.writerow({
                            'Project Name': project_data['name'],
                            'Service': service.upper(),
                            'Current Month Cost': f"${cost:.2f}",
                            'Daily Average': f"${daily_avg:.2f}",
                            'Status': project_data['status'],
                            'Calculation Method': calc_method
                        })
                    
                    # Write project total
                    if project_data['total'] > 0:
                        daily_avg = project_data['total'] / days_in_month if days_in_month > 0 else Decimal('0')
                        writer.writerow({
                            'Project Name': project_data['name'],
                            'Service': 'TOTAL',
                            'Current Month Cost': f"${project_data['total']:.2f}",
                            'Daily Average': f"${daily_avg:.2f}",
                            'Status': project_data['status'],
                            'Calculation Method': 'Sum of services'
                        })
                        writer.writerow({})  # Empty row for separation
                
                logger.info(f"Cost report exported to {filename}")
                
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
    
    def run(self):
        """Main execution method"""
        logger.info("Starting AWS AI Cost Calculator...")
        logger.info(f"Session authenticated: {'Yes' if os.environ.get('AWS_SESSION_TOKEN') else 'No'}")
        
        # Calculate costs
        self.calculate_all_costs()
        
        # Export results
        if self.cost_data:
            self.export_to_csv()
            # Print summary
            self.print_summary()
        else:
            logger.warning("No cost data collected. Check your configuration and AWS permissions.")
    
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