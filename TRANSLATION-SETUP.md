# Dynamic Translation for FarmWise AI Interface Strings

## Overview

The language selector lists all 22 constitutionally scheduled Indian languages. The app has built-in translations for selected interface text in five languages and can request a fixed set of additional interface strings from Google Cloud Translation:

1. **Built-in translations** (English, Hindi, Kannada, Telugu, Tamil) — compiled into the frontend at build time
2. **Dynamic translations** — fetched on demand from the backend API for language codes mapped by the translation service

This is not yet a complete translation of every screen into all 22 languages. Unsupported language codes may map to a nearby language or stay in English.

User data (crop notes, profiles, private messages) is never sent to the translation service—only fixed interface text is translated.

---

## Implementation Details

### Frontend

#### Components Added/Modified:
- **`src/App.tsx`**
  - Added `PRE_TRANSLATED_LANGUAGES` set containing languages with built-in translations
  - Added `dynamicTranslations` state to store translations fetched from backend
  - Updated `LanguageContext` to include `dynamicTranslations`
  - Modified `changeLanguage()` to fetch missing translations from `/api/v1/translate/interface-strings/{language}`
  - Updated `useLanguage()` hook to check fallback chain: marketplace translations → UI translations → dynamic translations → English → key

#### How It Works:
1. User opens app and selects a language from the dropdown
2. If language is in `PRE_TRANSLATED_LANGUAGES` (en, hi, kn, te, ta), use built-in translations immediately
3. If language is not pre-translated, fetch translations from backend:
   - `GET /api/v1/translate/interface-strings/{language}`
   - Cache result in state for the session
   - Display translated UI on next render

#### Build Process:
```bash
npm run build
# Compiles TypeScript, bundles React, minifies CSS/JS
# No runtime language download needed for 5 pre-translated languages
```

### Backend

#### New Files:
- **`backend/app/services/translator.py`**
  - `TranslatorService` class with static methods for translation
  - `INTERFACE_STRINGS` dict containing all fixed UI text eligible for translation
  - `LANGUAGE_CODES` mapping FarmWise language codes to Google Translate language codes
  - `translate_strings()` — batch-translates dictionary entries to target language
  - `get_interface_translations()` — public method to get all UI strings translated
  - Returns translated fixed strings for supported codes; reports provider/configuration failures to the caller

- **`backend/app/api/routes/translate.py`**
  - `GET /api/v1/translate/interface-strings/{language}` endpoint
  - Returns `{ key: translated_text }` JSON object
  - No authentication required (interface strings are public)

#### Configuration:
- Added `google_translate_api_key` setting to `app/core/config.py`
- Read from `GOOGLE_TRANSLATE_API_KEY` environment variable
- Added `google-cloud-translate>=3.11` to `requirements.txt`

#### Security:
- Translator only accepts fixed interface keys from `INTERFACE_STRINGS`
- User data is never included in translation requests
- Service account key stored securely as environment variable (never committed)

#### Graceful Degradation:
- If Google Cloud key is missing: the API returns HTTP 503
- If language code is unsupported: returns English translations
- If translation API fails: the API returns an error; the frontend continues showing its English fallback text

---

## Languages Supported

### With Built-in Translations (No API Call Needed):
1. English (en)
2. Hindi (hi)
3. Kannada (kn)
4. Telugu (te)
5. Tamil (ta)

### Requested Through the Backend (where Google supports the target code):
6. Assamese (as)
7. Bengali (bn)
8. Bodo (brx) → mapped to Hindi
9. Dogri (doi) → mapped to Hindi
10. Gujarati (gu)
11. Kashmiri (ks) → mapped to Urdu
12. Konkani (kok) → unsupported (fallback to English)
13. Maithili (mai) → mapped to Hindi
14. Malayalam (ml)
15. Manipuri/Meitei (mni) → unsupported (fallback to English)
16. Marathi (mr)
17. Nepali (ne)
18. Odia (or)
19. Punjabi (pa)
20. Sanskrit (sa) → mapped to Hindi
21. Santali (sat) → unsupported (fallback to English)
22. Sindhi (sd) → mapped to Urdu
23. Urdu (ur)

**Note:** Bodo, Konkani, Manipuri, and Santali are currently unmapped and remain English. Dogri and Maithili are mapped to Hindi; Kashmiri and Sindhi are mapped to Urdu; Sanskrit is mapped to Hindi. A language being listed in the selector does not guarantee that every app string is translated.

---

## API Documentation

### Translation Endpoint

**Endpoint:**
```
GET /api/v1/translate/interface-strings/{language}
```

**Path Parameters:**
- `language` (string, required): Language code (e.g., `hi`, `kn`, `te`, `as`, `ml`)

**Response (200 OK):**
```json
{
  "dashboard": "डैशबोर्ड",
  "farm": "मेरा खेत",
  "planner": "फसल योजनाकार",
  "markets": "बाज़ार की जानकारी",
  "buyers": "खरीदार और दलाल",
  "marketplace": "फसल बाज़ार",
  "messages": "संदेश",
  "harvest": "मेरी फसल",
  "guide": "भारत की फसल मार्गदर्शिका",
  "forecast": "खेती का बजट और मुनाफ़ा",
  "analytics": "विश्लेषण",
  "profile": "प्रोफ़ाइल",
  "login": "लॉग इन",
  "signup": "शुरू करें",
  "greeting": "सुप्रभात",
  "cropPlan": "मुझे क्या उगाना चाहिए?",
  "marketPlan": "मुझे कहाँ बेचना चाहिए?",
  "onlineMarketplaces": "ऑनलाइन कृषि बाज़ार",
  "externalEyebrow": "कृषि बाज़ार",
  "externalTitle": "व्यापार के लिए और बाज़ार खोजें।",
  "externalText": "किसान बाज़ार देखने और कृषि आपूर्तिकर्ताओं व खरीदारों से जुड़ने के लिए इन बाहरी प्लेटफ़ॉर्म पर जाएँ।",
  "farmizenCategory": "जैविक किसान बाज़ार",
  "farmizenDescription": "स्थानीय और जैविक उपज के लिए Farmizen के किसान बाज़ार देखें।",
  "commodityCategory": "कृषि आपूर्तिकर्ताओं और खरीदारों के लिए B2B",
  "commodityDescription": "CommodityOnline के ज़रिए कृषि आपूर्तिकर्ताओं और खरीदारों से जुड़ें।",
  "visitFarmizen": "Farmizen पर जाएँ",
  "visitCommodity": "CommodityOnline पर जाएँ",
  "externalDisclaimer": "यह बाहरी वेबसाइट खोलेगा। FarmWise वहाँ की सूचियों या लेन-देन का प्रबंधन नहीं करता।"
}
```

**Response (200 OK):**
For English or an unmapped language code, fixed interface strings are returned in English. For supported configured languages, Google Cloud Translation returns translations.

**Response (503 Service Unavailable):**
Returned when translation is requested for a mapped non-English language but the API key is missing or the provider cannot initialize.

**Example Usage (Frontend):**
```typescript
const translations = await api.getInterfaceTranslations('hi');
console.log(translations.dashboard); // "डैशबोर्ड"
```

---

## Configuration

### For Local Development:
No configuration needed for English and pre-translated languages. To test cloud translation locally:

1. Create a restricted Google Cloud API key with Cloud Translation API enabled.
2. Store the key as a backend secret; do not commit it.
3. Set the environment variable:
   ```powershell
   $env:GOOGLE_TRANSLATE_API_KEY = "your-api-key"
   ```
4. Restart the backend
5. Test: `curl http://localhost:8000/api/v1/translate/interface-strings/ml`

### For Production (GitHub Actions + Render):

1. Create a restricted Google Cloud API key with Cloud Translation API enabled
2. Add to GitHub repository secrets as `GOOGLE_TRANSLATE_API_KEY`
3. Pass to backend via GitHub Actions workflow:
   ```yaml
   - name: Deploy to Render
     env:
       GOOGLE_TRANSLATE_API_KEY: ${{ secrets.GOOGLE_TRANSLATE_API_KEY }}
   ```
4. Or set directly on Render dashboard: **Settings → Environment**
5. Redeploy backend

**Important:** Never commit the API key to the repository.

---

## Testing

### Backend Translation Tests:
```bash
cd backend
python -m pytest tests/test_translation.py -v
```

**Test Coverage:**
- ✅ English translations return identity (no API call)
- ✅ Translation requires configuration and reports missing API keys
- ✅ Configured translation requests use the Google batch API
- ✅ Unsupported languages fall back to English
- ✅ All expected interface keys are present

**Result:**
```
tests/test_translation.py::test_get_interface_translations_english PASSED
tests/test_translation.py::test_get_interface_translations_hindi PASSED
tests/test_translation.py::test_get_interface_translations_unsupported_language PASSED
tests/test_translation.py::test_translate_returns_all_interface_strings PASSED

============================== 4 passed ==============================
```

### All Backend Tests:
```bash
python -m pytest tests/ -q
# 17 passed (13 original + 4 translation tests)
```

### Frontend Build:
```bash
npm run build
# ✓ built in 455ms
# dist/index.html                   0.51 kB
# dist/assets/index-C_Q7bSAP.css   50.53 kB
# dist/assets/index-xETqtW3N.js   326.92 kB
```

---

## How Users Access This Feature

### Farmer/Buyer Workflow:
1. User opens FarmWise AI at `https://tharun-rk.github.io/FARMWISE-AI/`
2. In the top-right corner, they click the language selector (currently shows "English · English")
3. They see all 23 language options with both native and English names
4. They select a language, e.g., "मलयాளം · Malayalam"
5. Frontend immediately checks if Malayalam is pre-translated (it isn't)
6. Frontend calls `/api/v1/translate/interface-strings/ml` (the backend request)
7. Backend translates all interface text and returns JSON
8. Frontend updates the UI with Malayalam text on next render
9. The selection is saved to `localStorage` so the language persists across sessions

### What Gets Translated:
- Navigation sidebar: Dashboard, My Farm, Crop Planner, etc.
- Modal titles and buttons: Log in, Get started, Send message, etc.
- Marketplace page: Farmizen and CommodityOnline section headings
- Greeting messages: "Good morning" → language-specific greeting

### What Does NOT Get Translated:
- Farmer's own crop notes and harvest descriptions
- Buyer's profile text and business description
- Private conversation messages
- Market prices and technical data

---

## Troubleshooting

### Issue: "Failed to load translations for [language]"
**Cause:** Backend API unreachable or misconfigured.
**Solution:**
- Check `VITE_API_URL` is set and points to `/api/v1`
- Verify backend is running: `curl http://localhost:8000/api/v1/translate/interface-strings/en`
- Check browser console for network errors

### Issue: Language selector shows all languages but clicking them does nothing
**Cause:** Backend `/api/v1/translate` route not registered.
**Solution:**
- Check `backend/app/main.py` includes `from app.api.routes import translate`
- Check `app.include_router(translate.router, prefix=PREFIX)` is present
- Restart backend after code changes

### Issue: Translations are in English instead of the selected language
**Cause:** Google Cloud Translation API key missing, invalid, or not allowed to use the API.
**Solution:**
- Check backend logs for `Could not initialize Google Translate` errors
- Verify `GOOGLE_TRANSLATE_API_KEY` environment variable is set
- Test with: `curl http://localhost:8000/api/v1/translate/interface-strings/hi`
  - A 503 response indicates missing configuration or a provider error; inspect the backend log
  - Verify the API key is restricted to the correct project and the Cloud Translation API is enabled

### Issue: Some language codes return only English
**Cause:** Language code not supported by Google Translate.
**Solution:**
- Check `LANGUAGE_CODES` mapping in `backend/app/services/translator.py`
- Unsupported languages (Bodo, Konkani, Manipuri, Santali) are mapped to nearby languages or English
- This is expected behavior—fallback ensures the app is always usable

---

## Performance & Caching

### Current (Session-Level Caching):
- First language switch: API call (50–200 ms depending on network/API latency)
- Subsequent switches to same language: instant (cached in React state)
- Session data is lost on page reload (user must switch language again)

### Future Optimization:
- Add `localStorage` caching with expiration (e.g., 7 days)
- Backend response caching (Redis) to avoid repeated API calls
- Batch translation requests when user changes language multiple times
- Content Delivery Network (CDN) caching headers for frequently requested languages

---

## Summary of Changes

### Files Created:
- `backend/app/services/translator.py` — Translation service
- `backend/app/api/routes/translate.py` — Translation API endpoint
- `backend/tests/test_translation.py` — Translation tests

### Files Modified:
- `src/App.tsx` — Language selector integration, dynamic translation fetching, context updates
- `src/api.ts` — Added `getInterfaceTranslations()` API method
- `backend/app/main.py` — Registered translate router
- `backend/app/core/config.py` — Added `google_translate_api_key` setting
- `backend/requirements.txt` — Added `google-cloud-translate>=3.11`
- `README.md` — Updated language support documentation
- `backend/README.md` — Documented translation endpoint and configuration

### Test Coverage:
- ✅ 17 backend tests passing (13 original + 4 translation tests)
- ✅ Frontend builds without errors
- ✅ No regressions in existing features

---

## Next Steps for Deployment

1. **GitHub Pages (Frontend):**
   - Merge this PR to `main`
   - GitHub Actions automatically builds and deploys
   - Set `VITE_API_URL` repository variable to deployed backend URL

2. **Render Backend:**
   - Merge this PR to `main`
   - Render auto-rebuilds Docker container
   - Add `GOOGLE_TRANSLATE_API_KEY` to Render environment
   - Service restarts with new env var

3. **Verification:**
   - Test on GitHub Pages: Select a non-English language
   - Verify translations appear within 1–2 seconds
   - Check browser console for API call success
   - Verify user data is never sent to translation service

---

## References

- Google Cloud Translation API: https://cloud.google.com/translate/docs
- 22 Scheduled Languages of India: https://en.wikipedia.org/wiki/Official_languages_of_India
- FarmWise README: Language Support section
