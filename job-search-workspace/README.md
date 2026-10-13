# Personal Job-Search Workspace

A local-first Streamlit app for organising job leads, explaining role-fit scores, extracting résumé text locally, creating editable application drafts, and tracking applications manually.

Inspired by the workflow goals of [GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn), this is a separate application. It does not run the upstream bot or automate LinkedIn.

## Safety and privacy defaults

- No LinkedIn scraping, browser automation, login automation, form filling, or automatic submission.
- No external AI calls. Drafts use local templates and terms extracted from the résumé PDF you choose to upload.
- Jobs and drafts are saved in `data/jobs.sqlite3`; the local candidate profile is saved in `profile.json`.
- Both `profile.json` and the database are excluded from Git. The public repository contains only a generic profile template.
- When running in Codespaces, the PDF you upload is processed in that cloud-hosted workspace. The app does not send it to an external AI API. For processing that remains on your own computer, run the app locally.
- The app can create an application review pack ZIP; it never submits it to an employer. You review the application and submit it through the employer's official process.

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

When Codespaces offers to open port 8501, open it in the browser. Keep the terminal running; stop the app with `Ctrl+C`. Keep the forwarded port private.

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

1. Open **Profile & data** and upload your résumé PDF. Choose **Extract résumé text and save to private profile** to save the extracted text in the ignored local `profile.json`.
2. Check the candidate profile and correct any skill terms. The résumé extraction is text-only; scanned/image-only PDFs are not OCR-processed.
3. Open **Austria search** to access the official AMS all-jobs portal, AMS eJob-Room, and the Austrian federal public-service job board. Copy suggested search phrases into those sites manually; use Vienna/Austria and full-time filters.
4. Add interesting jobs manually or import CSV / a permitted public RSS/Atom feed. Read a site's terms before using its feed.
5. Review **Match jobs** and inspect evidence and gaps. The weighted score uses skills (45%), role fit (25%), location (20%), and full-time status (10%). It is a prioritisation aid, not a prediction of hiring success.
6. Generate and edit cover-letter and screening-interest drafts. Download an application review pack ZIP, which includes a résumé PDF only when one is available in the current app session.
7. Open the employer's official listing, verify every fact and declaration, and submit the application yourself. Then update the tracker manually.

## Austria search limitations

The app provides links to official job-search sites but deliberately does not scrape them. The AMS states that its **alle jobs** service is for manual job searches and prohibits automated extraction of listed vacancies. The EURES portal also prohibits scraping and limits API extraction to approved partner organisations. Use these sources manually and add suitable listings to the tracker.

- [AMS alle jobs](https://jobs.ams.at/public/emps/)
- [AMS eJob-Room](https://jobroom.ams.or.at/)
- [Jobbörse der Republik Österreich](https://bund.jobboerse.gv.at/sap/bc/jobs/)

## CSV format

The built-in CSV template is available in **Add / import jobs**. Required columns are `title` and `company`. Optional columns include `location`, `job_url`, `description`, `requirements`, `employment_type`, `work_arrangement`, `source`, and `posted_date`.

## Public RSS/Atom feeds

Only use public feed URLs for which automated access is permitted. LinkedIn pages, login-protected URLs, local/private network hosts, and feeds that redirect are rejected. Supply the final feed URL directly.

## Fit score transparency

Scores compare terms in the job title/description/requirements with terms in the candidate profile, including a limited vocabulary of terms found in the saved résumé text. A high score does not verify work authorisation, salary, seniority, sponsorship, language requirements, or employer interest. Confirm those details manually.

## Files

- `app.py` — dashboard, SQLite tracking, score logic, PDF text extraction, official Austrian search links and review-pack export
- `profile.example.json` — generic Austria-first starting profile
- `profile.json` — local candidate profile and extracted résumé text, intentionally not committed
- `data/jobs.sqlite3` — created automatically and ignored by Git
