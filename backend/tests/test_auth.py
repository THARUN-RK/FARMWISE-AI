from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_login_accepts_formatted_phone_and_email():
    suffix = uuid4().hex[:10]
    phone = f"+9198{uuid4().int % 10**8:08d}"
    password = "StrongPass123"
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Auth Test Farmer",
            "phone": f"+91 ({phone[3:5]}) {phone[5:9]}-{phone[9:]}",
            "email": f"  Auth-{suffix}@Example.com  ",
            "password": password,
            "confirm_password": password,
        },
    )
    assert registered.status_code == 201

    phone_login = client.post(
        "/api/v1/auth/login",
        json={"identifier": f" {phone[:3]} {phone[3:7]} {phone[7:]} ", "password": password},
    )
    assert phone_login.status_code == 200
    assert phone_login.json()["data"]["user"]["phone"] == phone

    email_login = client.post(
        "/api/v1/auth/login",
        json={"identifier": f"AUTH-{suffix}@EXAMPLE.COM", "password": password},
    )
    assert email_login.status_code == 200
    assert email_login.json()["data"]["user"]["id"] == registered.json()["data"]["user"]["id"]


def test_login_rejects_invalid_password():
    phone = f"+9199{uuid4().int % 10**8:08d}"
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Auth Test Farmer",
            "phone": phone,
            "email": "",
            "password": "StrongPass123",
        },
    )
    assert registered.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": "WrongPass123"},
    )
    assert response.status_code == 401


def test_registration_allows_multiple_accounts_without_email():
    for _ in range(2):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Auth Test Farmer",
                "phone": f"+9197{uuid4().int % 10**8:08d}",
                "email": " ",
                "password": "StrongPass123",
            },
        )
        assert response.status_code == 201


def test_google_login_requires_phone_then_creates_and_reuses_account(monkeypatch):
    email = f"google-{uuid4().hex[:10]}@example.com"
    monkeypatch.setattr(
        auth_routes,
        "verify_google_credential",
        lambda credential: {
            "sub": "google-subject",
            "email": email,
            "email_verified": True,
            "iss": "https://accounts.google.com",
            "name": "Google Farmer",
        },
    )

    first_attempt = client.post(
        "/api/v1/auth/google",
        json={"credential": "a" * 40},
    )
    assert first_attempt.status_code == 200
    assert first_attempt.json()["data"]["phone_required"] is True

    phone = f"+9195{uuid4().int % 10**8:08d}"
    created = client.post(
        "/api/v1/auth/google",
        json={"credential": "a" * 40, "phone": phone},
    )
    assert created.status_code == 200
    assert created.json()["data"]["user"]["email"] == email
    assert created.json()["data"]["user"]["phone"] == phone

    signed_in = client.post(
        "/api/v1/auth/google",
        json={"credential": "a" * 40},
    )
    assert signed_in.status_code == 200
    assert signed_in.json()["data"]["user"]["id"] == created.json()["data"]["user"]["id"]


def test_google_login_reports_missing_oauth_configuration(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "")
    response = client.post(
        "/api/v1/auth/google",
        json={"credential": "a" * 40},
    )
    assert response.status_code == 503


def test_profile_saves_opt_in_location_coordinates():
    phone = f"+9194{uuid4().int % 10**8:08d}"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Location Test Farmer",
            "phone": phone,
            "password": "StrongPass123",
        },
    )
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['data']['access_token']}"}
    response = client.put(
        "/api/v1/farmers/profile",
        headers=headers,
        json={
            "name": "Location Test Farmer",
            "language": "en",
            "state": "Karnataka",
            "district": "Mysuru",
            "location_name": "Mysuru, Karnataka",
            "latitude": 12.2958,
            "longitude": 76.6394,
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["latitude"] == 12.2958
    assert response.json()["data"]["longitude"] == 76.6394


def test_refresh_cookie_rotates_and_replay_revokes_its_family():
    phone = f"+9195{uuid4().int % 10**8:08d}"
    registered = client.post(
        "/api/v1/auth/register",
        json={"name": "Refresh Test Farmer", "phone": phone, "password": "StrongPass123"},
    )
    assert registered.status_code == 201
    old_access = registered.json()["data"]["access_token"]
    old_refresh = registered.cookies.get("farmwise_refresh")
    assert old_refresh
    assert "httponly" in registered.headers["set-cookie"].lower()

    refresh_headers = {"X-FarmWise-Refresh": "1"}
    rotated = client.post(
        "/api/v1/auth/refresh",
        headers=refresh_headers,
        cookies={"farmwise_refresh": old_refresh},
    )
    assert rotated.status_code == 200
    new_access = rotated.json()["data"]["access_token"]
    new_refresh = rotated.cookies.get("farmwise_refresh")
    assert new_refresh and new_refresh != old_refresh
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old_access}"}).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"}).status_code == 200

    replay = client.post(
        "/api/v1/auth/refresh",
        headers=refresh_headers,
        cookies={"farmwise_refresh": old_refresh},
    )
    assert replay.status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"}).status_code == 401


def test_logout_revokes_access_session_and_admin_self_registration_is_rejected():
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Logout Test Farmer",
            "phone": f"+9196{uuid4().int % 10**8:08d}",
            "password": "StrongPass123",
        },
    )
    access = registration.json()["data"]["access_token"]
    logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {access}"})
    assert logout.status_code == 200
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"}).status_code == 401

    admin_signup = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Self Assigned Admin",
            "phone": f"+9197{uuid4().int % 10**8:08d}",
            "password": "StrongPass123",
            "role": "admin",
        },
    )
    assert admin_signup.status_code == 422


def test_authentication_rate_limit_returns_429():
    for _ in range(10):
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": "+919999999998", "password": "WrongPassword123"},
        )
        assert response.status_code == 401
    limited = client.post(
        "/api/v1/auth/login",
        json={"phone": "+919999999998", "password": "WrongPassword123"},
    )
    assert limited.status_code == 429
