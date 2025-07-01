#!/usr/bin/env python3
"""
Enhanced AWS AI Cost Calculator with high accuracy
Uses AWS MCP for real-time cost data
"""

import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import json
from typing import Dict, List, Optional, Tuple
import logging
from collections import defaultdict
from enhanced_config import AI_SERVICE_CONFIG, COST_ALLOCATION_TAGS, AI_PROJECTS, AWS_ACCOUNTS

logger = logging.getLogger(__name__)

class EnhancedCostCalculator:
    """High-accuracy cost calculator for AWS AI services"""
    
    def __init__(self, profile_name: Optional[str] = None):
        self.profile_name = profile_name
        self.session = self._create_session()
        self.ce_client = self.session.client('ce', region_name='us-east-1')
        self.organizations_client = self.session.client('organizations', region_name='us-east-1')
        self.sts_client = self.session.client('sts')
        
    def _create_session(self) -> boto3.Session:
        """Create boto3 session with profile if specified"""
        if self.profile_name:
            return boto3.Session(profile_name=self.profile_name)
        return boto3.Session()
    
    def get_current_account_info(self) -> Dict:
        """Get current AWS account information"""
        try:
            response = self.sts_client.get_caller_identity()
            account_id = response['Account']
            account_info = AWS_ACCOUNTS.get(account_id, {
                "name": f"Account {account_id}",
                "environment": "unknown",
                "type": "unknown"
            })
            account_info["id"] = account_id
            return account_info
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def calculate_ai_costs(self, start_date: str, end_date: str) -> Dict:
        """Calculate AI costs with high accuracy"""
        results = {
            "account": self.get_current_account_info(),
            "date_range": {"start": start_date, "end": end_date},
            "services": {},
            "projects": defaultdict(lambda: {"cost": Decimal("0"), "resources": []}),
            "total_cost": Decimal("0"),
            "total_ai_cost": Decimal("0"),
            "accuracy_metrics": {
                "tagged_resources": 0,
                "matched_resources": 0,
                "confidence_score": 0.0
            }
        }
        
        # Get costs by service
        for service_key, service_config in AI_SERVICE_CONFIG.items():
            service_costs = self._get_service_costs(
                service_config["service_codes"],
                start_date,
                end_date
            )
            
            if service_costs["total"] > 0:
                ai_portion = Decimal(str(service_costs["total"])) * Decimal(str(service_config["cost_percentage"] / 100))
                
                results["services"][service_key] = {
                    "name": service_config["name"],
                    "total_cost": float(service_costs["total"]),
                    "ai_cost": float(ai_portion),
                    "percentage": service_config["cost_percentage"],
                    "resources": service_costs.get("resources", []),
                    "tagged_costs": service_costs.get("tagged_costs", {})
                }
                
                results["total_cost"] = results["total_cost"] + Decimal(str(service_costs["total"]))
                results["total_ai_cost"] = results["total_ai_cost"] + ai_portion
                
                # Map resources to projects
                self._map_resources_to_projects(
                    service_key,
                    service_config,
                    service_costs,
                    results["projects"]
                )
        
        # Calculate accuracy metrics
        results["accuracy_metrics"] = self._calculate_accuracy_metrics(results)
        
        # Convert Decimals for JSON serialization
        results["total_cost"] = float(results["total_cost"])
        results["total_ai_cost"] = float(results["total_ai_cost"])
        results["projects"] = dict(results["projects"])
        
        for project in results["projects"].values():
            project["cost"] = float(project["cost"])
        
        return results
    
    def _get_service_costs(self, service_codes: List[str], start_date: str, end_date: str) -> Dict:
        """Get costs for specific services with detailed breakdown"""
        try:
            # Get untagged costs
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': service_codes
                    }
                },
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'},
                    {'Type': 'DIMENSION', 'Key': 'OPERATION'}
                ]
            )
            
            total_cost = Decimal("0")
            resources = []
            
            for result in response['ResultsByTime']:
                for group in result.get('Groups', []):
                    cost = Decimal(group['Metrics']['UnblendedCost']['Amount'])
                    if cost > 0:
                        total_cost += cost
                        resources.append({
                            'usage_type': group['Keys'][0],
                            'operation': group['Keys'][1],
                            'cost': float(cost)
                        })
            
            # Get tagged costs if available
            tagged_costs = self._get_tagged_costs(service_codes, start_date, end_date)
            
            return {
                'total': float(total_cost),
                'resources': resources,
                'tagged_costs': tagged_costs
            }
            
        except Exception as e:
            logger.error(f"Error getting service costs: {e}")
            return {'total': 0, 'resources': [], 'tagged_costs': {}}
    
    def _get_tagged_costs(self, service_codes: List[str], start_date: str, end_date: str) -> Dict:
        """Get costs broken down by tags"""
        tagged_costs = {}
        
        for tag in COST_ALLOCATION_TAGS:
            try:
                response = self.ce_client.get_cost_and_usage(
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': service_codes
                        }
                    },
                    GroupBy=[{'Type': 'TAG', 'Key': tag}]
                )
                
                tag_values = {}
                for result in response['ResultsByTime']:
                    for group in result.get('Groups', []):
                        tag_value = group['Keys'][0] if group['Keys'][0] else 'untagged'
                        cost = float(group['Metrics']['UnblendedCost']['Amount'])
                        if cost > 0:
                            tag_values[tag_value] = tag_values.get(tag_value, 0) + cost
                
                if tag_values:
                    tagged_costs[tag] = tag_values
                    
            except Exception as e:
                logger.debug(f"Could not get tagged costs for {tag}: {e}")
        
        return tagged_costs
    
    def _map_resources_to_projects(self, service_key: str, service_config: Dict, 
                                  service_costs: Dict, projects: Dict) -> None:
        """Map resources to specific projects based on configuration"""
        resources = service_config.get("resources", {})
        
        for project_key, project_resources in resources.items():
            if project_key in AI_PROJECTS:
                # Check tagged costs first
                for tag, values in service_costs.get("tagged_costs", {}).items():
                    for tag_value, cost in values.items():
                        if project_key in tag_value.lower():
                            projects[project_key]["cost"] += Decimal(str(cost))
                            projects[project_key]["resources"].append({
                                "service": service_config["name"],
                                "type": "tagged",
                                "tag": f"{tag}={tag_value}",
                                "cost": cost
                            })
                
                # Check specific resource names
                for resource in service_costs.get("resources", []):
                    for project_resource in project_resources:
                        if isinstance(project_resource, str):
                            if project_resource.lower() in resource.get("usage_type", "").lower():
                                cost = Decimal(str(resource["cost"])) * Decimal(str(service_config["cost_percentage"] / 100))
                                projects[project_key]["cost"] += cost
                                projects[project_key]["resources"].append({
                                    "service": service_config["name"],
                                    "type": "matched",
                                    "resource": project_resource,
                                    "cost": float(cost)
                                })
    
    def _calculate_accuracy_metrics(self, results: Dict) -> Dict:
        """Calculate accuracy metrics for the cost calculation"""
        metrics = {
            "tagged_resources": 0,
            "matched_resources": 0,
            "total_resources": 0,
            "confidence_score": 0.0
        }
        
        for service in results["services"].values():
            for tag_costs in service.get("tagged_costs", {}).values():
                metrics["tagged_resources"] += len(tag_costs)
            metrics["total_resources"] += len(service.get("resources", []))
        
        for project in results["projects"].values():
            for resource in project["resources"]:
                if resource["type"] == "matched":
                    metrics["matched_resources"] += 1
        
        # Calculate confidence score based on tagging and matching
        if metrics["total_resources"] > 0:
            tagged_ratio = metrics["tagged_resources"] / metrics["total_resources"]
            matched_ratio = metrics["matched_resources"] / metrics["total_resources"]
            metrics["confidence_score"] = min(1.0, (tagged_ratio * 0.7 + matched_ratio * 0.3) * 100)
        
        return metrics
    
    def get_cost_forecast(self, months: int = 3) -> Dict:
        """Forecast future AI costs based on historical data"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)  # 3 months of data
        
        historical_costs = []
        current = start_date
        
        while current < end_date:
            month_end = (current.replace(day=1) + timedelta(days=31)).replace(day=1)
            costs = self.calculate_ai_costs(
                current.strftime('%Y-%m-%d'),
                min(month_end, end_date).strftime('%Y-%m-%d')
            )
            historical_costs.append(costs["total_ai_cost"])
            current = month_end
        
        if historical_costs:
            avg_monthly_cost = sum(historical_costs) / len(historical_costs)
            growth_rate = 0.1  # Assume 10% monthly growth
            
            forecast = {
                "historical_average": avg_monthly_cost,
                "forecast_months": []
            }
            
            for i in range(1, months + 1):
                forecast_cost = avg_monthly_cost * (1 + growth_rate) ** i
                forecast["forecast_months"].append({
                    "month": (end_date + timedelta(days=30 * i)).strftime('%Y-%m'),
                    "estimated_cost": forecast_cost
                })
            
            return forecast
        
        return {"error": "No historical data available"}