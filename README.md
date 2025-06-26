# AWS AI Cost Calculator with SSO

An interactive cost calculator for AWS AI services that uses SSO authentication (including Okta) and automatically discovers AI-related resources.

## Features

- 🔐 **SSO Authentication** - Works with AWS SSO including Okta integration
- 🔍 **Auto-Discovery** - Automatically finds AI services (Lambda, S3, Bedrock, etc.)
- 💰 **Cost Analysis** - Calculates costs per service and project
- 📊 **Project Breakdown** - Groups costs by AI project (Ask Eva, IEP Report, etc.)
- 📈 **Projections** - Shows cost projections for scaling to 57 schools
- 📁 **Export** - Saves results to CSV and JSON

## Prerequisites

1. Python 3.8 or higher
2. AWS CLI installed (for SSO authentication)
3. Access to AWS via SSO/Okta
4. IAM permissions for Cost Explorer and resource listing

## Installation

1. Clone or download this calculator:
```bash
cd /Users/lasaj917/Claude\ Code/aws-ai-cost-calculator-sso
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure AWS CLI for SSO (if not already done):
```bash
aws configure sso
```

## Usage

### Basic Usage

Run the interactive CLI:
```bash
python cli.py
```

The tool will:
1. Prompt for your AWS SSO URL (e.g., `https://successacademies.awsapps.com/start`)
2. Open your browser for Okta authentication
3. Let you select AWS accounts to analyze
4. Automatically discover AI services
5. Calculate and display costs

### Command Line Options

```bash
# Automatically select all available accounts
python cli.py --all-accounts

# Export results to CSV/JSON
python cli.py --export
```

### Direct Script Usage

For programmatic access:
```bash
python sso_cost_calculator.py
```

## How It Works

1. **Authentication**: Uses AWS SSO to authenticate via your browser
2. **Discovery**: Scans for AI resources using pattern matching:
   - Lambda: Functions with names like `*-ai-*`, `*ask-eva*`, `*iep-report*`
   - S3: Buckets like `sa-ai-*`, `*-modeltraining`
   - Bedrock: All usage (100% AI)
   - DynamoDB: Tables with AI-related names
3. **Cost Calculation**: Uses AWS Cost Explorer API to get current month costs
4. **Project Attribution**: Maps resources to projects based on naming patterns

## Configuration

The tool saves your SSO URL for convenience in `.aws-cost-config.json`:
```json
{
  "sso_start_url": "https://successacademies.awsapps.com/start",
  "sso_region": "us-east-1"
}
```

## AI Projects Tracked

- **Ask Eva**: Chatbot POC
- **IEP Report**: PDF generation for scholars
- **Resume Knockout**: Resume filtering
- **Resume Scoring**: Resume ranking
- **Financial Aid**: Cost letter filtering

## Output

### Console Output
- Service-level cost breakdown
- Project-level cost aggregation
- Total costs across all accounts
- Daily averages
- Projections for 57 schools

### Export Files
- `ai_costs_summary_YYYYMMDD_HHMMSS.csv` - Cost breakdown
- `ai_resources_YYYYMMDD_HHMMSS.json` - Discovered resources

## Troubleshooting

### SSO Login Issues
- Make sure your SSO URL is correct
- Check that you have AWS CLI installed: `aws --version`
- Ensure your Okta session hasn't expired

### Permission Errors
Required IAM permissions:
- `ce:GetCostAndUsage`
- `lambda:ListFunctions`
- `lambda:ListTags`
- `s3:ListBuckets`
- `s3:GetBucketTagging`
- `dynamodb:ListTables`
- `dynamodb:DescribeTable`
- `bedrock:List*`
- `sts:GetCallerIdentity`

### No Costs Showing
- Costs may take 24-48 hours to appear in Cost Explorer
- Check that your resources have been running in the current month
- Verify the account has AI-related resources

## Security

- No credentials are stored in the code
- SSO tokens are temporary and managed by AWS CLI
- All authentication happens through your browser
- The tool only requires read permissions

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your AWS permissions
3. Ensure resources are properly tagged

## Future Enhancements

- [ ] Historical cost trends
- [ ] More granular Lambda cost allocation
- [ ] Budget alerts
- [ ] Cost optimization recommendations
- [ ] Web dashboard interface