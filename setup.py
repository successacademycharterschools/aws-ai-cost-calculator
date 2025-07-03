#!/usr/bin/env python3
"""
AWS AI Cost Calculator - Interactive Setup Script
This script will help you set up the AWS AI Cost Calculator on your machine.
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path

# Colors for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Print welcome banner"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        AWS AI Cost Calculator - Setup Assistant            ║")
    print("║                                                            ║")
    print("║  This tool helps track AI service costs across AWS        ║")
    print("║  accounts with SSO/Okta authentication                     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    print(f"{Colors.BLUE}🔍 Checking Python version...{Colors.END}")
    if sys.version_info < (3, 8):
        print(f"{Colors.RED}❌ Python 3.8 or higher is required. You have {sys.version}{Colors.END}")
        sys.exit(1)
    print(f"{Colors.GREEN}✅ Python {sys.version.split()[0]} detected{Colors.END}")

def check_aws_cli():
    """Check if AWS CLI is installed"""
    print(f"\n{Colors.BLUE}🔍 Checking AWS CLI installation...{Colors.END}")
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ AWS CLI is installed: {result.stdout.strip()}{Colors.END}")
            return True
    except FileNotFoundError:
        pass
    
    print(f"{Colors.YELLOW}⚠️  AWS CLI not found. Would you like to install it?{Colors.END}")
    print("   Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
    response = input("\nContinue without AWS CLI? (y/n): ").lower()
    return response == 'y'

def create_virtual_environment():
    """Create virtual environment"""
    print(f"\n{Colors.BLUE}🔧 Setting up virtual environment...{Colors.END}")
    
    venv_path = Path('venv')
    if venv_path.exists():
        print(f"{Colors.YELLOW}Virtual environment already exists.{Colors.END}")
        response = input("Would you like to recreate it? (y/n): ").lower()
        if response == 'y':
            import shutil
            shutil.rmtree('venv')
        else:
            return
    
    subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
    print(f"{Colors.GREEN}✅ Virtual environment created{Colors.END}")
    
    # Get activation command based on OS
    if platform.system() == 'Windows':
        activate_cmd = 'venv\\Scripts\\activate'
    else:
        activate_cmd = 'source venv/bin/activate'
    
    print(f"\n{Colors.YELLOW}To activate the virtual environment, run:{Colors.END}")
    print(f"   {activate_cmd}")

def install_dependencies():
    """Install required dependencies"""
    print(f"\n{Colors.BLUE}📦 Installing dependencies...{Colors.END}")
    
    # Determine pip path
    if platform.system() == 'Windows':
        pip_path = 'venv\\Scripts\\pip'
    else:
        pip_path = 'venv/bin/pip'
    
    # Install main requirements
    print("Installing main dependencies...")
    subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
    
    # Install web interface requirements
    if os.path.exists('web-interface/requirements.txt'):
        print("\nInstalling web interface dependencies...")
        subprocess.run([pip_path, 'install', '-r', 'web-interface/requirements.txt'], check=True)
    
    print(f"{Colors.GREEN}✅ All dependencies installed{Colors.END}")

def configure_sso():
    """Configure SSO settings"""
    print(f"\n{Colors.BLUE}🔐 Configuring AWS SSO...{Colors.END}")
    
    config_file = Path('.aws-cost-config.json')
    config = {}
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"{Colors.YELLOW}Existing configuration found:{Colors.END}")
        print(f"   SSO URL: {config.get('sso_start_url', 'Not set')}")
        print(f"   Region: {config.get('sso_region', 'Not set')}")
        response = input("\nWould you like to update it? (y/n): ").lower()
        if response != 'y':
            return
    
    print("\nPlease provide your AWS SSO configuration:")
    sso_url = input("SSO Start URL (e.g., https://d-9067640efb.awsapps.com/start): ").strip()
    
    if not sso_url:
        print(f"{Colors.YELLOW}⚠️  No SSO URL provided. You can configure it later.{Colors.END}")
        return
    
    sso_region = input("SSO Region [us-east-1]: ").strip() or 'us-east-1'
    
    config = {
        'sso_start_url': sso_url,
        'sso_region': sso_region
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"{Colors.GREEN}✅ SSO configuration saved{Colors.END}")

def create_env_file():
    """Create .env file for web interface"""
    print(f"\n{Colors.BLUE}🔧 Setting up environment configuration...{Colors.END}")
    
    env_file = Path('.env')
    if env_file.exists():
        print(f"{Colors.YELLOW}.env file already exists.{Colors.END}")
        return
    
    # Copy from .env.example if it exists
    env_example = Path('.env.example')
    if env_example.exists():
        import shutil
        shutil.copy('.env.example', '.env')
        print(f"{Colors.GREEN}✅ Created .env file from template{Colors.END}")
        print(f"{Colors.YELLOW}   Please edit .env to add any API keys or secrets{Colors.END}")
    else:
        # Create basic .env file
        with open('.env', 'w') as f:
            f.write("# Environment configuration\n")
            f.write("FLASK_ENV=development\n")
            f.write("FLASK_DEBUG=True\n")
            f.write("# Add your AWS credentials here if not using SSO\n")
            f.write("# AWS_ACCESS_KEY_ID=\n")
            f.write("# AWS_SECRET_ACCESS_KEY=\n")
            f.write("# AWS_DEFAULT_REGION=us-east-1\n")
        print(f"{Colors.GREEN}✅ Created basic .env file{Colors.END}")

def setup_aws_cli_sso():
    """Offer to configure AWS CLI SSO"""
    print(f"\n{Colors.BLUE}🔧 AWS CLI SSO Configuration...{Colors.END}")
    print("Would you like to configure AWS CLI for SSO now?")
    response = input("This will open your browser for authentication (y/n): ").lower()
    
    if response == 'y':
        subprocess.run(['aws', 'configure', 'sso'])
        print(f"{Colors.GREEN}✅ AWS CLI SSO configuration complete{Colors.END}")

def print_next_steps():
    """Print next steps for the user"""
    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Setup Complete!{Colors.END}")
    print(f"\n{Colors.BLUE}Next steps:{Colors.END}")
    
    if platform.system() == 'Windows':
        activate_cmd = 'venv\\Scripts\\activate'
    else:
        activate_cmd = 'source venv/bin/activate'
    
    print(f"\n1. Activate the virtual environment:")
    print(f"   {Colors.YELLOW}{activate_cmd}{Colors.END}")
    
    print(f"\n2. Run the CLI tool:")
    print(f"   {Colors.YELLOW}python cli.py{Colors.END}")
    
    print(f"\n3. Or start the web interface:")
    print(f"   {Colors.YELLOW}cd web-interface && python app.py{Colors.END}")
    print(f"   Then open: {Colors.BLUE}http://localhost:5002{Colors.END}")
    
    print(f"\n{Colors.BLUE}Features:{Colors.END}")
    print("   • SSO/Okta authentication")
    print("   • Automatic AI resource discovery")
    print("   • Cost breakdown by service and project")
    print("   • AI-powered optimization recommendations")
    print("   • Export to CSV/JSON")
    
    print(f"\n{Colors.YELLOW}Need help?{Colors.END}")
    print("   • Check README.md for detailed documentation")
    print("   • View logs in server.log for troubleshooting")
    print("   • Ensure you have proper AWS permissions")

def main():
    """Main setup function"""
    print_banner()
    
    try:
        # Check prerequisites
        check_python_version()
        aws_cli_available = check_aws_cli()
        
        # Setup environment
        create_virtual_environment()
        install_dependencies()
        
        # Configuration
        configure_sso()
        create_env_file()
        
        # Optional AWS CLI setup
        if aws_cli_available:
            setup_aws_cli_sso()
        
        # Done!
        print_next_steps()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup cancelled by user.{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Setup failed: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()