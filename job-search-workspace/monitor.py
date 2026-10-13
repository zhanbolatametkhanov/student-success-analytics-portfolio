from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "profile.json"
DB_PATH = ROOT / "data" / "jobs.sqlite3"
STATE_PATH = ROOT / "data" / "monitor_state.json"
API_URL = "https://www.arbeitnow.com/api/job-board-api"
MAX_PAGES_PER_SCAN = 3
USER_AGENT = "PersonalJobSearchWorkspace/1.0 (+https://www.arbeitnow.com/blog/job-board-api)"

ROLE_TERMS = (
    "data analyst", "data engineer", "business analyst", "business systems",
    "business intelligence", "systems analyst", "system analyst", "systems engineer",
    "system engineer", "system administrator", "it administrator", "it manager",
    "it lead", "it operations", "infrastructure engineer", "cloud engineer",
    "reporting analyst", "reporting", "power bi", "sql developer", "data management",
    "research data", "research support", "university it", "higher education technology",
    "academic technology", "campus management", "erp", "sap", "digital systems",
    "application support", "systems integration", "data quality", "software engineer",
)
AUSTRIA_TERMS = (
    "austria", "österreich", "osterreich", "vienna", "wien", "graz", "linz",
    "salzburg", "innsbruck", "klagenfurt", "sankt pölten", "sankt polten",
    "st. pölten", "st. polten", "wels", "dornbirn", "villach", "burgenland",
    "lower austria", "upper austria", "styria", "tyrol", "carinthia", "vorarlberg",
)
NON_FULL_TIME = (
    "part-time", "part time", "teilzeit", "praktikum", "internship",
    "working student", "werkstudent", "mini-job", "minijob", "freelance only",
)


class PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.parts.append(text)


def strip_html(value: str) -> str:
    parser = PlainText()
    try:
        parser.feed(value or "")
        return html.unescape(" ".join(parser.parts))
    except Exception:
        return html.unescape(re.sub(r"<[^>]+>", " ", value or ""))


def load_local_env() -> None:
    """Load ignored .env key/value pairs without printing secrets."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value
    except OSError:
        return


def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        return {}
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, dedupe_key TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL, company TEXT NOT NULL, location TEXT DEFAULT '',
        job_url TEXT DEFAULT '', description TEXT DEFAULT '', requirements TEXT DEFAULT '',
        employment_type TEXT DEFAULT 'Unknown', work_arrangement TEXT DEFAULT 'Unclear',
        source TEXT DEFAULT 'Manual entry', posted_date TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Inbox', notes TEXT DEFAULT '',
        cover_letter TEXT DEFAULT '', interest_answer TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
    return db


def profile_keywords(profile: dict) -> set[str]:
    terms = set(ROLE_TERMS)
    for role in profile.get("target_roles", []):
        if isinstance(role, str) and role.strip():
            terms.add(role.strip().casefold())
    for group in (profile.get("skills") or {}).values():
        if isinstance(group, list):
            terms.update(x.strip().casefold() for x in group if isinstance(x, str) and x.strip())
    resume_text = str(profile.get("resume_text") or "").casefold()
    standard = (
        "python", "sql", "excel", "power bi", "tableau", "jira", "confluence",
        "git", "gerrit", "ci/cd", "monitoring", "cloud", "virtualisation",
        "virtualization", "network infrastructure", "cybersecurity", "security audits",
        "backup", "disaster recovery", "erlang", "html", "css", "erp", "sap",
        "data analysis", "data analytics", "data quality", "reporting", "kpi",
        "dashboard", "stakeholder", "project management", "it management",
        "engineering management", "research support", "higher education",
        "software development", "risk management", "budget planning", "forecasting",
        "process improvement", "documentation", "runbooks", "systems integration",
    )
    terms.update(term for term in standard if term in resume_text)
    return terms


def convert_posting(post: dict, keywords: set[str], source_name: str = "Arbeitnow public job-board API") -> dict | None:
    title = str(post.get("title") or "").strip()
    company = str(post.get("company_name") or "").strip()
    url = str(post.get("url") or "").strip()
    location = str(post.get("location") or "").strip()
    description = strip_html(str(post.get("description") or ""))
    job_types = post.get("job_types") or []
    job_types_text = " ".join(str(x) for x in job_types)
    remote = bool(post.get("remote"))
    fulltext = f"{title} {company} {location} {job_types_text} {description}".casefold()

    if not title or not company or urlparse(url).scheme != "https":
        return None

    relevant = any(term in fulltext for term in keywords)
    if not relevant:
        return None

    in_austria = any(term in location.casefold() for term in AUSTRIA_TERMS)
    # Remote ads are included as "verify eligible country"; a remote flag does not
    # prove the employer permits work from Austria.
    remote_only = remote
    if not in_austria and not remote_only:
        return None

    title_and_type = f"{title} {job_types_text}".casefold()
    if any(term in title_and_type for term in NON_FULL_TIME):
        return None

    commitment = job_types_text.casefold()
    if any(term in commitment for term in ("full-time", "full time", "vollzeit")):
        employment_type = "Full-time"
    elif any(term in commitment for term in ("part-time", "teilzeit", "internship", "praktikum")):
        employment_type = "Part-time"
    else:
        employment_type = "Unknown"

    if remote and location and not in_austria:
        location = f"{location} · remote (verify country eligibility)"
    elif remote and not location:
        location = "Remote (verify country eligibility)"

    timestamp = post.get("created_at")
    posted_date = ""
    if isinstance(timestamp, (int, float)):
        posted_date = datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat()
    elif isinstance(timestamp, str) and timestamp.strip():
        try:
            posted_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            posted_date = timestamp[:10] if len(timestamp) >= 10 else ""

    return {
        "title": title,
        "company": company,
        "location": location or "Location not specified",
        "job_url": url,
        "description": description[:30000],
        "requirements": "",
        "employment_type": employment_type,
        "work_arrangement": "Remote" if remote else "Unclear",
        "source": source_name,
        "posted_date": posted_date,
    }


def upsert(job: dict) -> bool:
    url = str(job.get("job_url") or "").strip()
    if not url or urlparse(url).scheme != "https":
        return False
    dedupe_key = hashlib.sha256(("url:" + url.rstrip("/").casefold()).encode("utf-8")).hexdigest()
    values = (
        dedupe_key, job["title"], job["company"], job["location"], url,
        job.get("description", ""), job.get("requirements", ""),
        job.get("employment_type", "Unknown"), job.get("work_arrangement", "Unclear"),
        job.get("source", "Arbeitnow public job-board API"), job.get("posted_date", ""),
    )
    with connect() as db:
        before = db.total_changes
        db.execute("""INSERT OR IGNORE INTO jobs
            (dedupe_key,title,company,location,job_url,description,requirements,
             employment_type,work_arrangement,source,posted_date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", values)
        return db.total_changes > before


def scan_adzuna(session: requests.Session, keywords: set[str]) -> tuple[int, int, list[str]]:
    app_id = os.environ.get("ADZUNA_APP_ID", "").strip()
    app_key = os.environ.get("ADZUNA_APP_KEY", "").strip()
    if not app_id or not app_key:
        return 0, 0, []
    searches = [
        ("data analyst", "Vienna"),
        ("data engineer", "Austria"),
        ("business systems analyst", "Austria"),
        ("systems engineer", "Austria"),
        ("IT manager", "Vienna"),
    ]
    seen = added = 0
    errors: list[str] = []
    for what, where in searches:
        try:
            response = session.get(
                f"https://api.adzuna.com/v1/api/jobs/at/search/1",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "results_per_page": 50,
                    "what": what,
                    "where": where,
                    "full_time": 1,
                    "max_days_old": 14,
                    "sort_by": "date",
                    "content-type": "application/json",
                },
                timeout=(8, 25),
            )
            response.raise_for_status()
            payload = response.json()
            entries = payload.get("results", [])
            if not isinstance(entries, list):
                errors.append(f"Adzuna search '{what}' did not contain a results list.")
                continue
            seen += len(entries)
            for item in entries:
                if not isinstance(item, dict):
                    continue
                loc = item.get("location") or {}
                comp = item.get("company") or {}
                redirect_url = str(item.get("redirect_url") or item.get("adref") or "").strip()
                desc = str(item.get("description") or "")
                locname = str(loc.get("display_name") or where)
                remote = any(term in f"{item.get('title', '')} {desc}".casefold() for term in ("remote", "home office", "homeoffice", "fully remote"))
                posting = {
                    "title": item.get("title", ""),
                    "company_name": comp.get("display_name", "Unspecified employer"),
                    "location": locname,
                    "url": redirect_url,
                    "description": desc,
                    "job_types": ["Full-time"],
                    "remote": remote,
                    "created_at": item.get("created"),
                }
                job = convert_posting(posting, keywords, source_name="Adzuna Austria API")
                if job and upsert(job):
                    added += 1
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"Adzuna '{what}' in {where}: {type(exc).__name__}: {exc}")
        time.sleep(1)
    return seen, added, errors


def scan_once() -> dict:
    load_local_env()
    profile = load_profile()
    keywords = profile_keywords(profile)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    seen_api = 0
    added = 0
    pages_scanned = 0
    errors: list[str] = []
    for page in range(1, MAX_PAGES_PER_SCAN + 1):
        pages_scanned = page
        try:
            response = session.get(API_URL, params={"page": page}, timeout=(8, 25))
            response.raise_for_status()
            payload = response.json()
            entries = payload.get("data", [])
            if not isinstance(entries, list):
                errors.append(f"Arbeitnow API page {page} did not contain a data list.")
                break
            if not entries:
                break
            seen_api += len(entries)
            for post in entries:
                if not isinstance(post, dict):
                    continue
                job = convert_posting(post, keywords)
                if job and upsert(job):
                    added += 1
            # Respect the provider's pagination metadata and keep scans bounded.
            if not (payload.get("links") or {}).get("next"):
                break
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"Arbeitnow page {page}: {type(exc).__name__}: {exc}")
            break
        finally:
            time.sleep(1)
    adzuna_seen, adzuna_added, adzuna_errors = scan_adzuna(session, keywords)
    seen_api += adzuna_seen
    added += adzuna_added
    errors.extend(adzuna_errors)
    state = {
        "last_scan_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": ["Arbeitnow public job-board API"] + (["Adzuna Austria API"] if os.environ.get("ADZUNA_APP_ID") and os.environ.get("ADZUNA_APP_KEY") else []),
        "arbeitnow_pages_scanned": pages_scanned,
        "api_listings_seen": seen_api,
        "new_matches_added": added,
        "adzuna_configured": bool(os.environ.get("ADZUNA_APP_ID") and os.environ.get("ADZUNA_APP_KEY")),
        "errors": errors,
        "interval_hours": None,
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False), flush=True)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuously monitor permitted public job data for Austria/Vienna/remote role matches.")
    parser.add_argument("--once", action="store_true", help="Scan once and exit.")
    parser.add_argument("--interval-hours", type=float, default=6.0, help="Hours between scans; minimum 1 hour.")
    args = parser.parse_args()
    interval = max(1.0, args.interval_hours)
    if args.once:
        state = scan_once()
        return 0 if not state["errors"] else 1

    print(f"Starting monitor; scans every {interval:g} hour(s). Press Ctrl+C to stop.", flush=True)
    try:
        while True:
            state = scan_once()
            print(f"Next scan in {interval:g} hour(s).", flush=True)
            time.sleep(interval * 3600)
    except KeyboardInterrupt:
        print("Monitor stopped.", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
