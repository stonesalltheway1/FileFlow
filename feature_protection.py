#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileFlow Feature Protection
---------------------------
This module provides feature protection for premium features.
"""

import tkinter as tk
from tkinter import messagebox
from functools import wraps
from license_ui import LicenseActivationWindow

# Dictionary of premium features with user-friendly names
PREMIUM_FEATURES = {
    "find_duplicates": "Duplicate Finder",
    "auto_organize": "Auto Organize",
    "rename_files": "Smart File Renaming",
    "clear_database": "Database Management",
    "import_database": "Database Import",
    "export_database": "Database Export",
    "show_cleanup_suggestions": "Cleanup Suggestions"
}

def premium_feature(feature_name):
    """
    Decorator to protect premium features with license check.
    
    Args:
        feature_name: String identifier for the feature (must match a key in PREMIUM_FEATURES)
        
    Returns:
        Decorated function that checks for valid license before executing
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'license_manager'):
                return _show_premium_feature_dialog(self, feature_name)
                
            # Check license using the manager from license_ui
            if hasattr(self, 'license_manager'):
                result = self.license_manager.check_license()
                if result.get("success"):
                    return func(self, *args, **kwargs)
            
            # No valid license, show activation dialog
            return _show_premium_feature_dialog(self, feature_name)
        return wrapper
    return decorator

def _show_premium_feature_dialog(app, feature_name):
    """
    Show dialog informing user that this is a premium feature.
    
    Args:
        app: The FileFlowApp instance
        feature_name: String identifier for the feature
    """
    display_name = PREMIUM_FEATURES.get(feature_name, feature_name)
    
    response = messagebox.askyesno(
        "Premium Feature",
        f"The {display_name} is a premium feature that requires a license.\n\n"
        "Would you like to activate a license now?",
        icon=messagebox.INFO
    )
    
    if response:
        # Show license activation window
        LicenseActivationWindow(
            app.root,
            app.COLORS if hasattr(app, 'COLORS') else None,
            on_success=lambda: app._update_status("License activated successfully!")
        )
    
    return None
