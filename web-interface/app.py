#!/usr/bin/env python3
"""
Flask API server for AWS AI Cost Calculator
Provides web interface for the SSO cost calculator
"""

import os
import sys
import json
import logging
from datetime import datetime
from decimal import Decimal
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from botocore.exceptions import ClientError
import secrets

# Add the parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from current directory first
from sso_wrapper import WebSSOAuthenticator

# Import from parent directory
sys.path.insert(0, parent_dir)
# Try to use enhanced discovery, fall back to original if not available
try:
    from enhanced_ai_discovery import EnhancedAIDiscovery as AIServiceDiscovery
except ImportError:
    from ai_service_discovery import AIServiceDiscovery
from sso_cost_calculator import SSOCostCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal objects"""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def convert_decimals(obj):
    """Recursively convert Decimal objects to float in dictionaries"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(v) for v in obj]
    return obj

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.json_encoder = DecimalEncoder
# Enable CORS with credentials support
CORS(app, resources={r"/api/*": {
    "origins": ["http://localhost:5000", "http://127.0.0.1:5000", "http://10.0.0.64:5000"],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})

# Store calculator instances in session
calculators = {}

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test endpoint to verify API is working"""
    return jsonify({
        'status': 'ok',
        'message': 'API is working',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/debug/aws', methods=['GET'])
def debug_aws():
    """Debug endpoint to check AWS configuration"""
    try:
        import boto3
        # Try to get caller identity
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return jsonify({
            'status': 'ok',
            'aws_configured': True,
            'account': identity.get('Account', 'Unknown')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'aws_configured': False,
            'error': str(e)
        })

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    session_id = session.get('session_id')
    if session_id and session_id in calculators:
        return jsonify({
            'authenticated': True,
            'session_id': session_id,
            'sso_url': calculators[session_id].get('sso_url')
        })
    return jsonify({'authenticated': False})

@app.route('/api/auth/configure', methods=['POST'])
def configure_sso():
    """Configure SSO settings"""
    data = request.json
    sso_url = data.get('sso_url')
    sso_region = data.get('sso_region', 'us-east-1')
    
    if not sso_url:
        return jsonify({'error': 'SSO URL is required'}), 400
    
    # Create a new session
    session_id = secrets.token_hex(16)
    session['session_id'] = session_id
    
    # Store configuration
    authenticator = WebSSOAuthenticator()
    authenticator.set_config(sso_url, sso_region)
    
    calculators[session_id] = {
        'sso_url': sso_url,
        'sso_region': sso_region,
        'authenticator': authenticator,
        'discovery': AIServiceDiscovery(),
        'calculator': SSOCostCalculator()
    }
    
    return jsonify({
        'status': 'configured',
        'session_id': session_id,
        'message': 'SSO configured. Please proceed with authentication.'
    })

@app.route('/api/auth/start', methods=['POST'])
def start_auth():
    """Start SSO authentication process"""
    session_id = session.get('session_id')
    logger.info(f"Start auth called. Session ID from cookie: {session_id}")
    logger.info(f"Available calculator sessions: {list(calculators.keys())}")
    
    if not session_id or session_id not in calculators:
        logger.error(f"Session not configured. Session ID: {session_id}, Available: {list(calculators.keys())}")
        return jsonify({'error': 'Session not configured'}), 400
    
    calc_data = calculators[session_id]
    authenticator = calc_data['authenticator']
    
    try:
        logger.info(f"Starting authentication for session {session_id}")
        
        # This will return the auth URL and device code
        auth_info = authenticator.authenticate()
        
        # Store auth info in session
        calc_data['auth_info'] = auth_info
        
        logger.info(f"Authentication info received: {bool(auth_info)}")
        
        return jsonify({
            'status': 'authentication_started',
            'message': 'Authentication started. Check your browser for the SSO login page.',
            'auth_completed': True if auth_info else False,
            'details': 'A browser window should open for AWS SSO login. Please complete the authentication there.'
        })
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS Client error during authentication: {error_code} - {error_message}")
        
        if error_code == 'InvalidRequestException':
            return jsonify({
                'error': 'Invalid SSO configuration. Please check your SSO URL and region.',
                'details': error_message
            }), 400
        elif error_code == 'UnauthorizedException':
            return jsonify({
                'error': 'Authorization failed. Please check your AWS credentials.',
                'details': error_message
            }), 401
        else:
            return jsonify({
                'error': f'AWS error: {error_code}',
                'details': error_message
            }), 500
    except Exception as e:
        logger.error(f"Authentication error: {type(e).__name__}: {str(e)}")
        return jsonify({
            'error': f'Authentication failed: {type(e).__name__}',
            'details': str(e),
            'hint': 'Check the server logs for more details'
        }), 500

@app.route('/api/accounts/list', methods=['GET'])
def list_accounts():
    """List available AWS accounts"""
    session_id = session.get('session_id')
    if not session_id or session_id not in calculators:
        return jsonify({'error': 'Not authenticated'}), 401
    
    calc_data = calculators[session_id]
    if 'auth_info' not in calc_data:
        return jsonify({'error': 'Authentication required'}), 401
    
    authenticator = calc_data['authenticator']
    
    try:
        accounts = authenticator.list_accounts(calc_data['auth_info']['access_token'])
        return jsonify({'accounts': accounts})
    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/select', methods=['POST'])
def select_accounts():
    """Select accounts for analysis"""
    session_id = session.get('session_id')
    if not session_id or session_id not in calculators:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    selected_account_ids = data.get('account_ids', [])
    
    calc_data = calculators[session_id]
    calc_data['selected_accounts'] = selected_account_ids
    
    logger.info(f"Account selection saved for session {session_id}:")
    logger.info(f"  - Selected account IDs: {selected_account_ids}")
    logger.info(f"  - Number of accounts selected: {len(selected_account_ids)}")
    
    return jsonify({
        'status': 'accounts_selected',
        'selected_count': len(selected_account_ids)
    })

@app.route('/api/discover', methods=['POST'])
def discover_resources():
    """Discover AI resources in selected accounts"""
    session_id = session.get('session_id')
    if not session_id or session_id not in calculators:
        return jsonify({'error': 'Not authenticated'}), 401
    
    calc_data = calculators[session_id]
    authenticator = calc_data['authenticator']
    discovery = calc_data['discovery']
    
    # Get parameters from request
    data = request.json or {}
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    additional_services = data.get('additional_services', [])
    account_filter = data.get('account_filter', 'all')
    
    # Store dates and services in session
    calc_data['start_date'] = start_date
    calc_data['end_date'] = end_date
    calc_data['additional_services'] = additional_services
    calc_data['account_filter'] = account_filter
    
    try:
        # Get sessions for selected accounts
        all_accounts = authenticator.list_accounts(calc_data['auth_info']['access_token'])
        selected_account_ids = calc_data.get('selected_accounts', [])
        
        if not selected_account_ids:
            return jsonify({'error': 'No accounts selected. Please select at least one account.'}), 400
            
        selected_accounts = [acc for acc in all_accounts if acc['accountId'] in selected_account_ids]
        
        if not selected_accounts:
            return jsonify({'error': 'None of the selected accounts could be found.'}), 404
            
        logger.info(f"Processing {len(selected_accounts)} selected accounts out of {len(all_accounts)} total accounts")
        logger.info(f"Selected accounts: {[acc.get('accountName', acc['accountId']) for acc in selected_accounts]}")
        
        # Apply account filter
        if account_filter != 'all':
            filtered_accounts = [
                acc for acc in selected_accounts 
                if account_filter.lower() in acc.get('accountName', '').lower()
            ]
            logger.info(f"After applying filter '{account_filter}': {len(filtered_accounts)} accounts remain")
            selected_accounts = filtered_accounts
        
        discoveries = []
        for account in selected_accounts:
            # Get credentials
            creds = authenticator.get_role_credentials(
                calc_data['auth_info']['access_token'],
                account['accountId']
            )
            
            if creds:
                # Create boto3 session
                import boto3
                boto_session = boto3.Session(
                    aws_access_key_id=creds['AccessKeyId'],
                    aws_secret_access_key=creds['SecretAccessKey'],
                    aws_session_token=creds['SessionToken'],
                    region_name='us-east-1'
                )
                
                # Discover resources with additional services
                account_name = account.get('accountName', account['accountId'])
                logger.info(f"Discovering resources in account: {account_name} ({account['accountId']})")
                
                # Use enhanced discovery if available
                if hasattr(discovery, 'discover_all_ai_resources'):
                    discovery_result = discovery.discover_all_ai_resources(
                        boto_session, 
                        account_name,
                        additional_services=additional_services
                    )
                else:
                    discovery_result = discovery.discover_all_services(
                        boto_session, 
                        account_name,
                        additional_services=additional_services
                    )
                discoveries.append(discovery_result)
        
        # Store discoveries
        calc_data['discoveries'] = discoveries
        
        return jsonify({
            'status': 'discovery_complete',
            'discoveries': discoveries
        })
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/costs/calculate', methods=['POST'])
def calculate_costs():
    """Calculate costs for discovered resources"""
    session_id = session.get('session_id')
    if not session_id or session_id not in calculators:
        return jsonify({'error': 'Not authenticated'}), 401
    
    calc_data = calculators[session_id]
    calculator = calc_data['calculator']
    authenticator = calc_data['authenticator']
    
    # Get date parameters from request or use stored dates
    data = request.json or {}
    start_date = data.get('start_date') or calc_data.get('start_date')
    end_date = data.get('end_date') or calc_data.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Date range is required'}), 400
    
    try:
        # Get sessions and calculate costs
        all_accounts = authenticator.list_accounts(calc_data['auth_info']['access_token'])
        selected_account_ids = calc_data.get('selected_accounts', [])
        
        if not selected_account_ids:
            return jsonify({'error': 'No accounts selected. Please run discovery first.'}), 400
            
        selected_accounts = [acc for acc in all_accounts if acc['accountId'] in selected_account_ids]
        
        if not selected_accounts:
            return jsonify({'error': 'None of the selected accounts could be found.'}), 404
            
        logger.info(f"Calculating costs for {len(selected_accounts)} selected accounts")
        
        all_costs = []
        for account, discovery in zip(selected_accounts, calc_data.get('discoveries', [])):
            # Get credentials
            creds = authenticator.get_role_credentials(
                calc_data['auth_info']['access_token'],
                account['accountId']
            )
            
            if creds:
                # Create boto3 session
                import boto3
                boto_session = boto3.Session(
                    aws_access_key_id=creds['AccessKeyId'],
                    aws_secret_access_key=creds['SecretAccessKey'],
                    aws_session_token=creds['SessionToken'],
                    region_name='us-east-1'
                )
                
                # Calculate costs with additional services
                account_name = account.get('accountName', account['accountId'])
                logger.info(f"Calculating costs for account: {account_name} ({account['accountId']})")
                costs = calculator.calculate_costs_for_resources(
                    boto_session, account_name, discovery, start_date, end_date,
                    additional_services=calc_data.get('additional_services', [])
                )
                all_costs.append(costs)
        
        # Convert all Decimal values in costs to float
        all_costs = convert_decimals(all_costs)
        
        # Calculate totals and projections
        grand_total = sum(c['total'] for c in all_costs)
        
        # Calculate days in selected period
        from datetime import datetime as dt
        start = dt.strptime(start_date, '%Y-%m-%d')
        end = dt.strptime(end_date, '%Y-%m-%d')
        days_in_period = (end - start).days + 1
        
        daily_avg = float(grand_total) / days_in_period if days_in_period > 0 else 0
        projection_57_schools = float(grand_total) * 57
        
        result = {
            'costs_by_account': all_costs,
            'grand_total': float(grand_total),
            'daily_average': daily_avg,
            'projection_57_schools': projection_57_schools,
            'period': f"{start_date} to {end_date}"
        }
        
        # Store results
        calc_data['results'] = result
        
        # Convert all Decimal values to float before returning
        result = convert_decimals(result)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Cost calculation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<format>', methods=['GET'])
def export_results(format):
    """Export results in specified format"""
    session_id = session.get('session_id')
    if not session_id or session_id not in calculators:
        return jsonify({'error': 'Not authenticated'}), 401
    
    calc_data = calculators[session_id]
    if 'results' not in calc_data:
        return jsonify({'error': 'No results to export'}), 400
    
    if format == 'json':
        return jsonify(calc_data['results'])
    elif format == 'csv':
        # Generate CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Account', 'Service', 'Cost', 'Project'])
        
        for account_costs in calc_data['results']['costs_by_account']:
            account_name = account_costs['account']
            for service, cost in account_costs.get('services', {}).items():
                writer.writerow([account_name, service.upper(), f"${cost:.2f}", 'All Projects'])
            
            for project, cost in account_costs.get('projects', {}).items():
                if cost > 0:
                    writer.writerow([account_name, 'Multiple', f"${cost:.2f}", project])
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=ai_costs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    else:
        return jsonify({'error': 'Invalid format'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)