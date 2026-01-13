# Universal Video Downloader

A powerful video downloader supporting YouTube, Facebook, Twitter, TikTok, Instagram, and 1000+ other sites. Built with Python and Eel for a native desktop experience.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

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

| Platform | File | Installation |
|----------|------|--------------|
| Windows | `Universal-Video-Downloader.exe` | Run directly |
| macOS | `Universal-Video-Downloader-macOS.dmg` | Open DMG, drag to Applications |
| Linux | `Universal-Video-Downloader-Linux.AppImage` | `chmod +x` then run |

## Quick Start

### Option 1: Download Executable (Recommended)

1. Download the appropriate file for your platform from [Releases](https://github.com/shohan-001/youtube-downloader-pro/releases)
2. Run the application
3. Paste any video URL and click Download

### Option 2: Run from Source

```bash
git clone https://github.com/shohan-001/youtube-downloader-pro.git
cd youtube-downloader-pro
pip install -r requirements.txt
python main.py
```

### Building the Executable

**Windows:**
```bash
build_exe.bat
```

**macOS/Linux:**
```bash
chmod +x build.sh
./build.sh
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

- Windows 10/11, macOS 10.14+, or Linux
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

## 🗺️ Roadmap

### v1.2.0 (Coming Soon)
- [ ] **Batch Downloads** - Download from a list of URLs
- [ ] **Download Queue** - Queue multiple downloads
- [ ] **Download History** - Track previously downloaded videos
- [ ] **Custom Filename Templates** - Choose how files are named

### v1.3.0
- [ ] **Scheduled Downloads** - Set downloads to start at specific times
- [ ] **Subtitles Download** - Download subtitles along with video
- [ ] **Auto-update yt-dlp** - Keep yt-dlp updated automatically
- [ ] **Browser Extension** - One-click download from browser

### v2.0.0 (Future)
- [ ] **macOS & Linux Support** - Cross-platform builds
- [ ] **Video Preview** - Preview before downloading
- [ ] **Format Converter** - Convert downloaded files to other formats
- [ ] **Watch Folders** - Monitor folders for URL files to auto-download

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
