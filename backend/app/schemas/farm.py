from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class FarmProfileCreate(BaseModel):
    state: str = Field(min_length=2, max_length=80)
    district: str = Field(min_length=2, max_length=80)
    taluk: str | None = Field(default=None, max_length=80)
    village: str | None = Field(default=None, max_length=100)
    land_area_acres: float = Field(gt=0)
    soil_type: str = Field(min_length=2, max_length=80)
    water_availability: str = Field(min_length=2, max_length=50)
    irrigation_type: str = Field(min_length=2, max_length=50)
    current_season: str = Field(min_length=2, max_length=50)
    budget: float = Field(ge=0)
    previous_crop: str | None = Field(default=None, max_length=80)
    preferred_crop_category: str | None = Field(default=None, max_length=80)

    @field_validator("state", "district", "taluk", "village", "soil_type", "water_availability", "irrigation_type", "current_season", "previous_crop", "preferred_crop_category", mode="before")
    @classmethod
    def clean_optional_text(cls, value):
        if value is None:
            return value
        if not isinstance(value, str):
            raise TypeError("Field must be a string")
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class FarmProfileOut(FarmProfileCreate):
    id: int
    user_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
