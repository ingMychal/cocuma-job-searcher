# Cocuma Job Searcher

**Smarter search for [Cocuma](https://www.cocuma.cz/jobs/) jobs.** Search only by **job title** and **company name** — no more wading through descriptions. Type "manager" and get actual manager roles, not every listing that mentions the word somewhere.

---

### Run locally

**Double-click** `run.command` (macOS). The app starts and your browser opens automatically.

Or from the terminal:

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000/** (the app can open it for you).

### What you do

1. Click **Obnovit příležitosti z Cocuma** once to fetch the latest listings.
2. Search in the box (e.g. *project manager*) — results are filtered locally by title and company only.
3. Reload the page anytime; use **Obnovit…** again when you want fresh data from Cocuma.

Data is stored in `data/jobs.json`. No server account, no weird URLs — just double-click and search.
