import os
os.environ["DATABASE_URL"] = "sqlite:///./test_farmwise.db"
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.entities import Crop
from app.utils.distance import calculate_distance_km

client = TestClient(app)

def auth():
    response = client.post("/api/v1/auth/register", json={"name":"Test Farmer","phone":"+919876543210","password":"StrongPass123"})
    if response.status_code == 409:
        response = client.post("/api/v1/auth/login", json={"phone":"+919876543210","password":"StrongPass123"})
    return response.json()["data"]["access_token"]

def test_distance():
    assert 110 < calculate_distance_km(0, 0, 1, 0) < 112

def test_profit_validation_and_math():
    response = client.post("/api/v1/profit/calculate", json={"crop":"Tomato","land_size":2,"expected_yield":1000,"selling_price":20,"production_cost":5000,"transport_cost":1000,"market_charges":200})
    assert response.status_code == 200
    assert response.json()["data"]["estimated_profit"] == 13800

def test_profile_and_farm_flow():
    db = SessionLocal()
    if not db.query(Crop).count():
        for name, water in (("Groundnut", "Low"), ("Chilli", "Medium"), ("Tomato", "Medium")):
            db.add(Crop(name=name, duration_days=100, water_requirement=water, soil_types="Loamy", suitable_seasons="Kharif", climate_requirement="18-35C", base_production_cost_per_acre=20000, expected_yield_per_acre=1000, risk_level="Low"))
        db.commit()
    db.close()
    token = auth(); headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/farmers/profile", headers=headers, json={"name":"Test Farmer","language":"en","location_name":"Karnataka","latitude":15.3,"longitude":75.7}).status_code == 200
    farm = client.post("/api/v1/farms", headers=headers, json={"land_size_acres":2,"soil_type":"Loamy","water_availability":"Medium","current_season":"Kharif","budget":50000}).json()["data"]
    recommendations = client.post("/api/v1/recommendations/crops", headers=headers, json={"farm_id":farm["id"]})
    assert recommendations.status_code == 200
    assert len(recommendations.json()["data"]["recommendations"]) == 3
