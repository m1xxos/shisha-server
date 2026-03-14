/* Music Parser – frontend logic */

function toggleAdvanced() {
  const panel = document.getElementById('advancedPanel');
  panel.classList.toggle('open');
}

function setStatus(state, message) {
  const el = document.getElementById('status');
  el.className = `show ${state}`;

  const spinner = (state === 'pending' || state === 'downloading')
    ? '<div class="spinner"></div>'
    : '';

  const icons = { done: '✅', error: '❌' };
  const icon = icons[state] ? `<span>${icons[state]}</span>` : '';

  el.innerHTML = `${spinner}${icon}<span>${message}</span>`;
}

function hideStatus() {
  document.getElementById('status').className = '';
  document.getElementById('status').innerHTML = '';
}

async function pollJob(jobId) {
  const interval = 2000; // ms
  const maxAttempts = 300; // 10 minutes

  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(r => setTimeout(r, interval));

    let data;
    try {
      const resp = await fetch(`/api/jobs/${jobId}`);
      data = await resp.json();
    } catch {
      setStatus('error', 'Lost connection to server.');
      return;
    }

    if (data.status === 'done') {
      setStatus('done', data.message);
      document.getElementById('downloadBtn').disabled = false;
      return;
    }

    if (data.status === 'error') {
      setStatus('error', data.message);
      document.getElementById('downloadBtn').disabled = false;
      return;
    }

    // pending / downloading
    setStatus(data.status, data.message);
  }

  setStatus('error', 'Timed out waiting for job to finish.');
  document.getElementById('downloadBtn').disabled = false;
}

async function startDownload() {
  const url = document.getElementById('url').value.trim();
  if (!url) {
    setStatus('error', 'Please enter a URL.');
    return;
  }

  const payload = {
    url,
    start_time: document.getElementById('startTime').value.trim() || null,
    end_time:   document.getElementById('endTime').value.trim()   || null,
    title:      document.getElementById('metaTitle').value.trim() || null,
    artist:     document.getElementById('metaArtist').value.trim() || null,
    album:      document.getElementById('metaAlbum').value.trim() || null,
  };

  document.getElementById('downloadBtn').disabled = true;
  setStatus('pending', 'Queuing job…');

  let jobId;
  try {
    const resp = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || 'Server error');
    }

    const data = await resp.json();
    jobId = data.job_id;
  } catch (e) {
    setStatus('error', `Failed to start: ${e.message}`);
    document.getElementById('downloadBtn').disabled = false;
    return;
  }

  setStatus('downloading', 'Downloading audio…');
  pollJob(jobId);
}

// Allow pressing Enter in the URL field
document.getElementById('url').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') startDownload();
});
