from datetime import date, timedelta
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.entities import Buyer, BuyerRequirement, Crop, Farm, Farmer, Market, MarketPrice

CROPS = [("Groundnut", "Arachis hypogaea", 110, "Low", 17000, 950, "Low"), ("Chilli", "Capsicum annuum", 120, "Medium", 24000, 700, "Medium"), ("Tomato", "Solanum lycopersicum", 95, "Medium", 30000, 2800, "Low"), ("Onion", "Allium cepa", 110, "Medium", 26000, 2500, "Medium"), ("Maize", "Zea mays", 100, "Medium", 18000, 2200, "Low"), ("Paddy", "Oryza sativa", 125, "High", 28000, 2600, "Medium"), ("Cotton", "Gossypium", 170, "Medium", 32000, 700, "Medium"), ("Potato", "Solanum tuberosum", 100, "Medium", 35000, 5000, "Medium"), ("Turmeric", "Curcuma longa", 210, "High", 45000, 2800, "Medium"), ("Sugarcane", "Saccharum officinarum", 300, "High", 65000, 32000, "Low")]
MARKET_NAMES = ["Market A", "Market B", "Market C", "Guntur Central", "Mangalagiri APMC", "Vijayawada Wholesale", "Kurnool Yard", "Anantapur Market", "Mysuru APMC", "Hubballi Market"]

def seed():
    Base.metadata.create_all(bind=engine); db = SessionLocal()
    try:
        if db.scalar(select(Crop).limit(1)): print("Seed already present; no duplicates created."); return
        crops = []
        for name, scientific, duration, water, cost, yield_, risk in CROPS:
            crop = Crop(name=name, scientific_name=scientific, duration_days=duration, water_requirement=water, soil_types="Loamy,Red loam,Black soil", suitable_seasons="Kharif,Rabi", climate_requirement="18-35C", base_production_cost_per_acre=cost, expected_yield_per_acre=yield_, risk_level=risk, description=f"DEMO DATA profile for {name}."); db.add(crop); crops.append(crop)
        farmer = Farmer(name="Demo Farmer", phone="+919999999999", email="demo@farmwise.local", password_hash=hash_password("DemoPass123!"), location_name="Karnataka", latitude=15.3173, longitude=75.7139); db.add(farmer); db.flush(); db.add(Farm(farmer_id=farmer.id, land_size_acres=2, soil_type="Loamy", water_availability="Medium", current_season="Kharif", budget=50000, previous_crop="Maize"))
        markets = []
        for index, name in enumerate(MARKET_NAMES):
            market = Market(name=name, location_name="Karnataka / Andhra Pradesh", latitude=15.3 + index * .12, longitude=75.7 + index * .1, market_charge_per_kg=.4, transport_base_cost=1 + index * .12); db.add(market); markets.append(market)
        db.flush(); today = date.today()
        tomato = next(c for c in crops if c.name == "Tomato")
        for market in markets:
            for days_ago in range(0, 35, 7): db.add(MarketPrice(market_id=market.id, crop_id=tomato.id, date=today - timedelta(days=days_ago), price_per_kg=18 + (market.id % 3) * 1.5 + (35 - days_ago) * .03, arrival_quantity=20 + market.id, demand_level="very high" if market.id % 3 == 1 else "high"))
        for index in range(30):
            buyer = Buyer(name=f"Demo Buyer {index + 1}", business_type=["Trader", "Wholesaler", "Processor", "FPO"][index % 4], location_name="Karnataka", latitude=15.3 + index * .01, longitude=75.7 + index * .01, phone=f"+91900000{index:04d}", email=f"buyer{index + 1}@demo.farmwise", verification_status="verified" if index < 10 else "pending", verification_fields="phone,location" if index < 10 else "location", rating=4.1 + (index % 8) / 10); db.add(buyer); db.flush(); db.add(BuyerRequirement(buyer_id=buyer.id, crop_id=tomato.id, min_quantity_tonnes=1, max_quantity_tonnes=5 + index % 4, accepted_grades="A,B", min_price=17, max_price=22, required_from=today, required_until=today + timedelta(days=90)))
        db.commit(); print("Seeded DEMO DATA: 1 farmer, 10 crops, 10 markets, 30 buyers, price history.")
    finally: db.close()

if __name__ == "__main__": seed()
