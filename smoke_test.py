"""Basic route smoke-test. Run with: python smoke_test.py"""
import os
os.environ.setdefault("SECRET_KEY", "smoke-test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite://")
import app as project

def main():
    project.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SQLALCHEMY_DATABASE_URI="sqlite://")
    with project.app.app_context():
        project.db.drop_all()
        project.db.create_all()
    client = project.app.test_client()
    response = client.get("/")
    assert response.status_code == 200, f"Landing route: {response.status_code}"
    response = client.get("/health")
    assert response.status_code == 200, f"Health route: {response.status_code}"
    response = client.get("/login")
    assert response.status_code == 200, f"Login route: {response.status_code}"
    response = client.get("/register")
    assert response.status_code == 200, f"Register route: {response.status_code}"
    print("Smoke test passed: /, /health, /login, /register")

if __name__ == "__main__":
    main()
