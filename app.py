
import os, csv, io, re
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, SelectField, DateField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import or_
from werkzeug.middleware.proxy_fix import ProxyFix
from urllib.parse import urlparse

app = Flask(__name__)
is_production = os.getenv("FLASK_ENV") == "production" or bool(os.getenv("RENDER"))
secret_key = os.getenv("SECRET_KEY")
if is_production and not secret_key:
    raise RuntimeError("Set a strong SECRET_KEY environment variable before deploying.")
app.config["SECRET_KEY"] = secret_key or "local-development-only-change-this-key"
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = is_production
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["WTF_CSRF_TIME_LIMIT"] = 3600

database_url = os.getenv("DATABASE_URL", "sqlite:///job_tracker.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://") and "+psycopg" not in database_url:
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 300}

# Render and other reverse-proxy deployments terminate HTTPS before Flask.
if is_production:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

db, csrf = SQLAlchemy(), CSRFProtect()
db.init_app(app)
csrf.init_app(app)

STATUSES = ["Wishlist", "Applied", "Online Assessment", "Interview", "Offer Received", "Rejected", "Withdrawn"]
TYPES = ["Full-time", "Part-time", "Internship", "Contract", "Other"]

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    applications = db.relationship("Application", backref="owner", cascade="all, delete-orphan", lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    company = db.Column(db.String(120), nullable=False)
    job_title = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), default="")
    job_url = db.Column(db.String(500), default="")
    salary = db.Column(db.String(80), default="")
    employment_type = db.Column(db.String(30), default="Full-time")
    status = db.Column(db.String(30), default="Applied", nullable=False)
    applied_date = db.Column(db.Date, default=date.today, nullable=False)
    interview_date = db.Column(db.DateTime)
    follow_up_date = db.Column(db.Date)
    notes = db.Column(db.Text, default="")
    interview_notes = db.Column(db.Text, default="")

class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=160)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create account")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")

class ApplicationForm(FlaskForm):
    company = StringField("Company name", validators=[DataRequired(), Length(max=120)])
    job_title = StringField("Job title", validators=[DataRequired(), Length(max=120)])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    job_url = StringField("Job link", validators=[Optional(), Length(max=500)])
    salary = StringField("Salary / range", validators=[Optional(), Length(max=80)])
    employment_type = SelectField("Employment type", choices=[(x,x) for x in TYPES])
    status = SelectField("Status", choices=[(x,x) for x in STATUSES])
    applied_date = DateField("Application date", validators=[DataRequired()], format="%Y-%m-%d")
    interview_date = StringField("Interview date & time", validators=[Optional()])
    follow_up_date = DateField("Follow-up date", validators=[Optional()], format="%Y-%m-%d")
    notes = TextAreaField("Application notes", validators=[Optional(), Length(max=5000)])
    interview_notes = TextAreaField("Interview notes", validators=[Optional(), Length(max=5000)])
    submit = SubmitField("Save application")

def user_now():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not user_now():
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def owned_or_404(app_id):
    item = Application.query.filter_by(id=app_id, user_id=user_now().id).first()
    if not item: abort(404)
    return item

def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        return None

def valid_job_url(value):
    value = (value or "").strip()
    if not value:
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and " " not in value

@app.context_processor
def globals_for_templates():
    return {"current_user": user_now, "statuses": STATUSES}

@app.errorhandler(413)
def too_large(_):
    flash("Upload is too large. Keep the request under 6 MB.", "error")
    return redirect(url_for("matcher"))

@app.route("/")
def index():
    if user_now():
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if user_now(): return redirect(url_for("dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            u = User(name=form.name.data.strip(), email=email, password_hash=generate_password_hash(form.password.data))
            db.session.add(u); db.session.commit(); session.clear(); session["user_id"] = u.id
            flash("Welcome! Your account is ready.", "success")
            return redirect(url_for("dashboard"))
    return render_template("auth.html", form=form, mode="register")

@app.route("/login", methods=["GET","POST"])
def login():
    if user_now(): return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if u and check_password_hash(u.password_hash, form.password.data):
            session.clear(); session["user_id"] = u.id
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("auth.html", form=form, mode="login")

@app.post("/logout")
@login_required
def logout():
    session.clear(); flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    items = Application.query.filter_by(user_id=user_now().id).all()
    counts = {s: sum(1 for x in items if x.status == s) for s in STATUSES}
    now = datetime.now()
    today = date.today()
    active_statuses = {"Applied", "Online Assessment", "Interview", "Offer Received", "Rejected"}
    active_items = [x for x in items if x.status in active_statuses]
    denominator = len(active_items)
    interview_or_offer = sum(1 for x in active_items if x.status in {"Interview", "Offer Received"})
    responded = sum(1 for x in active_items if x.status in {"Interview", "Offer Received", "Rejected"})
    interview_rate = round(interview_or_offer / denominator * 100, 1) if denominator else 0
    response_rate = round(responded / denominator * 100, 1) if denominator else 0
    offer_rate = round(counts["Offer Received"] / denominator * 100, 1) if denominator else 0
    upcoming = sorted([x for x in items if x.interview_date and now <= x.interview_date <= datetime.combine(today + timedelta(days=7), datetime.max.time())], key=lambda x:x.interview_date)[:5]
    followups = sorted([x for x in items if x.follow_up_date and x.follow_up_date >= today and x.status not in ["Offer Received","Rejected","Withdrawn"]], key=lambda x:x.follow_up_date)[:5]

    # Notifications are derived from saved dates; no email service or background worker is required.
    notifications = []
    for item in items:
        if item.interview_date and now <= item.interview_date <= now + timedelta(days=7):
            days_left = (item.interview_date.date() - today).days
            when = "today" if days_left == 0 else "tomorrow" if days_left == 1 else item.interview_date.strftime("%d %b")
            notifications.append({"kind":"interview", "priority":0 if days_left <= 1 else 1, "title":f"Interview {when}", "body":f"{item.company} · {item.job_title}", "date":item.interview_date.date(), "url":url_for("edit_application", app_id=item.id)})
        if item.follow_up_date and item.status not in {"Offer Received", "Rejected", "Withdrawn"}:
            if item.follow_up_date < today:
                notifications.append({"kind":"overdue", "priority":0, "title":"Follow-up overdue", "body":f"{item.company} · {item.job_title}", "date":item.follow_up_date, "url":url_for("edit_application", app_id=item.id)})
            elif item.follow_up_date <= today + timedelta(days=3):
                notifications.append({"kind":"followup", "priority":1, "title":"Follow-up coming up", "body":f"{item.company} · {item.job_title}", "date":item.follow_up_date, "url":url_for("edit_application", app_id=item.id)})
    notifications.sort(key=lambda n: (n["priority"], n["date"]))
    notifications = notifications[:8]

    labels, values = [], []
    for offset in range(5,-1,-1):
        idx = today.year * 12 + today.month - 1 - offset
        y, m = idx // 12, idx % 12 + 1
        labels.append(date(y,m,1).strftime("%b %Y"))
        values.append(sum(1 for x in items if x.applied_date.year == y and x.applied_date.month == m))
    return render_template("dashboard.html", items=items, counts=counts, total=len(items), upcoming=upcoming, followups=followups, offer_rate=offer_rate, interview_rate=interview_rate, response_rate=response_rate, active_total=denominator, notifications=notifications, labels=labels, values=values)

@app.route("/applications")
@login_required
def applications():
    q = Application.query.filter_by(user_id=user_now().id)
    search, status, sort = request.args.get("q","").strip(), request.args.get("status",""), request.args.get("sort","newest")
    if search:
        pat = f"%{search}%"
        q = q.filter(or_(Application.company.ilike(pat), Application.job_title.ilike(pat), Application.location.ilike(pat)))
    if status in STATUSES: q = q.filter_by(status=status)
    q = q.order_by(Application.applied_date.asc() if sort == "oldest" else Application.company.asc() if sort == "company" else Application.applied_date.desc())
    return render_template("applications.html", items=q.all(), search=search, selected_status=status, sort=sort)

def fill_item(item, form):
    item.company = form.company.data.strip(); item.job_title = form.job_title.data.strip()
    item.location = (form.location.data or "").strip(); item.job_url = (form.job_url.data or "").strip()
    item.salary = (form.salary.data or "").strip(); item.employment_type = form.employment_type.data
    item.status = form.status.data; item.applied_date = form.applied_date.data
    item.interview_date = parse_dt(form.interview_date.data); item.follow_up_date = form.follow_up_date.data
    item.notes = form.notes.data or ""; item.interview_notes = form.interview_notes.data or ""

@app.route("/applications/new", methods=["GET","POST"])
@login_required
def new_application():
    form = ApplicationForm()
    if request.method == "GET":
        form.applied_date.data = date.today(); form.status.data = "Applied"; form.employment_type.data = "Full-time"
    if form.validate_on_submit():
        if not valid_job_url(form.job_url.data):
            flash("Job link must start with https:// or http://.", "error")
            return render_template("application_form.html", form=form, mode="new")
        if form.interview_date.data and not parse_dt(form.interview_date.data):
            flash("Please enter a valid interview date and time.", "error")
            return render_template("application_form.html", form=form, mode="new")
        item = Application(user_id=user_now().id)
        fill_item(item, form)
        db.session.add(item)
        db.session.commit()
        flash("Application added.", "success")
        return redirect(url_for("applications"))
    return render_template("application_form.html", form=form, mode="new")

@app.route("/applications/<int:app_id>/edit", methods=["GET","POST"])
@login_required
def edit_application(app_id):
    item = owned_or_404(app_id); form = ApplicationForm(obj=item)
    if request.method == "GET": form.interview_date.data = item.interview_date.strftime("%Y-%m-%dT%H:%M") if item.interview_date else ""
    if form.validate_on_submit():
        if not valid_job_url(form.job_url.data):
            flash("Job link must start with https:// or http://.", "error")
            return render_template("application_form.html", form=form, mode="edit")
        if form.interview_date.data and not parse_dt(form.interview_date.data):
            flash("Please enter a valid interview date and time.", "error")
            return render_template("application_form.html", form=form, mode="edit")
        fill_item(item, form)
        db.session.commit()
        flash("Application updated.", "success")
        return redirect(url_for("applications"))
    return render_template("application_form.html", form=form, mode="edit")

@app.post("/applications/<int:app_id>/delete")
@login_required
def delete_application(app_id):
    item = owned_or_404(app_id); db.session.delete(item); db.session.commit()
    flash("Application deleted.", "success"); return redirect(url_for("applications"))

@app.route("/export.csv")
@login_required
def export_csv():
    items = Application.query.filter_by(user_id=user_now().id).order_by(Application.applied_date.desc()).all()
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(["Company","Job Title","Location","Job Link","Salary","Employment Type","Status","Application Date","Interview Date","Follow-up Date","Notes","Interview Notes"])
    for x in items:
        w.writerow([x.company,x.job_title,x.location,x.job_url,x.salary,x.employment_type,x.status,x.applied_date.isoformat() if x.applied_date else "",x.interview_date.isoformat(sep=" ") if x.interview_date else "",x.follow_up_date.isoformat() if x.follow_up_date else "",x.notes,x.interview_notes])
    return Response("\ufeff"+out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=job_applications.csv"})

SKILLS = ["python","java","c++","javascript","typescript","html","css","react","flask","django","fastapi","sql","mysql","postgresql","sqlite","mongodb","git","github","docker","aws","machine learning","deep learning","scikit-learn","pandas","numpy","data analysis","power bi","excel","rest api","data structures","algorithms","oop","dbms","operating systems","computer networks","tensorflow","pytorch","xgboost","nlp","linux","testing"]
def extract_skills(text):
    low = re.sub(r"\s+", " ", text.lower())
    return sorted(s for s in SKILLS if re.search(r"(?<![a-z0-9+#.])"+re.escape(s)+r"(?![a-z0-9+#.])", low))

@app.route("/matcher", methods=["GET","POST"])
@login_required
def matcher():
    result = None; resume_text = ""; job_description = ""
    if request.method == "POST":
        resume_text = (request.form.get("resume_text") or "").strip()
        job_description = (request.form.get("job_description") or "").strip()
        f = request.files.get("resume_file")
        if f and f.filename:
            if not f.filename.lower().endswith(".pdf"):
                flash("Upload a PDF resume or paste resume text.", "error")
            else:
                try: resume_text = "\n".join(p.extract_text() or "" for p in PdfReader(f.stream).pages[:15]).strip()
                except Exception: flash("Could not read that PDF. Paste the resume text instead.", "error"); resume_text = ""
        if not job_description: flash("Paste a job description.", "error")
        elif not resume_text: flash("Upload a text-based PDF or paste your resume text.", "error")
        elif len(job_description) > 30000 or len(resume_text) > 30000: flash("Each text input must be under 30,000 characters.", "error")
        else:
            try:
                matrix = TfidfVectorizer(stop_words="english", ngram_range=(1,2)).fit_transform([resume_text,job_description])
                score = round(float(cosine_similarity(matrix[0:1],matrix[1:2])[0][0])*100,1)
            except ValueError: score = 0.0
            rs, js = extract_skills(resume_text), extract_skills(job_description)
            result = {"score":score,"matching":sorted(set(rs)&set(js)),"missing":sorted(set(js)-set(rs))}
    return render_template("matcher.html", result=result, resume_text=resume_text, job_description=job_description)

@app.get("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return {"status": "ok", "database": "connected"}, 200
    except Exception:
        app.logger.exception("Health check failed")
        return {"status": "degraded", "database": "unavailable"}, 503

@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/") or request.path == "/health":
        return {"error": "Not found"}, 404
    return render_template("error.html", code=404, title="Page not found",
                           message="That page doesn't exist, or it may have moved."), 404

@app.errorhandler(500)
def internal_error(_error):
    db.session.rollback()
    app.logger.exception("Unhandled application error")
    return render_template("error.html", code=500, title="Something went wrong",
                           message="Please try again. If the issue continues, check the deployment logs."), 500

# Creates missing tables on first run; this is not a schema migration tool.
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "").lower() == "true"
    )