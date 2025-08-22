#!/bin/bash

echo "🌤️  Installing Cloudinary CLI Tool..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if 7z is available (for large file compression)
echo "🔍 Checking for 7z compression tool..."
if command -v 7zz &> /dev/null; then
    echo "✅ 7zz found (macOS p7zip)"
elif command -v 7z &> /dev/null; then
    echo "✅ 7z found (Linux/Windows)"
elif command -v 7za &> /dev/null; then
    echo "✅ 7za found (alternative)"
else
    echo "⚠️  7z not found. Large file compression will be disabled."
    echo "   To enable compression, install 7z:"
    echo "   - macOS: brew install p7zip"
    echo "   - Linux: sudo apt-get install p7zip-full"
    echo "   - Windows: Download from 7-zip.org"
    echo ""
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "❌ requirements.txt not found. Please ensure you're in the correct directory."
    exit 1
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies. Please check your internet connection and try again."
    exit 1
fi

echo "✅ Dependencies installed successfully:"
pip list | grep -E "(cloudinary|dotenv|requests)"

# Test 7z functionality
echo ""
echo "🧪 Testing 7z compression functionality..."
python3 -c "
import subprocess
import sys

def check_7z():
    commands = ['7zz', '7z', '7za']
    for cmd in commands:
        try:
            subprocess.run([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return cmd
        except FileNotFoundError:
            continue
    return None

cmd = check_7z()
if cmd:
    print(f'✅ 7z compression ready ({cmd})')
else:
    print('⚠️  7z not available - large files will be uploaded as-is')
    print('   Install with: brew install p7zip (macOS) or apt-get install p7zip-full (Linux)')
"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your Cloudinary credentials!"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Local installation complete!"

# Ask if user wants global access
echo ""
read -p "Do you want to make this tool globally accessible? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌐 Setting up global access..."

    # Get the current directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Create the global wrapper script
    cat > cloudinary-cli << EOF2
#!/bin/bash
cd "$SCRIPT_DIR"
source .venv/bin/activate
python3 main.py "\$@"
EOF2

    # Make it executable
    chmod +x cloudinary-cli

    # Move to /usr/local/bin
    echo "📁 Installing to /usr/local/bin (requires sudo)..."
    sudo mv cloudinary-cli /usr/local/bin/

    echo ""
    echo "✅ Global installation complete!"
    echo ""
    echo "You can now use 'cloudinary-cli' from anywhere:"
    echo "  cloudinary-cli upload ./images my_photos"
    echo "  cloudinary-cli list"
    echo "  cloudinary-cli download"
    echo ""
    echo "To remove global access:"
    echo "  sudo rm /usr/local/bin/cloudinary-cli"
else
    echo ""
    echo "To use the tool locally:"
    echo "  source .venv/bin/activate"
    echo "  python3 main.py upload ./images my_photos"
    echo "  deactivate"
fi

echo ""
echo "Next steps:"
echo "1. Edit .env file with your Cloudinary credentials"
echo "2. Test the installation: ./test-installation.sh"
echo ""
echo "💡 Optional: Install 7z for large file compression:"
echo "   - macOS: brew install p7zip"
echo "   - Linux: sudo apt-get install p7zip-full"
echo "   - Windows: Download from 7-zip.org"
