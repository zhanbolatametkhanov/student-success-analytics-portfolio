# Personal Job-Search Workspace

A local-first Streamlit app for organising job leads, explaining role-fit scores, creating editable application drafts, and tracking applications manually.

Inspired by the workflow goals of [GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn), this is a separate application. It does not run the upstream bot or automate LinkedIn.

## Safety and privacy defaults

- No LinkedIn scraping, browser automation, login automation, form filling, or automatic submission.
- No external AI calls. Drafts use simple local templates and facts stored in your local candidate profile.
- Job records and drafts are saved in `data/jobs.sqlite3`.
- `profile.json` is excluded from Git because it contains personal information. The app creates a generic profile from `profile.example.json` the first time it runs; review and personalize it before using drafts.
- This repository is public. Never commit your résumé, `profile.json`, the SQLite database, drafts, exports, credentials, or application notes.
- Codespaces are cloud-hosted. Run locally if your candidate data must remain physically on your own computer.

## Run in GitHub Codespaces (Bash)

Open a Codespace on the `add-personal-job-search-workspace` branch, then run these commands one at a time:

```bash
cd job-search-workspace
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 0.0.0.0
```

When Codespaces offers to open port 8501, open it in the browser. Keep the terminal running; stop the app with `Ctrl+C`. Leave the forwarded port private.

## Run on your own computer (Linux/macOS)

```bash
cd job-search-workspace
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

### Windows PowerShell

```powershell
cd job-search-workspace
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

## First-use workflow

1. Open **Profile & data** and review the candidate profile. Only include facts you can substantiate.
2. Add a job manually, import a CSV, or import a permitted public RSS/Atom job feed.
3. Review **Match jobs** and inspect the evidence and gaps. The weighted score uses skills (45%), role fit (25%), location (20%), and full-time status (10%). It is a prioritisation aid, not a prediction of hiring success.
4. Generate and edit application drafts. Add employer-specific motivation and verify every statement.
5. Open the employer's official listing and submit the application yourself. Then update the tracker manually.
6. Export the tracker to CSV when useful.

## CSV format

The built-in CSV template is available in **Add / import jobs**. Required columns are `title` and `company`. Optional columns include `location`, `job_url`, `description`, `requirements`, `employment_type`, `work_arrangement`, `source`, and `posted_date`.

## Public RSS/Atom feeds

Only use public feed URLs for which automated access is permitted. LinkedIn pages, login-protected URLs, local/private network hosts, and feeds that redirect are rejected. Supply the final feed URL directly.

## Fit score transparency

Scores compare terms in the job title/description/requirements with terms in the candidate profile. A high score does not verify work authorisation, salary, seniority, sponsorship, language requirements, or employer interest. Confirm those details manually.

## Files

- `app.py` — Streamlit dashboard, SQLite storage, scoring, local drafts and imports
- `profile.example.json` — generic starting profile
- `profile.json` — local candidate profile, intentionally not committed
- `data/jobs.sqlite3` — created automatically and ignored by Git
