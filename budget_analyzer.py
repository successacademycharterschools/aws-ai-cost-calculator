#!/usr/bin/env python3
"""
AI-Powered Budget Analyzer for AWS AI Cost Calculator
Uses Amazon Bedrock to provide intelligent cost analysis and recommendations
"""

import json
import boto3
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class AIBudgetAnalyzer:
    def __init__(self, boto_session=None):
        """Initialize the AI Budget Analyzer with Bedrock client"""
        self.session = boto_session or boto3.Session()
        self.bedrock_runtime = self.session.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'
        )
        
        # Cost optimization knowledge base
        self.optimization_strategies = {
            'bedrock': {
                'model_selection': {
                    'Claude-3-Opus': {'use_case': 'Complex reasoning, creative tasks', 'relative_cost': 1.0},
                    'Claude-3-Sonnet': {'use_case': 'Balanced performance', 'relative_cost': 0.2},
                    'Claude-3-Haiku': {'use_case': 'Simple tasks, high volume', 'relative_cost': 0.025},
                    'Claude-Instant': {'use_case': 'Quick responses, basic tasks', 'relative_cost': 0.04}
                },
                'optimization_techniques': [
                    'Use batch processing for 50% cost reduction on non-real-time workloads',
                    'Implement prompt caching for up to 90% savings on repeated queries',
                    'Use provisioned throughput for consistent workloads (40-60% savings)',
                    'Implement intelligent prompt routing based on complexity'
                ]
            },
            'kendra': {
                'cost_drivers': ['Index storage', 'Query volume', 'Document processing'],
                'optimization_techniques': [
                    'Eliminate idle indices ($60K+ annual savings per index)',
                    'Optimize document sync schedules',
                    'Implement query result caching',
                    'Use relevance filtering to reduce indexed content',
                    'Consider OpenSearch for 80% cost reduction if advanced NLP not required'
                ]
            },
            'sagemaker': {
                'optimization_techniques': [
                    'Use Spot instances for training (up to 90% savings)',
                    'Implement auto-scaling for endpoints',
                    'Use multi-model endpoints to share resources',
                    'Consider Graviton instances for 20% cost reduction',
                    'Apply SageMaker Savings Plans for up to 64% savings'
                ]
            }
        }
    
    def analyze_costs(self, cost_data: Dict, discovery_data: Dict) -> Dict:
        """Perform comprehensive AI-powered cost analysis"""
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(cost_data, discovery_data)
            
            # Generate AI insights
            insights = self._generate_ai_insights(analysis_context)
            
            # Detect anomalies
            anomalies = self._detect_cost_anomalies(cost_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(cost_data, discovery_data)
            
            # Calculate potential savings
            savings_opportunities = self._calculate_savings_opportunities(cost_data, discovery_data)
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                cost_data, insights, recommendations, savings_opportunities
            )
            
            return {
                'executive_summary': executive_summary,
                'insights': insights,
                'anomalies': anomalies,
                'recommendations': recommendations,
                'savings_opportunities': savings_opportunities,
                'optimization_score': self._calculate_optimization_score(cost_data, discovery_data),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Budget analysis error: {e}")
            return self._generate_fallback_analysis(cost_data, discovery_data)
    
    def _prepare_analysis_context(self, cost_data: Dict, discovery_data: Dict) -> str:
        """Prepare context for AI analysis"""
        total_cost = cost_data.get('grand_total', 0)
        project_breakdown = cost_data.get('project_breakdown', {})
        
        context = f"""
        AWS AI Cost Analysis Context:
        - Total Monthly Cost: ${total_cost:.2f}
        - Number of AI Projects: {len(project_breakdown)}
        - Date Range: {cost_data.get('period', 'Last 30 days')}
        
        Project Costs:
        """
        
        for project, data in project_breakdown.items():
            if data.get('total_cost', 0) > 0:
                context += f"\n- {project}: ${data['total_cost']:.2f} ({data.get('resource_count', 0)} resources)"
        
        # Add service breakdown
        context += "\n\nService Costs:"
        for account_costs in cost_data.get('costs_by_account', []):
            for service, cost in account_costs.get('services', {}).items():
                if cost > 0:
                    context += f"\n- {service}: ${cost:.2f}"
        
        return context
    
    def _generate_ai_insights(self, context: str) -> List[Dict]:
        """Generate AI-powered insights using Bedrock"""
        prompt = f"""
        As an AWS cost optimization expert, analyze the following AWS AI service costs and provide 
        actionable insights. Focus on identifying cost patterns, efficiency opportunities, and 
        strategic recommendations.
        
        {context}
        
        Provide 3-5 key insights in JSON format with the following structure:
        {{
            "insights": [
                {{
                    "title": "Brief insight title",
                    "description": "Detailed explanation",
                    "impact": "high|medium|low",
                    "category": "cost|efficiency|optimization|risk"
                }}
            ]
        }}
        
        Focus on:
        1. Cost concentration and distribution
        2. Service efficiency
        3. Optimization opportunities
        4. Risk factors
        5. Strategic recommendations
        """
        
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7
                })
            )
            
            response_body = json.loads(response['body'].read())
            insights_text = response_body['content'][0]['text']
            
            # Parse JSON response
            try:
                insights_data = json.loads(insights_text)
                return insights_data.get('insights', [])
            except:
                # Fallback to text parsing
                return self._parse_text_insights(insights_text)
                
        except Exception as e:
            logger.error(f"AI insights generation error: {e}")
            return self._generate_default_insights(context)
    
    def _detect_cost_anomalies(self, cost_data: Dict) -> List[Dict]:
        """Detect unusual cost patterns"""
        anomalies = []
        
        # Check for service concentration
        total_cost = cost_data.get('grand_total', 0)
        if total_cost > 0:
            for account_costs in cost_data.get('costs_by_account', []):
                for service, cost in account_costs.get('services', {}).items():
                    percentage = (cost / total_cost) * 100
                    
                    if percentage > 80 and service.lower() != 'kendra':
                        anomalies.append({
                            'type': 'high_concentration',
                            'severity': 'high',
                            'service': service,
                            'message': f'{service} represents {percentage:.1f}% of total costs',
                            'recommendation': f'Review {service} usage and consider optimization strategies'
                        })
                    elif percentage > 60:
                        anomalies.append({
                            'type': 'moderate_concentration',
                            'severity': 'medium',
                            'service': service,
                            'message': f'{service} represents {percentage:.1f}% of total costs',
                            'recommendation': f'Monitor {service} usage trends'
                        })
        
        # Check for zero-cost resources
        if cost_data.get('project_breakdown'):
            for project, data in cost_data.get('project_breakdown', {}).items():
                if data.get('resource_count', 0) > 5 and data.get('total_cost', 0) == 0:
                    anomalies.append({
                        'type': 'zero_cost_resources',
                        'severity': 'low',
                        'project': project,
                        'message': f'{project} has {data["resource_count"]} resources but no costs',
                        'recommendation': 'Verify resources are being used efficiently'
                    })
        
        return anomalies
    
    def _generate_recommendations(self, cost_data: Dict, discovery_data: Dict) -> List[Dict]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        # Analyze Bedrock usage
        bedrock_cost = 0
        for account_costs in cost_data.get('costs_by_account', []):
            bedrock_cost += account_costs.get('services', {}).get('bedrock', 0)
        
        if bedrock_cost > 100:
            recommendations.append({
                'service': 'bedrock',
                'priority': 'high',
                'title': 'Optimize Bedrock Model Selection',
                'description': 'Consider using Claude 3 Haiku or Claude Instant for simple queries',
                'potential_savings': f'${bedrock_cost * 0.4:.2f}/month',
                'implementation': [
                    'Analyze query complexity patterns',
                    'Implement model routing based on task type',
                    'Use Claude Instant for simple Q&A',
                    'Reserve Claude 3 Opus for complex reasoning'
                ]
            })
        
        # Analyze Kendra usage
        kendra_cost = 0
        for account_costs in cost_data.get('costs_by_account', []):
            kendra_cost += account_costs.get('services', {}).get('kendra', 0)
        
        if kendra_cost > 100:
            recommendations.append({
                'service': 'kendra',
                'priority': 'high',
                'title': 'Optimize Kendra Usage',
                'description': 'Kendra costs can be reduced through index optimization',
                'potential_savings': f'${kendra_cost * 0.3:.2f}/month',
                'implementation': [
                    'Review index utilization metrics',
                    'Implement query result caching',
                    'Consider OpenSearch for basic search needs',
                    'Optimize document sync schedules'
                ]
            })
        
        # Check for batch processing opportunities
        lambda_cost = 0
        for account_costs in cost_data.get('costs_by_account', []):
            lambda_cost += account_costs.get('services', {}).get('lambda', 0)
        
        if lambda_cost > 0:
            recommendations.append({
                'service': 'lambda',
                'priority': 'medium',
                'title': 'Implement Batch Processing',
                'description': 'Convert real-time workloads to batch for 50% savings',
                'potential_savings': f'${lambda_cost * 0.3:.2f}/month',
                'implementation': [
                    'Identify non-real-time workloads',
                    'Implement SQS queuing for batch jobs',
                    'Schedule processing during off-peak hours',
                    'Use Bedrock batch inference APIs'
                ]
            })
        
        return recommendations
    
    def _calculate_savings_opportunities(self, cost_data: Dict, discovery_data: Dict) -> Dict:
        """Calculate potential cost savings"""
        total_cost = cost_data.get('grand_total', 0)
        
        savings = {
            'total_potential_savings': 0,
            'savings_percentage': 0,
            'opportunities': []
        }
        
        # Model optimization savings
        bedrock_savings = 0
        for account_costs in cost_data.get('costs_by_account', []):
            bedrock_cost = account_costs.get('services', {}).get('bedrock', 0)
            bedrock_savings += bedrock_cost * 0.4  # 40% potential savings
        
        if bedrock_savings > 0:
            savings['opportunities'].append({
                'name': 'Model Optimization',
                'monthly_savings': float(bedrock_savings),
                'effort': 'low',
                'timeline': '1-2 weeks'
            })
        
        # Batch processing savings
        batch_savings = total_cost * 0.15  # 15% overall savings potential
        if batch_savings > 0:
            savings['opportunities'].append({
                'name': 'Batch Processing',
                'monthly_savings': float(batch_savings),
                'effort': 'medium',
                'timeline': '2-4 weeks'
            })
        
        # Caching savings
        caching_savings = total_cost * 0.25  # 25% potential savings
        if caching_savings > 0:
            savings['opportunities'].append({
                'name': 'Implement Caching',
                'monthly_savings': float(caching_savings),
                'effort': 'low',
                'timeline': '1 week'
            })
        
        # Service optimization savings
        kendra_cost = 0
        for account_costs in cost_data.get('costs_by_account', []):
            kendra_cost += account_costs.get('services', {}).get('kendra', 0)
        
        if kendra_cost > 50:
            kendra_savings = kendra_cost * 0.3
            savings['opportunities'].append({
                'name': 'Kendra Optimization',
                'monthly_savings': float(kendra_savings),
                'effort': 'medium',
                'timeline': '2-3 weeks'
            })
        
        # Reserved capacity savings
        if total_cost > 100:
            reserved_savings = total_cost * 0.2
            savings['opportunities'].append({
                'name': 'Reserved Capacity',
                'monthly_savings': float(reserved_savings),
                'effort': 'low',
                'timeline': '1 day'
            })
        
        # Calculate totals
        savings['total_potential_savings'] = sum(
            opp['monthly_savings'] for opp in savings['opportunities']
        )
        savings['savings_percentage'] = (
            (savings['total_potential_savings'] / total_cost * 100) 
            if total_cost > 0 else 0
        )
        
        return savings
    
    def _generate_executive_summary(self, cost_data: Dict, insights: List, 
                                  recommendations: List, savings: Dict) -> str:
        """Generate AI-powered executive summary"""
        total_cost = cost_data.get('grand_total', 0)
        total_resources = sum(
            data.get('resource_count', 0) 
            for data in cost_data.get('project_breakdown', {}).values()
        )
        
        summary = f"""
        ## Executive Summary
        
        **Total AI Spend**: ${total_cost:.2f}/month across {total_resources} resources
        
        **Key Findings**:
        • Potential savings of ${savings['total_potential_savings']:.2f}/month ({savings['savings_percentage']:.1f}%)
        • {len(recommendations)} optimization opportunities identified
        • {len(insights)} strategic insights generated
        
        **Immediate Actions**:
        1. {recommendations[0]['title'] if recommendations else 'Review service utilization'}
        2. Implement cost allocation tags for better tracking
        3. Set up automated cost anomaly alerts
        
        **Strategic Recommendations**:
        • Adopt a multi-model strategy for cost optimization
        • Implement batch processing for non-real-time workloads
        • Consider managed services to reduce operational overhead
        """
        
        return summary
    
    def _calculate_optimization_score(self, cost_data: Dict, discovery_data: Dict) -> int:
        """Calculate overall optimization score (0-100)"""
        score = 100
        
        # Deduct points for issues
        total_cost = cost_data.get('grand_total', 0)
        
        # Check for service concentration
        for account_costs in cost_data.get('costs_by_account', []):
            for service, cost in account_costs.get('services', {}).items():
                if total_cost > 0:
                    percentage = (cost / total_cost) * 100
                    if percentage > 80 and service.lower() != 'kendra':
                        score -= 20  # High concentration penalty
                    elif percentage > 60:
                        score -= 10  # Moderate concentration penalty
        
        # Check for unattributed costs
        unattributed = cost_data.get('project_breakdown', {}).get('Unattributed', {})
        if unattributed.get('total_cost', 0) > total_cost * 0.2:
            score -= 15  # High unattributed costs
        
        # Bonus for good practices
        if len(cost_data.get('project_breakdown', {})) > 3:
            score += 5  # Multiple projects tracked
        
        return max(0, min(100, score))
    
    def _generate_default_insights(self, context: str) -> List[Dict]:
        """Generate default insights when AI is unavailable"""
        return [
            {
                'title': 'Cost Concentration Analysis',
                'description': 'Review service cost distribution to identify optimization opportunities',
                'impact': 'high',
                'category': 'optimization'
            },
            {
                'title': 'Resource Utilization',
                'description': 'Monitor resource usage patterns to ensure efficient allocation',
                'impact': 'medium',
                'category': 'efficiency'
            }
        ]
    
    def _parse_text_insights(self, text: str) -> List[Dict]:
        """Parse text insights into structured format"""
        # Simple parser for fallback
        insights = []
        lines = text.split('\n')
        
        current_insight = {}
        for line in lines:
            line = line.strip()
            if line.startswith('Title:') or line.startswith('title:'):
                if current_insight:
                    insights.append(current_insight)
                current_insight = {'title': line.split(':', 1)[1].strip()}
            elif line.startswith('Description:') or line.startswith('description:'):
                current_insight['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('Impact:') or line.startswith('impact:'):
                current_insight['impact'] = line.split(':', 1)[1].strip().lower()
            elif line.startswith('Category:') or line.startswith('category:'):
                current_insight['category'] = line.split(':', 1)[1].strip().lower()
        
        if current_insight:
            insights.append(current_insight)
        
        return insights
    
    def _generate_fallback_analysis(self, cost_data: Dict, discovery_data: Dict) -> Dict:
        """Generate analysis without AI when Bedrock is unavailable"""
        total_cost = cost_data.get('grand_total', 0)
        
        return {
            'executive_summary': f"Total monthly AI spend: ${total_cost:.2f}. Manual review recommended.",
            'insights': self._generate_default_insights(""),
            'anomalies': self._detect_cost_anomalies(cost_data),
            'recommendations': [{
                'service': 'general',
                'priority': 'medium',
                'title': 'Enable AI-powered analysis',
                'description': 'Configure Bedrock access for intelligent insights',
                'potential_savings': 'TBD',
                'implementation': ['Set up Bedrock credentials', 'Enable AI analysis features']
            }],
            'savings_opportunities': {
                'total_potential_savings': total_cost * 0.2,
                'savings_percentage': 20,
                'opportunities': []
            },
            'optimization_score': 70,
            'generated_at': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test the analyzer
    analyzer = AIBudgetAnalyzer()
    
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
    
    result = analyzer.analyze_costs(test_cost_data, {})
    print(json.dumps(result, indent=2, default=str))