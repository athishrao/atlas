'use strict';

const DEFAULT_BASE_URL = 'http://atlas';

async function load() {
  const s = await chrome.storage.local.get({ baseUrl: DEFAULT_BASE_URL, userEmail: '' });
  document.getElementById('baseUrl').value   = s.baseUrl;
  document.getElementById('userEmail').value = s.userEmail;
}

document.getElementById('saveBtn').addEventListener('click', async () => {
  const baseUrl   = (document.getElementById('baseUrl').value.trim() || DEFAULT_BASE_URL).replace(/\/$/, '');
  const userEmail = document.getElementById('userEmail').value.trim();
  await chrome.storage.local.set({ baseUrl, userEmail });

  const msg = document.getElementById('savedMsg');
  msg.classList.add('show');
  setTimeout(() => msg.classList.remove('show'), 2000);
});

document.getElementById('testBtn').addEventListener('click', async () => {
  const baseUrl = (document.getElementById('baseUrl').value.trim() || DEFAULT_BASE_URL).replace(/\/$/, '');
  const res_el  = document.getElementById('testResult');
  res_el.textContent = 'Checking…';
  res_el.className = '';

  try {
    const res  = await fetch(`${baseUrl}/health`, { signal: AbortSignal.timeout(4000) });
    const data = await res.json();
    if (res.ok && data.status === 'ok') {
      res_el.textContent = '✓ Connected';
      res_el.className   = 'ok';
    } else {
      res_el.textContent = `✕ Unexpected response (${res.status})`;
      res_el.className   = 'err';
    }
  } catch (e) {
    res_el.textContent = `✕ Cannot reach ${baseUrl}`;
    res_el.className   = 'err';
  }
});

load();
