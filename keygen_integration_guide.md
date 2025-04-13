# FileFlow Keygen.sh Integration Guide

This guide explains how to fully set up and deploy the Keygen.sh licensing system for FileFlow, enabling both AppSumo and Gumroad sales channels.

## 1. Keygen.sh Account Setup

### API Key Configuration

1. Log in to your Keygen.sh dashboard
2. Navigate to **Settings** > **API Keys**
3. Create a new API key with the following permissions:
   - Licenses: Read, Write
   - Policies: Read
   - Users: Read, Write
4. Copy the generated API key and store it securely

### Environment Variables

Set up these environment variables on your webhook server:

```
KEYGEN_API_KEY=your_api_key_here
APPSUMO_WEBHOOK_SECRET=your_appsumo_secret_here
GUMROAD_WEBHOOK_SECRET=your_gumroad_secret_here
```

## 2. Webhook Deployment

### Option A: Deploy to Vercel

1. Create a Vercel account if you don't have one
2. Install the Vercel CLI: `npm install -g vercel`
3. Create a `requirements.txt` file with:
   ```
   flask
   requests
   ```
4. Create a `vercel.json` file with:
   ```json
   {
     "version": 2,
     "builds": [
       { "src": "keygen_webhooks.py", "use": "@vercel/python" }
     ],
     "routes": [
       { "src": "/webhook/appsumo", "dest": "keygen_webhooks.py" },
       { "src": "/webhook/gumroad", "dest": "keygen_webhooks.py" }
     ]
   }
   ```
5. Deploy with: `vercel --prod`
6. Set up environment variables in the Vercel dashboard

### Option B: Deploy to AWS Lambda

1. Install the AWS CLI and configure it
2. Install the AWS Serverless Application Model (SAM) CLI
3. Create a SAM template for your webhook handlers
4. Deploy with: `sam deploy --guided`

## 3. AppSumo Integration

1. Set up your AppSumo deal dashboard
2. Navigate to **Integration Settings**
3. Add your webhook URL: `https://your-deployment-url/webhook/appsumo`
4. Set up the webhook secret and save it in your environment variables
5. Test the integration with a test purchase

## 4. Gumroad Integration

1. Go to your Gumroad dashboard
2. Navigate to **Settings** > **Advanced**
3. Add your webhook URL: `https://your-deployment-url/webhook/gumroad`
4. Configure each product with the correct metadata
5. Test the integration with a test purchase

## 5. License Email Configuration

In the `keygen_webhooks.py` file, update the `send_license_email` function with your email service provider:

```python
# Example for SendGrid
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

def send_license_email(email, name, license_key):
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    
    from_email = Email("licenses@yourcompany.com")
    to_email = To(email)
    subject = "Your FileFlow License Key"
    
    content = Content("text/html", f"""
        <h1>Thank you for purchasing FileFlow!</h1>
        <p>Hello {name},</p>
        <p>Your FileFlow license key is: <strong>{license_key}</strong></p>
        <p>You can activate your copy of FileFlow by following these steps:
           <ol>
              <li>Open FileFlow application</li>
              <li>Go to Help > Activate License</li>
              <li>Enter your license key</li>
           </ol>
        </p>
        <p>If you have any questions, please contact our support team.</p>
    """)
    
    mail = Mail(from_email, to_email, subject, content)
    response = sg.client.mail.send.post(request_body=mail.get())
```

## 6. Testing the Integration

1. Generate a test license in Keygen.sh dashboard
2. Run the FileFlow test license application:
   ```
   python test_license.py
   ```
3. Enter the license key and verify it activates correctly
4. Test the webhook integration using the Keygen.sh webhook tester

## 7. Go Live Checklist

- [ ] Verified license activation works correctly
- [ ] Tested webhooks with test purchases
- [ ] Configured email delivery
- [ ] Set up proper error logging
- [ ] Backed up your Keygen.sh API keys
- [ ] Updated FileFlow application with the production license configuration

## Troubleshooting

### License validation fails

1. Check the Keygen.sh dashboard for the license status
2. Verify that your account ID and product ID are correct
3. Check for any validation errors in the application logs

### Webhook integration issues

1. Verify webhook URL is correct
2. Check webhook secrets match
3. Review server logs for any errors

For more help, contact Keygen.sh support or review the API documentation at https://keygen.sh/docs/api/
