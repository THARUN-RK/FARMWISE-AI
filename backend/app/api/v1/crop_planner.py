from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models.entities import CropRecommendation, Farmer, FarmProfile, SavedCropRecommendation
from app.schemas.recommendation import RecommendationResult, SavedRecommendationResponse
from app.services.crop_recommendation_service import CropRecommendationService
from app.services.weather_service import WeatherService

logger = logging.getLogger("farmwise.api.v1.crop_planner")
router = APIRouter(tags=["crop-planner"])


def _get_profile_or_404(db: Session, user: Farmer) -> FarmProfile:
    profile = db.scalar(select(FarmProfile).where(FarmProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=404, detail={"code": "FARM_PROFILE_NOT_FOUND", "message": "Save a farm profile before generating recommendations"})
    return profile


@router.post("/crop-planner/recommendations")
def generate_recommendations(
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    profile = _get_profile_or_404(db, user)
    weather = WeatherService.get_weather_for_location(user.latitude, user.longitude)
    try:
        payload = CropRecommendationService.generate_for_profile(db, user, profile, weather)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INCOMPLETE_FARM_PROFILE", "message": str(exc)}) from exc
    recommendations = payload["recommendations"]
    created_ids: list[int] = []

    for recommendation in recommendations:
        record = CropRecommendation(
            user_id=user.id,
            farm_profile_id=profile.id,
            crop_id=recommendation.get("crop_id"),
            crop_name=recommendation["crop_name"],
            suitability_score=float(recommendation["suitability_score"]),
            suitability_category=recommendation["suitability_category"],
            cultivation_duration_days=recommendation.get("cultivation_duration_days"),
            water_requirement=recommendation.get("water_requirement"),
            estimated_cost_per_acre=recommendation.get("estimated_cost_per_acre"),
            expected_yield=recommendation.get("expected_yield"),
            reasons=json.dumps(recommendation.get("reasons", [])),
            risks=json.dumps(recommendation.get("risks", [])),
            data_sources=json.dumps(recommendation.get("data_sources", [])),
            generated_at=datetime.utcnow(),
        )
        db.add(record)
        db.flush()
        created_ids.append(record.id)
        recommendation["recommendation_id"] = record.id
        recommendation["generated_at"] = record.generated_at.isoformat()

    db.commit()

    result = RecommendationResult(
        success=True,
        message="Crop recommendations generated successfully",
        farm_location={"district": profile.district, "state": profile.state},
        recommendations=[
            {
                "crop_id": item["crop_id"],
                "crop_name": item["crop_name"],
                "suitability_score": item["suitability_score"],
                "suitability_category": item["suitability_category"],
                "cultivation_duration_days": item.get("cultivation_duration_days"),
                "water_requirement": item.get("water_requirement"),
                "estimated_cost_per_acre": item.get("estimated_cost_per_acre"),
                "expected_yield": item.get("expected_yield"),
                "reasons": item.get("reasons", []),
                "risks": item.get("risks", []),
                "data_sources": item.get("data_sources", []),
            }
            for item in recommendations
        ],
        generated_at=datetime.utcnow(),
    )
    logger.info("Generated %s crop recommendations for user_id=%s", len(created_ids), user.id)
    return result.model_dump(mode="json")


@router.get("/crop-planner/recommendations")
def list_recommendations(
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(CropRecommendation)
        .where(CropRecommendation.user_id == user.id)
        .order_by(CropRecommendation.generated_at.desc())
    ).all()

    payload = []
    for row in rows:
        payload.append(
            {
                "recommendation_id": row.id,
                "crop_id": row.crop_id,
                "crop_name": row.crop_name,
                "suitability_score": row.suitability_score,
                "suitability_category": row.suitability_category,
                "cultivation_duration_days": row.cultivation_duration_days,
                "water_requirement": row.water_requirement,
                "estimated_cost_per_acre": row.estimated_cost_per_acre,
                "expected_yield": row.expected_yield,
                "reasons": json.loads(row.reasons) if row.reasons else [],
                "risks": json.loads(row.risks) if row.risks else [],
                "data_sources": json.loads(row.data_sources) if row.data_sources else [],
                "generated_at": row.generated_at.isoformat(),
            }
        )

    return {"success": True, "data": payload, "message": "Recommendation history retrieved successfully"}


@router.get("/crop-planner/weather")
def weather_for_location(
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(FarmProfile).where(FarmProfile.user_id == user.id))
    lat = user.latitude
    lon = user.longitude
    if profile is not None:
        # The farm profile does not store latitude/longitude, so this remains a best-effort lookup.
        pass
    return WeatherService.get_weather_for_location(lat, lon)


@router.post("/crop-planner/recommendations/{recommendation_id}/save")
def save_recommendation(
    recommendation_id: int,
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    recommendation = db.get(CropRecommendation, recommendation_id)
    if recommendation is None or recommendation.user_id != user.id:
        raise HTTPException(status_code=404, detail={"code": "RECOMMENDATION_NOT_FOUND", "message": "Recommendation not found"})

    existing = db.scalar(
        select(SavedCropRecommendation).where(
            SavedCropRecommendation.user_id == user.id,
            SavedCropRecommendation.recommendation_id == recommendation_id,
        )
    )
    if existing is not None:
        return SavedRecommendationResponse(success=True, message="Recommendation already saved", recommendation_id=recommendation_id, saved=True).model_dump()

    saved = SavedCropRecommendation(user_id=user.id, recommendation_id=recommendation_id)
    db.add(saved)
    db.commit()
    return SavedRecommendationResponse(success=True, message="Recommendation saved successfully", recommendation_id=recommendation_id, saved=True).model_dump()


@router.delete("/crop-planner/recommendations/{recommendation_id}/save")
def unsave_recommendation(
    recommendation_id: int,
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    saved = db.scalar(
        select(SavedCropRecommendation).where(
            SavedCropRecommendation.user_id == user.id,
            SavedCropRecommendation.recommendation_id == recommendation_id,
        )
    )
    if saved is None:
        raise HTTPException(status_code=404, detail={"code": "SAVED_RECOMMENDATION_NOT_FOUND", "message": "Saved recommendation not found"})
    db.delete(saved)
    db.commit()
    return {"success": True, "message": "Saved recommendation removed", "recommendation_id": recommendation_id}
