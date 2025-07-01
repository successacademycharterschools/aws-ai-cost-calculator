#!/usr/bin/env python3
"""
Demo script for high-accuracy AWS AI Cost Calculator
Shows real-time cost tracking with detailed breakdowns
"""

import json
from datetime import datetime, timedelta
from enhanced_calculator import EnhancedCostCalculator
from enhanced_config import AI_PROJECTS, AI_SERVICE_CONFIG
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import print as rprint

console = Console()

def run_demo():
    """Run the high-accuracy cost calculator demo"""
    console.print("\n[bold blue]AWS AI Cost Calculator - High Accuracy Demo[/bold blue]")
    console.print("Using enhanced configuration with real-time AWS data\n")
    
    # Initialize calculator
    with Progress() as progress:
        task = progress.add_task("[cyan]Initializing AWS connection...", total=100)
        calculator = EnhancedCostCalculator(profile_name="sa-sandbox")
        progress.update(task, advance=100)
    
    # Get account info
    account_info = calculator.get_current_account_info()
    console.print(Panel(f"[green]Connected to AWS Account:[/green] {account_info.get('name', 'Unknown')} ({account_info.get('id', 'Unknown')})", 
                       title="Account Info"))
    
    # Calculate costs for last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    console.print(f"\n[yellow]Calculating AI costs from {start_date} to {end_date}...[/yellow]")
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Analyzing AWS costs...", total=100)
        results = calculator.calculate_ai_costs(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        progress.update(task, advance=100)
    
    # Display results
    console.print("\n[bold green]═══ Cost Analysis Results ═══[/bold green]\n")
    
    # Summary metrics
    summary_table = Table(title="Summary Metrics", show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="cyan", width=30)
    summary_table.add_column("Value", justify="right", style="green")
    
    summary_table.add_row("Total AWS Costs", f"${results['total_cost']:,.2f}")
    summary_table.add_row("Total AI Costs", f"${results['total_ai_cost']:,.2f}")
    summary_table.add_row("AI Cost Percentage", f"{(results['total_ai_cost'] / results['total_cost'] * 100):.1f}%")
    summary_table.add_row("Accuracy Confidence", f"{results['accuracy_metrics']['confidence_score']:.1f}%")
    
    console.print(summary_table)
    
    # Service breakdown
    console.print("\n[bold yellow]Service Cost Breakdown:[/bold yellow]")
    service_table = Table(show_header=True, header_style="bold magenta")
    service_table.add_column("Service", style="cyan", width=25)
    service_table.add_column("Total Cost", justify="right", style="white")
    service_table.add_column("AI Cost", justify="right", style="green")
    service_table.add_column("AI %", justify="right", style="yellow")
    
    for service_key, service_data in results['services'].items():
        service_table.add_row(
            service_data['name'],
            f"${service_data['total_cost']:,.2f}",
            f"${service_data['ai_cost']:,.2f}",
            f"{service_data['percentage']}%"
        )
    
    console.print(service_table)
    
    # Project breakdown
    if results['projects']:
        console.print("\n[bold yellow]AI Project Costs:[/bold yellow]")
        project_table = Table(show_header=True, header_style="bold magenta")
        project_table.add_column("Project", style="cyan", width=20)
        project_table.add_column("Description", style="white", width=40)
        project_table.add_column("Cost", justify="right", style="green")
        project_table.add_column("Status", style="yellow")
        
        for project_key, project_data in results['projects'].items():
            if project_data['cost'] > 0:
                project_info = AI_PROJECTS.get(project_key, {})
                project_table.add_row(
                    project_info.get('name', project_key),
                    project_info.get('description', 'N/A'),
                    f"${project_data['cost']:,.2f}",
                    project_info.get('status', 'Unknown')
                )
        
        console.print(project_table)
    
    # Accuracy metrics
    console.print("\n[bold yellow]Accuracy Metrics:[/bold yellow]")
    accuracy_table = Table(show_header=True, header_style="bold magenta")
    accuracy_table.add_column("Metric", style="cyan", width=30)
    accuracy_table.add_column("Value", justify="right", style="green")
    
    metrics = results['accuracy_metrics']
    accuracy_table.add_row("Tagged Resources", str(metrics['tagged_resources']))
    accuracy_table.add_row("Matched Resources", str(metrics['matched_resources']))
    accuracy_table.add_row("Total Resources", str(metrics['total_resources']))
    accuracy_table.add_row("Confidence Score", f"{metrics['confidence_score']:.1f}%")
    
    console.print(accuracy_table)
    
    # Forecast
    console.print("\n[bold yellow]Cost Forecast (Next 3 Months):[/bold yellow]")
    forecast = calculator.get_cost_forecast(months=3)
    
    if "error" not in forecast:
        forecast_table = Table(show_header=True, header_style="bold magenta")
        forecast_table.add_column("Month", style="cyan")
        forecast_table.add_column("Estimated AI Cost", justify="right", style="green")
        
        forecast_table.add_row("Historical Average", f"${forecast['historical_average']:,.2f}")
        forecast_table.add_row("---", "---")
        
        for month_data in forecast['forecast_months']:
            forecast_table.add_row(
                month_data['month'],
                f"${month_data['estimated_cost']:,.2f}"
            )
        
        console.print(forecast_table)
    
    # Save results
    output_file = f"ai_cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    console.print(f"\n[green]✓ Full report saved to:[/green] {output_file}")
    
    # Demo talking points
    console.print("\n[bold cyan]═══ Demo Talking Points ═══[/bold cyan]")
    talking_points = [
        "🎯 High-accuracy cost tracking with " + f"{results['accuracy_metrics']['confidence_score']:.0f}% confidence",
        "📊 Real-time data from AWS Cost Explorer API",
        "🏷️ Cost allocation tag support for precise tracking",
        "🔍 Automatic resource discovery and mapping",
        "📈 Intelligent cost forecasting based on trends",
        "🏢 Multi-account support via AWS SSO",
        "💰 Identifies AI-specific costs vs general infrastructure",
        "📋 Detailed project-level cost breakdown"
    ]
    
    for point in talking_points:
        console.print(f"  • {point}")
    
    console.print("\n[bold green]Demo ready! The web interface provides an interactive version of this data.[/bold green]\n")

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        console.print("\n[yellow]Make sure you have logged in with AWS SSO:[/yellow]")
        console.print("[cyan]aws sso login --profile sa-sandbox[/cyan]\n")