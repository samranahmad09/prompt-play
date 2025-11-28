'use strict';

(function() {
  const QR_API = 'https://api.qrserver.com/v1/create-qr-code/';
  const QR_SIZE = 280; // px
  const qrImage = document.getElementById('qrImage');
  const qrFrame = document.getElementById('qrFrame');
  const qrLoading = document.getElementById('qrLoading');
  const urlInput = document.getElementById('urlInput');
  const copyBtn = document.getElementById('copyBtn');
  const downloadBtn = document.getElementById('downloadBtn');
  const openBtn = document.getElementById('openBtn');
  const refreshBtn = document.getElementById('refreshBtn');
  const statusEl = document.getElementById('status');

  async function getActiveTabUrl() {
    try {
      const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
      const tab = tabs && tabs[0];
      if (!tab) return null;
      // Prefer url; fall back to pendingUrl if needed
      const url = tab.url || tab.pendingUrl || null;
      return url;
    } catch (e) {
      console.error('tabs.query failed', e);
      return null;
    }
  }

  function buildQrSrc(data) {
    const encoded = encodeURIComponent(data);
    const size = `${QR_SIZE}x${QR_SIZE}`;
    // Add margin to improve readability for some scanners
    return `${QR_API}?size=${size}&data=${encoded}&margin=20&format=png`;
  }

  function setStatus(msg, type = 'info') {
    statusEl.textContent = msg || '';
    statusEl.style.color = type === 'error' ? '#ff6b81' : type === 'success' ? '#10b981' : '';
  }

  function showLoading(show) {
    if (show) {
      qrLoading.style.display = 'grid';
      qrImage.classList.add('hidden');
    } else {
      qrLoading.style.display = 'none';
      qrImage.classList.remove('hidden');
    }
  }

  async function generateFor(url) {
    if (!url) {
      setStatus('Could not detect a URL for this tab.', 'error');
      return;
    }
    urlInput.value = url;
    const src = buildQrSrc(url);
    showLoading(true);
    // Replace src and wait for load/error
    await new Promise((resolve) => requestAnimationFrame(resolve));
    qrImage.onload = () => { showLoading(false); setStatus('QR ready.', 'success'); };
    qrImage.onerror = () => { showLoading(false); setStatus('Failed to load QR image. Try refresh.', 'error'); };
    qrImage.src = src;
  }

  async function init() {
    setStatus('Fetching active tab...');
    const url = await getActiveTabUrl();
    await generateFor(url);
  }

  copyBtn.addEventListener('click', async () => {
    try {
      const text = urlInput.value;
      if (!text) return;
      await navigator.clipboard.writeText(text);
      setStatus('URL copied to clipboard.', 'success');
    } catch (e) {
      setStatus('Copy failed. Select text and press Ctrl/Cmd+C.', 'error');
    }
  });

  downloadBtn.addEventListener('click', async () => {
    try {
      const src = qrImage.getAttribute('src');
      if (!src) return setStatus('Generate a QR first.', 'error');
      const a = document.createElement('a');
      a.href = src;
      a.download = 'qr-link.png';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setStatus('Downloading QR...', 'info');
    } catch (e) {
      setStatus('Download failed.', 'error');
    }
  });

  openBtn.addEventListener('click', async () => {
    const url = urlInput.value;
    if (!url) return;
    try {
      await chrome.tabs.create({ url });
    } catch (e) {
      // If blocked, try window.open as fallback (unlikely in popup context)
      window.open(url, '_blank');
    }
  });

  refreshBtn.addEventListener('click', async () => {
    setStatus('Refreshing...');
    showLoading(true);
    const url = await getActiveTabUrl();
    await generateFor(url);
  });

  // Allow click to select all
  urlInput.addEventListener('focus', () => {
    urlInput.select();
  });

  document.addEventListener('DOMContentLoaded', init);
})();
