from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Farmer(Base):
    __tablename__ = "farmers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="farmer")
    language: Mapped[str] = mapped_column(String(10), default="en")
    state: Mapped[str | None] = mapped_column(String(80))
    district: Mapped[str | None] = mapped_column(String(80))
    location_name: Mapped[str | None] = mapped_column(String(160))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    farms: Mapped[list["Farm"]] = relationship(back_populates="farmer", cascade="all, delete-orphan")

class Farm(Base):
    __tablename__ = "farms"
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    land_size_acres: Mapped[float] = mapped_column(Float)
    soil_type: Mapped[str] = mapped_column(String(80))
    water_availability: Mapped[str] = mapped_column(String(30))
    current_season: Mapped[str] = mapped_column(String(50))
    budget: Mapped[float] = mapped_column(Float, default=0)
    previous_crop: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    farmer: Mapped[Farmer] = relationship(back_populates="farms")

class Crop(Base):
    __tablename__ = "crops"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    scientific_name: Mapped[str | None] = mapped_column(String(120))
    duration_days: Mapped[int] = mapped_column(Integer)
    water_requirement: Mapped[str] = mapped_column(String(30))
    soil_types: Mapped[str] = mapped_column(String(255))
    suitable_seasons: Mapped[str] = mapped_column(String(255))
    climate_requirement: Mapped[str] = mapped_column(String(255))
    base_production_cost_per_acre: Mapped[float] = mapped_column(Float)
    expected_yield_per_acre: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text, default="")

class CropRequirement(Base):
    __tablename__ = "crop_requirements"
    id: Mapped[int] = mapped_column(primary_key=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), index=True)
    soil_type: Mapped[str] = mapped_column(String(80))
    min_temperature: Mapped[float] = mapped_column(Float, default=18)
    max_temperature: Mapped[float] = mapped_column(Float, default=35)
    water_requirement: Mapped[str] = mapped_column(String(30))
    season: Mapped[str] = mapped_column(String(50))
    suitability_score: Mapped[float] = mapped_column(Float)

class Market(Base):
    __tablename__ = "markets"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    location_name: Mapped[str] = mapped_column(String(160))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    market_charge_per_kg: Mapped[float] = mapped_column(Float, default=0)
    transport_base_cost: Mapped[float] = mapped_column(Float, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class MarketPrice(Base):
    __tablename__ = "market_prices"
    id: Mapped[int] = mapped_column(primary_key=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id"), index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    price_per_kg: Mapped[float] = mapped_column(Float)
    arrival_quantity: Mapped[float] = mapped_column(Float, default=0)
    demand_level: Mapped[str] = mapped_column(String(20), default="medium")
    __table_args__ = (Index("ix_market_prices_lookup", "market_id", "crop_id", "date"),)

class Buyer(Base):
    __tablename__ = "buyers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    business_type: Mapped[str] = mapped_column(String(40))
    location_name: Mapped[str] = mapped_column(String(160))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    verification_status: Mapped[str] = mapped_column(String(20), default="pending")
    verification_fields: Mapped[str] = mapped_column(String(255), default="")
    rating: Mapped[float] = mapped_column(Float, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class BuyerRequirement(Base):
    __tablename__ = "buyer_requirements"
    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), index=True)
    min_quantity_tonnes: Mapped[float] = mapped_column(Float)
    max_quantity_tonnes: Mapped[float] = mapped_column(Float)
    accepted_grades: Mapped[str] = mapped_column(String(100))
    min_price: Mapped[float] = mapped_column(Float)
    max_price: Mapped[float] = mapped_column(Float)
    required_from: Mapped[date | None] = mapped_column(Date)
    required_until: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Harvest(Base):
    __tablename__ = "harvests"
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), index=True)
    quantity_tonnes: Mapped[float] = mapped_column(Float)
    grade: Mapped[str] = mapped_column(String(20))
    harvest_date: Mapped[date] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    crop_id: Mapped[int | None] = mapped_column(ForeignKey("crops.id"), nullable=True)
    recommendation_type: Mapped[str] = mapped_column(String(20), index=True)
    score: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float, default=0)
    expected_profit: Mapped[float] = mapped_column(Float, default=0)
    reason_codes: Mapped[str] = mapped_column(Text, default="")
    model_version: Mapped[str] = mapped_column(String(40), default="rules-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Enquiry(Base):
    __tablename__ = "enquiries"
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), index=True)
    harvest_id: Mapped[int] = mapped_column(ForeignKey("harvests.id"), index=True)
    quantity_tonnes: Mapped[float] = mapped_column(Float)
    offered_price: Mapped[float] = mapped_column(Float)
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="sent")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
