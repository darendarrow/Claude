#!/bin/bash
# Reddit Media Downloader — Quick Setup Script
# Run this once after cloning/copying the project files.

set -e

echo "============================================================"
echo "  Reddit Media Downloader — Setup"
echo "============================================================"
echo ""

# Create required directories
mkdir -p data downloads
echo "✓ Created data/ and downloads/ directories"

# Copy .env template if needed
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env from template — please edit it with your credentials"
    else
        echo "⚠ .env.example not found — create .env manually"
    fi
else
    echo "✓ .env already exists"
fi

# Check Python dependencies
if command -v pip &> /dev/null; then
    echo ""
    read -p "Install Python dependencies now? [y/N] " install
    if [[ "$install" =~ ^[Yy]$ ]]; then
        pip install -r requirements.txt
        echo "✓ Dependencies installed"
    fi
fi

# Check ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✓ ffmpeg found (Reddit video audio merging enabled)"
else
    echo "⚠ ffmpeg not found — Reddit videos will be saved without audio"
fi

echo ""
echo "============================================================"
echo "  Setup complete! Next steps:"
echo "============================================================"
echo ""
echo "  1. Edit .env with your Reddit API credentials"
echo "     (Get them at https://www.reddit.com/prefs/apps)"
echo ""
echo "  2. Add your subreddits to SUBREDDITS= in .env"
echo ""
echo "  3. Run:  python reddit_media_downloader.py"
echo ""
echo "  Or with Docker:"
echo "     docker compose build"
echo "     docker compose up -d"
echo ""
