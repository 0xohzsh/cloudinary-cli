"""
Configuration module for Cloudinary CLI.
Handles environment variables and settings.
"""

import os
from dotenv import load_dotenv
import cloudinary

# Load environment variables
load_dotenv()


def get_cloudinary_config():
    """Get Cloudinary configuration from environment variables."""
    config = {
        "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "api_key": os.getenv("CLOUDINARY_API_KEY"),
        "api_secret": os.getenv("CLOUDINARY_API_SECRET"),
        "secure": os.getenv("CLOUDINARY_SECURE", "true").lower() == "true",
    }

    # Validate required config
    required_fields = ["cloud_name", "api_key", "api_secret"]
    missing_fields = [field for field in required_fields if not config[field]]

    if missing_fields:
        raise ValueError(
            f"Missing required Cloudinary configuration: {', '.join(missing_fields)}. "
            "Please check your .env file."
        )

    return config


def initialize_cloudinary():
    """Initialize Cloudinary with configuration from environment."""
    config = get_cloudinary_config()
    cloudinary.config(**config)
    return config


def get_default_folder():
    """Get the default folder for uploads."""
    return os.getenv("CLOUDINARY_DEFAULT_FOLDER", "")


def should_use_unique_names():
    """Check if Cloudinary should generate unique filenames."""
    return os.getenv("CLOUDINARY_UNIQUE_NAMES", "false").lower() == "true"


def get_max_file_size():
    """Get maximum file size before compression (in MB)."""
    return float(os.getenv("CLOUDINARY_MAX_FILE_SIZE", "8"))
