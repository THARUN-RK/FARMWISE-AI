"""
Harvest recording routes.

A harvest ties a farmer's crop to a quantity and grade,
enabling market ranking and buyer matching flows.
"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, farmer_only
from app.core.database import get_db
from app.models.entities import Crop, Harvest
from app.schemas.common import HarvestCreate

log = logging.getLogger("farmwise.harvests")
router = APIRouter(prefix="/harvests", tags=["harvests"])


def _response(data, message: str = ""):
    return {"success": True, "data": data, "message": message}


@router.post("", status_code=201)
def create_harvest(
    body: HarvestCreate,
    user=Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """Record a harvest for the authenticated farmer."""
    if not db.get(Crop, body.crop_id):
        raise HTTPException(404, "Crop not found")
    try:
        harvest_date = date.fromisoformat(body.harvest_date)
    except ValueError:
        raise HTTPException(422, "harvest_date must be YYYY-MM-DD")

    harvest = Harvest(
        farmer_id=user.id,
        harvest_date=harvest_date,
        **body.model_dump(exclude={"harvest_date"}),
    )
    db.add(harvest)
    db.commit()
    db.refresh(harvest)
    log.info("create_harvest farmer_id=%s harvest_id=%s", user.id, harvest.id)
    return _response(
        {"id": harvest.id, "crop_id": harvest.crop_id, "quantity_tonnes": harvest.quantity_tonnes,
         "grade": harvest.grade, "harvest_date": str(harvest.harvest_date)},
        "Harvest recorded",
    )


@router.get("")
def list_harvests(user=Depends(current_user), db: Session = Depends(get_db)):
    """List all harvests for the authenticated farmer."""
    harvests = db.scalars(select(Harvest).where(Harvest.farmer_id == user.id)).all()
    return _response(
        [
            {"id": h.id, "crop_id": h.crop_id, "quantity_tonnes": h.quantity_tonnes,
             "grade": h.grade, "harvest_date": str(h.harvest_date), "notes": h.notes}
            for h in harvests
        ]
    )
