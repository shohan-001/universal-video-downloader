# Universal Video Downloader

A powerful video downloader supporting YouTube, Facebook, Twitter, TikTok, Instagram, and 1000+ other sites. Built with Python and Eel for a native desktop experience.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

## Features

- 🎥 **Video Downloads** - Multiple qualities (4K, 1440p, 1080p, 720p, 480p, 360p)
- 🎵 **Audio Extraction** - Convert to MP3 with 320kbps quality
- 🌐 **1000+ Sites** - YouTube, Facebook, Twitter, TikTok, Instagram, Vimeo & more
- 📋 **Playlist Support** - Download entire playlists or select specific videos
- 🍪 **Cookie Authentication** - Access private/restricted videos
- 🌙 **Dark/Light Theme** - Clean UI with theme toggle
- 📊 **Real-time Progress** - Live download progress, speed, and ETA

## Supported Sites

| Site | Status | Site | Status |
|------|--------|------|--------|
| YouTube | ✅ | TikTok | ✅ |
| Facebook | ✅ | Vimeo | ✅ |
| Twitter/X | ✅ | Twitch | ✅ |
| Instagram | ✅ | Reddit | ✅ |
| SoundCloud | ✅ | Dailymotion | ✅ |
| Bilibili | ✅ | + 1000 more | ✅ |

[Full list of supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## Downloads

Download the latest release from the [Releases](https://github.com/shohan-001/youtube-downloader-pro/releases) page.

| File | Description |
|------|-------------|
| `Universal-Video-Downloader.exe` | Standalone Windows executable |

## Quick Start

### Option 1: Download Executable (Recommended)

1. Download `Universal-Video-Downloader.exe` from [Releases](https://github.com/shohan-001/youtube-downloader-pro/releases)
2. Run the application
3. Paste any video URL and click Download

### Option 2: Run from Source

```bash
git clone https://github.com/shohan-001/youtube-downloader-pro.git
cd youtube-downloader-pro
git checkout universal-downloader
pip install -r requirements.txt
python main.py
```

### Building the Executable

```bash
build_exe.bat
```

## Usage

1. **Paste URL** - Copy any video URL from supported sites
2. **Auto-detect** - The app automatically detects the site
3. **Select Mode** - Choose Video (MP4) or Audio (MP3)
4. **Choose Quality** - Select your preferred quality
5. **Download** - Click "Start Download"

### Supported URL Formats

```
YouTube:    https://www.youtube.com/watch?v=VIDEO_ID
Facebook:   https://www.facebook.com/watch?v=VIDEO_ID
Twitter:    https://twitter.com/user/status/TWEET_ID
TikTok:     https://www.tiktok.com/@user/video/VIDEO_ID
Instagram:  https://www.instagram.com/p/POST_ID/
Vimeo:      https://vimeo.com/VIDEO_ID
... and 1000+ more sites
```

### Cookie Authentication

For private/restricted videos:

1. Open Incognito Window (`Ctrl+Shift+N`)
2. Login to the site
3. Install "Get cookies.txt LOCALLY" extension
4. Export cookies and save as `cookies.txt`
5. In the app, click "Select Cookies File"

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

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/NewFeature`)
3. Commit your changes (`git commit -m 'Add NewFeature'`)
4. Push to the branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful downloading engine supporting 1000+ sites
- [Eel](https://github.com/python-eel/Eel) - Desktop app framework
- [FFmpeg](https://ffmpeg.org/) - Audio/video processing

## Disclaimer

For personal use only. Respect each site's Terms of Service and copyright laws.

---

Made by Shohan
