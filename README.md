# JobTrack Pro — Job Application Tracker

A portfolio-ready job application tracker built with **Python, Flask, SQLite, SQLAlchemy, HTML, CSS, and JavaScript**. It includes account authentication, job tracking, reminders, dashboard analytics, dark mode, CSV export, and a resume-to-job-description text matcher.

## Features

- **Authentication:** register/login, hashed passwords, sessions, CSRF protection, and per-user application isolation.
- **Job application CRUD:** create, view, edit, and delete opportunities; track company, role, location, link, salary, type, status, application date, notes, interview date, and follow-up date.
- **Search, filter, and sort:** search by company, role, or location; filter by status; sort by date or company.
- **Dashboard:** status counts and a six-month application activity chart.
- **In-app notifications:** upcoming interviews within 7 days, follow-ups due in 3 days, and overdue follow-ups. These are displayed in the dashboard; no email service or background worker is required.
- **Success analytics:** interview rate, response rate, and offer rate based on current application statuses. These are descriptive status-based metrics, not predictions of hiring outcomes.
- **Dark mode:** toggle in the top navigation; preference is stored in the browser.
- **CSV export:** download the user's applications.
- **Resume matcher:** compare resume text with a job description using TF-IDF and cosine similarity; extract text from text-based PDFs and show matching/missing skills.
- **Health check:** `/health` for deployment checks.
- **Sample dataset:** synthetic example applications in `data/sample_applications.csv`, plus a script to import them into an existing account.

## Project structure

```text
job_application_tracker_pro/
├── app.py
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example
├── .gitignore
├── README.md
├── data/
│   └── sample_applications.csv
├── scripts/
│   └── import_sample_data.py
├── tests/
│   └── test_app.py
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── application_form.html
    ├── applications.html
    ├── auth.html
    ├── base.html
    ├── dashboard.html
    ├── landing.html
    └── matcher.html
```

## Run locally on Windows

Install Python 3.10 or newer. Open a terminal in the project folder and run:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env` if you use a local environment-variable loader, then set a unique `SECRET_KEY`. The app reads environment variables directly; `.env` is not automatically loaded by Flask. For a quick local run, the app has a development fallback key, but **set `SECRET_KEY` before deploying**.

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
python app.py
```

Open `http://127.0.0.1:5000`. SQLite is used by default and the database is created automatically. The default database file is kept in Flask's instance directory and is excluded from Git.

### Import the synthetic sample data (optional)

1. Start the app and register your own account.
2. Stop the app or open a second terminal in the project folder with the same environment/database configuration.
3. Run this command using the email you registered with:

```powershell
python scripts/import_sample_data.py --email you@example.com
```

This adds sample rows to that user's account. They are **synthetic demo records**, not real vacancies or actual applications. To delete the sample rows, remove them through the UI. The optional `--clear-existing` flag deletes all existing applications for that account before importing; use it carefully.

### Run tests

```powershell
python -m unittest discover -s tests -v
```

## Push to GitHub

Create an empty repository on GitHub, then run these commands in the project folder (replace the URL):

```bash
git init
git add .
git commit -m "Add JobTrack Pro with notifications analytics and dark mode"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

If `origin` already exists, use `git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git` instead of adding it again. Do not commit `.env`, passwords, database files, or real application data.

## Deploy on Render with SQLite (no PostgreSQL setup)

1. Push the project to GitHub.
2. In Render, choose **New + → Web Service**, connect your repository, and select the project.
3. Use the settings below (the included `render.yaml` provides the build/start commands):
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Set `SECRET_KEY` to a long, random value in Render's Environment settings. Do not use the development fallback key.
5. Deploy and visit `/health`; it should return `{"status":"ok"}`.

The app automatically uses SQLite when `DATABASE_URL` is not set. **Important:** a standard Render web service has an ephemeral filesystem. The site can run with SQLite without PostgreSQL, but the database may be lost when the service is replaced, restarted, or redeployed. If you need persistent SQLite data on Render, attach a persistent disk (where available) mounted at `/var/data` and set `DATABASE_URL` to `sqlite:////var/data/job_tracker.db`. Persistent disks may require a paid Render plan. Do not store real user data on an ephemeral disk.

## Notes and limitations

- The resume match percentage is **text similarity**, not a hiring probability or a guarantee of suitability.
- PDF text extraction works best with text-based PDFs. Scanned image-only resumes may need OCR or pasted text.
- Notifications appear when the user opens the dashboard; this version does not send push/email alerts or run a background scheduler.
- Analytics are based on the current status saved for each application, not a full historical status-change log.
- Chart.js and Google Fonts are loaded from CDNs, so those parts need internet access in the browser. The core forms and database are local.
- Review and test the project in your environment before presenting it as production-ready. Use a strong secret, HTTPS, backups, and a persistent database/storage option for a real public service.
