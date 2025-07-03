# AWS AI Cost Calculator with SSO

An advanced cost calculator for AWS AI services featuring SSO/Okta authentication, automatic resource discovery, and AI-powered cost optimization recommendations.

## 🌟 Key Features

- **🔐 SSO Authentication** - Seamless login via AWS SSO/Okta
- **🔍 Auto-Discovery** - Automatically finds all AI-related resources
- **💰 Detailed Cost Analysis** - Breaks down costs by service, project, and account
- **🤖 AI-Powered Insights** - Get intelligent optimization recommendations using Amazon Bedrock
- **📊 Interactive Dashboard** - Modern web interface with real-time analysis
- **📈 Cost Projections** - See projections for scaling to 57 schools
- **💡 Optimization Roadmap** - Step-by-step plan to reduce costs by up to 90%
- **📁 Export Options** - Download results as CSV or JSON

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/successacademycharterschools/aws-ai-cost-calculator.git
cd aws-ai-cost-calculator

# Run the interactive setup script
python setup.py
```

The setup script will:
- Check Python version (3.8+ required)
- Create a virtual environment
- Install all dependencies
- Configure AWS SSO
- Set up environment variables
- Provide next steps

### Option 2: Manual Setup

```bash
# Clone and enter directory
git clone https://github.com/successacademycharterschools/aws-ai-cost-calculator.git
cd aws-ai-cost-calculator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r web-interface/requirements.txt

# Configure SSO (optional)
aws configure sso
```

## 📖 Usage

### Web Interface (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the web server
cd web-interface
python app.py
```

Open your browser to: **http://localhost:5002**

The web interface provides:
1. Visual SSO authentication flow
2. Account selection interface
3. Real-time cost calculation
4. AI-powered analysis dashboard
5. Interactive optimization recommendations

### Command Line Interface

```bash
# Run the CLI tool
python cli.py

# Or with options
python cli.py --all-accounts --export
```

## 🎯 AI-Powered Features

### Cost Optimization Analysis
The tool uses Amazon Bedrock to provide:
- **Executive Summary** - High-level cost overview and recommendations
- **Optimization Score** - 0-100 score indicating optimization potential
- **Savings Opportunities** - Specific actions with estimated savings
- **Implementation Roadmap** - Phased approach to cost reduction
- **ROI Analysis** - Payback period and net savings calculations

### Example Recommendations
- **Model Optimization**: Use Claude Haiku for simple queries (97.5% savings)
- **Batch Processing**: Convert real-time to batch workloads (50% savings)
- **Caching Strategy**: Implement prompt caching (up to 90% savings)
- **Service Migration**: Move from Kendra to OpenSearch (80% savings)

## 🏗️ Architecture

### Supported AWS Services
- **Amazon Bedrock** - Foundation models and AI agents
- **Amazon Kendra** - Intelligent search
- **Amazon SageMaker** - ML model training and hosting
- **AWS Lambda** - Serverless compute for AI workloads
- **Amazon S3** - Storage for AI datasets
- **Amazon DynamoDB** - NoSQL database for AI apps
- **Amazon Comprehend** - Natural language processing
- **Amazon Textract** - Document analysis
- **Amazon Polly** - Text-to-speech
- **Amazon Transcribe** - Speech-to-text
- **Amazon Lex** - Conversational interfaces

### Project Attribution
Automatically maps resources to AI projects:
- **Ask Eva** - AI chatbot assistant
- **IEP Report** - Student report generation
- **Financial Aid** - Document processing
- **Resume Scoring** - Recruitment automation
- **Parent App** - Parent engagement platform

## 🔧 Configuration

### SSO Configuration
The tool saves your SSO URL in `.aws-cost-config.json`:
```json
{
  "sso_start_url": "https://d-9067640efb.awsapps.com/start",
  "sso_region": "us-east-1"
}
```

### Environment Variables
Create a `.env` file (see `.env.example`):
```bash
FLASK_ENV=development
FLASK_DEBUG=True
# Optional: Add Bedrock configuration
AWS_DEFAULT_REGION=us-east-1
```

## 🔐 Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostAndUsageWithResources",
        "lambda:ListFunctions",
        "lambda:ListTags",
        "s3:ListAllMyBuckets",
        "s3:GetBucketTagging",
        "dynamodb:ListTables",
        "dynamodb:DescribeTable",
        "dynamodb:ListTagsOfResource",
        "bedrock:List*",
        "kendra:List*",
        "sagemaker:List*",
        "sts:GetCallerIdentity",
        "organizations:DescribeOrganization",
        "organizations:ListAccounts"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🐳 Docker Support

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or build manually
docker build -t aws-ai-cost-calculator .
docker run -p 5002:5002 aws-ai-cost-calculator
```

## 🚨 Troubleshooting

### Common Issues

1. **"No AI resources found"**
   - Ensure resources are properly tagged
   - Check IAM permissions
   - Verify resources exist in selected accounts

2. **SSO Authentication Failed**
   - Verify SSO URL is correct
   - Check Okta session hasn't expired
   - Run `aws configure sso` to refresh

3. **Cost Data Not Showing**
   - Costs may take 24-48 hours to appear
   - Ensure resources ran in the selected date range
   - Check Cost Explorer is enabled

4. **AI Analysis Not Working**
   - Verify Bedrock access in your AWS account
   - Check AWS credentials have Bedrock permissions
   - Fallback analysis will still provide recommendations

## 📊 Output Examples

### Cost Summary
```
Total Monthly Cost: $125.04
Daily Average: $4.17
Projected (57 Schools): $7,127.28

Optimization Potential: 90%
Estimated Savings: $113.01/month
```

### Service Breakdown
- Amazon Kendra: $120.04 (96%)
- Amazon Bedrock: $4.94 (4%)
- AWS Lambda: $0.06 (<1%)

### Export Files
- `ai_costs_summary_YYYYMMDD_HHMMSS.csv` - Detailed cost breakdown
- `ai_cost_report_YYYYMMDD.json` - Complete analysis with recommendations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is proprietary to Success Academy Charter Schools.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review server.log for detailed errors
3. Contact the AI/ML team

## 🎯 Roadmap

- [ ] Historical cost trending
- [ ] Automated cost alerts
- [ ] Multi-region support
- [ ] Cost allocation tags management
- [ ] Integration with AWS Organizations
- [ ] Scheduled report generation
- [ ] Slack notifications
- [ ] Advanced forecasting models