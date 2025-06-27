#!/usr/bin/env python3
"""
Simplified SSO wrapper for web interface
Removes console output dependencies
"""

import os
import sys
import json
import time
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

# Add the SSO calculator to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'aws-ai-cost-calculator-sso'))

class WebSSOAuthenticator:
    """Simplified SSO authenticator for web use"""
    
    def __init__(self):
        self.sso_client = None
        self.sso_oidc_client = None
        self.credentials_cache = {}
        self.config = {}
    
    def set_config(self, sso_start_url: str, sso_region: str):
        """Set SSO configuration"""
        self.config['sso_start_url'] = sso_start_url
        self.config['sso_region'] = sso_region
    
    def authenticate(self) -> Dict[str, any]:
        """Perform SSO authentication"""
        sso_start_url = self.config.get('sso_start_url')
        sso_region = self.config.get('sso_region', 'us-east-1')
        
        if not sso_start_url:
            raise ValueError("SSO start URL not configured")
        
        # Initialize SSO clients
        self.sso_oidc_client = boto3.client('sso-oidc', region_name=sso_region)
        self.sso_client = boto3.client('sso', region_name=sso_region)
        
        # Register client
        client_creds = self.sso_oidc_client.register_client(
            clientName='aws-ai-cost-calculator-web',
            clientType='public'
        )
        
        # Start device authorization
        device_auth = self.sso_oidc_client.start_device_authorization(
            clientId=client_creds['clientId'],
            clientSecret=client_creds['clientSecret'],
            startUrl=sso_start_url
        )
        
        # Open browser for authentication
        webbrowser.open(device_auth['verificationUriComplete'])
        
        # Poll for token
        token = self._poll_for_token(
            client_creds['clientId'],
            client_creds['clientSecret'],
            device_auth['deviceCode'],
            device_auth['interval']
        )
        
        if token:
            return {
                'access_token': token['accessToken'],
                'sso_region': sso_region,
                'start_url': sso_start_url,
                'expires_at': datetime.now() + timedelta(seconds=token['expiresIn'])
            }
        else:
            raise Exception("Authentication failed")
    
    def _poll_for_token(self, client_id: str, client_secret: str, 
                       device_code: str, interval: int) -> Optional[Dict]:
        """Poll for authentication token"""
        timeout = 600  # 10 minutes
        elapsed = 0
        
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
            except Exception as e:
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
            raise Exception(f"Error listing accounts: {e}")
    
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
                    role_name = roles['roleList'][0]['roleName']
                else:
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
            raise Exception(f"Error getting credentials: {e}")