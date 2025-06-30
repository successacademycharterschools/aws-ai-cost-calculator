#!/usr/bin/env python3
"""
Helper script to find your AWS SSO URL
"""

import os
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def find_aws_sso_config():
    """Look for AWS SSO configuration in common locations"""
    console.print("[bold]Searching for AWS SSO configuration...[/bold]\n")
    
    sso_urls = []
    
    # Check AWS CLI config
    aws_config_path = Path.home() / '.aws' / 'config'
    if aws_config_path.exists():
        console.print(f"[green]✓[/green] Found AWS config at {aws_config_path}")
        try:
            with open(aws_config_path, 'r') as f:
                content = f.read()
                # Look for SSO URLs in the config
                for line in content.split('\n'):
                    if 'sso_start_url' in line:
                        url = line.split('=')[1].strip()
                        if url and url not in sso_urls:
                            sso_urls.append(url)
                            console.print(f"  Found SSO URL: [cyan]{url}[/cyan]")
        except Exception as e:
            console.print(f"  [yellow]Could not read config: {e}[/yellow]")
    
    # Check AWS SSO cache
    sso_cache_dir = Path.home() / '.aws' / 'sso' / 'cache'
    if sso_cache_dir.exists():
        console.print(f"\n[green]✓[/green] Found SSO cache at {sso_cache_dir}")
        for cache_file in sso_cache_dir.glob('*.json'):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if 'startUrl' in data:
                        url = data['startUrl']
                        if url and url not in sso_urls:
                            sso_urls.append(url)
                            console.print(f"  Found SSO URL: [cyan]{url}[/cyan]")
            except:
                pass
    
    return sso_urls

def main():
    console.print(Panel.fit(
        "[bold blue]AWS SSO URL Finder[/bold blue]\n"
        "[dim]This tool helps find your AWS SSO portal URL[/dim]",
        border_style="blue"
    ))
    
    # Explain the difference
    console.print("\n[bold]Understanding AWS SSO URLs:[/bold]")
    console.print("• [red]Okta SAML URL[/red]: https://successacademies.okta.com/app/amazon_aws_sso/...")
    console.print("  This is used by Okta internally for SAML authentication")
    console.print("\n• [green]AWS SSO Start URL[/green]: https://[company].awsapps.com/start")
    console.print("  This is what you need for the AWS CLI and this tool")
    
    # Search for existing config
    console.print("\n")
    found_urls = find_aws_sso_config()
    
    if found_urls:
        console.print(f"\n[bold green]Found {len(found_urls)} SSO URL(s) in your AWS configuration![/bold green]")
        console.print("\nYou should use one of these URLs with the cost calculator.")
    else:
        console.print("\n[yellow]No AWS SSO URLs found in local configuration.[/yellow]")
        console.print("\n[bold]How to find your AWS SSO URL:[/bold]")
        console.print("1. Log into AWS through Okta")
        console.print("2. Once in AWS, look at the URL - it should contain '.awsapps.com'")
        console.print("3. Or check with your AWS administrator")
        console.print("\n[dim]The URL typically looks like:[/dim]")
        console.print("  • https://successacademies.awsapps.com/start")
        console.print("  • https://sa-prod.awsapps.com/start")
        console.print("  • https://d-1234567890.awsapps.com/start")
    
    # Offer to configure AWS CLI
    console.print("\n[bold]Configure AWS CLI for SSO:[/bold]")
    console.print("If you haven't configured AWS SSO yet, run:")
    console.print("[cyan]aws configure sso[/cyan]")
    console.print("\nThis will prompt you for your SSO URL and set everything up.")

if __name__ == "__main__":
    main()