import eel
import yt_dlp
import os
import sys
import json
import threading
import atexit
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

# App Info
APP_NAME = "Universal Video Downloader"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Shohan"
GITHUB_REPO = "shohan-001/universal-video-downloader"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Initialize Eel
eel.init('web')

# Configuration paths
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

APPDATA_DIR = os.path.join(os.environ.get('APPDATA', BASE_DIR), APP_NAME)
os.makedirs(APPDATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')
FFMPEG_DIR = os.path.join(APPDATA_DIR, 'ffmpeg')

# Global variables
download_folder = str(Path.home() / "Downloads")
cookies_file = None
cancel_flag = False
_app_closing = False

# Playlist download tracking
_playlist_current_index = 0
_playlist_total_count = 0
_playlist_current_title = ""
_playlist_entries = []

# Helper function to strip ANSI codes from yt-dlp output
import re
def strip_ansi(text):
    """Remove ANSI escape codes from string"""
    if not text:
        return ""
    ansi_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_pattern.sub('', str(text))

def clean_title(title):
    """Clean up video title by removing social metadata (reactions, comments, etc.)"""
    if not title:
        return "video"
    
    # Remove patterns like "93 reactions · 28 comments |" or "93 reactions · 28 comments"
    title = re.sub(r'\d+\s*(reactions?|likes?|comments?|shares?|views?)\s*(·|\|)?\s*', '', title, flags=re.IGNORECASE)
    
    # Remove leading/trailing special characters and whitespace
    title = re.sub(r'^[\s·|\-:]+', '', title)
    title = re.sub(r'[\s·|\-:]+$', '', title)
    
    # Limit length
    if len(title) > 100:
        title = title[:100]
    
    return title.strip() or "video"

def sanitize_folder_name(name):
    """Sanitize folder name by removing invalid characters"""
    if not name:
        return "playlist"
    # Remove characters invalid for Windows folder names
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', name)
    # Remove trailing periods and spaces
    sanitized = sanitized.rstrip('. ')
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized.strip() or "playlist"

# Popular supported sites (yt-dlp supports 1000+ sites)
SUPPORTED_SITES = {
    'youtube.com': 'YouTube',
    'youtu.be': 'YouTube',
    'music.youtube.com': 'YouTube Music',
    'facebook.com': 'Facebook',
    'fb.watch': 'Facebook',
    'twitter.com': 'Twitter/X',
    'x.com': 'Twitter/X',
    'instagram.com': 'Instagram',
    'tiktok.com': 'TikTok',
    'vimeo.com': 'Vimeo',
    'dailymotion.com': 'Dailymotion',
    'twitch.tv': 'Twitch',
    'reddit.com': 'Reddit',
    'soundcloud.com': 'SoundCloud',
    'bilibili.com': 'Bilibili',
    'nicovideo.jp': 'Niconico',
    'pornhub.com': 'Pornhub',
    'xvideos.com': 'XVideos',
    'rumble.com': 'Rumble',
    'bitchute.com': 'BitChute',
    'odysee.com': 'Odysee',
    'bandcamp.com': 'Bandcamp',
    'mixcloud.com': 'Mixcloud',
}

def force_exit(route=None, sockets=None):
    print(f"[App] force_exit called! Route: {route}, Sockets: {sockets}")
    global _app_closing
    if _app_closing:
        return
    _app_closing = True
    print("[App] Exiting...")
    os._exit(0)

# NOTE: Removed atexit.register(force_exit) - it was causing premature exits

# Browser detection functions
def find_edge_path():
    paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def find_chrome_path():
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def find_brave_path():
    paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def find_any_chromium_browser():
    for finder in [find_edge_path, find_chrome_path, find_brave_path]:
        path = finder()
        if path:
            return path
    return None

# Config management
def load_config():
    global download_folder, cookies_file
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                download_folder = config.get('download_folder', str(Path.home() / "Downloads"))
                cookies_file = config.get('cookies_file', None)
    except Exception as e:
        print(f"[Config] Error loading: {e}")

def save_config():
    try:
        config = {
            'download_folder': download_folder,
            'cookies_file': cookies_file
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[Config] Error saving: {e}")

@eel.expose
def get_config():
    """Return current config for JavaScript"""
    return {
        'download_folder': download_folder,
        'cookies_file': cookies_file
    }

# FFmpeg functions
def get_ffmpeg_path():
    ffmpeg_exe = os.path.join(FFMPEG_DIR, 'ffmpeg.exe')
    if os.path.exists(ffmpeg_exe):
        return FFMPEG_DIR
    if shutil.which('ffmpeg'):
        return os.path.dirname(shutil.which('ffmpeg'))
    return None

@eel.expose
def check_ffmpeg():
    return get_ffmpeg_path() is not None

@eel.expose
def install_ffmpeg():
    try:
        eel.update_ffmpeg_status("Downloading FFmpeg...")
        os.makedirs(FFMPEG_DIR, exist_ok=True)
        
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = os.path.join(FFMPEG_DIR, "ffmpeg.zip")
        
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        
        eel.update_ffmpeg_status("Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(FFMPEG_DIR)
        
        # Find and move ffmpeg.exe
        for root, dirs, files in os.walk(FFMPEG_DIR):
            if 'ffmpeg.exe' in files:
                for f in ['ffmpeg.exe', 'ffprobe.exe']:
                    src = os.path.join(root, f)
                    dst = os.path.join(FFMPEG_DIR, f)
                    if os.path.exists(src) and src != dst:
                        shutil.move(src, dst)
                break
        
        os.remove(zip_path)
        eel.update_ffmpeg_status("FFmpeg installed!")
        return True
    except Exception as e:
        eel.update_ffmpeg_status(f"Error: {str(e)}")
        return False

# Exposed functions
@eel.expose
def get_app_version():
    return APP_VERSION

@eel.expose
def get_app_name():
    return APP_NAME

@eel.expose
def check_for_updates(check_nightly=True):
    """Check GitHub for latest release (stable or nightly)"""
    try:
        import urllib.request
        import json
        
        # Check stable release first
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={'User-Agent': 'Universal-Video-Downloader'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            stable_data = json.loads(response.read().decode())
        
        stable_version = stable_data.get('tag_name', '').replace('v', '').replace('-universal', '')
        current_version = APP_VERSION
        
        # Compare versions
        def parse_version(v):
            try:
                # Handle versions like "1.1.0" 
                parts = v.split('.')
                return tuple(map(int, parts[:3]))
            except:
                return (0, 0, 0)
        
        stable_is_newer = parse_version(stable_version) > parse_version(current_version)
        
        # Find download URL for stable exe
        stable_download_url = None
        for asset in stable_data.get('assets', []):
            if asset['name'].endswith('.exe'):
                stable_download_url = asset['browser_download_url']
                break
        
        # Check nightly release if enabled
        nightly_data = None
        nightly_download_url = None
        nightly_is_newer = False
        nightly_commit = None
        
        if check_nightly:
            try:
                nightly_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/nightly"
                req_nightly = urllib.request.Request(
                    nightly_url,
                    headers={'User-Agent': 'Universal-Video-Downloader'}
                )
                
                with urllib.request.urlopen(req_nightly, timeout=10) as response:
                    nightly_data = json.loads(response.read().decode())
                
                # Get nightly commit from body
                nightly_body = nightly_data.get('body', '')
                if 'Commit:' in nightly_body:
                    nightly_commit = nightly_body.split('Commit:')[1].strip()[:7]
                
                # Find nightly exe
                for asset in nightly_data.get('assets', []):
                    if asset['name'].endswith('.exe'):
                        nightly_download_url = asset['browser_download_url']
                        break
                
                # Nightly is "newer" if it exists and has a different publish date
                if nightly_download_url:
                    nightly_is_newer = True
            except:
                pass  # Nightly may not exist
        
        # Determine which update to offer (prefer stable if available)
        update_available = stable_is_newer or nightly_is_newer
        download_url = stable_download_url if stable_is_newer else nightly_download_url
        version_info = stable_version if stable_is_newer else f"nightly ({nightly_commit or 'latest'})"
        is_nightly = not stable_is_newer and nightly_is_newer
        
        return {
            'success': True,
            'current_version': current_version,
            'latest_version': version_info,
            'update_available': update_available,
            'download_url': download_url,
            'release_notes': stable_data.get('body', '') if stable_is_newer else (nightly_data.get('body', '') if nightly_data else ''),
            'release_url': stable_data.get('html_url', '') if stable_is_newer else (nightly_data.get('html_url', '') if nightly_data else ''),
            'is_nightly': is_nightly
        }
    except Exception as e:
        print(f"[Update] Check failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'current_version': APP_VERSION,
            'update_available': False,
            'is_nightly': False
        }

@eel.expose
def download_update(download_url):
    """Download the update in background"""
    def download_thread():
        try:
            import urllib.request
            
            # Download to temp location
            update_path = os.path.join(APPDATA_DIR, 'update.exe')
            
            def progress_hook(count, block_size, total_size):
                percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
                eel.update_download_progress(min(percent, 100))
            
            eel.update_download_progress(0)
            urllib.request.urlretrieve(download_url, update_path, progress_hook)
            eel.update_download_progress(100)
            
            eel.update_download_complete(True, update_path)
        except Exception as e:
            print(f"[Update] Download failed: {e}")
            eel.update_download_complete(False, str(e))
    
    thread = threading.Thread(target=download_thread, daemon=True)
    thread.start()
    return True

@eel.expose
def apply_update(update_path):
    """Apply the downloaded update"""
    try:
        if not os.path.exists(update_path):
            return {'success': False, 'error': 'Update file not found'}
        
        # Create a batch script to replace exe after app closes
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
        else:
            return {'success': False, 'error': 'Cannot update in development mode'}
        
        batch_script = os.path.join(APPDATA_DIR, 'update.bat')
        
        with open(batch_script, 'w') as f:
            f.write('@echo off\n')
            f.write('echo Updating Universal Video Downloader...\n')
            f.write('timeout /t 2 /nobreak >nul\n')
            f.write(f'copy /Y "{update_path}" "{current_exe}"\n')
            f.write(f'del "{update_path}"\n')
            f.write(f'start "" "{current_exe}"\n')
            f.write(f'del "%~f0"\n')
        
        # Run the batch script and exit
        subprocess.Popen(['cmd', '/c', batch_script], 
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Exit the app
        force_exit()
        
        return {'success': True}
    except Exception as e:
        print(f"[Update] Apply failed: {e}")
        return {'success': False, 'error': str(e)}

@eel.expose
def get_download_folder():
    return download_folder

@eel.expose
def set_download_folder(folder):
    global download_folder
    download_folder = folder
    save_config()
    return True

@eel.expose
def set_cookies_file(path):
    global cookies_file
    cookies_file = path
    save_config()
    return True

@eel.expose
def get_cookies_file():
    return cookies_file

@eel.expose
def open_download_folder():
    if os.path.exists(download_folder):
        os.startfile(download_folder)

@eel.expose
def select_cookies_file():
    """Open file dialog to select cookies.txt file"""
    global cookies_file
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title="Select Cookies File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        root.destroy()
        
        if file_path:
            cookies_file = file_path
            save_config()
            return {'success': True, 'path': file_path}
        return {'success': False, 'path': ''}
    except Exception as e:
        print(f"[Error] select_cookies_file: {e}")
        return {'success': False, 'path': '', 'error': str(e)}

@eel.expose
def select_download_folder():
    """Open folder dialog to select download folder"""
    global download_folder
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        folder_path = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=download_folder
        )
        
        root.destroy()
        
        if folder_path:
            download_folder = folder_path
            save_config()
            return {'success': True, 'path': folder_path}
        return {'success': False, 'path': ''}
    except Exception as e:
        print(f"[Error] select_download_folder: {e}")
        return {'success': False, 'path': '', 'error': str(e)}

@eel.expose
def detect_site(url):
    """Detect the site from URL and return site info"""
    url_lower = url.lower()
    for domain, name in SUPPORTED_SITES.items():
        if domain in url_lower:
            return {'detected': True, 'site': name, 'domain': domain}
    # For unknown sites, yt-dlp will try to extract anyway
    return {'detected': False, 'site': 'Unknown', 'domain': 'auto-detect'}

@eel.expose
def get_supported_sites():
    """Return list of popular supported sites"""
    return list(set(SUPPORTED_SITES.values()))

@eel.expose
def fetch_video_info(url):
    """Fetch video info from any supported site"""
    try:
        print(f"[Info] Fetching: {url}")
        
        # Check if this is a YouTube Mix/Radio playlist (dynamically generated)
        is_youtube_mix = 'list=RD' in url or 'list=RDMM' in url
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': True,  # Fast extraction
            'socket_timeout': 30,
        }
        
        # Limit YouTube Mix playlists since they're dynamically generated (infinite)
        if is_youtube_mix:
            ydl_opts['playlist_end'] = 50  # Only get first 50 videos
            print(f"[Info] YouTube Mix detected - limiting to 50 entries")
        
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        if not info:
            return {'success': False, 'error': 'Could not fetch info'}
        
        # Check if playlist
        is_playlist = info.get('_type') == 'playlist'
        entries_data = []
        playlist_thumbnail = None
        
        if is_playlist:
            entries = info.get('entries', [])
            print(f"[Info] Playlist detected with {len(entries)} raw entries")
            
            # Get thumbnail from first valid entry if available
            for entry in entries:
                if entry and entry.get('id'):
                    playlist_thumbnail = entry.get('thumbnail') or (entry.get('thumbnails', [{}])[0].get('url') if entry.get('thumbnails') else None)
                    if playlist_thumbnail:
                        break
            
            # Get all VALID entries (filter out None and placeholder entries)
            for i, e in enumerate(entries):
                # Only include entries with valid ID and title
                if e and e.get('id'):
                    title = e.get('title') or e.get('id', 'Unknown Video')
                    # Skip entries that are just video IDs (placeholders)
                    if title and title != '[Deleted video]' and title != '[Private video]':
                        # Format duration if available
                        duration_secs = e.get('duration')
                        if duration_secs:
                            mins, secs = divmod(int(duration_secs), 60)
                            duration_str = f"{mins}:{secs:02d}"
                        else:
                            duration_str = None
                        
                        entries_data.append({
                            'index': len(entries_data),  # Use actual index in filtered list
                            'original_index': i,  # Keep original index for yt-dlp
                            'id': e.get('id'),
                            'title': title,
                            'duration': duration_secs,
                            'duration_str': duration_str,
                            'uploader': e.get('uploader') or e.get('channel'),
                            'thumbnail': e.get('thumbnail') or f"https://i.ytimg.com/vi/{e.get('id')}/mqdefault.jpg"
                        })
            
            print(f"[Info] Valid playlist entries: {len(entries_data)}")
        
        # Get formats for quality detection
        available_qualities = ['Best']
        if 'formats' in info:
            heights = set()
            for f in info['formats']:
                if f.get('vcodec') != 'none' and f.get('height'):
                    heights.add(f['height'])
            
            for h in sorted(list(heights), reverse=True):
                if h >= 2160:
                    available_qualities.append(f'{h}p (4K)')
                elif h >= 1440:
                    available_qualities.append(f'{h}p (2K)')
                else:
                    available_qualities.append(f'{h}p')
        
        # Format duration
        duration_secs = info.get('duration', 0) or 0
        if duration_secs:
            hours = int(duration_secs // 3600)
            minutes = int((duration_secs % 3600) // 60)
            seconds = int(duration_secs % 60)
            duration = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
        else:
            duration = "--:--"
        
        # Detect site
        site_info = detect_site(url)
        
        result = {
            'success': True,
            'title': info.get('title', 'Unknown'),
            'channel': info.get('channel') or info.get('uploader') or 'Unknown',
            'duration': duration,
            'thumbnail': info.get('thumbnail') or playlist_thumbnail or '',
            'qualities': available_qualities if len(available_qualities) > 1 else ['Best', '1080p', '720p', '480p', '360p'],
            'is_playlist': is_playlist,
            'is_mix': is_youtube_mix,  # YouTube Mix/Radio playlist flag
            'playlist_title': info.get('title', '') if is_playlist else '',
            'playlist_count': len(entries_data) if is_playlist else 0,
            'entries': entries_data,
            'site': site_info['site'],
            'extractor': info.get('extractor', 'Unknown'),
        }
        
        print(f"[Info] Site: {result['site']}, Title: {result['title']}")
        return result
        
    except Exception as e:
        print(f"[Error] fetch_video_info: {e}")
        return {'success': False, 'error': str(e)}

@eel.expose
def start_download(url, mode='video', quality='Best', playlist_mode='single', selected_indices=None):
    """Download video/audio from any supported site"""
    global cancel_flag, _playlist_current_index, _playlist_total_count, _playlist_current_title, _playlist_entries
    cancel_flag = False
    _playlist_current_index = 0
    _playlist_total_count = 0
    _playlist_current_title = ""
    _playlist_entries = []
    
    def download_thread():
        global cancel_flag, _playlist_current_index, _playlist_total_count, _playlist_current_title, _playlist_entries
        try:
            print(f"[Download] Starting: {url}")
            print(f"[Download] Mode: {mode}, Quality: {quality}, Playlist Mode: {playlist_mode}")
            
            ffmpeg_path = get_ffmpeg_path()
            target_folder = download_folder
            
            # For playlist downloads, create a subfolder with playlist name
            is_playlist_download = playlist_mode in ['all', 'select']
            
            if is_playlist_download:
                # Fetch playlist info to get title and entries
                fetch_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                    'extract_flat': True,
                }
                if cookies_file and os.path.exists(cookies_file):
                    fetch_opts['cookiefile'] = cookies_file
                
                with yt_dlp.YoutubeDL(fetch_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                
                if info and info.get('_type') == 'playlist':
                    playlist_title = info.get('title', 'Playlist')
                    entries = info.get('entries', [])
                    
                    # If selecting specific indices, filter entries
                    if playlist_mode == 'select' and selected_indices:
                        _playlist_entries = [entries[i] for i in selected_indices if i < len(entries)]
                        _playlist_total_count = len(_playlist_entries)
                    else:
                        _playlist_entries = entries
                        _playlist_total_count = len(entries)
                    
                    # Create subfolder for playlist
                    folder_name = sanitize_folder_name(playlist_title)
                    target_folder = os.path.join(download_folder, folder_name)
                    os.makedirs(target_folder, exist_ok=True)
                    print(f"[Download] Created playlist folder: {target_folder}")
                    print(f"[Download] Total videos to download: {_playlist_total_count}")
                    
                    # Send initial playlist progress
                    eel.update_playlist_progress(0, _playlist_total_count, "Starting...", True)
            
            # Determine if we need title cleaning (only for Facebook/social sites with metadata in title)
            needs_title_cleaning = any(site in url.lower() for site in ['facebook.com', 'fb.watch', 'fb.com'])
            
            if needs_title_cleaning and not is_playlist_download:
                # Pre-fetch and clean title for Facebook-type sites
                with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True, 'noplaylist': True}) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        raw_title = info.get('title', 'video')
                        cleaned_title = clean_title(raw_title)
                        print(f"[Download] Original title: {raw_title[:50]}...")
                        print(f"[Download] Cleaned title: {cleaned_title}")
                        outtmpl = os.path.join(target_folder, f'{cleaned_title}.%(ext)s')
                    except:
                        outtmpl = os.path.join(target_folder, '%(title).100s.%(ext)s')
            else:
                # Use yt-dlp's default title handling
                outtmpl = os.path.join(target_folder, '%(title).100s.%(ext)s')
            
            # Progress hook for playlist tracking
            def playlist_progress_hook(d):
                global _playlist_current_index, _playlist_current_title
                
                # Call the main progress hook
                progress_hook(d)
                
                if is_playlist_download and d['status'] == 'downloading':
                    # Extract current video title from filename if available
                    filename = d.get('filename', '')
                    if filename:
                        base = os.path.basename(filename)
                        title = os.path.splitext(base)[0].replace('_', ' ')[:50]
                        if title and title != _playlist_current_title:
                            _playlist_current_title = title
                            eel.update_playlist_progress(_playlist_current_index, _playlist_total_count, title, True)
                
                if is_playlist_download and d['status'] == 'finished':
                    _playlist_current_index += 1
                    print(f"[Download] Completed video {_playlist_current_index}/{_playlist_total_count}")
                    eel.update_playlist_progress(_playlist_current_index, _playlist_total_count, _playlist_current_title, True)
            
            # Base options
            ydl_opts = {
                'outtmpl': outtmpl,
                'restrictfilenames': True,  # Replace special chars with underscores
                'progress_hooks': [playlist_progress_hook],
                'quiet': True,
                'no_warnings': True,
                # Speed optimizations
                'concurrent_fragment_downloads': 4,  # Download 4 fragments simultaneously
                'buffersize': 1024 * 16,  # 16KB buffer
                'http_chunk_size': 1024 * 1024 * 10,  # 10MB chunks
                'retries': 10,
                'fragment_retries': 10,
            }
            
            if ffmpeg_path:
                ydl_opts['ffmpeg_location'] = ffmpeg_path
            
            if cookies_file and os.path.exists(cookies_file):
                ydl_opts['cookiefile'] = cookies_file
            
            # Playlist handling
            if playlist_mode == 'single':
                ydl_opts['noplaylist'] = True
            elif playlist_mode == 'all':
                ydl_opts['noplaylist'] = False
            elif playlist_mode == 'select' and selected_indices:
                indices = [str(i + 1) for i in selected_indices]
                ydl_opts['playlist_items'] = ','.join(indices)
            
            # Format selection
            if mode == 'audio':
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }]
            else:
                # Handle video quality selection
                if quality.lower() == 'best':
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                else:
                    # Extract numeric height from quality string (e.g., "1080p", "720p (2K)")
                    height = ''.join(filter(str.isdigit, quality.split('p')[0].split(' ')[0]))
                    if height:
                        ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
                    else:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                
                ydl_opts['merge_output_format'] = 'mp4'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if not cancel_flag:
                # Send final playlist progress
                if is_playlist_download:
                    eel.update_playlist_progress(_playlist_current_index, _playlist_total_count, "All downloads complete!", False)
                eel.download_complete(True, "Download completed!")
            
        except Exception as e:
            if not cancel_flag:
                error_msg = str(e)
                print(f"[Error] Download: {error_msg}")
                eel.download_complete(False, error_msg)
    
    thread = threading.Thread(target=download_thread, daemon=True)
    thread.start()
    return True

# Global for tracking download process
_current_ydl = None

def progress_hook(d):
    global cancel_flag
    if cancel_flag:
        raise yt_dlp.utils.DownloadCancelled("Download cancelled by user")
    global _current_ydl # Changed from cancel_flag to _current_ydl
    
    if d['status'] == 'downloading':
        try:
            # Calculate progress
            if d.get('total_bytes'):
                p = d['downloaded_bytes'] / d['total_bytes'] * 100
            elif d.get('total_bytes_estimate'):
                p = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
            else:
                p = 0
                
            percentage = f"{p:.1f}%"
            
            # Get speed
            speed = d.get('_speed_str', '')
            if not speed:
                speed_val = d.get('speed', 0)
                if speed_val:
                    if speed_val > 1024 * 1024:
                        speed = f"{speed_val / (1024 * 1024):.2f}MiB/s"
                    elif speed_val > 1024:
                        speed = f"{speed_val / 1024:.2f}KiB/s"
                    else:
                        speed = f"{speed_val:.0f}B/s"
                else:
                    speed = "-"
            speed = strip_ansi(speed.strip())
            
            # Get ETA
            # Get ETA
            eta = d.get('_eta_str', '')
            if not eta:
                eta_val = d.get('eta', 0)
                if eta_val:
                    mins, secs = divmod(int(eta_val), 60)
                    eta = f"{mins:02d}:{secs:02d}"
            eta = strip_ansi(str(eta).strip())
            
            # Get size
            size = ""
            if d.get('total_bytes'):
                size = f"{d['total_bytes'] / (1024 * 1024):.2f}MiB"
            elif d.get('total_bytes_estimate'):
                size = f"~{d['total_bytes_estimate'] / (1024 * 1024):.2f}MiB"
            elif d.get('downloaded_bytes'):
                 size = f"{d['downloaded_bytes'] / (1024 * 1024):.2f}MiB+"
            
            # Send to UI
            eel.update_progress(percentage, speed, eta, size)
        except Exception as e:
            print(f"[Error] Progress hook error: {e}")

@eel.expose
def cancel_download():
    global cancel_flag, _current_ydl
    cancel_flag = True
    # Immediately notify UI
    eel.download_complete(False, "Download cancelled")
    return True

# Main entry point
if __name__ == '__main__':
    print("--- Starting Universal Video Downloader v2.1 ---")
    load_config()
    
    browser_path = find_any_chromium_browser()
    
    try:
        if browser_path:
            eel.start('index.html', 
                     mode='custom',
                     cmdline_args=[
                         browser_path, 
                         '--app=http://localhost:8000/index.html',
                         '--enable-features=Vulkan',
                         '--force-device-scale-factor=1'
                     ],
                     size=(800, 600),
                     port=8000,
                     shutdown_delay=30.0,  # Allow 30 seconds for pending requests
                     close_callback=force_exit)
        else:
            print("[App] No Chromium browser found, using default browser")
            eel.start('index.html', 
                     mode='default',
                     size=(800, 600),
                     port=8000,
                     shutdown_delay=30.0,  # Allow 30 seconds for pending requests
                     close_callback=force_exit)
    except (SystemExit, KeyboardInterrupt):
        pass
    finally:
        force_exit()
