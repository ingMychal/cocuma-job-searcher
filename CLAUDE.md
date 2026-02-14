# CLAUDE.md

## Project

Cocuma Job Searcher — Flask web app that scrapes job listings from https://www.cocuma.cz/jobs/ and lets users search by **job title and company name only** (not description). This solves cocuma.cz's overly broad full-text search.

## First step — always do this first

Assess the current state of the codebase. The project was partially refactored in Cursor. Some changes may be incomplete or missing. Read all files, identify what exists, what's broken, and what's missing before making any changes. Report your findings before proceeding.

## Architecture rules

- **One codebase, two modes** controlled by `PUBLIC_DEPLOY` env var.
  - Unset or falsy → local mode: manual refresh button visible, `/refresh` route works, scraper delay 0.1s.
  - Set to `1`/`true`/`yes`/`on` (case-insensitive, trimmed) → production mode: no refresh button, `/refresh` returns 404, scraper delay 1s, lazy background refresh enabled.
- **No separate branches or forks for local vs production.** Same code, different behavior from env var.

## Search rules

- Search only in **job title** and **company name**. Never description.
- Multi-word query = AND (each word must appear in title or company).
- Case-insensitive.
- Keywords come only from browser search input (`?q=`). No server-side defaults, no config files.

## Lazy background refresh (production mode only)

This is the most important feature to implement correctly:

1. User visits the page → serve existing `data/jobs.json` immediately (even if stale).
2. Check if `jobs.json` is missing or older than 12 hours.
3. If yes → start scrape in a **background thread** (never block the request).
4. Page includes a small JS snippet that polls a lightweight endpoint (e.g. `GET /last-update`) every few seconds.
5. When the background scrape finishes and the timestamp changes → JS reloads the page automatically. No loading spinner, no notification to user.
6. If scrape fails → do nothing. Keep serving old data. Log the error.
7. **Thread safety:** write to a temp file, then atomic rename to `jobs.json`. Never serve a half-written file.
8. **Prevent concurrent scrapes:** if a scrape is already running, skip (don't queue another one).

## Scraper rules

- Scrape only `/jobs/` and `/jobs/page/N/` — these are allowed by cocuma.cz/robots.txt.
- Never scrape `/jobs/?q=` URLs (disallowed by robots.txt).
- User-Agent header required.
- Timeout: 15s per request.
- Retries: 3 with backoff.
- Request delay: 0.1s (local) / 1s (production) — read from `PUBLIC_DEPLOY`.
- Extract: title, company, link, location, employment_type from job cards.
- Output: `data/jobs.json` — single file, overwritten only on full successful scrape.

## Data handling

- Single source of truth: `data/jobs.json`.
- Missing or corrupt file → empty list, no crash.
- Never overwrite on failed scrape.
- `data/` directory in `.gitignore`.

## UI

- Czech language interface.
- Banner at top: "Příležitosti jsou z cocuma.cz/jobs. S Cocuma nejsme nijak spojeni." with link.
- Search bar + "HLEDAT" button.
- Job cards grid (title, company, location, type) linking to cocuma.cz.
- Show last update timestamp.
- In local mode: show "Obnovit příležitosti z Cocuma" button.
- In production mode: no refresh button, no indication of background scraping.
- Empty state when no data: friendly message, no crash.

## Production deployment target

- **Render free tier** (or similar free PaaS).
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
- Env var: `PUBLIC_DEPLOY=1`
- No cron needed — lazy refresh handles everything.
- Ephemeral filesystem is fine — if `jobs.json` disappears, next visitor triggers background scrape.

## Dependencies

`requirements.txt` must include: flask, requests, beautifulsoup4, urllib3, gunicorn.

## Files to include

- `app.py` — Flask app with all routes
- `scraper.py` — Scraper logic
- `search.py` — Search/filter logic
- `templates/index.html` — Main page template
- `templates/error.html` — Error page
- `requirements.txt`
- `.gitignore`
- `robots.txt` route (disallow `/refresh` and `/?q=`)
- `run.command` — macOS double-click launcher for local use
- `README.md` — Short, explains what it does and how to run locally + deploy
- `CLAUDE.md` — This file

## Do NOT

- Do not add Docker, databases, cron jobs, or external schedulers.
- Do not expose `data/jobs.json` as a public endpoint.
- Do not allow any public user to trigger a scrape directly.
- Do not use JavaScript frameworks. Vanilla JS only where needed (the polling snippet).
- Do not over-engineer. This is a hobby project.

## Owner context

Owner is not a programmer (analyst). Keep code simple. He uses GitHub Desktop and macOS.
