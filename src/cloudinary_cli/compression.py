"""
Compression and decompression utilities for large files.
Uses 7z for splitting large files into manageable volumes.
"""

import os
import subprocess
import tempfile
import shutil
from .config import get_max_file_size


def check_7z_available():
    """Check if 7z is available in the system."""
    # Try different 7z command names
    commands = ["7zz", "7z", "7za"]
    for cmd in commands:
        try:
            subprocess.run([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return cmd
        except FileNotFoundError:
            continue
    return None


def get_file_size_mb(file_path):
    """Get file size in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)


def compress_large_file(file_path, max_size_mb=None):
    """Compress large files using 7z with volume splitting."""
    cmd_7z = check_7z_available()
    if not cmd_7z:
        print("⚠️  7z not available. Large files will be uploaded as-is.")
        return file_path, False

    # Get max file size from env or default to 8MB (safely under 10MB limit)
    if max_size_mb is None:
        max_size_mb = get_max_file_size()

    file_size_mb = get_file_size_mb(file_path)
    if file_size_mb <= max_size_mb:
        return file_path, False

    print(f"📦 File is {file_size_mb:.1f}MB, compressing and splitting...")

    # Create temporary directory for compressed files
    temp_dir = tempfile.mkdtemp(prefix="cloudinary_compress_")
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    archive_path = os.path.join(temp_dir, f"{base_name}.7z")

    try:
        # Compress with volume splitting (each volume max size)
        volume_size = f"{int(max_size_mb)}m"
        cmd = [
            cmd_7z,
            "a",
            "-v" + volume_size,  # Volume size
            "-mx=5",  # Compression level (0-9, 5 is balanced)
            archive_path,
            file_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Compression failed: {result.stderr}")
            shutil.rmtree(temp_dir)
            return file_path, False

        # Find all volume files
        volume_files = []
        for f in os.listdir(temp_dir):
            if f.startswith(base_name) and ".7z." in f:
                volume_files.append(os.path.join(temp_dir, f))

        volume_files.sort()  # Ensure correct order

        if not volume_files:
            print("❌ No volume files created")
            shutil.rmtree(temp_dir)
            return file_path, False

        print(f"✅ Compressed into {len(volume_files)} volumes")
        return volume_files, True

    except Exception as e:
        print(f"❌ Compression error: {e}")
        shutil.rmtree(temp_dir)
        return file_path, False


def decompress_7z_file(file_path, output_dir):
    """Decompress 7z file(s)."""
    cmd_7z = check_7z_available()
    if not cmd_7z:
        print("⚠️  7z not available. Cannot decompress files.")
        return False

    try:
        # Extract the archive
        cmd = [cmd_7z, "x", file_path, f"-o{output_dir}", "-y"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Decompression failed: {result.stderr}")
            return False

        print(f"✅ Decompressed: {file_path}")
        return True

    except Exception as e:
        print(f"❌ Decompression error: {e}")
        return False


def detect_and_decompress_archives(download_dir):
    """Detect and decompress 7z archives in the download directory."""
    try:
        # Look for .7z.001 files (first volume of multi-volume archives)
        volume_files = [f for f in os.listdir(download_dir) if f.endswith(".7z.001")]

        for volume_file in volume_files:
            volume_path = os.path.join(download_dir, volume_file)
            print(f"🗜️  Detected multi-volume archive: {volume_file}")

            if decompress_7z_file(volume_path, download_dir):
                # Remove all volume files after successful decompression
                base_name = volume_file.replace(".7z.001", ".7z")
                volume_pattern = base_name + "."

                removed_count = 0
                for f in os.listdir(download_dir):
                    if f.startswith(volume_pattern) and (
                        f.endswith(".001")
                        or f.endswith(".002")
                        or f.endswith(".003")
                        or ".7z.0" in f
                    ):
                        volume_to_remove = os.path.join(download_dir, f)
                        os.remove(volume_to_remove)
                        removed_count += 1

                print(f"🗑️  Removed {removed_count} volume files after decompression")
            else:
                print(f"❌ Failed to decompress {volume_file}")

    except Exception as e:
        print(f"⚠️  Error during archive detection/decompression: {e}")
