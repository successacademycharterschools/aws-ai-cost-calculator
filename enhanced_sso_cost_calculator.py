#!/usr/bin/env python3
"""
Enhanced AWS AI Cost Calculator with SSO Support
Calculates costs for ALL AWS AI/ML services with project attribution
"""

import os
import json
import csv
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
import boto3
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.columns import Columns

from sso_auth import SSOAuthenticator
from enhanced_ai_discovery import EnhancedAIDiscovery

console = Console()

class EnhancedSSOCostCalculator:
    def __init__(self):
        self.authenticator = SSOAuthenticator()
        self.discovery = EnhancedAIDiscovery()
        self.cost_data = {}
        self.discovered_resources = []
        
        # Load AI services configuration
        with open('ai_services_config.json', 'r') as f:
            self.config = json.load(f)
        
    def calculate_costs_for_resources(self, session: boto3.Session, account_name: str, 
                                    discovered: Dict, start_date: str = None, end_date: str = None,
                                    additional_services: List[str] = None) -> Dict:
        """Calculate costs for discovered AI resources"""
        ce_client = session.client('ce', region_name='us-east-1')
        
        # Use provided dates or default to current month
        if not start_date or not end_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            display_end_date = today.strftime('%Y-%m-%d')
            ce_end_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            # AWS Cost Explorer needs the day after the end date
            display_end_date = end_date
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            ce_end_date = (end_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
        
        costs = {
            'account': account_name,
            'period': f"{start_date} to {display_end_date}",
            'services': {},
            'projects': {},
            'total': Decimal('0'),
            'service_details': {}
        }
        
        # Get account ID from session
        try:
            sts = session.client('sts')
            account_id = sts.get_caller_identity()['Account']
        except:
            console.print(f"[yellow]Warning: Could not get account ID for {account_name}[/yellow]")
            return costs
        
        # Calculate costs for each service type
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Calculate costs for each discovered AI service
            for service_key, service_data in discovered.get('services', {}).items():
                if service_key in self.config['ai_services']:
                    service_info = self.config['ai_services'][service_key]
                    task = progress.add_task(
                        f"[cyan]Calculating {service_info['cost_explorer_name']} costs for {account_name}...", 
                        total=None
                    )
                    
                    service_cost = self._calculate_ai_service_costs(
                        ce_client, service_info['cost_explorer_name'], 
                        start_date, ce_end_date, account_id
                    )
                    
                    if service_cost > 0:
                        costs['services'][service_key] = service_cost
                        costs['total'] += service_cost
                        
                        # Store detailed service information
                        costs['service_details'][service_key] = {
                            'cost': service_cost,
                            'resources': service_data.get('resources', []),
                            'count': service_data.get('count', 0),
                            'category': service_info.get('category', 'Unknown')
                        }
                    
                    progress.update(task, completed=True)
                
                # Handle traditional services (Lambda, S3, DynamoDB) with AI resources
                elif service_key in ['lambda', 's3', 'dynamodb']:
                    task = progress.add_task(
                        f"[cyan]Calculating {service_key.upper()} costs for AI resources...", 
                        total=None
                    )
                    
                    if service_key == 'lambda':
                        service_cost = self._calculate_lambda_costs(
                            ce_client, service_data.get('resources', []),
                            start_date, ce_end_date, account_id
                        )
                    elif service_key == 's3':
                        service_cost = self._calculate_s3_costs(
                            ce_client, service_data.get('resources', []),
                            start_date, ce_end_date, account_id
                        )
                    elif service_key == 'dynamodb':
                        service_cost = self._calculate_dynamodb_costs(
                            ce_client, service_data.get('resources', []),
                            start_date, ce_end_date, account_id
                        )
                    
                    if service_cost > 0:
                        costs['services'][service_key] = service_cost
                        costs['total'] += service_cost
                        
                        costs['service_details'][service_key] = {
                            'cost': service_cost,
                            'resources': service_data.get('resources', []),
                            'count': service_data.get('count', 0),
                            'category': service_data.get('service_info', {}).get('category', 'Infrastructure')
                        }
                    
                    progress.update(task, completed=True)
        
        # Calculate project-level costs
        self._calculate_project_costs(costs, discovered)
        
        return costs
    
    def _calculate_ai_service_costs(self, ce_client, service_name: str,
                                  start_date: str, end_date: str, account_id: str) -> Decimal:
        """Calculate costs for a specific AI service"""
        try:
            response = ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'And': [
                        {'Dimensions': {'Key': 'SERVICE', 'Values': [service_name]}},
                        {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [account_id]}}
                    ]
                }
            )
            
            total_cost = Decimal('0')
            for result in response.get('ResultsByTime', []):
                amount = result['Total']['UnblendedCost']['Amount']
                total_cost += Decimal(amount)
            
            return total_cost
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get costs for {service_name}: {str(e)}[/yellow]")
            return Decimal('0')
    
    def _calculate_lambda_costs(self, ce_client, lambda_functions: List[Dict],
                              start_date: str, end_date: str, account_id: str) -> Decimal:
        """Calculate costs for specific Lambda functions"""
        if not lambda_functions:
            return Decimal('0')
        
        try:
            # Get total Lambda costs for the account
            response = ce_client.get_cost_and_usage(
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
            
            total_lambda_cost = Decimal('0')
            for result in response.get('ResultsByTime', []):
                amount = result['Total']['UnblendedCost']['Amount']
                total_lambda_cost += Decimal(amount)
            
            # For now, distribute costs evenly among AI functions
            # In production, you'd use CloudWatch metrics for more accurate attribution
            if total_lambda_cost > 0:
                # Get total number of Lambda functions in the account for proportion
                return total_lambda_cost * Decimal(len(lambda_functions)) / Decimal(100)  # Rough estimate
            
            return Decimal('0')
            
        except Exception as e:
            return Decimal('0')
    
    def _calculate_s3_costs(self, ce_client, s3_buckets: List[Dict],
                          start_date: str, end_date: str, account_id: str) -> Decimal:
        """Calculate costs for specific S3 buckets"""
        if not s3_buckets:
            return Decimal('0')
        
        try:
            # Get S3 costs with bucket-level granularity
            bucket_names = [bucket['name'] for bucket in s3_buckets]
            
            response = ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'And': [
                        {'Dimensions': {'Key': 'SERVICE', 'Values': ['Amazon Simple Storage Service']}},
                        {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [account_id]}}
                    ]
                },
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}]
            )
            
            total_cost = Decimal('0')
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    # Filter for usage types that might be related to our buckets
                    usage_type = group['Keys'][0]
                    if any(bucket in usage_type for bucket in bucket_names):
                        amount = group['Metrics']['UnblendedCost']['Amount']
                        total_cost += Decimal(amount)
            
            # If no specific bucket costs found, estimate based on total S3 costs
            if total_cost == 0:
                total_s3_response = ce_client.get_cost_and_usage(
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    Filter={
                        'And': [
                            {'Dimensions': {'Key': 'SERVICE', 'Values': ['Amazon Simple Storage Service']}},
                            {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [account_id]}}
                        ]
                    }
                )
                
                for result in total_s3_response.get('ResultsByTime', []):
                    amount = result['Total']['UnblendedCost']['Amount']
                    # Rough estimate: AI buckets are 10% of total S3 costs
                    total_cost += Decimal(amount) * Decimal('0.1')
            
            return total_cost
            
        except Exception as e:
            return Decimal('0')
    
    def _calculate_dynamodb_costs(self, ce_client, dynamodb_tables: List[Dict],
                                start_date: str, end_date: str, account_id: str) -> Decimal:
        """Calculate costs for specific DynamoDB tables"""
        if not dynamodb_tables:
            return Decimal('0')
        
        try:
            # Get DynamoDB costs
            response = ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'And': [
                        {'Dimensions': {'Key': 'SERVICE', 'Values': ['Amazon DynamoDB']}},
                        {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [account_id]}}
                    ]
                }
            )
            
            total_cost = Decimal('0')
            for result in response.get('ResultsByTime', []):
                amount = result['Total']['UnblendedCost']['Amount']
                # Rough estimate: AI tables are 20% of total DynamoDB costs
                total_cost += Decimal(amount) * Decimal('0.2')
            
            return total_cost
            
        except Exception as e:
            return Decimal('0')
    
    def _calculate_project_costs(self, costs: Dict, discovered: Dict):
        """Aggregate costs by project with accurate attribution"""
        projects = discovered.get('projects', {})
        
        for project_name, project_data in projects.items():
            if project_name == 'Unknown':
                continue
            
            project_cost = Decimal('0')
            project_services = {}
            
            # Calculate costs for each service used by the project
            for service_key, resources in project_data.get('services', {}).items():
                if service_key in costs['services']:
                    # Calculate proportion of service cost for this project
                    total_service_resources = discovered['services'][service_key]['count']
                    project_service_resources = len(resources)
                    
                    if total_service_resources > 0:
                        service_cost = costs['services'][service_key]
                        project_service_cost = service_cost * Decimal(project_service_resources) / Decimal(total_service_resources)
                        
                        project_cost += project_service_cost
                        project_services[service_key] = {
                            'cost': project_service_cost,
                            'resources': project_service_resources
                        }
            
            if project_cost > 0:
                costs['projects'][project_name] = {
                    'total_cost': project_cost,
                    'services': project_services,
                    'resource_count': project_data['total_resources']
                }
    
    def display_cost_report(self, all_costs: List[Dict], output_format: str = 'table'):
        """Display comprehensive cost report"""
        if output_format == 'table':
            self._display_table_report(all_costs)
        elif output_format == 'json':
            return json.dumps(all_costs, cls=DecimalEncoder, indent=2)
        elif output_format == 'csv':
            return self._generate_csv_report(all_costs)
    
    def _display_table_report(self, all_costs: List[Dict]):
        """Display costs in rich tables"""
        total_org_cost = sum(cost['total'] for cost in all_costs)
        
        # Organization summary
        console.print(f"\n[bold cyan]AWS AI Services Cost Report[/bold cyan]")
        console.print(f"Total Organization AI Spend: [bold green]${total_org_cost:,.2f}[/bold green]")
        
        # Account breakdown
        account_table = Table(title="\nCost by Account")
        account_table.add_column("Account", style="cyan")
        account_table.add_column("Period", style="white")
        account_table.add_column("Total Cost", style="green")
        account_table.add_column("Services Used", style="yellow")
        
        for cost in all_costs:
            services_count = len(cost['services'])
            account_table.add_row(
                cost['account'],
                cost['period'],
                f"${cost['total']:,.2f}",
                str(services_count)
            )
        
        console.print(account_table)
        
        # Service breakdown across all accounts
        service_totals = {}
        for cost in all_costs:
            for service, amount in cost['services'].items():
                if service not in service_totals:
                    service_totals[service] = {
                        'cost': Decimal('0'),
                        'accounts': 0,
                        'category': 'Unknown'
                    }
                service_totals[service]['cost'] += amount
                service_totals[service]['accounts'] += 1
                
                # Get category from service details
                if 'service_details' in cost and service in cost['service_details']:
                    service_totals[service]['category'] = cost['service_details'][service]['category']
                elif service in self.config['ai_services']:
                    service_totals[service]['category'] = self.config['ai_services'][service]['category']
        
        if service_totals:
            service_table = Table(title="\nCost by AI Service")
            service_table.add_column("Service", style="cyan")
            service_table.add_column("Category", style="magenta")
            service_table.add_column("Total Cost", style="green")
            service_table.add_column("Accounts", style="yellow")
            
            # Sort by cost descending
            sorted_services = sorted(service_totals.items(), key=lambda x: x[1]['cost'], reverse=True)
            
            for service, data in sorted_services:
                service_name = service
                if service in self.config['ai_services']:
                    service_name = self.config['ai_services'][service]['cost_explorer_name']
                
                service_table.add_row(
                    service_name,
                    data['category'],
                    f"${data['cost']:,.2f}",
                    str(data['accounts'])
                )
            
            console.print(service_table)
        
        # Project breakdown
        project_totals = {}
        for cost in all_costs:
            for project_name, project_data in cost.get('projects', {}).items():
                if project_name not in project_totals:
                    project_totals[project_name] = {
                        'cost': Decimal('0'),
                        'services': set(),
                        'resources': 0
                    }
                project_totals[project_name]['cost'] += project_data['total_cost']
                project_totals[project_name]['services'].update(project_data['services'].keys())
                project_totals[project_name]['resources'] += project_data['resource_count']
        
        if project_totals:
            project_table = Table(title="\nCost by Project")
            project_table.add_column("Project", style="cyan")
            project_table.add_column("Total Cost", style="green")
            project_table.add_column("Services", style="yellow")
            project_table.add_column("Resources", style="white")
            
            # Sort by cost descending
            sorted_projects = sorted(project_totals.items(), key=lambda x: x[1]['cost'], reverse=True)
            
            for project_name, data in sorted_projects:
                services_list = ', '.join(sorted(data['services']))
                project_table.add_row(
                    project_name,
                    f"${data['cost']:,.2f}",
                    services_list,
                    str(data['resources'])
                )
            
            console.print(project_table)
    
    def _generate_csv_report(self, all_costs: List[Dict]) -> str:
        """Generate CSV report for all costs"""
        csv_lines = []
        
        # Header
        csv_lines.append("Account,Service,Category,Cost,Period,Project")
        
        # Data rows
        for cost_data in all_costs:
            account = cost_data['account']
            period = cost_data['period']
            
            for service, amount in cost_data['services'].items():
                category = 'Unknown'
                if 'service_details' in cost_data and service in cost_data['service_details']:
                    category = cost_data['service_details'][service]['category']
                elif service in self.config['ai_services']:
                    category = self.config['ai_services'][service]['category']
                
                # Find projects using this service
                projects = []
                for project_name, project_data in cost_data.get('projects', {}).items():
                    if service in project_data.get('services', {}):
                        projects.append(project_name)
                
                project_str = ';'.join(projects) if projects else 'Unassigned'
                csv_lines.append(f'"{account}","{service}","{category}",{amount:.2f},"{period}","{project_str}"')
        
        return '\n'.join(csv_lines)

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal objects"""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)