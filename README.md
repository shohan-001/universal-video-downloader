# YouTube Downloader Pro

A modern YouTube video and playlist downloader with a clean dark-themed UI. Built with Python and Eel for a native-like desktop experience.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

## Features

- **Video Downloads** - Multiple qualities (4K, 1440p, 1080p, 720p, 480p, 360p)
- **Audio Extraction** - Convert to MP3 with 320kbps quality
- **Playlist Support** - Download entire playlists or select specific videos
- **Cookie Authentication** - Access age-restricted and private videos
- **Dark/Light Theme** - Clean UI with theme toggle
- **Real-time Progress** - Live download progress, speed, and ETA
- **Custom Save Location** - Choose where to save downloads

## Downloads

Download the latest release from the [Releases](https://github.com/shohan-001/youtube-downloader-pro/releases) page.

| File | Description |
|------|-------------|
| `YT-Downloader-Pro.exe` | Standalone Windows executable (no installation required) |

## Quick Start

### Option 1: Download Executable (Recommended)

1. Download `YT-Downloader-Pro.exe` from [Releases](https://github.com/shohan-001/youtube-downloader-pro/releases)
2. Run the application
3. Paste a YouTube URL and click Download

### Option 2: Run from Source

```bash
git clone https://github.com/shohan-001/youtube-downloader-pro.git
cd youtube-downloader-pro
pip install -r requirements.txt
python main.py
```

### Building the Executable

```bash
build_exe.bat
```

The executable will be created in the `dist/` folder.

## Usage

1. **Paste URL** - Copy any YouTube video or playlist URL
2. **Select Mode** - Choose Video (MP4) or Audio (MP3)
3. **Choose Quality** - Select your preferred quality
4. **Download** - Click "Start Download"

### Playlist Downloads

- **Download this video only** - Downloads just the current video
- **Download entire playlist** - Downloads all videos
- **Select specific videos** - Choose which videos to download

### Supported URL Formats

| Format | Example |
|--------|---------|
| Standard Video | `https://www.youtube.com/watch?v=VIDEO_ID` |
| Short URL | `https://youtu.be/VIDEO_ID` |
| Playlist | `https://www.youtube.com/playlist?list=PLAYLIST_ID` |
| Video in Playlist | `https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID` |
| YouTube Music | `https://music.youtube.com/watch?v=VIDEO_ID` |
| Video ID Only | `dQw4w9WgXcQ` (11-character ID) |

### Video Quality Options

| Quality | Resolution | Best For |
|---------|------------|----------|
| Best | Highest available | Maximum quality |
| 4K (2160p) | 3840×2160 | Large displays |
| 2K (1440p) | 2560×1440 | High-end monitors |
| 1080p | 1920×1080 | Standard HD |
| 720p | 1280×720 | Balanced quality/size |
| 480p | 854×480 | Mobile devices |
| 360p | 640×360 | Slow connections |

### Audio Quality (MP3)

| Quality | Bitrate | File Size (per minute) |
|---------|---------|------------------------|
| Best | 320 kbps | ~2.4 MB |
| High | 256 kbps | ~1.9 MB |
| Medium | 192 kbps | ~1.4 MB |
| Low | 128 kbps | ~0.9 MB |

**Note:** Audio extraction requires FFmpeg. The app will prompt you to install it automatically if not found.

### Cookie Authentication

For age-restricted or private videos, you need cookies from your YouTube login.

**Long-Lasting Cookie Method (Recommended):**

Using an Incognito/Private window creates cookies that last longer:

1. Open Incognito Window (Ctrl+Shift+N in Chrome/Edge)
2. Login to YouTube
3. Install a cookie export extension like "Get cookies.txt LOCALLY"
4. Export cookies for youtube.com and save as `cookies.txt`
5. In the app, click "Select Cookies File" and choose your file

**Why Incognito?** These cookies typically last 1-2 weeks vs hours for regular cookies.

**Note:** Keep your cookies file private - it contains your login session.

## Requirements

- Windows 10/11
- Microsoft Edge, Chrome, Brave, or any modern browser

## Project Structure

```
youtube-downloader-pro/
├── main.py              # Main application
├── requirements.txt     # Python dependencies
├── build_exe.bat        # Build script
├── icon.ico             # App icon
└── web/
    ├── index.html
    ├── style.css
    └── script.js
```

## Configuration

Config stored in: `%APPDATA%/YouTube Downloader Pro/config.json`

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| App won't start | Make sure you have a modern browser installed (Edge, Chrome, or Brave) |
| Download stuck at 0% | Check your internet connection. Try a different video. |
| "Video unavailable" error | Video may be region-locked, private, or deleted. Try using cookies. |
| Age-restricted video fails | Export and use cookies from your logged-in YouTube session. |
| No audio in downloaded video | FFmpeg issue - reinstall FFmpeg or let the app install it automatically. |
| MP3 conversion fails | FFmpeg is required. Click "Install FFmpeg" when prompted. |
| Slow download speed | YouTube may be throttling. Try during off-peak hours. |
| "HTTP Error 429" | Too many requests - wait a few minutes and try again. |

### Cookie Issues

| Issue | Solution |
|-------|----------|
| Cookies expired quickly | Use the Incognito Tab method |
| "Sign in required" error | Re-export fresh cookies from your browser |
| Private video access denied | Ensure your account has access to the video |

### Performance Tips

- Use SSD for download folder for faster write speeds
- Wired connection is faster than WiFi for large downloads
- Close other downloads to maximize bandwidth
- Update yt-dlp if downloads consistently fail: `pip install -U yt-dlp`

### Still Having Issues?

1. Check if the video plays in your browser first
2. Try downloading a different video to isolate the issue
3. Update to the latest version
4. [Open an issue](https://github.com/shohan-001/youtube-downloader-pro/issues) on GitHub

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloading engine
- [Eel](https://github.com/python-eel/Eel) - Desktop app framework
- [FFmpeg](https://ffmpeg.org/) - Audio/video processing

## Disclaimer

For personal use only. Respect YouTube's Terms of Service and copyright laws.

---

Made by Shohan
