from __future__ import annotations
import csv
import hashlib
import ipaddress
import io
import json
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import feedparser
import requests
import streamlit as st
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "profile.json"
DB_PATH = ROOT / "data" / "jobs.sqlite3"
PRIVATE_RESUME_PATH = ROOT / "data" / "private_resume.pdf"
MONITOR_PID_PATH = ROOT / "data" / "monitor.pid"
MONITOR_LOG_PATH = ROOT / "data" / "monitor.log"
STATUSES = ["Inbox", "Shortlisted", "Draft Ready", "Ready for Review", "Applied", "Interview", "Offer", "Rejected", "Withdrawn", "Closed"]


def load_profile():
    if not PROFILE_PATH.exists():
        PROFILE_PATH.write_text((ROOT / "profile.example.json").read_text(encoding="utf-8"), encoding="utf-8")
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def monitor_status():
    """Return (running, pid), validating that PID belongs to monitor.py."""
    try:
        pid = int(MONITOR_PID_PATH.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False, None
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", "ignore")
        running = "monitor.py" in cmdline and "job-search-workspace" in cmdline
    except OSError:
        try:
            os.kill(pid, 0)
            running = True
        except OSError:
            running = False
    if not running:
        try:
            MONITOR_PID_PATH.unlink()
        except OSError:
            pass
        return False, None
    return True, pid


def start_monitor():
    running, pid = monitor_status()
    if running:
        return pid
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_handle = MONITOR_LOG_PATH.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "monitor.py"), "--interval-hours", "6"],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )
    log_handle.close()
    MONITOR_PID_PATH.write_text(str(process.pid), encoding="utf-8")
    return process.pid


def stop_monitor():
    running, pid = monitor_status()
    if not running or pid is None:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        MONITOR_PID_PATH.unlink()
    except OSError:
        pass
    return True


def tail_monitor_log(max_lines=30):
    try:
        lines = MONITOR_LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-max_lines:])
    except OSError:
        return "No monitor log yet."


def save_profile(profile):
    PROFILE_PATH.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect() as db:
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


def safe_url(url):
    p = urlparse((url or "").strip())
    return p.scheme in ("https", "http") and bool(p.hostname) and not p.username and not p.password


def add_job(job):
    title, company = str(job.get("title") or "").strip(), str(job.get("company") or "").strip()
    if not title or not company:
        raise ValueError("Job title and company are required.")
    url = str(job.get("job_url") or "").strip()
    if url and not safe_url(url):
        raise ValueError("The job URL must be a valid HTTP(S) URL.")
    key_source = "url:" + url.rstrip("/").casefold() if url else "job:" + "|".join(" ".join(str(job.get(k) or "").casefold().split()) for k in ("title", "company", "location"))
    key = hashlib.sha256(key_source.encode()).hexdigest()
    values = (key, title, company, str(job.get("location") or ""), url,
              str(job.get("description") or ""), str(job.get("requirements") or ""),
              str(job.get("employment_type") or "Unknown"), str(job.get("work_arrangement") or "Unclear"),
              str(job.get("source") or "Manual entry"), str(job.get("posted_date") or ""))
    with connect() as db:
        cur = db.execute("""INSERT OR IGNORE INTO jobs
        (dedupe_key,title,company,location,job_url,description,requirements,employment_type,work_arrangement,source,posted_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""", values)
        if cur.rowcount:
            return True
        return False


def jobs_all():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY created_at DESC,id DESC").fetchall()]


def get_job(job_id):
    with connect() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?", (int(job_id),)).fetchone()
        return dict(row) if row else None


def update_job(job_id, **fields):
    allowed = {"status", "notes", "cover_letter", "interest_answer"}
    clean = {k: v for k, v in fields.items() if k in allowed}
    if not clean:
        return
    clean["updated_at"] = date.today().isoformat()
    sql = ", ".join(f"{k}=?" for k in clean)
    with connect() as db:
        db.execute(f"UPDATE jobs SET {sql} WHERE id=?", (*clean.values(), int(job_id)))


RESUME_KEYWORDS = [
    "Python", "SQL", "Excel", "Power BI", "Tableau", "Jira", "Confluence",
    "Git", "Gerrit", "CI/CD", "monitoring", "cloud", "virtualization",
    "virtualisation", "network infrastructure", "cybersecurity", "security audits",
    "backup", "disaster recovery", "Erlang", "HTML", "CSS", "ERP", "SAP",
    "data analysis", "data analytics", "data quality", "reporting", "KPI",
    "dashboard", "stakeholder", "project management", "IT management",
    "engineering management", "research support", "higher education",
    "academic technology", "software development", "risk management",
    "budget planning", "forecasting", "process improvement", "documentation",
    "runbooks", "systems integration", "Linux", "cloud infrastructure"
]


def profile_terms(profile):
    terms = []
    for group in (profile.get("skills") or {}).values():
        terms.extend(group if isinstance(group, list) else [])
    terms.extend(profile.get("target_roles", []))
    resume_text = str(profile.get("resume_text") or "").casefold()
    terms.extend(term for term in RESUME_KEYWORDS if term.casefold() in resume_text)
    return sorted({str(x).strip() for x in terms if str(x).strip()}, key=str.casefold)


def score(job, profile):
    text = " ".join(str(job.get(k) or "") for k in ("title", "description", "requirements")).casefold()
    terms = profile_terms(profile)
    matched = [term for term in terms if term.casefold() in text]
    skill_pct = min(100, round(100 * len(matched) / max(1, min(10, len(terms)))))
    role_hits = [r for r in profile.get("target_roles", []) if r.casefold() in (job.get("title", "") + " " + job.get("description", "")).casefold()]
    role_pct = min(100, 35 * len(role_hits) + (20 if any(w in (job.get("title", "") + " " + job.get("description", "")).casefold() for w in ("analyst", "engineer", "systems", "data", "academic", "technology")) else 0))
    locations = [x.casefold() for x in profile.get("preferred_locations", [])]
    jobloc = (job.get("location") or "").casefold()
    if not jobloc:
        location_pct = 25
    elif any(x in jobloc or jobloc in x for x in locations):
        location_pct = 100
    elif "remote" in jobloc and any("remote" in x for x in locations):
        location_pct = 100
    else:
        location_pct = 20
    contract_pct = 100 if "full" in (job.get("employment_type") or "").casefold() else (0 if job.get("employment_type") in ("Part-time", "Contract", "Internship") else 50)
    total = round(skill_pct * .45 + role_pct * .25 + location_pct * .20 + contract_pct * .10)
    gaps = []
    if not jobloc: gaps.append("Confirm work location and on-site expectations.")
    if job.get("employment_type") in ("Unknown", ""): gaps.append("Confirm that the role is full-time.")
    if any(x in text for x in ("visa", "sponsorship", "authorised", "authorized", "work permit")): gaps.append("Verify work authorisation and sponsorship conditions.")
    if "german" in text or "deutsch" in text: gaps.append("Verify the required German level.")
    if not matched: gaps.append("No profile skill keywords matched; read the description manually.")
    return {"score": total, "skill_score": skill_pct, "role_score": role_pct, "location_score": location_pct, "contract_score": contract_pct, "matched": matched[:12], "role_hits": role_hits, "gaps": gaps}


def check_public_feed(url):
    if not safe_url(url):
        raise ValueError("Enter a valid public HTTP(S) feed URL.")
    p = urlparse(url)
    host = (p.hostname or "").casefold()
    if host == "linkedin.com" or host.endswith(".linkedin.com") or host in ("localhost", "localhost.localdomain"):
        raise ValueError("LinkedIn and localhost are not supported as feed sources.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)}
        if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
            raise ValueError("The feed hostname must resolve only to public IP addresses.")
    except socket.gaierror as exc:
        raise ValueError("Could not resolve the feed hostname.") from exc
    response = requests.get(url, timeout=15, allow_redirects=False, headers={"User-Agent": "PersonalJobSearchWorkspace/1.0"})
    if 300 <= response.status_code < 400:
        raise ValueError("This feed redirects; use the final public feed URL directly.")
    response.raise_for_status()
    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        raise ValueError("The URL did not return a readable RSS/Atom feed.")
    result = []
    for entry in parsed.entries:
        link = str(entry.get("link") or "").strip()
        if not link or not safe_url(link):
            continue
        result.append({"title": str(entry.get("title") or "Untitled listing"), "company": str(entry.get("author") or (entry.get("source", {}).get("title") if isinstance(entry.get("source"), dict) else entry.get("source")) or "Unspecified employer"), "location": "", "job_url": link, "description": str(entry.get("summary") or ""), "requirements": "", "employment_type": "Unknown", "work_arrangement": "Unclear", "source": host, "posted_date": str(entry.get("published") or "")})
    return result


def draft_cover(job, profile):
    name = profile.get("name") or "Applicant"
    highlights = profile.get("verified_highlights") or []
    evidence = "\n".join(f"- {x}" for x in highlights[:3]) if highlights else "- [Add verified experience relevant to this role]"
    return f"""Dear Hiring Team,

I am writing to express my interest in the {job['title']} position at {job['company']}. The role appears relevant to my background in systems, data, engineering and operational improvement.

Relevant experience from my profile:
{evidence}

I would welcome the opportunity to discuss how this experience could contribute to your team. I have tailored this draft from my saved profile and will review every statement for accuracy and relevance before sending it.

Kind regards,
{name}"""


def draft_interest(job, profile):
    return f"I am interested in the {job['title']} role at {job['company']} because it appears aligned with my background in systems, data, reporting and technical operations. I would tailor this statement further after reviewing the responsibilities and confirming the specific requirements."


def make_application_pack(job, profile, letter, interest, resume_upload=None):
    """Build a review pack in memory; no forms are filled or submissions sent."""
    buffer = io.BytesIO()
    job_summary = (
        f"Job: {job.get('title', '')}\n"
        f"Company: {job.get('company', '')}\n"
        f"Location: {job.get('location', '')}\n"
        f"Employment type: {job.get('employment_type', '')}\n"
        f"Work arrangement: {job.get('work_arrangement', '')}\n"
        f"Official URL: {job.get('job_url', '')}\n"
        f"Source: {job.get('source', '')}\n"
    )
    review_checklist = (
        "Before applying, review each item:\n"
        "- Confirm all claims in the CV and cover letter are accurate.\n"
        "- Confirm full-time status, location, language, salary, work authorisation, and sponsorship.\n"
        "- Complete any employer-specific application questions yourself.\n"
        "- Read any declarations and privacy notices before agreeing.\n"
        "- Submit only on the employer's official application page.\n"
    )
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("job-details.txt", job_summary)
        archive.writestr("cover-letter-draft.txt", letter or "[Draft not prepared yet]")
        archive.writestr("screening-interest-draft.txt", interest or "[Draft not prepared yet]")
        archive.writestr("review-checklist.txt", review_checklist)
        evidence = "\n".join(profile.get("verified_highlights") or [])
        archive.writestr("candidate-evidence-to-review.txt", evidence or "Review the candidate profile and add verified role-specific evidence.")
        pdf_bytes = None
        pdf_name = "resume.pdf"
        if resume_upload is not None:
            try:
                pdf_name = Path(resume_upload.name).name
                if pdf_name.lower().endswith(".pdf"):
                    pdf_bytes = resume_upload.getvalue()
            except Exception:
                pdf_bytes = None
        elif PRIVATE_RESUME_PATH.exists():
            try:
                pdf_bytes = PRIVATE_RESUME_PATH.read_bytes()
            except OSError:
                pdf_bytes = None
        if pdf_bytes:
            archive.writestr(f"resume/{pdf_name}", pdf_bytes)
        else:
            archive.writestr("resume/README.txt", "No PDF is saved in this local workspace. Upload your CV in Profile & data before preparing an application pack.")
    return buffer.getvalue()


st.set_page_config(page_title="Personal Job-Search Workspace", page_icon="🧭", layout="wide")
init_db()
profile = load_profile()
st.title("🧭 Personal Job-Search Workspace")
st.caption("Local-first job discovery, transparent fit scoring, editable drafts, and a manual-review application tracker.")
st.info("Privacy default: no external AI, no LinkedIn scraping, no account automation, and no automatic application submission. Data is saved to local files in this workspace.")

with st.sidebar:
    st.subheader("Search preferences")
    st.write("**Locations**")
    st.write(", ".join(profile.get("preferred_locations", [])) or "Add locations under Profile & data")
    st.write("**Target roles**")
    for role in profile.get("target_roles", []): st.write(f"- {role}")
    st.caption("Verify eligibility, language, salary, and sponsorship directly with each employer.")
    st.caption(f"Local database: {DB_PATH}")

tabs = st.tabs(["Overview", "Add / import jobs", "Match jobs", "Drafts", "Application tracker", "Profile & data", "Austria search", "Continuous monitor"])
with tabs[0]:
    records = jobs_all()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jobs saved", len(records))
    c2.metric("Shortlisted", sum(x["status"] == "Shortlisted" for x in records))
    c3.metric("Drafts ready", sum(x["status"] in ("Draft Ready", "Ready for Review") for x in records))
    c4.metric("Applied", sum(x["status"] == "Applied" for x in records))
    st.subheader("Recent jobs")
    if records:
        st.dataframe([{"Fit": score(j, profile)["score"], "Title": j["title"], "Company": j["company"], "Location": j["location"], "Status": j["status"], "Added": j["created_at"]} for j in records[:10]], use_container_width=True, hide_index=True)
    else:
        st.write("Your tracker is empty. Add a role manually, import CSV, or use a permitted public job feed.")
    st.subheader("Daily workflow")
    st.markdown("1. Add or import a listing.  2. Read match evidence and gaps.  3. Shortlist promising roles.  4. Prepare and edit drafts.  5. Review and apply personally on the employer's official site.")

with tabs[1]:
    st.subheader("Add a job manually")
    with st.form("manual_job", clear_on_submit=True):
        a, b = st.columns(2)
        title = a.text_input("Job title *")
        company = b.text_input("Company / institution *")
        location = a.text_input("Location", placeholder="Vienna, Austria; Remote (eligible country)")
        url = b.text_input("Official job URL")
        employment = a.selectbox("Employment type", ["Full-time", "Part-time", "Contract", "Internship", "Unknown"])
        arrangement = b.selectbox("Work arrangement", ["On-site", "Hybrid", "Remote", "Unclear"])
        description = st.text_area("Job description", height=140)
        requirements = st.text_area("Requirements (optional)", height=90)
        submitted = st.form_submit_button("Save job")
    if submitted:
        try:
            ok = add_job({"title": title, "company": company, "location": location, "job_url": url, "employment_type": employment, "work_arrangement": arrangement, "description": description, "requirements": requirements, "source": "Manual entry"})
            st.success("Job saved." if ok else "Duplicate detected; existing record kept.")
        except ValueError as e: st.error(str(e))
    st.divider()
    st.subheader("Import CSV")
    st.caption("Required columns: title, company. Optional: location, job_url, description, requirements, employment_type, work_arrangement, source, posted_date.")
    template = "title,company,location,job_url,description,requirements,employment_type,work_arrangement,source,posted_date\nData Analyst,Example Employer,\"Vienna, Austria\",https://example.com/jobs/123,\"Python; Excel; KPI reporting\",\"Power BI; SQL\",Full-time,Hybrid,CSV example,2026-10-01\n"
    st.download_button("Download CSV template", template, "job_import_template.csv", "text/csv")
    up = st.file_uploader("Choose CSV file", type=["csv"])
    if up and st.button("Import CSV"):
        added = skipped = 0
        errors = []
        try:
            reader = csv.DictReader(io.StringIO(up.getvalue().decode("utf-8-sig", errors="replace")))
            if not reader.fieldnames: raise ValueError("CSV requires a header row.")
            for number, row in enumerate(reader, start=2):
                row = {str(k or "").strip().casefold().replace(" ", "_"): str(v or "").strip() for k, v in row.items()}
                row["source"] = row.get("source") or "CSV import"
                try:
                    if add_job(row): added += 1
                    else: skipped += 1
                except ValueError as exc: errors.append(f"Row {number}: {exc}"); skipped += 1
            st.success(f"Added {added}; skipped {skipped}.")
            for err in errors[:10]: st.warning(err)
        except Exception as exc: st.error(f"CSV import failed: {exc}")
    st.divider()
    st.subheader("Import a public RSS / Atom job feed")
    st.caption("Use only permitted public feeds. LinkedIn pages, login-only URLs, private hosts, and redirecting feeds are rejected.")
    feed_url = st.text_input("Public feed URL", placeholder="https://example.org/jobs/rss.xml")
    if st.button("Fetch and import feed"):
        try:
            entries = check_public_feed(feed_url)
            added = sum(1 for entry in entries if add_job(entry))
            st.success(f"Feed processed: {added} new job(s), {len(entries)-added} duplicate(s).")
        except Exception as exc: st.error(f"Feed import failed: {exc}")

with tabs[2]:
    st.subheader("Transparent job-fit ranking")
    st.caption("Weights: skills 45%, role match 25%, location 20%, full-time status 10%. Scores prioritise review; they do not predict hiring outcomes.")
    query = st.text_input("Filter by title, company, location, or text")
    minimum = st.slider("Minimum fit score", 0, 100, 0, 5)
    for job in jobs_all():
        result = score(job, profile)
        haystack = " ".join(str(job.get(k) or "") for k in ("title", "company", "location", "description", "requirements"))
        if result["score"] < minimum or (query and query.casefold() not in haystack.casefold()): continue
        with st.expander(f"{result['score']}/100 · {job['title']} — {job['company']}"):
            st.write(f"**Location:** {job['location'] or 'Not specified'} · **Type:** {job['employment_type']} · **Arrangement:** {job['work_arrangement']}")
            x1, x2, x3, x4 = st.columns(4)
            x1.metric("Skills", f"{result['skill_score']}%")
            x2.metric("Role", f"{result['role_score']}%")
            x3.metric("Location", f"{result['location_score']}%")
            x4.metric("Full-time", f"{result['contract_score']}%")
            st.write("**Matching profile terms:** " + (", ".join(result["matched"]) if result["matched"] else "No exact keyword evidence found"))
            st.write("**Role evidence:** " + (", ".join(result["role_hits"]) if result["role_hits"] else "No exact target-role title match"))
            for gap in result["gaps"]: st.warning(gap)
            if job.get("job_url") and safe_url(job["job_url"]): st.link_button("Open official job listing", job["job_url"])

with tabs[3]:
    st.subheader("Prepare application drafts")
    records = jobs_all()
    if not records: st.write("Add a job before drafting.")
    else:
        options = {f"#{j['id']} · {j['title']} — {j['company']}": j["id"] for j in records}
        picked = st.selectbox("Choose a job", list(options))
        job = get_job(options[picked])
        if job.get("job_url") and safe_url(job["job_url"]): st.link_button("Open job listing", job["job_url"])
        st.caption("Drafts use local templates and your saved candidate facts. Nothing is sent to an employer or AI service.")
        if st.button("Generate cover-letter draft"):
            update_job(job["id"], cover_letter=draft_cover(job, profile), status="Draft Ready")
            st.rerun()
        if st.button("Generate screening-interest draft"):
            update_job(job["id"], interest_answer=draft_interest(job, profile))
            st.rerun()
        job = get_job(job["id"])
        if job.get("cover_letter"):
            letter = st.text_area("Cover-letter draft — edit and verify before use", job["cover_letter"], height=300, key=f"letter_{job['id']}")
            if st.button("Save edited cover letter"):
                update_job(job["id"], cover_letter=letter, status="Ready for Review")
                st.success("Draft saved locally.")
        if job.get("interest_answer"):
            answer = st.text_area("Screening-interest draft — edit and verify", job["interest_answer"], height=160, key=f"answer_{job['id']}")
            if st.button("Save screening answer"):
                update_job(job["id"], interest_answer=answer)
                st.success("Answer saved locally.")
        if job.get("cover_letter"): st.download_button("Download cover letter TXT", job["cover_letter"], f"cover_letter_{job['id']}.txt", "text/plain")
        if job.get("cover_letter"):
            resume_upload = st.session_state.get("resume_pdf_upload")
            pack = make_application_pack(job, profile, job.get("cover_letter", ""), job.get("interest_answer", ""), resume_upload)
            st.download_button("Download application review pack (ZIP)", pack, f"application_pack_{job['id']}.zip", "application/zip")

with tabs[4]:
    st.subheader("Application tracker")
    records = jobs_all()
    if records:
        stages = st.selectbox("Filter stage", ["All"] + STATUSES)
        visible = [j for j in records if stages == "All" or j["status"] == stages]
        st.dataframe([{"ID": j["id"], "Title": j["title"], "Company": j["company"], "Location": j["location"], "Stage": j["status"], "Updated": j["updated_at"]} for j in visible], use_container_width=True, hide_index=True)
        opts = {f"#{j['id']} · {j['title']} — {j['company']} [{j['status']}]": j["id"] for j in visible}
        if opts:
            chosen = st.selectbox("Edit record", list(opts))
            job = get_job(opts[chosen])
            with st.form(f"tracker_{job['id']}"):
                stage = st.selectbox("Stage", STATUSES, index=STATUSES.index(job["status"]) if job["status"] in STATUSES else 0)
                notes = st.text_area("Notes / follow-up", job["notes"], height=120)
                save = st.form_submit_button("Save tracker record")
            if save:
                update_job(job["id"], status=stage, notes=notes)
                st.success("Tracker updated.")
                st.rerun()
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "title", "company", "location", "job_url", "employment_type", "work_arrangement", "source", "status", "notes", "created_at", "updated_at"])
        writer.writeheader()
        writer.writerows([{k: j.get(k, "") for k in writer.fieldnames} for j in records])
        st.download_button("Export tracker CSV", output.getvalue(), f"job_tracker_{date.today().isoformat()}.csv", "text/csv")
    else: st.write("No jobs saved yet.")
    st.caption("Only mark a role Applied after you personally submit it outside this app.")

with tabs[5]:
    st.subheader("Candidate profile")
    st.caption("This profile is local-only. Review all facts and keep work authorisation, sponsorship, salary, and education status unconfirmed until you verify them.")
    with st.form("profile_edit"):
        name = st.text_input("Name", profile.get("name", ""))
        current_location = st.text_input("Current location", profile.get("current_location", ""))
        preferred_locations = st.text_area("Preferred locations (one per line)", "\n".join(profile.get("preferred_locations", [])))
        target_roles = st.text_area("Target roles (one per line)", "\n".join(profile.get("target_roles", [])))
        highlights = st.text_area("Résumé facts / verified highlights (one per line)", "\n".join(profile.get("verified_highlights", [])), height=220)
        unknowns = st.text_area("Details to confirm (one per line)", "\n".join(profile.get("unknowns_to_confirm", [])), height=140)
        skill_text = {k: st.text_area(f"Skills — {k}", ", ".join(v), height=80) for k, v in (profile.get("skills") or {}).items()}
        save = st.form_submit_button("Save candidate profile")
    if save:
        profile.update({"name": name.strip(), "current_location": current_location.strip(),
            "preferred_locations": [x.strip() for x in preferred_locations.splitlines() if x.strip()],
            "target_roles": [x.strip() for x in target_roles.splitlines() if x.strip()],
            "verified_highlights": [x.strip() for x in highlights.splitlines() if x.strip()],
            "unknowns_to_confirm": [x.strip() for x in unknowns.splitlines() if x.strip()],
            "skills": {k: [x.strip() for x in v.split(",") if x.strip()] for k, v in skill_text.items()}})
        save_profile(profile)
        st.success("Profile saved locally.")
        st.rerun()
    st.write(f"Profile file: {PROFILE_PATH}")
    st.write(f"Database file: {DB_PATH}")
    st.write("Do not commit profile.json, your résumé, the database, saved drafts, or application notes to this public repository. Codespaces are cloud-hosted; run locally if files must remain physically on your computer.")

    st.divider()
    st.subheader("Use your résumé PDF")
    st.warning("When this app runs in Codespaces, an uploaded PDF enters that cloud-hosted environment. The app extracts text locally in this workspace and does not send it to an AI API. For on-device-only processing, run the app on your own computer.")
    resume_upload = st.file_uploader("Upload your current CV (PDF)", type=["pdf"], key="resume_pdf_upload")
    if resume_upload is not None and st.button("Extract résumé text and save to private profile"):
        try:
            reader = PdfReader(io.BytesIO(resume_upload.getvalue()))
            extracted = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
            if not extracted:
                st.error("No selectable text was found. This may be a scanned PDF; this starter app does not run OCR.")
            else:
                PRIVATE_RESUME_PATH.parent.mkdir(parents=True, exist_ok=True)
                PRIVATE_RESUME_PATH.write_bytes(resume_upload.getvalue())
                profile["resume_text"] = extracted
                profile["resume_filename"] = Path(resume_upload.name).name
                save_profile(profile)
                st.success("Résumé text and PDF saved inside this private workspace. Both are ignored by Git.")
                st.rerun()
        except Exception as exc:
            st.error(f"Could not read this PDF: {exc}")
    if profile.get("resume_text"):
        st.success(f"Résumé text saved locally ({len(profile['resume_text']):,} characters). Matching now considers recognisable résumé skill terms.")
        with st.expander("Preview extracted résumé text"):
            st.text_area("Extracted text (preview/edit not saved here)", str(profile["resume_text"])[:12000], height=260, disabled=True)
        if st.button("Remove extracted résumé text from profile"):
            profile.pop("resume_text", None)
            profile.pop("resume_filename", None)
            save_profile(profile)
            st.success("Saved résumé text removed from profile.")
            st.rerun()
    if PRIVATE_RESUME_PATH.exists():
        st.caption(f"Saved PDF: {PRIVATE_RESUME_PATH.name} ({PRIVATE_RESUME_PATH.stat().st_size:,} bytes)")
        if st.button("Delete saved résumé PDF"):
            try:
                PRIVATE_RESUME_PATH.unlink()
                st.success("Saved résumé PDF deleted.")
                st.rerun()
            except OSError as exc:
                st.error(f"Could not delete PDF: {exc}")

with tabs[6]:
    st.subheader("Austria-first job search")
    st.write("Use the official search pages below, then add relevant vacancies to this workspace for matching, drafting, and tracking.")
    st.warning("The AMS alle jobs service is for manual searches and prohibits automated extraction of its listed vacancies. This app does not scrape AMS, EURES, LinkedIn, or other sites that prohibit automated collection.")
    st.link_button("Open AMS alle jobs — all of Austria", "https://jobs.ams.at/public/emps/")
    st.link_button("Open AMS eJob-Room", "https://jobroom.ams.or.at/")
    st.link_button("Open Jobbörse der Republik Österreich", "https://bund.jobboerse.gv.at/sap/bc/jobs/")
    st.subheader("Suggested search terms")
    st.caption("On AMS, search manually by occupation and set the location field to Wien or Österreich. Use the full-time (Vollzeit) filter.")
    searches = [
        ("Systems & IT", '("IT-System" ODER "Systemadministrator" ODER "IT-Manager" ODER "System Engineer")'),
        ("Data & reporting", '("Data Analyst" ODER "Datenanalyst" ODER "Business Intelligence" ODER "Reporting")'),
        ("Data engineering", '("Data Engineer" ODER "Datenmanagement" ODER "SQL" ODER "Datenintegration")'),
        ("Business systems", '("Business Analyst" ODER "Prozessmanagement" ODER "Digitalisierung" ODER "ERP")'),
        ("Academic technology", '("Hochschul-IT" ODER "Forschungsdaten" ODER "Campus Management" ODER "Studienverwaltung")'),
    ]
    for label, query_text in searches:
        with st.expander(label):
            st.code(query_text, language=None)
            st.caption("Copy this phrase into the search website manually and refine the filters there.")
    st.subheader("What to do with promising results")
    st.markdown("1. Open the vacancy and verify that it is current, full-time, and in an acceptable location.\n2. Copy the official job URL and description.\n3. Add the job under **Add / import jobs**.\n4. Review the score and gaps under **Match jobs**.\n5. Prepare a draft and download an application review pack under **Drafts**.\n6. Review and submit the application on the employer's official page yourself.")


with tabs[7]:
    st.subheader("Continuous job monitoring")
    st.write("The monitor checks a public European job-board API immediately, then repeats every six hours while this Codespace stays running. New relevant Austria/Vienna and remote postings are saved to the local SQLite tracker and deduplicated by URL.")
    st.caption("Source: Arbeitnow's public job-board API. The provider updates listings hourly and asks API users not to abuse it; scans are deliberately limited to three pages every six hours.")
    st.warning("This is continuous job discovery, not universal automatic application submission. Do not use this monitor to scrape LinkedIn or AMS alle jobs. The AMS service requires manual search. Job boards and ATS platforms have separate rules.")
    running, pid = monitor_status()
    status_col, action_col = st.columns([2, 1])
    with status_col:
        if running:
            st.success(f"Monitor running (PID {pid}). It scans every six hours.")
        else:
            st.info("Monitor is stopped.")
    with action_col:
        if running:
            if st.button("Stop monitor", type="secondary", use_container_width=True):
                stopped = stop_monitor()
                st.success("Stop signal sent." if stopped else "Monitor was already stopped.")
                st.rerun()
        else:
            if st.button("Start continuous monitor", type="primary", use_container_width=True):
                new_pid = start_monitor()
                st.success(f"Monitor started (PID {new_pid}). The first scan should begin immediately.")
                st.rerun()
    if st.button("Run one scan now", disabled=running):
        try:
            with st.spinner("Checking permitted public job API pages..."):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "monitor.py"), "--once"],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=180,
                )
            st.code((result.stdout or "") + (result.stderr or ""), language="json")
            if result.returncode == 0:
                st.success("Scan finished. Newly discovered jobs have been added to the local tracker.")
            else:
                st.error("The scan reported an error; see output above.")
        except Exception as exc:
            st.error(f"Could not run the scan: {exc}")
    st.subheader("Latest monitor log")
    st.code(tail_monitor_log(), language="text")
    st.subheader("What happens automatically")
    st.markdown("- Checks a limited number of pages from the permitted public Arbeitnow API.\n- Filters out many unrelated roles and clearly part-time/internship postings.\n- Saves Austria-location matches and relevant remote listings; remote country eligibility remains unverified.\n- Deduplicates known job URLs and saves the scan summary to the local workspace.\n- Uses the saved résumé text and profile terms as keyword evidence when available.")
    st.subheader("Why it cannot automatically submit everywhere")
    st.markdown("Employer application endpoints are not a universal applicant API. Greenhouse's submission API requires an employer API key, and Lever's documented submission API key is generated by a Lever Super Admin. The app cannot legitimately invent those credentials. Job sites also ask individual questions about work authorisation, sponsorship, salary and declarations; these must not be guessed. This version will automatically discover and rank jobs and prepare drafts, but you submit through the employer's official page.")
    st.link_button("Read Arbeitnow public API documentation", "https://www.arbeitnow.com/blog/job-board-api")
