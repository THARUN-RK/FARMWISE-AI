import json
import logging
from datetime import date, datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import Base, engine, ensure_local_schema, get_db
from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.models.entities import Buyer, Crop, Enquiry, Farm, Farmer, Harvest, Market, MarketPrice, Recommendation
from app.schemas.common import *
from app.services.engines import BuyerMatchingService, CropRecommendationService, MarketRankingService, calculate_profit

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("farmwise")
Base.metadata.create_all(bind=engine)
ensure_local_schema()
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
app = FastAPI(title="FarmWise AI API", version="1.0.0", description="India-realistic crop-to-market decision intelligence API. DEMO DATA is clearly marked.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def response(data, message=""):
    return {"success": True, "data": data, "message": message}

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> Farmer:
    try: payload = decode_token(token); user = db.get(Farmer, int(payload["sub"]))
    except (ValueError, KeyError, TypeError): user = None
    if not user: raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Invalid or expired token"})
    return user

def farmer_only(user: Farmer = Depends(current_user)) -> Farmer:
    if user.role not in ("farmer", "admin"): raise HTTPException(403, "Farmer access required")
    return user

@app.get("/health")
def health(): return {"status": "ok", "demo_data": settings.demo_data}

@app.post("/api/v1/auth/register", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if body.role not in ("farmer", "buyer", "admin"): raise HTTPException(422, "Unsupported role")
    if db.scalar(select(Farmer).where(Farmer.phone == body.phone)): raise HTTPException(409, "Phone already registered")
    if body.email and db.scalar(select(Farmer).where(Farmer.email == body.email)): raise HTTPException(409, "Email already registered")
    user = Farmer(name=body.name, phone=body.phone, email=body.email, password_hash=hash_password(body.password), role=body.role, language=body.language, state=body.state, district=body.district, location_name=body.district); db.add(user); db.commit(); db.refresh(user)
    return response({"user": CurrentUser.model_validate(user), "access_token": create_access_token(str(user.id), user.role)}, "Account created")

@app.post("/api/v1/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    identifier = body.identifier or body.phone
    user = db.scalar(select(Farmer).where((Farmer.phone == identifier) | (Farmer.email == identifier)))
    if not user or not verify_password(body.password, user.password_hash): raise HTTPException(401, "Invalid phone or password")
    return response({"access_token": create_access_token(str(user.id), user.role), "token_type": "bearer", "user": CurrentUser.model_validate(user)}, "Login successful")

@app.get("/api/v1/auth/me")
def me(user: Farmer = Depends(current_user)): return response(CurrentUser.model_validate(user))

@app.post("/api/v1/farmers/profile")
def create_profile(body: ProfileUpdate, user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)):
    for key, value in body.model_dump().items(): setattr(user, key, value)
    db.commit(); db.refresh(user); return response(CurrentUser.model_validate(user), "Profile saved")

@app.get("/api/v1/farmers/profile")
def get_profile(user: Farmer = Depends(current_user)): return response(CurrentUser.model_validate(user))

@app.put("/api/v1/farmers/profile")
def update_profile(body: ProfileUpdate, user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)): return create_profile(body, user, db)

@app.post("/api/v1/farms")
def create_farm(body: FarmCreate, user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)):
    farm = Farm(farmer_id=user.id, **body.model_dump()); db.add(farm); db.commit(); db.refresh(farm); return response(FarmOut.model_validate(farm), "Farm saved")

@app.get("/api/v1/farms")
def list_farms(user: Farmer = Depends(current_user), db: Session = Depends(get_db)): return response([FarmOut.model_validate(x) for x in db.scalars(select(Farm).where(Farm.farmer_id == user.id)).all()])

@app.put("/api/v1/farms/{farm_id}")
def update_farm(farm_id: int, body: FarmCreate, user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)):
    farm = db.scalar(select(Farm).where(Farm.id == farm_id, Farm.farmer_id == user.id))
    if not farm: raise HTTPException(404, "Farm not found")
    for key, value in body.model_dump().items(): setattr(farm, key, value)
    db.commit(); db.refresh(farm); return response(FarmOut.model_validate(farm), "Farm updated")

@app.post("/api/v1/recommendations/crops")
def recommend_crops(body: CropRequest, user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)):
    farm = db.scalar(select(Farm).where(Farm.id == body.farm_id, Farm.farmer_id == user.id))
    if not farm: raise HTTPException(404, "Farm not found")
    results = CropRecommendationService.recommend(db, farm)
    for item in results: db.add(Recommendation(farmer_id=user.id, crop_id=item["crop_id"], recommendation_type="crop", score=item["score"], expected_profit=item["expected_profit_per_acre"], reason_codes=json.dumps(item["reason_codes"])))
    db.commit(); log.info("crop_recommendation farmer_id=%s model=rules-v1", user.id); return response({"recommendations": results, "model_version": "rules-v1"}, "Recommendation generated successfully")

@app.get("/api/v1/recommendations/sowing-window/{crop_id}")
def sowing_window(crop_id: int, season: str = Query("Kharif"), user: Farmer = Depends(current_user), db: Session = Depends(get_db)):
    crop = db.get(Crop, crop_id)
    if not crop: raise HTTPException(404, "Crop not found")
    start = date.today() + timedelta(days=7); end = start + timedelta(days=30); harvest_start = start + timedelta(days=crop.duration_days); harvest_end = harvest_start + timedelta(days=20)
    return response({"crop": crop.name, "sowing_window": {"start": str(start), "end": str(end)}, "expected_harvest_window": {"start": str(harvest_start), "end": str(harvest_end)}, "confidence": .86, "reasons": [f"Rules-based {season} calendar", "Weather confirmation is recommended before sowing"], "model_type": "agronomic-rules"})

@app.post("/api/v1/harvests", status_code=201)
def create_harvest(body: HarvestCreate, user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)):
    if not db.get(Crop, body.crop_id): raise HTTPException(404, "Crop not found")
    try: harvest_date = date.fromisoformat(body.harvest_date)
    except ValueError: raise HTTPException(422, "harvest_date must be YYYY-MM-DD")
    harvest = Harvest(farmer_id=user.id, harvest_date=harvest_date, **body.model_dump(exclude={"harvest_date"})); db.add(harvest); db.commit(); db.refresh(harvest); return response({"id": harvest.id, **body.model_dump()}, "Harvest recorded")

@app.get("/api/v1/markets")
def markets(db: Session = Depends(get_db)): return response([{"id": m.id, "name": m.name, "location_name": m.location_name, "active": m.active} for m in db.scalars(select(Market).where(Market.active.is_(True))).all()])

@app.get("/api/v1/markets/prices")
def market_prices(crop_id: int | None = None, market_id: int | None = None, db: Session = Depends(get_db)):
    query = select(MarketPrice)
    if crop_id: query = query.where(MarketPrice.crop_id == crop_id)
    if market_id: query = query.where(MarketPrice.market_id == market_id)
    return response([{"id": p.id, "market_id": p.market_id, "crop_id": p.crop_id, "date": str(p.date), "price_per_kg": p.price_per_kg, "demand_level": p.demand_level} for p in db.scalars(query.order_by(MarketPrice.date.desc())).all()])

@app.get("/api/v1/markets/forecast")
def market_forecast(crop_id: int, market_id: int, forecast_days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    prices = db.scalars(select(MarketPrice).where(MarketPrice.crop_id == crop_id, MarketPrice.market_id == market_id).order_by(MarketPrice.date)).all()
    if not prices: raise HTTPException(404, "Insufficient price data")
    average = sum(item.price_per_kg for item in prices[-5:]) / min(5, len(prices)); spread = max(0.5, average * .08)
    return response({"crop_id": crop_id, "market_id": market_id, "forecast": [{"date": str(date.today() + timedelta(days=index)), "predicted_price": round(average, 2), "lower_bound": round(average - spread, 2), "upper_bound": round(average + spread, 2)} for index in range(1, forecast_days + 1)], "model_type": "moving-average-baseline", "model_version": "baseline-v1", "data_date_range": {"start": str(prices[0].date), "end": str(prices[-1].date)}, "note": "Baseline model - demonstration only."})

@app.get("/api/v1/markets/{market_id}")
def market_detail(market_id: int, db: Session = Depends(get_db)):
    market = db.get(Market, market_id)
    if not market: raise HTTPException(404, "Market not found")
    return response({"id": market.id, "name": market.name, "location_name": market.location_name, "latitude": market.latitude, "longitude": market.longitude, "market_charge_per_kg": market.market_charge_per_kg, "transport_base_cost": market.transport_base_cost, "data_label": "DEMO DATA"})

@app.post("/api/v1/markets/recommend")
def recommend_markets(body: MarketRequest, user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)):
    harvest = db.scalar(select(Harvest).where(Harvest.id == body.harvest_id, Harvest.farmer_id == user.id))
    if not harvest: raise HTTPException(404, "Harvest not found")
    result = MarketRankingService.rank(db, harvest)
    if not result: raise HTTPException(404, "No market data available")
    return response({"markets": result, "data_label": "DEMO DATA"}, "Markets ranked by estimated net realization")

@app.post("/api/v1/buyers/match")
def match_buyers(body: BuyerRequest, user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)):
    harvest = db.scalar(select(Harvest).where(Harvest.id == body.harvest_id, Harvest.farmer_id == user.id))
    if not harvest: raise HTTPException(404, "Harvest not found")
    return response({"buyers": BuyerMatchingService.match(db, harvest), "data_label": "DEMO DATA"}, "Buyer matches generated")

@app.get("/api/v1/buyers")
def list_buyers(db: Session = Depends(get_db)):
    return response([{"id": buyer.id, "name": buyer.name, "business_type": buyer.business_type, "location_name": buyer.location_name, "verification_status": buyer.verification_status, "verification_fields": buyer.verification_fields} for buyer in db.scalars(select(Buyer).where(Buyer.active.is_(True))).all()], "DEMO DATA")

@app.post("/api/v1/enquiries", status_code=201)
def create_enquiry(body: EnquiryCreate, user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)):
    if not db.get(Buyer, body.buyer_id): raise HTTPException(404, "Buyer not found")
    harvest = db.scalar(select(Harvest).where(Harvest.id == body.harvest_id, Harvest.farmer_id == user.id))
    if not harvest: raise HTTPException(404, "Harvest not found")
    enquiry = Enquiry(farmer_id=user.id, **body.model_dump()); db.add(enquiry); db.commit(); db.refresh(enquiry); return response({"id": enquiry.id, "status": enquiry.status, **body.model_dump()}, "Enquiry sent")

@app.get("/api/v1/enquiries")
def enquiries(user: Farmer = Depends(current_user), db: Session = Depends(get_db)): return response([{"id": e.id, "buyer_id": e.buyer_id, "harvest_id": e.harvest_id, "quantity_tonnes": e.quantity_tonnes, "offered_price": e.offered_price, "status": e.status} for e in db.scalars(select(Enquiry).where(Enquiry.farmer_id == user.id)).all()])

@app.patch("/api/v1/enquiries/{enquiry_id}/status")
def update_enquiry(enquiry_id: int, body: StatusUpdate, user: Farmer = Depends(current_user), db: Session = Depends(get_db)):
    enquiry = db.scalar(select(Enquiry).where(Enquiry.id == enquiry_id, Enquiry.farmer_id == user.id))
    if not enquiry: raise HTTPException(404, "Enquiry not found")
    enquiry.status = body.status; db.commit(); return response({"id": enquiry.id, "status": enquiry.status}, "Enquiry updated")

@app.post("/api/v1/profit/calculate")
def profit(body: ProfitRequest): return response(calculate_profit(body.model_dump()), "Profit calculated from supplied estimates")

@app.get("/api/v1/weather/current")
def current_weather(location: str = "Karnataka", user: Farmer = Depends(current_user)): return response({"provider": "mock", "data_label": "DEMO DATA", "location": location, "temperature_c": 28, "rain_probability": 42, "humidity": 72})

@app.get("/api/v1/weather/forecast")
def weather_forecast(location: str = "Karnataka", user: Farmer = Depends(current_user)): return response({"provider": "mock", "data_label": "DEMO DATA", "location": location, "forecast": [{"date": str(date.today() + timedelta(days=index)), "temperature_c": 28 + index % 3, "rain_probability": 35 + index * 4} for index in range(1, 8)]})

@app.get("/api/v1/alerts")
def alerts(user: Farmer = Depends(current_user)): return response([{"type": "weather", "severity": "medium", "message": "Rain probability is elevated this week. Review irrigation plans."}, {"type": "crop-care", "severity": "low", "message": "Scout tomato plots twice this week for early stress signs."}])

@app.get("/api/v1/dashboard/impact")
def impact(user: Farmer = Depends(farmer_only), db: Session = Depends(get_db)):
    farm = db.scalar(select(Farm).where(Farm.farmer_id == user.id)); acres = farm.land_size_acres if farm else 1
    return response({"data_label": "ESTIMATED / DEMO DATA", "expected_net_realization": round(53900 * acres, 2), "expected_farmer_profit": round(84600 * acres, 2), "transport_cost": 1.5, "estimated_selling_delay_days": 2, "post_harvest_loss_assumption_percent": 5, "water_efficiency_index": 74, "input_efficiency_index": 81})

@app.get("/api/v1/admin/analytics")
def analytics(user: Farmer = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "admin": raise HTTPException(403, "Admin access required")
    return response({"registered_farmers": db.scalar(select(func.count(Farmer.id))) or 0, "active_farms": db.scalar(select(func.count(Farm.id))) or 0, "harvests": db.scalar(select(func.count(Harvest.id))) or 0, "enquiries": db.scalar(select(func.count(Enquiry.id))) or 0, "successful_matches": db.scalar(select(func.count(Enquiry.id)).where(Enquiry.status.in_(["accepted", "completed"]))) or 0})
