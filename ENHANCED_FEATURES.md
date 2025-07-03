# Enhanced AWS AI Cost Calculator - Feature Guide

## 🚀 What's New in the Enhanced Version

### 1. **Enhanced AI Resource Discovery**
The enhanced version finds MORE AI resources than before:

- **Bedrock**: Agents, Knowledge Bases, Custom Models, Inference Profiles
- **Lambda Functions**: Automatically identifies AI-related functions by:
  - Function names (e.g., contains "ai", "ml", "bedrock")
  - Environment variables (e.g., BEDROCK_ENDPOINT)
  - Tags (Project tags)
- **S3 Buckets**: Identifies AI data buckets by naming patterns
- **DynamoDB Tables**: Finds tables used by AI applications

### 2. **Project-Based Cost Attribution**
Automatically groups costs by your projects:

| Project | Identification Patterns |
|---------|------------------------|
| Ask Eva | `ask-eva`, `eva-poc`, `sa-ai-ask-eva` |
| IEP Report | `iepreport`, `iep-report`, `sa-ai-iepreport` |
| Resume Knockout | `resume-knockout`, `resumeknockout` |
| Resume Scoring | `resume-scoring`, `resumescoring` |
| Financial Aid | `financial-aid`, `financialaid` |

### 3. **Improved Cost Accuracy**
- Uses AWS Cost Explorer for ACTUAL costs (not estimates)
- Attributes Lambda/S3/DynamoDB costs to AI workloads
- Provides detailed breakdowns by service and project

### 4. **Web Interface Enhancements**
- Real-time cost discovery progress indicators
- Project-based cost visualization
- Export capabilities for reports

## 📋 Testing the Enhanced Features

### Quick Test
Run the comprehensive test script:
```bash
cd /Users/lasaj917/Claude\ Code/aws-ai-cost-calculator
python test_enhanced_features.py
```

This will check:
- ✅ Web interface status
- ✅ Enhanced discovery module
- ✅ Project attribution system
- ✅ AWS SSO authentication
- ✅ Cost calculation accuracy

### Manual Testing Steps

#### 1. **Test via Web Interface** (Recommended)
```bash
# Already running at http://localhost:5001
# If not, start it:
python web-interface/app.py
```

Then:
1. Open http://localhost:5001
2. Click "Configure AWS Settings"
3. Select "Environment Variables" (since you have AWS SSO)
4. Click "Start Authentication"
5. Select account(s) - try "aws-sandbox"
6. Click "Discover AI Resources"
7. Click "Calculate Costs"

#### 2. **Test Enhanced Discovery Directly**
```bash
python enhanced_ai_discovery.py
```

This shows all AI resources found across your AWS accounts.

#### 3. **Test Project Attribution**
```bash
python -c "
from enhanced_project_attribution import ProjectAttributor
attr = ProjectAttributor()
test_resource = {'name': 'sa-ai-ask-eva-lambda', 'type': 'lambda_function'}
print(f'Project: {attr.identify_project(test_resource)}')
"
```

#### 4. **Verify Cost Calculations**
```bash
python verify_web_data.py
```

This shows the last calculated costs and verifies the data.

## 🔍 How to Verify It's Working

### Check 1: Enhanced Discovery
Look for these in the discovery results:
- Bedrock agents and knowledge bases
- Lambda functions tagged with AI projects
- S3 buckets with AI naming patterns
- DynamoDB tables for conversation history

### Check 2: Project Attribution
After cost calculation, you should see:
```
Project Costs:
- ask-eva: $XXX.XX
- iep-report: $XXX.XX
- unattributed: $XXX.XX
```

### Check 3: Cost Accuracy
Compare with AWS Cost Explorer:
1. Go to AWS Console > Cost Explorer
2. Filter by the same date range
3. Look at services like Bedrock, Lambda
4. Calculator should show similar costs

## 🛠️ Troubleshooting

### Issue: "AWS credentials not configured"
**Solution:**
```bash
aws sso login
# Or set environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
```

### Issue: "No AI resources found"
**Check:**
1. Are you selecting the right account? (aws-sandbox has AI resources)
2. Do resources have proper tags/names?
3. Check the date range (last 30 days)

### Issue: "Web interface not accessible"
**Solution:**
```bash
# Check if running
curl http://localhost:5001/api/auth/status

# If not, start it:
cd /Users/lasaj917/Claude\ Code/aws-ai-cost-calculator
python web-interface/app.py
```

## 📊 Understanding the Results

### Cost Report Structure
```json
{
  "account": {
    "name": "aws-sandbox",
    "id": "529443669576"
  },
  "services": {
    "bedrock": {
      "total_cost": 150.00,
      "resources": ["ask-eva-agent", "knowledge-base-1"]
    },
    "lambda": {
      "ai_cost": 25.00,
      "ai_functions": ["sa-ai-ask-eva-lambda"]
    }
  },
  "project_costs": {
    "ask-eva": {
      "total": 175.00,
      "services": {"bedrock": 150.00, "lambda": 25.00}
    }
  }
}
```

### Key Metrics
- **Total AWS Cost**: All AWS services
- **AI-Related Cost**: Just AI services and resources
- **Project Breakdown**: Costs per project
- **Unattributed**: AI costs not mapped to projects

## 🎯 Next Steps

1. **Run Regular Reports**: Schedule weekly/monthly runs
2. **Tag Resources**: Add Project tags for better attribution
3. **Set Cost Alerts**: Monitor for unexpected increases
4. **Export Data**: Use JSON export for further analysis

## 💡 Pro Tips

1. **For Most Accurate Results:**
   - Run after the 3rd of each month (when AWS finalizes costs)
   - Use 30-day date ranges
   - Ensure all resources are properly tagged

2. **To Find Missing Resources:**
   - Check CloudWatch Logs for Lambda invocations
   - Look for S3 buckets with ".ai" or "-ml-" patterns
   - Review DynamoDB tables with "conversation" or "history"

3. **For Cost Optimization:**
   - Identify unused Bedrock knowledge bases
   - Find Lambda functions with high invocation costs
   - Look for S3 buckets with high storage costs