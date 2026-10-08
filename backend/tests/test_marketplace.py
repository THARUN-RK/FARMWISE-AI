from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.entities import Crop


client = TestClient(app)


def test_farmer_photo_listing_is_visible_to_authenticated_marketplace():
    db = SessionLocal()
    crop = db.scalar(select(Crop).order_by(Crop.id))
    if crop is None:
        crop = Crop(
            name=f"Test crop {uuid4().hex[:8]}",
            duration_days=100,
            water_requirement="Medium",
            soil_types="Loamy",
            suitable_seasons="Kharif",
            climate_requirement="18-35C",
            base_production_cost_per_acre=20000,
            expected_yield_per_acre=1000,
            risk_level="Low",
        )
        db.add(crop)
        db.commit()
        db.refresh(crop)
    crop_id = crop.id
    db.close()

    phone = f"+9196{uuid4().int % 10**8:08d}"
    farmer_name = f"Marketplace Farmer {uuid4().hex[:6]}"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": farmer_name,
            "phone": phone,
            "password": "StrongPass123",
            "state": "Karnataka",
            "district": "Mysuru",
        },
    )
    assert registration.status_code == 201
    token = registration.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/harvests",
        headers=headers,
        json={
            "crop_id": crop_id,
            "quantity_tonnes": 2.5,
            "grade": "A",
            "harvest_date": date.today().isoformat(),
            "notes": "Ready for pickup",
            "photo_data_url": "data:image/jpeg;base64,/9j/2Q==",
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["is_listed"] is True

    listings = client.get("/api/v1/marketplace/listings", headers=headers)
    assert listings.status_code == 200
    listing = next(
        item for item in listings.json()["data"]
        if item["farmer"]["account_id"] == registration.json()["data"]["user"]["id"]
    )
    assert listing["farmer"]["name"] == farmer_name
    assert listing["farmer"]["district"] == "Mysuru"
    assert "phone" not in listing["farmer"]
    assert "email" not in listing["farmer"]
    assert listing["quantity_tonnes"] == 2.5
    assert listing["photo_data_url"] == "data:image/jpeg;base64,/9j/2Q=="

    own_harvests = client.get("/api/v1/harvests", headers=headers)
    assert own_harvests.json()["data"][0]["is_listed"] is True


def test_conversation_contact_and_location_require_each_party_consent():
    db = SessionLocal()
    crop = db.scalar(select(Crop).order_by(Crop.id))
    if crop is None:
        crop = Crop(
            name=f"Conversation crop {uuid4().hex[:8]}",
            duration_days=100,
            water_requirement="Medium",
            soil_types="Loamy",
            suitable_seasons="Kharif",
            climate_requirement="18-35C",
            base_production_cost_per_acre=20000,
            expected_yield_per_acre=1000,
            risk_level="Low",
        )
        db.add(crop)
        db.commit()
        db.refresh(crop)
    crop_id = crop.id
    db.close()

    suffix = uuid4().hex[:8]

    def register(name: str, role: str, phone: str, email: str):
        result = client.post(
            "/api/v1/auth/register",
            json={
                "name": name,
                "phone": phone,
                "email": email,
                "password": "StrongPass123",
                "role": role,
                "state": "Karnataka",
                "district": "Mysuru",
            },
        )
        assert result.status_code == 201
        data = result.json()["data"]
        return data["user"], {"Authorization": f"Bearer {data['access_token']}"}

    farmer, farmer_headers = register(
        "Consent Farmer", "farmer", f"+9197{uuid4().int % 10**8:08d}", f"farmer-{suffix}@example.com"
    )
    profile = client.put(
        "/api/v1/farmers/profile",
        headers=farmer_headers,
        json={
            "name": farmer["name"],
            "language": "en",
            "location_name": "Farm address",
            "state": "Karnataka",
            "district": "Mysuru",
            "latitude": 12.2958,
            "longitude": 76.6394,
        },
    )
    assert profile.status_code == 200
    harvest = client.post(
        "/api/v1/harvests",
        headers=farmer_headers,
        json={
            "crop_id": crop_id,
            "quantity_tonnes": 1,
            "grade": "A",
            "harvest_date": date.today().isoformat(),
            "photo_data_url": "data:video/mp4;base64,AAAA",
        },
    )
    assert harvest.status_code == 201

    buyer, buyer_headers = register(
        "Consent Buyer", "buyer", f"+9198{uuid4().int % 10**8:08d}", f"buyer-{suffix}@example.com"
    )
    buyer_profile_update = client.put(
        "/api/v1/farmers/profile",
        headers=buyer_headers,
        json={
            "name": buyer["name"],
            "language": "en",
            "location_name": "Buyer address",
            "state": "Karnataka",
            "district": "Mysuru",
            "latitude": 12.3,
            "longitude": 76.6,
        },
    )
    assert buyer_profile_update.status_code == 200
    buyer_directory = client.get("/api/v1/buyers").json()["data"]
    buyer_profile = next(entry for entry in buyer_directory if entry["account_id"] == buyer["id"])
    assert "phone" not in buyer_profile
    assert "email" not in buyer_profile

    listings = client.get("/api/v1/marketplace/listings", headers=buyer_headers).json()["data"]
    listing = next(entry for entry in listings if entry["farmer"]["account_id"] == farmer["id"])
    assert listing["media_type"] == "video/mp4"
    assert "phone" not in listing["farmer"]
    assert "email" not in listing["farmer"]

    started = client.post(
        "/api/v1/conversations",
        headers=buyer_headers,
        json={"listing_id": listing["id"], "message": "Is this ready?", "share_my_contact": False, "share_my_location": False},
    )
    assert started.status_code == 201
    conversation = started.json()["data"]
    assert "phone" not in conversation["other_party"]
    assert "location_name" not in conversation["other_party"]

    buyer_reply = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=buyer_headers,
        json={"message": "Please contact me", "share_my_contact": True, "share_my_location": True},
    )
    assert buyer_reply.status_code == 200
    farmer_view = client.get("/api/v1/conversations", headers=farmer_headers).json()["data"][0]
    assert farmer_view["other_party"]["phone"] == buyer["phone"]
    assert farmer_view["other_party"]["email"] == buyer["email"]
    assert farmer_view["other_party"]["location_name"] == "Buyer address"

    farmer_reply = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=farmer_headers,
        json={"message": "Yes, ready", "share_my_contact": True, "share_my_location": True},
    )
    assert farmer_reply.status_code == 200
    buyer_view = client.get("/api/v1/conversations", headers=buyer_headers).json()["data"][0]
    assert buyer_view["other_party"]["phone"] == farmer["phone"]
    assert buyer_view["other_party"]["email"] == farmer["email"]
    assert buyer_view["other_party"]["location_name"] == "Farm address"
    assert buyer_view["other_party"]["latitude"] == 12.2958


def test_crop_media_rejects_oversized_video():
    db = SessionLocal()
    crop = db.scalar(select(Crop.id).order_by(Crop.id))
    db.close()
    if crop is None:
        return
    phone = f"+9199{uuid4().int % 10**8:08d}"
    registration = client.post(
        "/api/v1/auth/register",
        json={"name": "Video Test Farmer", "phone": phone, "password": "StrongPass123"},
    )
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['data']['access_token']}"}
    response = client.post(
        "/api/v1/harvests",
        headers=headers,
        json={
            "crop_id": crop,
            "quantity_tonnes": 1,
            "grade": "A",
            "harvest_date": date.today().isoformat(),
            "photo_data_url": "data:video/mp4;base64," + ("A" * 14_000_001),
        },
    )
    assert response.status_code == 422


def test_farmer_financial_forecast_uses_saved_farm_and_is_not_buyer_accessible():
    db = SessionLocal()
    crop = db.scalar(select(Crop).order_by(Crop.id))
    crop_id = crop.id if crop else None
    db.close()
    if crop_id is None:
        return

    farmer_result = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Forecast Farmer",
            "phone": f"+9193{uuid4().int % 10**8:08d}",
            "password": "StrongPass123",
        },
    )
    buyer_result = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Forecast Buyer",
            "phone": f"+9192{uuid4().int % 10**8:08d}",
            "password": "StrongPass123",
            "role": "buyer",
        },
    )
    assert farmer_result.status_code == buyer_result.status_code == 201
    farmer_headers = {"Authorization": f"Bearer {farmer_result.json()['data']['access_token']}"}
    buyer_headers = {"Authorization": f"Bearer {buyer_result.json()['data']['access_token']}"}
    farm = client.post(
        "/api/v1/farms",
        headers=farmer_headers,
        json={
            "land_size_acres": 2,
            "soil_type": "Loamy",
            "water_availability": "Medium",
            "current_season": "Kharif",
            "budget": 30000,
        },
    )
    assert farm.status_code == 201
    farm_id = farm.json()["data"]["id"]

    forecast = client.post(
        "/api/v1/dashboard/financial-forecast",
        headers=farmer_headers,
        json={"crop_id": crop_id, "farm_id": farm_id},
    )
    assert forecast.status_code == 200
    result = forecast.json()["data"]
    assert result["farm_acres"] == 2
    assert result["available_budget"] == 30000
    assert result["production_budget_required"] > 0
    assert set(result["scenarios"]) == {"low", "expected", "high"}
    assert result["confidence"] in ("low", "medium")
    assert "not a trained" in result["assumptions"]["model"]

    buyer_forecast = client.post(
        "/api/v1/dashboard/financial-forecast",
        headers=buyer_headers,
        json={"crop_id": crop_id},
    )
    assert buyer_forecast.status_code == 403
