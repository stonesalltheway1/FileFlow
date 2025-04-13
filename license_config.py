#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileFlow License Configuration
------------------------------
This file contains the necessary configuration for licensing FileFlow
through Keygen.sh, which works with both AppSumo and Gumroad integrations.
"""

import os
import json
import hashlib
import datetime
import urllib.request
import urllib.parse

# License provider configuration
LICENSE_PROVIDER = {
    "name": "Keygen",
    "api_url": "https://api.keygen.sh/v1",
    "verify_endpoint": "/accounts/{account_id}/licenses/actions/validate-key",
}

# Account and product information
ACCOUNT_INFO = {
    "account_id": "1-rjweb-v68f-47be-b32c-101ntwbtnfdz",  # Your Keygen account ID
    "product_id": "fileflow",  # Your product ID in Keygen
    "license_policy_id": "fileflow-license-policy",  # Your policy ID in Keygen
}

# License storage path (relative to user's home directory)
LICENSE_FILE = os.path.join(os.path.expanduser("~"), ".fileflow", "license.json")


class LicenseManager:
    """Handles license validation and management for FileFlow."""
    
    def __init__(self):
        self.license_data = None
        self.load_license()
    
    def load_license(self):
        """Load license data from file if it exists."""
        try:
            if os.path.exists(LICENSE_FILE):
                with open(LICENSE_FILE, 'r') as f:
                    self.license_data = json.load(f)
        except Exception as e:
            print(f"Error loading license: {e}")
            self.license_data = None
    
    def save_license(self):
        """Save license data to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(LICENSE_FILE), exist_ok=True)
            
            with open(LICENSE_FILE, 'w') as f:
                json.dump(self.license_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving license: {e}")
            return False
    
    def activate_license(self, license_key):
        """Activate a license key."""
        # Local validation first (format check)
        if not self._validate_key_format(license_key):
            return {"success": False, "message": "Invalid license key format"}
        
        # Try online validation if possible
        try:
            validation_result = self._online_validation(license_key)
            if validation_result.get("success"):
                # Store the license information
                self.license_data = {
                    "license_key": license_key,
                    "activation_date": datetime.datetime.now().isoformat(),
                    "status": "active",
                    "product_id": ACCOUNT_INFO["product_id"],
                    "validation_data": validation_result
                }
                self.save_license()
            return validation_result
        except Exception as e:
            # Fallback to offline validation if online fails
            return self._offline_validation(license_key)
    
    def check_license(self):
        """Check if a valid license exists and is active."""
        if not self.license_data:
            return {"success": False, "message": "No license found"}
        
        # Try to re-validate online if possible, otherwise use cached data
        try:
            return self._online_validation(self.license_data["license_key"])
        except Exception:
            # Use offline validation as fallback
            if self.license_data.get("status") == "active":
                return {"success": True, "message": "License is active (offline mode)"}
            return {"success": False, "message": "License validation failed"}
    
    def deactivate_license(self):
        """Deactivate the current license."""
        if self.license_data:
            self.license_data["status"] = "inactive"
            self.save_license()
            return {"success": True, "message": "License deactivated"}
        return {"success": False, "message": "No license to deactivate"}
    
    def _validate_key_format(self, key):
        """Basic validation of license key format."""
        # Implement your key format validation logic
        # This is a simple check - customize based on your actual key format
        if not key or len(key) < 20:
            return False
        
        # Check if key matches expected format (example: XXXX-XXXX-XXXX-XXXX)
        parts = key.split("-")
        if len(parts) < 4:
            return False
            
        return True
    
    def _online_validation(self, license_key):
        """Validate license key with Keygen.sh service."""
        url = f"{LICENSE_PROVIDER['api_url']}{LICENSE_PROVIDER['verify_endpoint']}".replace('{account_id}', ACCOUNT_INFO['account_id'])
        
        headers = {
            'Content-Type': 'application/vnd.api+json',
            'Accept': 'application/vnd.api+json'
        }
        
        data = {
            "meta": {
                "key": license_key,
                "product": ACCOUNT_INFO['product_id']
            }
        }
        
        try:
            req = urllib.request.Request(
                url,
                json.dumps(data).encode('utf-8'),
                headers
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Parse Keygen response
                if result.get('meta', {}).get('valid'):
                    return {
                        "success": True,
                        "message": "License validated successfully",
                        "expires": result.get('meta', {}).get('expiry'),
                        "machines": result.get('meta', {}).get('machines', {}),
                        "status": result.get('meta', {}).get('status', 'active')
                    }
                else:
                    reason = result.get('meta', {}).get('detail', "Invalid license key")
                    logger.warning(f"License validation failed: {reason}")
                    return {
                        "success": False,
                        "message": reason
                    }
        except Exception as e:
            logger.error(f"Error validating license: {e}")
            # Fall back to offline validation
            return self._offline_validation(license_key)
    
    def _offline_validation(self, license_key):
        """Fallback validation when online validation is not available."""
        # For Keygen.sh, offline validation checks for proper license key format
        # Pattern is usually like: XXXXX-XXX-XXX-XXXXX-XXX-XXXXXX-XX
        
        # Validate the key format (basic check)
        if re.match(r'^[A-Z0-9]{5,7}(-[A-Z0-9]{2,7}){3,6}$', license_key, re.IGNORECASE):
            # If this is a cached license, check if it was previously validated
            if self.license_data and self.license_data.get("license_key") == license_key:
                if self.license_data.get("status") == "active":
                    return {"success": True, "message": "License is active (cached)"}
            
            # Store as new offline validation
            self.license_data = {
                "license_key": license_key,
                "activation_date": datetime.datetime.now().isoformat(),
                "status": "active",
                "product_id": ACCOUNT_INFO["product_id"],
                "validation_method": "offline",
                "offline_validation_expires": (datetime.datetime.now() + 
                                               datetime.timedelta(days=7)).isoformat()
            }
            self.save_license()
            return {"success": True, "message": "License activated (offline mode)"}
        
        return {"success": False, "message": "Invalid license key format"}


# Generate a license key (for testing/development only)
def generate_test_key():
    """Generate a test license key for development purposes."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"FILEFLOW-TEST-{timestamp}-{ACCOUNT_INFO['product_id'][:8]}"
    hash_val = hashlib.md5(raw.encode()).hexdigest()[:8]
    return f"FILEFLOW-{timestamp[:8]}-{hash_val}-TEST"


# Example usage:
if __name__ == "__main__":
    # This code only runs when this file is executed directly (for testing)
    license_manager = LicenseManager()
    
    # Generate and activate a test license
    test_key = generate_test_key()
    print(f"Generated test key: {test_key}")
    
    result = license_manager.activate_license(test_key)
    print(f"Activation result: {result}")
    
    check_result = license_manager.check_license()
    print(f"License check result: {check_result}")
