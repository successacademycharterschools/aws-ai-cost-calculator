#!/usr/bin/env python3
"""
AI Service Discovery Module
Automatically discovers AI-related AWS resources
"""

import re
from typing import Dict, List, Set, Tuple
from datetime import datetime
import boto3
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class AIServiceDiscovery:
    def __init__(self):
        # AI service patterns - Updated to catch specific resources
        self.ai_patterns = {
            'lambda': [
                r'.*-ai-.*',
                r'.*ask-eva.*',
                r'.*iep.*',
                r'.*iepreport.*',
                r'.*resume-.*',
                r'.*knockout.*',
                r'.*scoring.*',
                r'.*financial-aid.*',
                r'sa-ai-.*',
                r'.*querykb.*',
                r'.*iep_performance.*'
            ],
            's3': [
                r'sa-ai-.*',
                r'.*-ai-.*',
                r'.*-modeltraining.*',
                r'.*modeltraining.*',
                r'.*ask-eva.*',
                r'.*resume-.*',
                r'.*iep.*'
            ],
            'dynamodb': [
                r'.*_ai_.*',
                r'.*-ai-.*',
                r'.*conversation.*',
                r'.*chat.*',
                r'sa_ai_.*'  # Added to catch sa_ai_ask_eva_conversation_history
            ],
            'bedrock': [
                r'.*eva.*',
                r'.*-ai-.*',
                r'.*quick-start.*',
                r'askk-eva.*',  # To catch typo in knowledge base name
                r'.*knowledge.*base.*',
                r'.*agent.*'
            ],
            'tags': {
                'Project': ['AskEva', 'IEPReport', 'ResumeKnockout', 'ResumeScoring', 'FinancialAid'],
                'project': ['ask-eva', 'iep-report', 'resume-knockout', 'resume-scoring', 'financial-aid'],
                'Environment': ['AI', 'ML'],
                'Service': ['AI', 'MachineLearning']
            }
        }
        
        # Services that are 100% AI-related
        self.ai_only_services = ['bedrock', 'kendra', 'sagemaker', 'comprehend', 'textract', 'rekognition']
        
        # Project mappings
        self.projects = {
            'ask-eva': 'Ask Eva',
            'iep-report': 'IEP Report',
            'resume-knockout': 'Resume Knockout',
            'resume-scoring': 'Resume Scoring',
            'financial-aid': 'Financial Aid'
        }
    
    def discover_all_services(self, session: boto3.Session, account_name: str, additional_services: List[str] = None) -> Dict:
        """Discover all AI-related services in an account"""
        discoveries = {
            'account': account_name,
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {
                'total_ai_resources': 0,
                'services_found': set()
            }
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Lambda Functions
            task = progress.add_task(f"[cyan]Scanning Lambda functions in {account_name}...", total=None)
            lambda_resources = self.discover_lambda_functions(session)
            if lambda_resources:
                discoveries['services']['lambda'] = lambda_resources
                discoveries['summary']['total_ai_resources'] += len(lambda_resources)
                discoveries['summary']['services_found'].add('lambda')
            progress.update(task, completed=True)
            
            # S3 Buckets
            task = progress.add_task(f"[cyan]Scanning S3 buckets in {account_name}...", total=None)
            s3_resources = self.discover_s3_buckets(session)
            if s3_resources:
                discoveries['services']['s3'] = s3_resources
                discoveries['summary']['total_ai_resources'] += len(s3_resources)
                discoveries['summary']['services_found'].add('s3')
            progress.update(task, completed=True)
            
            # DynamoDB Tables
            task = progress.add_task(f"[cyan]Scanning DynamoDB tables in {account_name}...", total=None)
            dynamodb_resources = self.discover_dynamodb_tables(session)
            if dynamodb_resources:
                discoveries['services']['dynamodb'] = dynamodb_resources
                discoveries['summary']['total_ai_resources'] += len(dynamodb_resources)
                discoveries['summary']['services_found'].add('dynamodb')
            progress.update(task, completed=True)
            
            # Bedrock Resources
            task = progress.add_task(f"[cyan]Scanning Bedrock resources in {account_name}...", total=None)
            bedrock_resources = self.discover_bedrock_resources(session)
            if bedrock_resources:
                discoveries['services']['bedrock'] = bedrock_resources
                discoveries['summary']['total_ai_resources'] += len(bedrock_resources['models']) + len(bedrock_resources['knowledge_bases'])
                discoveries['summary']['services_found'].add('bedrock')
            progress.update(task, completed=True)
            
            # API Gateway
            task = progress.add_task(f"[cyan]Scanning API Gateway in {account_name}...", total=None)
            api_resources = self.discover_api_gateway(session)
            if api_resources:
                discoveries['services']['apigateway'] = api_resources
                discoveries['summary']['total_ai_resources'] += len(api_resources)
                discoveries['summary']['services_found'].add('apigateway')
            progress.update(task, completed=True)
            
            # Additional Services (SNS, EventBridge, etc.)
            if additional_services:
                for service in additional_services:
                    if service == 'sns':
                        task = progress.add_task(f"[cyan]Scanning SNS topics in {account_name}...", total=None)
                        sns_resources = self.discover_sns_topics(session)
                        if sns_resources:
                            discoveries['services']['sns'] = sns_resources
                            discoveries['summary']['total_ai_resources'] += len(sns_resources)
                            discoveries['summary']['services_found'].add('sns')
                        progress.update(task, completed=True)
                    
                    elif service == 'events':
                        task = progress.add_task(f"[cyan]Scanning EventBridge rules in {account_name}...", total=None)
                        eventbridge_resources = self.discover_eventbridge_rules(session)
                        if eventbridge_resources:
                            discoveries['services']['eventbridge'] = eventbridge_resources
                            discoveries['summary']['total_ai_resources'] += len(eventbridge_resources)
                            discoveries['summary']['services_found'].add('eventbridge')
                        progress.update(task, completed=True)
        
        # Convert set to list for JSON serialization
        discoveries['summary']['services_found'] = list(discoveries['summary']['services_found'])
        
        return discoveries
    
    def _matches_patterns(self, name: str, patterns: List[str]) -> bool:
        """Check if name matches any AI patterns"""
        name_lower = name.lower()
        for pattern in patterns:
            if re.match(pattern, name_lower):
                return True
        return False
    
    def _identify_project(self, name: str, tags: Dict = None) -> str:
        """Identify which AI project a resource belongs to"""
        name_lower = name.lower()
        
        # Check tags first
        if tags:
            for tag_key, tag_value in tags.items():
                if tag_key in ['Project', 'project']:
                    return tag_value
        
        # Check name patterns
        for project_key, project_name in self.projects.items():
            if project_key in name_lower:
                return project_name
        
        return 'Unknown'
    
    def discover_lambda_functions(self, session: boto3.Session) -> List[Dict]:
        """Discover AI-related Lambda functions"""
        lambda_client = session.client('lambda')
        ai_functions = []
        
        try:
            paginator = lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page.get('Functions', []):
                    function_name = function['FunctionName']
                    
                    # Check if it matches AI patterns
                    if self._matches_patterns(function_name, self.ai_patterns['lambda']):
                        # Get tags
                        tags = {}
                        try:
                            tag_response = lambda_client.list_tags(Resource=function['FunctionArn'])
                            tags = tag_response.get('Tags', {})
                        except:
                            pass
                        
                        ai_functions.append({
                            'name': function_name,
                            'arn': function['FunctionArn'],
                            'runtime': function.get('Runtime', 'Unknown'),
                            'memory': function.get('MemorySize', 0),
                            'project': self._identify_project(function_name, tags),
                            'tags': tags
                        })
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list Lambda functions: {e}[/yellow]")
        
        return ai_functions
    
    def discover_s3_buckets(self, session: boto3.Session) -> List[Dict]:
        """Discover AI-related S3 buckets"""
        s3_client = session.client('s3')
        ai_buckets = []
        
        try:
            response = s3_client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                if self._matches_patterns(bucket_name, self.ai_patterns['s3']):
                    # Get bucket tags
                    tags = {}
                    try:
                        tag_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
                        tags = {tag['Key']: tag['Value'] for tag in tag_response.get('TagSet', [])}
                    except:
                        pass
                    
                    # Get bucket size (approximate)
                    size_bytes = 0
                    try:
                        # This is expensive, so we'll skip for now
                        # Could implement with CloudWatch metrics instead
                        pass
                    except:
                        pass
                    
                    ai_buckets.append({
                        'name': bucket_name,
                        'creation_date': bucket['CreationDate'].isoformat(),
                        'project': self._identify_project(bucket_name, tags),
                        'tags': tags,
                        'size_bytes': size_bytes
                    })
        
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list S3 buckets: {e}[/yellow]")
        
        return ai_buckets
    
    def discover_dynamodb_tables(self, session: boto3.Session) -> List[Dict]:
        """Discover AI-related DynamoDB tables"""
        dynamodb_client = session.client('dynamodb')
        ai_tables = []
        
        try:
            paginator = dynamodb_client.get_paginator('list_tables')
            
            for page in paginator.paginate():
                for table_name in page.get('TableNames', []):
                    if self._matches_patterns(table_name, self.ai_patterns['dynamodb']):
                        # Get table details
                        try:
                            table_info = dynamodb_client.describe_table(TableName=table_name)
                            table_details = table_info['Table']
                            
                            # Get tags
                            tags = {}
                            try:
                                tag_response = dynamodb_client.list_tags_of_resource(
                                    ResourceArn=table_details['TableArn']
                                )
                                tags = {tag['Key']: tag['Value'] for tag in tag_response.get('Tags', [])}
                            except:
                                pass
                            
                            ai_tables.append({
                                'name': table_name,
                                'arn': table_details['TableArn'],
                                'status': table_details['TableStatus'],
                                'item_count': table_details.get('ItemCount', 0),
                                'size_bytes': table_details.get('TableSizeBytes', 0),
                                'project': self._identify_project(table_name, tags),
                                'tags': tags
                            })
                        except:
                            ai_tables.append({
                                'name': table_name,
                                'project': self._identify_project(table_name),
                                'error': 'Could not get table details'
                            })
        
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list DynamoDB tables: {e}[/yellow]")
        
        return ai_tables
    
    def discover_bedrock_resources(self, session: boto3.Session) -> Dict:
        """Discover Bedrock models and knowledge bases"""
        bedrock_resources = {
            'models': [],
            'knowledge_bases': [],
            'agents': []
        }
        
        try:
            bedrock_client = session.client('bedrock', region_name='us-east-1')
            bedrock_agent_client = session.client('bedrock-agent', region_name='us-east-1')
            
            # List custom models
            try:
                response = bedrock_client.list_custom_models()
                for model in response.get('modelSummaries', []):
                    bedrock_resources['models'].append({
                        'name': model['modelName'],
                        'arn': model['modelArn'],
                        'base_model': model.get('baseModelName', 'Unknown')
                    })
            except:
                pass
            
            # List knowledge bases
            try:
                response = bedrock_agent_client.list_knowledge_bases()
                for kb in response.get('knowledgeBaseSummaries', []):
                    bedrock_resources['knowledge_bases'].append({
                        'name': kb['name'],
                        'id': kb['knowledgeBaseId'],
                        'status': kb['status'],
                        'project': self._identify_project(kb['name'])
                    })
            except:
                pass
            
            # List agents
            try:
                response = bedrock_agent_client.list_agents()
                for agent in response.get('agentSummaries', []):
                    bedrock_resources['agents'].append({
                        'name': agent['agentName'],
                        'id': agent['agentId'],
                        'status': agent['agentStatus'],
                        'project': self._identify_project(agent['agentName'])
                    })
            except:
                pass
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list Bedrock resources: {e}[/yellow]")
        
        return bedrock_resources
    
    def discover_api_gateway(self, session: boto3.Session) -> List[Dict]:
        """Discover AI-related API Gateway endpoints"""
        api_client = session.client('apigateway')
        ai_apis = []
        
        try:
            # REST APIs
            response = api_client.get_rest_apis()
            for api in response.get('items', []):
                api_name = api['name']
                if self._matches_patterns(api_name, self.ai_patterns['lambda']):  # Use same patterns
                    tags = api.get('tags', {})
                    ai_apis.append({
                        'name': api_name,
                        'id': api['id'],
                        'type': 'REST',
                        'project': self._identify_project(api_name, tags),
                        'tags': tags
                    })
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list API Gateway resources: {e}[/yellow]")
        
        return ai_apis
    
    def discover_sns_topics(self, session: boto3.Session) -> List[Dict]:
        """Discover AI-related SNS topics"""
        sns_client = session.client('sns')
        ai_topics = []
        
        try:
            paginator = sns_client.get_paginator('list_topics')
            
            for page in paginator.paginate():
                for topic in page.get('Topics', []):
                    topic_arn = topic['TopicArn']
                    # Extract topic name from ARN
                    topic_name = topic_arn.split(':')[-1]
                    
                    if self._matches_patterns(topic_name, self.ai_patterns['lambda']):  # Use same patterns
                        # Get topic attributes and tags
                        tags = {}
                        try:
                            tag_response = sns_client.list_tags_for_resource(ResourceArn=topic_arn)
                            tags = {tag['Key']: tag['Value'] for tag in tag_response.get('Tags', [])}
                        except:
                            pass
                        
                        ai_topics.append({
                            'name': topic_name,
                            'arn': topic_arn,
                            'project': self._identify_project(topic_name, tags),
                            'tags': tags
                        })
        
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list SNS topics: {e}[/yellow]")
        
        return ai_topics
    
    def discover_eventbridge_rules(self, session: boto3.Session) -> List[Dict]:
        """Discover AI-related EventBridge rules"""
        events_client = session.client('events')
        ai_rules = []
        
        try:
            # List all event buses
            buses = ['default']  # Start with default bus
            try:
                bus_response = events_client.list_event_buses()
                buses.extend([bus['Name'] for bus in bus_response.get('EventBuses', []) if bus['Name'] != 'default'])
            except:
                pass
            
            for bus_name in buses:
                try:
                    paginator = events_client.get_paginator('list_rules')
                    for page in paginator.paginate(EventBusName=bus_name):
                        for rule in page.get('Rules', []):
                            rule_name = rule['Name']
                            
                            if self._matches_patterns(rule_name, self.ai_patterns['lambda']):
                                # Get rule details and tags
                                tags = {}
                                try:
                                    tag_response = events_client.list_tags_for_resource(ResourceArn=rule['Arn'])
                                    tags = {tag['Key']: tag['Value'] for tag in tag_response.get('Tags', [])}
                                except:
                                    pass
                                
                                ai_rules.append({
                                    'name': rule_name,
                                    'arn': rule['Arn'],
                                    'bus': bus_name,
                                    'state': rule.get('State', 'Unknown'),
                                    'project': self._identify_project(rule_name, tags),
                                    'tags': tags
                                })
                except:
                    pass
        
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list EventBridge rules: {e}[/yellow]")
        
        return ai_rules
    
    def print_discovery_summary(self, discoveries: List[Dict]):
        """Print a summary of discovered resources"""
        console.print("\n[bold green]AI Service Discovery Summary[/bold green]\n")
        
        total_resources = 0
        
        for discovery in discoveries:
            account = discovery['account']
            console.print(f"[bold]{account}:[/bold]")
            
            if discovery['summary']['total_ai_resources'] == 0:
                console.print("  [yellow]No AI resources found[/yellow]")
                continue
            
            # Create summary table
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Service", style="cyan")
            table.add_column("Count", style="green")
            table.add_column("Examples", style="dim")
            
            for service, resources in discovery['services'].items():
                if service == 'bedrock':
                    count = len(resources.get('models', [])) + len(resources.get('knowledge_bases', [])) + len(resources.get('agents', []))
                    examples = []
                    if resources.get('knowledge_bases'):
                        examples.append(resources['knowledge_bases'][0]['name'])
                    if resources.get('agents'):
                        examples.append(resources['agents'][0]['name'])
                else:
                    count = len(resources)
                    examples = [r['name'] for r in resources[:2]]
                
                if count > 0:
                    table.add_row(
                        service.upper(),
                        str(count),
                        ', '.join(examples[:2]) + ('...' if count > 2 else '')
                    )
                    total_resources += count
            
            console.print(table)
            console.print()
        
        console.print(f"[bold green]Total AI resources found: {total_resources}[/bold green]\n")