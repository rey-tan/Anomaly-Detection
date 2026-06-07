import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.api.app import app
from src.api import models, database


@pytest.fixture(scope="function")
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[database.get_db] = override_get_db
    yield SessionLocal()
    app.dependency_overrides.clear()


def test_register_request_sends_otp_and_verifies_email(test_db):
    client = TestClient(app)

    response = client.post(
        "/test/register/request",
        json={
            "username": "newanalyst",
            "email": "newanalyst@example.com",
            "password": "securepassword123",
            "role": "analyst",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newanalyst@example.com"
    assert data["message"].startswith("OTP sent to email")

    db = test_db
    user = db.query(models.User).filter(models.User.email == "newanalyst@example.com").first()
    assert user is not None
    assert user.email_verified is False
    assert user.otp_code == "123456"

    verify_response = client.post(
        "/test/register/verify",
        json={
            "email": "newanalyst@example.com",
            "otp_code": user.otp_code,
        },
    )

    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["username"] == "newanalyst"
    assert verify_data["email"] == "newanalyst@example.com"
    assert verify_data["email_verified"] is True

    db.expire_all()
    user = db.query(models.User).filter(models.User.email == "newanalyst@example.com").first()
    assert user.email_verified is True
    assert user.otp_code is None
    assert user.otp_expires_at is None


def test_register_request_duplicate_username_or_email_fails(test_db):
    client = TestClient(app)

    response = client.post(
        "/test/register/request",
        json={
            "username": "duplicate",
            "email": "duplicate@example.com",
            "password": "pass123",
        },
    )
    assert response.status_code == 200

    response2 = client.post(
        "/test/register/request",
        json={
            "username": "duplicate",
            "email": "another@example.com",
            "password": "pass456",
        },
    )
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"]

    response3 = client.post(
        "/test/register/request",
        json={
            "username": "anotheruser",
            "email": "duplicate@example.com",
            "password": "pass456",
        },
    )
    assert response3.status_code == 409
    assert "already registered" in response3.json()["detail"]




def test_login_with_username_or_email_after_verification(test_db):
    client = TestClient(app)

    response = client.post(
        "/test/register/request",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == 200

    db = test_db
    user = db.query(models.User).filter(models.User.email == "testuser@example.com").first()
    assert user is not None

    verify_response = client.post(
        "/test/register/verify",
        json={
            "email": "testuser@example.com",
            "otp_code": user.otp_code,
        },
    )
    assert verify_response.status_code == 200

    db.expire_all()
    user = db.query(models.User).filter(models.User.email == "testuser@example.com").first()
    assert user.email_verified is True

    login_username_response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "testpass123",
        },
    )
    assert login_username_response.status_code == 200
    assert "access_token" in login_username_response.json()

    login_email_response = client.post(
        "/login",
        data={
            "username": "testuser@example.com",
            "password": "testpass123",
        },
    )
    assert login_email_response.status_code == 200
    assert "access_token" in login_email_response.json()


def test_register_with_invalid_otp_fails(test_db):
    """Test that providing an invalid OTP fails verification."""
    client = TestClient(app)

    response = client.post(
        "/test/register/request",
        json={
            "username": "invalidotpuser",
            "email": "invalidotp@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200

    verify_response = client.post(
        "/test/register/verify",
        json={
            "email": "invalidotp@example.com",
            "otp_code": "999999",
        },
    )
    assert verify_response.status_code == 400
    assert "Invalid or expired OTP" in verify_response.json()["detail"]


def test_login_with_invalid_credentials_fails(test_db):
    """Test that login with wrong password fails."""
    client = TestClient(app)

    # First register a user
    register_response = client.post(
        "/test/register/request",
        json={
            "username": "validuser",
            "email": "validuser@example.com",
            "password": "correctpassword",
        },
    )
    assert register_response.status_code == 200

    db = test_db
    user = db.query(models.User).filter(models.User.email == "validuser@example.com").first()

    verify_response = client.post(
        "/test/register/verify",
        json={
            "email": "validuser@example.com",
            "otp_code": user.otp_code,
        },
    )
    assert verify_response.status_code == 200

    # Try login with wrong password
    login_response = client.post(
        "/login",
        data={
            "username": "validuser",
            "password": "wrongpassword",
        },
    )
    assert login_response.status_code == 401
    assert "Incorrect username or password" in login_response.json()["detail"]


def test_login_nonexistent_user_fails(test_db):
    """Test that login with nonexistent username fails."""
    client = TestClient(app)

    login_response = client.post(
        "/login",
        data={
            "username": "nonexistent",
            "password": "anypassword",
        },
    )
    assert login_response.status_code == 401
    assert "Incorrect username or password" in login_response.json()["detail"]
