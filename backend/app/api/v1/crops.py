from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models.entities import Crop, Farmer
from app.schemas.crop import CropDetail, CropSummary

router = APIRouter(tags=["crops"])


@router.get("/crops")
def list_crops(
    db: Session = Depends(get_db),
    _user: Farmer = Depends(current_user),
):
    crops = db.scalars(select(Crop).order_by(Crop.name.asc())).all()
    return {
        "success": True,
        "data": [CropSummary.model_validate(crop).model_dump() for crop in crops],
        "message": "Crops retrieved successfully",
    }


@router.get("/crops/{crop_id}")
def get_crop(crop_id: int, db: Session = Depends(get_db), _user: Farmer = Depends(current_user)):
    crop = db.get(Crop, crop_id)
    if crop is None:
        raise HTTPException(status_code=404, detail={"code": "CROP_NOT_FOUND", "message": "Crop not found"})
    return {"success": True, "data": CropDetail.model_validate(crop).model_dump()}
