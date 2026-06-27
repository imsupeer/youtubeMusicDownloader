let tracks = [];
let probeResult = null;
let eventSource = null;

const urlInput = document.getElementById('url-input');
const probeBtn = document.getElementById('probe-btn');
const probeStatus = document.getElementById('probe-status');
const bitrateSelect = document.getElementById('bitrate-select');
const outdirInput = document.getElementById('outdir-input');
const browseFolderBtn = document.getElementById('browse-folder-btn');
const trackList = document.getElementById('track-list');
const selectAllBtn = document.getElementById('select-all-btn');
const selectNoneBtn = document.getElementById('select-none-btn');
const progressBar = document.getElementById('progress-bar');
const footerStatus = document.getElementById('footer-status');
const downloadBtn = document.getElementById('download-btn');

function setStatus(message, tone = 'info') {
  footerStatus.textContent = message;
  probeStatus.textContent = message;
  const tones = {
    info: 'text-gray-400',
    success: 'text-emerald-400',
    error: 'text-red-400',
  };
  probeStatus.className = `text-sm ${tones[tone] || tones.info}`;
}

function setProgress(percent) {
  progressBar.style.width = `${Math.min(100, Math.max(0, percent))}%`;
}

function renderTracks() {
  if (!tracks.length) {
    trackList.innerHTML = '<li class="px-3 py-2">No tracks yet.</li>';
    selectAllBtn.classList.add('hidden');
    selectNoneBtn.classList.add('hidden');
    return;
  }

  const isPlaylist = probeResult?.type === 'playlist';
  selectAllBtn.classList.toggle('hidden', !isPlaylist);
  selectNoneBtn.classList.toggle('hidden', !isPlaylist);

  trackList.innerHTML = tracks
    .map(
      (track, index) => `
      <li class="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5">
        ${
          isPlaylist
            ? `<input type="checkbox" data-index="${index}" class="track-check rounded border-white/20 bg-surface-raised text-accent focus:ring-accent" checked />`
            : `<span class="w-4 h-4 rounded-full bg-accent/20 border border-accent/40"></span>`
        }
        <span class="truncate">${escapeHtml(track.title || track.url || 'Untitled')}</span>
      </li>`,
    )
    .join('');
}

function escapeHtml(value) {
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
}

function selectedTracks() {
  if (probeResult?.type !== 'playlist') return tracks;
  const checks = trackList.querySelectorAll('.track-check');
  return [...checks].filter((el) => el.checked).map((el) => tracks[Number(el.dataset.index)]);
}

async function loadConfig() {
  const res = await fetch('/api/config');
  const config = await res.json();
  outdirInput.value = config.default_outdir;
  bitrateSelect.innerHTML = config.bitrates
    .map((kbps) => `<option value="${kbps}" ${kbps === config.default_bitrate ? 'selected' : ''}>${kbps} kbps</option>`)
    .join('');
}

function connectEvents() {
  if (eventSource) eventSource.close();
  eventSource = new EventSource('/api/events');
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'progress') {
      setProgress(data.percent);
      setStatus(`${data.message} - ${Math.round(data.percent)}%`);
    } else if (data.type === 'started') {
      setProgress(0);
      setStatus(data.message);
      downloadBtn.disabled = true;
    } else if (data.type === 'completed') {
      setStatus(data.message, 'success');
    } else if (data.type === 'error') {
      setStatus(data.message, 'error');
      downloadBtn.disabled = false;
    } else if (data.type === 'idle') {
      setProgress(100);
      setStatus(data.message, 'success');
      downloadBtn.disabled = false;
    }
  };
  eventSource.onerror = () => {
    setTimeout(connectEvents, 2000);
  };
}

probeBtn.addEventListener('click', async () => {
  const url = urlInput.value.trim();
  if (!url) {
    setStatus('Enter a YouTube URL.', 'error');
    return;
  }
  probeBtn.disabled = true;
  setStatus('Detecting URL…');
  try {
    const res = await fetch('/api/probe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.detail || 'Probe failed');
    probeResult = body;
    tracks = body.entries || [];
    if (body.type === 'single') {
      setStatus(`Single video: ${body.title || tracks[0]?.title || 'Untitled'}`, 'success');
    } else if (body.type === 'playlist') {
      setStatus(`Playlist: ${tracks.length} tracks found - select what to download`, 'success');
    } else {
      tracks = [];
      setStatus('Unsupported URL.', 'error');
    }
    setProgress(0);
    renderTracks();
  } catch (err) {
    tracks = [];
    renderTracks();
    setStatus(err.message, 'error');
  } finally {
    probeBtn.disabled = false;
  }
});

selectAllBtn.addEventListener('click', () => {
  trackList.querySelectorAll('.track-check').forEach((el) => (el.checked = true));
});

selectNoneBtn.addEventListener('click', () => {
  trackList.querySelectorAll('.track-check').forEach((el) => (el.checked = false));
});

browseFolderBtn.addEventListener('click', async () => {
  browseFolderBtn.disabled = true;
  try {
    const initial = outdirInput.value.trim();
    const res = await fetch('/api/pick-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(initial ? { initial_dir: initial } : {}),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.detail || 'Could not open folder picker');
    if (body.path) {
      outdirInput.value = body.path;
      setStatus(`Output folder: ${body.path}`, 'success');
    }
  } catch (err) {
    setStatus(err.message, 'error');
  } finally {
    browseFolderBtn.disabled = false;
  }
});

downloadBtn.addEventListener('click', async () => {
  const selected = selectedTracks();
  if (!selected.length) {
    setStatus('No tracks selected.', 'error');
    return;
  }
  const outdir = outdirInput.value.trim();
  if (!outdir) {
    setStatus('Choose an output folder.', 'error');
    return;
  }
  downloadBtn.disabled = true;
  setProgress(0);
  setStatus(`Queuing ${selected.length} track(s)…`);
  try {
    const res = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        outdir,
        bitrate_kbps: Number(bitrateSelect.value),
        tracks: selected,
      }),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.detail || 'Download failed');
    setStatus(`Downloading ${body.queued} track(s)…`);
  } catch (err) {
    setStatus(err.message, 'error');
    downloadBtn.disabled = false;
  }
});

loadConfig();
connectEvents();
