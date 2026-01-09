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
APP_VERSION = "1.1.0"
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

def force_exit():
    global _app_closing
    if _app_closing:
        return
    _app_closing = True
    os._exit(0)

atexit.register(force_exit)

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
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': 'in_playlist',
        }
        
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        if not info:
            return {'success': False, 'error': 'Could not fetch info'}
        
        # Check if playlist
        is_playlist = info.get('_type') == 'playlist'
        
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
            'thumbnail': info.get('thumbnail', ''),
            'qualities': available_qualities if len(available_qualities) > 1 else ['Best', '1080p', '720p', '480p', '360p'],
            'is_playlist': is_playlist,
            'playlist_title': info.get('title', '') if is_playlist else '',
            'playlist_count': len(info.get('entries', [])) if is_playlist else 0,
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
    global cancel_flag
    cancel_flag = False
    
    def download_thread():
        global cancel_flag
        try:
            print(f"[Download] Starting: {url}")
            print(f"[Download] Mode: {mode}, Quality: {quality}")
            
            ffmpeg_path = get_ffmpeg_path()
            
            # Base options
            ydl_opts = {
                'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
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
                if quality == 'Best':
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                else:
                    height = quality.replace('p', '').split(' ')[0]
                    ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
                
                ydl_opts['merge_output_format'] = 'mp4'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if not cancel_flag:
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
    
    if d['status'] == 'downloading':
        try:
            # Get percent - try multiple fields
            percent = d.get('_percent_str', '')
            if not percent:
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total > 0:
                    percent = f"{(downloaded / total) * 100:.1f}%"
                else:
                    percent = "0%"
            percent = percent.strip()
            
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
            speed = speed.strip()
            
            # Get ETA
            eta = d.get('_eta_str', '')
            if not eta:
                eta_val = d.get('eta', 0)
                if eta_val:
                    mins, secs = divmod(int(eta_val), 60)
                    eta = f"{mins:02d}:{secs:02d}"
                else:
                    eta = "-"
            eta = eta.strip()
            
            # Get total size - try multiple fields and estimate if needed
            total_str = d.get('_total_bytes_str', '').strip()
            if not total_str or total_str == 'N/A':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                
                # If no total, try to estimate from downloaded bytes and percent
                if total_bytes == 0:
                    downloaded = d.get('downloaded_bytes', 0)
                    # Parse percent string to get numeric value
                    percent_str = d.get('_percent_str', '').strip()
                    if percent_str and downloaded > 0:
                        try:
                            pct = float(percent_str.replace('%', '').strip())
                            if pct > 0:
                                total_bytes = int(downloaded / pct * 100)
                        except:
                            pass
                
                if total_bytes > 0:
                    if total_bytes > 1024 * 1024 * 1024:
                        total_str = f"{total_bytes / (1024 * 1024 * 1024):.2f}GiB"
                    elif total_bytes > 1024 * 1024:
                        total_str = f"{total_bytes / (1024 * 1024):.2f}MiB"
                    elif total_bytes > 1024:
                        total_str = f"{total_bytes / 1024:.2f}KiB"
                    else:
                        total_str = f"{total_bytes}B"
                else:
                    # Show downloaded bytes if we can't get total
                    downloaded = d.get('downloaded_bytes', 0)
                    if downloaded > 1024 * 1024:
                        total_str = f"~{downloaded / (1024 * 1024):.1f}MiB+"
                    elif downloaded > 1024:
                        total_str = f"~{downloaded / 1024:.1f}KiB+"
                    else:
                        total_str = "-"
            
            eel.update_progress(percent, speed, eta, total_str)

        except Exception as e:
            print(f"[Progress] Error: {e}")

@eel.expose
def cancel_download():
    global cancel_flag, _current_ydl
    cancel_flag = True
    # Immediately notify UI
    eel.download_complete(False, "Download cancelled")
    return True

# Main entry point
if __name__ == '__main__':
    load_config()
    
    browser_path = find_any_chromium_browser()
    
    try:
        if browser_path:
            eel.start('index.html', 
                     mode='custom',
                     cmdline_args=[browser_path, '--app=http://localhost:8000/index.html'],
                     size=(950, 850),
                     port=8000,
                     close_callback=force_exit)
        else:
            print("[App] No Chromium browser found, using default browser")
            eel.start('index.html', 
                     mode='default',
                     size=(950, 850),
                     port=8000,
                     close_callback=force_exit)
    except (SystemExit, KeyboardInterrupt):
        pass
    finally:
        force_exit()
