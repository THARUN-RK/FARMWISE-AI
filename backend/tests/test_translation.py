"""Tests for translation endpoints."""

from fastapi.testclient import TestClient

from app.main import app
from app.services import translator

client = TestClient(app)


def test_get_interface_translations_english():
    """Test that English translations are returned (should be identity)."""
    response = client.get("/api/v1/translate/interface-strings/en")
    assert response.status_code == 200
    data = response.json()
    assert "dashboard" in data
    assert data.get("dashboard") == "Dashboard"


def test_translation_reports_missing_api_key(monkeypatch):
    """Non-English translation must report missing configuration instead of succeeding with English."""
    monkeypatch.setattr(translator.settings, "google_translate_api_key", "")
    response = client.get("/api/v1/translate/interface-strings/hi")
    assert response.status_code == 503
    assert response.json()["detail"] == "Google Cloud Translation API key is not configured."


def test_hindi_translations_use_google_batch_api(monkeypatch):
    """Translate fixed UI strings in one Google API call and preserve their keys."""

    class FakeClient:
        def translate(self, values, target_language):
            assert target_language == "hi"
            return [{"translatedText": f"{value} (hi)"} for value in values]

    monkeypatch.setattr(translator, "HAS_GOOGLE_TRANSLATE", True)
    monkeypatch.setattr(translator.settings, "google_translate_api_key", "test-key")
    monkeypatch.setattr(
        translator.TranslatorService,
        "_get_client",
        classmethod(lambda cls: FakeClient()),
    )

    response = client.get("/api/v1/translate/interface-strings/hi")
    assert response.status_code == 200
    assert response.json()["dashboard"] == "Dashboard (hi)"
    assert len(response.json()) == len(translator.INTERFACE_STRINGS)


def test_get_interface_translations_unsupported_language():
    """Test that unsupported languages fall back gracefully."""
    response = client.get("/api/v1/translate/interface-strings/xx")
    assert response.status_code == 200
    data = response.json()
    assert data["dashboard"] == "Dashboard"


def test_translate_returns_all_interface_strings():
    """Test that translation endpoint returns all expected interface strings."""
    response = client.get("/api/v1/translate/interface-strings/en")
    assert response.status_code == 200
    data = response.json()

    expected_keys = {
        "dashboard",
        "farm",
        "planner",
        "markets",
        "onlineMarketplaces",
        "buyers",
        "marketplace",
        "messages",
        "harvest",
        "guide",
        "forecast",
        "analytics",
        "profile",
        "login",
        "signup",
        "greeting",
        "cropPlan",
        "marketPlan",
        "externalEyebrow",
        "externalTitle",
        "externalText",
        "farmizenCategory",
        "farmizenDescription",
        "commodityCategory",
        "commodityDescription",
        "visitFarmizen",
        "visitCommodity",
        "externalDisclaimer",
    }

    for key in expected_keys:
        assert key in data, f"Missing translation key: {key}"
        assert isinstance(data[key], str), f"Translation for {key} should be a string"
        assert data[key], f"Translation for {key} should not be empty"
