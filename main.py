import eel
import yt_dlp
import os
import sys
import json
import threading
import signal
import atexit
import shutil
import subprocess
import urllib.request
import zipfile
import re
import time
from pathlib import Path

# App Version
APP_VERSION = "1.0.0"
APP_AUTHOR = "Isharaka"

# Initialize Eel
eel.init('web')

# Configuration file path - Use AppData for professional config storage
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Store config in AppData folder (like professional apps)
APPDATA_DIR = os.path.join(os.environ.get('APPDATA', BASE_DIR), 'YouTube Downloader Pro')
os.makedirs(APPDATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')
FFMPEG_DIR = os.path.join(APPDATA_DIR, 'ffmpeg')

# Global variables
download_folder = str(Path.home() / "Downloads")
cookies_file = None
cancel_flag = False
_app_closing = False
playlist_progress = {'completed': 0, 'total': 0}

def force_exit():
    """Force exit the application and all child processes"""
    global _app_closing
    if _app_closing:
        return
    _app_closing = True
    print("[App] Force exiting...")
    os._exit(0)

atexit.register(force_exit)

def find_edge_path():
    """Find Microsoft Edge installation"""
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in edge_paths:
        if os.path.exists(path):
            return path
    return None

def find_chrome_path():
    """Find Google Chrome installation"""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            return path
    return None

def find_brave_path():
    """Find Brave browser installation"""
    brave_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    ]
    for path in brave_paths:
        if os.path.exists(path):
            return path
    return None

def find_any_chromium_browser():
    """Find any Chromium-based browser that supports app mode"""
    # Try common Chromium browsers in order of preference
    browsers = [
        find_edge_path,
        find_chrome_path,
        find_brave_path,
    ]
    for finder in browsers:
        path = finder()
        if path:
            return path
    return None


def load_config():
    """Load saved configuration"""
    global download_folder, cookies_file
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                download_folder = config.get('download_folder', download_folder)
                saved_cookies = config.get('cookies_file', None)
                if saved_cookies and os.path.exists(saved_cookies):
                    cookies_file = saved_cookies
                else:
                    cookies_file = None
                print(f"[Config] Loaded: folder={download_folder}, cookies={cookies_file}")
    except Exception as e:
        print(f"[Config] Error loading: {e}")

def save_config():
    """Save configuration"""
    try:
        config = {
            'download_folder': download_folder,
            'cookies_file': cookies_file
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        print(f"[Config] Saved successfully")
    except Exception as e:
        print(f"[Config] Error saving: {e}")

load_config()

# ==================== EXPOSED FUNCTIONS ====================

@eel.expose
def get_app_info():
    """Get app version and author info"""
    return {
        'version': APP_VERSION,
        'author': APP_AUTHOR
    }

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
def select_download_folder():
    """Open folder dialog to select download folder"""
    global download_folder
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        folder = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=download_folder
        )
        
        root.destroy()
        
        if folder:
            download_folder = folder
            save_config()
            print(f"[Folder] Selected: {folder}")
            return {'success': True, 'path': folder}
        else:
            return {'success': False, 'error': 'No folder selected'}
    except Exception as e:
        print(f"[Error] select_download_folder: {e}")
        return {'success': False, 'error': str(e)}

@eel.expose
def select_cookies_file():
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        filepath = filedialog.askopenfilename(
            title="Select Cookies File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        root.destroy()
        
        if filepath:
            global cookies_file
            cookies_file = filepath
            save_config()
            print(f"[Cookies] Selected: {filepath}")
            return {'success': True, 'path': filepath}
        else:
            return {'success': False, 'error': 'No file selected'}
    except Exception as e:
        print(f"[Error] select_cookies_file: {e}")
        return {'success': False, 'error': str(e)}

@eel.expose
def get_cookies_file():
    if cookies_file and os.path.exists(cookies_file):
        return cookies_file
    return ""

@eel.expose
def fetch_video_info(url):
    """Fetch video/playlist info with ACTUAL available qualities"""
    try:
        # First pass: quick check for playlist
        ydl_opts_quick = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': True,
            'playlist_items': '1-50',
        }
        
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts_quick['cookiefile'] = cookies_file
        
        is_playlist = False
        playlist_title = None
        playlist_count = 0
        playlist_videos = []
        video_url = url
        
        with yt_dlp.YoutubeDL(ydl_opts_quick) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info.get('_type') == 'playlist' or 'entries' in info:
                entries = list(info.get('entries', []))
                if entries and len(entries) > 0:
                    is_playlist = True
                    playlist_title = info.get('title', 'Unknown Playlist')
                    playlist_count = len(entries)
                    
                    # Get video list for selection
                    for i, entry in enumerate(entries):
                        if entry:
                            playlist_videos.append({
                                'index': i,
                                'id': entry.get('id', ''),
                                'title': entry.get('title', f'Video {i+1}'),
                                'duration': entry.get('duration', 0) or 0,
                                'url': entry.get('url', entry.get('webpage_url', ''))
                            })
                    
                    # Use first video for quality detection
                    if entries[0]:
                        video_url = entries[0].get('url', entries[0].get('webpage_url', url))
        
        # Second pass: get FULL info with formats for quality detection
        ydl_opts_full = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,  # Get full format info
            'noplaylist': True,     # Only get this video, not playlist
        }
        
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts_full['cookiefile'] = cookies_file
        
        with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
            video_info = ydl.extract_info(video_url, download=False)
        
        # Format duration
        duration = video_info.get('duration', 0) or 0
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        if hours > 0:
            duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = f"{minutes}:{seconds:02d}"
        
        # Get ACTUAL available qualities from formats
        available_qualities = ['Best']
        if 'formats' in video_info:
            heights = set()
            for f in video_info['formats']:
                # Only consider video formats with height
                if f.get('vcodec') != 'none' and f.get('height'):
                    heights.add(f['height'])
            
            # Sort heights descending and create quality labels
            sorted_heights = sorted(list(heights), reverse=True)
            for h in sorted_heights:
                if h >= 2160:
                    available_qualities.append(f'{h}p (4K)')
                elif h >= 1440:
                    available_qualities.append(f'{h}p (2K)')
                else:
                    available_qualities.append(f'{h}p')
        
        print(f"[Info] Available qualities: {available_qualities}")
        
        return {
            'success': True,
            'title': video_info.get('title', 'Unknown'),
            'channel': video_info.get('channel', video_info.get('uploader', 'Unknown')),
            'duration': duration_str,
            'thumbnail': video_info.get('thumbnail', ''),
            'qualities': available_qualities,
            'is_playlist': is_playlist,
            'playlist_title': playlist_title,
            'playlist_count': playlist_count,
            'playlist_videos': playlist_videos
        }
    except Exception as e:
        print(f"[Error] fetch_video_info: {e}")
        return {'success': False, 'error': str(e)}

@eel.expose
def start_download(url, mode, quality, download_playlist=False, selected_indices=None):
    """Start download with improved options"""
    global cancel_flag, playlist_progress
    cancel_flag = False
    playlist_progress = {'completed': 0, 'total': 0}
    
    def download_task():
        global playlist_progress
        try:
            # Create playlist subfolder if downloading playlist
            target_folder = download_folder
            if download_playlist:
                # Get playlist title for folder name
                try:
                    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if info.get('title'):
                            # Sanitize folder name
                            folder_name = re.sub(r'[<>:"/\\|?*]', '', info['title'])[:50]
                            target_folder = os.path.join(download_folder, folder_name)
                            os.makedirs(target_folder, exist_ok=True)
                            print(f"[Download] Created folder: {target_folder}")
                except:
                    pass
            
            def progress_hook(d):
                if cancel_flag:
                    raise Exception("Download cancelled by user")
                
                if d['status'] == 'downloading':
                    try:
                        if 'total_bytes' in d:
                            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        elif 'total_bytes_estimate' in d:
                            percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                        else:
                            percent = 0
                        
                        speed = d.get('_speed_str', 'N/A')
                        eta = d.get('_eta_str', 'N/A')
                        
                        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                        if total_bytes:
                            size_mb = total_bytes / 1024 / 1024
                            size_str = f"{size_mb:.1f} MB"
                        else:
                            size_str = "N/A"
                        
                        status_text = 'downloading'
                        if 'info_dict' in d:
                            info = d['info_dict']
                            if 'playlist_index' in info and 'playlist_count' in info:
                                idx = info['playlist_index']
                                count = info['playlist_count']
                                status_text = f'downloading_playlist_{idx}_{count}'
                                playlist_progress['total'] = count
                        
                        eel.update_progress({
                            'percent': round(percent, 1),
                            'speed': speed,
                            'eta': eta,
                            'size': size_str,
                            'status': status_text
                        })
                    except Exception as e:
                        print(f"[Progress Error] {e}")
                
                elif d['status'] == 'finished':
                    playlist_progress['completed'] += 1
                    eel.update_progress({
                        'percent': 100,
                        'speed': '-',
                        'eta': 'Complete',
                        'size': '-',
                        'status': 'processing'
                    })
            
            # Build yt-dlp options with speed optimizations
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [progress_hook],
                'paths': {'home': target_folder},
                'noplaylist': not download_playlist,
                # Speed optimizations
                'concurrent_fragment_downloads': 4,
                'http_chunk_size': 10485760,  # 10MB chunks
                'retries': 10,
                'fragment_retries': 10,
                'file_access_retries': 5,
                'extractor_retries': 3,
            }
            
            # Handle selected videos for playlist
            if download_playlist and selected_indices:
                # Convert to 1-based indices for yt-dlp
                items = ','.join(str(i + 1) for i in selected_indices)
                ydl_opts['playlist_items'] = items
                print(f"[Download] Selected items: {items}")
            
            if cookies_file and os.path.exists(cookies_file):
                ydl_opts['cookiefile'] = cookies_file
                print(f"[Download] Using cookies: {cookies_file}")
            
            if mode == 'video':
                if quality == 'Best':
                    format_str = 'bestvideo+bestaudio/best'
                else:
                    match = re.match(r'(\d+)p', quality)
                    if match:
                        height = match.group(1)
                        format_str = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
                    else:
                        format_str = 'bestvideo+bestaudio/best'
                
                ydl_opts['format'] = format_str
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                # AUDIO: Try audio-only first, then fall back to LOWEST quality video
                # This minimizes data usage: bestaudio (~4MB) or worst video (~10MB)
                ydl_opts['format'] = 'bestaudio/worstaudio/worst'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }]
            
            print(f"[Download] Starting: {url}")
            print(f"[Download] Playlist mode: {download_playlist}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            eel.download_complete({
                'success': True,
                'message': 'Download completed successfully!',
                'folder': target_folder
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"[Error] download_task: {error_msg}")
            
            # Clean up partial files on cancel
            if cancel_flag:
                cleanup_partial_files(target_folder if 'target_folder' in dir() else download_folder)
                completed = playlist_progress['completed']
                total = playlist_progress['total']
                if total > 0:
                    error_msg = f"Cancelled. {completed} of {total} videos downloaded."
                else:
                    error_msg = "Download cancelled. Partial files cleaned up."
            
            eel.download_complete({
                'success': False,
                'error': error_msg
            })
    
    thread = threading.Thread(target=download_task, daemon=True)
    thread.start()
    
    return {'success': True, 'message': 'Download started'}

def cleanup_partial_files(folder):
    """Clean up .part files after cancel"""
    try:
        for file in os.listdir(folder):
            if file.endswith('.part') or file.endswith('.ytdl'):
                filepath = os.path.join(folder, file)
                try:
                    os.remove(filepath)
                    print(f"[Cleanup] Removed: {file}")
                except:
                    pass
    except Exception as e:
        print(f"[Cleanup Error] {e}")

@eel.expose
def cancel_download():
    global cancel_flag
    cancel_flag = True
    return True

@eel.expose
def open_folder():
    try:
        if sys.platform == 'win32':
            os.startfile(download_folder)
        elif sys.platform == 'darwin':
            os.system(f'open "{download_folder}"')
        else:
            os.system(f'xdg-open "{download_folder}"')
        return True
    except Exception as e:
        return False

@eel.expose
def check_ffmpeg():
    """Check if FFmpeg is available"""
    # Check system PATH
    if shutil.which('ffmpeg'):
        return {'installed': True, 'path': 'system'}
    
    # Check local ffmpeg folder
    local_ffmpeg = os.path.join(FFMPEG_DIR, 'bin', 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        # Add to PATH for this session
        os.environ['PATH'] = os.path.join(FFMPEG_DIR, 'bin') + os.pathsep + os.environ['PATH']
        return {'installed': True, 'path': 'local'}
    
    return {'installed': False, 'path': None}

@eel.expose
def install_ffmpeg():
    """Download and install FFmpeg"""
    def install_task():
        try:
            eel.ffmpeg_progress({'status': 'downloading', 'percent': 0})
            
            # FFmpeg download URL (essentials build from gyan.dev)
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            zip_path = os.path.join(BASE_DIR, 'ffmpeg.zip')
            
            # Download with progress
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = (block_num * block_size / total_size) * 100
                    eel.ffmpeg_progress({'status': 'downloading', 'percent': min(percent, 100)})
            
            urllib.request.urlretrieve(url, zip_path, report_progress)
            
            eel.ffmpeg_progress({'status': 'extracting', 'percent': 100})
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find the root folder name in zip
                root_folder = zip_ref.namelist()[0].split('/')[0]
                zip_ref.extractall(BASE_DIR)
            
            # Rename to 'ffmpeg'
            extracted_path = os.path.join(BASE_DIR, root_folder)
            if os.path.exists(FFMPEG_DIR):
                shutil.rmtree(FFMPEG_DIR)
            os.rename(extracted_path, FFMPEG_DIR)
            
            # Clean up zip
            os.remove(zip_path)
            
            # Add to PATH
            os.environ['PATH'] = os.path.join(FFMPEG_DIR, 'bin') + os.pathsep + os.environ['PATH']
            
            eel.ffmpeg_progress({'status': 'complete', 'percent': 100})
            print("[FFmpeg] Installation complete")
            
        except Exception as e:
            print(f"[FFmpeg Error] {e}")
            eel.ffmpeg_progress({'status': 'error', 'error': str(e)})
    
    thread = threading.Thread(target=install_task, daemon=True)
    thread.start()
    return {'success': True}

def on_close(page, sockets):
    print("[App] Window closed, shutting down...")
    force_exit()

if __name__ == '__main__':
    def signal_handler(sig, frame):
        print("[App] Signal received, closing...")
        force_exit()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Find any Chromium-based browser for app mode (Edge, Chrome, Brave)
        browser_path = find_any_chromium_browser()
        
        if browser_path:
            browser_name = os.path.basename(browser_path).replace('.exe', '').title()
            print(f"[App] v{APP_VERSION} - Using {browser_name}: {browser_path}")
            eel.start('index.html',
                     mode='custom',
                     cmdline_args=[
                         browser_path,
                         '--app=http://localhost:8080/index.html',
                         '--disable-extensions',
                         '--disable-sync',
                         '--no-first-run',
                         '--start-maximized'
                     ],
                     size=(900, 800),
                     port=8080,
                     close_callback=on_close,
                     block=True)
        else:
            # FALLBACK: Use default system browser (works on ANY PC)
            print(f"[App] v{APP_VERSION} - No Chromium browser found, using default browser...")
            print("[App] The app will open in your default browser.")
            print("[App] For best experience, install Chrome, Edge, or Brave.")
            eel.start('index.html',
                     mode='default',  # Opens in default browser tab
                     size=(900, 800),
                     port=8080,
                     close_callback=on_close,
                     block=True)
                     
    except (SystemExit, KeyboardInterrupt):
        print("[App] Exited normally")
    except Exception as e:
        print(f"[Error] Failed to start: {e}")
    finally:
        force_exit()