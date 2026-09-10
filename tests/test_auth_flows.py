import os
import sys
from pathlib import Path
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.database.models import User

client = TestClient(app)

def test_admin_login():
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"
    print("✅ Admin Login Test Passed (role=admin, token issued)")


def test_analyst_login():
    response = client.post("/auth/login", json={"username": "analyst", "password": "user123"})
    assert response.status_code == 200, f"Analyst login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "analyst"
    print("✅ Analyst Login Test Passed (role=analyst, token issued)")


def test_invalid_login():
    response = client.post("/auth/login", json={"username": "admin", "password": "wrongpassword123"})
    assert response.status_code == 401, f"Expected 401 for bad password, got {response.status_code}"
    print("✅ Invalid Login Handled (HTTP 401 Unauthorized)")


def test_user_registration():
    import uuid
    rand_suffix = str(uuid.uuid4())[:6]
    test_username = f"analyst_test_{rand_suffix}"
    test_email = f"test_{rand_suffix}@customerai.local"

    payload = {
        "full_name": "Test Analyst User",
        "username": test_username,
        "email": test_email,
        "password": "securepassword123",
        "role": "analyst"
    }

    response = client.post("/auth/register", json=payload)
    assert response.status_code == 200, f"Registration failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == test_username
    assert data["user"]["role"] == "analyst"
    print(f"✅ User Registration Test Passed (user={test_username})")

    # Clean up test user
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.username == test_username).first()
        if u:
            db.delete(u)
            db.commit()
    finally:
        db.close()


def test_html_elements_and_roles():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text

    # Verify role selection portal elements
    assert "authRoleSelectView" in html, "Missing authRoleSelectView"
    assert "authAdminLoginView" in html, "Missing authAdminLoginView"
    assert "authAnalystLoginView" in html, "Missing authAnalystLoginView"
    assert "authRegisterView" in html, "Missing authRegisterView"

    # Verify role selection cards
    assert "role-choice-admin" in html
    assert "role-choice-analyst" in html
    assert "role-choice-register" in html

    # Verify form elements
    assert "adminUsername" in html
    assert "adminPassword" in html
    assert "adminPassToggle" in html

    assert "analystUsername" in html
    assert "analystPassword" in html
    assert "analystPassToggle" in html

    assert "regFullName" in html
    assert "regUsername" in html
    assert "regEmail" in html
    assert "regPassword" in html
    assert "regConfirmPassword" in html
    assert "regPassToggle" in html
    assert "regConfirmPassToggle" in html

    print("✅ Served HTML structure and all role elements verified!")


if __name__ == "__main__":
    test_admin_login()
    test_analyst_login()
    test_invalid_login()
    test_user_registration()
    test_html_elements_and_roles()
    print("\n🎉 ALL AUTHENTICATION AND LOGIN TESTS PASSED SUCCESSFULLY!")
