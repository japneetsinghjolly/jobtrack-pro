"""Import the synthetic sample dataset into an existing user's account.

Usage from the project root:
    python scripts/import_sample_data.py --email you@example.com

All rows are synthetic examples. Review/remove them after trying the app.
"""
import argparse
import csv
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import app, db, User, Application  # noqa: E402

DATA_FILE = ROOT / "data" / "sample_applications.csv"


def parse_date(value):
    return date.fromisoformat(value) if value else None


def parse_datetime(value):
    return datetime.fromisoformat(value) if value else None


def main():
    parser = argparse.ArgumentParser(description="Import sample applications for an existing JobTrack Pro account.")
    parser.add_argument("--email", required=True, help="Email address of the account that should receive the sample rows")
    parser.add_argument("--clear-existing", action="store_true", help="Delete that user's existing applications before importing (use carefully)")
    args = parser.parse_args()

    with app.app_context():
        user = User.query.filter_by(email=args.email.strip().lower()).first()
        if not user:
            parser.error("No account found for that email. Register in the app first.")
        if args.clear_existing:
            Application.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        imported = 0
        with DATA_FILE.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                item = Application(
                    user_id=user.id,
                    company=row["company"], job_title=row["job_title"],
                    location=row.get("location", ""), job_url=row.get("job_url", ""),
                    salary=row.get("salary", ""), employment_type=row.get("employment_type", "Full-time"),
                    status=row.get("status", "Applied"), applied_date=parse_date(row.get("applied_date", "")) or date.today(),
                    interview_date=parse_datetime(row.get("interview_date", "")),
                    follow_up_date=parse_date(row.get("follow_up_date", "")),
                    notes=row.get("notes", ""), interview_notes=row.get("interview_notes", ""),
                )
                db.session.add(item)
                imported += 1
        db.session.commit()
        print(f"Imported {imported} synthetic sample applications for {user.email}.")
        print("Open the dashboard and replace/delete the demo rows when ready.")


if __name__ == "__main__":
    main()
