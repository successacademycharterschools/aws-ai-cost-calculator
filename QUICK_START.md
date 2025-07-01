# 🚀 AWS AI Cost Calculator - Quick Start for Mac Users

## Setup in 30 Seconds

```bash
# 1. Clone this repo
git clone https://github.com/successacademycharterschools/aws-ai-cost-calculator.git

# 2. Go to the folder
cd aws-ai-cost-calculator

# 3. Run the magic setup script
python3 setup_and_run.py
```

**That's it!** The script does everything for you and opens the web app.

## What You'll See

1. **Terminal Progress** - Shows each setup step
2. **Browser Opens** - For AWS/Okta login (first time only)
3. **Web App Launches** - At http://localhost:5001

## Daily Use (After First Setup)

```bash
# Just run this:
./start.sh

# Or if you prefer:
cd web-interface && python app.py
```

## 🎯 Features

- **Real-time AWS costs** - Direct from AWS APIs
- **AI cost breakdown** - See Bedrock, Lambda, S3 costs
- **Project tracking** - Ask Eva, IEP Report, etc.
- **Export to Excel** - Download CSV reports

## 🔍 Verify Accuracy

To check the numbers are correct:
```bash
python verify_accuracy.py
```

This compares the calculator with AWS Cost Explorer directly.

## ❓ Common Questions

**Q: Where do the numbers come from?**
A: Direct from AWS Cost Explorer API - same as AWS Console

**Q: How are AI costs calculated?**
A: 
- Bedrock/Kendra: 100% (fully AI services)
- Lambda: 30% (estimated AI workloads)
- S3: 20% (AI data storage)
- DynamoDB: 25% (conversation history)

**Q: Why no costs showing?**
A: AWS costs take 24-48 hours to appear. Use `test_offline_processing.py` for demo data.

## 🆘 Need Help?

1. Check if AWS CLI works: `aws --version`
2. Re-login if needed: `aws sso login --profile sa-sandbox`
3. See full guide: `SETUP_GUIDE.md`

---
Made with ❤️ for Success Academies