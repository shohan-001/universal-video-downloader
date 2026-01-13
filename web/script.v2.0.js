// ==================== GLOBAL STATE ====================
let currentVideoInfo = null;
let updateDownloadUrl = null;
let updatePath = null;
let isPlaylistDownload = false;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', async function () {
    // Load saved settings
    await loadSettings();

    // Setup URL input event
    const urlInput = document.getElementById('urlInput');
    urlInput.addEventListener('paste', function () {
        setTimeout(() => handleUrlInput(), 100);
    });
    urlInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') handleUrlInput();
    });

    // Check for updates silently
    setTimeout(() => checkForUpdates(true), 2000);

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }

    // Initialize Particles
    initParticles();
    window.addEventListener('resize', resizeCanvas);
});

// ==================== PARTICLES BACKGROUND ====================
let particleCtx;
let particles = [];
const particleCount = 50;
let canvas;

function initParticles() {
    canvas = document.getElementById('particles');
    particleCtx = canvas.getContext('2d');
    resizeCanvas();

    for (let i = 0; i < particleCount; i++) {
        particles.push(createParticle());
    }

    animateParticles();
}

function resizeCanvas() {
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

function createParticle() {
    return {
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 3 + 1,
        speedX: Math.random() * 1 - 0.5,
        speedY: Math.random() * 1 - 0.5,
        color: `hsla(${Math.random() * 60 + 220}, 70%, 60%, ${Math.random() * 0.4 + 0.1})` // Blue/Purple hues
    };
}

function animateParticles() {
    if (!canvas) return;
    particleCtx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {
        p.x += p.speedX;
        p.y += p.speedY;

        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        particleCtx.fillStyle = p.color;
        particleCtx.beginPath();
        particleCtx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        particleCtx.fill();
    });

    // Add subtle gradient connection lines if close
    particles.forEach((p1, i) => {
        particles.slice(i + 1).forEach(p2 => {
            const dx = p1.x - p2.x;
            const dy = p1.y - p2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 100) {
                particleCtx.strokeStyle = `rgba(100, 120, 255, ${0.1 * (1 - dist / 100)})`;
                particleCtx.lineWidth = 0.5;
                particleCtx.beginPath();
                particleCtx.moveTo(p1.x, p1.y);
                particleCtx.lineTo(p2.x, p2.y);
                particleCtx.stroke();
            }
        });
    });

    requestAnimationFrame(animateParticles);
}

// ==================== SETTINGS ====================
async function loadSettings() {
    try {
        const config = await eel.get_config()();
        if (config.download_folder) {
            document.getElementById('downloadPath').textContent = config.download_folder;
        }
        if (config.cookies_file) {
            document.getElementById('cookiesPath').textContent = config.cookies_file;
        }
    } catch (e) {
        console.error('Failed to load config:', e);
    }
}

function toggleSettings() {
    const section = document.getElementById('settingsSection');
    section.style.display = section.style.display === 'none' ? 'block' : 'none';
}

async function changeDownloadFolder() {
    try {
        const folder = await eel.select_download_folder()();
        if (folder) {
            document.getElementById('downloadPath').textContent = folder;
            showStatus('Download folder updated!', 'success');
        }
    } catch (e) {
        showStatus('Failed to change folder', 'error');
    }
}

async function selectCookiesFile() {
    try {
        const file = await eel.select_cookies_file()();
        if (file) {
            document.getElementById('cookiesPath').textContent = file;
            showStatus('Cookies file set!', 'success');
        }
    } catch (e) {
        showStatus('Failed to select cookies file', 'error');
    }
}

async function openDownloadFolder() {
    try {
        await eel.open_download_folder()();
    } catch (e) {
        showStatus('Failed to open folder', 'error');
    }
}

// ==================== URL HANDLING ====================
// ==================== UI STATE HANDLING ====================

// Helper function to add timeout to Eel calls
function withTimeout(promise, timeoutMs = 60000) {
    return Promise.race([
        promise,
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timed out')), timeoutMs)
        )
    ]);
}

async function handleUrlInput() {
    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();
    if (!url) return;

    // Detect site immediately
    detectSite(url);

    // Get DOM elements
    const fetchBtn = document.getElementById('fetchBtn');
    const videoSection = document.getElementById('videoSection');
    const progressSection = document.getElementById('progressSection');
    const downloadBtn = document.getElementById('downloadBtn');
    const statusContainer = document.getElementById('statusContainer');

    // Show loading state
    fetchBtn.disabled = true;
    fetchBtn.querySelector('.fetch-text').style.display = 'none';
    fetchBtn.querySelector('.fetch-loading').style.display = 'inline-block';

    // Hide previous results
    videoSection.style.display = 'none';
    statusContainer.style.display = 'none';

    try {
        console.log('[JS] Calling fetch_video_info...');
        const info = await withTimeout(eel.fetch_video_info(url)(), 120000);  // 120 seconds for large playlists
        console.log('[JS] Got response:', info);

        if (info.success) {
            displayVideoInfo(info);
            // Hide progress section when new video fetched
            progressSection.style.display = 'none';
            downloadBtn.style.display = 'flex';
        } else {
            showStatus(info.error || 'Failed to fetch video info', 'error');
        }
    } catch (e) {
        console.error('[JS] Fetch error:', e);
        if (e.message === 'Request timed out') {
            showStatus('Request timed out. The video may be taking too long to fetch.', 'error');
        } else {
            showStatus('Error connecting to backend: ' + e.message, 'error');
        }
    } finally {
        fetchBtn.disabled = false;
        fetchBtn.querySelector('.fetch-text').style.display = 'inline';
        fetchBtn.querySelector('.fetch-loading').style.display = 'none';
    }
}

function detectSite(url) {
    const siteBadge = document.getElementById('siteBadge');
    const sites = {
        'youtube.com': 'YouTube',
        'youtu.be': 'YouTube',
        'tiktok.com': 'TikTok',
        'instagram.com': 'Instagram',
        'facebook.com': 'Facebook',
        'fb.watch': 'Facebook',
        'twitter.com': 'Twitter',
        'x.com': 'Twitter',
        'vimeo.com': 'Vimeo',
        'reddit.com': 'Reddit',
        'twitch.tv': 'Twitch',
        'dailymotion.com': 'Dailymotion',
        'soundcloud.com': 'SoundCloud',
        'bilibili.com': 'Bilibili'
    };

    let detected = null;
    for (const [domain, name] of Object.entries(sites)) {
        if (url.includes(domain)) {
            detected = name;
            break;
        }
    }

    if (detected) {
        siteBadge.textContent = detected;
        siteBadge.classList.add('visible');
    } else {
        siteBadge.classList.remove('visible');
    }
}

// ==================== VIDEO DISPLAY ====================
let selectedPlaylistIndices = null;

function displayVideoInfo(info) {
    currentVideoInfo = info;
    selectedPlaylistIndices = null; // Reset selection

    console.log('[JS] displayVideoInfo called with:', info);

    // Set thumbnail
    const thumbnail = document.getElementById('videoThumbnail');
    if (thumbnail) {
        if (info.thumbnail) {
            thumbnail.src = info.thumbnail;
            thumbnail.style.display = 'block';
        } else {
            thumbnail.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 9"><rect fill="%23333" width="16" height="9"/></svg>';
            thumbnail.style.display = 'block';
        }
    }

    // Set title
    const titleEl = document.getElementById('videoTitle');
    if (titleEl) titleEl.textContent = info.title;

    // Set duration
    const durationEl = document.getElementById('videoDuration');
    if (durationEl) durationEl.textContent = info.duration;

    // Set source and channel
    const sourceEl = document.getElementById('videoSource');
    if (sourceEl) {
        sourceEl.innerHTML = '<span class="meta-icon">📺</span><span class="meta-text">' + (info.extractor || 'Unknown') + '</span>';
    }

    const channelEl = document.getElementById('videoChannel');
    if (channelEl) {
        channelEl.innerHTML = '<span class="meta-icon">👤</span><span class="meta-text">' + (info.channel || info.uploader || 'Unknown') + '</span>';
    }

    // Show playlist info and options if applicable
    const playlistInfo = document.getElementById('playlistInfo');
    const playlistModeOptions = document.getElementById('playlistModeOptions');
    const playlistText = document.getElementById('playlistText');

    if (info.is_playlist && info.playlist_count && info.playlist_count > 1) {
        if (playlistInfo) playlistInfo.style.display = 'flex';
        if (playlistText) {
            if (info.is_mix) {
                playlistText.textContent = `Mix: ${info.playlist_count} videos (showing up to 50)`;
            } else {
                playlistText.textContent = `Playlist: ${info.playlist_count} videos`;
            }
        }
        if (playlistModeOptions) playlistModeOptions.style.display = 'block';
    } else {
        if (playlistInfo) playlistInfo.style.display = 'none';
        if (playlistModeOptions) playlistModeOptions.style.display = 'none';
    }

    // Update quality options
    updateQualityOptions();

    // Show the section
    const videoSection = document.getElementById('videoSection');
    if (videoSection) {
        videoSection.style.display = 'block';
        videoSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function updateQualityOptions() {
    const mode = document.querySelector('input[name="downloadMode"]:checked').value;
    const select = document.getElementById('qualitySelect');

    if (mode === 'audio') {
        select.innerHTML = `
            <option value="320">320 kbps (Best)</option>
            <option value="256">256 kbps</option>
            <option value="192">192 kbps</option>
            <option value="128">128 kbps</option>
        `;
    } else {
        // Use qualities from backend (returned by fetch_video_info)
        if (currentVideoInfo && currentVideoInfo.qualities && currentVideoInfo.qualities.length > 1) {
            select.innerHTML = '';
            currentVideoInfo.qualities.forEach(q => {
                // Handle "Best" and formatted qualities like "1080p", "720p (2K)" etc.
                const value = q === 'Best' ? 'best' : q.replace(/[^0-9]/g, '');
                const label = q === 'Best' ? 'Best Available' : q;
                select.innerHTML += `<option value="${value}">${label}</option>`;
            });
        } else {
            // Fallback to common qualities
            select.innerHTML = `
                <option value="best">Best Available</option>
                <option value="1080">Full HD (1080p)</option>
                <option value="720">HD (720p)</option>
                <option value="480">SD (480p)</option>
                <option value="360">Low (360p)</option>
            `;
        }
    }
}

// ==================== DOWNLOAD ====================
async function startDownload() {
    if (!currentVideoInfo) {
        showStatus('Please fetch a video first', 'error');
        return;
    }

    const url = document.getElementById('urlInput').value.trim();
    const mode = document.querySelector('input[name="downloadMode"]:checked').value;
    const quality = document.getElementById('qualitySelect').value;

    // Get playlist mode if this is a playlist
    let playlistMode = 'single';
    const playlistModeEl = document.querySelector('input[name="playlistMode"]:checked');
    if (playlistModeEl && currentVideoInfo.is_playlist) {
        playlistMode = playlistModeEl.value;
    }

    // If "select" mode and no videos selected yet, open the playlist modal
    if (playlistMode === 'select' && currentVideoInfo.is_playlist && !selectedPlaylistIndices) {
        openPlaylistModal();
        showStatus('Please select videos from the playlist, then click Download Selected', 'info');
        return;
    }

    console.log('[Download] Starting: mode=' + mode + ', quality=' + quality + ', playlistMode=' + playlistMode);
    if (selectedPlaylistIndices) {
        console.log('[Download] Selected indices:', selectedPlaylistIndices);
    }

    // Show progress section
    const progressSection = document.getElementById('progressSection');
    progressSection.style.display = 'block';
    document.getElementById('downloadBtn').disabled = true;

    // Reset progress
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('downloadSpeed').textContent = '-';
    document.getElementById('downloadEta').textContent = '-';
    document.getElementById('downloadSize').textContent = '-';
    document.getElementById('progressStatus').textContent = 'Starting download...';

    // Check if this is a playlist download
    isPlaylistDownload = (playlistMode === 'all' || playlistMode === 'select') && currentVideoInfo.is_playlist;

    // Show/reset playlist progress section
    const playlistProgress = document.getElementById('playlistProgress');
    if (isPlaylistDownload && playlistProgress) {
        playlistProgress.style.display = 'block';
        document.getElementById('playlistProgressCount').textContent = '0/0 videos';
        document.getElementById('currentVideoTitle').textContent = 'Preparing...';
    } else if (playlistProgress) {
        playlistProgress.style.display = 'none';
    }

    try {
        // Pass selectedPlaylistIndices when in select mode
        const indices = (playlistMode === 'select') ? selectedPlaylistIndices : null;
        const result = await eel.start_download(url, mode, quality, playlistMode, indices)();
        if (!result) {
            showStatus('Failed to start download', 'error');
            resetDownloadUI();
        }
        // Reset selection after starting download
        selectedPlaylistIndices = null;
    } catch (e) {
        console.error('Download error:', e);
        showStatus('Download failed: ' + e.message, 'error');
        resetDownloadUI();
    }
}

async function cancelDownload() {
    try {
        await eel.cancel_download()();
        showStatus('Download cancelled', 'info');
        resetDownloadUI();
    } catch (e) {
        console.error('Cancel error:', e);
    }
}

function resetDownloadUI() {
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('downloadBtn').disabled = false;

    // Hide playlist progress
    const playlistProgress = document.getElementById('playlistProgress');
    if (playlistProgress) {
        playlistProgress.style.display = 'none';
    }
    isPlaylistDownload = false;
}

// ==================== PROGRESS CALLBACKS ====================
eel.expose(update_progress);
function update_progress(percent, speed, eta, size) {
    // Parse percent
    let numPercent = parseFloat(percent.replace('%', '').trim()) || 0;
    numPercent = Math.min(100, Math.max(0, numPercent));

    document.getElementById('progressBar').style.width = numPercent + '%';
    document.getElementById('downloadSpeed').textContent = speed || '-';
    document.getElementById('downloadEta').textContent = eta || '-';
    document.getElementById('downloadSize').textContent = size || '-';

    // Update status text based on download type
    if (isPlaylistDownload) {
        document.getElementById('progressStatus').textContent = `Downloading video... ${numPercent.toFixed(1)}%`;
    } else {
        document.getElementById('progressStatus').textContent = `Downloading... ${numPercent.toFixed(1)}%`;
    }
}

// Playlist progress callback
eel.expose(update_playlist_progress);
function update_playlist_progress(currentIndex, total, currentTitle, isDownloading) {
    const playlistProgress = document.getElementById('playlistProgress');
    const countEl = document.getElementById('playlistProgressCount');
    const titleEl = document.getElementById('currentVideoTitle');

    if (!playlistProgress) return;

    playlistProgress.style.display = 'block';

    // Update count
    if (countEl) {
        countEl.textContent = `${currentIndex}/${total} videos completed`;
    }

    // Update current video title
    if (titleEl) {
        if (isDownloading && currentIndex < total) {
            titleEl.textContent = currentTitle || 'Downloading...';
        } else if (!isDownloading) {
            titleEl.textContent = '✅ ' + currentTitle;
        }
    }

    // Update main progress status
    const statusEl = document.getElementById('progressStatus');
    if (statusEl && isDownloading) {
        statusEl.textContent = `Downloading video ${currentIndex + 1} of ${total}...`;
    }
}

eel.expose(download_complete);
function download_complete(success, message) {
    resetDownloadUI();

    if (success) {
        showStatus('âœ… Download complete!', 'success');

        // Show notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Download Complete', {
                body: currentVideoInfo?.title || 'Your video has been downloaded',
                icon: currentVideoInfo?.thumbnail
            });
        }
    } else {
        if (message && !message.includes('cancelled')) {
            showStatus('âŒ ' + message, 'error');
        }
    }
}

// ==================== STATUS MESSAGES ====================
function showStatus(message, type = 'info') {
    const container = document.getElementById('statusContainer');
    const messageEl = document.getElementById('statusMessage');

    messageEl.textContent = message;
    messageEl.className = 'status-message ' + type;
    container.style.display = 'block';

    // Auto-hide after 4 seconds
    setTimeout(() => {
        container.style.display = 'none';
    }, 4000);
}

// ==================== UPDATE FUNCTIONS ====================
async function checkForUpdates(silent = false) {
    try {
        const updateBtn = document.getElementById('updateBtn');
        if (!silent) {
            updateBtn.innerHTML = '&#8987;<span class="update-badge" id="updateBadge"></span>';
        }

        const result = await eel.check_for_updates()();

        // Restore button
        updateBtn.innerHTML = '&#128260;<span class="update-badge" id="updateBadge"></span>';

        console.log('Update check result:', result);

        if (result.success && result.update_available) {
            document.getElementById('updateBadge').classList.add('active');
            updateDownloadUrl = result.download_url;

            const versionText = result.is_nightly
                ? 'v' + result.current_version + ' \u2192 ' + result.latest_version
                : 'v' + result.current_version + ' \u2192 v' + result.latest_version;
            document.getElementById('updateVersionInfo').textContent = versionText;

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
        document.getElementById('updateBtn').innerHTML = '&#128260;<span class="update-badge" id="updateBadge"></span>';
        if (!silent) {
            showStatus('Failed to check for updates', 'error');
        }
    }
}

function showUpdateModal() {
    document.getElementById('updateModal').classList.add('active');
    document.getElementById('updateProgress').style.display = 'none';
    document.getElementById('updateButtons').style.display = 'flex';
    document.getElementById('updateStatus').textContent = 'A new version is available with improvements and bug fixes.';
}

function closeUpdateModal() {
    document.getElementById('updateModal').classList.remove('active');
    const version = document.getElementById('updateVersionInfo').textContent;
    localStorage.setItem('updateDismissed_' + version, 'true');
}

async function downloadAndInstallUpdate() {
    if (!updateDownloadUrl) {
        showStatus('No update URL available', 'error');
        return;
    }

    document.getElementById('updateButtons').style.display = 'none';
    document.getElementById('updateProgress').style.display = 'flex';
    document.getElementById('updateStatus').textContent = 'Downloading update...';

    try {
        await eel.download_update(updateDownloadUrl)();
    } catch (e) {
        console.error('Update download failed:', e);
        showStatus('Update failed: ' + e.message, 'error');
        closeUpdateModal();
    }
}

eel.expose(update_download_progress);
function update_download_progress(percent) {
    document.getElementById('updateProgressBar').style.width = percent + '%';
    document.getElementById('updateProgressText').textContent = percent + '%';
}

eel.expose(update_download_complete);
async function update_download_complete(success, pathOrError) {
    if (success) {
        updatePath = pathOrError;
        document.getElementById('updateStatus').textContent = 'Download complete! Installing...';

        try {
            await eel.apply_update(updatePath)();
        } catch (e) {
            console.error('Apply update failed:', e);
            showStatus('Failed to apply update', 'error');
            closeUpdateModal();
        }
    } else {
        showStatus('Update download failed: ' + pathOrError, 'error');
        closeUpdateModal();
    }
}


// ==================== PLAYLIST MODAL ====================
function openPlaylistModal() {
    const modal = document.getElementById('playlistModal');
    const playlistList = document.getElementById('playlistList');

    if (!modal || !playlistList || !currentVideoInfo || !currentVideoInfo.entries) {
        showStatus('No playlist data available', 'error');
        return;
    }

    // Clear previous content
    playlistList.innerHTML = '';

    // Populate with playlist entries (with thumbnails)
    currentVideoInfo.entries.forEach((entry, index) => {
        const item = document.createElement('div');
        item.className = 'playlist-item';
        const title = entry.title || 'Unknown';
        const num = index + 1;
        const thumbnail = entry.thumbnail || '';
        const duration = entry.duration_str || '';
        const uploader = entry.uploader || '';
        const originalIndex = entry.original_index !== undefined ? entry.original_index : index;

        item.innerHTML = `
            <label class="checkbox-container">
                <input type="checkbox" class="playlist-checkbox" data-index="${index}" data-original-index="${originalIndex}" onchange="updateSelectionCount()">
                <span class="checkmark"></span>
            </label>
            <div class="playlist-item-thumb">
                <img src="${thumbnail}" alt="" onerror="this.style.display='none'">
                ${duration ? `<span class="playlist-item-duration">${duration}</span>` : ''}
            </div>
            <div class="playlist-item-info">
                <span class="playlist-item-title">${title}</span>
                ${uploader ? `<span class="playlist-item-uploader">${uploader}</span>` : ''}
            </div>
        `;
        playlistList.appendChild(item);
    });

    // Reset selection count
    document.getElementById('selectAllCheckbox').checked = false;
    updateSelectionCount();

    // Show modal
    modal.style.display = 'flex';
}

function closePlaylistModal() {
    const modal = document.getElementById('playlistModal');
    if (modal) modal.style.display = 'none';
}

function toggleSelectAll() {
    const selectAll = document.getElementById('selectAllCheckbox');
    const checkboxes = document.querySelectorAll('.playlist-checkbox');

    checkboxes.forEach(cb => {
        cb.checked = selectAll.checked;
    });

    updateSelectionCount();
}

function updateSelectionCount() {
    const checkboxes = document.querySelectorAll('.playlist-checkbox:checked');
    const countEl = document.getElementById('selectionCount');
    if (countEl) {
        countEl.textContent = checkboxes.length + ' selected';
    }
}

function confirmPlaylistSelection() {
    const checkboxes = document.querySelectorAll('.playlist-checkbox:checked');
    // Use original_index for yt-dlp (1-indexed playlist_items)
    const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.originalIndex));

    if (selectedIndices.length === 0) {
        showStatus('Please select at least one video', 'error');
        return;
    }

    selectedPlaylistIndices = selectedIndices;
    closePlaylistModal();

    showStatus(selectedIndices.length + ' videos selected. Click Start Download to begin.', 'success');
}
