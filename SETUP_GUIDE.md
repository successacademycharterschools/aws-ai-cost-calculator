# 🚀 AWS AI Cost Calculator - Complete Setup Guide

This guide will walk you through setting up the AWS AI Cost Calculator on your Mac in just a few minutes.

## 📋 Prerequisites

Before starting, make sure you have:

1. **macOS** (10.15 or later)
2. **Internet connection**
3. **AWS/Okta login credentials** (Success Academies SSO)
4. **5 minutes** of time

## 🎯 Quick Start (2 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/successacademycharterschools/aws-ai-cost-calculator.git

# 2. Enter the directory
cd aws-ai-cost-calculator

# 3. Run the setup script
python3 setup_and_run.py
```

That's it! The script will handle everything else and open your browser.

## 📖 Detailed Setup Steps

### Step 1: Clone the Repository

Open Terminal and run:
```bash
git clone https://github.com/successacademycharterschools/aws-ai-cost-calculator.git
cd aws-ai-cost-calculator
```

### Step 2: Run the Automated Setup

```bash
python3 setup_and_run.py
```

This script will:
- ✅ Check your Python version
- ✅ Install AWS CLI if needed
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Configure AWS SSO
- ✅ Launch the web interface

### Step 3: AWS SSO Login (First Time Only)

When prompted:

1. **The script will show:**
   ```
   🔐 Checking AWS SSO configuration...
   Configure AWS SSO now? (y/n): y
   ```

2. **Your browser will open** to the Success Academies SSO page
   - URL: `https://d-9067640efb.awsapps.com/start`
   - Login with your Okta credentials

3. **After login**, return to Terminal and you'll see:
   ```
   ✅ SSO authentication complete
   ```

### Step 4: Access the Application

The web interface will automatically open at:
- **URL**: `http://localhost:5001`
- **Backup URL**: `http://127.0.0.1:5001`

## 🎨 Using the Web Interface

### Main Features:

1. **Dashboard View**
   - Total AI costs across all services
   - Cost breakdown by service (Bedrock, Lambda, S3, etc.)
   - Project-specific costs (Ask Eva, IEP Report, etc.)

2. **Date Selection**
   - Choose custom date ranges
   - Default: Last 30 days
   - Maximum: 12 months history

3. **Export Options**
   - Download as CSV for Excel
   - Export as JSON for processing

### Understanding the Numbers:

The calculator shows:
- **Total AWS Costs**: All AWS services
- **AI-Specific Costs**: Calculated portion attributed to AI
- **Service Breakdown**: Individual service costs
- **Project Attribution**: Costs mapped to specific projects

## 🔍 Verifying Accuracy

To ensure the numbers are accurate:

1. **Cross-check with AWS Console:**
   ```
   AWS Console → Cost Explorer → Filter by Service
   Compare with calculator output
   ```

2. **AI Cost Attribution:**
   - **100%**: Bedrock, Kendra, SageMaker (fully AI services)
   - **30%**: Lambda (estimated AI workloads)
   - **20%**: S3 (AI data storage)
   - **25%**: DynamoDB (conversation history)

3. **Resource Matching:**
   - Lambda: `sa-ai-*`, `*ask-eva*`, `*iep-report*`
   - S3: `sa-ai-*`, `*-modeltraining`
   - DynamoDB: `sa_ai_ask_eva_conversation_history`

## 🛠️ Troubleshooting

### Issue: "No costs showing"

**Solution**: AWS costs take 24-48 hours to appear
```bash
# Use test data instead:
python3 test_offline_processing.py
```

### Issue: "Port 5001 already in use"

**Solution**: The script will automatically try port 5002
```bash
# Or manually specify a port:
cd web-interface
python3 app.py --port 5003
```

### Issue: "AWS authentication failed"

**Solution**: Re-login to AWS SSO
```bash
aws sso login --profile sa-sandbox
```

### Issue: "Module not found"

**Solution**: Activate virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 🔐 Security Notes

- **No credentials stored**: Uses temporary AWS SSO tokens
- **Read-only access**: Only queries cost data
- **Local only**: Runs on your machine, no external servers
- **Session-based**: Tokens expire after 1 hour

## 📊 For Demos

When demonstrating to stakeholders:

1. **Show real-time data**: Click "Refresh" to get latest costs
2. **Highlight savings**: Compare current vs projected costs
3. **Export reports**: Download CSV for presentations
4. **Project breakdown**: Show costs per AI initiative

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: Look in Terminal for error messages
2. **Verify prerequisites**: Ensure AWS CLI is installed
3. **Test AWS access**: Run `aws sts get-caller-identity --profile sa-sandbox`
4. **Contact support**: Reach out to the dev team

## 🎯 Quick Commands Reference

```bash
# First time setup
python3 setup_and_run.py

# Run web interface only
cd web-interface && python3 app.py

# Run command-line version
python3 demo_high_accuracy.py

# Test with sample data
python3 test_offline_processing.py

# Check AWS connection
aws sts get-caller-identity --profile sa-sandbox

# Re-login to AWS
aws sso login --profile sa-sandbox
```

## ✅ Success Checklist

You're ready when you can:
- [ ] See the web interface at http://localhost:5001
- [ ] View cost data in the dashboard
- [ ] Export data to CSV/JSON
- [ ] See costs broken down by service
- [ ] View project-specific costs

---

**Need help?** The setup script provides helpful error messages and suggestions at each step!