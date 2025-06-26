#!/usr/bin/env python3
"""
Interactive CLI for AWS AI Cost Calculator
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from sso_cost_calculator import SSOCostCalculator

console = Console()

OKTA_SSO_INSTRUCTIONS = """
# AWS SSO Login via Okta

Since you access AWS through Okta, here's what will happen:

1. **Enter your SSO URL** - This should be something like:
   `https://successacademies.awsapps.com/start`

2. **Browser will open** to your Okta login page

3. **Log in with your Okta credentials**

4. **Select AWS accounts** to analyze

The tool will then automatically discover all AI services and calculate costs.
"""

@click.command()
@click.option('--export', is_flag=True, help='Export results to CSV/JSON')
@click.option('--all-accounts', is_flag=True, help='Automatically select all available accounts')
def main(export, all_accounts):
    """AWS AI Cost Calculator with SSO Authentication"""
    
    console.print(Panel.fit(
        "[bold blue]AWS AI Cost Calculator[/bold blue]\n"
        "[dim]Automated discovery and cost analysis for AI services[/dim]",
        border_style="blue"
    ))
    
    # Show Okta SSO instructions
    console.print("\n")
    console.print(Markdown(OKTA_SSO_INSTRUCTIONS))
    console.print("\n")
    
    # Confirm to proceed
    if not click.confirm("Ready to proceed with SSO login?", default=True):
        console.print("[yellow]Cancelled by user[/yellow]")
        return
    
    # Run the calculator
    try:
        calculator = SSOCostCalculator()
        
        # Set flag for auto-selecting all accounts
        if all_accounts:
            calculator.authenticator.config['auto_select_all'] = True
        
        calculator.run()
        
        console.print("\n[bold green]✓ Analysis complete![/bold green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]If authentication failed, please check your SSO URL and try again.[/dim]")


if __name__ == "__main__":
    main()