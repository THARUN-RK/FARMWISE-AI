"""
Harvest recording routes.

A harvest ties a farmer's crop to a quantity and grade,
enabling market ranking and buyer matching flows.
"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, farmer_only
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.entities import Crop, CropListing, Harvest
from app.schemas.common import HarvestCreate

log = logging.getLogger("farmwise.harvests")
router = APIRouter(prefix="/harvests", tags=["harvests"])


def _response(data, message: str = ""):
    return {"success": True, "data": data, "message": message}


@router.post("", status_code=201)
@limiter.limit("10/minute")
def create_harvest(
    request: Request,
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
        **body.model_dump(exclude={"harvest_date", "photo_data_url"}),
    )
    db.add(harvest)
    if body.photo_data_url:
        db.flush()
        db.add(CropListing(harvest_id=harvest.id, photo_data_url=body.photo_data_url))
    db.commit()
    db.refresh(harvest)
    log.info("create_harvest farmer_id=%s harvest_id=%s", user.id, harvest.id)
    return _response(
        {"id": harvest.id, "crop_id": harvest.crop_id, "quantity_tonnes": harvest.quantity_tonnes,
         "grade": harvest.grade, "harvest_date": str(harvest.harvest_date),
         "is_listed": bool(body.photo_data_url)},
        "Harvest recorded",
    )


@router.get("")
def list_harvests(user=Depends(current_user), db: Session = Depends(get_db)):
    """List all harvests for the authenticated farmer."""
    rows = db.execute(
        select(Harvest, Crop)
        .join(Crop, Crop.id == Harvest.crop_id)
        .where(Harvest.farmer_id == user.id)
        .order_by(Harvest.harvest_date.desc())
    ).all()
    harvests = [harvest for harvest, _ in rows]
    listings = {
        listing.harvest_id: listing
        for listing in db.scalars(
            select(CropListing).where(CropListing.harvest_id.in_([h.id for h in harvests]))
        ).all()
    } if harvests else {}
    return _response(
        [
            {
                "id": harvest.id,
                "crop_id": harvest.crop_id,
                "crop": crop.name,
                "quantity_tonnes": harvest.quantity_tonnes,
                "grade": harvest.grade,
                "harvest_date": str(harvest.harvest_date),
                "notes": harvest.notes,
                "is_listed": harvest.id in listings,
            }
            for harvest, crop in rows
        ]
    )
