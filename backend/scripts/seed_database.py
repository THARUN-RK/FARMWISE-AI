from datetime import date, timedelta
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.entities import Buyer, BuyerRequirement, Crop, Farm, Farmer, Market, MarketPrice

CROPS = [
    ("Ragi", "Eleusine coracana", "Millets", 100, "Low to medium", "Kharif,Rabi", "Red loam, loamy", "Karnataka, Tamil Nadu, Andhra Pradesh", 9000, 1800, 2200, "20-30C", "500-700 mm", "Sorghum and millets"),
    ("Paddy", "Oryza sativa", "Cereals", 120, "High", "Kharif", "Clay loam, alluvial", "Karnataka, Andhra Pradesh, Telangana", 18000, 3000, 4200, "24-32C", "1000-1500 mm", "Rice and cereals"),
    ("Maize", "Zea mays", "Cereals", 90, "Medium", "Kharif,Rabi", "Loamy, red loam", "Karnataka, Andhra Pradesh", 16000, 2700, 3500, "20-32C", "600-900 mm", "Combinable cereals"),
    ("Groundnut", "Arachis hypogaea", "Oilseeds", 110, "Low to medium", "Kharif", "Sandy loam, red loam", "Karnataka, Tamil Nadu", 14000, 2500, 3200, "22-34C", "500-750 mm", "Groundnut and oilseeds"),
    ("Red gram", "Cajanus cajan", "Pulses", 160, "Low", "Kharif", "Black soil, red loam", "Karnataka, Maharashtra", 11000, 1800, 2600, "20-32C", "500-800 mm", "Pulses and legumes"),
    ("Green gram", "Vigna radiata", "Pulses", 70, "Low", "Kharif,Rabi", "Loamy, sandy loam", "Karnataka, Tamil Nadu", 8000, 1400, 2000, "25-35C", "400-600 mm", "Short-duration pulses"),
    ("Black gram", "Vigna mungo", "Pulses", 80, "Low", "Kharif,Rabi", "Loamy, clay loam", "Karnataka, Andhra Pradesh", 9000, 1500, 2200, "24-33C", "500-700 mm", "Pulses and legumes"),
    ("Sunflower", "Helianthus annuus", "Oilseeds", 90, "Medium", "Kharif", "Loamy, black soil", "Karnataka, Maharashtra", 12000, 2200, 3000, "20-30C", "500-700 mm", "Oilseed cereals"),
    ("Tomato", "Solanum lycopersicum", "Vegetables", 95, "Medium", "Rabi,Kharif", "Loamy, red loam", "Karnataka, Tamil Nadu", 30000, 3500, 5200, "18-30C", "600-900 mm", "Vegetables and horticulture"),
    ("Onion", "Allium cepa", "Vegetables", 100, "Medium", "Kharif,Rabi", "Loamy, sandy loam", "Karnataka, Maharashtra", 26000, 2500, 4200, "15-30C", "500-800 mm", "Vegetables and bulb crops"),
    ("Chilli", "Capsicum annuum", "Vegetables", 120, "Medium", "Kharif,Rabi", "Loamy, red loam", "Karnataka, Telangana", 24000, 2800, 4200, "20-32C", "600-900 mm", "Vegetable and spice crops"),
    ("Potato", "Solanum tuberosum", "Vegetables", 100, "Medium", "Rabi", "Loamy, sandy loam", "Karnataka, Tamil Nadu", 35000, 4200, 5400, "15-25C", "500-750 mm", "Vegetable tubers"),
    ("Coconut", "Cocos nucifera", "Perennials", 330, "Medium", "Year-round", "Sandy loam, laterite", "Karnataka, Kerala, Tamil Nadu", 45000, 3000, 6100, "24-32C", "1500-2000 mm", "Perennial plantation crop"),
    ("Arecanut", "Areca catechu", "Perennials", 360, "High", "Year-round", "Loamy, laterite", "Karnataka, Kerala", 47000, 5000, 7600, "20-32C", "1800-2500 mm", "Perennial plantation crop"),
    ("Sugarcane", "Saccharum officinarum", "Commercial", 300, "High", "Year-round", "Loamy, clay loam", "Karnataka, Maharashtra", 65000, 16000, 24500, "22-35C", "1000-1500 mm", "Commercial sugar crop"),
]
MARKET_NAMES = ["Market A", "Market B", "Market C", "Guntur Central", "Mangalagiri APMC", "Vijayawada Wholesale", "Kurnool Yard", "Anantapur Market", "Mysuru APMC", "Hubballi Market"]

def seed():
    db = SessionLocal()
    try:
        if db.scalar(select(Crop).limit(1)): print("Seed already present; no duplicates created."); return
        crops = []
        for name, scientific, category, duration, water, seasons, soil_types, regions, cost, yield_min, yield_max, temperature, rainfall, description in CROPS:
            crop = Crop(
                crop_name=name,
                crop_category=category,
                scientific_name=scientific,
                duration_days=duration,
                water_requirement=water,
                soil_types=soil_types,
                suitable_seasons=seasons,
                climate_requirement=f"{temperature}; rainfall {rainfall}",
                suitable_regions=regions,
                minimum_land_area=0.5,
                seed_requirement_per_acre="Use local seed rate as per agronomic recommendation",
                fertilizer_guidelines="Use soil-test-guided nutrition plan; do not extrapolate from non-local sources",
                estimated_cost_per_acre=float(cost),
                expected_yield_min=float(yield_min),
                expected_yield_max=float(yield_max),
                temperature_range=temperature,
                rainfall_requirement=rainfall,
                base_production_cost_per_acre=float(cost),
                expected_yield_per_acre=float(yield_max),
                risk_level="medium",
                description=f"Seeded crop profile for {name}. {description}",
            ); db.add(crop); crops.append(crop)
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
