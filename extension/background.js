'use strict';

const DEFAULT_BASE_URL = 'http://atlas';

async function getSettings() {
  return chrome.storage.local.get({ baseUrl: DEFAULT_BASE_URL, userEmail: '' });
}

// ── Omnibox suggestions (type "go <query>" in address bar) ────────────────
chrome.omnibox.onInputChanged.addListener(async (text, suggest) => {
  const q = text.trim();
  if (!q) return;
  try {
    const { baseUrl } = await getSettings();
    const url = `${baseUrl.replace(/\/$/, '')}/api/links?q=${encodeURIComponent(q)}&limit=6`;
    const res = await fetch(url);
    if (!res.ok) return;
    const links = await res.json();
    if (!links.length) return;
    suggest(links.map(l => ({
      content: l.short,
      description: `<match>${l.short}</match>  —  ${l.url}${l.description ? '  ·  ' + l.description : ''}`,
    })));
  } catch { /* atlas unreachable */ }
});

// ── Omnibox navigation (press Enter after typing "go <short>") ────────────
chrome.omnibox.onInputEntered.addListener(async (text, disposition) => {
  const { baseUrl } = await getSettings();
  const target = `${baseUrl.replace(/\/$/, '')}/${text.trim()}`;

  switch (disposition) {
    case 'currentTab':
      chrome.tabs.update({ url: target });
      break;
    case 'newForegroundTab':
      chrome.tabs.create({ url: target });
      break;
    case 'newBackgroundTab':
      chrome.tabs.create({ url: target, active: false });
      break;
  }
});
