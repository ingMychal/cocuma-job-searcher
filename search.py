"""
Local search over jobs: matches only job title OR company name (never description).
Multi-word queries use AND: each word must appear in title or company. Case-insensitive.
"""


def _normalize(s: str) -> str:
    if not s:
        return ""
    return " ".join(str(s).lower().split())


def _words(query: str) -> list[str]:
    if not query or not query.strip():
        return []
    return [w for w in query.strip().split() if w]


def filter_jobs_by_title_or_company(jobs: list[dict], query: str) -> list[dict]:
    """
    Filter jobs so the search query matches only in job title or company name.
    Does not search in description or any other field.

    - Case-insensitive.
    - Multi-word: each word must appear in either title or company (AND).
    """
    words = _words(query)
    if not words:
        return list(jobs)

    normalized_words = [_normalize(w) for w in words]
    result = []

    for job in jobs:
        title = _normalize((job.get("title") or ""))
        company = _normalize((job.get("company") or ""))

        match = True
        for nw in normalized_words:
            if nw not in title and nw not in company:
                match = False
                break
        if match:
            result.append(job)

    return result
