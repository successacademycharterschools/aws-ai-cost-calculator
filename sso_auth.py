#!/usr/bin/env python3
"""
AWS SSO Authentication Handler
Handles browser-based SSO login and token management
"""

import os
import json
import time
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError, TokenRetrievalError
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import track

console = Console()

class SSOAuthenticator:
    def __init__(self):
        self.sso_client = None
        self.sso_oidc_client = None
        self.credentials_cache = {}
        self.config_file = ".aws-cost-config.json"
        self.load_config()
    
    def load_config(self):
        """Load saved configuration if available"""
        self.config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                console.print("[green]✓[/green] Loaded saved configuration")
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not load config: {e}")
    
    def save_config(self):
        """Save configuration for future use"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            console.print("[green]✓[/green] Configuration saved")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not save config: {e}")
    
    def get_sso_config(self) -> Tuple[str, str]:
        """Get SSO configuration from user or saved config"""
        console.print("\n[bold blue]AWS SSO Configuration[/bold blue]")
        console.print("[dim]Note: This should be your AWS SSO portal URL, not the Okta SAML URL[/dim]")
        console.print("[dim]It typically looks like: https://[your-company].awsapps.com/start[/dim]")
        console.print("[dim]You can find it in the AWS SSO settings or ask your AWS administrator[/dim]\n")
        
        # Get SSO Start URL
        default_url = self.config.get('sso_start_url', '')
        sso_start_url = Prompt.ask(
            "Enter your AWS SSO start URL",
            default=default_url if default_url else None,
            console=console
        )
        
        # Get SSO Region
        default_region = self.config.get('sso_region', 'us-east-1')
        sso_region = Prompt.ask(
            "Enter AWS region",
            default=default_region,
            console=console
        )
        
        # Save config
        self.config['sso_start_url'] = sso_start_url
        self.config['sso_region'] = sso_region
        
        if Confirm.ask("Save this configuration for future use?", default=True):
            self.save_config()
        
        return sso_start_url, sso_region
    
    def authenticate(self) -> Dict[str, any]:
        """Perform SSO authentication"""
        sso_start_url, sso_region = self.get_sso_config()
        
        # Initialize SSO clients
        self.sso_oidc_client = boto3.client('sso-oidc', region_name=sso_region)
        self.sso_client = boto3.client('sso', region_name=sso_region)
        
        try:
            # Start device authorization
            console.print("\n[bold]Starting SSO authentication...[/bold]")
            
            # Register client
            client_creds = self.sso_oidc_client.register_client(
                clientName='aws-ai-cost-calculator',
                clientType='public'
            )
            
            # Start device authorization
            device_auth = self.sso_oidc_client.start_device_authorization(
                clientId=client_creds['clientId'],
                clientSecret=client_creds['clientSecret'],
                startUrl=sso_start_url
            )
            
            # Display authorization URL
            console.print(f"\n[bold yellow]Please visit:[/bold yellow] {device_auth['verificationUriComplete']}")
            console.print(f"[dim]Or manually enter code:[/dim] {device_auth['userCode']}")
            
            # Open browser
            if Confirm.ask("\nOpen browser automatically?", default=True):
                webbrowser.open(device_auth['verificationUriComplete'])
            
            # Poll for token
            console.print("\n[bold]Waiting for authentication...[/bold]")
            token = self._poll_for_token(
                client_creds['clientId'],
                client_creds['clientSecret'],
                device_auth['deviceCode'],
                device_auth['interval']
            )
            
            if token:
                console.print("[green]✓[/green] Authentication successful!")
                return {
                    'access_token': token['accessToken'],
                    'sso_region': sso_region,
                    'start_url': sso_start_url,
                    'expires_at': datetime.now() + timedelta(seconds=token['expiresIn'])
                }
            else:
                raise Exception("Authentication failed")
                
        except Exception as e:
            console.print(f"[red]Error during authentication:[/red] {e}")
            raise
    
    def _poll_for_token(self, client_id: str, client_secret: str, 
                       device_code: str, interval: int) -> Optional[Dict]:
        """Poll for authentication token"""
        timeout = 600  # 10 minutes
        elapsed = 0
        
        with console.status("[bold blue]Authenticating...") as status:
            while elapsed < timeout:
                try:
                    token_response = self.sso_oidc_client.create_token(
                        clientId=client_id,
                        clientSecret=client_secret,
                        grantType='urn:ietf:params:oauth:grant-type:device_code',
                        deviceCode=device_code
                    )
                    return token_response
                except self.sso_oidc_client.exceptions.AuthorizationPendingException:
                    time.sleep(interval)
                    elapsed += interval
                    status.update(f"[bold blue]Authenticating... ({elapsed}s)")
                except Exception as e:
                    console.print(f"[red]Token error:[/red] {e}")
                    return None
        
        return None
    
    def list_accounts(self, access_token: str) -> List[Dict]:
        """List available AWS accounts"""
        try:
            paginator = self.sso_client.get_paginator('list_accounts')
            accounts = []
            
            for page in paginator.paginate(accessToken=access_token):
                accounts.extend(page['accountList'])
            
            return accounts
        except Exception as e:
            console.print(f"[red]Error listing accounts:[/red] {e}")
            return []
    
    def get_role_credentials(self, access_token: str, account_id: str, 
                           role_name: str = None) -> Optional[Dict]:
        """Get temporary credentials for an account"""
        try:
            # List roles if not specified
            if not role_name:
                roles = self.sso_client.list_account_roles(
                    accessToken=access_token,
                    accountId=account_id
                )
                
                if roles['roleList']:
                    # Use first available role
                    role_name = roles['roleList'][0]['roleName']
                else:
                    console.print(f"[red]No roles available for account {account_id}[/red]")
                    return None
            
            # Get role credentials
            creds = self.sso_client.get_role_credentials(
                accessToken=access_token,
                accountId=account_id,
                roleName=role_name
            )
            
            return {
                'AccessKeyId': creds['roleCredentials']['accessKeyId'],
                'SecretAccessKey': creds['roleCredentials']['secretAccessKey'],
                'SessionToken': creds['roleCredentials']['sessionToken'],
                'Expiration': datetime.fromtimestamp(creds['roleCredentials']['expiration'] / 1000)
            }
            
        except Exception as e:
            console.print(f"[red]Error getting credentials:[/red] {e}")
            return None
    
    def select_accounts(self, accounts: List[Dict]) -> List[Dict]:
        """Interactive account selection"""
        console.print("\n[bold]Available AWS Accounts:[/bold]")
        
        # Display accounts table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Account Name", style="cyan")
        table.add_column("Account ID", style="green")
        table.add_column("Email", style="dim")
        
        for idx, account in enumerate(accounts, 1):
            table.add_row(
                str(idx),
                account.get('accountName', 'N/A'),
                account['accountId'],
                account.get('emailAddress', 'N/A')
            )
        
        console.print(table)
        
        # Get selection
        selection = Prompt.ask(
            "\nSelect accounts to analyze (comma-separated numbers or 'all')",
            default="all"
        )
        
        if selection.lower() == 'all':
            return accounts
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                selected = [accounts[i] for i in indices if 0 <= i < len(accounts)]
                return selected
            except (ValueError, IndexError):
                console.print("[red]Invalid selection. Using all accounts.[/red]")
                return accounts
    
    def get_authenticated_sessions(self) -> List[Tuple[str, boto3.Session]]:
        """Get authenticated boto3 sessions for selected accounts"""
        # Authenticate
        auth_info = self.authenticate()
        
        # List accounts
        accounts = self.list_accounts(auth_info['access_token'])
        if not accounts:
            raise Exception("No AWS accounts available")
        
        # Select accounts
        selected_accounts = self.select_accounts(accounts)
        
        # Get credentials for each account
        sessions = []
        console.print("\n[bold]Getting credentials for selected accounts...[/bold]")
        
        for account in track(selected_accounts, description="Processing accounts"):
            creds = self.get_role_credentials(
                auth_info['access_token'],
                account['accountId']
            )
            
            if creds:
                # Create boto3 session
                session = boto3.Session(
                    aws_access_key_id=creds['AccessKeyId'],
                    aws_secret_access_key=creds['SecretAccessKey'],
                    aws_session_token=creds['SessionToken'],
                    region_name='us-east-1'  # Cost Explorer requires us-east-1
                )
                
                account_name = account.get('accountName', account['accountId'])
                sessions.append((account_name, session))
                console.print(f"  [green]✓[/green] {account_name}")
            else:
                console.print(f"  [red]✗[/red] Failed to get credentials for {account.get('accountName', account['accountId'])}")
        
        return sessions


if __name__ == "__main__":
    # Test authentication
    auth = SSOAuthenticator()
    try:
        sessions = auth.get_authenticated_sessions()
        console.print(f"\n[green]Successfully authenticated to {len(sessions)} account(s)![/green]")
    except Exception as e:
        console.print(f"[red]Authentication failed:[/red] {e}")