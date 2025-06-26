# AWS AI Cost Calculator

Simple Python script to calculate AWS costs for AI projects across multiple environments.

## Features

- Tracks costs for 5 AI projects: Resume Knockout, Ask Eva, Resume Scoring, IEP Report, Financial Aid
- Filters Lambda costs to include only AI-related functions
- Aggregates costs from both sandbox and non-prod environments
- Automatic error handling and retry logic
- Exports results to CSV format

## Setup

1. Install AWS CLI and configure credentials:
   ```bash
   aws configure
   ```

2. Set your AWS account IDs:
   ```bash
   export AWS_SANDBOX_ACCOUNT_ID="123456789012"
   export AWS_NONPROD_ACCOUNT_ID="234567890123"
   ```

3. Run the calculator:
   ```bash
   ./run_cost_calculator.sh
   ```

   Or manually:
   ```bash
   pip install -r requirements.txt
   python ai_cost_calculator.py
   ```

## Output

The script generates `ai_project_costs.csv` with:
- Project name
- Service-level cost breakdown
- Current month costs
- Daily average costs
- Project status (POC/MVP/Paused)

## Required AWS Permissions

Your AWS credentials need the following permissions:
- `ce:GetCostAndUsage` - To query cost data
- `ce:GetCostForecast` - Optional for projections

## Configuration

The script automatically identifies AI resources by:
- Lambda function name patterns (e.g., "ask-eva-*", "iep-report-*")
- Project tags (if configured)
- Service associations defined in the code

## Error Handling

The script includes:
- Automatic retry with exponential backoff
- Continues processing if individual services fail
- Detailed logging of all operations
- Fallback mechanisms for API failures