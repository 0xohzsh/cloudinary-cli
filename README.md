# Cloudinary CLI Tool

A command-line tool for managing files in Cloudinary with automatic compression, duplicate detection, and folder management.

## Features

- 📤 Upload files & folders with directory structure preservation
- 📥 Download folders with automatic decompression
- 📋 List and manage Cloudinary folders
- 🔍 Skip duplicates automatically
- 📦 Compress large files (>8MB) using 7z volume splitting
- 🚫 Filter hidden/temporary files automatically
- 🌐 Support all file types (images, videos, documents)

## Quick Start

```bash
# Install
./install.sh

# Configure (add your Cloudinary credentials)
nano .env

# Use
python3 main.py upload ./videos my-folder
python3 main.py list
python3 main.py download
```

## Commands

| Command                  | Description           |
| ------------------------ | --------------------- |
| `upload <path> <folder>` | Upload file/directory |
| `download`               | Download folder       |
| `list`                   | List folders          |
| `files`                  | List files in folder  |
| `delete`                 | Delete folder         |

## Configuration

Create `.env` with your Cloudinary credentials:

```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_DEFAULT_FOLDER=melted
CLOUDINARY_MAX_FILE_SIZE=8
```

## Requirements

- Python 3.7+
- 7z compression tool: `brew install p7zip` (macOS) or `apt-get install p7zip-full` (Linux)

## Architecture

Modular design with clean separation:

```
src/cloudinary_cli/
├── cli.py              # Command-line interface
├── cloudinary_ops.py   # Upload/download operations
├── compression.py      # 7z compression handling
├── config.py          # Environment configuration
└── utils.py           # Helper functions
```
