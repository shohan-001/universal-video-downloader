#!/bin/bash
# ========================================
#   Universal Video Downloader Build Script
#   For macOS and Linux
# ========================================

set -e

echo "========================================"
echo "  Universal Video Downloader Build"
echo "========================================"
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=Linux;;
    Darwin*)    PLATFORM=macOS;;
    *)          PLATFORM="UNKNOWN:${OS}"
esac

echo "Detected platform: $PLATFORM"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
pip3 install pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist build

# Build based on platform
if [ "$PLATFORM" = "macOS" ]; then
    echo "Building for macOS..."
    
    # Create icns from ico if needed
    if [ ! -f "icon.icns" ] && [ -f "icon.ico" ]; then
        echo "Converting icon to icns..."
        mkdir -p icon.iconset
        sips -s format png icon.ico --out icon.iconset/icon_256x256.png 2>/dev/null || true
        iconutil -c icns icon.iconset -o icon.icns 2>/dev/null || echo "Warning: Could not create icns"
        rm -rf icon.iconset
    fi
    
    python3 -m PyInstaller --noconfirm --onedir --windowed \
        --icon=icon.icns \
        --name="Universal-Video-Downloader" \
        --add-data="web:web" \
        --hidden-import=eel \
        --hidden-import=yt_dlp \
        --hidden-import=bottle_websocket \
        --osx-bundle-identifier=com.universalvideodownloader.app \
        main.py
    
    # Create DMG
    echo "Creating DMG..."
    mkdir -p dmg-contents
    cp -r "dist/Universal-Video-Downloader.app" dmg-contents/
    ln -s /Applications dmg-contents/Applications
    hdiutil create -volname "Universal Video Downloader" \
        -srcfolder dmg-contents \
        -ov -format UDZO \
        "dist/Universal-Video-Downloader.dmg"
    rm -rf dmg-contents
    
    echo ""
    echo "========================================"
    echo "  BUILD SUCCESSFUL!"
    echo "========================================"
    echo ""
    echo "App:  dist/Universal-Video-Downloader.app"
    echo "DMG:  dist/Universal-Video-Downloader.dmg"
    
elif [ "$PLATFORM" = "Linux" ]; then
    echo "Building for Linux..."
    
    python3 -m PyInstaller --noconfirm --onedir \
        --name="Universal-Video-Downloader" \
        --add-data="web:web" \
        --hidden-import=eel \
        --hidden-import=yt_dlp \
        --hidden-import=bottle_websocket \
        main.py
    
    echo ""
    echo "========================================"
    echo "  BUILD SUCCESSFUL!"
    echo "========================================"
    echo ""
    echo "Executable: dist/Universal-Video-Downloader/Universal-Video-Downloader"
    echo ""
    echo "To create AppImage, install appimagetool and run:"
    echo "  wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "  chmod +x appimagetool-x86_64.AppImage"
    
else
    echo "ERROR: Unsupported platform: $PLATFORM"
    echo "For Windows, use build_exe.bat"
    exit 1
fi

echo ""
