#!/usr/bin/env python3
"""
Enhanced project attribution for AWS AI costs
Maps resources to projects based on tags and naming patterns
"""

import re
import json
from decimal import Decimal
from typing import Dict, List, Set
from rich.console import Console
from rich.table import Table

console = Console()

class ProjectAttributor:
    def __init__(self):
        """Initialize with project patterns and rules"""
        # Load config
        with open('ai_services_config.json', 'r') as f:
            self.config = json.load(f)
        
        # Project identification patterns
        self.project_patterns = {
            'ask-eva': {
                'patterns': [
                    r'ask-eva',
                    r'askeva', 
                    r'eva-poc',
                    r'sa-ai-ask-eva',
                    r'sa_ai_ask_eva',  # DynamoDB pattern
                    r'agent-quick-start.*eva',
                    r'knowledge-base.*eva'
                ],
                'tag_values': ['ask-eva', 'Ask Eva', 'AskEva', 'ask_eva'],
                'bucket_names': ['sa-ai-ask-eva', 'sa-ai-ask-eva-frontend'],
                'lambda_patterns': ['ask-eva', 'eva-Lambda', 'list-conv-history'],
                'dynamodb_patterns': ['sa_ai_ask_eva', 'ask-eva', 'askeva']
            },
            'iep-report': {
                'patterns': [
                    r'iepreport',
                    r'iep[-_]report',
                    r'sa-ai-iepreport',
                    r'GetAssessments',
                    r'GetScholarData', 
                    r'PdfGeneration',
                    r'iep[-_]performacne',  # Note the typo in the actual Lambda name
                    r'iep[-_]',
                    r'iep$',
                    r'querykb',
                    r'llmquery',
                    r'iep[-_]claude',
                    r'iep[-_]qna',
                    r'iep[-_]learning',
                    r'iep[-_]kwtxt',
                    r'iep[-_]db',
                    r'knowledge-base.*iep',
                    r'genai-index'  # Kendra indices for IEP
                ],
                'tag_values': ['iep-report', 'IEP Report', 'IEPReport', 'iep_report', 'iep'],
                'bucket_names': ['sa-ai-modeltraining'],
                'lambda_patterns': ['iepreport', 'iep_', 'iep-', 'querykb', 'llmquery'],
                'knowledge_base_patterns': ['iep', 'learning', 'qna', 'kwtxt'],
                'agent_patterns': ['iep-claude', 'iep_learningstyle']
            },
            'resume-knockout': {
                'patterns': [
                    r'resume-knockout',
                    r'resumeknockout',
                    r'resume.*knockout'
                ],
                'tag_values': ['resume-knockout', 'Resume Knockout', 'ResumeKnockout'],
                'bucket_names': [],
                'lambda_patterns': ['resume-knockout', 'knockout']
            },
            'resume-scoring': {
                'patterns': [
                    r'resume-scoring',
                    r'resumescoring',
                    r'resume.*scoring'
                ],
                'tag_values': ['resume-scoring', 'Resume Scoring', 'ResumeScoring'],
                'bucket_names': [],
                'lambda_patterns': ['resume-scoring', 'scoring']
            },
            'financial-aid': {
                'patterns': [
                    r'financial[-_]aid',
                    r'financialaid',
                    r'fin[-_]aid',
                    r'sa[-_]ai.*fin.*aid',
                    r'analyze[-_]fin[-_]aid',
                    r'textract.*results',
                    r'bedrock.*claude3.*fin.*aid'
                ],
                'tag_values': ['financial-aid', 'Financial Aid', 'FinancialAid', 'fin-aid', 'fin_aid'],
                'bucket_names': ['sa-ai-bedrock-claude3-fin-aid-letters-sy-2024-2025'],
                'lambda_patterns': ['financial-aid', 'finaid', 'fin_aid', 'analyze_fin_aid', 'textract_results']
            },
            'parent-app': {
                'patterns': [
                    r'parent[-_]app',
                    r'parentapp',
                    r'sa[-_]ai[-_]parent'
                ],
                'tag_values': ['parent-app', 'Parent App', 'ParentApp'],
                'bucket_names': [],
                'lambda_patterns': ['parent-app', 'parentapp']
            },
            'sales-force': {
                'patterns': [
                    r'salesforce',
                    r'sales[-_]force',
                    r'sf[-_]integration',
                    r'sa[-_]ai[-_]sf'
                ],
                'tag_values': ['salesforce', 'Sales Force', 'SalesForce', 'sf-integration'],
                'bucket_names': [],
                'lambda_patterns': ['salesforce', 'sf-integration']
            },
            'professional-development': {
                'patterns': [
                    r'prof[-_]dev',
                    r'professional[-_]development',
                    r'pd[-_]bot',
                    r'training[-_]bot'
                ],
                'tag_values': ['prof-dev', 'Professional Development', 'ProfessionalDevelopment', 'pd-bot'],
                'bucket_names': [],
                'lambda_patterns': ['prof-dev', 'pd-bot', 'training-bot']
            },
            'infrastructure': {
                'patterns': [
                    r'ai-image-object-detection',
                    r'os-bkbds',
                    r'opensearch',
                    r'sagemaker-model',
                    r'agent-quick-start-(?!.*eva)(?!.*iep)',  # Generic agents not matching other projects
                    r'knowledge-base-quick-start-(?!.*eva)(?!.*iep)'  # Generic KBs not matching other projects
                ],
                'tag_values': ['infrastructure', 'Infrastructure', 'ai-infrastructure'],
                'bucket_names': [],
                'opensearch_patterns': ['os-bkbds', 'opensearch'],
                'sagemaker_patterns': ['ai-image-object-detection']
            }
        }
    
    def identify_project(self, resource: Dict) -> str:
        """Identify which project a resource belongs to"""
        # Check tags first (most reliable)
        if 'tags' in resource and resource['tags']:
            for tag_key, tag_value in resource['tags'].items():
                if tag_key.lower() in ['project', 'projectname', 'project-name']:
                    # Direct tag match
                    for project_id, project_config in self.project_patterns.items():
                        if tag_value in project_config['tag_values']:
                            return project_id
        
        # Check resource name/ARN patterns
        resource_name = resource.get('name', '') or resource.get('arn', '')
        resource_name_lower = resource_name.lower()
        
        for project_id, project_config in self.project_patterns.items():
            # Check regex patterns
            for pattern in project_config['patterns']:
                if re.search(pattern, resource_name_lower):
                    return project_id
            
            # Check specific bucket names
            if resource.get('type') == 's3_bucket':
                bucket_name = resource.get('name', '')
                if bucket_name in project_config['bucket_names']:
                    return project_id
            
            # Check Lambda function patterns
            if resource.get('type') == 'lambda_function':
                for lambda_pattern in project_config['lambda_patterns']:
                    if lambda_pattern in resource_name_lower:
                        return project_id
            
            # Check Bedrock knowledge base patterns
            if resource.get('type') == 'knowledge_base' and 'knowledge_base_patterns' in project_config:
                for kb_pattern in project_config['knowledge_base_patterns']:
                    if kb_pattern in resource_name_lower:
                        return project_id
            
            # Check Bedrock agent patterns
            if resource.get('type') == 'agent' and 'agent_patterns' in project_config:
                for agent_pattern in project_config['agent_patterns']:
                    if agent_pattern in resource_name_lower:
                        return project_id
            
            # Check DynamoDB table patterns
            if resource.get('type') == 'dynamodb_table' and 'dynamodb_patterns' in project_config:
                for db_pattern in project_config['dynamodb_patterns']:
                    if db_pattern in resource_name_lower:
                        return project_id
            
            # Check OpenSearch domain patterns
            if resource.get('type') == 'domain' and 'opensearch_patterns' in project_config:
                for os_pattern in project_config['opensearch_patterns']:
                    if os_pattern in resource_name_lower:
                        return project_id
            
            # Check SageMaker model patterns
            if resource.get('type') == 'model' and 'sagemaker_patterns' in project_config:
                for sm_pattern in project_config['sagemaker_patterns']:
                    if sm_pattern in resource_name_lower:
                        return project_id
        
        return 'unattributed'
    
    def attribute_costs_to_projects(self, discovered_resources: Dict, service_costs: Dict) -> Dict:
        """Attribute costs to projects based on resource discovery"""
        project_costs = {
            'ask-eva': {'total': Decimal('0'), 'services': {}, 'resources': []},
            'iep-report': {'total': Decimal('0'), 'services': {}, 'resources': []},
            'resume-knockout': {'total': Decimal('0'), 'services': {}, 'resources': []},
            'resume-scoring': {'total': Decimal('0'), 'services': {}, 'resources': []},
            'financial-aid': {'total': Decimal('0'), 'services': {}, 'resources': []},
            'parent-app': {'total': Decimal('0'), 'services': {}, 'resources': []},
            'sales-force': {'total': Decimal('0'), 'services': {}, 'resources': []},
            'professional-development': {'total': Decimal('0'), 'services': {}, 'resources': []},
            'infrastructure': {'total': Decimal('0'), 'services': {}, 'resources': []},
            'unattributed': {'total': Decimal('0'), 'services': {}, 'resources': []}
        }
        
        # Map each resource to a project
        resource_to_project = {}
        project_resource_counts = {p: {} for p in project_costs.keys()}
        
        for service, service_data in discovered_resources.items():
            if 'resources' in service_data:
                for resource in service_data['resources']:
                    project = self.identify_project(resource)
                    resource_id = resource.get('arn', resource.get('name', 'unknown'))
                    resource_to_project[resource_id] = project
                    
                    # Count resources by type for each project
                    if service not in project_resource_counts[project]:
                        project_resource_counts[project][service] = 0
                    project_resource_counts[project][service] += 1
                    
                    # Track resource details
                    project_costs[project]['resources'].append({
                        'service': service,
                        'name': resource.get('name', 'unknown'),
                        'type': resource.get('type', service)
                    })
        
        # Distribute costs based on resource allocation
        for service, cost in service_costs.items():
            if cost > 0:
                # For AI services with direct costs
                if service in ['bedrock', 'sagemaker', 'comprehend', 'textract', 
                              'rekognition', 'polly', 'transcribe', 'translate',
                              'forecast', 'personalize', 'lex', 'kendra']:
                    
                    # Count total resources for this service
                    total_resources = sum(
                        project_resource_counts[p].get(service, 0) 
                        for p in project_costs.keys()
                    )
                    
                    if total_resources > 0:
                        # Distribute cost proportionally
                        for project in project_costs.keys():
                            resource_count = project_resource_counts[project].get(service, 0)
                            if resource_count > 0:
                                project_share = cost * Decimal(resource_count) / Decimal(total_resources)
                                project_costs[project]['total'] += project_share
                                project_costs[project]['services'][service] = project_share
                    else:
                        # No resources found, add to unattributed
                        project_costs['unattributed']['total'] += cost
                        project_costs['unattributed']['services'][service] = cost
                
                # For infrastructure services (Lambda, S3, DynamoDB)
                elif service in ['lambda', 's3', 'dynamodb']:
                    # These need special handling based on the specific resources
                    total_resources = sum(
                        project_resource_counts[p].get(service, 0) 
                        for p in project_costs.keys()
                    )
                    
                    if total_resources > 0:
                        for project in project_costs.keys():
                            resource_count = project_resource_counts[project].get(service, 0)
                            if resource_count > 0:
                                # Apply AI workload percentage estimate
                                ai_percentage = {
                                    'lambda': Decimal('0.3'),  # 30% of Lambda is AI
                                    's3': Decimal('0.2'),      # 20% of S3 is AI data
                                    'dynamodb': Decimal('0.25') # 25% of DynamoDB is AI data
                                }.get(service, Decimal('0.1'))
                                
                                project_share = cost * ai_percentage * Decimal(resource_count) / Decimal(total_resources)
                                project_costs[project]['total'] += project_share
                                project_costs[project]['services'][service] = project_share
                    else:
                        # Add small portion to unattributed
                        unattributed_share = cost * Decimal('0.1')  # 10% unattributed
                        project_costs['unattributed']['total'] += unattributed_share
                        project_costs['unattributed']['services'][service] = unattributed_share
        
        return project_costs
    
    def print_attribution_report(self, project_costs: Dict):
        """Print detailed project attribution report"""
        # Project cost table
        project_table = Table(title="\n📊 Cost Attribution by Project")
        project_table.add_column("Project", style="cyan")
        project_table.add_column("Total Cost", style="green")
        project_table.add_column("Top Services", style="yellow")
        project_table.add_column("Resource Count", style="white")
        
        for project_id, data in project_costs.items():
            if data['total'] > 0:
                project_name = self.config['project_mappings'].get(
                    project_id, {'name': project_id.title()}
                )['name']
                
                # Get top 3 services by cost
                top_services = sorted(
                    data['services'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:3]
                top_services_str = ', '.join([s[0] for s in top_services])
                
                project_table.add_row(
                    project_name,
                    f"${data['total']:.2f}",
                    top_services_str,
                    str(len(data['resources']))
                )
        
        console.print(project_table)
        
        # Service breakdown per project
        for project_id, data in project_costs.items():
            if data['total'] > 0 and project_id != 'unattributed':
                project_name = self.config['project_mappings'].get(
                    project_id, {'name': project_id.title()}
                )['name']
                
                service_table = Table(title=f"\n{project_name} - Service Breakdown")
                service_table.add_column("Service", style="cyan")
                service_table.add_column("Cost", style="green")
                service_table.add_column("% of Project", style="yellow")
                
                for service, cost in sorted(data['services'].items(), 
                                          key=lambda x: x[1], reverse=True):
                    percentage = (cost / data['total']) * 100 if data['total'] > 0 else 0
                    service_table.add_row(
                        service.upper(),
                        f"${cost:.2f}",
                        f"{percentage:.1f}%"
                    )
                
                console.print(service_table)
        
        # Summary
        total_attributed = sum(
            data['total'] for p, data in project_costs.items() 
            if p != 'unattributed'
        )
        total_unattributed = project_costs['unattributed']['total']
        total_all = total_attributed + total_unattributed
        
        if total_all > 0:
            attribution_rate = (total_attributed / total_all) * 100
            console.print(f"\n[bold]Attribution Summary:[/bold]")
            console.print(f"  Total Costs: ${total_all:.2f}")
            console.print(f"  Attributed: ${total_attributed:.2f} ({attribution_rate:.1f}%)")
            console.print(f"  Unattributed: ${total_unattributed:.2f} ({100-attribution_rate:.1f}%)")
            
            if attribution_rate < 80:
                console.print("\n[yellow]⚠️  Low attribution rate. Consider:[/yellow]")
                console.print("  • Adding project tags to resources")
                console.print("  • Updating naming conventions")
                console.print("  • Reviewing unattributed resources")


if __name__ == "__main__":
    # Test the attribution logic
    attributor = ProjectAttributor()
    
    # Sample test data
    test_resources = {
        'bedrock': {
            'resources': [
                {'name': 'ask-eva-poc-agent-quick-start-i87ch', 'type': 'agent', 'tags': {}},
                {'name': 'sa-ai-ask-eva-tone-agent', 'type': 'agent', 'tags': {'Project': 'ask-eva'}}
            ]
        },
        'lambda': {
            'resources': [
                {'name': 'iepreport-GetAssessmentsFunction', 'type': 'lambda_function'},
                {'name': 'sa-ai-ask-eva-Lambda', 'type': 'lambda_function'},
                {'name': 'iep_performacne', 'type': 'lambda_function'}
            ]
        },
        's3': {
            'resources': [
                {'name': 'sa-ai-ask-eva', 'type': 's3_bucket'},
                {'name': 'sa-ai-modeltraining', 'type': 's3_bucket'}
            ]
        }
    }
    
    test_costs = {
        'bedrock': Decimal('1000'),
        'lambda': Decimal('500'),
        's3': Decimal('200')
    }
    
    project_costs = attributor.attribute_costs_to_projects(test_resources, test_costs)
    attributor.print_attribution_report(project_costs)