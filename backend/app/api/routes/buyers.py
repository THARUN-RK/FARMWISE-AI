"""
Buyer discovery, matching, and enquiry routes.

Buyer matching uses BuyerMatchingService which scores buyers by
crop requirement fit, quantity match, grade acceptance, proximity, and
verification status.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, farmer_only
from app.core.database import get_db
from app.models.entities import Buyer, Enquiry, Harvest
from app.schemas.common import BuyerRequest, EnquiryCreate, StatusUpdate
from app.services.engines import BuyerMatchingService

log = logging.getLogger("farmwise.buyers")
router = APIRouter(tags=["buyers"])


def _response(data, message: str = ""):
    return {"success": True, "data": data, "message": message}


@router.get("/buyers")
def list_buyers(db: Session = Depends(get_db)):
    """List all active buyers."""
    buyers = db.scalars(select(Buyer).where(Buyer.active.is_(True))).all()
    return _response(
        [
            {
                "id": b.id,
                "name": b.name,
                "business_type": b.business_type,
                "location_name": b.location_name,
                "verification_status": b.verification_status,
                "verification_fields": b.verification_fields,
                "rating": b.rating,
            }
            for b in buyers
        ]
    )


@router.post("/buyers/match")
def match_buyers(
    body: BuyerRequest,
    user=Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """Match buyers to a farmer's harvest based on crop, quantity, grade, and proximity."""
    harvest = db.scalar(select(Harvest).where(Harvest.id == body.harvest_id, Harvest.farmer_id == user.id))
    if not harvest:
        raise HTTPException(404, "Harvest not found")
    matches = BuyerMatchingService.match(db, harvest)
    log.info("buyer_match farmer_id=%s harvest_id=%s matches=%d", user.id, body.harvest_id, len(matches))
    return _response({"buyers": matches}, "Buyer matches generated")


@router.post("/enquiries", status_code=201)
def create_enquiry(
    body: EnquiryCreate,
    user=Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """Send an enquiry to a buyer for a specific harvest."""
    if not db.get(Buyer, body.buyer_id):
        raise HTTPException(404, "Buyer not found")
    harvest = db.scalar(select(Harvest).where(Harvest.id == body.harvest_id, Harvest.farmer_id == user.id))
    if not harvest:
        raise HTTPException(404, "Harvest not found")

    enquiry = Enquiry(farmer_id=user.id, **body.model_dump())
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)
    log.info("enquiry_created farmer_id=%s buyer_id=%s", user.id, body.buyer_id)
    return _response(
        {"id": enquiry.id, "status": enquiry.status, **body.model_dump()},
        "Enquiry sent",
    )


@router.get("/enquiries")
def list_enquiries(user=Depends(current_user), db: Session = Depends(get_db)):
    """List all enquiries sent by the authenticated farmer."""
    enquiries = db.scalars(select(Enquiry).where(Enquiry.farmer_id == user.id)).all()
    return _response(
        [
            {
                "id": e.id,
                "buyer_id": e.buyer_id,
                "harvest_id": e.harvest_id,
                "quantity_tonnes": e.quantity_tonnes,
                "offered_price": e.offered_price,
                "status": e.status,
                "created_at": str(e.created_at),
            }
            for e in enquiries
        ]
    )


@router.patch("/enquiries/{enquiry_id}/status")
def update_enquiry_status(
    enquiry_id: int,
    body: StatusUpdate,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """Update an enquiry status (e.g., accepted, completed)."""
    enquiry = db.scalar(select(Enquiry).where(Enquiry.id == enquiry_id, Enquiry.farmer_id == user.id))
    if not enquiry:
        raise HTTPException(404, "Enquiry not found")
    enquiry.status = body.status
    db.commit()
    return _response({"id": enquiry.id, "status": enquiry.status}, "Enquiry updated")
