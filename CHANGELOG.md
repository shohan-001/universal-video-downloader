# Changelog

All notable changes to Universal Video Downloader will be documented in this file.

## [2.0.0] - 2026-01-13

### 🎉 Major Release - "Universal"

This is a complete rewrite with a new modern UI and multi-platform support!

### ✨ New Features

- **Multi-Platform Support** - Now available for Windows, macOS, and Linux
- **Playlist Download Improvements**
  - Shows current video being downloaded with thumbnail
  - Displays progress counter (e.g., "3/10 videos")
  - Creates dedicated folder for each playlist
  - Smart handling of YouTube Mix/Radio playlists
- **Enhanced Progress Display**
  - Real-time download speed
  - Accurate ETA calculation
  - File size indicator
- **Modern UI Design**
  - Glass-morphism effects
  - Animated particle background
  - 3D button effects with hover animations
  - Smooth transitions throughout

### 🛠️ Improvements

- **Video Selection Modal** - Select specific videos from playlists with thumbnail previews
- **Better Quality Detection** - Shows all available qualities (4K, 2K, 1080p, etc.)
- **Cookie Authentication** - Support for private/restricted video downloads
- **Auto-Updates** - Check for new versions automatically
- **Speed Optimizations** - Concurrent fragment downloads for faster speeds

### 🐛 Bug Fixes

- Fixed UTF-8 encoding issues in update notifications
- Fixed incorrect video count for YouTube Mix playlists
- Fixed playlist folder naming with special characters
- Improved error handling and user feedback

### 🏗️ Technical Changes

- Migrated to yt-dlp from youtube-dl for better site support
- Added GitHub Actions workflow for automated multi-platform builds
- Improved code structure and maintainability

---

## [1.0.0] - Initial Release

- Basic YouTube video downloading
- MP3 audio extraction
- Simple single-file downloads
