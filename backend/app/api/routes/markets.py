"""
Market routes: list, detail, prices, forecast, and market recommendations.

Market recommendations use the existing MarketRankingService that scores
markets by net realization (price - transport - charges), demand, and distance.
"""
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, farmer_only
from app.core.database import get_db
from app.models.entities import Harvest, Market, MarketPrice
from app.schemas.common import MarketRequest
from app.services.engines import MarketRankingService

log = logging.getLogger("farmwise.markets")
router = APIRouter(prefix="/markets", tags=["markets"])


def _response(data, message: str = ""):
    return {"success": True, "data": data, "message": message}


@router.get("")
def list_markets(db: Session = Depends(get_db)):
    """List all active markets."""
    markets = db.scalars(select(Market).where(Market.active.is_(True))).all()
    return _response(
        [{"id": m.id, "name": m.name, "location_name": m.location_name, "active": m.active} for m in markets]
    )


@router.get("/prices")
def market_prices(
    crop_id: int | None = None,
    market_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Return market price history, optionally filtered by crop or market."""
    query = select(MarketPrice)
    if crop_id:
        query = query.where(MarketPrice.crop_id == crop_id)
    if market_id:
        query = query.where(MarketPrice.market_id == market_id)
    prices = db.scalars(query.order_by(MarketPrice.date.desc())).all()
    return _response(
        [
            {"id": p.id, "market_id": p.market_id, "crop_id": p.crop_id,
             "date": str(p.date), "price_per_kg": p.price_per_kg, "demand_level": p.demand_level}
            for p in prices
        ]
    )


@router.get("/forecast")
def market_forecast(
    crop_id: int,
    market_id: int,
    forecast_days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """
    Simple moving-average price forecast.

    This is a baseline model for demonstration — not a financial guarantee.
    """
    prices = db.scalars(
        select(MarketPrice)
        .where(MarketPrice.crop_id == crop_id, MarketPrice.market_id == market_id)
        .order_by(MarketPrice.date)
    ).all()
    if not prices:
        raise HTTPException(404, "Insufficient price data")

    average = sum(p.price_per_kg for p in prices[-5:]) / min(5, len(prices))
    spread = max(0.5, average * 0.08)
    return _response(
        {
            "crop_id": crop_id,
            "market_id": market_id,
            "forecast": [
                {
                    "date": str(date.today() + timedelta(days=i)),
                    "predicted_price": round(average, 2),
                    "lower_bound": round(average - spread, 2),
                    "upper_bound": round(average + spread, 2),
                }
                for i in range(1, forecast_days + 1)
            ],
            "model_type": "moving-average-baseline",
            "model_version": "baseline-v1",
            "data_date_range": {"start": str(prices[0].date), "end": str(prices[-1].date)},
            "note": "Baseline model — decision support only.",
        }
    )


@router.post("/recommend")
def recommend_markets(
    body: MarketRequest,
    user=Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """Rank nearby markets by estimated net realization for a given harvest."""
    harvest = db.scalar(select(Harvest).where(Harvest.id == body.harvest_id, Harvest.farmer_id == user.id))
    if not harvest:
        raise HTTPException(404, "Harvest not found")
    result = MarketRankingService.rank(db, harvest)
    if not result:
        raise HTTPException(404, "No market data available for this crop")
    log.info("market_recommend farmer_id=%s harvest_id=%s", user.id, body.harvest_id)
    return _response({"markets": result}, "Markets ranked by estimated net realization")


@router.get("/{market_id}")
def market_detail(market_id: int, db: Session = Depends(get_db)):
    """Return full detail for a single market."""
    market = db.get(Market, market_id)
    if not market:
        raise HTTPException(404, "Market not found")
    return _response(
        {
            "id": market.id,
            "name": market.name,
            "location_name": market.location_name,
            "latitude": market.latitude,
            "longitude": market.longitude,
            "market_charge_per_kg": market.market_charge_per_kg,
            "transport_base_cost": market.transport_base_cost,
        }
    )
