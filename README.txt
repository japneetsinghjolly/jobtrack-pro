JOBTRACK PRO — PREMIUM FULL PROJECT

Included:
- app.py: Flask application, authentication, per-user application records, CRUD, search/filter/sort, CSV export, resume PDF/text matcher, dashboard metrics and reminders, CSRF protection, health check, production cookie settings and error pages.
- templates/: landing, login/register, dashboard, applications, add/edit form, resume matcher, shared layout, error page.
- static/css/style.css: responsive premium styling.
- static/js/main.js: responsive menu, dismissible messages, password visibility, delete confirmation and file selection label.
- requirements.txt, Procfile, runtime.txt, .gitignore.

LOCAL RUN
1. Install Python 3.12.
2. In this folder, run:
   python -m venv .venv
   Windows: .venv\Scripts\activate
   macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   set SECRET_KEY=replace-with-a-long-random-secret  (Windows CMD)
   export SECRET_KEY='replace-with-a-long-random-secret' (macOS/Linux)
   python app.py
3. Open http://127.0.0.1:5000

RENDER DEPLOYMENT
- Build command: pip install -r requirements.txt
- Start command: gunicorn app:app
- Set SECRET_KEY to a long random value in Render Environment.
- Set DATABASE_URL to your Render PostgreSQL Internal Database URL. Keep the same existing DATABASE_URL if your existing data must remain available.
- Redeploy and test /health. It should return status ok and database connected.
- If using an existing database, back it up first. db.create_all() creates missing tables but does not alter existing table schemas. If the existing database was made by a different app.py schema, a proper migration may be needed.
- Use PostgreSQL for persistent live data. A local SQLite database on an ephemeral hosting filesystem can be lost during rebuilds/restarts.
- Do not commit .env files or database files.
- Set FLASK_DEBUG=false in production (or leave it unset).

FEATURES
- Registration/login with password hashing and CSRF protection.
- Per-user application isolation.
- Create, edit and delete job applications.
- Status pipeline, search, status filter, sort and CSV export.
- Interview and follow-up reminders on the dashboard.
- Resume PDF/text vs job description similarity and skill comparison.
- Health endpoint at /health.

IMPORTANT LIMITATIONS
- The resume match percentage is a text similarity signal, not an AI hiring prediction.
- Reminders appear in the dashboard; email/SMS reminders are not sent without configuring a notification provider.
- Email verification, password reset emails, OAuth, billing and external AI APIs are not configured in this standalone package.
- No software package can be guaranteed to work on every host without checking that host's Python version, environment variables, database schema and deployment settings.
