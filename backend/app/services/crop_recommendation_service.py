from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Crop, Farm, FarmProfile

logger = logging.getLogger("farmwise.crop_recommendation")


def _normalize(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split()).lower()


def _as_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


class CropRecommendationService:
    @staticmethod
    def _get_profile(db: Session, user: Any) -> FarmProfile | None:
        profile = db.scalar(select(FarmProfile).where(FarmProfile.user_id == user.id))
        if profile is not None:
            return profile
        legacy_farm = db.scalar(
            select(Farm).where(Farm.farmer_id == user.id).order_by(Farm.updated_at.desc())
        )
        if legacy_farm is None:
            return None
        profile = FarmProfile(
            user_id=user.id,
            state=getattr(user, "state", None),
            district=getattr(user, "district", None),
            land_area_acres=legacy_farm.land_size_acres,
            soil_type=legacy_farm.soil_type,
            water_availability=legacy_farm.water_availability,
            current_season=legacy_farm.current_season,
            budget=legacy_farm.budget,
            previous_crop=legacy_farm.previous_crop,
        )
        db.add(profile)
        db.flush()
        return profile

    @staticmethod
    def _missing_fields(profile: FarmProfile) -> list[str]:
        required = {
            "state": profile.state,
            "district": profile.district,
            "land_area_acres": profile.land_area_acres,
            "soil_type": profile.soil_type,
            "water_availability": profile.water_availability,
            "irrigation_type": profile.irrigation_type,
            "current_season": profile.current_season,
            "budget": profile.budget,
        }
        missing = [name for name, value in required.items() if value in (None, "", 0)]
        return missing

    @staticmethod
    def _score_soil(profile_soil: str | None, crop_soils: Iterable[str]) -> int:
        if not profile_soil:
            return 60
        normalized_profile = _normalize(profile_soil)
        crop_values = [
            _normalize(item)
            for item in crop_soils
            if item and str(item).strip()
        ]
        if not crop_values:
            return 75
        if any(normalized_profile == item for item in crop_values):
            return 95
        if any(normalized_profile in item or item in normalized_profile for item in crop_values):
            return 82
        return 60

    @staticmethod
    def _score_season(profile_season: str | None, crop_seasons: Iterable[str]) -> int:
        if not profile_season:
            return 60
        profile_norm = _normalize(profile_season)
        crop_values = [
            _normalize(item)
            for item in crop_seasons
            if item and str(item).strip()
        ]
        if not crop_values:
            return 75
        if any(profile_norm == item or profile_norm in item or item in profile_norm for item in crop_values):
            return 90
        return 65

    @staticmethod
    def _score_water(profile_water: str | None, crop_water: str | None) -> int:
        profile_key = _normalize(profile_water or "")
        crop_key = _normalize(crop_water or "")
        if not profile_key or not crop_key:
            return 70
        score_map = {
            "low": {"low": 96, "medium": 72, "high": 45},
            "medium": {"low": 88, "medium": 95, "high": 78},
            "high": {"low": 81, "medium": 90, "high": 96},
            "adequate": {"low": 88, "medium": 94, "high": 82},
        }
        return score_map.get(profile_key, {}).get(crop_key, 70)

    @staticmethod
    def _score_budget(profile_budget: float | None, crop_estimated_cost: float | None) -> int:
        if profile_budget is None or profile_budget <= 0:
            return 70
        if crop_estimated_cost is None:
            return 75
        ratio = profile_budget / crop_estimated_cost if crop_estimated_cost else 0
        if ratio >= 1.1:
            return 95
        if ratio >= 0.8:
            return 82
        if ratio >= 0.6:
            return 68
        return 45

    @staticmethod
    def _score_region(profile_district: str | None, crop_regions: Iterable[str]) -> int:
        if not profile_district:
            return 60
        district = _normalize(profile_district)
        region_values = [
            _normalize(item)
            for item in crop_regions
            if item and str(item).strip()
        ]
        if not region_values:
            return 70
        if any(district in item or item in district for item in region_values):
            return 92
        return 70

    @staticmethod
    def _score_weather(weather: dict[str, Any] | None) -> int:
        if not weather or not weather.get("current"):
            return 75
        temp = weather["current"].get("temperature_c")
        humidity = weather["current"].get("humidity_percent")
        if temp is None and humidity is None:
            return 75
        if temp is not None and humidity is not None:
            if 20 <= float(temp) <= 35 and 40 <= float(humidity) <= 85:
                return 88
            return 70
        return 75

    @staticmethod
    def generate_for_profile(
        db: Session,
        user: Any,
        profile: FarmProfile,
        weather: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        missing_fields = CropRecommendationService._missing_fields(profile)
        if missing_fields:
            raise ValueError(
                "Incomplete farm profile: " + ", ".join(missing_fields) + ". Complete the required profile fields before asking for recommendations."
            )

        crops = db.scalars(select(Crop).order_by(Crop.name.asc())).all()
        recommendations: list[dict[str, Any]] = []

        for crop in crops:
            soil_score = CropRecommendationService._score_soil(profile.soil_type, _as_list(crop.soil_types))
            season_score = CropRecommendationService._score_season(profile.current_season, _as_list(crop.suitable_seasons))
            water_score = CropRecommendationService._score_water(profile.water_availability, crop.water_requirement)
            region_score = CropRecommendationService._score_region(profile.district, _as_list(crop.suitable_regions))
            budget_score = CropRecommendationService._score_budget(profile.budget, crop.estimated_cost_per_acre)
            weather_score = CropRecommendationService._score_weather(weather)

            suitability_score = round(
                soil_score * 0.25
                + season_score * 0.20
                + water_score * 0.20
                + region_score * 0.15
                + budget_score * 0.10
                + weather_score * 0.10
            )

            if suitability_score >= 80:
                category = "High"
            elif suitability_score >= 60:
                category = "Medium"
            else:
                category = "Low"

            reasons = []
            if soil_score >= 80:
                reasons.append("Soil conditions match the crop requirement")
            else:
                reasons.append("Soil conditions need monitoring")
            if season_score >= 80:
                reasons.append("Season matches the crop stage")
            if water_score >= 80:
                reasons.append("Water availability supports the crop")
            else:
                reasons.append("Water availability may require irrigation planning")
            if region_score >= 80:
                reasons.append("District suitability is favourable")

            risks = []
            if soil_score < 70:
                risks.append("Soil suitability is below the preferred range")
            if water_score < 70:
                risks.append("Water stress risk is elevated")
            if budget_score < 65:
                risks.append("Budget may constrain the recommended input plan")

            recommendations.append(
                {
                    "crop_id": crop.id,
                    "crop_name": crop.crop_name,
                    "suitability_score": suitability_score,
                    "suitability_category": category,
                    "cultivation_duration_days": crop.cultivation_duration_days,
                    "water_requirement": crop.water_requirement,
                    "estimated_cost_per_acre": crop.estimated_cost_per_acre,
                    "expected_yield": crop.expected_yield_min or crop.expected_yield_per_acre,
                    "reasons": reasons,
                    "risks": risks,
                    "data_sources": [
                        "Farm profile inputs",
                        "Crop database record",
                    ],
                    "generated_at": None,
                }
            )

        recommendations.sort(key=lambda item: item["suitability_score"], reverse=True)
        return {
            "success": True,
            "message": "Crop recommendations generated successfully",
            "farm_location": {
                "district": profile.district,
                "state": profile.state,
            },
            "recommendations": recommendations,
            "generated_at": None,
        }
