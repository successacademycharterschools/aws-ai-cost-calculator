# Okta Integration Guide for AWS AI Cost Calculator

This guide will help you set up the AWS AI Cost Calculator as an Okta application tile that your team can access with single sign-on.

## Prerequisites

- Okta Administrator access
- AWS account with appropriate permissions
- A publicly accessible URL for the application (we'll set this up)

## Step 1: Deploy the Application

### Option A: AWS EC2 Deployment (Recommended)

1. **Launch an EC2 instance**:
   ```bash
   # Use Amazon Linux 2 or Ubuntu 20.04+
   # Instance type: t3.small or larger
   # Security group: Allow ports 80, 443, and 5002
   ```

2. **Install the application**:
   ```bash
   # SSH into your instance
   ssh -i your-key.pem ec2-user@your-instance-ip

   # Install Git and Python
   sudo yum update -y  # or apt-get update
   sudo yum install -y git python3 python3-pip  # or apt-get

   # Clone the repository
   git clone https://github.com/successacademycharterschools/aws-ai-cost-calculator.git
   cd aws-ai-cost-calculator

   # Run setup
   python3 setup.py
   ```

3. **Set up NGINX for HTTPS**:
   ```bash
   # Install NGINX
   sudo yum install -y nginx  # or apt-get

   # Install Certbot for SSL
   sudo yum install -y certbot python3-certbot-nginx

   # Configure NGINX (see nginx.conf below)
   sudo nano /etc/nginx/sites-available/ai-calculator
   ```

4. **NGINX Configuration** (`/etc/nginx/sites-available/ai-calculator`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

       location / {
           proxy_pass http://localhost:5002;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

5. **Enable the site and get SSL certificate**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/ai-calculator /etc/nginx/sites-enabled/
   sudo certbot --nginx -d your-domain.com
   sudo systemctl restart nginx
   ```

6. **Create a systemd service** (`/etc/systemd/system/ai-calculator.service`):
   ```ini
   [Unit]
   Description=AWS AI Cost Calculator
   After=network.target

   [Service]
   Type=simple
   User=ec2-user
   WorkingDirectory=/home/ec2-user/aws-ai-cost-calculator
   Environment="PATH=/home/ec2-user/aws-ai-cost-calculator/venv/bin"
   ExecStart=/home/ec2-user/aws-ai-cost-calculator/venv/bin/python web-interface/app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start the service**:
   ```bash
   sudo systemctl enable ai-calculator
   sudo systemctl start ai-calculator
   ```

### Option B: AWS ECS/Fargate Deployment

1. **Build and push Docker image**:
   ```bash
   # Build the image
   docker build -t aws-ai-cost-calculator .

   # Tag for ECR
   docker tag aws-ai-cost-calculator:latest YOUR_ECR_URI/aws-ai-cost-calculator:latest

   # Push to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URI
   docker push YOUR_ECR_URI/aws-ai-cost-calculator:latest
   ```

2. **Create ECS task definition and service**
3. **Set up Application Load Balancer with HTTPS**

## Step 2: Configure Okta Application

### Create the Application in Okta

1. **Log in to Okta Admin Console**
2. Navigate to **Applications** > **Applications**
3. Click **Create App Integration**
4. Choose **SAML 2.0** and click **Next**

### Configure SAML Settings

1. **General Settings**:
   - App name: `AWS AI Cost Calculator`
   - App logo: Upload a logo (optional)
   - App visibility: Check "Do not display application icon to users"
   - Click **Next**

2. **Configure SAML**:
   - Single Sign-On URL: `https://your-domain.com/saml/acs`
   - Audience URI (SP Entity ID): `https://your-domain.com`
   - Default RelayState: Leave blank
   - Name ID format: `EmailAddress`
   - Application username: `Email`

3. **Attribute Statements**:
   | Name | Name format | Value |
   |------|-------------|-------|
   | email | Basic | user.email |
   | firstName | Basic | user.firstName |
   | lastName | Basic | user.lastName |
   | awsRole | Basic | user.awsRole (if configured) |

4. **Group Attribute Statements** (optional):
   - Name: `groups`
   - Name format: `Basic`
   - Filter: `Matches regex .*`

### Feedback Settings

1. Select "I'm an Okta customer adding an internal app"
2. Check "This is an internal app that we have created"
3. Click **Finish**

## Step 3: Update Application for SAML

Currently, the application uses AWS SSO. To integrate with Okta SAML, you'll need to add SAML support:

### Install SAML dependencies

```bash
pip install python-saml flask-saml2
```

### Create SAML configuration

Create `web-interface/saml_config.py`:

```python
import os
from urllib.parse import urlparse

def get_saml_settings(app_url):
    """Generate SAML settings for the application"""
    
    return {
        "sp": {
            "entityId": app_url,
            "assertionConsumerService": {
                "url": f"{app_url}/saml/acs",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            },
            "singleLogoutService": {
                "url": f"{app_url}/saml/sls",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
        "idp": {
            "entityId": os.getenv('OKTA_ENTITY_ID', 'http://www.okta.com/YOUR_ID'),
            "singleSignOnService": {
                "url": os.getenv('OKTA_SSO_URL', 'https://your-domain.okta.com/app/appid/sso/saml'),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "singleLogoutService": {
                "url": os.getenv('OKTA_SLO_URL', 'https://your-domain.okta.com/app/appid/slo/saml'),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "x509cert": os.getenv('OKTA_X509_CERT', '')
        }
    }
```

### Update app.py for SAML

Add these routes to `web-interface/app.py`:

```python
from flask import request, redirect, url_for
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from saml_config import get_saml_settings

def init_saml_auth(req):
    """Initialize SAML authentication"""
    app_url = os.getenv('APP_URL', 'https://your-domain.com')
    auth = OneLogin_Saml2_Auth(req, get_saml_settings(app_url))
    return auth

def prepare_flask_request(request):
    """Prepare request in the appropriate format for SAML"""
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.headers['Host'],
        'server_port': request.environ['SERVER_PORT'],
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy()
    }

@app.route('/saml/login', methods=['GET'])
def saml_login():
    """Initiate SAML login"""
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    return redirect(auth.login())

@app.route('/saml/acs', methods=['POST'])
def saml_acs():
    """SAML Assertion Consumer Service"""
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    
    errors = auth.get_errors()
    if not errors:
        session['samlUserdata'] = auth.get_attributes()
        session['samlNameId'] = auth.get_nameid()
        session['samlNameIdFormat'] = auth.get_nameid_format()
        session['samlNameIdNameQualifier'] = auth.get_nameid_nq()
        session['samlNameIdSPNameQualifier'] = auth.get_nameid_spnq()
        session['samlSessionIndex'] = auth.get_session_index()
        
        # Set authenticated flag
        session['authenticated'] = True
        session['user_email'] = session['samlNameId']
        
        return redirect(url_for('index'))
    else:
        return jsonify({'errors': errors, 'last_error_reason': auth.get_last_error_reason()}), 400
```

## Step 4: Assign Users in Okta

1. In Okta Admin Console, go to your AWS AI Cost Calculator app
2. Click on **Assignments** tab
3. Click **Assign** and choose:
   - **Assign to People**: For individual users
   - **Assign to Groups**: For team access
4. Click **Save and Go Back**

## Step 5: Configure AWS IAM for Okta Users

### Create IAM Role for Okta Users

1. **Create IAM Policy** (`OktaAICostCalculatorPolicy`):
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

2. **Create IAM Role** with SAML 2.0 federation:
   - Trusted entity: SAML 2.0 federation
   - SAML provider: Your Okta provider
   - Attach the policy created above

## Step 6: Create Okta Tile

1. In Okta Admin Console, go to your app
2. Click **General** tab
3. Under **App Embed Link**, copy the embed link
4. Configure the tile:
   - Display name: `AWS AI Cost Calculator`
   - Description: `Track and optimize AI service costs`
   - Icon: Upload a custom icon

## Step 7: Test the Integration

1. Log out of Okta
2. Log back in as a test user
3. Click on the AWS AI Cost Calculator tile
4. Verify:
   - SAML authentication works
   - User lands on the cost calculator
   - AWS resources are accessible

## Troubleshooting

### Common Issues

1. **SAML Response Error**
   - Check SAML settings match between Okta and app
   - Verify X.509 certificate is correctly configured
   - Check clock synchronization (SAML is time-sensitive)

2. **AWS Permission Denied**
   - Verify IAM role trust policy includes Okta
   - Check IAM policy has required permissions
   - Ensure SAML attributes include necessary AWS role

3. **Application Not Loading**
   - Check NGINX/load balancer configuration
   - Verify security groups allow HTTPS traffic
   - Check application logs: `sudo journalctl -u ai-calculator`

### Debug Mode

Enable SAML debug mode in `.env`:
```bash
SAML_DEBUG=True
```

## Security Best Practices

1. **Use HTTPS everywhere** - Never run SAML over HTTP
2. **Rotate certificates** - Update X.509 certificates annually
3. **Implement session timeout** - Set appropriate session lifetimes
4. **Enable MFA in Okta** - Require MFA for sensitive applications
5. **Audit logs** - Monitor SAML authentications and AWS API calls
6. **Least privilege** - Only grant necessary AWS permissions

## Next Steps

1. Set up monitoring and alerting
2. Configure automated backups
3. Implement usage analytics
4. Set up CI/CD pipeline
5. Create user training materials

For additional help, contact your Okta administrator or the AI/ML team.