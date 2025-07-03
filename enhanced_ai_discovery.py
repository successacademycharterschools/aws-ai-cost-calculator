#!/usr/bin/env python3
"""
Enhanced AI Service Discovery Module
Discovers ALL AWS AI/ML services and maps them to projects
"""

import json
import re
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from decimal import Decimal

console = Console()

class EnhancedAIDiscovery:
    def __init__(self):
        # Load AI services configuration
        with open('ai_services_config.json', 'r') as f:
            self.config = json.load(f)
        
        self.ai_services = self.config['ai_services']
        self.project_mappings = self.config['project_mappings']
        self.tag_keys = self.config['tag_keys']
        
    def discover_all_ai_resources(self, session: boto3.Session, account_name: str, 
                                 additional_services: List[str] = None) -> Dict:
        """Discover all AI resources across all AI services"""
        discoveries = {
            'account': account_name,
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'projects': {},
            'summary': {
                'total_ai_resources': 0,
                'services_found': set(),
                'projects_found': set(),
                'untagged_resources': 0
            }
        }
        
        # Get enabled services
        enabled_services = []
        for service_key, service_info in self.ai_services.items():
            if service_info.get('enabled_by_default', False):
                enabled_services.append(service_key)
        
        # Add any additional services requested
        if additional_services:
            for service in additional_services:
                if service in self.ai_services and service not in enabled_services:
                    enabled_services.append(service)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Discover resources for each enabled AI service
            for service_key in enabled_services:
                service_info = self.ai_services[service_key]
                task = progress.add_task(
                    f"[cyan]Scanning {service_info['cost_explorer_name']} in {account_name}...", 
                    total=None
                )
                
                try:
                    # Call the appropriate discovery method
                    discovery_method = getattr(self, f'discover_{service_key}', None)
                    if discovery_method:
                        resources = discovery_method(session)
                        if resources:
                            discoveries['services'][service_key] = {
                                'resources': resources,
                                'count': len(resources),
                                'service_info': service_info
                            }
                            discoveries['summary']['total_ai_resources'] += len(resources)
                            discoveries['summary']['services_found'].add(service_key)
                            
                            # Map resources to projects
                            self._map_resources_to_projects(service_key, resources, discoveries)
                    else:
                        # Fallback to generic resource discovery
                        console.print(f"[yellow]No specific discovery for {service_key}, using generic method[/yellow]")
                        
                except Exception as e:
                    console.print(f"[red]Error discovering {service_key}: {str(e)}[/red]")
                
                progress.update(task, completed=True)
            
            # Also discover traditional resources (Lambda, S3, DynamoDB) with AI patterns
            task = progress.add_task(f"[cyan]Scanning Lambda functions for AI resources...", total=None)
            lambda_resources = self.discover_lambda_ai_resources(session)
            if lambda_resources:
                discoveries['services']['lambda'] = {
                    'resources': lambda_resources,
                    'count': len(lambda_resources),
                    'service_info': {'category': 'Compute', 'description': 'AI-related Lambda functions'}
                }
                discoveries['summary']['total_ai_resources'] += len(lambda_resources)
                self._map_resources_to_projects('lambda', lambda_resources, discoveries)
            progress.update(task, completed=True)
            
            task = progress.add_task(f"[cyan]Scanning S3 buckets for AI resources...", total=None)
            s3_resources = self.discover_s3_ai_resources(session)
            if s3_resources:
                discoveries['services']['s3'] = {
                    'resources': s3_resources,
                    'count': len(s3_resources),
                    'service_info': {'category': 'Storage', 'description': 'AI-related S3 buckets'}
                }
                discoveries['summary']['total_ai_resources'] += len(s3_resources)
                self._map_resources_to_projects('s3', s3_resources, discoveries)
            progress.update(task, completed=True)
            
            task = progress.add_task(f"[cyan]Scanning DynamoDB tables for AI resources...", total=None)
            dynamodb_resources = self.discover_dynamodb_ai_resources(session)
            if dynamodb_resources:
                discoveries['services']['dynamodb'] = {
                    'resources': dynamodb_resources,
                    'count': len(dynamodb_resources),
                    'service_info': {'category': 'Database', 'description': 'AI-related DynamoDB tables'}
                }
                discoveries['summary']['total_ai_resources'] += len(dynamodb_resources)
                self._map_resources_to_projects('dynamodb', dynamodb_resources, discoveries)
            progress.update(task, completed=True)
        
        # Convert sets to lists for JSON serialization
        discoveries['summary']['services_found'] = list(discoveries['summary']['services_found'])
        discoveries['summary']['projects_found'] = list(discoveries['summary']['projects_found'])
        
        return discoveries
    
    def _map_resources_to_projects(self, service_key: str, resources: List[Dict], discoveries: Dict):
        """Map resources to projects based on tags and naming patterns"""
        for resource in resources:
            project = resource.get('project', 'Unknown')
            
            if project not in discoveries['projects']:
                discoveries['projects'][project] = {
                    'name': project,
                    'services': {},
                    'total_resources': 0
                }
            
            if service_key not in discoveries['projects'][project]['services']:
                discoveries['projects'][project]['services'][service_key] = []
            
            discoveries['projects'][project]['services'][service_key].append(resource)
            discoveries['projects'][project]['total_resources'] += 1
            
            if project != 'Unknown':
                discoveries['summary']['projects_found'].add(project)
            else:
                discoveries['summary']['untagged_resources'] += 1
    
    def _get_resource_tags(self, client, method_name: str, **kwargs) -> Dict:
        """Generic method to get resource tags"""
        try:
            response = getattr(client, method_name)(**kwargs)
            return response.get('Tags', {})
        except:
            return {}
    
    def _identify_project(self, resource_name: str, tags: Dict = None) -> str:
        """Identify project from tags or resource name"""
        # Check tags first
        if tags:
            for tag_category in self.tag_keys['project']:
                if tag_category in tags:
                    return tags[tag_category]
        
        # Check resource name patterns
        name_lower = resource_name.lower()
        for project_key, project_info in self.project_mappings.items():
            if project_key in name_lower:
                return project_info['name']
        
        return 'Unknown'
    
    # Bedrock Discovery
    def discover_bedrock(self, session: boto3.Session) -> List[Dict]:
        """Discover Bedrock agents and knowledge bases"""
        resources = []
        
        # Try multiple regions as Bedrock might be regional
        regions = ['us-east-1', 'us-west-2']
        
        for region in regions:
            try:
                bedrock_agent = session.client('bedrock-agent', region_name=region)
                
                # List knowledge bases
                try:
                    kb_response = bedrock_agent.list_knowledge_bases()
                    for kb in kb_response.get('knowledgeBaseSummaries', []):
                        resources.append({
                            'type': 'knowledge_base',
                            'name': kb['name'],
                            'id': kb['knowledgeBaseId'],
                            'status': kb['status'],
                            'region': region,
                            'project': self._identify_project(kb['name'])
                        })
                except:
                    pass
                
                # List agents
                try:
                    agents_response = bedrock_agent.list_agents()
                    for agent in agents_response.get('agentSummaries', []):
                        resources.append({
                            'type': 'agent',
                            'name': agent['agentName'],
                            'id': agent['agentId'],
                            'status': agent['agentStatus'],
                            'region': region,
                            'project': self._identify_project(agent['agentName'])
                        })
                except:
                    pass
                
            except Exception as e:
                if 'AccessDeniedException' not in str(e):
                    console.print(f"[yellow]Could not access Bedrock in {region}: {str(e)}[/yellow]")
        
        return resources
    
    # SageMaker Discovery
    def discover_sagemaker(self, session: boto3.Session) -> List[Dict]:
        """Discover SageMaker resources"""
        resources = []
        sagemaker = session.client('sagemaker')
        
        # List endpoints
        try:
            endpoints = sagemaker.list_endpoints()
            for endpoint in endpoints.get('Endpoints', []):
                tags = self._get_resource_tags(
                    sagemaker, 'list_tags',
                    ResourceArn=endpoint['EndpointArn']
                )
                resources.append({
                    'type': 'endpoint',
                    'name': endpoint['EndpointName'],
                    'arn': endpoint['EndpointArn'],
                    'status': endpoint['EndpointStatus'],
                    'created': endpoint['CreationTime'].isoformat(),
                    'project': self._identify_project(endpoint['EndpointName'], tags)
                })
        except:
            pass
        
        # List notebook instances
        try:
            notebooks = sagemaker.list_notebook_instances()
            for notebook in notebooks.get('NotebookInstances', []):
                tags = self._get_resource_tags(
                    sagemaker, 'list_tags',
                    ResourceArn=notebook['NotebookInstanceArn']
                )
                resources.append({
                    'type': 'notebook_instance',
                    'name': notebook['NotebookInstanceName'],
                    'arn': notebook['NotebookInstanceArn'],
                    'status': notebook['NotebookInstanceStatus'],
                    'instance_type': notebook['InstanceType'],
                    'project': self._identify_project(notebook['NotebookInstanceName'], tags)
                })
        except:
            pass
        
        # List training jobs (recent ones)
        try:
            training_jobs = sagemaker.list_training_jobs(MaxResults=50)
            for job in training_jobs.get('TrainingJobSummaries', []):
                tags = self._get_resource_tags(
                    sagemaker, 'list_tags',
                    ResourceArn=job['TrainingJobArn']
                )
                resources.append({
                    'type': 'training_job',
                    'name': job['TrainingJobName'],
                    'arn': job['TrainingJobArn'],
                    'status': job['TrainingJobStatus'],
                    'created': job['CreationTime'].isoformat(),
                    'project': self._identify_project(job['TrainingJobName'], tags)
                })
        except:
            pass
        
        return resources
    
    # Comprehend Discovery
    def discover_comprehend(self, session: boto3.Session) -> List[Dict]:
        """Discover Comprehend resources"""
        resources = []
        comprehend = session.client('comprehend')
        
        # List document classifiers
        try:
            classifiers = comprehend.list_document_classifiers()
            for classifier in classifiers.get('DocumentClassifierPropertiesList', []):
                resources.append({
                    'type': 'document_classifier',
                    'name': classifier.get('DocumentClassifierArn', '').split('/')[-1],
                    'arn': classifier['DocumentClassifierArn'],
                    'status': classifier['Status'],
                    'project': self._identify_project(classifier.get('DocumentClassifierArn', ''))
                })
        except:
            pass
        
        # List entity recognizers
        try:
            recognizers = comprehend.list_entity_recognizers()
            for recognizer in recognizers.get('EntityRecognizerPropertiesList', []):
                resources.append({
                    'type': 'entity_recognizer',
                    'name': recognizer.get('EntityRecognizerArn', '').split('/')[-1],
                    'arn': recognizer['EntityRecognizerArn'],
                    'status': recognizer['Status'],
                    'project': self._identify_project(recognizer.get('EntityRecognizerArn', ''))
                })
        except:
            pass
        
        return resources
    
    # Textract Discovery
    def discover_textract(self, session: boto3.Session) -> List[Dict]:
        """Discover Textract resources"""
        # Textract doesn't have persistent resources, but we can check for recent jobs
        # This is a placeholder - in production, you'd track Textract usage through CloudTrail
        return []
    
    # Rekognition Discovery
    def discover_rekognition(self, session: boto3.Session) -> List[Dict]:
        """Discover Rekognition resources"""
        resources = []
        rekognition = session.client('rekognition')
        
        # List collections
        try:
            collections = rekognition.list_collections()
            for collection_id in collections.get('CollectionIds', []):
                resources.append({
                    'type': 'collection',
                    'name': collection_id,
                    'id': collection_id,
                    'project': self._identify_project(collection_id)
                })
        except:
            pass
        
        # List stream processors
        try:
            processors = rekognition.list_stream_processors()
            for processor in processors.get('StreamProcessors', []):
                resources.append({
                    'type': 'stream_processor',
                    'name': processor['Name'],
                    'status': processor.get('Status', 'Unknown'),
                    'project': self._identify_project(processor['Name'])
                })
        except:
            pass
        
        return resources
    
    # Polly Discovery
    def discover_polly(self, session: boto3.Session) -> List[Dict]:
        """Discover Polly resources"""
        resources = []
        polly = session.client('polly')
        
        # List lexicons
        try:
            lexicons = polly.list_lexicons()
            for lexicon in lexicons.get('Lexicons', []):
                resources.append({
                    'type': 'lexicon',
                    'name': lexicon['Name'],
                    'language': lexicon.get('LanguageCode', 'Unknown'),
                    'project': self._identify_project(lexicon['Name'])
                })
        except:
            pass
        
        return resources
    
    # Transcribe Discovery
    def discover_transcribe(self, session: boto3.Session) -> List[Dict]:
        """Discover Transcribe resources"""
        resources = []
        transcribe = session.client('transcribe')
        
        # List vocabularies
        try:
            vocabularies = transcribe.list_vocabularies()
            for vocab in vocabularies.get('Vocabularies', []):
                resources.append({
                    'type': 'vocabulary',
                    'name': vocab['VocabularyName'],
                    'language': vocab['LanguageCode'],
                    'state': vocab['VocabularyState'],
                    'project': self._identify_project(vocab['VocabularyName'])
                })
        except:
            pass
        
        # List language models
        try:
            models = transcribe.list_language_models()
            for model in models.get('Models', []):
                resources.append({
                    'type': 'language_model',
                    'name': model['ModelName'],
                    'language': model['LanguageCode'],
                    'status': model['ModelStatus'],
                    'project': self._identify_project(model['ModelName'])
                })
        except:
            pass
        
        return resources
    
    # Translate Discovery
    def discover_translate(self, session: boto3.Session) -> List[Dict]:
        """Discover Translate resources"""
        resources = []
        translate = session.client('translate')
        
        # List terminologies
        try:
            terminologies = translate.list_terminologies()
            for term in terminologies.get('TerminologyPropertiesList', []):
                resources.append({
                    'type': 'terminology',
                    'name': term['Name'],
                    'arn': term['Arn'],
                    'source_language': term.get('SourceLanguageCode', 'Unknown'),
                    'project': self._identify_project(term['Name'])
                })
        except:
            pass
        
        return resources
    
    # Forecast Discovery
    def discover_forecast(self, session: boto3.Session) -> List[Dict]:
        """Discover Forecast resources"""
        resources = []
        forecast = session.client('forecast')
        
        # List datasets
        try:
            datasets = forecast.list_datasets()
            for dataset in datasets.get('Datasets', []):
                resources.append({
                    'type': 'dataset',
                    'name': dataset['DatasetName'],
                    'arn': dataset['DatasetArn'],
                    'domain': dataset.get('Domain', 'Unknown'),
                    'project': self._identify_project(dataset['DatasetName'])
                })
        except:
            pass
        
        # List predictors
        try:
            predictors = forecast.list_predictors()
            for predictor in predictors.get('Predictors', []):
                resources.append({
                    'type': 'predictor',
                    'name': predictor['PredictorName'],
                    'arn': predictor['PredictorArn'],
                    'status': predictor.get('Status', 'Unknown'),
                    'project': self._identify_project(predictor['PredictorName'])
                })
        except:
            pass
        
        return resources
    
    # Personalize Discovery
    def discover_personalize(self, session: boto3.Session) -> List[Dict]:
        """Discover Personalize resources"""
        resources = []
        personalize = session.client('personalize')
        
        # List dataset groups
        try:
            dataset_groups = personalize.list_dataset_groups()
            for group in dataset_groups.get('datasetGroups', []):
                resources.append({
                    'type': 'dataset_group',
                    'name': group['name'],
                    'arn': group['datasetGroupArn'],
                    'status': group['status'],
                    'project': self._identify_project(group['name'])
                })
        except:
            pass
        
        # List campaigns
        try:
            campaigns = personalize.list_campaigns()
            for campaign in campaigns.get('campaigns', []):
                resources.append({
                    'type': 'campaign',
                    'name': campaign['name'],
                    'arn': campaign['campaignArn'],
                    'status': campaign['status'],
                    'project': self._identify_project(campaign['name'])
                })
        except:
            pass
        
        return resources
    
    # Lex Discovery
    def discover_lex(self, session: boto3.Session) -> List[Dict]:
        """Discover Lex resources"""
        resources = []
        lex = session.client('lexv2-models')
        
        # List bots
        try:
            bots = lex.list_bots()
            for bot in bots.get('botSummaries', []):
                resources.append({
                    'type': 'bot',
                    'name': bot['botName'],
                    'id': bot['botId'],
                    'status': bot['botStatus'],
                    'project': self._identify_project(bot['botName'])
                })
        except:
            pass
        
        return resources
    
    # Kendra Discovery
    def discover_kendra(self, session: boto3.Session) -> List[Dict]:
        """Discover Kendra resources"""
        resources = []
        kendra = session.client('kendra')
        
        # List indexes
        try:
            indexes = kendra.list_indices()
            for index in indexes.get('IndexConfigurationSummaryItems', []):
                tags = self._get_resource_tags(
                    kendra, 'list_tags_for_resource',
                    ResourceARN=f"arn:aws:kendra:{session.region_name}:{session.client('sts').get_caller_identity()['Account']}:index/{index['Id']}"
                )
                resources.append({
                    'type': 'index',
                    'name': index['Name'],
                    'id': index['Id'],
                    'status': index['Status'],
                    'created': index['CreatedAt'].isoformat(),
                    'project': self._identify_project(index['Name'], tags)
                })
        except:
            pass
        
        return resources
    
    # Traditional resource discovery with AI patterns
    def discover_lambda_ai_resources(self, session: boto3.Session) -> List[Dict]:
        """Discover AI-related Lambda functions"""
        lambda_client = session.client('lambda')
        ai_functions = []
        
        # AI patterns for Lambda functions
        ai_patterns = [
            r'.*-ai-.*', r'.*ask-eva.*', r'.*iep.*', r'.*resume-.*',
            r'.*knockout.*', r'.*scoring.*', r'.*financial-aid.*',
            r'sa-ai-.*', r'.*querykb.*', r'.*bedrock.*', r'.*sagemaker.*',
            r'.*comprehend.*', r'.*textract.*', r'.*rekognition.*'
        ]
        
        try:
            paginator = lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page.get('Functions', []):
                    function_name = function['FunctionName']
                    
                    # Check if it matches AI patterns
                    is_ai = False
                    for pattern in ai_patterns:
                        if re.match(pattern, function_name.lower()):
                            is_ai = True
                            break
                    
                    if is_ai:
                        # Get tags
                        tags = {}
                        try:
                            tag_response = lambda_client.list_tags(Resource=function['FunctionArn'])
                            tags = tag_response.get('Tags', {})
                        except:
                            pass
                        
                        ai_functions.append({
                            'type': 'function',
                            'name': function_name,
                            'arn': function['FunctionArn'],
                            'runtime': function.get('Runtime', 'Unknown'),
                            'memory': function.get('MemorySize', 0),
                            'timeout': function.get('Timeout', 0),
                            'last_modified': function.get('LastModified', ''),
                            'project': self._identify_project(function_name, tags)
                        })
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list Lambda functions: {e}[/yellow]")
        
        return ai_functions
    
    def discover_s3_ai_resources(self, session: boto3.Session) -> List[Dict]:
        """Discover AI-related S3 buckets"""
        s3_client = session.client('s3')
        ai_buckets = []
        
        # AI patterns for S3 buckets
        ai_patterns = [
            r'sa-ai-.*', r'.*-ai-.*', r'.*-modeltraining.*',
            r'.*modeltraining.*', r'.*ask-eva.*', r'.*resume-.*',
            r'.*iep.*', r'.*sagemaker.*', r'.*bedrock.*'
        ]
        
        try:
            response = s3_client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                # Check if it matches AI patterns
                is_ai = False
                for pattern in ai_patterns:
                    if re.match(pattern, bucket_name.lower()):
                        is_ai = True
                        break
                
                if is_ai:
                    # Get bucket tags
                    tags = {}
                    try:
                        tag_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
                        tags = {tag['Key']: tag['Value'] for tag in tag_response.get('TagSet', [])}
                    except:
                        pass
                    
                    ai_buckets.append({
                        'type': 'bucket',
                        'name': bucket_name,
                        'created': bucket['CreationDate'].isoformat(),
                        'project': self._identify_project(bucket_name, tags)
                    })
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list S3 buckets: {e}[/yellow]")
        
        return ai_buckets
    
    def discover_dynamodb_ai_resources(self, session: boto3.Session) -> List[Dict]:
        """Discover AI-related DynamoDB tables"""
        dynamodb = session.client('dynamodb')
        ai_tables = []
        
        # AI patterns for DynamoDB tables
        ai_patterns = [
            r'.*_ai_.*', r'.*-ai-.*', r'.*conversation.*',
            r'.*chat.*', r'sa_ai_.*', r'.*ask_eva.*', r'.*iep.*'
        ]
        
        try:
            paginator = dynamodb.get_paginator('list_tables')
            
            for page in paginator.paginate():
                for table_name in page.get('TableNames', []):
                    
                    # Check if it matches AI patterns
                    is_ai = False
                    for pattern in ai_patterns:
                        if re.match(pattern, table_name.lower()):
                            is_ai = True
                            break
                    
                    if is_ai:
                        # Get table details and tags
                        try:
                            table_desc = dynamodb.describe_table(TableName=table_name)
                            table_arn = table_desc['Table']['TableArn']
                            
                            tags = {}
                            try:
                                tag_response = dynamodb.list_tags_of_resource(ResourceArn=table_arn)
                                tags = {tag['Key']: tag['Value'] for tag in tag_response.get('Tags', [])}
                            except:
                                pass
                            
                            ai_tables.append({
                                'type': 'table',
                                'name': table_name,
                                'arn': table_arn,
                                'status': table_desc['Table']['TableStatus'],
                                'item_count': table_desc['Table'].get('ItemCount', 0),
                                'size_bytes': table_desc['Table'].get('TableSizeBytes', 0),
                                'project': self._identify_project(table_name, tags)
                            })
                        except:
                            pass
        except Exception as e:
            console.print(f"[yellow]Warning: Could not list DynamoDB tables: {e}[/yellow]")
        
        return ai_tables
    
    def display_discovery_summary(self, discoveries: Dict):
        """Display a summary of discovered AI resources"""
        console.print("\n[bold cyan]AI Service Discovery Summary[/bold cyan]")
        console.print(f"Account: {discoveries['account']}")
        console.print(f"Total AI Resources: {discoveries['summary']['total_ai_resources']}")
        console.print(f"Services Found: {len(discoveries['summary']['services_found'])}")
        console.print(f"Projects Identified: {len(discoveries['summary']['projects_found'])}")
        console.print(f"Untagged Resources: {discoveries['summary']['untagged_resources']}")
        
        # Service breakdown table
        if discoveries['services']:
            service_table = Table(title="\nAI Services Breakdown")
            service_table.add_column("Service", style="cyan")
            service_table.add_column("Category", style="green")
            service_table.add_column("Resources", style="yellow")
            
            for service_key, service_data in discoveries['services'].items():
                service_info = service_data.get('service_info', {})
                service_table.add_row(
                    service_info.get('cost_explorer_name', service_key),
                    service_info.get('category', 'Unknown'),
                    str(service_data['count'])
                )
            
            console.print(service_table)
        
        # Project breakdown table
        if discoveries['projects']:
            project_table = Table(title="\nProject Resource Distribution")
            project_table.add_column("Project", style="cyan")
            project_table.add_column("Total Resources", style="yellow")
            project_table.add_column("Services Used", style="green")
            
            for project_name, project_data in discoveries['projects'].items():
                if project_name != 'Unknown':
                    services_list = ', '.join(project_data['services'].keys())
                    project_table.add_row(
                        project_name,
                        str(project_data['total_resources']),
                        services_list
                    )
            
            console.print(project_table)