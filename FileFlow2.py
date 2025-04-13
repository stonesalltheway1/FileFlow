#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileFlow: Intelligent File Organization System
Version: 1.0.0
Released: April 2025
Author: AI-Generated

A sophisticated file organization system that:
- Analyzes user's existing file organization patterns
- Suggests personalized organization systems
- Automatically sorts and renames files based on content
- Cleans up duplicate files
- Maintains consistent naming conventions
"""

import os
import sys
import time
import re
import json
import hashlib
import shutil
import logging
import threading
import queue
import datetime
import mimetypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from collections import defaultdict, Counter
import webbrowser
import urllib.request
import tempfile
import zipfile
import platform
import uuid
import configparser

# Import license management system
from license_ui import add_license_to_app
from feature_protection import premium_feature

# Check Python version
if sys.version_info < (3, 10):
    print("FileFlow requires Python 3.10 or higher. Please upgrade your Python installation.")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fileflow.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FileFlow")

# Constants
VERSION = "1.0.0"
APP_NAME = "FileFlow"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".fileflow", "config.ini")
DATABASE_FILE = os.path.join(os.path.expanduser("~"), ".fileflow", "fileflow_db.json")
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".fileflow")
UPDATE_URL = "https://api.github.com/repos/fileflow/fileflow/releases/latest"
CHUNK_SIZE = 8192  # For reading files in chunks
MIN_FILE_SIZE = 100  # Minimum file size to analyze in bytes

# Ensure application data directory exists
os.makedirs(APP_DATA_DIR, exist_ok=True)

# Theme colors - Modern flat design palette
COLORS = {
    "primary": "#4361EE",      # Modern blue
    "secondary": "#3DA5D9",    # Light blue
    "accent": "#EA4C89",       # Pink (Dribbble color)
    "background": "#FFFFFF",   # Clean white background
    "background_dark": "#121212", # Dark mode background
    "surface": "#F8F9FA",      # Card/panel surface color
    "text": "#212529",         # Dark text
    "text_secondary": "#6C757D", # Secondary text
    "text_light": "#FFFFFF",   # Light text
    "success": "#4CAF50",      # Success green
    "warning": "#FF9800",      # Warning orange
    "error": "#F44336",        # Error red
    "info": "#2196F3",         # Info blue
    "gray": "#6C757D",         # Gray
    "light_gray": "#E9ECEF",   # Light gray
    "border": "#DEE2E6",       # Border color
    "hover": "#F2F7FF",        # Hover state color
}

# File categories and their associated extensions
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".ico"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".tex"],
    "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
    "Presentations": [".ppt", ".pptx", ".key", ".odp"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"],
    "Video": [".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv", ".webm", ".m4v"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".c", ".cpp", ".php", ".rb", ".go", ".ts", ".swift", ".kt"],
    "Data": [".json", ".xml", ".yaml", ".yml", ".sql", ".db", ".sqlite"],
    "Executables": [".exe", ".msi", ".app", ".bat", ".sh", ".command"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "Design": [".psd", ".ai", ".xd", ".sketch", ".fig", ".afdesign"],
    "3D": [".obj", ".fbx", ".blend", ".stl", ".3ds", ".max"],
    "eBooks": [".epub", ".mobi", ".azw", ".azw3", ".ibooks"],
    "Misc": []  # Default category for unrecognized extensions
}

class ConfigManager:
    """Handles application configuration."""
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = CONFIG_FILE
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default if not exists."""
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                return
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Create default configuration
        self.config["General"] = {
            "first_run": "true",
            "auto_update_check": "true",
            "last_update_check": "0",
            "theme": "light"
        }
        
        self.config["Scanning"] = {
            "ignore_hidden_files": "true",
            "ignore_system_files": "true",
            "max_file_size_mb": "1000", 
            "chunk_size_kb": "64",
            "excluded_folders": "node_modules,venv,.git,__pycache__,build,dist"
        }
        
        self.config["Duplicates"] = {
            "min_size_kb": "10",
            "compare_method": "content",  # Options: content, name, both
            "hash_algorithm": "sha256"    # Options: md5, sha1, sha256
        }
        
        self.config["Organization"] = {
            "default_mode": "suggest",    # Options: suggest, auto
            "preserve_original": "true",
            "naming_convention": "camel", # Options: camel, snake, kebab, normal
        }
        
        self.config["Interface"] = {
            "show_tooltips": "true",
            "confirm_operations": "true",
            "max_recent_dirs": "10",
            "use_modern_ui": "true",
            "animation_enabled": "true"
        }
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Save the default configuration
        self.save_config()
    
    def save_config(self):
        """Save the current configuration to file."""
        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, section, option, fallback=None):
        """Get a configuration value."""
        if section in self.config and option in self.config[section]:
            return self.config[section][option]
        return fallback
    
    def set(self, section, option, value):
        """Set a configuration value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][option] = str(value)
        return self.save_config()
    
    def get_boolean(self, section, option, fallback=False):
        """Get a boolean configuration value."""
        value = self.get(section, option)
        if value is None:
            return fallback
        return value.lower() in ("yes", "true", "t", "1")
    
    def get_int(self, section, option, fallback=0):
        """Get an integer configuration value."""
        value = self.get(section, option)
        if value is None:
            return fallback
        try:
            return int(value)
        except ValueError:
            return fallback
    
    def get_float(self, section, option, fallback=0.0):
        """Get a float configuration value."""
        value = self.get(section, option)
        if value is None:
            return fallback
        try:
            return float(value)
        except ValueError:
            return fallback


class FileDatabase:
    """Database for storing file information and organization patterns."""
    
    def __init__(self, db_file=DATABASE_FILE):
        self.db_file = db_file
        self.data = {
            "metadata": {
                "version": VERSION,
                "last_updated": datetime.datetime.now().isoformat(),
                "file_count": 0
            },
            "files": {},
            "directories": {},
            "patterns": {
                "naming": {},
                "organization": {},
                "extensions": {}
            },
            "history": [],
            "stats": {
                "total_size": 0,
                "by_category": {},
                "by_extension": {}
            },
            "settings": {}
        }
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        self.load()
    
    def load(self):
        """Load the database from file."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    loaded_data = json.load(f)
                    self.data.update(loaded_data)
                    return True
            except Exception as e:
                logger.error(f"Error loading database: {e}")
        return False
    
    def save(self):
        """Save the database to file."""
        try:
            self.data["metadata"]["last_updated"] = datetime.datetime.now().isoformat()
            
            with open(self.db_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            return False
    
    def add_file(self, file_path, metadata):
        """Add or update a file in the database."""
        file_path_str = str(file_path)
        self.data["files"][file_path_str] = metadata
        self.data["metadata"]["file_count"] = len(self.data["files"])
        
        # Update extension statistics
        ext = os.path.splitext(file_path_str)[1].lower()
        if ext:
            if ext not in self.data["patterns"]["extensions"]:
                self.data["patterns"]["extensions"][ext] = 0
            self.data["patterns"]["extensions"][ext] += 1
        
        # Update category statistics
        category = self._get_category_for_extension(ext)
        if category not in self.data["stats"]["by_category"]:
            self.data["stats"]["by_category"][category] = {
                "count": 0,
                "size": 0
            }
        
        self.data["stats"]["by_category"][category]["count"] += 1
        self.data["stats"]["by_category"][category]["size"] += metadata.get("size", 0)
        
        # Update total size
        self.data["stats"]["total_size"] += metadata.get("size", 0)
    
    def remove_file(self, file_path):
        """Remove a file from the database."""
        file_path_str = str(file_path)
        if file_path_str in self.data["files"]:
            metadata = self.data["files"][file_path_str]
            
            # Update statistics
            ext = os.path.splitext(file_path_str)[1].lower()
            if ext and ext in self.data["patterns"]["extensions"]:
                self.data["patterns"]["extensions"][ext] -= 1
                if self.data["patterns"]["extensions"][ext] <= 0:
                    del self.data["patterns"]["extensions"][ext]
            
            # Update category statistics
            category = self._get_category_for_extension(ext)
            if category in self.data["stats"]["by_category"]:
                self.data["stats"]["by_category"][category]["count"] -= 1
                self.data["stats"]["by_category"][category]["size"] -= metadata.get("size", 0)
                
                if self.data["stats"]["by_category"][category]["count"] <= 0:
                    del self.data["stats"]["by_category"][category]
            
            # Update total size
            self.data["stats"]["total_size"] -= metadata.get("size", 0)
            
            # Remove the file
            del self.data["files"][file_path_str]
            self.data["metadata"]["file_count"] = len(self.data["files"])
            return True
        
        return False
    
    def get_file(self, file_path):
        """Get file metadata from the database."""
        file_path_str = str(file_path)
        return self.data["files"].get(file_path_str)
    
    def get_all_files(self):
        """Get all files from the database."""
        return self.data["files"]
    
    def get_stats(self):
        """Get database statistics."""
        return self.data["stats"]
    
    def add_directory(self, dir_path, metadata):
        """Add or update a directory in the database."""
        dir_path_str = str(dir_path)
        self.data["directories"][dir_path_str] = metadata
    
    def get_directory(self, dir_path):
        """Get directory metadata from the database."""
        dir_path_str = str(dir_path)
        return self.data["directories"].get(dir_path_str)
    
    def add_history_entry(self, action, details):
        """Add an entry to the history log."""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        self.data["history"].append(entry)
        
        # Limit history to 1000 entries
        if len(self.data["history"]) > 1000:
            self.data["history"] = self.data["history"][-1000:]
    
    def get_history(self, limit=100):
        """Get history entries, most recent first."""
        return list(reversed(self.data["history"][-limit:]))
    
    def add_pattern(self, pattern_type, pattern, count=1):
        """Add or update a pattern in the database."""
        if pattern_type not in self.data["patterns"]:
            self.data["patterns"][pattern_type] = {}
        
        if pattern not in self.data["patterns"][pattern_type]:
            self.data["patterns"][pattern_type][pattern] = 0
        
        self.data["patterns"][pattern_type][pattern] += count
    
    def get_patterns(self, pattern_type):
        """Get patterns of a specific type."""
        if pattern_type in self.data["patterns"]:
            return self.data["patterns"][pattern_type]
        return {}
    
    def clear(self):
        """Clear the database."""
        self.data = {
            "metadata": {
                "version": VERSION,
                "last_updated": datetime.datetime.now().isoformat(),
                "file_count": 0
            },
            "files": {},
            "directories": {},
            "patterns": {
                "naming": {},
                "organization": {},
                "extensions": {}
            },
            "history": [],
            "stats": {
                "total_size": 0,
                "by_category": {},
                "by_extension": {}
            },
            "settings": {}
        }
        self.save()
    
    def _get_category_for_extension(self, extension):
        """Get the category for a file extension."""
        if not extension:
            return "Misc"
        
        extension = extension.lower()
        for category, extensions in FILE_CATEGORIES.items():
            if extension in extensions:
                return category
        
        return "Misc"


class FileScanner:
    """Scans directories for files and extracts metadata."""
    
    def __init__(self, config_manager, file_database):
        self.config = config_manager
        self.db = file_database
        self.scanning = False
        self.scan_queue = queue.Queue()
        self.scan_results = queue.Queue()
        self.scan_thread = None
        self.processed_files = 0
        self.total_files = 0
        self.current_file = ""
        self.cancel_scan = False
    
    def start_scan(self, directory, callback=None):
        """Start scanning a directory in a background thread."""
        if self.scanning:
            return False
        
        self.scanning = True
        self.cancel_scan = False
        self.processed_files = 0
        self.total_files = 0
        self.current_file = ""
        
        # Clear queues
        while not self.scan_queue.empty():
            self.scan_queue.get()
        
        while not self.scan_results.empty():
            self.scan_results.get()
        
        # Start scanning thread
        self.scan_thread = threading.Thread(
            target=self._scan_thread,
            args=(directory, callback),
            daemon=True
        )
        self.scan_thread.start()
        
        return True
    
    def stop_scan(self):
        """Stop the scanning process."""
        self.cancel_scan = True
        
        if self.scan_thread:
            self.scan_thread.join(1.0)
            self.scan_thread = None
        
        self.scanning = False
    
    def get_progress(self):
        """Get the scanning progress."""
        if self.total_files == 0:
            progress = 0
        else:
            progress = self.processed_files / self.total_files
        
        return {
            "processed": self.processed_files,
            "total": self.total_files,
            "progress": progress,
            "current_file": self.current_file,
            "scanning": self.scanning
        }
    
    def _scan_thread(self, directory, callback=None):
        """Background thread for scanning directories."""
        try:
            start_time = time.time()
            logger.info(f"Starting scan of {directory}")
            
            # Count files first
            self.total_files = sum(1 for _ in self._enumerate_files(directory))
            logger.info(f"Found {self.total_files} files to process")
            
            # Process files
            for file_path in self._enumerate_files(directory):
                if self.cancel_scan:
                    logger.info("Scan cancelled")
                    break
                
                self.current_file = file_path
                self.scan_queue.put(file_path)
                
                # Process file
                try:
                    metadata = self._process_file(file_path)
                    if metadata:
                        self.db.add_file(file_path, metadata)
                        self.scan_results.put((file_path, metadata))
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                
                self.processed_files += 1
                
                # Save database periodically
                if self.processed_files % 100 == 0:
                    self.db.save()
                
                # Update callback
                if callback:
                    try:
                        callback(self.get_progress())
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
            
            # Save database
            self.db.save()
            
            end_time = time.time()
            logger.info(f"Scan completed in {end_time - start_time:.2f} seconds")
            
            # Final callback
            if callback:
                try:
                    callback(self.get_progress())
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error in scan thread: {e}")
        finally:
            self.scanning = False
    
    def _enumerate_files(self, directory):
        """Enumerate all files in a directory recursively."""
        ignore_hidden = self.config.get_boolean("Scanning", "ignore_hidden_files", True)
        ignore_system = self.config.get_boolean("Scanning", "ignore_system_files", True)
        max_size_mb = self.config.get_int("Scanning", "max_file_size_mb", 1000)
        max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        
        # Get excluded folders list from config
        excluded_folders_str = self.config.get("Scanning", "excluded_folders", "")
        excluded_folders = [folder.strip() for folder in excluded_folders_str.split(',') if folder.strip()]
        
        for root, dirs, files in os.walk(directory):
            # Filter directories
            # First handle excluded folders (including node_modules, etc.)
            if excluded_folders:
                dirs[:] = [d for d in dirs if d not in excluded_folders]
            
            if ignore_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            if ignore_system:
                # Skip system directories on Windows
                if platform.system() == "Windows":
                    dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d)) and 
                              not os.path.join(root, d).startswith(os.path.join(os.environ.get('SystemRoot', 'C:\\Windows')))]
                # Skip system directories on macOS and Linux
                else:
                    dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d)) and 
                              not d.startswith(('__MACOSX', '.Trash', '.fseventsd', '.Spotlight-V100', 'System Volume Information'))]
            
            # Process files
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip hidden files if configured
                if ignore_hidden and (file.startswith('.') or '\\.' in file_path or '/.' in file_path):
                    continue
                
                # Skip system files if configured
                if ignore_system:
                    if platform.system() == "Windows" and (
                        file.lower() in ('thumbs.db', 'desktop.ini', 'ntuser.dat') or 
                        file_path.startswith(os.path.join(os.environ.get('SystemRoot', 'C:\\Windows')))
                    ):
                        continue
                    elif file in ('.DS_Store', '.localized'):
                        continue
                
                try:
                    # Skip if file is too large
                    size = os.path.getsize(file_path)
                    if max_size > 0 and size > max_size:
                        logger.info(f"Skipping large file: {file_path} ({size/1024/1024:.2f} MB)")
                        continue
                    
                    yield file_path
                except (FileNotFoundError, PermissionError) as e:
                    logger.warning(f"Error accessing file {file_path}: {e}")
    
    def _process_file(self, file_path):
        """Process a file and extract metadata."""
        try:
            stat_info = os.stat(file_path)
            
            # Basic file info
            metadata = {
                "size": stat_info.st_size,
                "created": stat_info.st_ctime,
                "modified": stat_info.st_mtime,
                "accessed": stat_info.st_atime,
                "name": os.path.basename(file_path),
                "extension": os.path.splitext(file_path)[1].lower(),
                "path": os.path.dirname(file_path),
                "is_hidden": os.path.basename(file_path).startswith('.') or '\\.' in file_path or '/.' in file_path,
                "mime_type": self._get_mime_type(file_path),
                "category": self._get_file_category(file_path),
                "hash": self._calculate_file_hash(file_path),
                "scanned_at": datetime.datetime.now().isoformat(),
            }
            
            # Additional metadata based on file type
            if metadata["size"] < MIN_FILE_SIZE:
                return metadata
            
            # Get more detailed metadata based on file type
            self._enrich_metadata(file_path, metadata)
            
            return metadata
        
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"Error processing file {file_path}: {e}")
            return None
    
    def _get_mime_type(self, file_path):
        """Get MIME type of a file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return mime_type
        
        # Try to determine by reading the file
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8192)
                
                # Check for common binary signatures
                if header.startswith(b'\xFF\xD8\xFF'):
                    return 'image/jpeg'
                elif header.startswith(b'\x89PNG\r\n\x1A\n'):
                    return 'image/png'
                elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                    return 'image/gif'
                elif header.startswith(b'%PDF-'):
                    return 'application/pdf'
                elif header.startswith(b'PK\x03\x04'):
                    return 'application/zip'
                elif header.startswith(b'\x50\x4B\x03\x04\x14\x00\x06\x00'):
                    return 'application/vnd.openxmlformats-officedocument'
                
                # Try to detect text files
                try:
                    header.decode('utf-8')
                    return 'text/plain'
                except UnicodeDecodeError:
                    pass
        except Exception:
            pass
        
        return 'application/octet-stream'
    
    def _get_file_category(self, file_path):
        """Get category of a file based on its extension."""
        extension = os.path.splitext(file_path)[1].lower()
        
        for category, extensions in FILE_CATEGORIES.items():
            if extension in extensions:
                return category
        
        return "Misc"
    
    def _calculate_file_hash(self, file_path):
        """Calculate a hash of the file for duplicate detection."""
        hash_algorithm = self.config.get("Duplicates", "hash_algorithm", "sha256")
        
        if hash_algorithm == "md5":
            hasher = hashlib.md5()
        elif hash_algorithm == "sha1":
            hasher = hashlib.sha1()
        else:
            hasher = hashlib.sha256()
        
        chunk_size_kb = self.config.get_int("Scanning", "chunk_size_kb", 64)
        chunk_size = chunk_size_kb * 1024  # Convert to bytes
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b''):
                    hasher.update(chunk)
            
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def _enrich_metadata(self, file_path, metadata):
        """Add more detailed metadata based on file type."""
        mime_type = metadata.get("mime_type", "")
        
        # Extract text content for indexing/categorization
        if mime_type.startswith("text/"):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_sample = f.read(8192)
                    metadata["text_sample"] = text_sample
            except Exception:
                pass
        
        # You can add more specific metadata extraction based on file types
        # For example, image dimensions, document metadata, etc.
        # This would require additional libraries depending on file types
        
        return metadata


class DuplicateFinder:
    """Finds duplicate files in the database."""
    
    def __init__(self, config_manager, file_database):
        self.config = config_manager
        self.db = file_database
        self.processing = False
        self.processed_files = 0
        self.total_files = 0
        self.cancel_requested = False
        self.duplicates = {}  # hash -> [file_paths]
    
    def find_duplicates(self, callback=None):
        """Find duplicate files in the database."""
        if self.processing:
            return False
        
        self.processing = True
        self.cancel_requested = False
        self.processed_files = 0
        self.duplicates = {}
        
        # Start processing thread
        threading.Thread(
            target=self._process_thread,
            args=(callback,),
            daemon=True
        ).start()
        
        return True
    
    def cancel(self):
        """Cancel the duplicate finding process."""
        self.cancel_requested = True
    
    def get_progress(self):
        """Get the duplicate finding progress."""
        if self.total_files == 0:
            progress = 0
        else:
            progress = min(1.0, self.processed_files / self.total_files)
        
        return {
            "processed": self.processed_files,
            "total": self.total_files,
            "progress": progress,
            "duplicates_found": sum(len(files) - 1 for files in self.duplicates.values() if len(files) > 1),
            "processing": self.processing
        }
    
    def get_duplicates(self):
        """Get the list of duplicate files."""
        return {hash_value: file_list for hash_value, file_list in self.duplicates.items() if len(file_list) > 1}
    
    def get_duplicates_by_size(self):
        """Get duplicate files grouped by size."""
        duplicates_by_size = {}
        
        for hash_value, file_list in self.duplicates.items():
            if len(file_list) <= 1:
                continue
            
            # Get the file size
            size = 0
            for file_path in file_list:
                metadata = self.db.get_file(file_path)
                if metadata:
                    size = metadata.get("size", 0)
                    break
            
            if size not in duplicates_by_size:
                duplicates_by_size[size] = []
            
            duplicates_by_size[size].append({
                "hash": hash_value,
                "files": file_list,
                "count": len(file_list),
                "size": size,
                "total_size": size * len(file_list),
                "wasted_size": size * (len(file_list) - 1)
            })
        
        return duplicates_by_size
    
    def get_total_duplicates_stats(self):
        """Get statistics about duplicate files."""
        dupes = self.get_duplicates()
        total_duplicates = 0
        total_size = 0
        wasted_size = 0
        
        for hash_value, file_list in dupes.items():
            file_count = len(file_list)
            if file_count <= 1:
                continue
            
            total_duplicates += file_count - 1  # Original + duplicates
            
            # Get the file size
            size = 0
            for file_path in file_list:
                metadata = self.db.get_file(file_path)
                if metadata:
                    size = metadata.get("size", 0)
                    break
            
            total_size += size * file_count
            wasted_size += size * (file_count - 1)  # Space wasted by duplicates
        
        return {
            "duplicate_groups": len(dupes),
            "total_duplicates": total_duplicates,
            "total_size": total_size,
            "wasted_size": wasted_size
        }
    
    def resolve_duplicates(self, resolution_method, duplicates_to_resolve=None, keep_filter=None, callback=None):
        """Resolve duplicate files.
        
        Args:
            resolution_method: str, one of "delete", "move", "symlink", "hardlink", "rename"
            duplicates_to_resolve: dict, hash -> [file_paths] to resolve, or None for all
            keep_filter: function, takes list of file_paths and returns the path to keep
            callback: function, called with progress updates
        """
        if self.processing:
            return False
        
        self.processing = True
        
        # Start processing thread
        threading.Thread(
            target=self._resolve_thread,
            args=(resolution_method, duplicates_to_resolve, keep_filter, callback),
            daemon=True
        ).start()
        
        return True
    
    def _process_thread(self, callback=None):
        """Background thread for finding duplicates."""
        try:
            start_time = time.time()
            logger.info("Starting duplicate file search")
            
            all_files = self.db.get_all_files()
            self.total_files = len(all_files)
            
            # First pass: group by size
            size_groups = defaultdict(list)
            for file_path, metadata in all_files.items():
                size = metadata.get("size", 0)
                if size < self.config.get_int("Duplicates", "min_size_kb", 10) * 1024:
                    continue
                size_groups[size].append(file_path)
            
            # Second pass: calculate hashes for files of the same size
            potential_dupes = [files for size, files in size_groups.items() if len(files) > 1]
            
            compare_method = self.config.get("Duplicates", "compare_method", "content")
            
            # Process each group
            for group_index, files in enumerate(potential_dupes):
                if self.cancel_requested:
                    logger.info("Duplicate search cancelled")
                    break
                
                if compare_method == "name":
                    # Group by name
                    name_groups = defaultdict(list)
                    for file_path in files:
                        name = os.path.basename(file_path)
                        name_groups[name].append(file_path)
                    
                    # Add duplicate groups
                    for name, file_list in name_groups.items():
                        if len(file_list) > 1:
                            hash_value = f"name:{name}"
                            self.duplicates[hash_value] = file_list
                
                elif compare_method == "content" or compare_method == "both":
                    # Group by hash
                    hash_groups = defaultdict(list)
                    for file_path in files:
                        if self.cancel_requested:
                            break
                        
                        metadata = self.db.get_file(file_path)
                        if metadata and "hash" in metadata:
                            hash_value = metadata["hash"]
                            hash_groups[hash_value].append(file_path)
                        
                        self.processed_files += 1
                        
                        # Update callback
                        if callback and group_index % 10 == 0:
                            try:
                                callback(self.get_progress())
                            except Exception as e:
                                logger.error(f"Error in callback: {e}")
                    
                    # Add duplicate groups
                    for hash_value, file_list in hash_groups.items():
                        if hash_value and len(file_list) > 1:
                            if hash_value in self.duplicates:
                                self.duplicates[hash_value].extend(file_list)
                            else:
                                self.duplicates[hash_value] = file_list
                
                # Also check by name if we're using "both" method
                if compare_method == "both":
                    # Group by name
                    name_groups = defaultdict(list)
                    for file_path in files:
                        name = os.path.basename(file_path)
                        name_groups[name].append(file_path)
                    
                    # Add duplicate groups
                    for name, file_list in name_groups.items():
                        if len(file_list) > 1:
                            hash_value = f"name:{name}"
                            self.duplicates[hash_value] = file_list
            
            end_time = time.time()
            logger.info(f"Duplicate search completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Found {len(self.get_duplicates())} duplicate groups")
            
            # Final callback
            if callback:
                try:
                    callback(self.get_progress())
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error in duplicate search thread: {e}")
        finally:
            self.processing = False
    
    def _resolve_thread(self, resolution_method, duplicates_to_resolve, keep_filter, callback=None):
        """Background thread for resolving duplicates."""
        try:
            start_time = time.time()
            logger.info(f"Starting duplicate resolution with method: {resolution_method}")
            
            if duplicates_to_resolve is None:
                duplicates_to_resolve = self.get_duplicates()
            
            total_groups = len(duplicates_to_resolve)
            processed_groups = 0
            
            # Process each duplicate group
            for hash_value, file_list in duplicates_to_resolve.items():
                if len(file_list) <= 1:
                    continue
                
                if self.cancel_requested:
                    logger.info("Duplicate resolution cancelled")
                    break
                
                # Determine which file to keep
                if keep_filter:
                    file_to_keep = keep_filter(file_list)
                else:
                    # Default: keep the oldest file
                    file_to_keep = file_list[0]
                    oldest_time = float('inf')
                    
                    for file_path in file_list:
                        metadata = self.db.get_file(file_path)
                        if metadata:
                            created_time = metadata.get("created", float('inf'))
                            if created_time < oldest_time:
                                oldest_time = created_time
                                file_to_keep = file_path
                
                # Process duplicates
                for file_path in file_list:
                    if file_path == file_to_keep:
                        continue
                    
                    if resolution_method == "delete":
                        self._delete_duplicate(file_path)
                    elif resolution_method == "move":
                        self._move_duplicate(file_path)
                    elif resolution_method == "symlink":
                        self._symlink_duplicate(file_path, file_to_keep)
                    elif resolution_method == "hardlink":
                        self._hardlink_duplicate(file_path, file_to_keep)
                    elif resolution_method == "rename":
                        self._rename_duplicate(file_path)
                
                processed_groups += 1
                
                # Update callback
                if callback and processed_groups % 10 == 0:
                    try:
                        progress = processed_groups / total_groups
                        callback({
                            "processed": processed_groups,
                            "total": total_groups,
                            "progress": progress,
                            "processing": self.processing
                        })
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
            
            end_time = time.time()
            logger.info(f"Duplicate resolution completed in {end_time - start_time:.2f} seconds")
            
            # Final callback
            if callback:
                try:
                    callback({
                        "processed": processed_groups,
                        "total": total_groups,
                        "progress": 1.0,
                        "processing": False
                    })
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error in duplicate resolution thread: {e}")
        finally:
            self.processing = False
    
    def _delete_duplicate(self, file_path):
        """Delete a duplicate file."""
        try:
            # Use send2trash if available
            try:
                import send2trash
                send2trash.send2trash(file_path)
                logger.info(f"Moved to trash: {file_path}")
            except ImportError:
                # Fall back to os.remove
                os.remove(file_path)
                logger.info(f"Deleted: {file_path}")
            
            # Remove from database
            self.db.remove_file(file_path)
            
            # Add to history
            self.db.add_history_entry("delete_duplicate", {
                "file_path": file_path
            })
            
            return True
        except Exception as e:
            logger.error(f"Error deleting duplicate {file_path}: {e}")
            return False
    
    def _move_duplicate(self, file_path):
        """Move a duplicate file to a duplicates folder."""
        try:
            # Create duplicates folder in the parent directory
            parent_dir = os.path.dirname(file_path)
            duplicates_dir = os.path.join(parent_dir, "Duplicates")
            os.makedirs(duplicates_dir, exist_ok=True)
            
            # Move the file
            filename = os.path.basename(file_path)
            new_path = os.path.join(duplicates_dir, filename)
            
            # If a file with the same name already exists, add a suffix
            if os.path.exists(new_path):
                base, ext = os.path.splitext(filename)
                suffix = 1
                while os.path.exists(new_path):
                    new_path = os.path.join(duplicates_dir, f"{base}_{suffix}{ext}")
                    suffix += 1
            
            shutil.move(file_path, new_path)
            logger.info(f"Moved duplicate: {file_path} -> {new_path}")
            
            # Update database
            self.db.remove_file(file_path)
            
            # Add to history
            self.db.add_history_entry("move_duplicate", {
                "original_path": file_path,
                "new_path": new_path
            })
            
            return True
        except Exception as e:
            logger.error(f"Error moving duplicate {file_path}: {e}")
            return False
    
    def _symlink_duplicate(self, file_path, target_path):
        """Replace a duplicate file with a symbolic link to the original."""
        try:
            # Delete the duplicate
            os.remove(file_path)
            
            # Create a symbolic link
            os.symlink(target_path, file_path)
            logger.info(f"Created symlink: {file_path} -> {target_path}")
            
            # Update database
            self.db.remove_file(file_path)
            
            # Add to history
            self.db.add_history_entry("symlink_duplicate", {
                "symlink_path": file_path,
                "target_path": target_path
            })
            
            return True
        except Exception as e:
            logger.error(f"Error creating symlink for {file_path}: {e}")
            return False
    
    def _hardlink_duplicate(self, file_path, target_path):
        """Replace a duplicate file with a hard link to the original."""
        try:
            # Delete the duplicate
            os.remove(file_path)
            
            # Create a hard link
            os.link(target_path, file_path)
            logger.info(f"Created hardlink: {file_path} -> {target_path}")
            
            # Update database
            self.db.remove_file(file_path)
            
            # Add to history
            self.db.add_history_entry("hardlink_duplicate", {
                "hardlink_path": file_path,
                "target_path": target_path
            })
            
            return True
        except Exception as e:
            logger.error(f"Error creating hardlink for {file_path}: {e}")
            return False
    
    def _rename_duplicate(self, file_path):
        """Rename a duplicate file."""
        try:
            # Get the file name and extension
            dir_path = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            base, ext = os.path.splitext(filename)
            
            # Add a suffix to the file name
            new_filename = f"{base}_duplicate{ext}"
            new_path = os.path.join(dir_path, new_filename)
            
            # If a file with the same name already exists, add a number
            if os.path.exists(new_path):
                suffix = 1
                while os.path.exists(new_path):
                    new_path = os.path.join(dir_path, f"{base}_duplicate_{suffix}{ext}")
                    suffix += 1
            
            # Rename the file
            os.rename(file_path, new_path)
            logger.info(f"Renamed duplicate: {file_path} -> {new_path}")
            
            # Update database
            self.db.remove_file(file_path)
            
            # Scan the renamed file
            metadata = FileScanner(self.config, self.db)._process_file(new_path)
            if metadata:
                self.db.add_file(new_path, metadata)
            
            # Add to history
            self.db.add_history_entry("rename_duplicate", {
                "original_path": file_path,
                "new_path": new_path
            })
            
            return True
        except Exception as e:
            logger.error(f"Error renaming duplicate {file_path}: {e}")
            return False


class FileOrganizer:
    """Organizes files based on content, type, and user patterns."""
    
    def __init__(self, config_manager, file_database):
        self.config = config_manager
        self.db = file_database
        self.processing = False
        self.cancel_requested = False
        self.processed_files = 0
        self.total_files = 0
        self.current_file = ""
    
    def analyze_patterns(self, callback=None):
        """Analyze file organization patterns."""
        if self.processing:
            return False
        
        self.processing = True
        self.cancel_requested = False
        self.processed_files = 0
        self.total_files = 0
        self.current_file = ""
        
        # Start processing thread
        threading.Thread(
            target=self._analyze_thread,
            args=(callback,),
            daemon=True
        ).start()
        
        return True
    
    def suggest_organization(self, directory, callback=None):
        """Suggest organization for files in a directory."""
        if self.processing:
            return False
        
        self.processing = True
        self.cancel_requested = False
        self.processed_files = 0
        self.total_files = 0
        self.current_file = ""
        
        # Start processing thread
        threading.Thread(
            target=self._suggest_thread,
            args=(directory, callback),
            daemon=True
        ).start()
        
        return True
    
    def auto_organize(self, directory, rules=None, callback=None):
        """Automatically organize files in a directory."""
        if self.processing:
            return False
        
        self.processing = True
        self.cancel_requested = False
        self.processed_files = 0
        self.total_files = 0
        self.current_file = ""
        
        # Start processing thread
        threading.Thread(
            target=self._organize_thread,
            args=(directory, rules, callback),
            daemon=True
        ).start()
        
        return True
    
    def cancel(self):
        """Cancel the current operation."""
        self.cancel_requested = True
    
    def get_progress(self):
        """Get the progress of the current operation."""
        if self.total_files == 0:
            progress = 0
        else:
            progress = min(1.0, self.processed_files / self.total_files)
        
        return {
            "processed": self.processed_files,
            "total": self.total_files,
            "progress": progress,
            "current_file": self.current_file,
            "processing": self.processing
        }
    
    def get_organization_suggestions(self, directory):
        """Get organization suggestions for a directory."""
        # Analyze files in the directory
        files = {}
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                metadata = self.db.get_file(file_path)
                if metadata:
                    files[file_path] = metadata
        
        # Group files by category
        by_category = defaultdict(list)
        for file_path, metadata in files.items():
            category = metadata.get("category", "Misc")
            by_category[category].append(file_path)
        
        # Group files by extension
        by_extension = defaultdict(list)
        for file_path, metadata in files.items():
            extension = metadata.get("extension", "").lower()
            if extension:
                by_extension[extension].append(file_path)
        
        # Group files by created year/month
        by_date = defaultdict(list)
        for file_path, metadata in files.items():
            created = metadata.get("created")
            if created:
                date = datetime.datetime.fromtimestamp(created)
                year_month = date.strftime("%Y-%m")
                by_date[year_month].append(file_path)
        
        # Group files by name pattern
        by_name_pattern = defaultdict(list)
        for file_path, metadata in files.items():
            name = metadata.get("name", "")
            # Extract name pattern (e.g., prefix, numbering)
            pattern = self._extract_name_pattern(name)
            if pattern:
                by_name_pattern[pattern].append(file_path)
        
        # Create suggestions
        suggestions = {
            "by_category": {category: len(files) for category, files in by_category.items()},
            "by_extension": {ext: len(files) for ext, files in by_extension.items()},
            "by_date": {date: len(files) for date, files in by_date.items()},
            "by_name_pattern": {pattern: len(files) for pattern, files in by_name_pattern.items()},
            "total_files": len(files)
        }
        
        return suggestions
    
    def get_rename_suggestions(self, files):
        """Get rename suggestions for files."""
        suggestions = []
        
        for file_path in files:
            metadata = self.db.get_file(file_path)
            if not metadata:
                continue
            
            original_name = metadata.get("name", "")
            extension = metadata.get("extension", "").lower()
            category = metadata.get("category", "Misc")
            created = metadata.get("created")
            
            # Build suggested name
            suggested_name = original_name
            
            # Clean up spaces and special characters
            suggested_name = re.sub(r'[^\w\s.-]', '', suggested_name)
            
            # Apply naming convention
            naming_convention = self.config.get("Organization", "naming_convention", "camel")
            
            if naming_convention == "camel":
                # Convert to CamelCase
                suggested_name = "".join(word.capitalize() for word in re.split(r'[\s_-]+', suggested_name))
            elif naming_convention == "snake":
                # Convert to snake_case
                suggested_name = re.sub(r'[\s-]+', '_', suggested_name.lower())
            elif naming_convention == "kebab":
                # Convert to kebab-case
                suggested_name = re.sub(r'[\s_]+', '-', suggested_name.lower())
            else:
                # Normal case with spaces
                suggested_name = re.sub(r'[_-]+', ' ', suggested_name)
                suggested_name = " ".join(word.capitalize() for word in suggested_name.split())
            
            # Add date prefix if created date is available
            if created:
                date = datetime.datetime.fromtimestamp(created)
                date_prefix = date.strftime("%Y-%m-%d_")
                
                # Only add if not already present
                if not suggested_name.startswith(date_prefix):
                    suggested_name = date_prefix + suggested_name
            
            # Add extension if not present
            if extension and not suggested_name.endswith(extension):
                suggested_name += extension
            
            # Only add if different from original
            if suggested_name != original_name:
                suggestions.append({
                    "file_path": file_path,
                    "original_name": original_name,
                    "suggested_name": suggested_name
                })
        
        return suggestions
    
    def auto_rename(self, files, rename_mapping=None, callback=None):
        """Automatically rename files."""
        if self.processing:
            return False
        
        self.processing = True
        self.cancel_requested = False
        self.processed_files = 0
        self.total_files = len(files)
        self.current_file = ""
        
        # Start processing thread
        threading.Thread(
            target=self._rename_thread,
            args=(files, rename_mapping, callback),
            daemon=True
        ).start()
        
        return True
    
    def _rename_thread(self, files, rename_mapping, callback=None):
        """Background thread for renaming files."""
        try:
            start_time = time.time()
            logger.info(f"Starting auto rename for {len(files)} files")
            
            # Generate rename suggestions if not provided
            if rename_mapping is None:
                rename_mapping = {}
                suggestions = self.get_rename_suggestions(files)
                
                for suggestion in suggestions:
                    file_path = suggestion["file_path"]
                    suggested_name = suggestion["suggested_name"]
                    rename_mapping[file_path] = suggested_name
            
            # Process each file
            for file_path in files:
                if self.cancel_requested:
                    logger.info("Auto rename cancelled")
                    break
                
                self.current_file = file_path
                
                # Skip if no mapping for this file
                if file_path not in rename_mapping:
                    self.processed_files += 1
                    continue
                
                new_name = rename_mapping[file_path]
                
                # Rename the file
                try:
                    dir_path = os.path.dirname(file_path)
                    new_path = os.path.join(dir_path, new_name)
                    
                    # Skip if the new path already exists
                    if os.path.exists(new_path):
                        logger.warning(f"Cannot rename {file_path}: {new_path} already exists")
                        self.processed_files += 1
                        continue
                    
                    # Rename
                    os.rename(file_path, new_path)
                    logger.info(f"Renamed {file_path} to {new_path}")
                    
                    # Update database
                    metadata = self.db.get_file(file_path)
                    if metadata:
                        metadata["name"] = new_name
                        metadata["path"] = dir_path
                        
                        self.db.remove_file(file_path)
                        self.db.add_file(new_path, metadata)
                    
                    # Add to history
                    self.db.add_history_entry("rename", {
                        "original_path": file_path,
                        "new_path": new_path
                    })
                
                except Exception as e:
                    logger.error(f"Error renaming {file_path}: {e}")
                
                self.processed_files += 1
                
                # Update callback
                if callback and self.processed_files % 10 == 0:
                    try:
                        callback(self.get_progress())
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
            
            # Save database
            self.db.save()
            
            end_time = time.time()
            logger.info(f"Auto rename completed in {end_time - start_time:.2f} seconds")
            
            # Final callback
            if callback:
                try:
                    callback(self.get_progress())
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error in auto rename thread: {e}")
        finally:
            self.processing = False
    
    def _analyze_thread(self, callback=None):
        """Background thread for analyzing file organization patterns."""
        try:
            start_time = time.time()
            logger.info("Starting organization pattern analysis")
            
            all_files = self.db.get_all_files()
            self.total_files = len(all_files)
            
            # Analyze file naming patterns
            naming_patterns = defaultdict(int)
            
            for file_path, metadata in all_files.items():
                if self.cancel_requested:
                    logger.info("Pattern analysis cancelled")
                    break
                
                self.current_file = file_path
                
                name = metadata.get("name", "")
                pattern = self._extract_name_pattern(name)
                if pattern:
                    naming_patterns[pattern] += 1
                
                self.processed_files += 1
                
                # Update callback
                if callback and self.processed_files % 100 == 0:
                    try:
                        callback(self.get_progress())
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
            
            # Analyze directory structure patterns
            dir_patterns = defaultdict(int)
            
            for file_path, _ in all_files.items():
                dir_path = os.path.dirname(file_path)
                pattern = self._extract_dir_pattern(dir_path)
                if pattern:
                    dir_patterns[pattern] += 1
            
            # Save patterns to database
            for pattern, count in naming_patterns.items():
                self.db.add_pattern("naming", pattern, count)
            
            for pattern, count in dir_patterns.items():
                self.db.add_pattern("organization", pattern, count)
            
            # Save database
            self.db.save()
            
            end_time = time.time()
            logger.info(f"Pattern analysis completed in {end_time - start_time:.2f} seconds")
            
            # Final callback
            if callback:
                try:
                    callback(self.get_progress())
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error in pattern analysis thread: {e}")
        finally:
            self.processing = False
    
    def _suggest_thread(self, directory, callback=None):
        """Background thread for suggesting organization."""
        try:
            start_time = time.time()
            logger.info(f"Starting organization suggestions for {directory}")
            
            # Count files
            self.total_files = sum(1 for _ in self._enumerate_files(directory))
            
            # Get suggestions
            suggestions = self.get_organization_suggestions(directory)
            
            end_time = time.time()
            logger.info(f"Organization suggestions completed in {end_time - start_time:.2f} seconds")
            
            # Final callback
            if callback:
                try:
                    callback({
                        "processed": self.total_files,
                        "total": self.total_files,
                        "progress": 1.0,
                        "suggestions": suggestions,
                        "processing": False
                    })
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error in suggestion thread: {e}")
        finally:
            self.processing = False
    
    def _organize_thread(self, directory, rules, callback=None):
        """Background thread for automatically organizing files."""
        try:
            start_time = time.time()
            logger.info(f"Starting auto organization for {directory}")
            
            # Count files
            self.total_files = sum(1 for _ in self._enumerate_files(directory))
            
            # If no rules provided, use default organization rules
            if rules is None:
                rules = self._generate_default_rules(directory)
            
            # Process each file
            moved_files = []
            
            for file_path in self._enumerate_files(directory):
                if self.cancel_requested:
                    logger.info("Auto organization cancelled")
                    break
                
                self.current_file = file_path
                
                # Get metadata
                metadata = self.db.get_file(file_path)
                if not metadata:
                    # Scan file if not in database
                    scanner = FileScanner(self.config, self.db)
                    metadata = scanner._process_file(file_path)
                    if metadata:
                        self.db.add_file(file_path, metadata)
                
                if metadata:
                    # Apply rules
                    destination = self._apply_rules(file_path, metadata, rules)
                    
                    if destination and destination != os.path.dirname(file_path):
                        # Move the file
                        try:
                            os.makedirs(destination, exist_ok=True)
                            
                            filename = os.path.basename(file_path)
                            new_path = os.path.join(destination, filename)
                            
                            # If a file with the same name already exists, add a suffix
                            if os.path.exists(new_path):
                                base, ext = os.path.splitext(filename)
                                suffix = 1
                                while os.path.exists(new_path):
                                    new_path = os.path.join(destination, f"{base}_{suffix}{ext}")
                                    suffix += 1
                            
                            # Move the file
                            shutil.move(file_path, new_path)
                            logger.info(f"Moved {file_path} to {new_path}")
                            
                            # Update database
                            self.db.remove_file(file_path)
                            metadata["path"] = destination
                            self.db.add_file(new_path, metadata)
                            
                            # Add to history
                            self.db.add_history_entry("move", {
                                "original_path": file_path,
                                "new_path": new_path
                            })
                            
                            moved_files.append({
                                "original_path": file_path,
                                "new_path": new_path
                            })
                        
                        except Exception as e:
                            logger.error(f"Error moving {file_path}: {e}")
                
                self.processed_files += 1
                
                # Update callback
                if callback and self.processed_files % 10 == 0:
                    try:
                        callback({
                            "processed": self.processed_files,
                            "total": self.total_files,
                            "progress": self.processed_files / self.total_files,
                            "moved_files": moved_files,
                            "processing": self.processing
                        })
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
            
            # Save database
            self.db.save()
            
            end_time = time.time()
            logger.info(f"Auto organization completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Moved {len(moved_files)} files")
            
            # Final callback
            if callback:
                try:
                    callback({
                        "processed": self.processed_files,
                        "total": self.total_files,
                        "progress": 1.0,
                        "moved_files": moved_files,
                        "processing": False
                    })
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error in organization thread: {e}")
        finally:
            self.processing = False
    
    def _enumerate_files(self, directory):
        """Enumerate all files in a directory recursively."""
        for root, dirs, files in os.walk(directory):
            for file in files:
                yield os.path.join(root, file)
    
    def _extract_name_pattern(self, filename):
        """Extract pattern from a filename."""
        # Remove extension
        name, _ = os.path.splitext(filename)
        
        # Check for date patterns
        date_pattern = re.search(r'^\d{4}-\d{2}-\d{2}', name)
        if date_pattern:
            return "date_prefix"
        
        # Check for numbered sequences
        number_pattern = re.search(r'(\D+)(\d+)$', name)
        if number_pattern:
            return f"numbered_{number_pattern.group(1)}"
        
        # Check for common prefixes
        prefix_pattern = re.search(r'^([A-Za-z]+)_', name)
        if prefix_pattern:
            return f"prefix_{prefix_pattern.group(1)}"
        
        return None
    
    def _extract_dir_pattern(self, dir_path):
        """Extract pattern from a directory path."""
        # Split the directory path
        parts = dir_path.replace('\\', '/').split('/')
        
        if not parts:
            return None
        
        # Check for category-based organization
        last_part = parts[-1]
        
        for category in FILE_CATEGORIES.keys():
            if last_part.lower() == category.lower():
                return "category_based"
        
        # Check for date-based organization
        date_pattern = re.search(r'^(\d{4})([-_/](\d{2}))?$', last_part)
        if date_pattern:
            return "date_based"
        
        # Check for alphabetical organization
        alpha_pattern = re.search(r'^[A-Za-z]$', last_part)
        if alpha_pattern:
            return "alphabetical"
        
        return None
    
    def _generate_default_rules(self, directory):
        """Generate default organization rules."""
        rules = []
        
        # Rule 1: Organize by category
        rules.append({
            "type": "category",
            "destination": "{category}"
        })
        
        # Rule 2: For images, also organize by date
        rules.append({
            "type": "category",
            "category": "Images",
            "destination": "Images/{year}/{month}"
        })
        
        # Rule 3: For documents, organize by year
        rules.append({
            "type": "category",
            "category": "Documents",
            "destination": "Documents/{year}"
        })
        
        return rules
    
    def _apply_rules(self, file_path, metadata, rules):
        """Apply organization rules to a file."""
        for rule in rules:
            rule_type = rule.get("type", "")
            
            if rule_type == "category":
                # Check if the rule applies to this file
                category = metadata.get("category", "Misc")
                rule_category = rule.get("category")
                
                if rule_category and category != rule_category:
                    continue
                
                # Get the destination pattern
                destination_pattern = rule.get("destination", "{category}")
                
                # Replace placeholders
                destination = destination_pattern
                
                # Basic replacements
                destination = destination.replace("{category}", category)
                
                # File extension
                extension = metadata.get("extension", "").lower()
                if extension:
                    destination = destination.replace("{extension}", extension[1:])  # Remove the dot
                
                # Date placeholders
                created = metadata.get("created")
                if created:
                    date = datetime.datetime.fromtimestamp(created)
                    
                    destination = destination.replace("{year}", date.strftime("%Y"))
                    destination = destination.replace("{month}", date.strftime("%m"))
                    destination = destination.replace("{day}", date.strftime("%d"))
                    destination = destination.replace("{date}", date.strftime("%Y-%m-%d"))
                
                # Join with the base directory
                destination_path = os.path.join(os.path.dirname(file_path), destination)
                
                return destination_path
            
            elif rule_type == "extension":
                # Check if the rule applies to this file
                extension = metadata.get("extension", "").lower()
                rule_extension = rule.get("extension", "").lower()
                
                if rule_extension and extension != rule_extension:
                    continue
                
                # Get the destination pattern
                destination_pattern = rule.get("destination", "{extension}")
                
                # Replace placeholders
                destination = destination_pattern
                
                if extension:
                    destination = destination.replace("{extension}", extension[1:])  # Remove the dot
                
                # Join with the base directory
                destination_path = os.path.join(os.path.dirname(file_path), destination)
                
                return destination_path
            
            elif rule_type == "date":
                # Check if the rule applies to this file
                created = metadata.get("created")
                if not created:
                    continue
                
                # Get the destination pattern
                destination_pattern = rule.get("destination", "{year}/{month}")
                
                # Replace placeholders
                destination = destination_pattern
                
                date = datetime.datetime.fromtimestamp(created)
                
                destination = destination.replace("{year}", date.strftime("%Y"))
                destination = destination.replace("{month}", date.strftime("%m"))
                destination = destination.replace("{day}", date.strftime("%d"))
                destination = destination.replace("{date}", date.strftime("%Y-%m-%d"))
                
                # Join with the base directory
                destination_path = os.path.join(os.path.dirname(file_path), destination)
                
                return destination_path
        
        # No rule applied
        return None


class UpdateManager:
    """Handles checking for updates and updating the application."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.checking = False
        self.update_available = False
        self.latest_version = None
        self.update_url = None
    
    def check_for_updates(self, force=False, callback=None):
        """Check for updates."""
        if self.checking:
            return False
        
        # Check if we've checked recently
        if not force:
            last_check = self.config.get_int("General", "last_update_check", 0)
            if time.time() - last_check < 86400:  # Check once per day
                if callback:
                    callback({
                        "checking": False,
                        "update_available": self.update_available,
                        "latest_version": self.latest_version,
                        "current_version": VERSION
                    })
                return False
        
        self.checking = True
        
        # Start check thread
        threading.Thread(
            target=self._check_thread,
            args=(callback,),
            daemon=True
        ).start()
        
        return True
    
    def _check_thread(self, callback=None):
        """Background thread for checking updates."""
        try:
            logger.info("Checking for updates...")
            
            # Update the last check time
            self.config.set("General", "last_update_check", int(time.time()))
            
            try:
                # Fetch update information
                with urllib.request.urlopen(UPDATE_URL, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    latest_version = data.get("tag_name", "").lstrip('v')
                    self.latest_version = latest_version
                    
                    # Compare versions
                    if self._compare_versions(latest_version, VERSION) > 0:
                        self.update_available = True
                        self.update_url = data.get("html_url", "")
                        logger.info(f"Update available: {latest_version}")
                    else:
                        self.update_available = False
                        logger.info("No updates available")
            
            except Exception as e:
                logger.error(f"Error checking for updates: {e}")
                self.update_available = False
            
            # Callback
            if callback:
                try:
                    callback({
                        "checking": False,
                        "update_available": self.update_available,
                        "latest_version": self.latest_version,
                        "current_version": VERSION
                    })
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error in update check thread: {e}")
        finally:
            self.checking = False
    
    def download_update(self, callback=None):
        """Download and install the update."""
        if not self.update_available or not self.update_url:
            return False
        
        # Start download thread
        threading.Thread(
            target=self._download_thread,
            args=(callback,),
            daemon=True
        ).start()
        
        return True
    
    def _download_thread(self, callback=None):
        """Background thread for downloading updates."""
        try:
            logger.info(f"Downloading update from {self.update_url}")
            
            try:
                # Download the update
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    with urllib.request.urlopen(self.update_url) as response:
                        total_size = int(response.info().get('Content-Length', 0))
                        downloaded = 0
                        
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            
                            tmp_file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update callback
                            if callback:
                                progress = downloaded / total_size if total_size > 0 else 0
                                try:
                                    callback({
                                        "downloading": True,
                                        "progress": progress,
                                        "downloaded": downloaded,
                                        "total_size": total_size
                                    })
                                except Exception as e:
                                    logger.error(f"Error in callback: {e}")
                
                # Extract the update
                target_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
                
                # Replace the application files
                # This would normally require platform-specific code or an installer
                # For simplicity, we'll just show a message to the user
                if callback:
                    try:
                        callback({
                            "downloading": False,
                            "progress": 1.0,
                            "downloaded": total_size,
                            "total_size": total_size,
                            "extract_path": target_dir,
                            "message": "Update downloaded. Please restart the application to apply the update."
                        })
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
            
            except Exception as e:
                logger.error(f"Error downloading update: {e}")
                if callback:
                    try:
                        callback({
                            "downloading": False,
                            "error": str(e)
                        })
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error in download thread: {e}")
    
    def _compare_versions(self, version1, version2):
        """Compare two version strings."""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        # Pad with zeros to ensure same length
        while len(v1_parts) < len(v2_parts):
            v1_parts.append(0)
        while len(v2_parts) < len(v1_parts):
            v2_parts.append(0)
        
        # Compare parts
        for i in range(len(v1_parts)):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0


class FileFlowApp:
    """Main application class."""
    
    def __init__(self):
        # Initialize components
        self.config = ConfigManager()
        self.db = FileDatabase()
        self.scanner = FileScanner(self.config, self.db)
        self.duplicate_finder = DuplicateFinder(self.config, self.db)
        self.organizer = FileOrganizer(self.config, self.db)
        self.update_manager = UpdateManager(self.config)
        
        # Initialize license management system
        self.license_functions = add_license_to_app(self)
        
        # Set up the UI
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Set icon if available
        try:
            self.root.iconbitmap("fileflow.ico")
        except Exception:
            pass
        
        # Initialize UI
        self._setup_ui()
        
        # Check for updates on startup
        if self.config.get_boolean("General", "auto_update_check", True):
            self.update_manager.check_for_updates(callback=self._update_check_callback)
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Configure style
        self._setup_style()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create menu bar
        self._setup_menu()
        
        # Create main sections
        self._setup_top_panel()
        self._setup_tabs()
        self._setup_status_bar()
    
    def _setup_style(self):
        """Set up TTK style with a modern look and feel."""
        try:
            style = ttk.Style()
            
            # Check if modern UI is enabled
            use_modern_ui = self.config.get_boolean("Interface", "use_modern_ui", True)
            
            # Configure colors based on theme
            if self.config.get("General", "theme", "light") == "dark":
                # Use a safer default theme
                try:
                    style.theme_use("clam")
                except Exception:
                    # Fall back to default if clam is not available
                    pass
                    
                bg_color = COLORS["background_dark"]
                surface_color = "#1E1E1E"
                fg_color = COLORS["text_light"]
                accent_color = COLORS["accent"]
                border_color = "#333333"
            else:
                try:
                    style.theme_use("clam")
                except Exception:
                    # Fall back to default if clam is not available
                    pass
                    
                bg_color = COLORS["background"]
                surface_color = COLORS["surface"]
                fg_color = COLORS["text"]
                accent_color = COLORS["primary"]
                border_color = COLORS["border"]
            
            # Set basic styles that should work on all systems
            style.configure("TFrame", background=bg_color)
            style.configure("TLabel", background=bg_color, foreground=fg_color)
            style.configure("TButton", background=accent_color, foreground="#FFFFFF")
            
            # Create custom header styles - using simple parameters that should work everywhere
            style.configure("Title.TLabel", font=("Segoe UI", 18))
            style.configure("Subtitle.TLabel", font=("Segoe UI", 14))
            style.configure("H1.TLabel", font=("Segoe UI", 20))
            style.configure("H2.TLabel", font=("Segoe UI", 18))
            style.configure("H3.TLabel", font=("Segoe UI", 16))
            
            # Create button styles that should be safe
            style.configure("Primary.TButton", background=COLORS["primary"], foreground=COLORS["text_light"])
            style.configure("Success.TButton", background=COLORS["success"], foreground=COLORS["text_light"])
            style.configure("Warning.TButton", background=COLORS["warning"], foreground=COLORS["text_light"])
            style.configure("Error.TButton", background=COLORS["error"], foreground=COLORS["text_light"])
            
            # Only apply modern UI styles if enabled and after basic styles work
            if use_modern_ui:
                try:
                    # Card style for frames
                    style.configure("Card.TFrame", background=surface_color, relief="solid", borderwidth=1)
                    
                    # Modern buttons
                    style.configure("TButton", padding=5, relief="flat")
                    style.map("TButton", 
                          background=[("active", COLORS["secondary"]), ("disabled", COLORS["light_gray"])],
                          foreground=[("disabled", COLORS["gray"])])
                    
                    # Configure notebook with tabs
                    style.configure("TNotebook", background=bg_color)
                    style.configure("TNotebook.Tab", background=bg_color, foreground=fg_color, padding=5)
                    style.map("TNotebook.Tab", 
                          background=[("selected", accent_color)], 
                          foreground=[("selected", COLORS["text_light"])])
                    
                    # Configure treeview
                    style.configure("Treeview", 
                                background=surface_color,
                                fieldbackground=surface_color,
                                foreground=fg_color)
                    style.configure("Treeview.Heading", 
                                background=bg_color,
                                foreground=fg_color)
                    style.map("Treeview", 
                          background=[("selected", COLORS["hover"])],
                          foreground=[("selected", accent_color)])
                except Exception as e:
                    logger.warning(f"Could not apply all modern UI styles: {e}")
            
            # Set root background color
            self.root.configure(background=bg_color)
            
        except Exception as e:
            # Log error but continue with default styling
            logger.error(f"Error setting up styles: {e}")
            # Create minimal styling to ensure the app can run
            try:
                style = ttk.Style()
                style.configure("TLabel", font=("Segoe UI", 10))
                style.configure("H1.TLabel", font=("Segoe UI", 20))
                style.configure("H2.TLabel", font=("Segoe UI", 18))
                style.configure("H3.TLabel", font=("Segoe UI", 16))
                style.configure("TButton")
                style.configure("Primary.TButton")
                style.configure("Card.TFrame")
            except Exception:
                # If even minimal styling fails, we'll use default tkinter styling
                pass
    
    def _setup_menu(self):
        """Set up the menu bar."""
        try:
            # Create menu bar
            menu_bar = tk.Menu(self.root)
            
            # File menu
            file_menu = tk.Menu(menu_bar, tearoff=0)
            file_menu.add_command(label="Scan Directory", command=self._select_scan_directory)
            file_menu.add_command(label="Scan Recent", command=self._scan_recent)
            file_menu.add_separator()
            file_menu.add_command(label="Import Database", command=self._import_database)
            file_menu.add_command(label="Export Database", command=self._export_database)
            file_menu.add_separator()
            file_menu.add_command(label="Clear Database", command=self._clear_database)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.root.quit)
            menu_bar.add_cascade(label="File", menu=file_menu)
            
            # Tools menu
            tools_menu = tk.Menu(menu_bar, tearoff=0)
            tools_menu.add_command(label="Find Duplicates", command=self._find_duplicates)
            tools_menu.add_command(label="Auto Organize Files", command=self._auto_organize)
            tools_menu.add_command(label="Rename Files", command=self._rename_files)
            menu_bar.add_cascade(label="Tools", menu=tools_menu)
            
            # Settings menu
            settings_menu = tk.Menu(menu_bar, tearoff=0)
            settings_menu.add_command(label="Preferences", command=self._show_preferences)
            settings_menu.add_separator()
            
            # Theme submenu
            theme_menu = tk.Menu(settings_menu, tearoff=0)
            theme_menu.add_command(label="Light", command=lambda: self._change_theme("light"))
            theme_menu.add_command(label="Dark", command=lambda: self._change_theme("dark"))
            settings_menu.add_cascade(label="Theme", menu=theme_menu)
            
            menu_bar.add_cascade(label="Settings", menu=settings_menu)
            
            # Help menu
            help_menu = tk.Menu(menu_bar, tearoff=0)
            help_menu.add_command(label="Help", command=self._show_help)
            help_menu.add_command(label="About", command=self._show_about)
            help_menu.add_separator()
            help_menu.add_command(label="Check for Updates", command=lambda: self.update_manager.check_for_updates(force=True, callback=self._update_check_callback))
            
            # Add license menu items
            self.license_functions["setup_license_menu"](help_menu)
            
            menu_bar.add_cascade(label="Help", menu=help_menu)
            
            # Set the menu to the root window
            self.root.config(menu=menu_bar)
            
        except Exception as e:
            # Log the error for debugging purposes
            logger.error(f"Error setting up menu: {e}")
            # Create a minimal menu bar if the regular one fails
            try:
                minimal_menu = tk.Menu(self.root)
                file_menu = tk.Menu(minimal_menu, tearoff=0)
                file_menu.add_command(label="Exit", command=self.root.quit)
                minimal_menu.add_cascade(label="File", menu=file_menu)
                self.root.config(menu=minimal_menu)
            except Exception as e2:
                logger.error(f"Even minimal menu failed: {e2}")
    
    def _setup_top_panel(self):
        """Set up the top panel with quick action buttons."""
        top_panel = ttk.Frame(self.main_frame)
        top_panel.pack(fill=tk.X, padx=5, pady=5)
        
        # Title
        title_label = ttk.Label(top_panel, text=APP_NAME, style="H1.TLabel")
        title_label.pack(side=tk.LEFT, padx=5)
        
        # Quick action buttons
        scan_button = ttk.Button(top_panel, text="Scan Directory", style="Primary.TButton", command=self._select_scan_directory)
        scan_button.pack(side=tk.RIGHT, padx=5)
        
        duplicates_button = ttk.Button(top_panel, text="Find Duplicates", command=self._find_duplicates)
        duplicates_button.pack(side=tk.RIGHT, padx=5)
        
        organize_button = ttk.Button(top_panel, text="Auto Organize", command=self._auto_organize)
        organize_button.pack(side=tk.RIGHT, padx=5)
    
    def _setup_tabs(self):
        """Set up the main content tabs."""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Dashboard tab
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self._setup_dashboard()
        
        # Duplicates tab
        self.duplicates_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.duplicates_frame, text="Duplicates")
        self._setup_duplicates_tab()
        
        # Organization tab
        self.organization_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.organization_frame, text="Organization")
        self._setup_organization_tab()
        
        # Statistics tab
        self.statistics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.statistics_frame, text="Statistics")
        self._setup_statistics_tab()
        
        # History tab
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="History")
        self._setup_history_tab()
    
    def _setup_dashboard(self):
        """Set up the dashboard tab with a modern UI."""
        # Main dashboard container
        dashboard = ttk.Frame(self.dashboard_frame)
        dashboard.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Welcome message
        welcome_frame = ttk.Frame(dashboard)
        welcome_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(welcome_frame, text="Welcome to FileFlow", style="H1.TLabel").pack(anchor=tk.W)
        ttk.Label(welcome_frame, text="Your intelligent file organization system", style="Subtitle.TLabel").pack(anchor=tk.W)
        
        # Top section with stats overview in card style
        stats_frame = ttk.Frame(dashboard)
        stats_frame.pack(fill=tk.X, pady=10)
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        stats_frame.columnconfigure(3, weight=1)
        
        # Files scanned card with modern styling
        files_card = ttk.Frame(stats_frame, style="Card.TFrame")
        files_card.grid(row=0, column=0, padx=8, pady=5, sticky="nesw")
        
        files_card_inner = ttk.Frame(files_card)
        files_card_inner.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        ttk.Label(files_card_inner, text="Files Scanned", foreground=COLORS["text_secondary"]).pack(anchor=tk.W)
        self.files_count_label = ttk.Label(files_card_inner, text="0", font=("Segoe UI", 28, "bold"))
        self.files_count_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Total size card
        size_card = ttk.Frame(stats_frame, style="Card.TFrame")
        size_card.grid(row=0, column=1, padx=8, pady=5, sticky="nesw")
        
        size_card_inner = ttk.Frame(size_card)
        size_card_inner.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        ttk.Label(size_card_inner, text="Total Size", foreground=COLORS["text_secondary"]).pack(anchor=tk.W)
        self.total_size_label = ttk.Label(size_card_inner, text="0 MB", font=("Segoe UI", 28, "bold"))
        self.total_size_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Duplicates card
        dupes_card = ttk.Frame(stats_frame, style="Card.TFrame")
        dupes_card.grid(row=0, column=2, padx=8, pady=5, sticky="nesw")
        
        dupes_card_inner = ttk.Frame(dupes_card)
        dupes_card_inner.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        ttk.Label(dupes_card_inner, text="Duplicate Files", foreground=COLORS["text_secondary"]).pack(anchor=tk.W)
        self.dupes_count_label = ttk.Label(dupes_card_inner, text="0", font=("Segoe UI", 28, "bold"))
        self.dupes_count_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Space wasted card
        saved_card = ttk.Frame(stats_frame, style="Card.TFrame")
        saved_card.grid(row=0, column=3, padx=8, pady=5, sticky="nesw")
        
        saved_card_inner = ttk.Frame(saved_card)
        saved_card_inner.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        ttk.Label(saved_card_inner, text="Space Wasted", foreground=COLORS["text_secondary"]).pack(anchor=tk.W)
        self.space_saved_label = ttk.Label(saved_card_inner, text="0 MB", font=("Segoe UI", 28, "bold"))
        self.space_saved_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Quick actions section
        actions_section = ttk.Frame(dashboard)
        actions_section.pack(fill=tk.X, pady=20)
        
        ttk.Label(actions_section, text="Quick Actions", style="H2.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        actions_container = ttk.Frame(actions_section, style="Card.TFrame")
        actions_container.pack(fill=tk.X, padx=0, pady=0)
        
        actions_inner = ttk.Frame(actions_container)
        actions_inner.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Action buttons with icons (using text symbols as placeholders)
        scan_btn = ttk.Button(actions_inner, text="📂 Scan Directory", 
                            style="Primary.TButton", 
                            command=self._select_scan_directory)
        scan_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        dupe_btn = ttk.Button(actions_inner, text="🔍 Find Duplicates", 
                            command=self._find_duplicates)
        dupe_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        org_btn = ttk.Button(actions_inner, text="🗂 Auto Organize", 
                           command=self._auto_organize)
        org_btn.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        clean_btn = ttk.Button(actions_inner, text="🧹 Cleanup Suggestions", 
                             command=self._show_cleanup_suggestions)
        clean_btn.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        # Recent activity section
        activity_section = ttk.Frame(dashboard)
        activity_section.pack(fill=tk.BOTH, expand=True, pady=10)
        activity_section.columnconfigure(0, weight=1)
        activity_section.columnconfigure(1, weight=1)
        activity_section.rowconfigure(0, weight=1)
        
        # Recent scans with modern styling
        scans_section = ttk.Frame(activity_section)
        scans_section.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nesw")
        
        ttk.Label(scans_section, text="Recent Scans", style="H3.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        scans_frame = ttk.Frame(scans_section, style="Card.TFrame")
        scans_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with modern styling
        self.scans_tree = ttk.Treeview(scans_frame, columns=("directory", "files", "date"), show="headings")
        self.scans_tree.heading("directory", text="Directory")
        self.scans_tree.heading("files", text="Files")
        self.scans_tree.heading("date", text="Date")
        self.scans_tree.column("directory", width=200)
        self.scans_tree.column("files", width=80)
        self.scans_tree.column("date", width=120)
        self.scans_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add a scrollbar
        scans_scrollbar = ttk.Scrollbar(scans_frame, orient=tk.VERTICAL, command=self.scans_tree.yview)
        self.scans_tree.configure(yscrollcommand=scans_scrollbar.set)
        scans_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Recent actions with modern styling
        actions_section = ttk.Frame(activity_section)
        actions_section.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="nesw")
        
        ttk.Label(actions_section, text="Recent Actions", style="H3.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        actions_frame = ttk.Frame(actions_section, style="Card.TFrame")
        actions_frame.pack(fill=tk.BOTH, expand=True)
        
        self.actions_tree = ttk.Treeview(actions_frame, columns=("action", "details", "date"), show="headings")
        self.actions_tree.heading("action", text="Action")
        self.actions_tree.heading("details", text="Details")
        self.actions_tree.heading("date", text="Date")
        self.actions_tree.column("action", width=100)
        self.actions_tree.column("details", width=200)
        self.actions_tree.column("date", width=120)
        self.actions_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add a scrollbar
        actions_scrollbar = ttk.Scrollbar(actions_frame, orient=tk.VERTICAL, command=self.actions_tree.yview)
        self.actions_tree.configure(yscrollcommand=actions_scrollbar.set)
        actions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status section
        status_section = ttk.Frame(dashboard, style="Card.TFrame")
        status_section.pack(fill=tk.X, pady=(20, 0))
        
        status_inner = ttk.Frame(status_section)
        status_inner.pack(padx=15, pady=15, fill=tk.BOTH)
        
        # System stats
        disk_usage = self._get_disk_usage()
        ttk.Label(status_inner, text=f"System Stats: {disk_usage['free_space']} free of {disk_usage['total_space']} ({disk_usage['percent_used']}% used)", 
                foreground=COLORS["text_secondary"]).pack(side=tk.LEFT)
        
        # Update dashboard data
        self._update_dashboard()
    
    def _setup_duplicates_tab(self):
        """Set up the duplicates tab."""
        # Top toolbar
        toolbar = ttk.Frame(self.duplicates_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="Find and manage duplicate files", style="H3.TLabel").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="Find Duplicates", command=self._find_duplicates).pack(side=tk.RIGHT, padx=5)
        
        # Duplicates list
        list_frame = ttk.LabelFrame(self.duplicates_frame, text="Duplicate Files")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a PanedWindow to resize the tree and details sections
        paned = ttk.PanedWindow(list_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tree section
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=3)
        
        self.dupes_tree = ttk.Treeview(tree_frame, columns=("group", "count", "size", "wasted"), show="tree headings")
        self.dupes_tree.heading("#0", text="File")
        self.dupes_tree.heading("group", text="Group")
        self.dupes_tree.heading("count", text="Count")
        self.dupes_tree.heading("size", text="Size")
        self.dupes_tree.heading("wasted", text="Wasted")
        self.dupes_tree.column("#0", width=400)
        self.dupes_tree.column("group", width=50)
        self.dupes_tree.column("count", width=50)
        self.dupes_tree.column("size", width=80)
        self.dupes_tree.column("wasted", width=80)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.dupes_tree.yview)
        self.dupes_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.dupes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.dupes_tree.bind("<<TreeviewSelect>>", self._on_dupe_select)
        
        # Details section
        details_frame = ttk.LabelFrame(paned, text="Details")
        paned.add(details_frame, weight=1)
        
        # File details
        self.dupe_details_text = tk.Text(details_frame, height=10, wrap=tk.WORD)
        details_scroll = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.dupe_details_text.yview)
        self.dupe_details_text.configure(yscrollcommand=details_scroll.set)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.dupe_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.dupe_details_text.configure(state=tk.DISABLED)
        
        # Actions panel
        actions_frame = ttk.Frame(self.duplicates_frame)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(actions_frame, text="Actions:").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(actions_frame, text="Delete Duplicates", command=lambda: self._resolve_duplicates("delete")).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Move to Duplicates Folder", command=lambda: self._resolve_duplicates("move")).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Create Symlinks", command=lambda: self._resolve_duplicates("symlink")).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Create Hardlinks", command=lambda: self._resolve_duplicates("hardlink")).pack(side=tk.LEFT, padx=5)
    
    def _setup_organization_tab(self):
        """Set up the organization tab."""
        # Top toolbar
        toolbar = ttk.Frame(self.organization_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="Organize and rename files", style="H3.TLabel").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="Organize Files", command=self._auto_organize).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Rename Files", command=self._rename_files).pack(side=tk.RIGHT, padx=5)
        
        # Create a notebook for organization options
        org_notebook = ttk.Notebook(self.organization_frame)
        org_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Organization suggestions tab
        suggestions_frame = ttk.Frame(org_notebook)
        org_notebook.add(suggestions_frame, text="Organization Suggestions")
        
        # Directory selection
        dir_frame = ttk.Frame(suggestions_frame)
        dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(dir_frame, text="Directory:").pack(side=tk.LEFT, padx=5)
        self.org_dir_entry = ttk.Entry(dir_frame, width=50)
        self.org_dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Browse", command=self._select_org_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(dir_frame, text="Analyze", command=self._analyze_org_directory).pack(side=tk.LEFT, padx=5)
        
        # Suggestions list
        suggestions_list_frame = ttk.LabelFrame(suggestions_frame, text="Suggestions")
        suggestions_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.suggestions_tree = ttk.Treeview(suggestions_list_frame, columns=("type", "count", "details"), show="headings")
        self.suggestions_tree.heading("type", text="Organization Type")
        self.suggestions_tree.heading("count", text="Files")
        self.suggestions_tree.heading("details", text="Details")
        self.suggestions_tree.column("type", width=150)
        self.suggestions_tree.column("count", width=50)
        self.suggestions_tree.column("details", width=400)
        
        suggestions_scroll = ttk.Scrollbar(suggestions_list_frame, orient=tk.VERTICAL, command=self.suggestions_tree.yview)
        self.suggestions_tree.configure(yscrollcommand=suggestions_scroll.set)
        suggestions_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.suggestions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Apply suggestions button
        ttk.Button(suggestions_frame, text="Apply Selected Suggestions", command=self._apply_org_suggestions).pack(pady=10)
        
        # Rename files tab
        rename_frame = ttk.Frame(org_notebook)
        org_notebook.add(rename_frame, text="Rename Files")
        
        # File selection
        file_frame = ttk.Frame(rename_frame)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(file_frame, text="Files:").pack(side=tk.LEFT, padx=5)
        self.rename_files_label = ttk.Label(file_frame, text="No files selected")
        self.rename_files_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Select Files", command=self._select_rename_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Generate Suggestions", command=self._generate_rename_suggestions).pack(side=tk.LEFT, padx=5)
        
        # Rename pattern
        pattern_frame = ttk.LabelFrame(rename_frame, text="Naming Pattern")
        pattern_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(pattern_frame, text="Format:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.naming_format_var = tk.StringVar(value=self.config.get("Organization", "naming_convention", "camel"))
        ttk.Radiobutton(pattern_frame, text="CamelCase", variable=self.naming_format_var, value="camel").grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(pattern_frame, text="snake_case", variable=self.naming_format_var, value="snake").grid(row=0, column=2, padx=5, pady=5)
        ttk.Radiobutton(pattern_frame, text="kebab-case", variable=self.naming_format_var, value="kebab").grid(row=0, column=3, padx=5, pady=5)
        ttk.Radiobutton(pattern_frame, text="Normal Case", variable=self.naming_format_var, value="normal").grid(row=0, column=4, padx=5, pady=5)
        
        ttk.Label(pattern_frame, text="Options:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.add_date_prefix_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(pattern_frame, text="Add date prefix", variable=self.add_date_prefix_var).grid(row=1, column=1, padx=5, pady=5)
        
        self.clean_spaces_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(pattern_frame, text="Clean spaces and special characters", variable=self.clean_spaces_var).grid(row=1, column=2, padx=5, pady=5, columnspan=2)
        
        # Rename preview list
        preview_frame = ttk.LabelFrame(rename_frame, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.rename_tree = ttk.Treeview(preview_frame, columns=("original", "new"), show="headings")
        self.rename_tree.heading("original", text="Original Name")
        self.rename_tree.heading("new", text="New Name")
        self.rename_tree.column("original", width=300)
        self.rename_tree.column("new", width=300)
        
        rename_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.rename_tree.yview)
        self.rename_tree.configure(yscrollcommand=rename_scroll.set)
        rename_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.rename_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Apply rename button
        ttk.Button(rename_frame, text="Apply Rename", command=self._apply_rename).pack(pady=10)
        
        # Rules tab
        rules_frame = ttk.Frame(org_notebook)
        org_notebook.add(rules_frame, text="Organization Rules")
        
        # Rules list
        rules_list_frame = ttk.LabelFrame(rules_frame, text="Custom Rules")
        rules_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.rules_tree = ttk.Treeview(rules_list_frame, columns=("type", "condition", "action"), show="headings")
        self.rules_tree.heading("type", text="Rule Type")
        self.rules_tree.heading("condition", text="Condition")
        self.rules_tree.heading("action", text="Action")
        self.rules_tree.column("type", width=100)
        self.rules_tree.column("condition", width=200)
        self.rules_tree.column("action", width=300)
        
        rules_scroll = ttk.Scrollbar(rules_list_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=rules_scroll.set)
        rules_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Rule actions
        rule_actions_frame = ttk.Frame(rules_frame)
        rule_actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(rule_actions_frame, text="Add Rule", command=self._add_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(rule_actions_frame, text="Edit Rule", command=self._edit_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(rule_actions_frame, text="Delete Rule", command=self._delete_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(rule_actions_frame, text="Import Rules", command=self._import_rules).pack(side=tk.LEFT, padx=5)
        ttk.Button(rule_actions_frame, text="Export Rules", command=self._export_rules).pack(side=tk.LEFT, padx=5)
    
    def _setup_statistics_tab(self):
        """Set up the statistics tab."""
        # Top toolbar
        toolbar = ttk.Frame(self.statistics_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="File Statistics", style="H3.TLabel").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="Refresh", command=self._refresh_statistics).pack(side=tk.RIGHT, padx=5)
        
        # Create a notebook for statistics views
        stats_notebook = ttk.Notebook(self.statistics_frame)
        stats_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # By category tab
        category_frame = ttk.Frame(stats_notebook)
        stats_notebook.add(category_frame, text="By Category")
        
        # Category pie chart (placeholder)
        category_chart_frame = ttk.LabelFrame(category_frame, text="File Distribution by Category")
        category_chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Simple pie chart using text for now
        self.category_chart = tk.Canvas(category_chart_frame, bg="white")
        self.category_chart.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Category list
        category_list_frame = ttk.LabelFrame(category_frame, text="Category Details")
        category_list_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.category_tree = ttk.Treeview(category_list_frame, columns=("count", "size", "percent"), show="headings")
        self.category_tree.heading("count", text="Files")
        self.category_tree.heading("size", text="Size")
        self.category_tree.heading("percent", text="Percent")
        self.category_tree.column("count", width=80)
        self.category_tree.column("size", width=100)
        self.category_tree.column("percent", width=80)
        
        category_scroll = ttk.Scrollbar(category_list_frame, orient=tk.VERTICAL, command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=category_scroll.set)
        category_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.category_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # By extension tab
        extension_frame = ttk.Frame(stats_notebook)
        stats_notebook.add(extension_frame, text="By Extension")
        
        # Extension list
        extension_list_frame = ttk.LabelFrame(extension_frame, text="Extensions")
        extension_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.extension_tree = ttk.Treeview(extension_list_frame, columns=("extension", "count", "category"), show="headings")
        self.extension_tree.heading("extension", text="Extension")
        self.extension_tree.heading("count", text="Files")
        self.extension_tree.heading("category", text="Category")
        self.extension_tree.column("extension", width=100)
        self.extension_tree.column("count", width=80)
        self.extension_tree.column("category", width=150)
        
        extension_scroll = ttk.Scrollbar(extension_list_frame, orient=tk.VERTICAL, command=self.extension_tree.yview)
        self.extension_tree.configure(yscrollcommand=extension_scroll.set)
        extension_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.extension_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # By size tab
        size_frame = ttk.Frame(stats_notebook)
        stats_notebook.add(size_frame, text="By Size")
        
        # Size distribution chart (placeholder)
        size_chart_frame = ttk.LabelFrame(size_frame, text="File Size Distribution")
        size_chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.size_chart = tk.Canvas(size_chart_frame, bg="white")
        self.size_chart.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Size groups list
        size_list_frame = ttk.LabelFrame(size_frame, text="Size Groups")
        size_list_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.size_tree = ttk.Treeview(size_list_frame, columns=("range", "count", "total_size", "percent"), show="headings")
        self.size_tree.heading("range", text="Size Range")
        self.size_tree.heading("count", text="Files")
        self.size_tree.heading("total_size", text="Total Size")
        self.size_tree.heading("percent", text="Percent")
        self.size_tree.column("range", width=150)
        self.size_tree.column("count", width=80)
        self.size_tree.column("total_size", width=100)
        self.size_tree.column("percent", width=80)
        
        size_scroll = ttk.Scrollbar(size_list_frame, orient=tk.VERTICAL, command=self.size_tree.yview)
        self.size_tree.configure(yscrollcommand=size_scroll.set)
        size_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.size_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # By date tab
        date_frame = ttk.Frame(stats_notebook)
        stats_notebook.add(date_frame, text="By Date")
        
        # Date distribution chart (placeholder)
        date_chart_frame = ttk.LabelFrame(date_frame, text="File Creation Date Distribution")
        date_chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.date_chart = tk.Canvas(date_chart_frame, bg="white")
        self.date_chart.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Date groups list
        date_list_frame = ttk.LabelFrame(date_frame, text="Date Groups")
        date_list_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.date_tree = ttk.Treeview(date_list_frame, columns=("period", "count", "size"), show="headings")
        self.date_tree.heading("period", text="Date Period")
        self.date_tree.heading("count", text="Files")
        self.date_tree.heading("size", text="Size")
        self.date_tree.column("period", width=150)
        self.date_tree.column("count", width=80)
        self.date_tree.column("size", width=100)
        
        date_scroll = ttk.Scrollbar(date_list_frame, orient=tk.VERTICAL, command=self.date_tree.yview)
        self.date_tree.configure(yscrollcommand=date_scroll.set)
        date_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.date_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def _setup_history_tab(self):
        """Set up the history tab."""
        # Top toolbar
        toolbar = ttk.Frame(self.history_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="Operation History", style="H3.TLabel").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="Refresh", command=self._refresh_history).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Clear History", command=self._clear_history).pack(side=tk.RIGHT, padx=5)
        
        # History list
        history_list_frame = ttk.Frame(self.history_frame)
        history_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.history_tree = ttk.Treeview(history_list_frame, columns=("timestamp", "action", "details"), show="headings")
        self.history_tree.heading("timestamp", text="Timestamp")
        self.history_tree.heading("action", text="Action")
        self.history_tree.heading("details", text="Details")
        self.history_tree.column("timestamp", width=150)
        self.history_tree.column("action", width=100)
        self.history_tree.column("details", width=400)
        
        history_scroll = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.history_tree.bind("<<TreeviewSelect>>", self._on_history_select)
        
        # Details section
        details_frame = ttk.LabelFrame(self.history_frame, text="Details")
        details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.history_details_text = tk.Text(details_frame, height=10, wrap=tk.WORD)
        details_scroll = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.history_details_text.yview)
        self.history_details_text.configure(yscrollcommand=details_scroll.set)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_details_text.configure(state=tk.DISABLED)
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, border=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        self.progress_bar = ttk.Progressbar(self.status_bar, mode='determinate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)
        self.progress_bar['value'] = 0
        
        version_label = ttk.Label(self.status_bar, text=f"v{VERSION}")
        version_label.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def _update_status(self, text, progress=None):
        """Update the status bar."""
        self.status_label.config(text=text)
        
        if progress is not None:
            self.progress_bar['value'] = int(progress * 100)
        else:
            self.progress_bar['value'] = 0
        
        self.root.update_idletasks()
    
    def _select_scan_directory(self):
        """Select a directory to scan."""
        directory = filedialog.askdirectory(title="Select Directory to Scan")
        if directory:
            self._scan_directory(directory)
    
    def _scan_directory(self, directory):
        """Scan a directory for files."""
        if not os.path.isdir(directory):
            messagebox.showerror("Error", f"Directory not found: {directory}")
            return
        
        self._update_status(f"Scanning {directory}...", 0)
        
        # Start the scan in a background thread
        self.scanner.start_scan(directory, callback=self._scan_callback)
    
    def _scan_callback(self, progress_data):
        """Callback for scan progress updates."""
        processed = progress_data.get('processed', 0)
        total = progress_data.get('total', 0)
        current = progress_data.get('current_file', '')
        progress_value = progress_data.get('progress', 0)
        
        if total > 0:
            self._update_status(f"Scanning {processed}/{total} files... ({int(progress_value * 100)}%)", progress_value)
        else:
            self._update_status(f"Scanning {processed} files...", 0)
        
        # Update dashboard when finished
        if not progress_data.get('scanning', True):
            self._update_status("Scan complete", 1.0)
            self._update_dashboard()
            self._refresh_statistics()
    
    def _scan_recent(self):
        """Scan a recently scanned directory."""
        # Get the selected item from the recent scans tree
        selected = self.scans_tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a directory from the recent scans list.")
            return
        
        # Get the directory from the selected item
        item = self.scans_tree.item(selected[0])
        directory = item['values'][0]
        
        # Scan the directory
        self._scan_directory(directory)
    
    @premium_feature("find_duplicates")
    def _find_duplicates(self):
        """Find duplicate files."""
        self._update_status("Finding duplicates...", 0)
        
        # Start the duplicate search in a background thread
        self.duplicate_finder.find_duplicates(callback=self._duplicates_callback)
    
    def _duplicates_callback(self, progress_data):
        """Callback for duplicate search progress updates."""
        processed = progress_data.get('processed', 0)
        total = progress_data.get('total', 0)
        progress_value = progress_data.get('progress', 0)
        duplicates_found = progress_data.get('duplicates_found', 0)
        
        if total > 0:
            self._update_status(f"Finding duplicates: {processed}/{total} files... {duplicates_found} duplicates found ({int(progress_value * 100)}%)", progress_value)
        else:
            self._update_status(f"Finding duplicates: {processed} files... {duplicates_found} duplicates found", 0)
        
        # Update UI when finished
        if not progress_data.get('processing', True):
            self._update_status("Duplicate search complete", 1.0)
            self._update_duplicates_tree()
            self._update_dashboard()
    
    def _update_duplicates_tree(self):
        """Update the duplicates tree view."""
        # Clear the tree
        for item in self.dupes_tree.get_children():
            self.dupes_tree.delete(item)
        
        # Get duplicates by size for better organization
        duplicates_by_size = self.duplicate_finder.get_duplicates_by_size()
        
        # Add duplicate groups to the tree
        size_groups = sorted(duplicates_by_size.keys(), reverse=True)
        
        for size in size_groups:
            groups = duplicates_by_size[size]
            size_node = self.dupes_tree.insert("", "end", text=f"Size: {self._format_size(size)}", 
                                              values=("", len(groups), self._format_size(size * sum(g['count'] for g in groups)), 
                                                      self._format_size(size * sum(g['count'] - 1 for g in groups))))
            
            for i, group in enumerate(groups):
                hash_value = group['hash']
                count = group['count']
                wasted = group['wasted_size']
                
                group_node = self.dupes_tree.insert(size_node, "end", text=f"Group {i+1}", 
                                                  values=(i+1, count, self._format_size(size), self._format_size(wasted)))
                
                for file_path in group['files']:
                    self.dupes_tree.insert(group_node, "end", text=file_path, values=("", "", "", ""))
        
        # Update the details text
        stats = self.duplicate_finder.get_total_duplicates_stats()
        
        self.dupe_details_text.configure(state=tk.NORMAL)
        self.dupe_details_text.delete(1.0, tk.END)
        self.dupe_details_text.insert(tk.END, "Duplicate Files Summary:\n\n")
        self.dupe_details_text.insert(tk.END, f"Duplicate Groups: {stats['duplicate_groups']}\n")
        self.dupe_details_text.insert(tk.END, f"Total Duplicates: {stats['total_duplicates']}\n")
        self.dupe_details_text.insert(tk.END, f"Total Size: {self._format_size(stats['total_size'])}\n")
        self.dupe_details_text.insert(tk.END, f"Wasted Space: {self._format_size(stats['wasted_size'])}\n")
        self.dupe_details_text.configure(state=tk.DISABLED)
    
    def _on_dupe_select(self, event):
        """Handle selection in the duplicates tree."""
        selected = self.dupes_tree.selection()
        if not selected:
            return
        
        item = self.dupes_tree.item(selected[0])
        text = item['text']
        values = item['values']
        
        # Update details text
        self.dupe_details_text.configure(state=tk.NORMAL)
        self.dupe_details_text.delete(1.0, tk.END)
        
        # Check if it's a file, group, or size node
        if values[0] == "" and values[1] == "" and values[2] == "":
            # It's a file
            file_path = text
            metadata = self.db.get_file(file_path)
            
            if metadata:
                self.dupe_details_text.insert(tk.END, f"File: {os.path.basename(file_path)}\n")
                self.dupe_details_text.insert(tk.END, f"Path: {os.path.dirname(file_path)}\n")
                self.dupe_details_text.insert(tk.END, f"Size: {self._format_size(metadata.get('size', 0))}\n")
                self.dupe_details_text.insert(tk.END, f"Created: {datetime.datetime.fromtimestamp(metadata.get('created', 0)).strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.dupe_details_text.insert(tk.END, f"Modified: {datetime.datetime.fromtimestamp(metadata.get('modified', 0)).strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.dupe_details_text.insert(tk.END, f"MIME Type: {metadata.get('mime_type', 'Unknown')}\n")
                self.dupe_details_text.insert(tk.END, f"Category: {metadata.get('category', 'Unknown')}\n")
                self.dupe_details_text.insert(tk.END, f"Hash: {metadata.get('hash', 'Unknown')}\n")
                
                # Add open and show in folder buttons
                self.dupe_details_text.insert(tk.END, "\n")
                
                # Insert buttons manually since Text widget doesn't directly support them
                self.dupe_details_text.insert(tk.END, "Actions: ")
                
                button_pos = self.dupe_details_text.index(tk.INSERT)
                open_button = ttk.Button(self.dupe_details_text, text="Open", command=lambda: self._open_file(file_path))
                self.dupe_details_text.window_create(button_pos, window=open_button)
                
                self.dupe_details_text.insert(tk.END, " ")
                
                button_pos = self.dupe_details_text.index(tk.INSERT)
                show_button = ttk.Button(self.dupe_details_text, text="Show in Folder", command=lambda: self._show_in_folder(file_path))
                self.dupe_details_text.window_create(button_pos, window=show_button)
            else:
                self.dupe_details_text.insert(tk.END, f"File: {file_path}\n")
                self.dupe_details_text.insert(tk.END, "No metadata available.\n")
        elif values[0] != "":
            # It's a group
            group_id = values[0]
            count = values[1]
            size = values[2]
            wasted = values[3]
            
            self.dupe_details_text.insert(tk.END, f"Duplicate Group {group_id}\n\n")
            self.dupe_details_text.insert(tk.END, f"Files: {count}\n")
            self.dupe_details_text.insert(tk.END, f"Size per file: {size}\n")
            self.dupe_details_text.insert(tk.END, f"Wasted space: {wasted}\n\n")
            
            # List all files in the group
            self.dupe_details_text.insert(tk.END, "Files in this group:\n")
            
            for child_id in self.dupes_tree.get_children(selected[0]):
                child = self.dupes_tree.item(child_id)
                file_path = child['text']
                self.dupe_details_text.insert(tk.END, f"- {file_path}\n")
        else:
            # It's a size node
            size_text = text.replace("Size: ", "")
            
            self.dupe_details_text.insert(tk.END, f"Files of size {size_text}\n\n")
            self.dupe_details_text.insert(tk.END, f"Duplicate groups: {values[1]}\n")
            self.dupe_details_text.insert(tk.END, f"Total size: {values[2]}\n")
            self.dupe_details_text.insert(tk.END, f"Wasted space: {values[3]}\n")
        
        self.dupe_details_text.configure(state=tk.DISABLED)
    
    def _resolve_duplicates(self, method):
        """Resolve duplicate files using the specified method."""
        # Get selected items
        selected = self.dupes_tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a duplicate group or file to resolve.")
            return
        
        # Confirm with user
        if not messagebox.askyesno("Confirm", f"Are you sure you want to {method} the selected duplicate files?"):
            return
        
        # Get files to resolve
        duplicates_to_resolve = {}
        files_to_resolve = []
        
        for item_id in selected:
            item = self.dupes_tree.item(item_id)
            text = item['text']
            values = item['values']
            
            # Check if it's a file, group, or size node
            if values[0] == "" and values[1] == "" and values[2] == "":
                # It's a file
                files_to_resolve.append(text)
            elif values[0] != "":
                # It's a group
                group_files = []
                for child_id in self.dupes_tree.get_children(item_id):
                    child = self.dupes_tree.item(child_id)
                    group_files.append(child['text'])
                
                # Keep the first file and resolve the rest
                if group_files:
                    hash_value = f"group_{item_id}"
                    duplicates_to_resolve[hash_value] = group_files
            else:
                # It's a size node, process all groups under it
                for group_id in self.dupes_tree.get_children(item_id):
                    group = self.dupes_tree.item(group_id)
                    group_files = []
                    
                    for child_id in self.dupes_tree.get_children(group_id):
                        child = self.dupes_tree.item(child_id)
                        group_files.append(child['text'])
                    
                    if group_files:
                        hash_value = f"group_{group_id}"
                        duplicates_to_resolve[hash_value] = group_files
        
        # If individual files were selected, find their groups
        if files_to_resolve:
            all_duplicates = self.duplicate_finder.get_duplicates()
            
            for hash_value, file_list in all_duplicates.items():
                for file_path in files_to_resolve:
                    if file_path in file_list:
                        # Add the entire group
                        if hash_value not in duplicates_to_resolve:
                            duplicates_to_resolve[hash_value] = file_list
        
        # Resolve duplicates
        if duplicates_to_resolve:
            self._update_status(f"Resolving duplicates using {method}...", 0)
            
            # Define the keep filter (keep the oldest file)
            def keep_filter(file_list):
                oldest_file = file_list[0]
                oldest_time = float('inf')
                
                for file_path in file_list:
                    metadata = self.db.get_file(file_path)
                    if metadata:
                        created_time = metadata.get("created", float('inf'))
                        if created_time < oldest_time:
                            oldest_time = created_time
                            oldest_file = file_path
                
                return oldest_file
            
            # Start the resolution process
            self.duplicate_finder.resolve_duplicates(method, duplicates_to_resolve, keep_filter, callback=self._resolution_callback)
    
    def _resolution_callback(self, progress_data):
        """Callback for duplicate resolution progress updates."""
        processed = progress_data.get('processed', 0)
        total = progress_data.get('total', 0)
        progress_value = progress_data.get('progress', 0)
        
        if total > 0:
            self._update_status(f"Resolving duplicates: {processed}/{total} groups... ({int(progress_value * 100)}%)", progress_value)
        else:
            self._update_status(f"Resolving duplicates: {processed} groups...", 0)
        
        # Update UI when finished
        if not progress_data.get('processing', True):
            self._update_status("Duplicate resolution complete", 1.0)
            self._find_duplicates()  # Refresh the duplicates list
            self._update_dashboard()
    
    @premium_feature("auto_organize")
    def _auto_organize(self):
        """Auto-organize files."""
        # Ask for directory
        directory = filedialog.askdirectory(title="Select Directory to Organize")
        if not directory:
            return
        
        # Confirm with user
        if not messagebox.askyesno("Confirm", f"Are you sure you want to auto-organize the files in {directory}?"):
            return
        
        self._update_status(f"Auto-organizing files in {directory}...", 0)
        
        # Start the organization process
        self.organizer.auto_organize(directory, callback=self._organization_callback)
    
    def _organization_callback(self, progress_data):
        """Callback for file organization progress updates."""
        processed = progress_data.get('processed', 0)
        total = progress_data.get('total', 0)
        progress_value = progress_data.get('progress', 0)
        moved_files = progress_data.get('moved_files', [])
        
        if total > 0:
            self._update_status(f"Organizing files: {processed}/{total} files... ({int(progress_value * 100)}%)", progress_value)
        else:
            self._update_status(f"Organizing files: {processed} files...", 0)
        
        # Update UI when finished
        if not progress_data.get('processing', True):
            self._update_status(f"Organization complete. Moved {len(moved_files)} files.", 1.0)
            
            # Show results
            if moved_files:
                result_dialog = tk.Toplevel(self.root)
                result_dialog.title("Organization Results")
                result_dialog.geometry("800x600")
                
                ttk.Label(result_dialog, text=f"Moved {len(moved_files)} files", style="H3.TLabel").pack(padx=10, pady=10)
                
                # Create a treeview to show the moved files
                tree = ttk.Treeview(result_dialog, columns=("original", "new"), show="headings")
                tree.heading("original", text="Original Location")
                tree.heading("new", text="New Location")
                tree.column("original", width=350)
                tree.column("new", width=350)
                
                for moved_file in moved_files:
                    tree.insert("", "end", values=(moved_file.get("original_path", ""), moved_file.get("new_path", "")))
                
                tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                ttk.Button(result_dialog, text="Close", command=result_dialog.destroy).pack(pady=10)
    
    @premium_feature("rename_files")
    def _rename_files(self):
        """Rename files based on patterns."""
        self._select_rename_files()
    
    def _select_rename_files(self):
        """Select files to rename."""
        files = filedialog.askopenfilenames(title="Select Files to Rename")
        if not files:
            return
        
        self.rename_files = list(files)
        self.rename_files_label.config(text=f"{len(files)} files selected")
        
        # Generate rename suggestions
        self._generate_rename_suggestions()
    
    def _generate_rename_suggestions(self):
        """Generate rename suggestions for selected files."""
        if not hasattr(self, 'rename_files') or not self.rename_files:
            messagebox.showinfo("No Files", "Please select files to rename first.")
            return
        
        # Clear the tree
        for item in self.rename_tree.get_children():
            self.rename_tree.delete(item)
        
        # Set naming convention from UI
        self.config.set("Organization", "naming_convention", self.naming_format_var.get())
        
        # Get rename suggestions
        suggestions = self.organizer.get_rename_suggestions(self.rename_files)
        
        # Add suggestions to the tree
        for suggestion in suggestions:
            self.rename_tree.insert("", "end", values=(suggestion["original_name"], suggestion["suggested_name"]))
        
        # If no suggestions were generated
        if not suggestions:
            messagebox.showinfo("No Suggestions", "No rename suggestions were generated for the selected files.")
    
    def _apply_rename(self):
        """Apply the rename suggestions."""
        if not hasattr(self, 'rename_files') or not self.rename_files:
            messagebox.showinfo("No Files", "Please select files to rename first.")
            return
        
        # Get the rename mapping from the tree
        rename_mapping = {}
        
        for item_id in self.rename_tree.get_children():
            values = self.rename_tree.item(item_id)['values']
            if len(values) >= 2:
                original_name = values[0]
                new_name = values[1]
                
                # Find the file path for this name
                for file_path in self.rename_files:
                    if os.path.basename(file_path) == original_name:
                        rename_mapping[file_path] = new_name
                        break
        
        if not rename_mapping:
            messagebox.showinfo("No Changes", "No files to rename.")
            return
        
        # Confirm with user
        if not messagebox.askyesno("Confirm", f"Are you sure you want to rename {len(rename_mapping)} files?"):
            return
        
        self._update_status(f"Renaming {len(rename_mapping)} files...", 0)
        
        # Start the rename process
        self.organizer.auto_rename(self.rename_files, rename_mapping, callback=self._rename_callback)
    
    def _rename_callback(self, progress_data):
        """Callback for file rename progress updates."""
        processed = progress_data.get('processed', 0)
        total = progress_data.get('total', 0)
        progress_value = progress_data.get('progress', 0)
        
        if total > 0:
            self._update_status(f"Renaming files: {processed}/{total} files... ({int(progress_value * 100)}%)", progress_value)
        else:
            self._update_status(f"Renaming files: {processed} files...", 0)
        
        # Update UI when finished
        if not progress_data.get('processing', True):
            self._update_status("Rename complete", 1.0)
            
            # Clear the rename list
            self.rename_files = []
            self.rename_files_label.config(text="No files selected")
            
            # Clear the tree
            for item in self.rename_tree.get_children():
                self.rename_tree.delete(item)
    
    def _select_org_directory(self):
        """Select a directory for organization suggestions."""
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            self.org_dir_entry.delete(0, tk.END)
            self.org_dir_entry.insert(0, directory)
    
    def _analyze_org_directory(self):
        """Analyze a directory for organization suggestions."""
        directory = self.org_dir_entry.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Error", "Please select a valid directory.")
            return
        
        self._update_status(f"Analyzing {directory} for organization suggestions...", 0)
        
        # Start the analysis process
        self.organizer.suggest_organization(directory, callback=self._suggestion_callback)
    
    def _suggestion_callback(self, progress_data):
        """Callback for organization suggestion progress updates."""
        processed = progress_data.get('processed', 0)
        total = progress_data.get('total', 0)
        progress_value = progress_data.get('progress', 0)
        suggestions = progress_data.get('suggestions', {})
        
        if total > 0:
            self._update_status(f"Analyzing files: {processed}/{total} files... ({int(progress_value * 100)}%)", progress_value)
        else:
            self._update_status(f"Analyzing files: {processed} files...", 0)
        
        # Update UI when finished
        if not progress_data.get('processing', True):
            self._update_status("Analysis complete", 1.0)
            
            # Update the suggestions tree
            self._update_suggestions_tree(suggestions)
    
    def _update_suggestions_tree(self, suggestions):
        """Update the organization suggestions tree."""
        # Clear the tree
        for item in self.suggestions_tree.get_children():
            self.suggestions_tree.delete(item)
        
        # Add category suggestions
        if 'by_category' in suggestions:
            category_node = self.suggestions_tree.insert("", "end", text="By Category", 
                                                      values=("Category", sum(suggestions['by_category'].values()), 
                                                              f"Organize by file category like Images, Documents, etc."))
            
            for category, count in sorted(suggestions['by_category'].items(), key=lambda x: x[1], reverse=True):
                self.suggestions_tree.insert(category_node, "end", text=category, 
                                           values=(category, count, f"Create a folder for {category}"))
        
        # Add extension suggestions
        if 'by_extension' in suggestions:
            extension_node = self.suggestions_tree.insert("", "end", text="By Extension", 
                                                       values=("Extension", sum(suggestions['by_extension'].values()), 
                                                               "Organize by file extension"))
            
            for ext, count in sorted(suggestions['by_extension'].items(), key=lambda x: x[1], reverse=True):
                if ext:  # Skip empty extension
                    self.suggestions_tree.insert(extension_node, "end", text=ext, 
                                               values=(ext, count, f"Create a folder for {ext} files"))
        
        # Add date suggestions
        if 'by_date' in suggestions:
            date_node = self.suggestions_tree.insert("", "end", text="By Date", 
                                                  values=("Date", sum(suggestions['by_date'].values()), 
                                                          "Organize by creation date"))
            
            for date, count in sorted(suggestions['by_date'].items()):
                self.suggestions_tree.insert(date_node, "end", text=date, 
                                           values=(date, count, f"Create a folder for {date}"))
        
        # Add name pattern suggestions
        if 'by_name_pattern' in suggestions:
            pattern_node = self.suggestions_tree.insert("", "end", text="By Name Pattern", 
                                                     values=("Pattern", sum(suggestions['by_name_pattern'].values()), 
                                                             "Organize by filename patterns"))
            
            for pattern, count in sorted(suggestions['by_name_pattern'].items(), key=lambda x: x[1], reverse=True):
                if pattern:  # Skip empty pattern
                    self.suggestions_tree.insert(pattern_node, "end", text=pattern, 
                                               values=(pattern, count, f"Group files with pattern: {pattern}"))
    
    def _apply_org_suggestions(self):
        """Apply the selected organization suggestions."""
        # Get the selected suggestion
        selected = self.suggestions_tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select an organization suggestion to apply.")
            return
        
        # Get the suggestion type
        item = self.suggestions_tree.item(selected[0])
        parent_id = self.suggestions_tree.parent(selected[0])
        
        if not parent_id:  # It's a top-level node
            suggestion_type = item['text']
        else:
            parent_item = self.suggestions_tree.item(parent_id)
            suggestion_type = parent_item['text']
        
        # Get the directory
        directory = self.org_dir_entry.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Error", "Please select a valid directory.")
            return
        
        # Create rules based on the suggestion type
        rules = []
        
        if suggestion_type == "By Category":
            # If a specific category is selected
            if parent_id:
                category = item['values'][0]
                rules.append({
                    "type": "category",
                    "category": category,
                    "destination": category
                })
            else:
                # General category organization
                rules.append({
                    "type": "category",
                    "destination": "{category}"
                })
        
        elif suggestion_type == "By Extension":
            # If a specific extension is selected
            if parent_id:
                extension = item['values'][0]
                rules.append({
                    "type": "extension",
                    "extension": extension,
                    "destination": extension[1:]  # Remove the dot
                })
            else:
                # General extension organization
                rules.append({
                    "type": "extension",
                    "destination": "{extension}"
                })
        
        elif suggestion_type == "By Date":
            # If a specific date period is selected
            if parent_id:
                date_period = item['values'][0]
                rules.append({
                    "type": "date",
                    "destination": date_period
                })
            else:
                # General date organization
                rules.append({
                    "type": "date",
                    "destination": "{year}/{month}"
                })
        
        # Apply the rules
        if rules:
            # Confirm with user
            if not messagebox.askyesno("Confirm", f"Are you sure you want to apply the selected organization to {directory}?"):
                return
            
            self._update_status(f"Applying organization to {directory}...", 0)
            
            # Start the organization process
            self.organizer.auto_organize(directory, rules, callback=self._organization_callback)
    
    def _add_rule(self):
        """Add a custom organization rule."""
        # Create a dialog for rule creation
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Organization Rule")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Rule Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        rule_type_var = tk.StringVar(value="category")
        rule_type_combo = ttk.Combobox(dialog, textvariable=rule_type_var, state="readonly")
        rule_type_combo['values'] = ("category", "extension", "date")
        rule_type_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Condition frame (will change based on rule type)
        condition_frame = ttk.LabelFrame(dialog, text="Condition")
        condition_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        
        # Variable to store condition widgets for later access
        condition_widgets = {}
        
        # Action frame
        action_frame = ttk.LabelFrame(dialog, text="Action")
        action_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        
        ttk.Label(action_frame, text="Destination:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        destination_entry = ttk.Entry(action_frame, width=40)
        destination_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Help text
        ttk.Label(action_frame, text="Use {category}, {extension}, {year}, {month}, etc. as placeholders").grid(
            row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Function to update condition frame based on rule type
        def update_condition_frame(*args):
            # Clear the frame
            for widget in condition_frame.winfo_children():
                widget.destroy()
            
            # Clear stored widgets
            condition_widgets.clear()
            
            rule_type = rule_type_var.get()
            
            if rule_type == "category":
                ttk.Label(condition_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                
                category_var = tk.StringVar()
                category_combo = ttk.Combobox(condition_frame, textvariable=category_var)
                category_combo['values'] = list(FILE_CATEGORIES.keys())
                category_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
                
                condition_widgets['category'] = category_var
                
                # Update destination suggestion
                destination_entry.delete(0, tk.END)
                destination_entry.insert(0, "{category}")
            
            elif rule_type == "extension":
                ttk.Label(condition_frame, text="Extension:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                
                extension_var = tk.StringVar()
                extension_entry = ttk.Entry(condition_frame, textvariable=extension_var)
                extension_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
                
                condition_widgets['extension'] = extension_var
                
                # Update destination suggestion
                destination_entry.delete(0, tk.END)
                destination_entry.insert(0, "{extension}")
            
            elif rule_type == "date":
                # No specific condition for date rules
                ttk.Label(condition_frame, text="Applies to all files with creation date").grid(
                    row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
                
                # Update destination suggestion
                destination_entry.delete(0, tk.END)
                destination_entry.insert(0, "{year}/{month}")
        
        # Bind rule type change
        rule_type_var.trace("w", update_condition_frame)
        
        # Initialize the condition frame
        update_condition_frame()
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Add Rule", command=lambda: self._add_rule_callback(
            rule_type_var.get(), condition_widgets, destination_entry.get(), dialog)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _add_rule_callback(self, rule_type, condition_widgets, destination, dialog):
        """Callback for adding a rule."""
        # Create the rule
        rule = {
            "type": rule_type,
            "destination": destination
        }
        
        # Add condition based on rule type
        if rule_type == "category" and 'category' in condition_widgets:
            category = condition_widgets['category'].get()
            if category:
                rule["category"] = category
        
        elif rule_type == "extension" and 'extension' in condition_widgets:
            extension = condition_widgets['extension'].get()
            if extension:
                # Add dot if not present
                if not extension.startswith('.'):
                    extension = '.' + extension
                rule["extension"] = extension
        
        # Add to the tree
        self.rules_tree.insert("", "end", values=(rule_type, self._format_rule_condition(rule), destination))
        
        # Close the dialog
        dialog.destroy()
    
    def _format_rule_condition(self, rule):
        """Format a rule condition for display."""
        rule_type = rule.get("type", "")
        
        if rule_type == "category":
            category = rule.get("category", "Any")
            return f"Category = {category}"
        
        elif rule_type == "extension":
            extension = rule.get("extension", "Any")
            return f"Extension = {extension}"
        
        elif rule_type == "date":
            return "All files with creation date"
        
        return ""
    
    def _edit_rule(self):
        """Edit a selected organization rule."""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a rule to edit.")
            return
        
        # Get the rule data
        item = self.rules_tree.item(selected[0])
        values = item['values']
        
        if len(values) < 3:
            return
        
        rule_type = values[0]
        condition = values[1]
        destination = values[2]
        
        # Extract condition data
        if rule_type == "category":
            category = condition.replace("Category = ", "")
        elif rule_type == "extension":
            extension = condition.replace("Extension = ", "")
        
        # Create a dialog for rule editing (similar to _add_rule)
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Organization Rule")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Rule Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        rule_type_var = tk.StringVar(value=rule_type)
        rule_type_combo = ttk.Combobox(dialog, textvariable=rule_type_var, state="readonly")
        rule_type_combo['values'] = ("category", "extension", "date")
        rule_type_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Condition frame
        condition_frame = ttk.LabelFrame(dialog, text="Condition")
        condition_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        
        # Variable to store condition widgets
        condition_widgets = {}
        
        # Action frame
        action_frame = ttk.LabelFrame(dialog, text="Action")
        action_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        
        ttk.Label(action_frame, text="Destination:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        destination_entry = ttk.Entry(action_frame, width=40)
        destination_entry.insert(0, destination)
        destination_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Help text
        ttk.Label(action_frame, text="Use {category}, {extension}, {year}, {month}, etc. as placeholders").grid(
            row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Function to update condition frame based on rule type
        def update_condition_frame(*args):
            # Clear the frame
            for widget in condition_frame.winfo_children():
                widget.destroy()
            
            # Clear stored widgets
            condition_widgets.clear()
            
            current_rule_type = rule_type_var.get()
            
            if current_rule_type == "category":
                ttk.Label(condition_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                
                category_var = tk.StringVar()
                if rule_type == "category":  # If originally a category rule
                    category_var.set(category)
                
                category_combo = ttk.Combobox(condition_frame, textvariable=category_var)
                category_combo['values'] = list(FILE_CATEGORIES.keys())
                category_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
                
                condition_widgets['category'] = category_var
            
            elif current_rule_type == "extension":
                ttk.Label(condition_frame, text="Extension:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                
                extension_var = tk.StringVar()
                if rule_type == "extension":  # If originally an extension rule
                    extension_var.set(extension)
                
                extension_entry = ttk.Entry(condition_frame, textvariable=extension_var)
                extension_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
                
                condition_widgets['extension'] = extension_var
            
            elif current_rule_type == "date":
                # No specific condition for date rules
                ttk.Label(condition_frame, text="Applies to all files with creation date").grid(
                    row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Bind rule type change
        rule_type_var.trace("w", update_condition_frame)
        
        # Initialize the condition frame
        update_condition_frame()
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Save", command=lambda: self._edit_rule_callback(
            selected[0], rule_type_var.get(), condition_widgets, destination_entry.get(), dialog)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _edit_rule_callback(self, item_id, rule_type, condition_widgets, destination, dialog):
        """Callback for editing a rule."""
        # Create the updated rule
        condition = ""
        
        if rule_type == "category" and 'category' in condition_widgets:
            category = condition_widgets['category'].get()
            if category:
                condition = f"Category = {category}"
        
        elif rule_type == "extension" and 'extension' in condition_widgets:
            extension = condition_widgets['extension'].get()
            if extension:
                condition = f"Extension = {extension}"
        
        elif rule_type == "date":
            condition = "All files with creation date"
        
        # Update the tree
        self.rules_tree.item(item_id, values=(rule_type, condition, destination))
        
        # Close the dialog
        dialog.destroy()
    
    def _delete_rule(self):
        """Delete a selected organization rule."""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a rule to delete.")
            return
        
        # Confirm with user
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete the selected rule?"):
            return
        
        # Delete the rule
        for item_id in selected:
            self.rules_tree.delete(item_id)
    
    def _import_rules(self):
        """Import organization rules from a file."""
        file_path = filedialog.askopenfilename(
            title="Import Rules",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                rules = json.load(f)
            
            # Validate rules
            if not isinstance(rules, list):
                raise ValueError("Rules should be a list")
            
            # Clear existing rules
            for item in self.rules_tree.get_children():
                self.rules_tree.delete(item)
            
            # Add imported rules
            for rule in rules:
                if not isinstance(rule, dict) or 'type' not in rule or 'destination' not in rule:
                    continue
                
                rule_type = rule.get('type', '')
                destination = rule.get('destination', '')
                
                # Format condition
                condition = self._format_rule_condition(rule)
                
                # Add to tree
                self.rules_tree.insert("", "end", values=(rule_type, condition, destination))
            
            messagebox.showinfo("Success", f"Imported {len(rules)} rules.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import rules: {e}")
    
    def _export_rules(self):
        """Export organization rules to a file."""
        # Get all rules from the tree
        rules = []
        
        for item_id in self.rules_tree.get_children():
            values = self.rules_tree.item(item_id)['values']
            if len(values) < 3:
                continue
            
            rule_type = values[0]
            condition = values[1]
            destination = values[2]
            
            rule = {
                "type": rule_type,
                "destination": destination
            }
            
            # Parse condition
            if rule_type == "category" and condition.startswith("Category = "):
                rule["category"] = condition.replace("Category = ", "")
            
            elif rule_type == "extension" and condition.startswith("Extension = "):
                extension = condition.replace("Extension = ", "")
                
                # Add dot if not present
                if not extension.startswith('.'):
                    extension = '.' + extension
                
                rule["extension"] = extension
            
            rules.append(rule)
        
        if not rules:
            messagebox.showinfo("No Rules", "There are no rules to export.")
            return
        
        # Ask for file path
        file_path = filedialog.asksaveasfilename(
            title="Export Rules",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w') as f:
                json.dump(rules, f, indent=2)
            
            messagebox.showinfo("Success", f"Exported {len(rules)} rules to {file_path}.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export rules: {e}")
    
    @premium_feature("show_cleanup_suggestions")
    def _show_cleanup_suggestions(self):
        """Show cleanup suggestions."""
        # Create a dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Cleanup Suggestions")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="Cleanup Suggestions", style="H2.TLabel").pack(padx=10, pady=10)
        
        # Create a notebook
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Duplicates tab
        dupes_frame = ttk.Frame(notebook)
        notebook.add(dupes_frame, text="Duplicates")
        
        # Get duplicate stats
        stats = self.duplicate_finder.get_total_duplicates_stats()
        
        dupes_stats = ttk.Frame(dupes_frame)
        dupes_stats.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(dupes_stats, text=f"Duplicate Groups: {stats.get('duplicate_groups', 0)}").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(dupes_stats, text=f"Total Duplicates: {stats.get('total_duplicates', 0)}").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(dupes_stats, text=f"Wasted Space: {self._format_size(stats.get('wasted_size', 0))}").pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Button(dupes_frame, text="Find Duplicates", command=lambda: [self._find_duplicates(), dialog.destroy()]).pack(pady=10)
        
        # Empty files tab
        empty_frame = ttk.Frame(notebook)
        notebook.add(empty_frame, text="Empty Files")
        
        # Count empty files and folders
        empty_files = []
        empty_folders = []
        
        for file_path, metadata in self.db.get_all_files().items():
            if metadata.get('size', 0) == 0:
                empty_files.append(file_path)
        
        ttk.Label(empty_frame, text=f"Empty Files: {len(empty_files)}").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(empty_frame, text=f"Empty Folders: {len(empty_folders)}").pack(anchor=tk.W, padx=5, pady=2)
        
        # Show list of empty files
        if empty_files:
            list_frame = ttk.LabelFrame(empty_frame, text="Empty Files")
            list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            tree = ttk.Treeview(list_frame, columns=("path",), show="headings")
            tree.heading("path", text="File Path")
            tree.column("path", width=500)
            
            for file_path in empty_files:
                tree.insert("", "end", values=(file_path,))
            
            tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=tree_scroll.set)
            tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            ttk.Button(empty_frame, text="Delete Empty Files", command=lambda: self._delete_empty_files(empty_files, dialog)).pack(pady=10)
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def _delete_empty_files(self, file_list, dialog):
        """Delete empty files."""
        if not file_list:
            return
        
        # Confirm with user
        if not messagebox.askyesno("Confirm", f"Are you sure you want to delete {len(file_list)} empty files?"):
            return
        
        # Delete files
        deleted = 0
        
        for file_path in file_list:
            try:
                if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
                    os.remove(file_path)
                    self.db.remove_file(file_path)
                    deleted += 1
                    
                    # Add to history
                    self.db.add_history_entry("delete_empty", {
                        "file_path": file_path
                    })
            except Exception as e:
                logger.error(f"Error deleting empty file {file_path}: {e}")
        
        # Save database
        self.db.save()
        
        messagebox.showinfo("Success", f"Deleted {deleted} empty files.")
        dialog.destroy()
    
    @premium_feature("import_database")
    def _import_database(self):
        """Import database from a file."""
        file_path = filedialog.askopenfilename(
            title="Import Database",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Confirm with user
        if not messagebox.askyesno("Confirm", "Importing a database will overwrite your current database. Continue?"):
            return
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate basic structure
            if not isinstance(data, dict) or 'metadata' not in data or 'files' not in data:
                raise ValueError("Invalid database format")
            
            # Set the data
            self.db.data = data
            self.db.save()
            
            messagebox.showinfo("Success", "Database imported successfully.")
            
            # Update UI
            self._update_dashboard()
            self._refresh_statistics()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import database: {e}")
    
    @premium_feature("export_database")
    def _export_database(self):
        """Export database to a file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Database",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self.db.data, f, indent=2)
            
            messagebox.showinfo("Success", "Database exported successfully.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export database: {e}")
    
    @premium_feature("clear_database")
    def _clear_database(self):
        """Clear the database."""
        # Confirm with user
        if not messagebox.askyesno("Confirm", "Are you sure you want to clear the database? This cannot be undone."):
            return
        
        # Clear the database
        self.db.clear()
        
        messagebox.showinfo("Success", "Database cleared successfully.")
        
        # Update UI
        self._update_dashboard()
        self._refresh_statistics()
    
    def _refresh_statistics(self):
        """Refresh the statistics tab."""
        # Clear trees
        for tree in [self.category_tree, self.extension_tree, self.size_tree, self.date_tree]:
            for item in tree.get_children():
                tree.delete(item)
        
        # Get stats
        stats = self.db.get_stats()
        
        # Category stats
        by_category = stats.get('by_category', {})
        total_size = stats.get('total_size', 0)
        
        for category, data in sorted(by_category.items(), key=lambda x: x[1].get('size', 0), reverse=True):
            count = data.get('count', 0)
            size = data.get('size', 0)
            percent = (size / total_size * 100) if total_size > 0 else 0
            
            self.category_tree.insert("", "end", text=category, 
                                     values=(count, self._format_size(size), f"{percent:.1f}%"))
        
        # Extension stats
        extensions = self.db.get_patterns('extensions')
        
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
            category = "Unknown"
            
            for cat, exts in FILE_CATEGORIES.items():
                if ext in exts:
                    category = cat
                    break
            
            self.extension_tree.insert("", "end", text=ext, values=(ext, count, category))
        
        # Size distribution
        size_ranges = {
            "< 10 KB": (0, 10 * 1024),
            "10 KB - 100 KB": (10 * 1024, 100 * 1024),
            "100 KB - 1 MB": (100 * 1024, 1024 * 1024),
            "1 MB - 10 MB": (1024 * 1024, 10 * 1024 * 1024),
            "10 MB - 100 MB": (10 * 1024 * 1024, 100 * 1024 * 1024),
            "100 MB - 1 GB": (100 * 1024 * 1024, 1024 * 1024 * 1024),
            "> 1 GB": (1024 * 1024 * 1024, float('inf'))
        }
        
        size_counts = {range_name: {'count': 0, 'size': 0} for range_name in size_ranges}
        
        for file_path, metadata in self.db.get_all_files().items():
            size = metadata.get('size', 0)
            
            for range_name, (min_size, max_size) in size_ranges.items():
                if min_size <= size < max_size:
                    size_counts[range_name]['count'] += 1
                    size_counts[range_name]['size'] += size
                    break
        
        for range_name, data in size_counts.items():
            count = data['count']
            total_size = data['size']
            percent = (total_size / stats.get('total_size', 1) * 100) if stats.get('total_size', 0) > 0 else 0
            
            self.size_tree.insert("", "end", text=range_name, 
                                 values=(range_name, count, self._format_size(total_size), f"{percent:.1f}%"))
        
        # Date distribution
        date_ranges = {}
        
        for file_path, metadata in self.db.get_all_files().items():
            created = metadata.get('created')
            if not created:
                continue
            
            date = datetime.datetime.fromtimestamp(created)
            year_month = date.strftime("%Y-%m")
            
            if year_month not in date_ranges:
                date_ranges[year_month] = {'count': 0, 'size': 0}
            
            date_ranges[year_month]['count'] += 1
            date_ranges[year_month]['size'] += metadata.get('size', 0)
        
        for year_month, data in sorted(date_ranges.items(), reverse=True):
            count = data['count']
            total_size = data['size']
            
            self.date_tree.insert("", "end", text=year_month, 
                                 values=(year_month, count, self._format_size(total_size)))
        
        # Draw charts
        self._draw_category_chart(by_category, total_size)
        self._draw_size_chart(size_counts, total_size)
        self._draw_date_chart(date_ranges)
    
    def _draw_category_chart(self, by_category, total_size):
        """Draw a pie chart for file categories."""
        # Clear canvas
        self.category_chart.delete("all")
        
        # Sort categories by size
        sorted_categories = sorted(by_category.items(), key=lambda x: x[1].get('size', 0), reverse=True)
        
        # Get top 5 categories plus "Others"
        top_categories = sorted_categories[:5]
        other_categories = sorted_categories[5:]
        
        # Calculate "Others" total
        other_size = 0
        for _, data in other_categories:
            other_size += data.get('size', 0)
        
        if other_size > 0:
            chart_data = top_categories + [("Others", {"size": other_size, "count": sum(data.get('count', 0) for _, data in other_categories)})]
        else:
            chart_data = top_categories
        
        # Draw the pie chart
        width = self.category_chart.winfo_width()
        height = self.category_chart.winfo_height()
        
        # If the canvas size is not yet available, use default values
        if width < 10:
            width = 400
        if height < 10:
            height = 300
        
        # Center and radius
        center_x = width // 2
        center_y = height // 2
        radius = min(center_x, center_y) - 20
        
        # Colors for the chart
        colors = [
            "#2D7DD2",  # Blue
            "#97CC04",  # Green
            "#F45D01",  # Orange
            "#6C464F",  # Purple
            "#FFC857",  # Yellow
            "#6C757D"   # Gray (for Others)
        ]
        
        # Draw the pie slices
        start_angle = 0
        legend_y = 20
        
        for i, (category, data) in enumerate(chart_data):
            size = data.get('size', 0)
            if total_size > 0:
                angle = size / total_size * 360
            else:
                angle = 0
            
            # Draw the slice
            color = colors[i % len(colors)]
            end_angle = start_angle + angle
            
            if angle > 0:  # Only draw if the slice has size
                self.category_chart.create_arc(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    start=start_angle, extent=angle,
                    fill=color, outline="white"
                )
            
            start_angle = end_angle
            
            # Draw the legend
            self.category_chart.create_rectangle(20, legend_y, 40, legend_y + 15, fill=color, outline="")
            
            percent = (size / total_size * 100) if total_size > 0 else 0
            legend_text = f"{category}: {self._format_size(size)} ({percent:.1f}%)"
            
            self.category_chart.create_text(45, legend_y + 7, text=legend_text, anchor=tk.W)
            
            legend_y += 25
    
    def _draw_size_chart(self, size_counts, total_size):
        """Draw a chart for file size distribution."""
        # Clear canvas
        self.size_chart.delete("all")
        
        # Draw a bar chart
        width = self.size_chart.winfo_width()
        height = self.size_chart.winfo_height()
        
        # If the canvas size is not yet available, use default values
        if width < 10:
            width = 400
        if height < 10:
            height = 300
        
        # Calculate bar widths and positions
        margin = 50
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        # Get the data
        ranges = list(size_counts.keys())
        counts = [data['count'] for data in size_counts.values()]
        
        # Skip empty ranges
        non_empty = [(r, c) for r, c in zip(ranges, counts) if c > 0]
        if not non_empty:
            return
        
        ranges, counts = zip(*non_empty)
        
        # Calculate bar width
        bar_width = chart_width / len(ranges)
        max_count = max(counts)
        
        # Draw the bars
        for i, (range_name, count) in enumerate(zip(ranges, counts)):
            # Calculate bar height and position
            bar_height = (count / max_count) * chart_height if max_count > 0 else 0
            bar_x = margin + i * bar_width
            bar_y = height - margin - bar_height
            
            # Draw the bar
            self.size_chart.create_rectangle(
                bar_x, bar_y,
                bar_x + bar_width - 5, height - margin,
                fill=COLORS["primary"], outline=""
            )
            
            # Draw the label (rotated for better fit)
            label_x = bar_x + bar_width / 2
            label_y = height - margin + 5
            
            self.size_chart.create_text(
                label_x, label_y,
                text=range_name,
                anchor=tk.N,
                angle=45
            )
            
            # Draw the count
            self.size_chart.create_text(
                label_x, bar_y - 5,
                text=str(count),
                anchor=tk.S
            )
        
        # Draw axes
        self.size_chart.create_line(
            margin, height - margin,
            width - margin, height - margin,
            width=2
        )
        
        self.size_chart.create_line(
            margin, height - margin,
            margin, margin,
            width=2
        )
        
        # Title
        self.size_chart.create_text(
            width / 2, 20,
            text="File Count by Size Range",
            font=("Arial", 12, "bold")
        )
    
    def _draw_date_chart(self, date_ranges):
        """Draw a chart for file date distribution."""
        # Clear canvas
        self.date_chart.delete("all")
        
        # Draw a line chart
        width = self.date_chart.winfo_width()
        height = self.date_chart.winfo_height()
        
        # If the canvas size is not yet available, use default values
        if width < 10:
            width = 400
        if height < 10:
            height = 300
        
        # Calculate chart dimensions
        margin = 50
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        # Get the data, sorted by date
        dates = sorted(date_ranges.keys())
        counts = [date_ranges[date]['count'] for date in dates]
        
        if not dates:
            return
        
        # Calculate max count for scaling
        max_count = max(counts) if counts else 0
        
        # Calculate point positions
        points = []
        for i, (date, count) in enumerate(zip(dates, counts)):
            x = margin + (i / (len(dates) - 1 if len(dates) > 1 else 1)) * chart_width
            y = height - margin - (count / max_count) * chart_height if max_count > 0 else height - margin
            points.append((x, y))
        
        # Draw the line
        if len(points) > 1:
            self.date_chart.create_line(points, fill=COLORS["primary"], width=2, smooth=True)
        
        # Draw points
        for x, y in points:
            self.date_chart.create_oval(x - 4, y - 4, x + 4, y + 4, fill=COLORS["primary"], outline="")
        
        # Draw axis labels
        # X-axis (dates)
        label_count = min(len(dates), 6)  # Limit to 6 labels to avoid crowding
        step = max(1, len(dates) // label_count)
        
        for i in range(0, len(dates), step):
            date = dates[i]
            x = margin + (i / (len(dates) - 1 if len(dates) > 1 else 1)) * chart_width
            
            # Draw tick
            self.date_chart.create_line(x, height - margin, x, height - margin + 5, width=1)
            
            # Draw label
            self.date_chart.create_text(
                x, height - margin + 15,
                text=date,
                anchor=tk.N,
                angle=45
            )
        
        # Y-axis (counts)
        for i in range(5):
            count = max_count * i / 4
            y = height - margin - (i / 4) * chart_height
            
            # Draw tick
            self.date_chart.create_line(margin - 5, y, margin, y, width=1)
            
            # Draw label
            self.date_chart.create_text(
                margin - 10, y,
                text=str(int(count)),
                anchor=tk.E
            )
        
        # Draw axes
        self.date_chart.create_line(
            margin, height - margin,
            width - margin, height - margin,
            width=2
        )
        
        self.date_chart.create_line(
            margin, height - margin,
            margin, margin,
            width=2
        )
        
        # Title
        self.date_chart.create_text(
            width / 2, 20,
            text="File Count by Date",
            font=("Arial", 12, "bold")
        )
    
    def _refresh_history(self):
        """Refresh the history tab."""
        # Clear the tree
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Get history entries
        history = self.db.get_history(limit=100)
        
        # Add entries to the tree
        for entry in history:
            timestamp = entry.get('timestamp', '')
            action = entry.get('action', '')
            details = entry.get('details', {})
            
            # Format details for display
            if 'file_path' in details:
                detail_text = details['file_path']
            elif 'original_path' in details and 'new_path' in details:
                detail_text = f"{details['original_path']} -> {details['new_path']}"
            else:
                detail_text = str(details)
            
            # Format timestamp
            timestamp_dt = datetime.datetime.fromisoformat(timestamp) if timestamp else datetime.datetime.now()
            formatted_timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            self.history_tree.insert("", "end", text=formatted_timestamp, values=(formatted_timestamp, action, detail_text))
    
    def _on_history_select(self, event):
        """Handle selection in the history tree."""
        selected = self.history_tree.selection()
        if not selected:
            return
        
        item = self.history_tree.item(selected[0])
        values = item['values']
        
        if len(values) < 3:
            return
        
        timestamp = values[0]
        action = values[1]
        details = values[2]
        
        # Display details
        self.history_details_text.configure(state=tk.NORMAL)
        self.history_details_text.delete(1.0, tk.END)
        
        self.history_details_text.insert(tk.END, f"Timestamp: {timestamp}\n")
        self.history_details_text.insert(tk.END, f"Action: {action}\n\n")
        self.history_details_text.insert(tk.END, f"Details: {details}\n")
        
        self.history_details_text.configure(state=tk.DISABLED)
    
    def _clear_history(self):
        """Clear the history log."""
        # Confirm with user
        if not messagebox.askyesno("Confirm", "Are you sure you want to clear the history?"):
            return
        
        # Clear history in database
        self.db.data['history'] = []
        self.db.save()
        
        # Refresh UI
        self._refresh_history()
    
    def _show_preferences(self):
        """Show preferences dialog with modern UI and expanded options."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Preferences")
        dialog.geometry("600x650")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configure background color based on theme
        if self.config.get("General", "theme", "light") == "dark":
            bg_color = COLORS["background_dark"]
        else:
            bg_color = COLORS["background"]
        
        dialog.configure(background=bg_color)
        
        # Title
        title_frame = ttk.Frame(dialog)
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(title_frame, text="Settings", style="H1.TLabel").pack(anchor=tk.W)
        ttk.Label(title_frame, text="Customize FileFlow to suit your needs", style="Subtitle.TLabel").pack(anchor=tk.W)
        
        # Create a notebook for different settings categories
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # General settings
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        ttk.Label(general_frame, text="General Settings", style="H3.TLabel").grid(
            row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)
        
        # Auto update check
        auto_update_var = tk.BooleanVar(value=self.config.get_boolean("General", "auto_update_check", True))
        ttk.Checkbutton(general_frame, text="Check for updates on startup", variable=auto_update_var).grid(
            row=1, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        # Theme
        ttk.Label(general_frame, text="Theme:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        
        theme_var = tk.StringVar(value=self.config.get("General", "theme", "light"))
        theme_combo = ttk.Combobox(general_frame, textvariable=theme_var, state="readonly")
        theme_combo['values'] = ("light", "dark")
        theme_combo.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Use modern UI
        modern_ui_var = tk.BooleanVar(value=self.config.get_boolean("Interface", "use_modern_ui", True))
        ttk.Checkbutton(general_frame, text="Use modern UI", variable=modern_ui_var).grid(
            row=3, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        # Enable animations
        animation_var = tk.BooleanVar(value=self.config.get_boolean("Interface", "animation_enabled", True))
        ttk.Checkbutton(general_frame, text="Enable animations", variable=animation_var).grid(
            row=4, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        # Scanning settings
        scanning_frame = ttk.Frame(notebook)
        notebook.add(scanning_frame, text="Scanning")
        
        ttk.Label(scanning_frame, text="Scanning Settings", style="H3.TLabel").grid(
            row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)
        
        # Ignore hidden files
        ignore_hidden_var = tk.BooleanVar(value=self.config.get_boolean("Scanning", "ignore_hidden_files", True))
        ttk.Checkbutton(scanning_frame, text="Ignore hidden files", variable=ignore_hidden_var).grid(
            row=1, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        # Ignore system files
        ignore_system_var = tk.BooleanVar(value=self.config.get_boolean("Scanning", "ignore_system_files", True))
        ttk.Checkbutton(scanning_frame, text="Ignore system files", variable=ignore_system_var).grid(
            row=2, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        # Max file size
        ttk.Label(scanning_frame, text="Max file size (MB):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        
        max_size_var = tk.StringVar(value=str(self.config.get_int("Scanning", "max_file_size_mb", 1000)))
        ttk.Entry(scanning_frame, textvariable=max_size_var, width=10).grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Excluded folders
        ttk.Label(scanning_frame, text="Excluded folders:").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        
        excluded_folders_var = tk.StringVar(value=self.config.get("Scanning", "excluded_folders", "node_modules,venv,.git,__pycache__,build,dist"))
        excluded_folders_entry = ttk.Entry(scanning_frame, textvariable=excluded_folders_var, width=40)
        excluded_folders_entry.grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Help text for excluded folders
        ttk.Label(scanning_frame, text="Separate multiple folders with commas", foreground=COLORS["text_secondary"]).grid(
            row=5, column=1, padx=10, pady=(0, 5), sticky=tk.W)
        
        # Duplicates settings
        duplicates_frame = ttk.Frame(notebook)
        notebook.add(duplicates_frame, text="Duplicates")
        
        ttk.Label(duplicates_frame, text="Duplicate Detection Settings", style="H3.TLabel").grid(
            row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)
        
        # Min file size
        ttk.Label(duplicates_frame, text="Min file size (KB):").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        
        min_size_var = tk.StringVar(value=str(self.config.get_int("Duplicates", "min_size_kb", 10)))
        ttk.Entry(duplicates_frame, textvariable=min_size_var, width=10).grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Compare method
        ttk.Label(duplicates_frame, text="Compare method:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        
        compare_method_var = tk.StringVar(value=self.config.get("Duplicates", "compare_method", "content"))
        compare_method_combo = ttk.Combobox(duplicates_frame, textvariable=compare_method_var, state="readonly")
        compare_method_combo['values'] = ("content", "name", "both")
        compare_method_combo.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Hash algorithm
        ttk.Label(duplicates_frame, text="Hash algorithm:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        
        hash_algo_var = tk.StringVar(value=self.config.get("Duplicates", "hash_algorithm", "sha256"))
        hash_algo_combo = ttk.Combobox(duplicates_frame, textvariable=hash_algo_var, state="readonly")
        hash_algo_combo['values'] = ("md5", "sha1", "sha256")
        hash_algo_combo.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Help text for hash algorithm
        ttk.Label(duplicates_frame, text="MD5: Fastest, SHA256: Most accurate", foreground=COLORS["text_secondary"]).grid(
            row=4, column=1, padx=10, pady=(0, 5), sticky=tk.W)
        
        # Organization settings
        organization_frame = ttk.Frame(notebook)
        notebook.add(organization_frame, text="Organization")
        
        ttk.Label(organization_frame, text="Organization Settings", style="H3.TLabel").grid(
            row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)
        
        # Default mode
        ttk.Label(organization_frame, text="Default mode:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        
        mode_var = tk.StringVar(value=self.config.get("Organization", "default_mode", "suggest"))
        mode_combo = ttk.Combobox(organization_frame, textvariable=mode_var, state="readonly")
        mode_combo['values'] = ("suggest", "auto")
        mode_combo.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Preserve original
        preserve_var = tk.BooleanVar(value=self.config.get_boolean("Organization", "preserve_original", True))
        ttk.Checkbutton(organization_frame, text="Preserve original files", variable=preserve_var).grid(
            row=2, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        # Naming convention
        ttk.Label(organization_frame, text="Naming convention:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        
        naming_var = tk.StringVar(value=self.config.get("Organization", "naming_convention", "camel"))
        naming_combo = ttk.Combobox(organization_frame, textvariable=naming_var, state="readonly")
        naming_combo['values'] = ("camel", "snake", "kebab", "normal")
        naming_combo.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Examples of naming conventions
        naming_examples = ttk.Frame(organization_frame)
        naming_examples.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        ttk.Label(naming_examples, text="Examples:", foreground=COLORS["text_secondary"]).grid(
            row=0, column=0, padx=0, pady=2, sticky=tk.W)
        ttk.Label(naming_examples, text="CamelCase: MyDocument.pdf", foreground=COLORS["text_secondary"]).grid(
            row=1, column=0, padx=20, pady=2, sticky=tk.W)
        ttk.Label(naming_examples, text="snake_case: my_document.pdf", foreground=COLORS["text_secondary"]).grid(
            row=2, column=0, padx=20, pady=2, sticky=tk.W)
        ttk.Label(naming_examples, text="kebab-case: my-document.pdf", foreground=COLORS["text_secondary"]).grid(
            row=3, column=0, padx=20, pady=2, sticky=tk.W)
        ttk.Label(naming_examples, text="Normal Case: My Document.pdf", foreground=COLORS["text_secondary"]).grid(
            row=4, column=0, padx=20, pady=2, sticky=tk.W)
        
        # Interface settings
        interface_frame = ttk.Frame(notebook)
        notebook.add(interface_frame, text="Interface")
        
        ttk.Label(interface_frame, text="Interface Settings", style="H3.TLabel").grid(
            row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)
        
        # Show tooltips
        tooltips_var = tk.BooleanVar(value=self.config.get_boolean("Interface", "show_tooltips", True))
        ttk.Checkbutton(interface_frame, text="Show tooltips", variable=tooltips_var).grid(
            row=1, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        # Confirm operations
        confirm_var = tk.BooleanVar(value=self.config.get_boolean("Interface", "confirm_operations", True))
        ttk.Checkbutton(interface_frame, text="Confirm operations", variable=confirm_var).grid(
            row=2, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
        # Max recent directories
        ttk.Label(interface_frame, text="Max recent directories:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        
        max_recent_var = tk.StringVar(value=str(self.config.get_int("Interface", "max_recent_dirs", 10)))
        ttk.Entry(interface_frame, textvariable=max_recent_var, width=10).grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        
        # About section
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="About")
        
        about_content = ttk.Frame(about_frame)
        about_content.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        ttk.Label(about_content, text="FileFlow", style="H1.TLabel").pack(anchor=tk.CENTER, pady=(0, 10))
        ttk.Label(about_content, text=f"Version {VERSION}").pack(anchor=tk.CENTER)
        ttk.Label(about_content, text="An intelligent file organization system").pack(anchor=tk.CENTER, pady=(0, 20))
        
        features_frame = ttk.LabelFrame(about_content, text="Key Features")
        features_frame.pack(fill=tk.X, padx=20, pady=10)
        
        features = [
            "Advanced file pattern analysis",
            "Smart duplicate detection",
            "Customizable organization rules",
            "Intelligent file renaming",
            "Exclusion of development folders like node_modules"
        ]
        
        for i, feature in enumerate(features):
            ttk.Label(features_frame, text=f"• {feature}").pack(anchor=tk.W, padx=10, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(button_frame, text="Save", style="Primary.TButton", command=lambda: self._save_preferences(
            auto_update_var.get(),
            theme_var.get(),
            ignore_hidden_var.get(),
            ignore_system_var.get(),
            max_size_var.get(),
            min_size_var.get(),
            compare_method_var.get(),
            hash_algo_var.get(),
            mode_var.get(),
            preserve_var.get(),
            naming_var.get(),
            tooltips_var.get(),
            confirm_var.get(),
            max_recent_var.get(),
            excluded_folders_var.get(),
            modern_ui_var.get(),
            animation_var.get(),
            dialog
        )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Reset button
        ttk.Button(button_frame, text="Reset to Defaults", command=lambda: self._reset_preferences(dialog)).pack(side=tk.LEFT, padx=5)
    
    def _save_preferences(self, auto_update, theme, ignore_hidden, ignore_system, max_size,
                        min_size, compare_method, hash_algo, mode, preserve, naming,
                        tooltips, confirm, max_recent, excluded_folders, modern_ui, animations, dialog):
        """Save preferences."""
        try:
            # Convert string values to appropriate types
            try:
                max_size = int(max_size)
            except ValueError:
                max_size = 1000
            
            try:
                min_size = int(min_size)
            except ValueError:
                min_size = 10
            
            try:
                max_recent = int(max_recent)
            except ValueError:
                max_recent = 10
            
            # Save to config
            self.config.set("General", "auto_update_check", str(auto_update))
            self.config.set("General", "theme", theme)
            
            self.config.set("Scanning", "ignore_hidden_files", str(ignore_hidden))
            self.config.set("Scanning", "ignore_system_files", str(ignore_system))
            self.config.set("Scanning", "max_file_size_mb", str(max_size))
            self.config.set("Scanning", "excluded_folders", excluded_folders)
            
            self.config.set("Duplicates", "min_size_kb", str(min_size))
            self.config.set("Duplicates", "compare_method", compare_method)
            self.config.set("Duplicates", "hash_algorithm", hash_algo)
            
            self.config.set("Organization", "default_mode", mode)
            self.config.set("Organization", "preserve_original", str(preserve))
            self.config.set("Organization", "naming_convention", naming)
            
            self.config.set("Interface", "show_tooltips", str(tooltips))
            self.config.set("Interface", "confirm_operations", str(confirm))
            self.config.set("Interface", "max_recent_dirs", str(max_recent))
            self.config.set("Interface", "use_modern_ui", str(modern_ui))
            self.config.set("Interface", "animation_enabled", str(animations))
            
            # Save the updated configuration
            self.config.save_config()
            
            # Display success message with animation if enabled
            if animations:
                dialog.destroy()
                success_dialog = tk.Toplevel(self.root)
                success_dialog.title("Success")
                success_dialog.geometry("300x150")
                success_dialog.transient(self.root)
                success_dialog.grab_set()
                
                # Configure success dialog with theme colors
                if theme == "dark":
                    bg_color = COLORS["background_dark"]
                    fg_color = COLORS["text_light"]
                else:
                    bg_color = COLORS["background"]
                    fg_color = COLORS["text"]
                
                success_dialog.configure(background=bg_color)
                
                # Create success message with custom styling
                success_frame = ttk.Frame(success_dialog)
                success_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                
                # Success icon (using text as placeholder)
                ttk.Label(success_frame, text="✓", font=("Segoe UI", 36), foreground=COLORS["success"]).pack(pady=(0, 10))
                
                ttk.Label(success_frame, text="Settings saved successfully", 
                        style="Title.TLabel").pack()
                
                # Auto-close after 1.5 seconds
                success_dialog.after(1500, success_dialog.destroy)
                
                # Apply theme change (requires restart)
                if theme != self.config.get("General", "theme", "light") or modern_ui != self.config.get_boolean("Interface", "use_modern_ui", True):
                    restart_dialog = tk.Toplevel(self.root)
                    restart_dialog.title("Restart Required")
                    restart_dialog.geometry("400x200")
                    restart_dialog.transient(self.root)
                    restart_dialog.grab_set()
                    restart_dialog.configure(background=bg_color)
                    
                    restart_frame = ttk.Frame(restart_dialog)
                    restart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                    
                    ttk.Label(restart_frame, text="Restart Required", 
                            style="H2.TLabel").pack(pady=(0, 10))
                    
                    ttk.Label(restart_frame, text="Some changes require a restart to take effect.",
                            style="Subtitle.TLabel").pack(pady=(0, 20))
                    
                    button_frame = ttk.Frame(restart_frame)
                    button_frame.pack(fill=tk.X)
                    
                    ttk.Button(button_frame, text="Restart Now", 
                             style="Primary.TButton", 
                             command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
                    
                    ttk.Button(button_frame, text="Later", 
                             command=restart_dialog.destroy).pack(side=tk.RIGHT, padx=5)
            else:
                # Simple message without animation
                messagebox.showinfo("Success", "Preferences saved successfully.")
                
                # Apply theme if changed
                if theme != self.config.get("General", "theme", "light"):
                    self._change_theme(theme)
                
                dialog.destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save preferences: {e}")
    
    def _reset_preferences(self, dialog):
        """Reset preferences to defaults."""
        # Confirm with user
        if not messagebox.askyesno("Confirm", "Are you sure you want to reset all preferences to defaults?"):
            return
        
        # Create a new configuration manager
        config = ConfigManager()
        
        # Load default configuration
        self.config = config
        
        messagebox.showinfo("Success", "Preferences reset to defaults.")
        dialog.destroy()
        
        # Apply theme
        self._change_theme(self.config.get("General", "theme", "light"))
    
    def _change_theme(self, theme):
        """Change application theme."""
        self.config.set("General", "theme", theme)
        
        # Restart application is required to fully apply theme
        if messagebox.askyesno("Restart Required", "The theme will be applied after restarting the application. Restart now?"):
            self.root.destroy()
            # The application will be restarted by the main script
        else:
            # Apply some basic theme changes without restart
            style = ttk.Style()
            
            if theme == "dark":
                style.configure("TFrame", background="#2D2D2D")
                style.configure("TLabel", background="#2D2D2D", foreground="#FFFFFF")
                style.configure("TButton", background=COLORS["primary"], foreground="#FFFFFF")
                self.root.configure(background="#2D2D2D")
            else:
                style.configure("TFrame", background=COLORS["background"])
                style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"])
                style.configure("TButton", background=COLORS["primary"], foreground="#FFFFFF")
                self.root.configure(background=COLORS["background"])
    
    def _show_help(self):
        """Show help dialog."""
        webbrowser.open("https://github.com/fileflow/fileflow/wiki/Help")
    
    def _show_about(self):
        """Show about dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("About FileFlow")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="FileFlow", style="H1.TLabel").pack(pady=10)
        ttk.Label(dialog, text=f"Version {VERSION}").pack()
        ttk.Label(dialog, text="An intelligent file organization system").pack(pady=5)
        ttk.Label(dialog, text="Released: April 2025").pack()
        
        ttk.Separator(dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(dialog, text="Features:").pack(anchor=tk.W, padx=20)
        
        features = [
            "Analyze your existing file organization patterns",
            "Suggest personalized organization systems",
            "Automatically sort and rename files based on content",
            "Clean up duplicate files",
            "Maintain consistent naming conventions"
        ]
        
        for feature in features:
            ttk.Label(dialog, text=f"• {feature}").pack(anchor=tk.W, padx=30)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=15)
    
    def _update_check_callback(self, data):
        """Callback for update check."""
        if data.get('checking', False):
            return
        
        update_available = data.get('update_available', False)
        latest_version = data.get('latest_version')
        
        if update_available:
            # Show update dialog
            if messagebox.askyesno("Update Available", 
                                 f"A new version of FileFlow is available: {latest_version}\n\n"
                                 f"Your current version is {VERSION}.\n\n"
                                 "Would you like to download the update now?"):
                self.update_manager.download_update(callback=self._download_callback)
    
    def _download_callback(self, data):
        """Callback for update download."""
        if data.get('downloading', False):
            progress = data.get('progress', 0)
            self._update_status(f"Downloading update: {int(progress * 100)}%", progress)
        else:
            if 'error' in data:
                messagebox.showerror("Download Error", f"Failed to download update: {data['error']}")
                self._update_status("Ready", 0)
            else:
                messagebox.showinfo("Download Complete", data.get('message', "Update downloaded successfully."))
                self._update_status("Ready", 0)
    
    def _update_dashboard(self):
        """Update the dashboard data with modern styling."""
        # Add animations if enabled
        use_animations = self.config.get_boolean("Interface", "animation_enabled", True)
        
        # Update file count with animation if enabled
        file_count = self.db.data['metadata']['file_count']
        if use_animations and hasattr(self, '_prev_file_count'):
            self._animate_counter(self.files_count_label, self._prev_file_count, file_count)
        else:
            self.files_count_label.config(text=str(file_count))
        self._prev_file_count = file_count
        
        # Update total size with formatted display
        total_size = self.db.data['stats']['total_size']
        self.total_size_label.config(text=self._format_size(total_size))
        
        # Update duplicates count and space saved
        stats = self.duplicate_finder.get_total_duplicates_stats()
        dupes_count = stats.get('total_duplicates', 0)
        
        if use_animations and hasattr(self, '_prev_dupes_count'):
            self._animate_counter(self.dupes_count_label, self._prev_dupes_count, dupes_count)
        else:
            self.dupes_count_label.config(text=str(dupes_count))
        self._prev_dupes_count = dupes_count
        
        # Update space wasted with proper formatting
        wasted_size = stats.get('wasted_size', 0)
        self.space_saved_label.config(text=self._format_size(wasted_size))
        
        # Change color based on wasted space
        if wasted_size > 1024 * 1024 * 1024:  # More than 1GB wasted
            self.space_saved_label.config(foreground=COLORS["error"])
        elif wasted_size > 100 * 1024 * 1024:  # More than 100MB wasted
            self.space_saved_label.config(foreground=COLORS["warning"])
        else:
            self.space_saved_label.config(foreground=COLORS["text"])
        
        # Update recent scans
        for item in self.scans_tree.get_children():
            self.scans_tree.delete(item)
        
        # Get directories from the database
        directories = {}
        
        for file_path, metadata in self.db.get_all_files().items():
            dir_path = os.path.dirname(file_path)
            
            if dir_path not in directories:
                directories[dir_path] = {
                    'count': 0,
                    'date': 0,
                    'size': 0
                }
            
            directories[dir_path]['count'] += 1
            directories[dir_path]['size'] += metadata.get('size', 0)
            
            # Get the most recent scan date
            scanned_at = metadata.get('scanned_at')
            if scanned_at:
                try:
                    scan_time = datetime.datetime.fromisoformat(scanned_at).timestamp()
                    if scan_time > directories[dir_path]['date']:
                        directories[dir_path]['date'] = scan_time
                except ValueError:
                    pass
        
        # Add directories to tree with modern styling
        for dir_path, data in sorted(directories.items(), key=lambda x: x[1]['date'], reverse=True)[:10]:
            count = data['count']
            date = datetime.datetime.fromtimestamp(data['date']).strftime('%Y-%m-%d %H:%M') if data['date'] > 0 else ''
            
            # Truncate long directory paths for better display
            display_path = dir_path
            if len(display_path) > 50:
                display_path = "..." + display_path[-47:]
            
            self.scans_tree.insert("", "end", values=(display_path, count, date))
        
        # Update recent actions
        for item in self.actions_tree.get_children():
            self.actions_tree.delete(item)
        
        # Get history entries
        history = self.db.get_history(limit=10)
        
        action_icons = {
            'scan': '🔍',
            'delete': '🗑️',
            'move': '📦',
            'organize': '🗂️',
            'rename': '✏️',
            'symlink': '🔗',
            'hardlink': '🔗',
            'delete_duplicate': '🗑️',
            'delete_empty': '🗑️'
        }
        
        for entry in history:
            timestamp = entry.get('timestamp', '')
            action = entry.get('action', '')
            details = entry.get('details', {})
            
            # Format details for display with icons
            icon = action_icons.get(action.split('_')[0], '🔹')
            
            if 'file_path' in details:
                detail_text = f"{icon} {os.path.basename(details['file_path'])}"
            elif 'original_path' in details and 'new_path' in details:
                detail_text = f"{icon} {os.path.basename(details['original_path'])} → {os.path.basename(details['new_path'])}"
            else:
                detail_text = f"{icon} {str(details)[:50]}"  # Limit length
            
            # Format timestamp in a more user-friendly way
            timestamp_dt = datetime.datetime.fromisoformat(timestamp) if timestamp else datetime.datetime.now()
            
            # Use relative time for recent actions (today/yesterday)
            now = datetime.datetime.now()
            if timestamp_dt.date() == now.date():
                formatted_timestamp = timestamp_dt.strftime("Today %H:%M")
            elif timestamp_dt.date() == (now - datetime.timedelta(days=1)).date():
                formatted_timestamp = timestamp_dt.strftime("Yesterday %H:%M")
            else:
                formatted_timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M")
            
            # Display action in a user-friendly format
            friendly_action = action.replace('_', ' ').title()
            
            self.actions_tree.insert("", "end", values=(friendly_action, detail_text, formatted_timestamp))
    
    def _animate_counter(self, label, start, end, duration=500):
        """Animate a counter from start to end value."""
        if start == end:
            return
        
        steps = 10
        step_time = duration / steps
        increment = (end - start) / steps
        
        def update_step(current_step):
            if current_step >= steps:
                label.config(text=str(end))
                return
            
            value = int(start + (current_step * increment))
            label.config(text=str(value))
            label.after(int(step_time), lambda: update_step(current_step + 1))
        
        update_step(0)
    
    def _get_disk_usage(self):
        """Get disk usage for the current drive."""
        try:
            if platform.system() == "Windows":
                # Get the drive of the current working directory
                drive = os.path.splitdrive(os.getcwd())[0] + "\\"
                total, used, free = shutil.disk_usage(drive)
            else:
                # For Unix-based systems
                total, used, free = shutil.disk_usage("/")
            
            percent_used = int((used / total) * 100)
            
            return {
                "total_space": self._format_size(total),
                "used_space": self._format_size(used),
                "free_space": self._format_size(free),
                "percent_used": percent_used
            }
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {
                "total_space": "Unknown",
                "used_space": "Unknown",
                "free_space": "Unknown",
                "percent_used": 0
            }
    
    def _format_size(self, size):
        """Format a size in bytes to a human-readable string."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
    
    def _open_file(self, file_path):
        """Open a file with the default application."""
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # Linux
                subprocess.call(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
    
    def _show_in_folder(self, file_path):
        """Show a file in its folder."""
        try:
            if platform.system() == "Windows":
                subprocess.call(["explorer", "/select,", file_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", "-R", file_path])
            else:  # Linux
                # Get the directory path
                dir_path = os.path.dirname(file_path)
                subprocess.call(["xdg-open", dir_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show file in folder: {e}")
    
    def run(self):
        """Run the application."""
        # Check license status at startup
        self.license_functions["check_license"]()
        
        # Start the main loop
        self.root.mainloop()


def main():
    """Main entry point for the application."""
    app = FileFlowApp()
    app.run()


if __name__ == "__main__":
    main()