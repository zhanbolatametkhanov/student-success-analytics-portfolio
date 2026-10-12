from __future__ import annotations
import csv
import hashlib
import ipaddress
import io
import json
import socket
import sqlite3
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "profile.json"
DB_PATH = ROOT / "data" / "jobs.sqlite3"
STATUSES = ["Inbox", "Shortlisted", "Draft Ready", "Ready for Review", "Applied", "Interview", "Offer", "Rejected", "Withdrawn", "Closed"]


def load_profile():
    if not PROFILE_PATH.exists():
        PROFILE_PATH.write_text((ROOT / "profile.example.json").read_text(encoding="utf-8"), encoding="utf-8")
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


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


def profile_terms(profile):
    terms = []
    for group in (profile.get("skills") or {}).values():
        terms.extend(group if isinstance(group, list) else [])
    terms.extend(profile.get("target_roles", []))
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
        result.append({"title": str(entry.get("title") or "Untitled listing"), "company": str(entry.get("author") or entry.get("source", {}).get("title") or "Unspecified employer"), "location": "", "job_url": link, "description": str(entry.get("summary") or ""), "requirements": "", "employment_type": "Unknown", "work_arrangement": "Unclear", "source": host, "posted_date": str(entry.get("published") or "")})
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

tabs = st.tabs(["Overview", "Add / import jobs", "Match jobs", "Drafts", "Application tracker", "Profile & data"])
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
