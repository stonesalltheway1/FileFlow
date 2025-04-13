#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileFlow Webhook Setup Script
-----------------------------
This script helps set up the webhook server for FileFlow's licensing system.
It creates necessary files and guides you through the configuration process.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# ANSI color codes for better readability
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_colored(text, color):
    """Print colored text."""
    print(f"{color}{text}{RESET}")

def check_requirements():
    """Check if all required tools are installed."""
    print_colored("\n=== Checking requirements ===", BOLD)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print_colored(f"❌ Python 3.8+ is required, but you have {python_version.major}.{python_version.minor}", RED)
        return False
    print_colored(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected", GREEN)
    
    # Check pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
        print_colored("✅ pip is installed", GREEN)
    except subprocess.CalledProcessError:
        print_colored("❌ pip is not installed", RED)
        return False
    
    return True

def setup_environment():
    """Set up virtual environment and install dependencies."""
    print_colored("\n=== Setting up environment ===", BOLD)
    
    # Create virtual environment
    if not os.path.exists("webhooks-env"):
        print_colored("Creating virtual environment...", YELLOW)
        try:
            subprocess.run([sys.executable, "-m", "venv", "webhooks-env"], check=True)
            print_colored("✅ Virtual environment created", GREEN)
        except subprocess.CalledProcessError as e:
            print_colored(f"❌ Failed to create virtual environment: {e}", RED)
            return False
    else:
        print_colored("✅ Virtual environment already exists", GREEN)
    
    # Install dependencies
    print_colored("Installing dependencies...", YELLOW)
    
    # Determine the pip path based on the OS
    pip_cmd = os.path.join("webhooks-env", "Scripts", "pip") if os.name == "nt" else os.path.join("webhooks-env", "bin", "pip")
    
    try:
        subprocess.run([pip_cmd, "install", "-r", "requirements-webhooks.txt"], check=True)
        print_colored("✅ Dependencies installed", GREEN)
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Failed to install dependencies: {e}", RED)
        return False
    
    return True

def create_env_file():
    """Create .env file if it doesn't exist."""
    print_colored("\n=== Setting up environment variables ===", BOLD)
    
    if not os.path.exists(".env"):
        print_colored("Creating .env file from template...", YELLOW)
        shutil.copy(".env.example", ".env")
        print_colored("✅ .env file created", GREEN)
        print_colored("⚠️ Please edit the .env file with your actual API keys and secrets", YELLOW)
    else:
        print_colored("✅ .env file already exists", GREEN)
    
    return True

def setup_vercel():
    """Guide the user through setting up Vercel deployment."""
    print_colored("\n=== Vercel Deployment Guide ===", BOLD)
    print_colored("To deploy to Vercel, follow these steps:", YELLOW)
    print("1. Install Vercel CLI: npm install -g vercel")
    print("2. Run: vercel login")
    print("3. Run: vercel")
    print("4. Set up environment variables in the Vercel dashboard")
    
    return True

def main():
    """Main function to run the setup script."""
    print_colored("\n🚀 FileFlow Webhook Setup", BOLD)
    print_colored("===========================", BOLD)
    
    if not check_requirements():
        print_colored("\n❌ Requirements check failed. Please fix the issues and try again.", RED)
        return
    
    if not setup_environment():
        print_colored("\n❌ Environment setup failed. Please fix the issues and try again.", RED)
        return
    
    if not create_env_file():
        print_colored("\n❌ Environment variable setup failed. Please fix the issues and try again.", RED)
        return
    
    setup_vercel()
    
    print_colored("\n✨ Setup completed successfully!", GREEN)
    print_colored("\nNext steps:", BOLD)
    print("1. Edit the .env file with your actual API keys and secrets")
    print("2. Test the webhook locally:")
    if os.name == "nt":
        print("   - webhooks-env\\Scripts\\python keygen_webhooks.py")
    else:
        print("   - source webhooks-env/bin/activate && python keygen_webhooks.py")
    print("3. Deploy to your chosen platform (Vercel or AWS Lambda)")
    print("\nFor more details, refer to the keygen_integration_guide.md file")

if __name__ == "__main__":
    main()
