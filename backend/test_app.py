
import pytest

from app import app, db, User
from werkzeug.security import generate_password_hash


@pytest.fixture()
def client():
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        user = User(
            name="Test User",
            email="test@example.com",
            password_hash=generate_password_hash("TestPassword123")
        )
        db.session.add(user)
        db.session.commit()

        test_client = app.test_client()

        yield test_client

        db.session.remove()
        db.drop_all()


def get_token(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )
    return response.get_json()["token"]


def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_invalid_login(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


def test_valid_login(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 200
    assert "token" in response.get_json()


def test_protected_endpoint_without_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_protected_endpoint_with_token(client):
    token = get_token(client)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "test@example.com"


def test_income_rejects_invalid_amount(client):
    token = get_token(client)

    response = client.post(
        "/api/income",
        json={"amount": -100},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400


def test_expense_rejects_invalid_amount(client):
    token = get_token(client)

    response = client.post(
        "/api/expenses",
        json={"amount": 0},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
