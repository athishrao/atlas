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

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DEBUG=true uvicorn app.main:app --reload --port 8000
```
