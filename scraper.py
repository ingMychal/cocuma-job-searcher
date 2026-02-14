"""
Scrape Cocuma job listings and save as JSON.
Uses retries, timeout, User-Agent, and rate limiting. Only overwrites data on full success.
Atomic writes via temp file + os.replace() to prevent serving half-written data.
"""
import json
import logging
import os
import tempfile
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

BASE_URL = "https://www.cocuma.cz"
JOBS_URL = "https://www.cocuma.cz/jobs/"
TIMEOUT_SEC = 15
MAX_RETRIES = 3
MAX_PAGES = 100

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _session():
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers["User-Agent"] = USER_AGENT
    return s


def _parse_job_card(card, base_url: str) -> dict | None:
    """Extract job fields from a job-thumbnail card. Returns None if no title/link."""
    href = card.get("href")
    if not href:
        return None
    link = href if href.startswith("http") else urljoin(base_url, href)

    title_el = card.find("p", class_="job-thumbnail-title")
    title = title_el.get_text(strip=True) if title_el else ""

    company = ""
    location = ""
    employment_type = ""

    # Collect all text segments from card (order preserved where possible)
    texts = []
    for el in card.find_all(["p", "span", "div"]):
        t = el.get_text(strip=True)
        if t and t not in texts:
            texts.append(t)

    if not title and texts:
        title = max((t for t in texts if len(t) > 3), key=len, default="")

    for t in texts:
        if t in ("Full-time", "Part-time"):
            employment_type = t
            break

    # Known badges and types to exclude from company/location
    skip = {"Fresh", "Superjoby", "Full-time", "Part-time", title}
    rest = [t for t in texts if t and t not in skip]

    if rest:
        company = rest[0]
    if len(rest) >= 2:
        # Last before employment_type is usually location
        location = rest[-1] if rest[-1] not in ("Full-time", "Part-time") else (rest[-2] if len(rest) > 2 else "")

    return {
        "title": title,
        "company": company or "",
        "link": link,
        "location": location,
        "employment_type": employment_type or "",
    }


def scrape_jobs(delay: float = 0.1) -> list[dict]:
    """
    Fetch all job pages from Cocuma and return list of job dicts.
    Raises on failure so caller can avoid overwriting existing data.

    Args:
        delay: seconds to wait between page requests (0.1 local, 1.0 production).
    """
    session = _session()
    jobs: list[dict] = []
    seen_links: set[str] = set()
    page = 1

    while page <= MAX_PAGES:
        url = JOBS_URL if page == 1 else f"{JOBS_URL}page/{page}/"
        try:
            r = session.get(url, timeout=TIMEOUT_SEC)
        except requests.RequestException:
            logger.exception("Request failed for %s", url)
            raise

        if r.status_code != 200:
            break

        soup = BeautifulSoup(r.content, "html.parser")
        cards = soup.find_all("a", class_="job-thumbnail")

        if not cards:
            break

        for card in cards:
            job = _parse_job_card(card, BASE_URL)
            if not job or not job.get("title") or not job.get("link"):
                continue
            if job["link"] in seen_links:
                continue
            seen_links.add(job["link"])
            jobs.append(job)

        page += 1
        time.sleep(delay)

    return jobs


def load_jobs(data_dir: str) -> list[dict]:
    """Load jobs from data/jobs.json. Return [] if file missing or invalid."""
    path = os.path.join(data_dir, "jobs.json")
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_jobs_atomic(data_dir: str, jobs: list[dict]) -> None:
    """Write jobs to data/jobs.json atomically (temp file + os.replace)."""
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "jobs.json")
    fd, tmp_path = tempfile.mkstemp(dir=data_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
