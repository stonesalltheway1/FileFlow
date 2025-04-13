#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileFlow License Management UI
------------------------------
This file contains the user interface components for license activation
and management in FileFlow.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import webbrowser
from license_config import LicenseManager, ACCOUNT_INFO

class LicenseActivationWindow:
    """License activation window for FileFlow."""
    
    def __init__(self, parent, colors, on_success=None, on_cancel=None):
        """Initialize the license activation window.
        
        Args:
            parent: Parent tkinter window
            colors: Dictionary of color values used for styling
            on_success: Callback function when license activation succeeds
            on_cancel: Callback function when user cancels
        """
        self.parent = parent
        self.colors = colors
        self.license_manager = LicenseManager()
        self.on_success = on_success
        self.on_cancel = on_cancel
        
        # Create the window
        self.window = tk.Toplevel(parent)
        self.window.title("Activate FileFlow")
        self.window.geometry("550x400")
        self.window.resizable(False, False)
        
        # Center the window
        self.window.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 275,
            parent.winfo_rooty() + parent.winfo_height()//2 - 200))
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Set up the UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Activate FileFlow", 
                  font=("Segoe UI", 18, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Enter your license key to activate the full version", 
                  font=("Segoe UI", 11)).pack(anchor=tk.W)
        
        # License key input section
        key_frame = ttk.Frame(main_frame)
        key_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(key_frame, text="License Key:", 
                  font=("Segoe UI", 11)).pack(anchor=tk.W, pady=(0, 5))
                  
        # License key entry with paste button
        entry_frame = ttk.Frame(key_frame)
        entry_frame.pack(fill=tk.X)
        
        self.license_var = tk.StringVar()
        self.license_entry = ttk.Entry(entry_frame, textvariable=self.license_var, width=45)
        self.license_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        paste_button = ttk.Button(entry_frame, text="Paste", 
                                command=self._paste_from_clipboard)
        paste_button.pack(side=tk.LEFT)
        
        # Product ID display (from your screenshot)
        product_frame = ttk.Frame(main_frame)
        product_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(product_frame, text="Product ID for FileFlow:",
                 font=("Segoe UI", 11)).pack(anchor=tk.W, pady=(0, 5))
        
        product_entry = ttk.Entry(product_frame, width=45)
        product_entry.insert(0, ACCOUNT_INFO["product_id"])
        product_entry.configure(state="readonly")
        product_entry.pack(anchor=tk.W)
        
        # Status message
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var,
                                     foreground=self.colors.get("error", "#F44336"))
        self.status_label.pack(pady=10, fill=tk.X)
        
        # Store license ID from purchase email note
        ttk.Label(main_frame, text="Please enter the license key from your purchase email",
                 font=("Segoe UI", 10, "italic")).pack(anchor=tk.W, pady=(10, 0))
        
        # Button frame at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0), side=tk.BOTTOM)
        
        # Purchase button on the left
        purchase_button = ttk.Button(button_frame, text="Purchase License", 
                                   command=self._open_purchase_page)
        purchase_button.pack(side=tk.LEFT)
        
        # Activate and Cancel buttons on the right
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                 command=self._on_cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.activate_button = ttk.Button(button_frame, text="Activate", 
                                       command=self._activate_license,
                                       style="Primary.TButton")
        self.activate_button.pack(side=tk.RIGHT, padx=(0, 5))
        
        # Demo mode link
        demo_frame = ttk.Frame(main_frame)
        demo_frame.pack(fill=tk.X, pady=10)
        
        demo_button = ttk.Button(demo_frame, text="Continue in Demo Mode", 
                              command=self._use_demo_mode)
        demo_button.pack(side=tk.RIGHT)
        
        # Set initial focus to license key entry
        self.license_entry.focus_set()
        
        # Bind Enter key to activate license
        self.window.bind("<Return>", lambda event: self._activate_license())
    
    def _paste_from_clipboard(self):
        """Paste license key from clipboard."""
        try:
            clipboard_text = self.window.clipboard_get().strip()
            self.license_var.set(clipboard_text)
        except Exception:
            self.status_var.set("Could not paste from clipboard")
    
    def _activate_license(self):
        """Activate the license with the entered key."""
        license_key = self.license_var.get().strip()
        
        if not license_key:
            self.status_var.set("Please enter a valid license key")
            self.status_label.configure(foreground=self.colors.get("error", "#F44336"))
            return
        
        # Disable the activate button during validation
        self.activate_button.configure(state="disabled")
        self.status_var.set("Validating license...")
        self.status_label.configure(foreground=self.colors.get("info", "#2196F3"))
        self.window.update()
        
        # Activate the license
        result = self.license_manager.activate_license(license_key)
        
        if result.get("success"):
            self.status_var.set("License activated successfully!")
            self.status_label.configure(foreground=self.colors.get("success", "#4CAF50"))
            self.window.update()
            
            # Wait a moment before closing
            self.window.after(1500, self._close_with_success)
        else:
            self.status_var.set(f"License activation failed: {result.get('message', 'Invalid key')}")
            self.status_label.configure(foreground=self.colors.get("error", "#F44336"))
            self.activate_button.configure(state="normal")
    
    def _close_with_success(self):
        """Close the window with success status."""
        if self.on_success:
            self.on_success()
        self.window.destroy()
    
    def _on_cancel(self):
        """Handle cancel button."""
        if self.on_cancel:
            self.on_cancel()
        self.window.destroy()
    
    def _use_demo_mode(self):
        """Continue with demo mode."""
        messagebox.showinfo("Demo Mode", 
                          "You are now using FileFlow in demo mode.\n\n"
                          "Some features will be limited. You can activate a license "
                          "at any time from the Help menu.")
        self._on_cancel()
    
    def _open_purchase_page(self):
        """Open the purchase page in a web browser."""
        # Replace with your actual purchase URLs
        purchase_options = {
            "AppSumo": "https://appsumo.com/products/fileflow",
            "Gumroad": "https://gumroad.com/l/fileflow",
            "Official Website": "https://fileflow.example.com/purchase"
        }
        
        # Create a small window with purchase options
        purchase_window = tk.Toplevel(self.window)
        purchase_window.title("Purchase FileFlow")
        purchase_window.geometry("300x200")
        purchase_window.resizable(False, False)
        
        # Center the window
        purchase_window.geometry("+%d+%d" % (
            self.window.winfo_rootx() + self.window.winfo_width()//2 - 150,
            self.window.winfo_rooty() + self.window.winfo_height()//2 - 100))
        
        # Make window modal
        purchase_window.transient(self.window)
        purchase_window.grab_set()
        
        # Content
        frame = ttk.Frame(purchase_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Purchase FileFlow", 
                font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))
        
        ttk.Label(frame, text="Select where you want to purchase:").pack(pady=(0, 10))
        
        # Purchase buttons
        for name, url in purchase_options.items():
            button = ttk.Button(frame, text=name, 
                              command=lambda u=url: self._open_url(u, purchase_window))
            button.pack(fill=tk.X, pady=5)
    
    def _open_url(self, url, window=None):
        """Open a URL in the default web browser."""
        webbrowser.open(url)
        if window:
            window.destroy()


# Integration with FileFlowApp class in fileflow2.py
def add_license_to_app(app):
    """Adds license management functionality to the FileFlow app.
    
    This function should be called from fileflow2.py to integrate
    the licensing system.
    
    Args:
        app: The FileFlowApp instance
    """
    # Add license manager to app
    app.license_manager = LicenseManager()
    
    # Add license check on startup
    def check_license_on_startup():
        result = app.license_manager.check_license()
        if not result.get("success"):
            # Show activation window if no valid license
            LicenseActivationWindow(
                app.root, 
                COLORS, 
                on_success=lambda: app._update_status("License activated successfully"),
                on_cancel=app._update_dashboard
            )
        else:
            app._update_status("License verified")
    
    # Add license menu to Help menu
    def setup_license_menu(help_menu):
        help_menu.add_separator()
        help_menu.add_command(
            label="Activate License", 
            command=lambda: LicenseActivationWindow(
                app.root, 
                COLORS, 
                on_success=lambda: app._update_status("License activated successfully")
            )
        )
        help_menu.add_command(
            label="License Information", 
            command=show_license_info
        )
    
    # Show license information
    def show_license_info():
        result = app.license_manager.check_license()
        
        if result.get("success"):
            license_data = app.license_manager.license_data
            activation_date = license_data.get("activation_date", "Unknown")
            try:
                # Format the date nicely if it's an ISO date string
                date_obj = datetime.datetime.fromisoformat(activation_date)
                activation_date = date_obj.strftime("%B %d, %Y")
            except (ValueError, TypeError):
                pass
                
            messagebox.showinfo(
                "License Information",
                f"FileFlow License Status\n\n"
                f"Status: Active\n"
                f"Product ID: {ACCOUNT_INFO['product_id']}\n"
                f"Activated: {activation_date}\n\n"
                f"Thank you for supporting FileFlow!"
            )
        else:
            messagebox.showwarning(
                "License Information",
                "No active license found.\n\n"
                "You are currently using FileFlow in demo mode.\n"
                "Some features may be limited.\n\n"
                "Please activate a license to unlock all features."
            )
    
    # Return functions to be called from the main app
    return {
        "check_license": check_license_on_startup,
        "setup_license_menu": setup_license_menu,
        "show_license_info": show_license_info
    }


# Constants for colors - should match the ones in fileflow2.py
COLORS = {
    "primary": "#4361EE",
    "secondary": "#3DA5D9",
    "accent": "#EA4C89",
    "background": "#FFFFFF",
    "background_dark": "#121212",
    "surface": "#F8F9FA",
    "text": "#212529",
    "text_secondary": "#6C757D",
    "text_light": "#FFFFFF",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#F44336",
    "info": "#2196F3",
    "gray": "#6C757D",
    "light_gray": "#E9ECEF",
    "border": "#DEE2E6",
    "hover": "#F2F7FF",
}


# For testing the UI independently
if __name__ == "__main__":
    root = tk.Tk()
    root.title("License Test")
    root.geometry("300x200")
    
    def on_success():
        print("License activated successfully!")
    
    def on_cancel():
        print("License activation canceled")
    
    def open_license_window():
        LicenseActivationWindow(root, COLORS, on_success, on_cancel)
    
    button = ttk.Button(root, text="Activate License", command=open_license_window)
    button.pack(padx=50, pady=50)
    
    root.mainloop()
