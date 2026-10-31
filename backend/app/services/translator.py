"""
Translation service using Google Cloud Translation API.
Translates ONLY fixed interface text, never user-generated content.
"""
import logging

from app.core.config import settings

log = logging.getLogger("farmwise.translator")

try:
    from google.api_core.exceptions import GoogleAPICallError
    from google.api_core.client_options import ClientOptions
    from google.cloud import translate_v2

    HAS_GOOGLE_TRANSLATE = True
except ImportError:
    HAS_GOOGLE_TRANSLATE = False


# Fixed interface strings eligible for translation.
# User data (crop notes, profiles, messages) must NEVER be sent to the translator.
INTERFACE_STRINGS = {
    "dashboard": "Dashboard",
    "farm": "My Farm",
    "planner": "Crop Planner",
    "markets": "Market Intelligence",
    "onlineMarketplaces": "Online Marketplaces",
    "buyers": "Buyers & Brokers",
    "marketplace": "Crop Marketplace",
    "messages": "Messages",
    "harvest": "My Harvest",
    "guide": "India Crop Guide",
    "forecast": "Farm Budget & Profit",
    "analytics": "Analytics",
    "profile": "Profile",
    "login": "Log in",
    "signup": "Get started",
    "greeting": "Good morning",
    "cropPlan": "What should I grow?",
    "marketPlan": "Where should you sell?",
    "externalEyebrow": "AGRICULTURE MARKETPLACES",
    "externalTitle": "Explore more places to trade.",
    "externalText": "Visit these external platforms to discover farmer markets and connect with agriculture suppliers and buyers.",
    "farmizenCategory": "Organic farmer markets",
    "farmizenDescription": "Explore Farmizen's farmers' markets for local and organic produce.",
    "commodityCategory": "B2B agri suppliers and buyers",
    "commodityDescription": "Connect with agricultural suppliers and buyers through CommodityOnline.",
    "visitFarmizen": "Visit Farmizen",
    "visitCommodity": "Visit CommodityOnline",
    "externalDisclaimer": "Opens an external website. FarmWise does not manage its listings or transactions.",
    "communityEyebrow": "COMMUNITY DIRECTORY",
    "communityDirectory": "Farmers, buyers & brokers",
    "directoryIntro": "Find people by role. Create an account and complete your profile to join the FarmWise community.",
    "createProfile": "Create your profile",
    "directoryEveryone": "Everyone",
    "directoryFarmers": "Farmers",
    "directoryBuyers": "Buyers & brokers",
    "directoryGrowing": "Growing",
    "directoryFilterLabel": "Filter people by type",
    "directoryVerified": "Verified business",
    "directoryBuyerAccount": "Buyer / broker account",
    "farmerProfilesEmpty": "Farmer profiles will appear here when they create an account.",
    "buyerProfilesEmpty": "Buyer and broker profiles will appear here after they create an account.",
    "buyerDirectoryEmptyHelp": "Choose Buyer / broker as your account type in Profile to join this list.",
    "chooseAccountType": "Choose account type",
    "accountType": "Account type",
    "farmerAccountType": "Farmer",
    "buyerAccountType": "Buyer / broker",
    "adminAccountType": "Administrator",
    "createRealAccount": "Create a real account",
    "directoryDemoNotice": "Demo Mode uses sample profiles. They are not saved to the shared directory. Create a real account to appear in the list.",
}

LANGUAGE_CODES = {
    "as": "as",
    "bn": "bn",
    "brx": "as",  # Bodo is unavailable; use the closest supported regional language
    "doi": "doi",
    "gu": "gu",
    "hi": "hi",
    "kn": "kn",
    "ks": "ur",  # Kashmiri not directly supported; use Urdu
    "kok": "gom",
    "mai": "mai",
    "ml": "ml",
    "mni": "mni-Mtei",
    "mr": "mr",
    "ne": "ne",
    "or": "or",
    "pa": "pa",
    "sa": "sa",
    "sat": "bn",  # Santali is unavailable; use a nearby supported regional language
    "sd": "sd",
    "ta": "ta",
    "te": "te",
    "ur": "ur",
}


class TranslatorService:
    """Translate fixed interface strings to Indian languages."""

    _client = None

    @classmethod
    def _get_client(cls):
        """Lazily initialize Google Translate client."""
        if cls._client is None and HAS_GOOGLE_TRANSLATE and settings.google_translate_api_key:
            try:
                cls._client = translate_v2.Client(
                    client_options=ClientOptions(api_key=settings.google_translate_api_key),
                )
            except GoogleAPICallError as error:
                log.exception("Could not initialize Google Translate")
                raise RuntimeError("Google Translate client initialization failed.") from error
            except (TypeError, ValueError) as error:
                log.exception("Could not initialize Google Translate")
                raise RuntimeError("Google Translate configuration is invalid.") from error
        return cls._client

    @staticmethod
    def translate_strings(
        strings: dict[str, str],
        target_language: str,
    ) -> dict[str, str]:
        """
        Translate a batch of fixed interface strings to the target language.

        Args:
            strings: Dict of {key: English text} for translation.
            target_language: Target language code (e.g., 'hi', 'kn').

        Returns:
            Dict of {key: translated text}. Unmapped languages return English;
            configuration or provider failures raise RuntimeError.
        """
        # Map FarmWise language codes to Google Translate codes.
        google_lang = LANGUAGE_CODES.get(target_language)
        if not google_lang or google_lang == "xx":
            return strings

        if google_lang == "en":
            return strings

        if not settings.google_translate_api_key:
            raise RuntimeError("Google Cloud Translation API key is not configured.")
        if not HAS_GOOGLE_TRANSLATE:
            raise RuntimeError("Google Cloud Translation dependency is not installed.")

        client = TranslatorService._get_client()
        if client is None:
            raise RuntimeError("Google Cloud Translation client could not be initialized.")

        try:
            translated = client.translate(
                list(strings.values()),
                target_language=google_lang,
            )
        except GoogleAPICallError as error:
            log.exception("Translation request failed for language %s", target_language)
            raise RuntimeError("Google Cloud Translation request failed.") from error
        if not isinstance(translated, list) or len(translated) != len(strings):
            raise RuntimeError("Google Cloud Translation returned an incomplete response.")

        return {
            key: result["translatedText"]
            for key, result in zip(strings, translated, strict=True)
        }

    @staticmethod
    def get_interface_translations(target_language: str) -> dict[str, str]:
        """
        Get all interface string translations for the target language.

        Returns {key: translated_text}. Falls back to English on error.
        """
        return TranslatorService.translate_strings(INTERFACE_STRINGS, target_language)
