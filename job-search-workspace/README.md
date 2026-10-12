# Personal Job-Search Workspace

A local-first starter app for organising job leads, scoring role fit transparently, drafting materials from user-confirmed résumé facts, and tracking applications manually.

This project is inspired by the workflow goals of [GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn), but it is a separate, simpler workspace. It does not run the upstream bot or automate LinkedIn.

## Safety and privacy defaults

- No LinkedIn scraping or browser automation.
- No automatic applications, form filling, account login, or application submission.
- No external AI API calls. Letter drafts are built from local templates and facts in `profile.json`.
- Jobs and drafts are stored in `data/jobs.sqlite3` on the machine running the app.
- `profile.json` is excluded from Git because it contains personal details. If it is missing, the app creates it from `profile.example.json`. Review all facts before using drafts.
- If you require data to remain physically on your own computer, run locally instead of in a cloud-hosted Codespace.

## Run in GitHub Codespaces (Bash)

Open a Codespace on the `add-personal-job-search-workspace` branch, then run:

```bash
cd job-search-workspace
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Open the forwarded port 8501 when Codespaces offers it. Keep the terminal running. Stop with `Ctrl+C`.

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

1. Review your candidate profile in **Profile & data**. Add only facts you can substantiate.
2. Add a job manually, import a CSV, or import a permitted public RSS/Atom feed.
3. Use **Match jobs** to inspect the score, evidence, and gaps. Score weights: skills 45%, role fit 25%, location 20%, full-time status 10%.
4. Generate and edit a local cover-letter draft. Add employer-specific motivation and verify every sentence.
5. Open the employer's official listing, apply yourself, and manually update the tracker.
6. Export your tracker to CSV when useful.

## Privacy note

This repository is public. Do not commit `profile.json`, a résumé, the SQLite database, application notes, exports, or any credentials. The `.gitignore` in this folder excludes these local files. Codespaces are cloud-hosted; run on your own computer if the data must stay physically local.

## CSV format

The app provides a CSV template in **Add / import jobs**. Required columns: `title`, `company`. Optional columns include `location`, `job_url`, `description`, `requirements`, `employment_type`, `work_arrangement`, `source`, and `posted_date`.

## Public RSS/Atom feeds

Use only public feed URLs where automated access is permitted. Do not enter LinkedIn pages, login-protected pages, or websites that disallow automated retrieval. The feed importer validates HTTP(S) URLs and does not follow redirects automatically.

## Fit score transparency

Scores compare job text to candidate profile terms. A strong score is not a prediction of hiring success and does not confirm eligibility, seniority, salary, visa sponsorship, language requirements, or employer interest. Verify those details manually.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Files

- `app.py` — Streamlit dashboard
- `database.py` — local SQLite operations and duplicate prevention
- `matching.py` — transparent scoring
- `drafting.py` — local-only draft templates
- `sources.py` — permitted public RSS/Atom feed helpers
- `profile.json` — local candidate profile; intentionally not committed
- `data/jobs.sqlite3` — created automatically and ignored by Git
