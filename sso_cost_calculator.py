#!/usr/bin/env python3
"""
AWS AI Cost Calculator with SSO Support
Main calculator that uses SSO authentication and auto-discovery
"""

import os
import json
import csv
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple
import boto3
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.columns import Columns

from sso_auth import SSOAuthenticator
from ai_service_discovery import AIServiceDiscovery

console = Console()

class SSOCostCalculator:
    def __init__(self):
        self.authenticator = SSOAuthenticator()
        self.discovery = AIServiceDiscovery()
        self.cost_data = {}
        self.discovered_resources = []
        
    def calculate_costs_for_resources(self, session: boto3.Session, account_name: str, 
                                    discovered: Dict, start_date: str = None, end_date: str = None) -> Dict:
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
            'total': Decimal('0')
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
            
            # Lambda costs
            if 'lambda' in discovered['services']:
                task = progress.add_task(f"[cyan]Calculating Lambda costs for {account_name}...", total=None)
                lambda_cost = self._calculate_lambda_costs(
                    ce_client, discovered['services']['lambda'], 
                    start_date, ce_end_date, account_id
                )
                if lambda_cost > 0:
                    costs['services']['lambda'] = lambda_cost
                    costs['total'] += lambda_cost
                progress.update(task, completed=True)
            
            # S3 costs
            if 's3' in discovered['services']:
                task = progress.add_task(f"[cyan]Calculating S3 costs for {account_name}...", total=None)
                s3_cost = self._calculate_s3_costs(
                    ce_client, discovered['services']['s3'],
                    start_date, ce_end_date, account_id
                )
                if s3_cost > 0:
                    costs['services']['s3'] = s3_cost
                    costs['total'] += s3_cost
                progress.update(task, completed=True)
            
            # DynamoDB costs
            if 'dynamodb' in discovered['services']:
                task = progress.add_task(f"[cyan]Calculating DynamoDB costs for {account_name}...", total=None)
                dynamodb_cost = self._calculate_dynamodb_costs(
                    ce_client, discovered['services']['dynamodb'],
                    start_date, ce_end_date, account_id
                )
                if dynamodb_cost > 0:
                    costs['services']['dynamodb'] = dynamodb_cost
                    costs['total'] += dynamodb_cost
                progress.update(task, completed=True)
            
            # Bedrock costs (100% AI)
            task = progress.add_task(f"[cyan]Calculating Bedrock costs for {account_name}...", total=None)
            bedrock_cost = self._calculate_service_costs(
                ce_client, 'Amazon Bedrock', start_date, ce_end_date, account_id
            )
            if bedrock_cost > 0:
                costs['services']['bedrock'] = bedrock_cost
                costs['total'] += bedrock_cost
            progress.update(task, completed=True)
            
            # Kendra costs (100% AI)
            task = progress.add_task(f"[cyan]Calculating Kendra costs for {account_name}...", total=None)
            kendra_cost = self._calculate_service_costs(
                ce_client, 'Amazon Kendra', start_date, ce_end_date, account_id
            )
            if kendra_cost > 0:
                costs['services']['kendra'] = kendra_cost
                costs['total'] += kendra_cost
            progress.update(task, completed=True)
        
        # Calculate project-level costs
        self._calculate_project_costs(costs, discovered)
        
        return costs
    
    def _calculate_lambda_costs(self, ce_client, lambda_functions: List[Dict],
                              start_date: str, end_date: str, account_id: str) -> Decimal:
        """Calculate costs for specific Lambda functions"""
        if not lambda_functions:
            return Decimal('0')
        
        try:
            # Get total Lambda costs
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
            
            total_cost = Decimal('0')
            for result in response.get('ResultsByTime', []):
                amount = result['Total']['UnblendedCost']['Amount']
                total_cost += Decimal(amount)
            
            # For now, return full Lambda cost if we have AI functions
            # In production, you'd want to use CloudWatch metrics for more accuracy
            return total_cost
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not calculate Lambda costs: {e}[/yellow]")
            return Decimal('0')
    
    def _calculate_s3_costs(self, ce_client, s3_buckets: List[Dict],
                          start_date: str, end_date: str, account_id: str) -> Decimal:
        """Calculate costs for specific S3 buckets"""
        if not s3_buckets:
            return Decimal('0')
        
        try:
            # Get S3 costs with bucket-level granularity if possible
            bucket_names = [b['name'] for b in s3_buckets]
            
            # Try to get costs by bucket using tags
            total_cost = Decimal('0')
            
            # First, try tag-based filtering
            for bucket in s3_buckets:
                if bucket.get('tags'):
                    for tag_key, tag_value in bucket['tags'].items():
                        if tag_key in ['Project', 'project']:
                            try:
                                response = ce_client.get_cost_and_usage(
                                    TimePeriod={'Start': start_date, 'End': end_date},
                                    Granularity='MONTHLY',
                                    Metrics=['UnblendedCost'],
                                    Filter={
                                        'And': [
                                            {'Dimensions': {'Key': 'SERVICE', 'Values': ['Amazon Simple Storage Service']}},
                                            {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [account_id]}},
                                            {'Tags': {'Key': tag_key, 'Values': [tag_value]}}
                                        ]
                                    }
                                )
                                
                                for result in response.get('ResultsByTime', []):
                                    amount = result['Total']['UnblendedCost']['Amount']
                                    total_cost += Decimal(amount)
                                break
                            except:
                                pass
            
            # If no tag-based costs found, estimate based on total S3 costs
            if total_cost == 0:
                response = ce_client.get_cost_and_usage(
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
                
                total_s3_cost = Decimal('0')
                for result in response.get('ResultsByTime', []):
                    amount = result['Total']['UnblendedCost']['Amount']
                    total_s3_cost += Decimal(amount)
                
                # Estimate AI portion (you can adjust this percentage)
                total_cost = total_s3_cost * Decimal('0.3')  # Assume 30% for AI
            
            return total_cost
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not calculate S3 costs: {e}[/yellow]")
            return Decimal('0')
    
    def _calculate_dynamodb_costs(self, ce_client, dynamodb_tables: List[Dict],
                                start_date: str, end_date: str, account_id: str) -> Decimal:
        """Calculate costs for specific DynamoDB tables"""
        if not dynamodb_tables:
            return Decimal('0')
        
        try:
            # Similar approach to S3
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
                total_cost += Decimal(amount)
            
            # Return full cost if we have AI tables
            return total_cost
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not calculate DynamoDB costs: {e}[/yellow]")
            return Decimal('0')
    
    def _calculate_service_costs(self, ce_client, service_name: str,
                               start_date: str, end_date: str, account_id: str) -> Decimal:
        """Calculate costs for a specific AWS service"""
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
            return Decimal('0')
    
    def _calculate_project_costs(self, costs: Dict, discovered: Dict):
        """Aggregate costs by project"""
        projects = {}
        
        # Go through each service's resources
        for service_name, resources in discovered['services'].items():
            if service_name == 'bedrock':
                # Handle Bedrock's nested structure
                for resource in resources.get('knowledge_bases', []):
                    project = resource.get('project', 'Unknown')
                    if project not in projects:
                        projects[project] = Decimal('0')
                    # Allocate portion of Bedrock costs
                    if 'bedrock' in costs['services']:
                        projects[project] += costs['services']['bedrock'] / 10  # Simple allocation
            else:
                for resource in resources:
                    project = resource.get('project', 'Unknown')
                    if project not in projects:
                        projects[project] = Decimal('0')
                    # Add portion of service cost to project
                    if service_name in costs['services']:
                        service_cost = costs['services'][service_name]
                        # Simple equal distribution for now
                        projects[project] += service_cost / len(resources)
        
        costs['projects'] = projects
    
    def print_cost_summary(self, all_costs: List[Dict]):
        """Print formatted cost summary"""
        console.print("\n[bold green]AWS AI Cost Analysis Summary[/bold green]\n")
        
        grand_total = Decimal('0')
        
        for cost_data in all_costs:
            account = cost_data['account']
            total = cost_data['total']
            grand_total += total
            
            # Account panel
            panel_content = f"[bold]Period:[/bold] {cost_data['period']}\n"
            panel_content += f"[bold]Total Cost:[/bold] [green]${total:.2f}[/green]\n\n"
            
            # Service breakdown
            if cost_data['services']:
                panel_content += "[bold]Service Breakdown:[/bold]\n"
                for service, amount in sorted(cost_data['services'].items()):
                    panel_content += f"  {service.upper()}: ${amount:.2f}\n"
            
            # Project breakdown
            if cost_data.get('projects'):
                panel_content += "\n[bold]Project Breakdown:[/bold]\n"
                for project, amount in sorted(cost_data['projects'].items()):
                    if amount > 0:
                        panel_content += f"  {project}: ${amount:.2f}\n"
            
            console.print(Panel(panel_content, title=f"[bold cyan]{account}[/bold cyan]"))
        
        # Grand total
        console.print(f"\n[bold green]Total AI Costs (All Accounts): ${grand_total:.2f}[/bold green]")
        
        # Daily average
        days_in_month = datetime.now().day
        daily_avg = grand_total / days_in_month if days_in_month > 0 else Decimal('0')
        console.print(f"[bold]Daily Average: ${daily_avg:.2f}[/bold]")
        
        # Projection for 57 schools
        console.print(f"\n[bold yellow]Projection for 57 schools: ${grand_total * 57:.2f}/month[/bold yellow]")
    
    def export_results(self, all_costs: List[Dict], discoveries: List[Dict]):
        """Export results to CSV"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export cost summary
        cost_filename = f'ai_costs_summary_{timestamp}.csv'
        with open(cost_filename, 'w', newline='') as csvfile:
            fieldnames = ['Account', 'Service', 'Cost', 'Project', 'Period']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for cost_data in all_costs:
                account = cost_data['account']
                period = cost_data['period']
                
                # Write service costs
                for service, amount in cost_data['services'].items():
                    writer.writerow({
                        'Account': account,
                        'Service': service.upper(),
                        'Cost': f"${amount:.2f}",
                        'Project': 'All Projects',
                        'Period': period
                    })
                
                # Write project costs
                for project, amount in cost_data.get('projects', {}).items():
                    if amount > 0:
                        writer.writerow({
                            'Account': account,
                            'Service': 'Multiple',
                            'Cost': f"${amount:.2f}",
                            'Project': project,
                            'Period': period
                        })
        
        # Export resource discovery
        discovery_filename = f'ai_resources_{timestamp}.json'
        with open(discovery_filename, 'w') as f:
            json.dump(discoveries, f, indent=2, default=str)
        
        console.print(f"\n[green]✓[/green] Results exported to:")
        console.print(f"  - {cost_filename}")
        console.print(f"  - {discovery_filename}")
    
    def run(self):
        """Main execution flow"""
        console.print("[bold blue]AWS AI Cost Calculator with SSO[/bold blue]")
        console.print("[dim]Using Okta-based AWS SSO authentication[/dim]\n")
        
        try:
            # Authenticate and get sessions
            sessions = self.authenticator.get_authenticated_sessions()
            
            if not sessions:
                console.print("[red]No authenticated sessions available[/red]")
                return
            
            # Discover resources in each account
            console.print("\n[bold]Discovering AI Resources...[/bold]\n")
            discoveries = []
            
            for account_name, session in sessions:
                discovery = self.discovery.discover_all_services(session, account_name)
                discoveries.append(discovery)
                self.discovered_resources.append(discovery)
            
            # Print discovery summary
            self.discovery.print_discovery_summary(discoveries)
            
            # Calculate costs
            console.print("\n[bold]Calculating Costs...[/bold]\n")
            all_costs = []
            
            for (account_name, session), discovery in zip(sessions, discoveries):
                costs = self.calculate_costs_for_resources(session, account_name, discovery)
                all_costs.append(costs)
                self.cost_data[account_name] = costs
            
            # Print cost summary
            self.print_cost_summary(all_costs)
            
            # Export results
            self.export_results(all_costs, discoveries)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise


if __name__ == "__main__":
    calculator = SSOCostCalculator()
    calculator.run()