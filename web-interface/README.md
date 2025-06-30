# AWS AI Cost Calculator - Web Interface

A web-based interface for the AWS AI Cost Calculator with Success Academies branding.

## Features

- 🎨 **Success Academies Branding** - Matches SA colors and design
- 🔐 **SSO Authentication** - Browser-based AWS SSO login via Okta
- 📊 **Interactive Dashboard** - Real-time cost visualization
- 📈 **Charts & Metrics** - Visual cost breakdowns
- 💾 **Export Options** - Download results as CSV or JSON

## Setup

1. **Install dependencies**:
```bash
cd aws-ai-cost-calculator-web
pip install -r requirements.txt
```

2. **Ensure the SSO calculator is accessible**:
The web app expects the SSO calculator to be in the parent directory:
```
aws-ai-cost-calculator-sso/
aws-ai-cost-calculator-web/  <-- You are here
```

3. **Run the web server**:
```bash
python app.py
```

4. **Open in browser**:
Navigate to `http://localhost:5000`

## Usage

1. **Configure SSO**: Enter your AWS SSO URL (already pre-filled)
2. **Authenticate**: Browser will open for Okta login
3. **Select Accounts**: Choose which AWS accounts to analyze
4. **View Results**: See costs broken down by service and project
5. **Export Data**: Download results as CSV or JSON

## UI Features

### Progress Tracker
Visual step-by-step progress indicator showing:
- SSO Configuration
- Account Selection
- Resource Discovery
- Cost Analysis

### Cost Metrics
- Total Monthly Cost
- Daily Average
- Projected Cost for 57 Schools
- Total AI Resources Found

### Interactive Elements
- Select All/Deselect All for accounts
- Sortable cost breakdown table
- Doughnut chart for service costs
- Export buttons

## Branding

Uses Success Academies brand colors:
- Primary Blue: `#005e9e`
- Orange: `#f7941e`
- Clean, modern design
- Professional typography

## API Endpoints

The Flask server provides these endpoints:
- `GET /` - Main web interface
- `GET /api/auth/status` - Check authentication
- `POST /api/auth/configure` - Configure SSO
- `POST /api/auth/start` - Start authentication
- `GET /api/accounts/list` - List AWS accounts
- `POST /api/accounts/select` - Select accounts
- `POST /api/discover` - Discover resources
- `POST /api/costs/calculate` - Calculate costs
- `GET /api/export/<format>` - Export results

## Security

- No credentials stored
- Session-based authentication
- All auth through browser
- Read-only AWS access

## Troubleshooting

### Page won't load
- Check Flask is running on port 5000
- Ensure no firewall blocking

### Authentication fails
- Verify SSO URL is correct
- Check Okta session is active
- Ensure AWS CLI is installed

### No costs showing
- Verify accounts have AI resources
- Check IAM permissions
- Wait 24-48 hours for new resources