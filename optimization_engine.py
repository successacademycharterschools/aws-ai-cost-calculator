#!/usr/bin/env python3
"""
Cost Optimization Engine for AWS AI Services
Provides specific, actionable recommendations for cost reduction
"""

import json
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class OptimizationEngine:
    def __init__(self):
        """Initialize optimization engine with AWS best practices"""
        self.service_optimizations = {
            'bedrock': {
                'model_alternatives': {
                    'claude-3-opus': [
                        {'alternative': 'claude-3-sonnet', 'use_case': 'General tasks', 'savings': 0.8},
                        {'alternative': 'claude-3-haiku', 'use_case': 'Simple queries', 'savings': 0.975},
                        {'alternative': 'claude-instant', 'use_case': 'Quick responses', 'savings': 0.96}
                    ],
                    'claude-3-sonnet': [
                        {'alternative': 'claude-3-haiku', 'use_case': 'Simple tasks', 'savings': 0.875},
                        {'alternative': 'claude-instant', 'use_case': 'Basic Q&A', 'savings': 0.8}
                    ]
                },
                'techniques': {
                    'batch_processing': {
                        'description': 'Process multiple requests in batch mode',
                        'savings': 0.5,
                        'implementation_effort': 'medium',
                        'time_to_implement': '1-2 weeks'
                    },
                    'prompt_caching': {
                        'description': 'Cache repeated prompts and contexts',
                        'savings': 0.9,
                        'implementation_effort': 'low',
                        'time_to_implement': '2-3 days'
                    },
                    'provisioned_throughput': {
                        'description': 'Use provisioned throughput for consistent workloads',
                        'savings': 0.5,
                        'implementation_effort': 'low',
                        'time_to_implement': '1 day'
                    },
                    'intelligent_routing': {
                        'description': 'Route queries to appropriate models based on complexity',
                        'savings': 0.65,
                        'implementation_effort': 'high',
                        'time_to_implement': '2-4 weeks'
                    }
                }
            },
            'kendra': {
                'alternatives': [
                    {
                        'service': 'OpenSearch',
                        'use_case': 'Basic search without advanced NLP',
                        'savings': 0.8,
                        'migration_effort': 'high'
                    },
                    {
                        'service': 'ElasticSearch',
                        'use_case': 'Custom search implementation',
                        'savings': 0.75,
                        'migration_effort': 'high'
                    }
                ],
                'techniques': {
                    'index_optimization': {
                        'description': 'Reduce indexed content and optimize sync schedules',
                        'savings': 0.3,
                        'implementation_effort': 'medium',
                        'time_to_implement': '1 week'
                    },
                    'query_caching': {
                        'description': 'Implement intelligent query result caching',
                        'savings': 0.4,
                        'implementation_effort': 'medium',
                        'time_to_implement': '1-2 weeks'
                    },
                    'relevance_filtering': {
                        'description': 'Filter documents before indexing',
                        'savings': 0.25,
                        'implementation_effort': 'low',
                        'time_to_implement': '3-5 days'
                    }
                }
            },
            'sagemaker': {
                'techniques': {
                    'spot_instances': {
                        'description': 'Use spot instances for training',
                        'savings': 0.9,
                        'implementation_effort': 'low',
                        'time_to_implement': '1 day'
                    },
                    'multi_model_endpoints': {
                        'description': 'Host multiple models on single endpoint',
                        'savings': 0.5,
                        'implementation_effort': 'medium',
                        'time_to_implement': '1 week'
                    },
                    'auto_scaling': {
                        'description': 'Implement dynamic endpoint scaling',
                        'savings': 0.4,
                        'implementation_effort': 'medium',
                        'time_to_implement': '3-5 days'
                    },
                    'graviton_instances': {
                        'description': 'Use AWS Graviton instances',
                        'savings': 0.2,
                        'implementation_effort': 'low',
                        'time_to_implement': '1-2 days'
                    }
                }
            },
            'lambda': {
                'techniques': {
                    'memory_optimization': {
                        'description': 'Right-size Lambda memory allocation',
                        'savings': 0.3,
                        'implementation_effort': 'low',
                        'time_to_implement': '1 day'
                    },
                    'async_processing': {
                        'description': 'Use asynchronous invocations',
                        'savings': 0.2,
                        'implementation_effort': 'medium',
                        'time_to_implement': '3-5 days'
                    },
                    'graviton_runtime': {
                        'description': 'Use Graviton-based runtime',
                        'savings': 0.2,
                        'implementation_effort': 'low',
                        'time_to_implement': '1 day'
                    }
                }
            }
        }
        
        self.project_specific_optimizations = {
            'ask-eva': {
                'recommendations': [
                    {
                        'title': 'Implement Tiered Model Strategy',
                        'description': 'Use Claude Instant for simple Q&A, Claude 3 Haiku for moderate complexity, Claude 3 Sonnet only for complex reasoning',
                        'impact': 'high',
                        'savings_estimate': 0.65
                    },
                    {
                        'title': 'Cache Frequent Queries',
                        'description': 'Implement Redis caching for top 100 most frequent questions',
                        'impact': 'high',
                        'savings_estimate': 0.4
                    }
                ]
            },
            'iep-report': {
                'recommendations': [
                    {
                        'title': 'Batch Report Generation',
                        'description': 'Process multiple reports in batch during off-peak hours',
                        'impact': 'high',
                        'savings_estimate': 0.5
                    },
                    {
                        'title': 'Optimize Kendra Usage',
                        'description': 'Consider moving to OpenSearch for document search, keep Kendra only for complex NLP queries',
                        'impact': 'very_high',
                        'savings_estimate': 0.8
                    }
                ]
            },
            'financial-aid': {
                'recommendations': [
                    {
                        'title': 'Async Document Processing',
                        'description': 'Use SQS and batch processing for document analysis',
                        'impact': 'medium',
                        'savings_estimate': 0.3
                    },
                    {
                        'title': 'Optimize Textract Usage',
                        'description': 'Pre-process documents to extract only relevant pages',
                        'impact': 'medium',
                        'savings_estimate': 0.25
                    }
                ]
            }
        }
    
    def generate_optimization_plan(self, cost_data: Dict, discovery_data: Dict) -> Dict:
        """Generate comprehensive optimization plan"""
        plan = {
            'summary': self._generate_summary(cost_data),
            'immediate_actions': [],
            'short_term_optimizations': [],
            'long_term_strategies': [],
            'service_specific': {},
            'project_specific': {},
            'implementation_roadmap': [],
            'roi_analysis': {}
        }
        
        # Analyze each service
        for account_costs in cost_data.get('costs_by_account', []):
            for service, cost in account_costs.get('services', {}).items():
                if cost > 0:
                    service_opts = self._analyze_service(service, cost, discovery_data)
                    if service_opts:
                        plan['service_specific'][service] = service_opts
        
        # Analyze each project
        for project, data in cost_data.get('project_breakdown', {}).items():
            if data.get('total_cost', 0) > 0:
                project_opts = self._analyze_project(project, data, discovery_data)
                if project_opts:
                    plan['project_specific'][project] = project_opts
        
        # Categorize optimizations
        self._categorize_optimizations(plan)
        
        # Generate implementation roadmap
        plan['implementation_roadmap'] = self._generate_roadmap(plan)
        
        # Calculate ROI
        plan['roi_analysis'] = self._calculate_roi(plan, cost_data)
        
        return plan
    
    def _generate_summary(self, cost_data: Dict) -> Dict:
        """Generate optimization summary"""
        total_cost = cost_data.get('grand_total', 0)
        
        return {
            'current_monthly_cost': float(total_cost),
            'estimated_savings': float(total_cost * 0.45),  # Conservative 45% estimate
            'optimization_potential': 'high' if total_cost > 100 else 'medium',
            'payback_period': '2-4 weeks',
            'risk_level': 'low'
        }
    
    def _analyze_service(self, service: str, cost: float, discovery_data: Dict) -> Dict:
        """Analyze optimization opportunities for a specific service"""
        service_key = service.lower().replace('amazon ', '').replace('aws ', '')
        
        if service_key not in self.service_optimizations:
            return {}
        
        optimizations = []
        service_config = self.service_optimizations[service_key]
        
        # Add technique-based optimizations
        for technique_name, technique_data in service_config.get('techniques', {}).items():
            potential_savings = cost * technique_data['savings']
            
            if potential_savings > 10:  # Only include if savings > $10/month
                optimizations.append({
                    'name': technique_name.replace('_', ' ').title(),
                    'description': technique_data['description'],
                    'monthly_savings': float(potential_savings),
                    'effort': technique_data['implementation_effort'],
                    'timeline': technique_data['time_to_implement'],
                    'priority': self._calculate_priority(potential_savings, technique_data['implementation_effort'])
                })
        
        # Add alternative service recommendations
        if 'alternatives' in service_config and cost > 50:
            for alt in service_config['alternatives']:
                potential_savings = cost * alt['savings']
                optimizations.append({
                    'name': f"Migrate to {alt['service']}",
                    'description': alt['use_case'],
                    'monthly_savings': float(potential_savings),
                    'effort': alt['migration_effort'],
                    'timeline': '2-4 weeks',
                    'priority': 'medium'
                })
        
        return {
            'current_cost': float(cost),
            'optimizations': sorted(optimizations, key=lambda x: x['monthly_savings'], reverse=True),
            'total_savings_potential': sum(opt['monthly_savings'] for opt in optimizations[:3])  # Top 3
        }
    
    def _analyze_project(self, project: str, project_data: Dict, discovery_data: Dict) -> Dict:
        """Analyze optimization opportunities for a specific project"""
        project_key = project.lower().replace(' ', '-')
        
        if project_key not in self.project_specific_optimizations:
            return self._generate_generic_project_optimizations(project, project_data)
        
        recommendations = []
        project_config = self.project_specific_optimizations[project_key]
        
        for rec in project_config['recommendations']:
            estimated_savings = project_data.get('total_cost', 0) * rec['savings_estimate']
            
            recommendations.append({
                'title': rec['title'],
                'description': rec['description'],
                'impact': rec['impact'],
                'estimated_monthly_savings': float(estimated_savings),
                'implementation_steps': self._generate_implementation_steps(rec['title'])
            })
        
        return {
            'current_cost': float(project_data.get('total_cost', 0)),
            'resource_count': project_data.get('resource_count', 0),
            'recommendations': recommendations,
            'optimization_score': self._calculate_project_optimization_score(project_data)
        }
    
    def _generate_generic_project_optimizations(self, project: str, project_data: Dict) -> Dict:
        """Generate generic optimizations for projects without specific configurations"""
        cost = project_data.get('total_cost', 0)
        
        recommendations = []
        
        if cost > 50:
            recommendations.append({
                'title': 'Implement Cost Allocation Tags',
                'description': 'Add detailed tags for better cost tracking and optimization',
                'impact': 'medium',
                'estimated_monthly_savings': float(cost * 0.1),
                'implementation_steps': [
                    'Define tagging strategy',
                    'Apply tags to all resources',
                    'Set up cost allocation reports'
                ]
            })
        
        if cost > 100:
            recommendations.append({
                'title': 'Review Service Utilization',
                'description': 'Analyze usage patterns and right-size resources',
                'impact': 'high',
                'estimated_monthly_savings': float(cost * 0.2),
                'implementation_steps': [
                    'Collect utilization metrics',
                    'Identify underutilized resources',
                    'Implement auto-scaling policies'
                ]
            })
        
        return {
            'current_cost': float(cost),
            'resource_count': project_data.get('resource_count', 0),
            'recommendations': recommendations,
            'optimization_score': 60  # Default score
        }
    
    def _categorize_optimizations(self, plan: Dict) -> None:
        """Categorize optimizations by implementation timeline"""
        all_optimizations = []
        
        # Collect all optimizations
        for service_data in plan['service_specific'].values():
            all_optimizations.extend(service_data.get('optimizations', []))
        
        # Add project-specific recommendations as well
        for project_data in plan['project_specific'].values():
            for rec in project_data.get('recommendations', []):
                all_optimizations.append({
                    'name': rec.get('title', 'Project Optimization'),
                    'monthly_savings': rec.get('estimated_monthly_savings', 0),
                    'effort': rec.get('impact', 'medium'),
                    'timeline': '1-2 weeks',
                    'priority': rec.get('impact', 'medium')
                })
        
        # Sort by priority and savings
        all_optimizations.sort(key=lambda x: (x.get('priority', 'low'), x.get('monthly_savings', 0)), reverse=True)
        
        # Categorize
        for opt in all_optimizations:
            if opt.get('effort') in ['low', 'quick'] or opt.get('monthly_savings', 0) > 50:
                plan['immediate_actions'].append(opt)
            elif opt.get('timeline', '').startswith('1') or opt.get('effort') == 'medium':
                plan['short_term_optimizations'].append(opt)
            else:
                plan['long_term_strategies'].append(opt)
        
        # Ensure each category has at least one item
        if not plan['immediate_actions'] and all_optimizations:
            plan['immediate_actions'].append(all_optimizations[0] if all_optimizations else {
                'name': 'Cost Tagging Implementation',
                'monthly_savings': 0,
                'effort': 'low',
                'timeline': '1 week'
            })
    
    def _generate_roadmap(self, plan: Dict) -> List[Dict]:
        """Generate implementation roadmap"""
        roadmap = []
        total_cost = plan.get('summary', {}).get('current_monthly_cost', 0)
        
        # Week 1: Quick wins
        immediate_actions = plan.get('immediate_actions', [])
        if immediate_actions:
            week1_savings = sum(opt.get('monthly_savings', 0) for opt in immediate_actions[:3])
            actions = [opt['name'] for opt in immediate_actions[:3]]
        else:
            # Default quick wins if none found
            week1_savings = total_cost * 0.1 if total_cost > 0 else 10
            actions = ['Enable cost allocation tags', 'Review unused resources', 'Implement basic monitoring']
        
        roadmap.append({
            'phase': 'Week 1: Quick Wins',
            'actions': actions,
            'estimated_savings': float(week1_savings),
            'effort': 'low'
        })
        
        # Week 2-4: Short-term optimizations
        short_term = plan.get('short_term_optimizations', [])
        if short_term:
            short_term_savings = sum(opt.get('monthly_savings', 0) for opt in short_term[:3])
            actions = [opt['name'] for opt in short_term[:3]]
        else:
            # Default short-term actions
            short_term_savings = total_cost * 0.2 if total_cost > 0 else 20
            actions = ['Implement caching strategy', 'Optimize model selection', 'Configure auto-scaling']
        
        roadmap.append({
            'phase': 'Week 2-4: Core Optimizations',
            'actions': actions,
            'estimated_savings': float(short_term_savings),
            'effort': 'medium'
        })
        
        # Month 2+: Strategic changes
        long_term = plan.get('long_term_strategies', [])
        if long_term:
            long_term_savings = sum(opt.get('monthly_savings', 0) for opt in long_term[:2])
            actions = [opt['name'] for opt in long_term[:2]]
        else:
            # Default long-term strategies
            long_term_savings = total_cost * 0.25 if total_cost > 0 else 25
            actions = ['Migrate to alternative services', 'Implement advanced batch processing']
        
        roadmap.append({
            'phase': 'Month 2+: Strategic Transformation',
            'actions': actions,
            'estimated_savings': float(long_term_savings),
            'effort': 'high'
        })
        
        return roadmap
    
    def _calculate_roi(self, plan: Dict, cost_data: Dict) -> Dict:
        """Calculate ROI for optimization efforts"""
        total_current_cost = cost_data.get('grand_total', 0)
        
        # Calculate total potential savings
        total_savings = 0
        for phase in plan['implementation_roadmap']:
            total_savings += phase['estimated_savings']
        
        # Estimate implementation costs (rough estimate)
        implementation_cost = total_savings * 0.5  # 0.5 month of savings for implementation
        
        return {
            'monthly_savings': float(total_savings),
            'annual_savings': float(total_savings * 12),
            'implementation_cost': float(implementation_cost),
            'payback_period_days': int((implementation_cost / total_savings) * 30) if total_savings > 0 else 0,
            'first_year_net_savings': float((total_savings * 12) - implementation_cost),
            'savings_percentage': float((total_savings / total_current_cost * 100)) if total_current_cost > 0 else 0
        }
    
    def _calculate_priority(self, savings: float, effort: str) -> str:
        """Calculate optimization priority based on savings and effort"""
        if savings > 100 and effort == 'low':
            return 'critical'
        elif savings > 50 and effort in ['low', 'medium']:
            return 'high'
        elif savings > 20:
            return 'medium'
        else:
            return 'low'
    
    def _generate_implementation_steps(self, optimization_title: str) -> List[str]:
        """Generate implementation steps for an optimization"""
        # Simplified implementation steps generator
        steps_map = {
            'Tiered Model': [
                'Analyze current query patterns',
                'Classify queries by complexity',
                'Implement routing logic',
                'Test and validate accuracy',
                'Monitor cost savings'
            ],
            'Batch': [
                'Identify batch-eligible workloads',
                'Implement queue system',
                'Create batch processing logic',
                'Schedule batch jobs',
                'Monitor performance'
            ],
            'Cache': [
                'Analyze query patterns',
                'Set up caching infrastructure',
                'Implement cache logic',
                'Set TTL policies',
                'Monitor hit rates'
            ]
        }
        
        # Find matching steps
        for key, steps in steps_map.items():
            if key.lower() in optimization_title.lower():
                return steps
        
        # Default steps
        return [
            'Analyze current implementation',
            'Design optimization approach',
            'Implement changes',
            'Test and validate',
            'Monitor results'
        ]
    
    def _calculate_project_optimization_score(self, project_data: Dict) -> int:
        """Calculate optimization score for a project (0-100)"""
        score = 50  # Base score
        
        # Adjust based on cost efficiency
        cost = project_data.get('total_cost', 0)
        resources = project_data.get('resource_count', 1)
        
        if resources > 0:
            cost_per_resource = cost / resources
            
            if cost_per_resource < 1:
                score += 20  # Very efficient
            elif cost_per_resource < 5:
                score += 10  # Efficient
            elif cost_per_resource > 20:
                score -= 20  # Inefficient
        
        # Adjust based on absolute cost
        if cost > 100:
            score -= 10  # High cost penalty
        elif cost < 10:
            score += 10  # Low cost bonus
        
        return max(0, min(100, score))

if __name__ == "__main__":
    # Test the optimization engine
    engine = OptimizationEngine()
    
    # Sample test data
    test_cost_data = {
        'grand_total': 125.04,
        'costs_by_account': [{
            'services': {
                'bedrock': 4.94,
                'kendra': 120.04,
                'lambda': 0.01,
                's3': 0.05
            }
        }],
        'project_breakdown': {
            'Ask Eva': {'total_cost': 1.24, 'resource_count': 8},
            'IEP Report': {'total_cost': 122.93, 'resource_count': 15},
            'Financial Aid': {'total_cost': 0.00, 'resource_count': 3}
        }
    }
    
    result = engine.generate_optimization_plan(test_cost_data, {})
    print(json.dumps(result, indent=2))