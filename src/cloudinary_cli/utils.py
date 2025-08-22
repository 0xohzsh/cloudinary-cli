"""
Utility functions for the Cloudinary CLI.
"""

import os
import urllib.parse
from .config import get_default_folder, should_use_unique_names


def get_resource_type(file_path):
    """Determine Cloudinary resource type based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()

    # Image extensions
    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".svg",
        ".ico",
        ".psd",
        ".ai",
        ".eps",
    }

    # Video extensions
    video_extensions = {
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".mkv",
        ".m4v",
        ".3gp",
        ".ogv",
        ".mxf",
        ".ts",
        ".m2ts",
    }

    if ext in image_extensions:
        return "image"
    elif ext in video_extensions:
        return "video"
    else:
        return "raw"


def should_skip_file(filename):
    """Check if a file should be skipped during upload."""
    skip_patterns = [
        ".DS_Store",
        ".Thumbs.db",
        "Thumbs.db",
        ".gitignore",
        ".git",
        "desktop.ini",
        "Desktop.ini",
        ".tmp",
        "~$",
        ".swp",
        ".swo",
        "__pycache__",
    ]

    # Skip hidden files (starting with .)
    if filename.startswith("."):
        return True

    # Skip files matching patterns
    for pattern in skip_patterns:
        if pattern in filename:
            return True

    return False


def normalize_cloud_folder(cloud_folder):
    """Normalize cloud folder path with default folder prefix."""
    default_folder = get_default_folder()

    if not default_folder:
        return cloud_folder

    # If cloud_folder already starts with default_folder, return as is
    if cloud_folder.startswith(default_folder + "/") or cloud_folder == default_folder:
        return cloud_folder

    # Add default folder prefix
    return f"{default_folder}/{cloud_folder}"


def get_cloudinary_filename(file_path, local_folder=None):
    """Get the filename to use for Cloudinary upload."""
    # Always return just the base filename without extension
    return os.path.splitext(os.path.basename(file_path))[0]


def get_folder_url(cloud_folder):
    """Generate Cloudinary console URL for a folder."""
    # URL encode the folder path
    encoded_folder = urllib.parse.quote(f"/{cloud_folder}", safe="")

    # Get cloud name from config (we'll need to import this)
    from .config import get_cloudinary_config

    config = get_cloudinary_config()
    cloud_name = config["cloud_name"]

    return f"https://console.cloudinary.com/console/c-{cloud_name}/media_library/folders/{encoded_folder}"
