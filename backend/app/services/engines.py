from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.entities import Buyer, BuyerRequirement, Crop, Farm, Farmer, Harvest, Market, MarketPrice
from app.utils.distance import calculate_distance_km

SOIL = {"loamy": {"groundnut": 95, "chilli": 90, "tomato": 78}, "red loam": {"groundnut": 94, "chilli": 88, "tomato": 86}, "black soil": {"groundnut": 88, "chilli": 82, "tomato": 72}}
WATER = {"low": {"low": 95, "medium": 72, "high": 45}, "medium": {"low": 92, "medium": 95, "high": 75}, "high": {"low": 90, "medium": 96, "high": 95}}

class CropRecommendationService:
    @staticmethod
    def recommend(db: Session, farm: Farm) -> list[dict]:
        crops = db.scalars(select(Crop)).all(); output = []
        for crop in crops:
            key = crop.name.lower(); soil = SOIL.get(farm.soil_type.lower(), {}).get(key, 75)
            climate, season = 84, 90 if farm.current_season.lower() in crop.suitable_seasons.lower() else 58
            water = WATER.get(farm.water_availability.lower(), WATER["medium"]).get(crop.water_requirement.lower(), 70)
            profit = min(100, crop.expected_yield_per_acre * 100 / max(crop.base_production_cost_per_acre * 2.2, 1))
            market = 86 if crop.risk_level.lower() == "low" else 73
            score = round(.25 * soil + .20 * climate + .15 * water + .15 * season + .15 * profit + .10 * market)
            reasons = (["High soil compatibility"] if soil >= 85 else ["Acceptable soil compatibility"]) + (["Suitable water requirement"] if water >= 85 else ["Water availability needs monitoring"]) + (["Good seasonal fit"] if season >= 80 else ["Seasonal fit is moderate"]) + (["Stable market trend"] if market >= 80 else ["Market volatility is higher"])
            output.append({"crop_id": crop.id, "crop": crop.name, "score": score, "risk": crop.risk_level, "expected_profit_per_acre": round(crop.expected_yield_per_acre * 20 - crop.base_production_cost_per_acre), "reason_codes": {"soil_match": soil, "climate_match": climate, "water_match": water, "season_match": season, "profit_score": round(profit), "market_stability": market}, "reasons": reasons, "explanation": f"{crop.name} is recommended because your soil, water availability and season are a {'strong' if score >= 80 else 'moderate'} match."})
        return sorted(output, key=lambda item: item["score"], reverse=True)[:3]

class MarketRankingService:
    @staticmethod
    def rank(db: Session, harvest: Harvest) -> list[dict]:
        farmer = db.get(Farmer, harvest.farmer_id); crop = db.get(Crop, harvest.crop_id)
        prices = db.scalars(select(MarketPrice).where(MarketPrice.crop_id == crop.id)).all(); markets = db.scalars(select(Market).where(Market.active.is_(True))).all()
        rows = []
        for market in markets:
            relevant = [p for p in prices if p.market_id == market.id]
            if not relevant: continue
            latest = sorted(relevant, key=lambda p: p.date)[-1]; distance = calculate_distance_km(farmer.latitude or 15.3, farmer.longitude or 75.7, market.latitude, market.longitude)
            transport = round(market.transport_base_cost + distance * .015, 2); net = round(latest.price_per_kg - transport - market.market_charge_per_kg, 2)
            demand = {"high": 95, "very high": 100, "medium": 75, "low": 55}.get(latest.demand_level.lower(), 70)
            score = round(.40 * max(0, min(100, net / max(latest.price_per_kg, 1) * 100)) + .20 * demand + .15 * max(0, 100 - min(distance, 100)) + .15 * 82 + .10 * 80)
            rows.append({"market_id": market.id, "market": market.name, "price_per_kg": latest.price_per_kg, "distance_km": distance, "transport_cost_per_kg": transport, "market_charges_per_kg": market.market_charge_per_kg, "net_realization_per_kg": net, "score": score, "demand": latest.demand_level, "reasons": ["Highest estimated net realization" if net == max((r["net_realization_per_kg"] for r in rows), default=net) else "Acceptable transport cost", "Strong buyer demand" if demand >= 90 else "Active local demand"]})
        rows.sort(key=lambda x: x["net_realization_per_kg"], reverse=True)
        for index, row in enumerate(rows): row["recommended"] = index == 0
        return rows

class BuyerMatchingService:
    @staticmethod
    def match(db: Session, harvest: Harvest) -> list[dict]:
        crop = db.get(Crop, harvest.crop_id); farmer = db.get(Farmer, harvest.farmer_id); results = []
        for req in db.scalars(select(BuyerRequirement).where(BuyerRequirement.crop_id == crop.id, BuyerRequirement.active.is_(True))).all():
            buyer = db.get(Buyer, req.buyer_id); quantity = 100 if req.min_quantity_tonnes <= harvest.quantity_tonnes <= req.max_quantity_tonnes else 45; grade = 100 if harvest.grade.lower() in req.accepted_grades.lower() else 40; price = 100 if req.min_price <= 18 <= req.max_price else 60; distance = max(0, 100 - calculate_distance_km(farmer.latitude or 15.3, farmer.longitude or 75.7, buyer.latitude, buyer.longitude)); reliability = {"verified": 100, "pending": 65, "unverified": 35}.get(buyer.verification_status, 35)
            score = round(.30 * 100 + .20 * quantity + .15 * grade + .15 * price + .10 * distance + .10 * reliability)
            results.append({"buyer_id": buyer.id, "name": buyer.name, "business_type": buyer.business_type, "verification_status": buyer.verification_status, "verification_fields": buyer.verification_fields.split(",") if buyer.verification_fields else [], "match_score": score, "required_quantity": f"{req.min_quantity_tonnes:g}-{req.max_quantity_tonnes:g} tonnes", "offer_price_range": f"{req.min_price:g}-{req.max_price:g}/kg", "reasons": ["Crop match", "Quantity requirement fits" if quantity == 100 else "Quantity is outside preferred range", "Grade accepted" if grade == 100 else "Grade needs confirmation", "Nearby buyer"]})
        return sorted(results, key=lambda item: item["match_score"], reverse=True)[:10]

def calculate_profit(data: dict) -> dict:
    revenue = data["expected_yield"] * data["selling_price"]; profit = revenue - data["production_cost"] - data["transport_cost"] - data["market_charges"]
    return {"crop": data["crop"], "revenue": round(revenue, 2), "production_cost": data["production_cost"], "transport_cost": data["transport_cost"], "market_charges": data["market_charges"], "estimated_profit": round(profit, 2), "profit_per_acre": round(profit / data["land_size"], 2), "net_realization_per_kg": round(profit / data["expected_yield"], 2)}
