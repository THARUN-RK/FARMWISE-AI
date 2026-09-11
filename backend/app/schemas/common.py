from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = ""

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(pattern=r"^\+?[0-9]{10,15}$")
    email: str | None = None
    password: str = Field(min_length=8)
    confirm_password: str | None = Field(default=None, min_length=8)
    role: str = "farmer"
    language: str = "en"
    state: str | None = None
    district: str | None = None

    @model_validator(mode="after")
    def passwords_match(self):
        if self.confirm_password is not None and self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

class LoginRequest(BaseModel):
    identifier: str | None = Field(default=None, min_length=3)
    phone: str | None = Field(default=None, min_length=3)
    password: str

    @model_validator(mode="after")
    def has_identifier(self):
        if not self.identifier and not self.phone:
            raise ValueError("Email or phone is required")
        return self

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2)
    language: str = "en"
    location_name: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    state: str | None = None
    district: str | None = None

class FarmCreate(BaseModel):
    land_size_acres: float = Field(gt=0)
    soil_type: str
    water_availability: str
    current_season: str
    budget: float = Field(ge=0)
    previous_crop: str | None = None

class FarmOut(FarmCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class CropRequest(BaseModel):
    farm_id: int = Field(gt=0)

class HarvestCreate(BaseModel):
    crop_id: int = Field(gt=0)
    quantity_tonnes: float = Field(gt=0)
    grade: str = "A"
    harvest_date: str
    notes: str | None = None

class MarketRequest(BaseModel):
    harvest_id: int = Field(gt=0)

class BuyerRequest(BaseModel):
    harvest_id: int = Field(gt=0)

class EnquiryCreate(BaseModel):
    buyer_id: int = Field(gt=0)
    harvest_id: int = Field(gt=0)
    quantity_tonnes: float = Field(gt=0)
    offered_price: float = Field(ge=0)
    message: str = ""

class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(sent|viewed|accepted|rejected|completed)$")

class ProfitRequest(BaseModel):
    crop: str
    land_size: float = Field(gt=0)
    expected_yield: float = Field(gt=0, description="Total expected yield in kg")
    selling_price: float = Field(ge=0)
    production_cost: float = Field(ge=0)
    transport_cost: float = Field(ge=0)
    market_charges: float = Field(ge=0)

class CurrentUser(BaseModel):
    id: int
    name: str
    phone: str
    role: str
    email: str | None = None
    language: str = "en"
    location_name: str | None = None
    state: str | None = None
    district: str | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
