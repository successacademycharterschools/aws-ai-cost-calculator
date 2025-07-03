#!/usr/bin/env python3
"""
AWS AI Cost Calculator - Easy Setup & Run Script
This script handles all setup requirements and launches the application
"""

import os
import sys
import subprocess
import shutil
import json
import platform
import time
from pathlib import Path

class Colors:
    """Terminal colors for better output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Display welcome banner"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}")
    print("="*60)
    print("   AWS AI Cost Calculator - Easy Setup")
    print("   Success Academies")
    print("="*60)
    print(f"{Colors.ENDC}\n")

def check_python_version():
    """Ensure Python 3.8+ is installed"""
    print(f"{Colors.BLUE}🔍 Checking Python version...{Colors.ENDC}")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"{Colors.RED}❌ Python 3.8+ required. You have {version.major}.{version.minor}{Colors.ENDC}")
        print(f"{Colors.YELLOW}📦 Install Python 3.8+ from https://python.org{Colors.ENDC}")
        return False
    print(f"{Colors.GREEN}✅ Python {version.major}.{version.minor} - OK{Colors.ENDC}")
    return True

def check_aws_cli():
    """Check if AWS CLI is installed"""
    print(f"\n{Colors.BLUE}🔍 Checking AWS CLI...{Colors.ENDC}")
    if shutil.which('aws') is None:
        print(f"{Colors.RED}❌ AWS CLI not found{Colors.ENDC}")
        print(f"{Colors.YELLOW}📦 Install with: brew install awscli{Colors.ENDC}")
        response = input(f"{Colors.CYAN}Would you like to install it now? (y/n): {Colors.ENDC}")
        if response.lower() == 'y':
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['brew', 'install', 'awscli'])
            else:
                print(f"{Colors.YELLOW}Please install AWS CLI manually{Colors.ENDC}")
                return False
    else:
        print(f"{Colors.GREEN}✅ AWS CLI installed{Colors.ENDC}")
    return True

def create_virtual_env():
    """Create and activate virtual environment"""
    print(f"\n{Colors.BLUE}🔧 Setting up virtual environment...{Colors.ENDC}")
    
    if not os.path.exists('venv'):
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])
        print(f"{Colors.GREEN}✅ Virtual environment created{Colors.ENDC}")
    else:
        print(f"{Colors.GREEN}✅ Virtual environment exists{Colors.ENDC}")
    
    # Get activation script path
    if platform.system() == 'Windows':
        activate_cmd = 'venv\\Scripts\\activate.bat'
        python_cmd = 'venv\\Scripts\\python.exe'
        pip_cmd = 'venv\\Scripts\\pip.exe'
    else:
        activate_cmd = 'source venv/bin/activate'
        python_cmd = 'venv/bin/python3'
        pip_cmd = 'venv/bin/pip3'
        
        # Check if the commands exist, fallback to python/pip if needed
        if not os.path.exists(python_cmd):
            python_cmd = 'venv/bin/python'
        if not os.path.exists(pip_cmd):
            pip_cmd = 'venv/bin/pip'
    
    return python_cmd, pip_cmd, activate_cmd

def install_dependencies(pip_cmd):
    """Install all required dependencies"""
    print(f"\n{Colors.BLUE}📦 Installing dependencies...{Colors.ENDC}")
    
    # Create combined requirements if needed
    requirements_files = ['requirements.txt']
    if os.path.exists('web-interface/requirements.txt'):
        requirements_files.append('web-interface/requirements.txt')
    
    for req_file in requirements_files:
        if os.path.exists(req_file):
            print(f"Installing from {req_file}...")
            subprocess.run([pip_cmd, 'install', '-r', req_file, '--quiet'])
    
    print(f"{Colors.GREEN}✅ Dependencies installed{Colors.ENDC}")

def check_aws_sso_config():
    """Check and configure AWS SSO"""
    print(f"\n{Colors.BLUE}🔐 Checking AWS SSO configuration...{Colors.ENDC}")
    
    # Check for existing AWS config
    aws_config_path = Path.home() / '.aws' / 'config'
    has_sso_profile = False
    
    if aws_config_path.exists():
        with open(aws_config_path, 'r') as f:
            config_content = f.read()
            if 'sso_start_url' in config_content:
                has_sso_profile = True
                print(f"{Colors.GREEN}✅ AWS SSO profile found{Colors.ENDC}")
    
    if not has_sso_profile:
        print(f"{Colors.YELLOW}⚠️  No AWS SSO profile found{Colors.ENDC}")
        print(f"\n{Colors.CYAN}Let's set up AWS SSO:{Colors.ENDC}")
        print("1. I'll help you configure AWS SSO")
        print("2. You'll need your SSO URL: https://d-9067640efb.awsapps.com/start")
        print("3. Browser will open for Okta login\n")
        
        response = input(f"{Colors.CYAN}Configure AWS SSO now? (y/n): {Colors.ENDC}")
        if response.lower() == 'y':
            configure_aws_sso()
    
    return has_sso_profile

def configure_aws_sso():
    """Interactive AWS SSO configuration"""
    print(f"\n{Colors.BLUE}🔧 Configuring AWS SSO...{Colors.ENDC}")
    
    # Create AWS config
    config_content = """[profile sa-sandbox]
sso_start_url = https://d-9067640efb.awsapps.com/start
sso_region = us-east-1
sso_account_id = 529443669576
sso_role_name = AdministratorAccess
region = us-east-1
output = json

[profile sa-production]
sso_start_url = https://d-9067640efb.awsapps.com/start
sso_region = us-east-1
sso_account_id = 309820967897
sso_role_name = AdministratorAccess
region = us-east-1
output = json
"""
    
    aws_dir = Path.home() / '.aws'
    aws_dir.mkdir(exist_ok=True)
    
    config_path = aws_dir / 'config'
    
    # Backup existing config
    if config_path.exists():
        backup_path = aws_dir / 'config.backup'
        shutil.copy(config_path, backup_path)
        print(f"{Colors.YELLOW}📋 Backed up existing config to ~/.aws/config.backup{Colors.ENDC}")
    
    # Write new config
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print(f"{Colors.GREEN}✅ AWS SSO configured{Colors.ENDC}")
    print(f"\n{Colors.CYAN}Now let's authenticate:{Colors.ENDC}")
    
    # Login to SSO
    try:
        print(f"{Colors.YELLOW}🌐 Opening browser for SSO login...{Colors.ENDC}")
        subprocess.run(['aws', 'sso', 'login', '--profile', 'sa-sandbox'])
        print(f"{Colors.GREEN}✅ SSO authentication complete{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}❌ SSO login failed: {e}{Colors.ENDC}")

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        shutil.copy('.env.example', '.env')
        print(f"{Colors.GREEN}✅ Created .env file from template{Colors.ENDC}")

def check_port_availability(port=5001):
    """Check if port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def launch_application(python_cmd):
    """Launch the web interface"""
    print(f"\n{Colors.BLUE}🚀 Launching AWS AI Cost Calculator...{Colors.ENDC}")
    
    # Check port availability
    port = 5001
    if not check_port_availability(port):
        print(f"{Colors.YELLOW}⚠️  Port {port} is in use{Colors.ENDC}")
        port = 5002
        print(f"{Colors.CYAN}Using port {port} instead{Colors.ENDC}")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}✨ Application starting!{Colors.ENDC}")
    print(f"{Colors.CYAN}📊 Open your browser to: http://localhost:{port}{Colors.ENDC}")
    print(f"{Colors.YELLOW}Press Ctrl+C to stop the server{Colors.ENDC}\n")
    
    # Get absolute path to python before changing directory
    python_abs_path = os.path.abspath(python_cmd)
    
    # Change to web-interface directory and run
    os.chdir('web-interface')
    
    # Update port in app.py if needed
    if port != 5001:
        update_app_port(port)
    
    try:
        subprocess.run([python_abs_path, 'app.py'])
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}✅ Server stopped{Colors.ENDC}")

def update_app_port(port):
    """Update port in app.py if needed"""
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        content = content.replace('port=5001', f'port={port}')
        
        with open('app.py', 'w') as f:
            f.write(content)
    except:
        pass

def run_health_check(python_cmd):
    """Run a quick health check"""
    print(f"\n{Colors.BLUE}🏥 Running health check...{Colors.ENDC}")
    
    # Test AWS connection
    try:
        result = subprocess.run(['aws', 'sts', 'get-caller-identity', '--profile', 'sa-sandbox'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ AWS connection OK{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}⚠️  AWS not authenticated - will prompt during app startup{Colors.ENDC}")
    except:
        print(f"{Colors.YELLOW}⚠️  Could not verify AWS connection{Colors.ENDC}")
    
    # Test Python imports
    test_imports = """
import boto3
import flask
import pandas
print("✅ All imports OK")
"""
    
    try:
        subprocess.run([python_cmd, '-c', test_imports], capture_output=True)
        print(f"{Colors.GREEN}✅ Python dependencies OK{Colors.ENDC}")
    except:
        print(f"{Colors.YELLOW}⚠️  Some dependencies may be missing{Colors.ENDC}")

def main():
    """Main setup and run function"""
    print_banner()
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Check AWS CLI
    if not check_aws_cli():
        print(f"\n{Colors.RED}❌ Setup incomplete. Please install AWS CLI first.{Colors.ENDC}")
        sys.exit(1)
    
    # Step 3: Create virtual environment
    python_cmd, pip_cmd, activate_cmd = create_virtual_env()
    
    # Step 4: Install dependencies
    install_dependencies(pip_cmd)
    
    # Step 5: Check AWS SSO configuration
    check_aws_sso_config()
    
    # Step 6: Create .env file
    create_env_file()
    
    # Step 7: Run health check
    run_health_check(python_cmd)
    
    # Step 8: Launch application
    print(f"\n{Colors.GREEN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ Setup complete! Launching application...{Colors.ENDC}")
    print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}")
    
    time.sleep(2)
    launch_application(python_cmd)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Setup cancelled by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.ENDC}")
        print(f"{Colors.YELLOW}💡 Try running with: python3 {sys.argv[0]}{Colors.ENDC}")