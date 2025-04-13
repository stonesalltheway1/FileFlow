#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileFlow License Integration Test
--------------------------------
This script provides a simple way to test the license management system.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from license_config import LicenseManager, generate_test_key
from license_ui import LicenseActivationWindow, COLORS

class TestLicensingApp:
    """Test application for license management."""
    
    def __init__(self):
        """Initialize the test application."""
        self.root = tk.Tk()
        self.root.title("FileFlow License Test")
        self.root.geometry("600x400")
        self.license_manager = LicenseManager()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="FileFlow License System Test", 
                font=("Segoe UI", 18, "bold")).pack(pady=(0, 20))
        
        # License status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, text="License Status:", 
                font=("Segoe UI", 12)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_var = tk.StringVar(value="Checking...")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                   font=("Segoe UI", 12, "bold"))
        self.status_label.pack(side=tk.LEFT)
        
        # License information
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)
        
        self.info_var = tk.StringVar(value="")
        ttk.Label(info_frame, textvariable=self.info_var,
                 wraplength=550).pack(fill=tk.X)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Check License",
                 command=self.check_license).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Generate Test Key",
                 command=self.generate_and_show_key).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Activate License",
                 command=self.show_activation_window).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Deactivate License",
                 command=self.deactivate_license).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Exit",
                 command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        
        # Initialize
        self.check_license()
    
    def check_license(self):
        """Check license status."""
        result = self.license_manager.check_license()
        
        if result.get("success"):
            self.status_var.set("Active")
            self.status_label.configure(foreground="green")
            
            # Show license details
            license_data = self.license_manager.license_data
            if license_data:
                info_text = f"License Key: {license_data.get('license_key', 'Unknown')}\n"
                info_text += f"Activated On: {license_data.get('activation_date', 'Unknown')}\n"
                info_text += f"Status: {license_data.get('status', 'Unknown')}"
                self.info_var.set(info_text)
        else:
            self.status_var.set("Not Active")
            self.status_label.configure(foreground="red")
            self.info_var.set("No valid license found. You can generate a test key or activate a license.")
    
    def generate_and_show_key(self):
        """Generate and display a test license key."""
        key = generate_test_key()
        messagebox.showinfo("Test License Key", 
                          f"Generated test key:\n\n{key}\n\nYou can use this key to activate the license.")
    
    def show_activation_window(self):
        """Show the license activation window."""
        LicenseActivationWindow(
            self.root,
            COLORS,
            on_success=lambda: self.on_activation_success(),
            on_cancel=lambda: print("Activation canceled")
        )
    
    def on_activation_success(self):
        """Handle successful license activation."""
        self.check_license()
        messagebox.showinfo("Success", "License activated successfully!")
    
    def deactivate_license(self):
        """Deactivate the current license."""
        result = self.license_manager.deactivate_license()
        if result.get("success"):
            messagebox.showinfo("Success", "License deactivated successfully.")
        else:
            messagebox.showwarning("Warning", result.get("message", "Failed to deactivate license."))
        self.check_license()
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = TestLicensingApp()
    app.run()
