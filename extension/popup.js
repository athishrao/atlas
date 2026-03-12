'use strict';

const DEFAULT_BASE_URL = 'http://atlas';

let allLinks   = [];
let baseUrl    = DEFAULT_BASE_URL;
let userEmail  = '';
let kbdIndex   = -1;   // keyboard-selected result index

const $ = id => document.getElementById(id);

// ── Settings ──────────────────────────────────────────────────────────────
async function loadSettings() {
  const s = await chrome.storage.local.get({ baseUrl: DEFAULT_BASE_URL, userEmail: '' });
  baseUrl   = (s.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
  userEmail = s.userEmail || '';
}

function apiHeaders() {
  const h = { 'Content-Type': 'application/json' };
  if (userEmail) h['X-Forwarded-User'] = userEmail;
  return h;
}

// ── Fetch all links on open ───────────────────────────────────────────────
async function fetchLinks() {
  try {
    const res = await fetch(`${baseUrl}/api/links?limit=500`);
    if (!res.ok) throw new Error(res.status);
    allLinks = await res.json();
    renderResults('');
  } catch {
    $('loadingState').textContent = `⚠ Cannot reach ${baseUrl} — check Options`;
  }
}

// ── Render filtered results ───────────────────────────────────────────────
function renderResults(query) {
  const list    = $('resultsList');
  const empty   = $('emptyState');
  const loading = $('loadingState');
  const kbd     = $('kbdHint');

  loading.hidden = true;
  kbdIndex = -1;

  const q = query.toLowerCase().trim();
  const filtered = q
    ? allLinks.filter(l =>
        l.short.includes(q) ||
        (l.description || '').toLowerCase().includes(q) ||
        l.url.toLowerCase().includes(q)
      )
    : allLinks;

  // ↵ key hint: active when there is at least one result
  kbd.classList.toggle('active', filtered.length > 0);

  list.innerHTML = '';

  if (filtered.length === 0) {
    list.hidden = true;
    empty.hidden = false;
    $('emptyQuery').textContent = q;
    return;
  }

  empty.hidden = true;
  list.hidden  = false;

  filtered.slice(0, 60).forEach((link, idx) => {
    const item = document.createElement('div');
    item.className = 'result-item';
    item.dataset.idx = idx;

    const displayUrl = link.url
      .replace(/^https?:\/\//, '')
      .replace(/^www\./, '');

    const hasDesc = !!(link.description && link.description.trim());

    item.innerHTML = `
      <span class="result-short">${esc(link.short)}</span>
      <div class="result-meta">
        ${hasDesc
          ? `<div class="result-title">${esc(link.description)}</div>
             <div class="result-url">${esc(displayUrl)}</div>`
          : `<div class="result-url primary">${esc(displayUrl)}</div>`
        }
      </div>
      <div class="result-actions">
        <button class="act-btn copy-btn" title="Copy link" data-short="${esc(link.short)}">⎘</button>
        <button class="act-btn open-btn" title="Open">↗</button>
      </div>
    `;

    item.querySelector('.copy-btn').addEventListener('click', e => {
      e.stopPropagation();
      const btn = e.currentTarget;
      const shortUrl = `${baseUrl}/${link.short}`;
      navigator.clipboard.writeText(shortUrl).then(() => {
        btn.textContent = '✓';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = '⎘'; btn.classList.remove('copied'); }, 1500);
      });
    });

    item.querySelector('.open-btn').addEventListener('click', e => {
      e.stopPropagation();
      openLink(link.short);
    });

    item.addEventListener('click', () => openLink(link.short));
    list.appendChild(item);
  });
}

function openLink(short) {
  chrome.tabs.update({ url: `${baseUrl}/${short}` });
  window.close();
}

// ── Keyboard navigation through results ──────────────────────────────────
function moveKbd(dir) {
  const items = $('resultsList').querySelectorAll('.result-item');
  if (!items.length) return;
  items[kbdIndex]?.classList.remove('kbd-selected');
  kbdIndex = Math.max(0, Math.min(items.length - 1, kbdIndex + dir));
  const sel = items[kbdIndex];
  sel.classList.add('kbd-selected');
  sel.scrollIntoView({ block: 'nearest' });
}

// ── View switching ────────────────────────────────────────────────────────
function switchToCreate(prefillShort = '') {
  $('searchView').hidden = true;
  $('createView').hidden = false;
  $('toggleCreate').textContent = '✕';
  $('toggleCreate').classList.add('active');
  $('createError').hidden = true;

  if (prefillShort) $('newShort').value = prefillShort;

  // Pre-fill URL from current tab
  chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
    const url = tabs[0]?.url;
    if (url && !url.startsWith('chrome://') && !url.startsWith('edge://')) {
      $('newUrl').value = url;
    }
    $('newShort').focus();
  });
}

function switchToSearch() {
  $('searchView').hidden = false;
  $('createView').hidden = true;
  $('toggleCreate').textContent = '+';
  $('toggleCreate').classList.remove('active');
  $('createError').hidden = true;
  $('createForm').reset();
  $('searchInput').focus();
}

// ── Status bar ────────────────────────────────────────────────────────────
function showStatus(msg, type = 'ok') {
  const bar = $('statusBar');
  bar.textContent = msg;
  bar.className = `status-bar ${type}`;
  bar.hidden = false;
  if (type === 'ok') setTimeout(() => { bar.hidden = true; }, 2500);
}

// ── Escape for HTML ───────────────────────────────────────────────────────
function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Event wiring ──────────────────────────────────────────────────────────
$('toggleCreate').addEventListener('click', () => {
  $('createView').hidden ? switchToCreate() : switchToSearch();
});

$('searchInput').addEventListener('input', e => {
  renderResults(e.target.value);
});

$('searchInput').addEventListener('keydown', e => {
  const q = $('searchInput').value.trim().toLowerCase();
  if (e.key === 'ArrowDown') { e.preventDefault(); moveKbd(+1); return; }
  if (e.key === 'ArrowUp')   { e.preventDefault(); moveKbd(-1); return; }

  if (e.key === 'Enter') {
    // If keyboard-navigated to a result, open that one
    const selected = $('resultsList').querySelector('.kbd-selected');
    if (selected) { selected.click(); return; }

    // Exact match → navigate
    const exact = allLinks.find(l => l.short === q);
    if (exact) { openLink(exact.short); return; }

    // No match but typed something → let atlas handle it (search fallback)
    if (q) { openLink(q); }
  }
});

// Keyboard shortcut: N = new link
document.addEventListener('keydown', e => {
  if (e.key === 'n' && document.activeElement !== $('searchInput') &&
      document.activeElement.tagName !== 'INPUT') {
    switchToCreate();
  }
});

$('createFromEmpty').addEventListener('click', () => {
  switchToCreate($('searchInput').value.trim());
});

$('createForm').addEventListener('submit', async e => {
  e.preventDefault();
  const short = $('newShort').value.trim().toLowerCase();
  const url   = $('newUrl').value.trim();
  const desc  = $('newDesc').value.trim();
  if (!short || !url) return;

  const btn   = $('submitBtn');
  const errEl = $('createError');
  btn.disabled = true;
  btn.textContent = 'Creating…';
  errEl.hidden = true;

  try {
    const res = await fetch(`${baseUrl}/api/links`, {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({ short, url, description: desc }),
    });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.detail || `Error ${res.status}`;
      errEl.hidden = false;
    } else {
      allLinks.unshift(data);
      switchToSearch();
      showStatus(`✓  ${short} → ${url.replace(/^https?:\/\//, '').slice(0, 40)}`, 'ok');
    }
  } catch {
    errEl.textContent = 'Network error — is atlas running?';
    errEl.hidden = false;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Create link →';
  }
});

// ── Init ──────────────────────────────────────────────────────────────────
(async () => {
  await loadSettings();
  await fetchLinks();
  $('searchInput').focus();
})();
