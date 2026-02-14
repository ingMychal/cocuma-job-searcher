"""
Cocuma Job Searcher – local web app.
Search runs only on job title and company name. Data from data/jobs.json; refresh overwrites it.

Dual mode controlled by PUBLIC_DEPLOY env var:
  - Unset/falsy → local mode (manual refresh button, 0.1s scraper delay)
  - Set to 1/true/yes/on → production mode (no refresh, 1s delay, lazy background refresh)
"""
import logging
import os
import threading
import time
import webbrowser
from datetime import datetime
from threading import Timer

from flask import Flask, Response, abort, redirect, render_template, request, url_for

from scraper import load_jobs, save_jobs_atomic, scrape_jobs
from search import filter_jobs_by_title_or_company

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# --- Dual mode ---

_TRUTHY = {"1", "true", "yes", "on"}


def _is_public_deploy() -> bool:
    val = os.environ.get("PUBLIC_DEPLOY", "").strip().lower()
    return val in _TRUTHY


PUBLIC_DEPLOY = _is_public_deploy()

# --- Background refresh state (production only) ---

_scrape_lock = threading.Lock()
_scrape_running = False
STALE_SECONDS = 12 * 60 * 60  # 12 hours


def _jobs_are_stale(data_dir: str) -> bool:
    """Return True if jobs.json is missing or older than 12 hours."""
    path = os.path.join(data_dir, "jobs.json")
    if not os.path.isfile(path):
        return True
    try:
        age = time.time() - os.path.getmtime(path)
        return age > STALE_SECONDS
    except OSError:
        return True


def _background_scrape(data_dir: str, delay: float) -> None:
    """Run scrape in background thread. Skips if another scrape is already running."""
    global _scrape_running
    try:
        jobs = scrape_jobs(delay=delay)
        save_jobs_atomic(data_dir, jobs)
        logger.info("Background scrape done: %d jobs saved", len(jobs))
    except Exception:
        logger.exception("Background scrape failed — keeping old data")
    finally:
        with _scrape_lock:
            _scrape_running = False


def _maybe_trigger_background_scrape() -> None:
    """If production mode and data is stale, start a background scrape (once at a time)."""
    global _scrape_running
    if not PUBLIC_DEPLOY:
        return
    if not _jobs_are_stale(DATA_DIR):
        return
    with _scrape_lock:
        if _scrape_running:
            return
        _scrape_running = True
    t = threading.Thread(target=_background_scrape, args=(DATA_DIR, 1.0), daemon=True)
    t.start()


# --- Helpers ---


def _last_update_iso(data_dir: str) -> str | None:
    """Return last update time of jobs.json as formatted string, or None if missing."""
    path = os.path.join(data_dir, "jobs.json")
    if not os.path.isfile(path):
        return None
    try:
        m = os.path.getmtime(path)
        return datetime.fromtimestamp(m).strftime("%d. %m. %Y, %H:%M")
    except OSError:
        return None


# --- Routes ---


@app.route("/")
def index():
    _maybe_trigger_background_scrape()
    q = request.args.get("q", "").strip()
    jobs = load_jobs(DATA_DIR)
    if q:
        jobs = filter_jobs_by_title_or_company(jobs, q)
    last_update = _last_update_iso(DATA_DIR)
    return render_template(
        "index.html",
        jobs=jobs,
        query=q,
        last_update=last_update,
        public_deploy=PUBLIC_DEPLOY,
    )


@app.route("/refresh")
def refresh():
    if PUBLIC_DEPLOY:
        abort(404)
    current_q = request.args.get("q", "").strip()
    try:
        jobs = scrape_jobs(delay=0.1)
        save_jobs_atomic(DATA_DIR, jobs)
        logger.info("Scraped %d jobs and saved to %s", len(jobs), os.path.join(DATA_DIR, "jobs.json"))
        return redirect(url_for("index", q=current_q or None))
    except Exception:
        logger.exception("Refresh failed")
        return (
            render_template("error.html", message="Nepodařilo se načíst příležitosti. Zkuste to později."),
            502,
        )


@app.route("/robots.txt")
def robots_txt():
    body = "User-agent: *\nDisallow: /refresh\nDisallow: /?q=\n"
    return Response(body, mimetype="text/plain")


if __name__ == "__main__":
    def _open_browser():
        webbrowser.open("http://127.0.0.1:5000/")

    Timer(1.2, _open_browser).start()
    app.run(debug=True, port=5000)
