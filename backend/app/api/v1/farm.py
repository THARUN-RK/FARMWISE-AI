from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models.entities import Farmer, FarmProfile
from app.schemas.farm import FarmProfileCreate, FarmProfileOut

logger = logging.getLogger("farmwise.api.v1.farm")
router = APIRouter(tags=["farm-profile"])


def _get_or_create_profile(db: Session, user: Farmer) -> FarmProfile:
    profile = db.scalar(select(FarmProfile).where(FarmProfile.user_id == user.id))
    if profile is not None:
        return profile
    profile = FarmProfile(user_id=user.id)
    db.add(profile)
    db.flush()
    return profile


@router.post("/farm/profile", status_code=201)
def create_farm_profile(
    body: FarmProfileCreate,
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(db, user)
    for field, value in body.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    logger.info("Farm profile created for user_id=%s", user.id)
    return {"success": True, "message": "Farm profile saved successfully", "data": FarmProfileOut.model_validate(profile)}


@router.get("/farm/profile")
def get_farm_profile(
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(FarmProfile).where(FarmProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=404, detail={"code": "FARM_PROFILE_NOT_FOUND", "message": "Farm profile not found"})
    return {"success": True, "data": FarmProfileOut.model_validate(profile)}


@router.put("/farm/profile")
def update_farm_profile(
    body: FarmProfileCreate,
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(db, user)
    for field, value in body.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    logger.info("Farm profile updated for user_id=%s", user.id)
    return {"success": True, "message": "Farm profile updated successfully", "data": FarmProfileOut.model_validate(profile)}
