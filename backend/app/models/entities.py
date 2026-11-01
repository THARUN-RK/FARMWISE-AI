from datetime import date, datetime
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
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
    contacts: Mapped[list["ContactDetail"]] = relationship(back_populates="farmer", cascade="all, delete-orphan")
    farm_profile: Mapped["FarmProfile | None"] = relationship(
        back_populates="farmer",
        uselist=False,
        cascade="all, delete-orphan",
    )

class ContactDetail(Base):
    __tablename__ = "contact_details"
    __table_args__ = (
        UniqueConstraint("farmer_id", "is_primary", name="uq_contact_details_farmer_primary"),
        UniqueConstraint("buyer_id", "is_primary", name="uq_contact_details_buyer_primary"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int | None] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), nullable=True, index=True)
    buyer_id: Mapped[int | None] = mapped_column(ForeignKey("buyers.id", ondelete="CASCADE"), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    alternate_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(12), nullable=True)
    preferred_contact_method: Mapped[str] = mapped_column(String(20), default="phone")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farmer: Mapped[Farmer | None] = relationship(back_populates="contacts")
    buyer: Mapped["Buyer | None"] = relationship(back_populates="contacts")


class FarmProfile(Base):
    __tablename__ = "farm_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), unique=True)
    state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    district: Mapped[str | None] = mapped_column(String(80), nullable=True)
    taluk: Mapped[str | None] = mapped_column(String(80), nullable=True)
    village: Mapped[str | None] = mapped_column(String(100), nullable=True)
    land_area_acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    water_availability: Mapped[str | None] = mapped_column(String(50), nullable=True)
    irrigation_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_season: Mapped[str | None] = mapped_column(String(50), nullable=True)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_crop: Mapped[str | None] = mapped_column(String(80), nullable=True)
    preferred_crop_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farmer: Mapped[Farmer] = relationship(back_populates="farm_profile")

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
    crop_category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    scientific_name: Mapped[str | None] = mapped_column(String(120))

    def __init__(self, **kwargs):
        if "crop_name" in kwargs and "name" not in kwargs:
            kwargs["name"] = kwargs.pop("crop_name")
        super().__init__(**kwargs)
    duration_days: Mapped[int] = mapped_column(Integer)
    water_requirement: Mapped[str] = mapped_column(String(30))
    soil_types: Mapped[str] = mapped_column(String(255))
    suitable_seasons: Mapped[str] = mapped_column(String(255))
    climate_requirement: Mapped[str] = mapped_column(String(255))
    suitable_regions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    minimum_land_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    seed_requirement_per_acre: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fertilizer_guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_cost_per_acre: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_yield_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_yield_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_range: Mapped[str | None] = mapped_column(String(80), nullable=True)
    rainfall_requirement: Mapped[str | None] = mapped_column(String(80), nullable=True)
    base_production_cost_per_acre: Mapped[float] = mapped_column(Float, default=0)
    expected_yield_per_acre: Mapped[float] = mapped_column(Float, default=0)
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def crop_name(self) -> str:
        return self.name

    @property
    def suitable_soil_types(self) -> str:
        return self.soil_types or ""

    @property
    def cultivation_duration_days(self) -> int:
        return self.duration_days or 0

    @property
    def suitable_regions_display(self) -> str:
        return self.suitable_regions or ""

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
    contacts: Mapped[list["ContactDetail"]] = relationship(back_populates="buyer", cascade="all, delete-orphan")

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

class CropListing(Base):
    __tablename__ = "crop_listings"
    id: Mapped[int] = mapped_column(primary_key=True)
    harvest_id: Mapped[int] = mapped_column(ForeignKey("harvests.id"), unique=True, index=True)
    photo_data_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("listing_id", "buyer_user_id", name="uq_conversation_listing_buyer"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("crop_listings.id"), index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    farmer_shares_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    farmer_shares_location: Mapped[bool] = mapped_column(Boolean, default=False)
    buyer_shares_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    buyer_shares_location: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ChatConversation(Base):
    """A farmer's private FarmWise AI assistant thread."""
    __tablename__ = "chat_conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    include_farm_context: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.id",
    )

class ChatMessage(Base):
    """A user turn or provider-generated assistant turn, with source metadata."""
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_messages_role"),
        Index("ix_chat_messages_conversation_created", "conversation_id", "created_at", "id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("chat_conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="en")
    source_references: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    conversation: Mapped[ChatConversation] = relationship(back_populates="messages")

class RefreshToken(Base):
    """Hashed rotating refresh token record; raw tokens never enter the database."""
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    family_id: Mapped[str] = mapped_column(String(36), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    replaced_by_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

class AuditLog(Base):
    """Security and sensitive-action audit metadata; never stores request bodies."""
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_created_action", "created_at", "action"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    outcome: Mapped[str] = mapped_column(String(20), default="success")
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class SoilTest(Base):
    __tablename__ = "soil_tests"
    __table_args__ = (
        CheckConstraint("ph IS NULL OR (ph >= 0 AND ph <= 14)", name="ck_soil_tests_ph_range"),
        CheckConstraint("nitrogen_ppm IS NULL OR nitrogen_ppm >= 0", name="ck_soil_tests_n_nonnegative"),
        CheckConstraint("phosphorus_ppm IS NULL OR phosphorus_ppm >= 0", name="ck_soil_tests_p_nonnegative"),
        CheckConstraint("potassium_ppm IS NULL OR potassium_ppm >= 0", name="ck_soil_tests_k_nonnegative"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    nitrogen_ppm: Mapped[float | None] = mapped_column(Float, nullable=True)
    phosphorus_ppm: Mapped[float | None] = mapped_column(Float, nullable=True)
    potassium_ppm: Mapped[float | None] = mapped_column(Float, nullable=True)
    lab_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    sampled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class FertilizerRecommendation(Base):
    __tablename__ = "fertilizer_recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    soil_test_id: Mapped[int | None] = mapped_column(ForeignKey("soil_tests.id", ondelete="SET NULL"), nullable=True, index=True)
    crop_id: Mapped[int | None] = mapped_column(ForeignKey("crops.id", ondelete="SET NULL"), nullable=True, index=True)
    crop_name: Mapped[str] = mapped_column(String(80))
    growth_stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str] = mapped_column(Text)
    source_references: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_estimate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class DiseaseDetection(Base):
    __tablename__ = "disease_detections"
    __table_args__ = (
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="ck_disease_detection_confidence_range"),
        CheckConstraint("status IN ('uploaded', 'processing', 'completed', 'escalated', 'failed')", name="ck_disease_detection_status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    storage_key: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(20), default="uploaded", index=True)
    predictions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    requires_expert_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class DetectionFeedback(Base):
    __tablename__ = "detection_feedback"
    __table_args__ = (UniqueConstraint("detection_id", "farmer_id", name="uq_detection_feedback_farmer"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    detection_id: Mapped[int] = mapped_column(ForeignKey("disease_detections.id", ondelete="CASCADE"), index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    corrected_condition: Mapped[str | None] = mapped_column(String(160), nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    notification_type: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (CheckConstraint("price_paise >= 0", name="ck_plans_price_nonnegative"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_key: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    price_paise: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    billing_interval: Mapped[str] = mapped_column(String(20), default="month")
    scan_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'active', 'past_due', 'cancelled', 'expired')", name="ck_subscriptions_status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    provider: Mapped[str] = mapped_column(String(40), default="razorpay")
    provider_subscription_id: Mapped[str | None] = mapped_column(String(160), unique=True, nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_paise >= 0", name="ck_payments_amount_nonnegative"),
        CheckConstraint("status IN ('pending', 'captured', 'failed', 'refunded')", name="ck_payments_status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), default="razorpay")
    provider_order_id: Mapped[str] = mapped_column(String(160), unique=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(160), unique=True, nullable=True)
    amount_paise: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ExpertReview(Base):
    __tablename__ = "expert_reviews"
    __table_args__ = (
        CheckConstraint("disease_detection_id IS NOT NULL OR recommendation_id IS NOT NULL", name="ck_expert_review_target"),
        CheckConstraint("status IN ('pending', 'in_review', 'completed')", name="ck_expert_review_status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    expert_user_id: Mapped[int | None] = mapped_column(ForeignKey("farmers.id", ondelete="SET NULL"), nullable=True, index=True)
    disease_detection_id: Mapped[int | None] = mapped_column(ForeignKey("disease_detections.id", ondelete="CASCADE"), nullable=True, index=True)
    recommendation_id: Mapped[int | None] = mapped_column(ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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

class CropRecommendation(Base):
    __tablename__ = "crop_recommendations"
    __table_args__ = (Index("ix_crop_recommendations_user_generated", "user_id", "generated_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"))
    farm_profile_id: Mapped[int | None] = mapped_column(ForeignKey("farm_profiles.id", ondelete="SET NULL"), nullable=True)
    crop_id: Mapped[int | None] = mapped_column(ForeignKey("crops.id", ondelete="SET NULL"), nullable=True)
    crop_name: Mapped[str] = mapped_column(String(80), index=True)
    suitability_score: Mapped[float] = mapped_column(Float, default=0)
    suitability_category: Mapped[str] = mapped_column(String(20), default="Low")
    cultivation_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    water_requirement: Mapped[str | None] = mapped_column(String(40), nullable=True)
    estimated_cost_per_acre: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasons: Mapped[str | None] = mapped_column(Text, nullable=True)
    risks: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_sources: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class SavedCropRecommendation(Base):
    __tablename__ = "saved_crop_recommendations"
    __table_args__ = (UniqueConstraint("user_id", "recommendation_id", name="uq_saved_crop_recommendation_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"))
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("crop_recommendations.id", ondelete="CASCADE"))
    saved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

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
