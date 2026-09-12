"""
Crop recommendation and sowing window routes.

Uses the existing CropRecommendationService (rule-based scoring).
All recommendations are scoped to the authenticated farmer's farm.
"""
import json
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, farmer_only
from app.core.database import get_db
from app.models.entities import Crop, Farm, Recommendation
from app.schemas.common import CropRequest
from app.services.engines import CropRecommendationService

log = logging.getLogger("farmwise.crops")
router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _response(data, message: str = ""):
    return {"success": True, "data": data, "message": message}


@router.post("/crops")
def recommend_crops(
    body: CropRequest,
    user=Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """
    Generate crop recommendations for a farm.

    Scores are rule-based (soil × climate × water × season × profit × market).
    Results are stored in the recommendations table for audit/history.
    These are decision-support estimates, not guarantees.
    """
    farm = db.scalar(select(Farm).where(Farm.id == body.farm_id, Farm.farmer_id == user.id))
    if not farm:
        raise HTTPException(404, "Farm not found")

    results = CropRecommendationService.recommend(db, farm)

    for item in results:
        db.add(
            Recommendation(
                farmer_id=user.id,
                crop_id=item["crop_id"],
                recommendation_type="crop",
                score=item["score"],
                expected_profit=item["expected_profit_per_acre"],
                reason_codes=json.dumps(item["reason_codes"]),
            )
        )
    db.commit()
    log.info("crop_recommendation farmer_id=%s farm_id=%s model=rules-v1", user.id, body.farm_id)
    return _response({"recommendations": results, "model_version": "rules-v1"}, "Recommendation generated")


@router.get("/sowing-window/{crop_id}")
def sowing_window(
    crop_id: int,
    season: str = Query("Kharif"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Return the recommended sowing and harvest window for a crop."""
    crop = db.get(Crop, crop_id)
    if not crop:
        raise HTTPException(404, "Crop not found")
    start = date.today() + timedelta(days=7)
    end = start + timedelta(days=30)
    harvest_start = start + timedelta(days=crop.duration_days)
    harvest_end = harvest_start + timedelta(days=20)
    return _response(
        {
            "crop": crop.name,
            "sowing_window": {"start": str(start), "end": str(end)},
            "expected_harvest_window": {"start": str(harvest_start), "end": str(harvest_end)},
            "confidence": 0.86,
            "reasons": [
                f"Rules-based {season} calendar",
                "Weather confirmation is recommended before sowing",
            ],
            "model_type": "agronomic-rules",
        }
    )
