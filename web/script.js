// Global variables
let currentVideoInfo = null;
let isDownloading = false;
let selectedVideoIndices = [];

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Load app version
    try {
        const appInfo = await eel.get_app_info()();
        document.getElementById('appVersion').textContent = `v${appInfo.version}`;
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
        console.log('[Cookies] Loaded from config:', savedCookies);
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
        await eel.open_folder()();
    } catch (e) {
        showStatus('Failed to open folder', 'error');
    }
}

// Check FFmpeg availability
async function checkFFmpeg() {
    try {
        const result = await eel.check_ffmpeg()();
        const ffmpegSection = document.getElementById('ffmpegSection');

        if (!result.installed) {
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
        const status = document.getElementById('ffmpegStatus');

        btn.disabled = true;
        btn.textContent = '⏳ Downloading...';
        status.textContent = 'Starting download...';

        await eel.install_ffmpeg()();
    } catch (e) {
        showStatus('Failed to install FFmpeg: ' + e.message, 'error');
        document.getElementById('ffmpegBtn').disabled = false;
        document.getElementById('ffmpegBtn').textContent = '⬇️ Install FFmpeg';
    }
}

// FFmpeg progress callback
eel.expose(ffmpeg_progress);
function ffmpeg_progress(data) {
    const btn = document.getElementById('ffmpegBtn');
    const status = document.getElementById('ffmpegStatus');
    const section = document.getElementById('ffmpegSection');

    if (data.status === 'downloading') {
        btn.textContent = `⏳ Downloading... ${Math.round(data.percent)}%`;
        status.textContent = `Downloading FFmpeg: ${Math.round(data.percent)}%`;
    } else if (data.status === 'extracting') {
        btn.textContent = '📦 Extracting...';
        status.textContent = 'Extracting files...';
    } else if (data.status === 'complete') {
        btn.textContent = '✅ Installed';
        status.textContent = 'FFmpeg installed successfully!';
        status.style.color = '#2ECC71';
        setTimeout(() => {
            section.style.display = 'none';
        }, 2000);
        showStatus('FFmpeg installed successfully!', 'success');
    } else if (data.status === 'error') {
        btn.disabled = false;
        btn.textContent = '⬇️ Install FFmpeg';
        status.textContent = 'Error: ' + data.error;
        status.style.color = '#E74C3C';
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
        } else {
            showStatus('No cookies file selected', 'info');
        }
    } catch (e) {
        showStatus('Failed to select cookies file', 'error');
        console.error(e);
    }
}

// Handle URL input
let fetchTimeout;
async function handleUrlInput() {
    const url = document.getElementById('url').value.trim();
    const videoInfo = document.getElementById('videoInfo');
    const playlistOptions = document.getElementById('playlistOptions');
    const loadingContainer = document.getElementById('loadingContainer');
    const videoInfoContent = document.getElementById('videoInfoContent');

    // Clear previous timeout
    clearTimeout(fetchTimeout);

    if (!url) {
        videoInfo.classList.remove('active');
        playlistOptions.classList.remove('active');
        loadingContainer.classList.remove('active');
        videoInfoContent.style.display = 'none';
        return;
    }

    // Validate YouTube URL
    if (!isValidYouTubeUrl(url)) {
        videoInfo.classList.remove('active');
        playlistOptions.classList.remove('active');
        return;
    }

    // Show loading spinner immediately
    fetchTimeout = setTimeout(async () => {
        try {
            // Show loading animation
            videoInfo.classList.add('active');
            loadingContainer.classList.add('active');
            videoInfoContent.style.display = 'none';
            showStatus('Fetching video info...', 'loading');

            const info = await eel.fetch_video_info(url)();

            // Hide loading, show content
            loadingContainer.classList.remove('active');
            videoInfoContent.style.display = 'flex';

            if (info.success) {
                displayVideoInfo(info);
                showStatus('Video info loaded', 'success');
            } else {
                videoInfo.classList.remove('active');
                playlistOptions.classList.remove('active');
                showStatus('Failed to fetch video info: ' + info.error, 'error');
            }
        } catch (e) {
            loadingContainer.classList.remove('active');
            videoInfo.classList.remove('active');
            playlistOptions.classList.remove('active');
            showStatus('Error fetching video info', 'error');
            console.error(e);
        }
    }, 300);
}

// Validate YouTube URL
function isValidYouTubeUrl(url) {
    const patterns = [
        /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/,
        /^(https?:\/\/)?(music\.youtube\.com)\/.+/,
        /^[a-zA-Z0-9_-]{11}$/
    ];
    return patterns.some(pattern => pattern.test(url));
}

// Display video information
function displayVideoInfo(info) {
    currentVideoInfo = info;
    selectedVideoIndices = [];

    const videoInfo = document.getElementById('videoInfo');
    const playlistOptions = document.getElementById('playlistOptions');

    document.getElementById('videoTitle').textContent = info.title;
    document.getElementById('videoChannel').textContent = info.channel;
    document.getElementById('videoDuration').textContent = info.duration;

    // Show playlist info if it's a playlist
    const playlistInfo = document.getElementById('playlistInfo');
    if (info.is_playlist) {
        document.getElementById('playlistTitle').textContent = info.playlist_title || 'Unknown';
        document.getElementById('playlistCount').textContent = info.playlist_count || 0;
        playlistInfo.classList.add('active');
        playlistOptions.classList.add('active');

        // Populate video list for selection
        populateVideoList(info.playlist_videos || []);
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

    // Update quality dropdown with ACTUAL available qualities
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

// Populate video list for playlist selection
function populateVideoList(videos) {
    const videoList = document.getElementById('videoList');
    videoList.innerHTML = '';

    videos.forEach((video, index) => {
        const duration = formatDuration(video.duration);
        const item = document.createElement('div');
        item.className = 'video-item';
        item.innerHTML = `
            <label class="video-checkbox">
                <input type="checkbox" data-index="${index}" onchange="updateSelectedCount()">
                <span class="video-number">${index + 1}.</span>
                <span class="video-title">${escapeHtml(video.title)}</span>
                <span class="video-duration">${duration}</span>
            </label>
        `;
        videoList.appendChild(item);
    });

    updateSelectedCount();
}

function formatDuration(seconds) {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Toggle video selection visibility
function toggleVideoSelection() {
    const mode = document.querySelector('input[name="playlistMode"]:checked').value;
    const videoSelection = document.getElementById('videoSelection');

    if (mode === 'select') {
        videoSelection.style.display = 'block';
    } else {
        videoSelection.style.display = 'none';
    }
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
        showStatus('Please enter a YouTube URL', 'error');
        return;
    }

    if (!isValidYouTubeUrl(url)) {
        showStatus('Invalid YouTube URL', 'error');
        return;
    }

    const mode = document.querySelector('input[name="mode"]:checked').value;
    const quality = document.getElementById('quality').value;

    // Check playlist mode and selected videos
    let downloadPlaylist = false;
    let selectedIndices = null;

    if (currentVideoInfo && currentVideoInfo.is_playlist) {
        const playlistMode = document.querySelector('input[name="playlistMode"]:checked').value;

        if (playlistMode === 'all') {
            downloadPlaylist = true;
        } else if (playlistMode === 'select') {
            downloadPlaylist = true;
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

    // Reset progress
    resetProgress();

    try {
        showStatus('Starting download...', 'loading');
        const result = await eel.start_download(url, mode, quality, downloadPlaylist, selectedIndices)();

        if (!result.success) {
            throw new Error(result.error || 'Download failed');
        }
    } catch (e) {
        showStatus('Failed to start download: ' + e.message, 'error');
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

// Eel exposed functions (called from Python)
eel.expose(update_progress);
function update_progress(data) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    progressFill.style.width = data.percent + '%';
    progressText.textContent = Math.round(data.percent) + '%';

    document.getElementById('speed').textContent = data.speed;
    document.getElementById('eta').textContent = data.eta;
    document.getElementById('size').textContent = data.size;

    // Update status
    if (data.status.startsWith('downloading_playlist_')) {
        const parts = data.status.split('_');
        const idx = parts[2];
        const count = parts[3];
        showStatus(`Downloading video ${idx} of ${count}... ${Math.round(data.percent)}%`, 'loading');
    } else if (data.status === 'downloading') {
        showStatus('Downloading... ' + Math.round(data.percent) + '%', 'loading');
    } else if (data.status === 'processing') {
        showStatus('Processing and converting...', 'warning');
    }
}

eel.expose(download_complete);
function download_complete(data) {
    if (data.success) {
        document.getElementById('progressFill').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';
        showStatus('✅ Download completed successfully!', 'success');

        // Show notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Download Complete', {
                body: currentVideoInfo ? currentVideoInfo.title : 'Your download is ready',
                icon: currentVideoInfo ? currentVideoInfo.thumbnail : ''
            });
        }
    } else {
        showStatus('❌ ' + data.error, 'error');
    }

    resetUI();
}

// Request notification permission
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}