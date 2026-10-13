"""Add sample job applications to an existing local JobTrack Pro account.

Usage:
  1. Register an account in the app.
  2. Set SAMPLE_USER_EMAIL to that account's email (or edit the value below).
  3. Run: python import_sample_data.py

This script does not create a user or reset existing data. It skips inserting
sample records if that account already has applications.
"""
import os
from datetime import date, datetime, timedelta
from app import app, db, User, Application

SAMPLE_EMAIL = os.getenv("SAMPLE_USER_EMAIL", "you@example.com").strip().lower()

SAMPLES = [
    {"company": "Acme Technologies", "job_title": "Software Developer Intern", "location": "Gurugram, India", "employment_type": "Internship", "status": "Applied", "days_ago": 2, "notes": "Sample record — replace with a real application."},
    {"company": "Northstar AI", "job_title": "Junior Machine Learning Engineer", "location": "Remote", "employment_type": "Full-time", "status": "Online Assessment", "days_ago": 5, "notes": "Sample record — practice assessment pending."},
    {"company": "Brightbyte Solutions", "job_title": "Python Developer", "location": "Noida, India", "employment_type": "Full-time", "status": "Interview", "days_ago": 8, "notes": "Sample record — prepare project explanations."},
    {"company": "PixelForge Labs", "job_title": "Backend Developer Intern", "location": "Delhi, India", "employment_type": "Internship", "status": "Wishlist", "days_ago": 0, "notes": "Sample record — research before applying."},
]

with app.app_context():
    db.create_all()
    user = User.query.filter_by(email=SAMPLE_EMAIL).first()
    if not user:
        raise SystemExit(f"No account found for {SAMPLE_EMAIL!r}. Register in the app first, then set SAMPLE_USER_EMAIL.")
    if Application.query.filter_by(user_id=user.id).first():
        raise SystemExit("This account already has applications. No sample data was added to avoid duplicates.")
    today = date.today()
    for sample in SAMPLES:
        item = Application(
            user_id=user.id,
            company=sample["company"],
            job_title=sample["job_title"],
            location=sample["location"],
            employment_type=sample["employment_type"],
            status=sample["status"],
            applied_date=today - timedelta(days=sample["days_ago"]),
            notes=sample["notes"],
        )
        if sample["status"] == "Interview":
            item.interview_date = datetime.now() + timedelta(days=3)
        db.session.add(item)
    db.session.commit()
    print(f"Added {len(SAMPLES)} sample applications for {user.email}.")
