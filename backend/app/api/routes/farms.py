"""
Farm management routes: create, list, update.

Each farmer can only access and modify their own farms — enforced
by filtering every query on `Farm.farmer_id == user.id`.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, farmer_only
from app.core.database import get_db
from app.models.entities import Farm
from app.schemas.common import FarmCreate, FarmOut

log = logging.getLogger("farmwise.farms")
router = APIRouter(prefix="/farms", tags=["farms"])


def _response(data, message: str = ""):
    return {"success": True, "data": data, "message": message}


@router.post("", status_code=201)
def create_farm(
    body: FarmCreate,
    user=Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """Create a new farm for the authenticated farmer."""
    farm = Farm(farmer_id=user.id, **body.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    log.info("create_farm farmer_id=%s farm_id=%s", user.id, farm.id)
    return _response(FarmOut.model_validate(farm), "Farm saved")


@router.get("")
def list_farms(user=Depends(current_user), db: Session = Depends(get_db)):
    """List all farms belonging to the authenticated user."""
    farms = db.scalars(select(Farm).where(Farm.farmer_id == user.id)).all()
    return _response([FarmOut.model_validate(f) for f in farms])


@router.put("/{farm_id}")
def update_farm(
    farm_id: int,
    body: FarmCreate,
    user=Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """Update a farm — only the owner may update it (enforced by farmer_id check)."""
    farm = db.scalar(select(Farm).where(Farm.id == farm_id, Farm.farmer_id == user.id))
    if not farm:
        raise HTTPException(404, "Farm not found")
    for key, value in body.model_dump().items():
        setattr(farm, key, value)
    db.commit()
    db.refresh(farm)
    log.info("update_farm farmer_id=%s farm_id=%s", user.id, farm_id)
    return _response(FarmOut.model_validate(farm), "Farm updated")


@router.delete("/{farm_id}", status_code=204)
def delete_farm(
    farm_id: int,
    user=Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """Delete a farm — only the owner may delete it."""
    farm = db.scalar(select(Farm).where(Farm.id == farm_id, Farm.farmer_id == user.id))
    if not farm:
        raise HTTPException(404, "Farm not found")
    db.delete(farm)
    db.commit()
    log.info("delete_farm farmer_id=%s farm_id=%s", user.id, farm_id)
