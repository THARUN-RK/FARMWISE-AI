"""
Translation API endpoints.
"""
from fastapi import APIRouter, HTTPException

from app.services.translator import TranslatorService

router = APIRouter(prefix="/translate", tags=["translate"])


@router.get("/interface-strings/{language}")
def get_interface_translations(language: str):
    """
    Translate all FarmWise interface strings to the target language.

    Returns {key: translated_text} for use in the frontend language selector.

    Example:
        GET /api/v1/translate/interface-strings/hi
        Returns: {"dashboard": "डैशबोर्ड", "farm": "मेरी खेती", ...}
    """
    try:
        return TranslatorService.get_interface_translations(language)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
