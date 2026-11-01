from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    crop_id: int | None = None
    crop_name: str
    suitability_score: float
    suitability_category: str
    cultivation_duration_days: int | None = None
    water_requirement: str | None = None
    estimated_cost_per_acre: float | None = None
    expected_yield: float | None = None
    reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)


class RecommendationResult(BaseModel):
    success: bool = True
    message: str = "Crop recommendations generated successfully"
    farm_location: dict[str, str | None] = Field(default_factory=dict)
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    generated_at: datetime | None = None


class SavedRecommendationResponse(BaseModel):
    success: bool = True
    message: str
    recommendation_id: int
    saved: bool
