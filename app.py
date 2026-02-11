"""
Cocuma Job Searcher – local web app.
Search runs only on job title and company name. Data from data/jobs.json; refresh overwrites it.
"""
import logging
import os
import webbrowser
from datetime import datetime
from threading import Timer

from flask import Flask, redirect, render_template, request, url_for

from scraper import load_jobs, save_jobs, scrape_jobs
from search import filter_jobs_by_title_or_company

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _last_update_iso(data_dir: str) -> str | None:
    """Return last update time of jobs.json as ISO string, or None if missing."""
    path = os.path.join(data_dir, "jobs.json")
    if not os.path.isfile(path):
        return None
    try:
        m = os.path.getmtime(path)
        return datetime.fromtimestamp(m).strftime("%d. %m. %Y, %H:%M")
    except OSError:
        return None


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    jobs = load_jobs(DATA_DIR)
    if q:
        jobs = filter_jobs_by_title_or_company(jobs, q)
    last_update = _last_update_iso(DATA_DIR)
    return render_template("index.html", jobs=jobs, query=q, last_update=last_update)


@app.route("/refresh")
def refresh():
    current_q = request.args.get("q", "").strip()
    try:
        jobs = scrape_jobs()
        save_jobs(DATA_DIR, jobs)
        logger.info("Scraped %d jobs and saved to %s", len(jobs), os.path.join(DATA_DIR, "jobs.json"))
        return redirect(url_for("index", q=current_q or None))
    except Exception as e:
        logger.exception("Refresh failed")
        return (
            render_template("error.html", message="Nepodařilo se načíst příležitosti. Zkuste to později."),
            502,
        )


if __name__ == "__main__":
    def _open_browser():
        webbrowser.open("http://127.0.0.1:5000/")

    Timer(1.2, _open_browser).start()
    app.run(debug=True, port=5000)
