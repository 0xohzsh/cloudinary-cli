"""
Cloudinary operations module.
Handles upload, download, list, and delete operations.
"""

import os
import shutil
import requests
import cloudinary.uploader
import cloudinary.api
from .config import should_use_unique_names
from .utils import (
    get_resource_type,
    should_skip_file,
    normalize_cloud_folder,
    get_cloudinary_filename,
    get_folder_url,
)
from .compression import compress_large_file, detect_and_decompress_archives


def check_file_exists(public_id, resource_type):
    """Check if a file already exists in Cloudinary."""
    try:
        cloudinary.api.resource(public_id, resource_type=resource_type)
        return True
    except cloudinary.api.NotFound:
        return False
    except Exception:
        # If there's any other error, assume file doesn't exist
        return True


def upload_single_file(file_path, cloud_folder, skip_duplicates=True):
    """Upload a single file to Cloudinary with compression support."""
    filename = os.path.basename(file_path)

    # Skip hidden/temporary files
    if should_skip_file(filename):
        print(f"⏭️  Skipping hidden/temporary file: {filename}")
        return True, 0, 1  # success, uploaded_count, skipped_count

    # Normalize cloud folder path
    current_cloud_folder = normalize_cloud_folder(cloud_folder)

    try:
        # Check if file needs compression
        compressed_files, was_compressed = compress_large_file(file_path)

        # Handle multiple files (compressed volumes) or single file
        if was_compressed and isinstance(compressed_files, list):
            uploaded_count = 0
            failed_count = 0

            # Upload all volume files
            for i, volume_file in enumerate(compressed_files):
                volume_filename = get_cloudinary_filename(
                    volume_file, os.path.dirname(volume_file)
                )
                volume_public_id = f"{current_cloud_folder}/{volume_filename}"

                # Determine resource type
                resource_type = get_resource_type(volume_file)

                # Check for duplicates if enabled
                if skip_duplicates and check_file_exists(
                    volume_public_id, resource_type
                ):
                    print(
                        f"⏭️  Skipping volume {i+1}/{len(compressed_files)} - already exists"
                    )
                    continue

                try:
                    print(
                        f"📄 Uploading volume {i+1}/{len(compressed_files)}: {os.path.basename(volume_file)}"
                    )
                    print(f"🎯 Target public_id: {volume_public_id}")
                    result = cloudinary.uploader.upload(
                        volume_file,
                        resource_type=resource_type,
                        public_id=volume_public_id,
                        use_filename=True,
                        unique_filename=should_use_unique_names(),
                    )
                    uploaded_count += 1
                    print(f"✅ Success: {result.get('public_id')}")
                except Exception as e:
                    print(f"❌ Failed to upload volume {i+1}: {e}")
                    failed_count += 1

            # Clean up temporary files
            temp_dir = os.path.dirname(compressed_files[0])
            shutil.rmtree(temp_dir)
            print(f"🗑️  Cleaned up temporary files")

            return failed_count == 0, uploaded_count, 0

        else:
            # Single file upload (original or single compressed file)
            upload_file = compressed_files if was_compressed else file_path

            # Get filename based on preserve path setting
            cloudinary_filename = get_cloudinary_filename(
                upload_file, os.path.dirname(file_path)
            )
            public_id = f"{current_cloud_folder}/{cloudinary_filename}"

            # Determine resource type
            resource_type = get_resource_type(upload_file)

            # Check for duplicates if enabled
            if skip_duplicates and check_file_exists(public_id, resource_type):
                display_name = (
                    os.path.basename(upload_file) if was_compressed else filename
                )
                print(
                    f"⏭️  Skipping '{display_name}' - already exists in '{current_cloud_folder}'"
                )
                return True, 0, 1

            try:
                target_public_id = f"{current_cloud_folder}/{cloudinary_filename}"
                display_name = (
                    os.path.basename(upload_file) if was_compressed else filename
                )
                print(
                    f"📄 Uploading {display_name} ({resource_type}) to folder '{current_cloud_folder}'..."
                )
                print(f"🎯 Target public_id: {target_public_id}")

                result = cloudinary.uploader.upload(
                    upload_file,
                    resource_type=resource_type,
                    public_id=target_public_id,
                    use_filename=True,
                    unique_filename=should_use_unique_names(),
                )
                uploaded_count = 1
                print(f"✅ Success: {result.get('public_id')}")

                # Clean up compressed file if needed
                if was_compressed and upload_file != file_path:
                    os.remove(upload_file)

                return True, uploaded_count, 0

            except Exception as e:
                print(f"❌ Failed to upload {file_path}: {e}")
                # Clean up compressed file if needed
                if was_compressed and upload_file != file_path:
                    os.remove(upload_file)
                return False, 0, 0

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False, 0, 0


def upload_files(local_folder, cloud_folder, skip_duplicates=True):
    """Upload files from local folder to Cloudinary."""
    # Normalize cloud folder path
    current_cloud_folder = normalize_cloud_folder(cloud_folder)

    print(f"📁 Uploading from '{local_folder}' to '{current_cloud_folder}'...")

    uploaded_count = 0
    failed_count = 0
    skipped_count = 0

    # Check if input is a file or directory
    if os.path.isfile(local_folder):
        success, uploaded, skipped = upload_single_file(
            local_folder, cloud_folder, skip_duplicates
        )
        if success:
            uploaded_count += uploaded
            skipped_count += skipped
        else:
            failed_count += 1
    else:
        # Directory upload - walk through all files
        for root, dirs, files in os.walk(local_folder):
            # Remove hidden directories from the walk
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file in files:
                file_path = os.path.join(root, file)

                # Calculate relative path to preserve directory structure
                relative_path = os.path.relpath(file_path, local_folder)

                # Create the cloud folder path including subdirectories
                if os.path.dirname(relative_path):
                    file_cloud_folder = (
                        f"{current_cloud_folder}/{os.path.dirname(relative_path)}"
                    )
                else:
                    file_cloud_folder = current_cloud_folder

                success, uploaded, skipped = upload_single_file(
                    file_path, file_cloud_folder.replace(os.sep, "/"), skip_duplicates
                )
                if success:
                    uploaded_count += uploaded
                    skipped_count += skipped
                else:
                    failed_count += 1

    # Print summary
    print(f"\n📊 Upload Summary:")
    print(f"✅ Uploaded: {uploaded_count} files")
    if skipped_count > 0:
        print(f"⏭️  Skipped: {skipped_count} files")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count} files")

    return uploaded_count, failed_count, skipped_count


def list_folders_in_melted():
    """List all folders in the melted directory."""
    try:
        default_folder = normalize_cloud_folder("")
        if not default_folder:
            prefix = ""
        else:
            prefix = default_folder + "/"

        result = cloudinary.api.subfolders(prefix.rstrip("/"))
        folders = result.get("folders", [])

        if not folders:
            print(f"📭 No folders found in '{default_folder or 'root'}'")
            return []

        print(f"📁 Folders in '{default_folder or 'root'}':")
        for i, folder in enumerate(folders, 1):
            folder_path = folder["path"]
            print(f"{i}. {os.path.basename(folder_path)} (path: {folder_path})")

        return folders

    except Exception as e:
        print(f"❌ Error listing folders: {e}")
        return []


def delete_folder(folder_path):
    """Delete a folder and all its contents from Cloudinary."""
    try:
        # Delete all resources in the folder first
        for resource_type in ["image", "video", "raw"]:
            try:
                # Delete resources with the folder prefix
                prefix = (
                    folder_path + "/" if not folder_path.endswith("/") else folder_path
                )
                result = cloudinary.api.delete_resources_by_prefix(
                    prefix, resource_type=resource_type
                )
                if result.get("deleted"):
                    print(f"🗑️  Deleted {len(result['deleted'])} {resource_type} files")
            except Exception as e:
                print(f"⚠️  Warning: Could not delete {resource_type} resources: {e}")

        # Delete the folder itself
        try:
            cloudinary.api.delete_folder(folder_path)
            print(f"🗑️  Deleted folder: {folder_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not delete folder structure: {e}")

        print(f"✅ Successfully deleted folder '{folder_path}' and all its contents")
        return True

    except Exception as e:
        print(f"❌ Error deleting folder '{folder_path}': {e}")
        return False


def download_file(url, local_path):
    """Download a file from URL to local path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Ensure the directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Check if it's a 7z file and decompress it
        if local_path.lower().endswith(".7z"):
            print(f"🗜️  Decompressing {os.path.basename(local_path)}...")
            output_dir = os.path.dirname(local_path)

            from .compression import decompress_7z_file

            if decompress_7z_file(local_path, output_dir):
                # Remove the compressed file after successful decompression
                os.remove(local_path)
                print(f"🗑️  Removed compressed file: {os.path.basename(local_path)}")

        return True
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        return False


def download_folder(folder_path, local_download_path):
    """Download all files from a Cloudinary folder."""
    downloaded_count = 0
    failed_count = 0

    print(f"📥 Starting download from '{folder_path}' to '{local_download_path}'...")

    try:
        # Create local download directory
        os.makedirs(local_download_path, exist_ok=True)

        # Get all resources in folder for each resource type
        for resource_type in ["image", "video", "raw"]:
            try:
                # Get resources with prefix matching the folder
                prefix = (
                    folder_path + "/" if not folder_path.endswith("/") else folder_path
                )
                result = cloudinary.api.resources(
                    type="upload",
                    resource_type=resource_type,
                    prefix=prefix,
                    max_results=500,  # Cloudinary API limit
                )

                resources = result.get("resources", [])

                for resource in resources:
                    public_id = resource["public_id"]
                    secure_url = resource["secure_url"]

                    # Extract filename from public_id (remove folder path)
                    filename = public_id.replace(prefix, "").split("/")[-1]

                    # Add appropriate extension based on format
                    if "format" in resource:
                        filename += f".{resource['format']}"

                    local_file_path = os.path.join(local_download_path, filename)

                    print(f"📄 Downloading {filename}...")
                    if download_file(secure_url, local_file_path):
                        downloaded_count += 1
                        print(f"✅ Success: {local_file_path}")
                    else:
                        failed_count += 1

            except Exception as e:
                print(f"⚠️  Warning: Could not fetch {resource_type} resources: {e}")

    except Exception as e:
        print(f"❌ Error downloading folder '{folder_path}': {e}")
        return

    # After all downloads, check for and decompress archives
    if downloaded_count > 0:
        print(f"\n🔍 Checking for compressed archives...")
        detect_and_decompress_archives(local_download_path)

    print(f"\n🎉 Download completed!")
    print(f"✅ Successfully downloaded: {downloaded_count} files")
    if failed_count > 0:
        print(f"❌ Failed downloads: {failed_count} files")
    print(f"📁 Files saved to: {local_download_path}")


def list_files_in_folder(folder_path):
    """List files in a specific Cloudinary folder."""
    try:
        print(f"📁 Files in '{folder_path}':")

        total_files = 0
        for resource_type in ["image", "video", "raw"]:
            try:
                # Get resources with prefix matching the folder
                prefix = (
                    folder_path + "/" if not folder_path.endswith("/") else folder_path
                )
                result = cloudinary.api.resources(
                    type="upload",
                    resource_type=resource_type,
                    prefix=prefix,
                    max_results=500,
                )

                resources = result.get("resources", [])

                for resource in resources:
                    public_id = resource["public_id"]
                    secure_url = resource["secure_url"]
                    created_at = resource.get("created_at", "Unknown")

                    # Extract filename from public_id
                    filename = public_id.replace(prefix, "").split("/")[-1]
                    if "format" in resource:
                        filename += f".{resource['format']}"

                    print(f"  📄 {filename}")
                    print(f"     ID: {public_id}")
                    print(f"     URL: {secure_url}")
                    print(f"     Created: {created_at}")
                    print()

                    total_files += 1

            except Exception as e:
                print(f"⚠️  Warning: Could not fetch {resource_type} resources: {e}")

        if total_files == 0:
            print(f"📭 No files found in folder '{folder_path}'")
        else:
            print(f"📊 Total files: {total_files}")

    except Exception as e:
        print(f"❌ Error listing files in folder '{folder_path}': {e}")
