// Global variables
let currentVideoInfo = null;
let isDownloading = false;
let selectedVideoIndices = [];
let updateDownloadUrl = null;
let updatePath = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Load app version
    try {
        const version = await eel.get_app_version()();
        document.getElementById('appVersion').textContent = `v${version}`;
    } catch (e) {
        console.error('Failed to get app info:', e);
    }

    // Load download folder
    try {
        const folder = await eel.get_download_folder()();
        updateSaveLocation(folder);
    } catch (e) {
        console.error('Failed to get download folder:', e);
    }

    // Load saved cookies file
    try {
        const savedCookies = await eel.get_cookies_file()();
        if (savedCookies && savedCookies.length > 0) {
            const filename = savedCookies.split(/[/\\]/).pop();
            document.getElementById('cookieStatus').textContent = `✅ ${filename}`;
            document.getElementById('cookieStatus').classList.add('active');
        }
    } catch (e) {
        console.error('Failed to load cookies:', e);
    }

    // Check FFmpeg
    checkFFmpeg();

    // Load theme preference
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);

    // Check for updates on startup (silent)
    setTimeout(() => checkForUpdates(true), 2000);
});


// Theme toggle
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeButton(newTheme);
}

function updateThemeButton(theme) {
    const btn = document.getElementById('themeBtn');
    btn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// Update save location display
function updateSaveLocation(path) {
    const el = document.getElementById('saveLocation');
    if (path.length > 40) {
        path = '...' + path.substring(path.length - 37);
    }
    el.textContent = path;
}

// Change download folder
async function changeFolder() {
    try {
        const result = await eel.select_download_folder()();
        if (result.success) {
            updateSaveLocation(result.path);
            showStatus('Download folder changed', 'success');
        }
    } catch (e) {
        showStatus('Failed to change folder', 'error');
    }
}

// Open download folder
async function openFolder() {
    try {
        await eel.open_download_folder()();
    } catch (e) {
        showStatus('Failed to open folder', 'error');
    }
}

// Check FFmpeg availability
async function checkFFmpeg() {
    try {
        const installed = await eel.check_ffmpeg()();
        const ffmpegSection = document.getElementById('ffmpegSection');

        if (!installed) {
            ffmpegSection.style.display = 'block';
            showStatus('⚠️ FFmpeg not found. Install it for MP3 conversion.', 'warning');
        } else {
            ffmpegSection.style.display = 'none';
        }
    } catch (e) {
        console.error('FFmpeg check failed:', e);
    }
}

// Install FFmpeg
async function installFFmpeg() {
    try {
        const btn = document.getElementById('ffmpegBtn');
        btn.disabled = true;
        btn.textContent = '⏳ Downloading...';
        await eel.install_ffmpeg()();
    } catch (e) {
        showStatus('Failed to install FFmpeg: ' + e, 'error');
        document.getElementById('ffmpegBtn').disabled = false;
        document.getElementById('ffmpegBtn').textContent = '⬇️ Install FFmpeg';
    }
}

// FFmpeg status callback
eel.expose(update_ffmpeg_status);
function update_ffmpeg_status(status) {
    const btn = document.getElementById('ffmpegBtn');
    const statusEl = document.getElementById('ffmpegStatus');
    const section = document.getElementById('ffmpegSection');

    statusEl.textContent = status;

    if (status.includes('installed')) {
        btn.textContent = '✅ Installed';
        statusEl.style.color = '#2ECC71';
        setTimeout(() => {
            section.style.display = 'none';
        }, 2000);
        showStatus('FFmpeg installed successfully!', 'success');
    } else if (status.includes('Error')) {
        btn.disabled = false;
        btn.textContent = '⬇️ Install FFmpeg';
        statusEl.style.color = '#E74C3C';
    }
}

// Handle cookie file selection
async function selectCookieFile() {
    try {
        const result = await eel.select_cookies_file()();
        if (result.success) {
            const filename = result.path.split(/[/\\]/).pop();
            document.getElementById('cookieStatus').textContent = `✅ ${filename}`;
            document.getElementById('cookieStatus').classList.add('active');
            showStatus('Cookies file loaded successfully', 'success');
        }
    } catch (e) {
        showStatus('Failed to select cookies file', 'error');
    }
}

// Handle URL input - accepts ANY video URL
let fetchTimeout;
async function handleUrlInput() {
    const url = document.getElementById('url').value.trim();
    const videoInfo = document.getElementById('videoInfo');
    const playlistOptions = document.getElementById('playlistOptions');
    const loadingContainer = document.getElementById('loadingContainer');
    const videoInfoContent = document.getElementById('videoInfoContent');
    const siteBadge = document.getElementById('siteBadge');

    clearTimeout(fetchTimeout);

    if (!url) {
        videoInfo.classList.remove('active');
        playlistOptions.classList.remove('active');
        loadingContainer.classList.remove('active');
        videoInfoContent.style.display = 'none';
        siteBadge.textContent = '';
        siteBadge.className = 'site-badge';
        return;
    }

    // Basic URL validation - just check if it looks like a URL
    if (!isValidUrl(url)) {
        videoInfo.classList.remove('active');
        playlistOptions.classList.remove('active');
        siteBadge.textContent = '';
        return;
    }

    // Detect and show site
    try {
        const siteInfo = await eel.detect_site(url)();
        if (siteInfo.detected) {
            siteBadge.textContent = siteInfo.site;
            siteBadge.className = 'site-badge detected';
        } else {
            siteBadge.textContent = 'Auto-detect';
            siteBadge.className = 'site-badge';
        }
    } catch (e) {
        siteBadge.textContent = '';
    }

    // Fetch video info after short delay
    fetchTimeout = setTimeout(async () => {
        try {
            videoInfo.classList.add('active');
            loadingContainer.classList.add('active');
            videoInfoContent.style.display = 'none';
            showStatus('Fetching video info...', 'loading');

            const info = await eel.fetch_video_info(url)();

            loadingContainer.classList.remove('active');
            videoInfoContent.style.display = 'flex';

            if (info.success) {
                displayVideoInfo(info);
                showStatus('Video info loaded', 'success');
            } else {
                videoInfo.classList.remove('active');
                playlistOptions.classList.remove('active');
                showStatus('Failed: ' + info.error, 'error');
            }
        } catch (e) {
            loadingContainer.classList.remove('active');
            videoInfo.classList.remove('active');
            playlistOptions.classList.remove('active');
            showStatus('Error fetching video info', 'error');
            console.error(e);
        }
    }, 500);
}

// Basic URL validation - accepts any URL
function isValidUrl(url) {
    // Accept any URL that looks like a URL or video ID
    const patterns = [
        /^https?:\/\/.+/i,           // Any http/https URL
        /^[a-zA-Z0-9_-]{11}$/        // YouTube video ID
    ];
    return patterns.some(pattern => pattern.test(url));
}

// Display video information
function displayVideoInfo(info) {
    currentVideoInfo = info;
    selectedVideoIndices = [];

    const videoInfo = document.getElementById('videoInfo');
    const playlistOptions = document.getElementById('playlistOptions');

    document.getElementById('videoTitle').textContent = info.title || 'Unknown';
    document.getElementById('videoChannel').textContent = info.channel || 'Unknown';
    document.getElementById('videoDuration').textContent = info.duration || '--:--';

    // Show site/source
    const videoSite = document.getElementById('videoSite');
    if (videoSite) {
        videoSite.textContent = info.site || info.extractor || 'Unknown';
    }

    // Show playlist info if it's a playlist
    const playlistInfo = document.getElementById('playlistInfo');
    if (info.is_playlist) {
        document.getElementById('playlistTitle').textContent = info.playlist_title || 'Unknown';
        document.getElementById('playlistCount').textContent = info.playlist_count || 0;
        playlistInfo.classList.add('active');
        playlistOptions.classList.add('active');
    } else {
        playlistInfo.classList.remove('active');
        playlistOptions.classList.remove('active');
    }

    // Update thumbnail
    const thumbnail = document.getElementById('thumbnail');
    if (info.thumbnail) {
        thumbnail.src = info.thumbnail;
        thumbnail.style.display = 'block';
    } else {
        thumbnail.style.display = 'none';
    }

    // Update quality dropdown with available qualities
    const mode = document.querySelector('input[name="mode"]:checked').value;
    if (mode === 'video' && info.qualities && info.qualities.length > 0) {
        const qualitySelect = document.getElementById('quality');
        qualitySelect.innerHTML = '';
        info.qualities.forEach(q => {
            const option = document.createElement('option');
            option.value = q;
            option.textContent = q;
            qualitySelect.appendChild(option);
        });
    }

    videoInfo.classList.add('active');
}

// Toggle video selection visibility
function toggleVideoSelection() {
    const mode = document.querySelector('input[name="playlistMode"]:checked').value;
    const videoSelection = document.getElementById('videoSelection');
    videoSelection.style.display = mode === 'select' ? 'block' : 'none';
}

// Select/Deselect all videos
function selectAllVideos() {
    const checkboxes = document.querySelectorAll('#videoList input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = true);
    updateSelectedCount();
}

function deselectAllVideos() {
    const checkboxes = document.querySelectorAll('#videoList input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);
    updateSelectedCount();
}

function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('#videoList input[type="checkbox"]:checked');
    selectedVideoIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
    document.getElementById('selectedCount').textContent = `${selectedVideoIndices.length} selected`;
}

// Update quality options based on mode
function updateOptions() {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const quality = document.getElementById('quality');

    if (mode === 'audio') {
        quality.innerHTML = `
            <option>320 kbps</option>
            <option>256 kbps</option>
            <option>192 kbps</option>
            <option>128 kbps</option>
        `;
    } else {
        quality.innerHTML = `
            <option>Best</option>
            <option>1080p</option>
            <option>720p</option>
            <option>480p</option>
            <option>360p</option>
        `;
    }
}

// Start download
async function startDownload() {
    const url = document.getElementById('url').value.trim();

    if (!url) {
        showStatus('Please enter a video URL', 'error');
        return;
    }

    if (!isValidUrl(url)) {
        showStatus('Invalid URL', 'error');
        return;
    }

    const mode = document.querySelector('input[name="mode"]:checked').value;
    const quality = document.getElementById('quality').value;

    // Check playlist mode
    let playlistMode = 'single';
    let selectedIndices = null;

    if (currentVideoInfo && currentVideoInfo.is_playlist) {
        playlistMode = document.querySelector('input[name="playlistMode"]:checked').value;

        if (playlistMode === 'select') {
            selectedIndices = selectedVideoIndices;
            if (selectedIndices.length === 0) {
                showStatus('Please select at least one video', 'error');
                return;
            }
        }
    }

    // Update UI
    isDownloading = true;
    document.getElementById('downloadBtn').style.display = 'none';
    document.getElementById('cancelBtn').style.display = 'block';
    document.getElementById('progressSection').classList.add('active');

    resetProgress();

    try {
        showStatus('Starting download...', 'loading');
        await eel.start_download(url, mode, quality, playlistMode, selectedIndices)();
    } catch (e) {
        showStatus('Failed to start download: ' + e, 'error');
        resetUI();
    }
}

// Cancel download
async function cancelDownload() {
    if (!isDownloading) return;
    try {
        await eel.cancel_download()();
        showStatus('Cancelling download...', 'warning');
    } catch (e) {
        console.error('Failed to cancel:', e);
    }
}

// Reset progress
function resetProgress() {
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressText').textContent = '0%';
    document.getElementById('speed').textContent = '-';
    document.getElementById('eta').textContent = '-';
    document.getElementById('size').textContent = '-';
}

// Reset UI after download
function resetUI() {
    isDownloading = false;
    document.getElementById('downloadBtn').style.display = 'block';
    document.getElementById('cancelBtn').style.display = 'none';

    setTimeout(() => {
        document.getElementById('progressSection').classList.remove('active');
    }, 3000);
}

// Show status message
function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;

    const colors = {
        'success': '#2ECC71',
        'error': '#E74C3C',
        'warning': '#F39C12',
        'loading': '#3498DB',
        'info': '#666'
    };

    statusEl.style.color = colors[type] || colors.info;
}

// Eel exposed functions
eel.expose(update_progress);
function update_progress(percent, speed, eta, size) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    // Parse percent string
    let percentNum = parseFloat(percent.replace('%', ''));
    if (isNaN(percentNum)) percentNum = 0;

    progressFill.style.width = percentNum + '%';
    progressText.textContent = Math.round(percentNum) + '%';

    document.getElementById('speed').textContent = speed;
    document.getElementById('eta').textContent = eta;
    document.getElementById('size').textContent = size;

    showStatus('Downloading... ' + Math.round(percentNum) + '%', 'loading');
}

eel.expose(download_complete);
function download_complete(success, message) {
    if (success) {
        document.getElementById('progressFill').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';
        showStatus('✅ ' + message, 'success');

        // Browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Download Complete', {
                body: currentVideoInfo ? currentVideoInfo.title : 'Your download is ready'
            });
        }
    } else {
        showStatus('❌ ' + message, 'error');
    }

    resetUI();
}

// Request notification permission
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}
// ==================== UPDATE FUNCTIONS ====================

// Check for updates
async function checkForUpdates(silent = false) {
    try {
        const updateBtn = document.getElementById('updateBtn');
        if (!silent) {
            updateBtn.textContent = '';
        }
        
        const result = await eel.check_for_updates()();
        
        if (!silent) {
            updateBtn.textContent = '';
        }
        
        if (result.success && result.update_available) {
            // Show update badge
            document.getElementById('updateBadge').classList.add('active');
            updateDownloadUrl = result.download_url;
            
            // Update modal content
            document.getElementById('updateVersionInfo').textContent = 
                +result.current_version+  v+result.latest_version;
            
            // Show modal if not silent or first time
            if (!silent || !localStorage.getItem('updateDismissed_' + result.latest_version)) {
                showUpdateModal();
            }
        } else if (!silent) {
            if (result.success) {
                showStatus('You have the latest version!', 'success');
            } else {
                showStatus('Failed to check for updates', 'error');
            }
        }
    } catch (e) {
        console.error('Update check failed:', e);
        if (!silent) {
            showStatus('Failed to check for updates', 'error');
        }
    }
}

// Show update modal
function showUpdateModal() {
    document.getElementById('updateModal').classList.add('active');
    document.getElementById('updateProgress').style.display = 'none';
    document.getElementById('updateButtons').style.display = 'flex';
    document.getElementById('updateStatus').textContent = 'A new version is available with improvements and bug fixes.';
}

// Close update modal
function closeUpdateModal() {
    document.getElementById('updateModal').classList.remove('active');
    // Remember dismissal for this version
    const version = document.getElementById('updateVersionInfo').textContent.split('')[1].trim();
    localStorage.setItem('updateDismissed_' + version, 'true');
}

// Download and install update
async function downloadAndInstallUpdate() {
    if (!updateDownloadUrl) {
        showStatus('No update URL available', 'error');
        return;
    }
    
    // Show progress
    document.getElementById('updateButtons').style.display = 'none';
    document.getElementById('updateProgress').style.display = 'block';
    document.getElementById('updateStatus').textContent = 'Downloading update...';
    
    try {
        await eel.download_update(updateDownloadUrl)();
    } catch (e) {
        console.error('Download failed:', e);
        document.getElementById('updateStatus').textContent = 'Download failed: ' + e;
        document.getElementById('updateButtons').style.display = 'flex';
    }
}

// Update download progress callback
eel.expose(update_download_progress);
function update_download_progress(percent) {
    document.getElementById('updateProgressBar').style.width = percent + '%';
    document.getElementById('updateStatus').textContent = 'Downloading update... ' + percent + '%';
}

// Update download complete callback
eel.expose(update_download_complete);
async function update_download_complete(success, pathOrError) {
    if (success) {
        updatePath = pathOrError;
        document.getElementById('updateStatus').textContent = 'Download complete! Installing...';
        document.getElementById('updateProgressBar').style.width = '100%';
        
        // Apply update after short delay
        setTimeout(async () => {
            try {
                const result = await eel.apply_update(updatePath)();
                if (!result.success) {
                    document.getElementById('updateStatus').textContent = 'Update failed: ' + result.error;
                    document.getElementById('updateButtons').style.display = 'flex';
                }
            } catch (e) {
                document.getElementById('updateStatus').textContent = 'Update failed: ' + e;
                document.getElementById('updateButtons').style.display = 'flex';
            }
        }, 1000);
    } else {
        document.getElementById('updateStatus').textContent = 'Download failed: ' + pathOrError;
        document.getElementById('updateButtons').style.display = 'flex';
    }
}
