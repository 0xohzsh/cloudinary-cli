#!/bin/bash

echo "🌤️  Installing Cloudinary CLI Tool..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is required but not installed. Please install git first."
    exit 1
fi

# Clone the repository
echo "📦 Cloning repository..."
git clone https://github.com/0xohzsh/cloudinary-cli.git cloudinary-cli

# Change to the directory
cd cloudinary-cli

# Make install script executable
chmod +x install.sh

# Run the installation
echo "🚀 Running installation..."
./install.sh

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. cd cloudinary-cli"
echo "2. Edit .env with your Cloudinary credentials"
echo "3. Run: python3 main.py --help"
echo ""
echo "For global access, the installer will prompt you during setup."
