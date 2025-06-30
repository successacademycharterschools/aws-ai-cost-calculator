#!/usr/bin/env python3
"""
Secure runner that loads credentials from .env file
"""

import os
import sys
from dotenv import load_dotenv
import subprocess

def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists('.env'):
        print("❌ Error: .env file not found!")
        print("\nTo create one:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your AWS credentials")
        print("3. Make sure .env is in .gitignore (it already is)")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Check required variables
    required = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing = [var for var in required if not os.environ.get(var)]
    
    if missing:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing)}")
        return False
    
    print("✅ Environment configured successfully")
    return True

def run_cost_export():
    """Run the cost export script"""
    if not check_env_file():
        return
    
    print("\n📊 Exporting AWS costs...")
    try:
        # Run the export script
        result = subprocess.run(['./simple_cost_export.sh'], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print("✅ Cost export completed")
            print("\n📈 Processing costs...")
            # Process the exported data
            subprocess.run([sys.executable, 'process_cost_exports.py'])
        else:
            print(f"❌ Export failed: {result.stderr}")
    except FileNotFoundError:
        print("❌ AWS CLI not found. Please install it first.")
        print("   brew install awscli  # on macOS")
        print("   pip install awscli   # or via pip")

if __name__ == "__main__":
    run_cost_export()