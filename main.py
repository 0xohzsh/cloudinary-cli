#!/usr/bin/env python3
"""
Cloudinary CLI Tool - Modular Version
A command-line tool for managing files in Cloudinary with automatic compression support.
"""

import sys
import os

# Add src to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from cloudinary_cli.cli import main

if __name__ == "__main__":
    main()
