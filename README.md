# atlas

Atlas is a self-hosted internal link shortener for teams. Instead of pasting long URLs into Slack or bookmarking tools, you give each destination a short, memorable name and navigate to it directly from your browser's address bar.

For example, typing `atlas/standup` lands you on your daily standup meeting link, `atlas/deploy` opens your CI pipeline, and `atlas/handbook` opens the company wiki — no searching, no bookmarks

Links are shared across the team, searchable, and owned by whoever created them. Admins can edit or delete any link; everyone else can only edit their own.

## How it works

- Type `atlas/<shortname>` in your browser → instantly redirected to the destination
- If the short name doesn't exist, you land on the directory with a pre-filled search
- Local file paths (`file://`) are supported — atlas shows a copy button instead of trying to redirect
- Click counts are tracked per link

## Quick Start

```bash
docker compose up
```

Then add your chosen hostname to `/etc/hosts`:

```
127.0.0.1  atlas
```

Open `http://atlas` in your browser.

## DNS Setup

For team-wide use, make the hostname resolve on every machine:

- **Internal DNS** — add an A record: `atlas.  IN A  <server-ip>`
- **`/etc/hosts`** — add `<server-ip>  atlas` on each machine (sudo required)

## Configuration

Set these in `docker-compose.yml` or a `.env` file:

| Variable       | Default                | Description                                          |
| -------------- | ---------------------- | ---------------------------------------------------- |
| `APP_NAME`     | `atlas`                | App title shown in the UI                            |
| `BASE_URL`     | `http://atlas`         | Public base URL; determines the display prefix       |
| `DATABASE_URL` | `sqlite:///./atlas.db` | SQLAlchemy connection string                         |
| `ATLAS_ADMINS` | _(empty)_              | Comma-separated admin emails                         |
| `DEBUG`        | `false`                | Skip auth, attribute all requests to `dev@localhost` |

## Auth

Atlas trusts the `X-Forwarded-User` header for user identity. In production, put an auth proxy in front (Nginx + oauth2-proxy, Authelia, Cloudflare Access) and have it inject the header.

Set `DEBUG=true` to skip auth entirely — suitable for a trusted internal network or local use.

## Bundles

Bundles group related links under a single short name. Visiting `atlas/onboarding` opens a landing page listing every link in the bundle — useful for checklists, project toolkits, or any set of links you share together.

**Example:** a bundle called `onboarding` might contain `handbook`, `jira`, `slack`, and `vpn`. Share `atlas/onboarding` with a new hire and they get all four in one place.

### Creating a bundle

1. Go to **Bundles** in the sidebar → **+ New Bundle**
2. Give it a short name (same rules as links — lowercase, alphanumeric, hyphens)
3. Add a display name, optional description, icon, and colour
4. Type link short names into the link selector to add them to the bundle
5. Save - the bundle is immediately available at `atlas/<short>`

### Bundle landing page

Visiting a bundle short name shows a card for each link in the bundle with its name, URL, and a direct link. Visit counts are tracked separately from individual link click counts.

## Browser Extension (Chrome)

The extension lets you search links and create new ones from any tab, without opening the Atlas UI. It also adds omnibox support so you can navigate by typing `go <shortname>` directly in the address bar.

### Install

1. Open `chrome://extensions`
2. Enable **Developer mode** (toggle, top-right)
3. Click **Load unpacked** → select the `extension/` folder in this repo
4. Pin the Atlas icon to your toolbar

### First-time setup

Right-click the extension icon → **Options**:

- **Base URL** — set to your Atlas address (default `http://atlas`). Click **Test connection** to verify.
- **User email** — only needed if Atlas is _not_ behind a proxy that injects `X-Forwarded-User`. Leave blank for the standard nginx setup.

### Using the popup

Click the ⌘ icon in the toolbar:

- **Search** — type to filter all links instantly. Press `↑ ↓` to navigate, `Enter` to open.
- **Open** — click any row, or press `Enter` on an exact short name match.
- **Copy** — click `⎘` on any row to copy the full short URL to clipboard.
- **Create** — click `+` (or press `N`). The current tab's URL is pre-filled. Submit creates the link immediately via the API.
- If no match is found, a **Create this link** shortcut appears pre-filled with your search query.

### Omnibox

In your browser omnibox, type `go` and then hit `tab` to enter Atlas search mode.

```
go standup        → navigates to atlas/standup
go dep            → shows autocomplete suggestions matching "dep"
```

Press `Enter` to open in the current tab, or `Alt+Enter` for a new tab.

## Import / Export

Atlas can export all your links and bundles to a file and restore them from it. Find this under **Import / Export** in the sidebar.

### Formats

**JSON** — full fidelity, includes links and bundles. Use this for backups, migrations, or moving data between Atlas instances.

```json
{
  "version": 1,
  "exported_at": "2025-01-15T10:30:00+00:00",
  "links": [
    { "short": "gh", "url": "https://github.com/org", "description": "GitHub" }
  ],
  "bundles": [
    {
      "short": "dev",
      "name": "Dev Tools",
      "description": "Daily tools",
      "icon": "🛠️",
      "color": "cyan",
      "link_shorts": ["gh", "jira", "figma"]
    }
  ]
}
```

**CSV** — good for bulk editing in a spreadsheet. The file has two sections separated by a blank line: `# LINKS` followed by `# BUNDLES`. Bundle link lists are stored as pipe-separated values in the `link_shorts` column.

```
# LINKS
short,url,description
gh,https://github.com/org,GitHub
jira,https://jira.company.com,Jira

# BUNDLES
short,name,description,icon,color,link_shorts
dev,Dev Tools,Daily tools,🛠️,cyan,gh|jira
```

### Exporting

Click **Export JSON** or **Export CSV** on the Import / Export page. The file downloads immediately with a timestamped filename (`atlas-export-YYYYMMDD-HHMMSS`).

### Importing

1. Go to **Import / Export** in the sidebar
2. Drop a `.json` or `.csv` file onto the upload area (or click to browse)
3. Choose a conflict strategy:
   - **Skip** — leave existing links and bundles untouched if their short name already exists
   - **Overwrite** — update the URL, description, and bundle contents of any existing entries
4. Click **Import** — a result banner shows how many entries were added, skipped, or errored

Imports are atomic per-format: if the file cannot be parsed at all, nothing is written. Individual rows that are missing required fields (short name or URL) are counted as errors but do not abort the rest of the import.

> **Tip:** To migrate between instances, export JSON from the old instance, spin up the new one, and import the file. All links and bundles are restored with their original short names.

Bundles are included in JSON exports and restored on import. CSV exports also include bundles, with their link list stored as a pipe-separated value in the `link_shorts` column.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DEBUG=true uvicorn app.main:app --reload --port 8000
```
