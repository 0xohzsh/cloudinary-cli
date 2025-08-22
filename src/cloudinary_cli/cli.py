"""
Command-line interface for the Cloudinary CLI tool.
"""

import argparse
import sys
import os
from .config import initialize_cloudinary
from .cloudinary_ops import (
    upload_files,
    upload_single_file,
    list_folders_in_melted,
    delete_folder,
    download_folder,
    list_files_in_folder,
)


def show_help():
    """Display available commands and usage examples."""
    print("\n🌤️  Cloudinary Management Tool")
    print("=" * 50)
    print("\nAvailable commands:")
    print(
        "  upload <local_path> <cloud_folder>    - Upload file or directory to Cloudinary"
    )
    print("  file <file_path>                      - Upload single file (interactive)")
    print("  list                                  - List folders in 'melted'")
    print("  files                                 - List files in a selected folder")
    print("  download                              - Download a folder from 'melted'")
    print("  delete                                - Delete a folder from 'melted'")
    print("\nUsage examples:")
    print(
        "  python main.py upload ./images my_photos           # Upload to default/my_photos"
    )
    print(
        "  python main.py upload ./photo.jpg single           # Upload to default/single"
    )
    print("  python main.py upload ./images photos --force      # Force re-upload")
    print("  python main.py upload ./images custom/path        # Explicit path")
    print(
        "  python main.py file ./document.pdf                 # Interactive file upload"
    )
    print("  python main.py list")
    print(
        "  python main.py files                                # List files in folder"
    )
    print("  python main.py download                             # Download a folder")
    print("  python main.py delete")
    print("\n💡 Notes:")
    print("  - Supports all file types (images, videos, documents, etc.)")
    print("  - Preserves original filenames (no random suffixes)")
    print("  - Automatically creates folders under default folder (set in .env)")
    print("  - Set CLOUDINARY_DEFAULT_FOLDER in .env to change default location")
    print("  - Leave CLOUDINARY_DEFAULT_FOLDER empty to use root folder")
    print("  - Set CLOUDINARY_UNIQUE_NAMES=true to generate unique filenames")
    print("  - Skips existing files by default (use --force to re-upload)")
    print("  - Upload preserves subdirectory structure for directories")
    print("  - Automatically skips hidden and temporary files")
    print("  - Compresses large files (>100MB) using 7z with volume splitting")
    print("  - Automatically decompresses 7z files on download")
    print("  - Creates remote folder if it doesn't exist")
    print("\nFor more help on a specific command, use:")
    print("  python main.py <command> --help")


def interactive_upload():
    """Interactive file upload."""
    print("\n📤 Interactive File Upload")
    print("=" * 30)

    # Get file path
    while True:
        file_path = input("Enter file path: ").strip()
        if not file_path:
            print("❌ File path cannot be empty")
            continue
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
        if not os.path.isfile(file_path):
            print(f"❌ Path is not a file: {file_path}")
            continue
        break

    # Get cloud folder
    cloud_folder = input("Enter cloud folder name: ").strip()
    if not cloud_folder:
        cloud_folder = "uploads"
        print(f"Using default folder: {cloud_folder}")

    # Ask about duplicates
    skip_duplicates = True
    force_upload = input("Force re-upload if file exists? (y/N): ").strip().lower()
    if force_upload in ["y", "yes"]:
        skip_duplicates = False

    print(f"\n📤 Uploading '{file_path}' to '{cloud_folder}'...")
    success, uploaded, skipped = upload_single_file(
        file_path, cloud_folder, skip_duplicates
    )

    if success:
        if uploaded > 0:
            print(f"✅ Upload completed successfully!")
        elif skipped > 0:
            print(f"⏭️  File was skipped (already exists)")
    else:
        print(f"❌ Upload failed")


def interactive_list_folders():
    """Interactive folder listing."""
    folders = list_folders_in_melted()
    return folders


def interactive_delete():
    """Interactive folder deletion."""
    folders = list_folders_in_melted()
    if not folders:
        return

    while True:
        try:
            choice = input(
                "\nEnter the number of the folder to delete (or 'q' to quit): "
            ).strip()
            if choice.lower() == "q":
                return

            folder_index = int(choice) - 1
            if 0 <= folder_index < len(folders):
                selected_folder = folders[folder_index]
                folder_path = selected_folder["path"]

                # Confirm deletion
                print(
                    f"\n⚠️  You are about to delete folder '{folder_path}' and ALL its contents."
                )
                confirm = input("Are you sure? Type 'DELETE' to confirm: ").strip()

                if confirm == "DELETE":
                    delete_folder(folder_path)
                else:
                    print("❌ Deletion cancelled")
                return
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a valid number")


def interactive_download():
    """Interactive folder download."""
    folders = list_folders_in_melted()
    if not folders:
        return

    while True:
        try:
            choice = input("Enter the number of the folder to download: ").strip()
            folder_index = int(choice) - 1
            if 0 <= folder_index < len(folders):
                selected_folder = folders[folder_index]
                folder_path = selected_folder["path"]

                # Get download path
                default_path = f"./downloads/{os.path.basename(folder_path)}"
                download_path = input(
                    f"Enter local download path (default: {default_path}): "
                ).strip()
                if not download_path:
                    download_path = default_path

                download_folder(folder_path, download_path)
                return
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a valid number")


def interactive_list_files():
    """Interactive file listing in folders."""
    folders = list_folders_in_melted()
    if not folders:
        return

    while True:
        try:
            choice = input("Enter the number of the folder to list files: ").strip()
            folder_index = int(choice) - 1
            if 0 <= folder_index < len(folders):
                selected_folder = folders[folder_index]
                folder_path = selected_folder["path"]
                list_files_in_folder(folder_path)
                return
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a valid number")


def main():
    """Main CLI entry point."""
    try:
        # Initialize Cloudinary
        initialize_cloudinary()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)

    # Check command line arguments
    if len(sys.argv) == 1:
        show_help()
        return

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Cloudinary Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload files or directories")
    upload_parser.add_argument("local_path", help="Local file or directory path")
    upload_parser.add_argument("cloud_folder", help="Cloudinary folder name")
    upload_parser.add_argument(
        "--force", action="store_true", help="Force re-upload existing files"
    )

    # File command (interactive upload)
    file_parser = subparsers.add_parser("file", help="Upload single file interactively")
    file_parser.add_argument("file_path", nargs="?", help="File path to upload")

    # List command
    subparsers.add_parser("list", help="List folders")

    # Files command
    subparsers.add_parser("files", help="List files in a folder")

    # Download command
    subparsers.add_parser("download", help="Download a folder")

    # Delete command
    subparsers.add_parser("delete", help="Delete a folder")

    args = parser.parse_args()

    # Execute commands
    if args.command == "upload":
        skip_duplicates = not args.force
        upload_files(args.local_path, args.cloud_folder, skip_duplicates)

    elif args.command == "file":
        if args.file_path:
            # Non-interactive mode with file path provided
            cloud_folder = input("Enter cloud folder name: ").strip()
            if not cloud_folder:
                cloud_folder = "uploads"

            skip_duplicates = True
            force_upload = (
                input("Force re-upload if file exists? (y/N): ").strip().lower()
            )
            if force_upload in ["y", "yes"]:
                skip_duplicates = False

            upload_single_file(args.file_path, cloud_folder, skip_duplicates)
        else:
            interactive_upload()

    elif args.command == "list":
        interactive_list_folders()

    elif args.command == "files":
        interactive_list_files()

    elif args.command == "download":
        interactive_download()

    elif args.command == "delete":
        interactive_delete()

    else:
        show_help()


if __name__ == "__main__":
    main()
