#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileFlow Keygen.sh Webhooks for AppSumo and Gumroad
---------------------------------------------------
This script provides webhook handlers to integrate AppSumo and Gumroad
with Keygen.sh for automated license key generation and delivery.

To use this script:
1. Deploy it to a web server or serverless function (e.g., AWS Lambda, Vercel, Netlify)
2. Set up webhook endpoints in AppSumo and Gumroad to point to this script
3. Configure the Keygen.sh credentials and product IDs

You can test this script locally using ngrok (https://ngrok.com) to expose your
local server to the internet temporarily.
"""

import os
import json
import hmac
import hashlib
import logging
import requests
from datetime import datetime
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FileFlow-Webhooks")

# Initialize Flask app
app = Flask(__name__)

# Configuration (replace with environment variables in production)
KEYGEN_ACCOUNT_ID = "1-rjweb-v68f-47be-b32c-101ntwbtnfdz" # Your Keygen account ID
KEYGEN_API_KEY = os.environ.get("KEYGEN_API_KEY", "YOUR_KEYGEN_API_KEY")
KEYGEN_PRODUCT_ID = "fileflow" # Your product ID in Keygen
KEYGEN_POLICY_ID = "fileflow-license-policy" # Your policy ID in Keygen

# AppSumo & Gumroad secrets for signature verification 
APPSUMO_WEBHOOK_SECRET = os.environ.get("APPSUMO_WEBHOOK_SECRET", "YOUR_APPSUMO_SECRET")
GUMROAD_WEBHOOK_SECRET = os.environ.get("GUMROAD_WEBHOOK_SECRET", "YOUR_GUMROAD_SECRET")

# Map plan codes to license tiers
APPSUMO_PLAN_MAPPING = {
    "tier1": "pro",      # AppSumo Tier 1 maps to Pro plan
    "tier2": "premium",  # AppSumo Tier 2 maps to Premium plan
    "tier3": "business", # AppSumo Tier 3 maps to Business plan
}

GUMROAD_PRODUCT_MAPPING = {
    "FileFlow-Pro": "pro",
    "FileFlow-Premium": "premium",
    "FileFlow-Business": "business",
}

# Keygen.sh API integration
def create_license(email, name, tier="premium"):
    """Create a license in Keygen.sh.
    
    Args:
        email: The customer's email
        name: The customer's name
        tier: The license tier (pro, premium, business)
        
    Returns:
        dict: The created license information
    """
    url = f"https://api.keygen.sh/v1/accounts/{KEYGEN_ACCOUNT_ID}/licenses"
    
    # Determine machine limit based on tier
    machine_limit = 1
    if tier == "premium":
        machine_limit = 3
    elif tier == "business":
        machine_limit = 5
    
    headers = {
        "Authorization": f"Bearer {KEYGEN_API_KEY}",
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json"
    }
    
    payload = {
        "data": {
            "type": "licenses",
            "attributes": {
                "name": f"{name}'s License",
                "metadata": {
                    "tier": tier,
                    "purchaseDate": datetime.now().isoformat(),
                    "source": "appsumo" if "tier" in tier else "gumroad"
                }
            },
            "relationships": {
                "policy": {
                    "data": {
                        "type": "policies",
                        "id": KEYGEN_POLICY_ID
                    }
                },
                "user": {
                    "data": {
                        "type": "users",
                        "attributes": {
                            "email": email,
                            "name": name,
                            "metadata": {
                                "source": "appsumo" if "tier" in tier else "gumroad"
                            }
                        }
                    }
                }
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating license: {e}")
        return None

def send_license_email(email, name, license_key):
    """Send the license key to the customer via email.
    
    In production, you would use a proper email service like SendGrid, Mailgun, etc.
    This is a placeholder implementation.
    
    Args:
        email: The customer's email
        name: The customer's name
        license_key: The license key to send
    """
    # Placeholder for email sending logic
    logger.info(f"Would send license key {license_key} to {email}")
    
    # In production, implement email sending:
    # Example with SendGrid:
    # 
    # import sendgrid
    # from sendgrid.helpers.mail import Mail, Email, To, Content
    # 
    # sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    # 
    # from_email = Email("noreply@yourcompany.com")
    # to_email = To(email)
    # subject = "Your FileFlow License Key"
    # content = Content("text/html", f"""
    #     <h1>Thank you for purchasing FileFlow!</h1>
    #     <p>Hello {name},</p>
    #     <p>Your FileFlow license key is: <strong>{license_key}</strong></p>
    #     <p>You can activate your copy of FileFlow by following these steps:
    #        <ol>
    #           <li>Open FileFlow application</li>
    #           <li>Go to Help > Activate License</li>
    #           <li>Enter your license key</li>
    #        </ol>
    #     </p>
    #     <p>If you have any questions, please contact our support team.</p>
    # """)
    # 
    # mail = Mail(from_email, to_email, subject, content)
    # response = sg.client.mail.send.post(request_body=mail.get())

# AppSumo webhook handler
@app.route('/webhook/appsumo', methods=['POST'])
def appsumo_webhook():
    """Handle AppSumo webhook events.
    
    AppSumo sends webhooks for various events including purchases, refunds, etc.
    We need to validate the signature and process the event accordingly.
    """
    # Verify webhook signature
    signature = request.headers.get('X-Appsumo-Signature', '')
    raw_body = request.get_data()
    
    if not verify_appsumo_signature(signature, raw_body):
        logger.warning("Invalid AppSumo signature")
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process the webhook data
    try:
        data = request.json
        event_type = data.get('event')
        
        # Handle purchase event
        if event_type == 'purchase':
            logger.info(f"Processing AppSumo purchase: {data}")
            
            # Extract customer info
            customer_email = data.get('customer', {}).get('email')
            customer_name = data.get('customer', {}).get('name', 'AppSumo Customer')
            
            # Get plan tier
            plan_id = data.get('plan_id', 'tier1')
            tier = APPSUMO_PLAN_MAPPING.get(plan_id, 'premium')
            
            # Create license in Keygen.sh
            license_response = create_license(
                email=customer_email,
                name=customer_name,
                tier=tier
            )
            
            if license_response:
                # Get the license key
                license_key = license_response.get('data', {}).get('attributes', {}).get('key')
                
                # Send license key via email
                send_license_email(customer_email, customer_name, license_key)
                
                # Return success response
                return jsonify({
                    "success": True,
                    "message": "License created successfully",
                    "license_key": license_key
                })
            
            return jsonify({
                "success": False,
                "message": "Failed to create license"
            }), 500
        
        # Handle refund event
        elif event_type == 'refund':
            # Implement refund handling logic (e.g., mark license as inactive)
            # For now, just log it
            logger.info(f"AppSumo refund received: {data}")
            return jsonify({"success": True, "message": "Refund processed"})
        
        # Handle other events
        else:
            logger.info(f"Unhandled AppSumo event: {event_type}")
            return jsonify({"success": True, "message": "Event received"})
    
    except Exception as e:
        logger.error(f"Error processing AppSumo webhook: {e}")
        return jsonify({"error": str(e)}), 500

# Gumroad webhook handler
@app.route('/webhook/gumroad', methods=['POST'])
def gumroad_webhook():
    """Handle Gumroad webhook events.
    
    Gumroad sends webhooks for various events including purchases, refunds, etc.
    """
    try:
        data = request.form.to_dict()
        logger.info(f"Received Gumroad webhook: {data}")
        
        # Verify the webhook
        if not verify_gumroad_signature(data):
            logger.warning("Invalid Gumroad webhook")
            return jsonify({"error": "Invalid webhook"}), 401
        
        # Handle sale event
        if data.get('resource_name') == 'sale':
            # Extract customer info
            customer_email = data.get('email', '')
            customer_name = data.get('full_name', 'Gumroad Customer')
            
            # Get product info and map to tier
            product_id = data.get('product_id', '')
            product_name = data.get('product_name', '')
            
            # Determine tier based on product
            tier = GUMROAD_PRODUCT_MAPPING.get(product_name, 'premium')
            
            # Create license in Keygen.sh
            license_response = create_license(
                email=customer_email,
                name=customer_name,
                tier=tier
            )
            
            if license_response:
                # Get the license key
                license_key = license_response.get('data', {}).get('attributes', {}).get('key')
                
                # Send license key via email
                send_license_email(customer_email, customer_name, license_key)
                
                # Return success response
                return jsonify({
                    "success": True,
                    "message": "License created successfully",
                    "license_key": license_key
                })
            
            return jsonify({
                "success": False,
                "message": "Failed to create license"
            }), 500
        
        # Handle refund event
        elif data.get('resource_name') == 'refund':
            # Implement refund handling logic (e.g., mark license as inactive)
            # For now, just log it
            logger.info(f"Gumroad refund received: {data}")
            return jsonify({"success": True, "message": "Refund processed"})
        
        # Handle other events
        else:
            logger.info(f"Unhandled Gumroad event: {data.get('resource_name')}")
            return jsonify({"success": True, "message": "Event received"})
    
    except Exception as e:
        logger.error(f"Error processing Gumroad webhook: {e}")
        return jsonify({"error": str(e)}), 500

# Signature verification helpers
def verify_appsumo_signature(signature, payload):
    """Verify the AppSumo webhook signature."""
    computed_hmac = hmac.new(
        APPSUMO_WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_hmac, signature)

def verify_gumroad_signature(data):
    """Verify the Gumroad webhook.
    
    Gumroad doesn't use signatures, we just check for expected fields.
    """
    # Check for required fields to help verify it's a real Gumroad webhook
    required_fields = ['resource_name', 'seller_id', 'product_id']
    for field in required_fields:
        if field not in data:
            return False
    
    # In production, you may want to verify the seller_id
    # matches your Gumroad account
    return True

# Main application entry point
if __name__ == '__main__':
    # For local development only - don't use in production
    app.run(debug=True, port=5000)
