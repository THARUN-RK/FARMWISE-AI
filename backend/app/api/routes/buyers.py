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
from app.models.entities import (
    Buyer, Conversation, ConversationMessage, Crop, CropListing,
    Enquiry, Farmer, Harvest,
)
from app.schemas.common import (
    BuyerRequest, ConversationCreate, ConversationReply, EnquiryCreate, StatusUpdate,
)
from app.services.engines import BuyerMatchingService

log = logging.getLogger("farmwise.buyers")
router = APIRouter(tags=["buyers"])


def _response(data, message: str = ""):
    return {"success": True, "data": data, "message": message}


def _conversation_user(user: Farmer, share_contact: bool, share_location: bool):
    details = {"name": user.name, "role": user.role}
    if share_contact:
        details.update({"phone": user.phone, "email": user.email})
    if share_location:
        details.update({
            "location_name": user.location_name,
            "state": user.state,
            "district": user.district,
            "latitude": user.latitude,
            "longitude": user.longitude,
        })
    return details


def _serialize_conversation(db: Session, conversation: Conversation, user: Farmer):
    listing = db.get(CropListing, conversation.listing_id)
    harvest = db.get(Harvest, listing.harvest_id)
    crop = db.get(Crop, harvest.crop_id)
    farmer = db.get(Farmer, conversation.farmer_id)
    buyer_user = db.get(Farmer, conversation.buyer_user_id)
    is_farmer = user.id == conversation.farmer_id
    other_user = buyer_user if is_farmer else farmer
    other_shares_contact = conversation.buyer_shares_contact if is_farmer else conversation.farmer_shares_contact
    other_shares_location = conversation.buyer_shares_location if is_farmer else conversation.farmer_shares_location
    messages = db.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at, ConversationMessage.id)
    ).all()
    return {
        "id": conversation.id,
        "listing_id": listing.id,
        "crop": crop.name,
        "photo_data_url": listing.photo_data_url,
        "quantity_tonnes": harvest.quantity_tonnes,
        "other_party": _conversation_user(other_user, other_shares_contact, other_shares_location),
        "my_contact_shared": conversation.farmer_shares_contact if is_farmer else conversation.buyer_shares_contact,
        "my_location_shared": conversation.farmer_shares_location if is_farmer else conversation.buyer_shares_location,
        "created_at": conversation.created_at.isoformat(),
        "messages": [
            {
                "id": message.id,
                "sender_id": message.sender_id,
                "body": message.body,
                "created_at": message.created_at.isoformat(),
                "is_mine": message.sender_id == user.id,
            }
            for message in messages
        ],
    }


@router.get("/buyers")
def list_buyers(db: Session = Depends(get_db)):
    """List all active buyers."""
    buyers = db.scalars(select(Buyer).where(Buyer.active.is_(True))).all()
    directory = [
            {
                "id": b.id,
                "account_id": None,
                "name": b.name,
                "business_type": b.business_type,
                "location_name": b.location_name,
                "verification_status": b.verification_status,
                "verification_fields": b.verification_fields,
                "rating": b.rating,
            }
            for b in buyers
        ]
    accounts = db.scalars(
        select(Farmer).where(Farmer.role == "buyer").order_by(Farmer.name)
    ).all()
    directory.extend(
        {
            "id": -account.id,
            "account_id": account.id,
            "name": account.name,
            "business_type": "Buyer / broker",
            "location_name": account.location_name or account.district or account.state or "Location not provided",
            "verification_status": "pending",
            "verification_fields": "account",
            "rating": 0,
        }
        for account in accounts
    )
    return _response(directory)


@router.get("/marketplace/listings")
def list_crop_listings(user=Depends(current_user), db: Session = Depends(get_db)):
    """Show crop media listings without disclosing private farmer contacts."""
    rows = db.execute(
        select(CropListing, Harvest, Crop, Farmer)
        .join(Harvest, Harvest.id == CropListing.harvest_id)
        .join(Crop, Crop.id == Harvest.crop_id)
        .join(Farmer, Farmer.id == Harvest.farmer_id)
        .order_by(CropListing.created_at.desc())
    ).all()
    return _response(
        [
            {
                "id": listing.id,
                "harvest_id": harvest.id,
                "crop": crop.name,
                "quantity_tonnes": harvest.quantity_tonnes,
                "grade": harvest.grade,
                "harvest_date": str(harvest.harvest_date),
                "notes": harvest.notes,
                "photo_data_url": listing.photo_data_url,
                "media_type": listing.photo_data_url.split(";", 1)[0].removeprefix("data:"),
                "farmer": {
                    "name": farmer.name,
                    "location_name": farmer.location_name or farmer.district or farmer.state,
                    "state": farmer.state,
                    "district": farmer.district,
                    "account_id": farmer.id,
                },
                "created_at": listing.created_at.isoformat(),
            }
            for listing, harvest, crop, farmer in rows
        ]
    )


@router.get("/conversations")
def list_conversations(user=Depends(current_user), db: Session = Depends(get_db)):
    if user.role not in ("farmer", "buyer"):
        raise HTTPException(403, "Farmer or buyer account required")
    query = select(Conversation)
    if user.role == "farmer":
        query = query.where(Conversation.farmer_id == user.id)
    else:
        query = query.where(Conversation.buyer_user_id == user.id)
    conversations = db.scalars(query.order_by(Conversation.updated_at.desc())).all()
    return _response([_serialize_conversation(db, item, user) for item in conversations])


@router.post("/conversations", status_code=201)
def create_conversation(
    body: ConversationCreate,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    if user.role not in ("farmer", "buyer"):
        raise HTTPException(403, "Farmer or buyer account required")
    listing = db.get(CropListing, body.listing_id)
    if not listing:
        raise HTTPException(404, "Crop listing not found")
    harvest = db.get(Harvest, listing.harvest_id)
    if user.role == "buyer":
        if harvest.farmer_id == user.id:
            raise HTTPException(400, "You cannot contact your own listing")
        farmer_id, buyer_user_id = harvest.farmer_id, user.id
    else:
        if harvest.farmer_id != user.id:
            raise HTTPException(403, "You can only contact buyers about your own crop listings")
        if not body.buyer_user_id:
            raise HTTPException(422, "Choose a registered buyer account to start a conversation")
        buyer = db.get(Farmer, body.buyer_user_id)
        if not buyer or buyer.role != "buyer":
            raise HTTPException(404, "Buyer account not found")
        farmer_id, buyer_user_id = user.id, buyer.id

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.listing_id == body.listing_id,
            Conversation.buyer_user_id == buyer_user_id,
        )
    )
    if not conversation:
        conversation = Conversation(
            listing_id=body.listing_id,
            farmer_id=farmer_id,
            buyer_user_id=buyer_user_id,
        )
        db.add(conversation)
        db.flush()
    if user.role == "farmer":
        conversation.farmer_shares_contact = body.share_my_contact
        conversation.farmer_shares_location = body.share_my_location
    else:
        conversation.buyer_shares_contact = body.share_my_contact
        conversation.buyer_shares_location = body.share_my_location
    db.add(ConversationMessage(
        conversation_id=conversation.id,
        sender_id=user.id,
        body=body.message.strip(),
    ))
    db.commit()
    db.refresh(conversation)
    log.info("conversation_started conversation_id=%s sender_id=%s", conversation.id, user.id)
    return _response(_serialize_conversation(db, conversation, user), "Message sent")


@router.post("/conversations/{conversation_id}/messages")
def send_conversation_message(
    conversation_id: int,
    body: ConversationReply,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    conversation = db.get(Conversation, conversation_id)
    if not conversation or user.id not in (conversation.farmer_id, conversation.buyer_user_id):
        raise HTTPException(404, "Conversation not found")
    is_farmer = user.id == conversation.farmer_id
    if body.share_my_contact is not None:
        if is_farmer:
            conversation.farmer_shares_contact = body.share_my_contact
        else:
            conversation.buyer_shares_contact = body.share_my_contact
    if body.share_my_location is not None:
        if is_farmer:
            conversation.farmer_shares_location = body.share_my_location
        else:
            conversation.buyer_shares_location = body.share_my_location
    db.add(ConversationMessage(
        conversation_id=conversation.id,
        sender_id=user.id,
        body=body.message.strip(),
    ))
    db.commit()
    db.refresh(conversation)
    return _response(_serialize_conversation(db, conversation, user), "Reply sent")


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
