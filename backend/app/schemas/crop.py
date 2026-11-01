from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CropSummary(BaseModel):
    id: int
    crop_name: str
    crop_category: str | None = None
    suitable_soil_types: str | None = None
    suitable_seasons: str | None = None
    water_requirement: str | None = None
    minimum_land_area: float | None = None
    cultivation_duration_days: int | None = None
    suitable_regions: str | None = None
    estimated_cost_per_acre: float | None = None
    expected_yield_min: float | None = None
    expected_yield_max: float | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class CropDetail(CropSummary):
    scientific_name: str | None = None
    seed_requirement_per_acre: str | None = None
    fertilizer_guidelines: str | None = None
    temperature_range: str | None = None
    rainfall_requirement: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
