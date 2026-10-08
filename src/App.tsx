import { createContext, useContext, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import "./marketplace.css";
import {
  api,
  clearToken,
  getToken,
  saveToken,
  type ApiCrop,
  type BuyerProfile,
  type CropListing,
  type CropOption,
  type Conversation,
  type FinancialForecast,
  type Farm,
  type HarvestPayload,
  type User,
} from "./api";
import { agricultureGuide } from "./agricultureGuide";

type GoogleCredentialResponse = { credential: string };
type GoogleCredentialHandler = (response: GoogleCredentialResponse) => void;
type GoogleIdentityClient = {
  initialize: (options: { client_id: string; callback: (response: GoogleCredentialResponse) => void }) => void;
  renderButton: (parent: HTMLElement, options: { theme: "outline"; size: "large"; text: "continue_with"; shape: "rectangular"; width: number }) => void;
};

let initializedGoogleClientId: string | null = null;
let activeGoogleCredentialHandler: GoogleCredentialHandler | null = null;

declare global {
  interface Window {
    google?: { accounts: { id: GoogleIdentityClient } };
  }
}

type Module =
  | "Dashboard"
  | "My Farm"
  | "Crop Planner"
  | "Market Intelligence"
  | "Online Marketplaces"
  | "Buyers & Brokers"
  | "Crop Marketplace"
  | "Messages"
  | "My Harvest"
  | "Crop Guide"
  | "Farm Budget & Profit"
  | "Analytics"
  | "Profile";
type Language = "en" | "kn" | "te" | "ta" | "hi" | "as" | "bn" | "brx" | "doi" | "gu" | "ks" | "kok" | "mai" | "ml" | "mni" | "mr" | "ne" | "or" | "pa" | "sa" | "sat" | "sd" | "ur";
const supportedLanguages: Array<{ code: Language; nativeName: string; englishName: string }> = [
  { code: "en", nativeName: "English", englishName: "English" },
  { code: "as", nativeName: "অসমীয়া", englishName: "Assamese" },
  { code: "bn", nativeName: "বাংলা", englishName: "Bengali" },
  { code: "brx", nativeName: "बड़ो", englishName: "Bodo" },
  { code: "doi", nativeName: "डोगरी", englishName: "Dogri" },
  { code: "gu", nativeName: "ગુજરાતી", englishName: "Gujarati" },
  { code: "hi", nativeName: "हिन्दी", englishName: "Hindi" },
  { code: "kn", nativeName: "ಕನ್ನಡ", englishName: "Kannada" },
  { code: "ks", nativeName: "कॉशुर", englishName: "Kashmiri" },
  { code: "kok", nativeName: "कोंकणी", englishName: "Konkani" },
  { code: "mai", nativeName: "मैथिली", englishName: "Maithili" },
  { code: "ml", nativeName: "മലയാളം", englishName: "Malayalam" },
  { code: "mni", nativeName: "মৈতৈলোন্", englishName: "Manipuri (Meitei)" },
  { code: "mr", nativeName: "मराठी", englishName: "Marathi" },
  { code: "ne", nativeName: "नेपाली", englishName: "Nepali" },
  { code: "or", nativeName: "ଓଡ଼ିଆ", englishName: "Odia" },
  { code: "pa", nativeName: "ਪੰਜਾਬੀ", englishName: "Punjabi" },
  { code: "sa", nativeName: "संस्कृतम्", englishName: "Sanskrit" },
  { code: "sat", nativeName: "ᱥᱟᱱᱛᱟᱲᱤ", englishName: "Santali" },
  { code: "sd", nativeName: "سنڌي", englishName: "Sindhi" },
  { code: "ta", nativeName: "தமிழ்", englishName: "Tamil" },
  { code: "te", nativeName: "తెలుగు", englishName: "Telugu" },
  { code: "ur", nativeName: "اردو", englishName: "Urdu" },
];
const LanguageContext = createContext<{ language: Language; setLanguage: (language: Language) => void; dynamicTranslations: Partial<Record<Language, Record<string, string>>> }>({ language: "en", setLanguage: () => undefined, dynamicTranslations: {} });
const translations: Partial<Record<Language, Record<string, string>>> = {
  en: { dashboard: "Dashboard", farm: "My Farm", planner: "Crop Planner", markets: "Market Intelligence", buyers: "Buyers & Brokers", marketplace: "Crop Marketplace", messages: "Messages", harvest: "My Harvest", guide: "India Crop Guide", forecast: "Farm Budget & Profit", analytics: "Analytics", profile: "Profile", login: "Log in", signup: "Get started", greeting: "Good morning", cropPlan: "What should I grow?", marketPlan: "Where should you sell?" },
  hi: { dashboard: "डैशबोर्ड", farm: "मेरा खेत", planner: "फसल योजनाकार", markets: "बाज़ार की जानकारी", buyers: "खरीदार और दलाल", marketplace: "फसल बाज़ार", messages: "संदेश", harvest: "मेरी फसल", guide: "भारत की फसल मार्गदर्शिका", forecast: "खेती का बजट और मुनाफ़ा", analytics: "विश्लेषण", profile: "प्रोफ़ाइल", login: "लॉग इन", signup: "शुरू करें", greeting: "सुप्रभात", cropPlan: "मुझे क्या उगाना चाहिए?", marketPlan: "मुझे कहाँ बेचना चाहिए?" },
  kn: { dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", farm: "ನನ್ನ ಜಮೀನು", planner: "ಬೆಳೆ ಯೋಜಕ", markets: "ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ", buyers: "ಖರೀದಿದಾರರು ಮತ್ತು ದಲ್ಲಾಳಿಗಳು", marketplace: "ಬೆಳೆ ಮಾರುಕಟ್ಟೆ", messages: "ಸಂದೇಶಗಳು", harvest: "ನನ್ನ ಕೊಯ್ಲು", guide: "ಭಾರತದ ಬೆಳೆ ಮಾರ್ಗದರ್ಶಿ", forecast: "ಕೃಷಿ ಬಜೆಟ್ ಮತ್ತು ಲಾಭ", analytics: "ವಿಶ್ಲೇಷಣೆ", profile: "ಪ್ರೊಫೈಲ್", login: "ಲಾಗಿನ್", signup: "ಪ್ರಾರಂಭಿಸಿ", greeting: "ಶುಭೋದಯ", cropPlan: "ನಾನು ಏನು ಬೆಳೆಯಬೇಕು?", marketPlan: "ನಾನು ಎಲ್ಲಿ ಮಾರಾಟ ಮಾಡಬೇಕು?" },
  te: { dashboard: "డాష్‌బోర్డ్", farm: "నా పొలం", planner: "పంట ప్రణాళిక", markets: "మార్కెట్ సమాచారం", buyers: "కొనుగోలుదారులు మరియు బ్రోకర్లు", marketplace: "పంట మార్కెట్", messages: "సందేశాలు", harvest: "నా పంట", guide: "భారత పంటల గైడ్", forecast: "వ్యవసాయ బడ్జెట్ మరియు లాభం", analytics: "విశ్లేషణ", profile: "ప్రొఫైల్", login: "లాగిన్", signup: "ప్రారంభించండి", greeting: "శుభోదయం", cropPlan: "నేను ఏమి పండించాలి?", marketPlan: "నేను ఎక్కడ అమ్మాలి?" },
  ta: { dashboard: "டாஷ்போர்டு", farm: "என் பண்ணை", planner: "பயிர் திட்டமிடல்", markets: "சந்தை தகவல்", buyers: "வாங்குபவர்கள் மற்றும் தரகர்கள்", marketplace: "பயிர் சந்தை", messages: "செய்திகள்", harvest: "என் அறுவடை", guide: "இந்தியப் பயிர் வழிகாட்டி", forecast: "பண்ணை பட்ஜெட் மற்றும் லாபம்", analytics: "பகுப்பாய்வு", profile: "சுயவிவரம்", login: "உள்நுழை", signup: "தொடங்குங்கள்", greeting: "காலை வணக்கம்", cropPlan: "நான் என்ன பயிரிட வேண்டும்?", marketPlan: "நான் எங்கே விற்க வேண்டும்?" },
};
const marketplacePageTranslations: Partial<Record<Language, Record<string, string>>> = {
  en: { onlineMarketplaces: "Online Marketplaces", externalEyebrow: "AGRICULTURE MARKETPLACES", externalTitle: "Explore more places to trade.", externalText: "Visit these external platforms to discover farmer markets and connect with agriculture suppliers and buyers.", farmizenCategory: "Organic farmer markets", farmizenDescription: "Explore Farmizen’s farmers’ markets for local and organic produce.", commodityCategory: "B2B agri suppliers and buyers", commodityDescription: "Connect with agricultural suppliers and buyers through CommodityOnline.", visitFarmizen: "Visit Farmizen", visitCommodity: "Visit CommodityOnline", externalDisclaimer: "Opens an external website. FarmWise does not manage its listings or transactions." },
  hi: { onlineMarketplaces: "ऑनलाइन कृषि बाज़ार", externalEyebrow: "कृषि बाज़ार", externalTitle: "व्यापार के लिए और बाज़ार खोजें।", externalText: "किसान बाज़ार देखने और कृषि आपूर्तिकर्ताओं व खरीदारों से जुड़ने के लिए इन बाहरी प्लेटफ़ॉर्म पर जाएँ।", farmizenCategory: "जैविक किसान बाज़ार", farmizenDescription: "स्थानीय और जैविक उपज के लिए Farmizen के किसान बाज़ार देखें।", commodityCategory: "कृषि आपूर्तिकर्ताओं और खरीदारों के लिए B2B", commodityDescription: "CommodityOnline के ज़रिए कृषि आपूर्तिकर्ताओं और खरीदारों से जुड़ें।", visitFarmizen: "Farmizen पर जाएँ", visitCommodity: "CommodityOnline पर जाएँ", externalDisclaimer: "यह बाहरी वेबसाइट खोलेगा। FarmWise वहाँ की सूचियों या लेन-देन का प्रबंधन नहीं करता।" },
  kn: { onlineMarketplaces: "ಆನ್‌ಲೈನ್ ಮಾರುಕಟ್ಟೆಗಳು", externalEyebrow: "ಕೃಷಿ ಮಾರುಕಟ್ಟೆಗಳು", externalTitle: "ವ್ಯಾಪಾರ ಮಾಡಲು ಇನ್ನಷ್ಟು ಮಾರುಕಟ್ಟೆಗಳನ್ನು ಅನ್ವೇಷಿಸಿ.", externalText: "ರೈತರ ಮಾರುಕಟ್ಟೆಗಳನ್ನು ಅನ್ವೇಷಿಸಲು ಮತ್ತು ಕೃಷಿ ಪೂರೈಕೆದಾರರು ಹಾಗೂ ಖರೀದಿದಾರರೊಂದಿಗೆ ಸಂಪರ್ಕಿಸಲು ಈ ಬಾಹ್ಯ ವೇದಿಕೆಗಳಿಗೆ ಭೇಟಿ ನೀಡಿ.", farmizenCategory: "ಸಾವಯವ ರೈತರ ಮಾರುಕಟ್ಟೆಗಳು", farmizenDescription: "ಸ್ಥಳೀಯ ಮತ್ತು ಸಾವಯವ ಉತ್ಪನ್ನಗಳಿಗಾಗಿ Farmizen ರೈತರ ಮಾರುಕಟ್ಟೆಗಳನ್ನು ಅನ್ವೇಷಿಸಿ.", commodityCategory: "ಕೃಷಿ ಪೂರೈಕೆದಾರರು ಮತ್ತು ಖರೀದಿದಾರರ B2B ವೇದಿಕೆ", commodityDescription: "CommodityOnline ಮೂಲಕ ಕೃಷಿ ಪೂರೈಕೆದಾರರು ಮತ್ತು ಖರೀದಿದಾರರೊಂದಿಗೆ ಸಂಪರ್ಕಿಸಿ.", visitFarmizen: "Farmizen ಗೆ ಭೇಟಿ ನೀಡಿ", visitCommodity: "CommodityOnline ಗೆ ಭೇಟಿ ನೀಡಿ", externalDisclaimer: "ಬಾಹ್ಯ ವೆಬ್‌ಸೈಟ್ ತೆರೆಯುತ್ತದೆ. ಅದರ ಪಟ್ಟಿಗಳು ಅಥವಾ ವಹಿವಾಟುಗಳನ್ನು FarmWise ನಿರ್ವಹಿಸುವುದಿಲ್ಲ." },
  te: { onlineMarketplaces: "ఆన్‌లైన్ మార్కెట్‌ప్లేస్‌లు", externalEyebrow: "వ్యవసాయ మార్కెట్‌ప్లేస్‌లు", externalTitle: "వ్యాపారం కోసం మరిన్ని వేదికలను చూడండి.", externalText: "రైతు మార్కెట్‌లను తెలుసుకోవడానికి, వ్యవసాయ సరఫరాదారులు మరియు కొనుగోలుదారులతో కలవడానికి ఈ బాహ్య వేదికలను సందర్శించండి.", farmizenCategory: "సేంద్రీయ రైతు మార్కెట్లు", farmizenDescription: "స్థానిక, సేంద్రీయ ఉత్పత్తుల కోసం Farmizen రైతు మార్కెట్‌లను చూడండి.", commodityCategory: "వ్యవసాయ సరఫరాదారులు, కొనుగోలుదారుల B2B వేదిక", commodityDescription: "CommodityOnline ద్వారా వ్యవసాయ సరఫరాదారులు, కొనుగోలుదారులతో కలవండి.", visitFarmizen: "Farmizen సందర్శించండి", visitCommodity: "CommodityOnline సందర్శించండి", externalDisclaimer: "బాహ్య వెబ్‌సైట్ తెరవబడుతుంది. అక్కడి జాబితాలు లేదా లావాదేవీలను FarmWise నిర్వహించదు." },
  ta: { onlineMarketplaces: "ஆன்லைன் சந்தைகள்", externalEyebrow: "வேளாண் சந்தைகள்", externalTitle: "வணிகம் செய்ய மேலும் சந்தைகளைக் கண்டறியுங்கள்.", externalText: "விவசாயிகள் சந்தைகளைக் கண்டறியவும், வேளாண் விநியோகஸ்தர்கள் மற்றும் வாங்குபவர்களுடன் இணையவும் இந்த வெளிப்புற தளங்களைப் பாருங்கள்.", farmizenCategory: "இயற்கை விவசாயிகள் சந்தைகள்", farmizenDescription: "உள்ளூர் மற்றும் இயற்கை விளைபொருட்களுக்கான Farmizen விவசாயிகள் சந்தைகளைக் கண்டறியுங்கள்.", commodityCategory: "வேளாண் விநியோகஸ்தர்கள் மற்றும் வாங்குபவர்களுக்கான B2B", commodityDescription: "CommodityOnline மூலம் வேளாண் விநியோகஸ்தர்கள் மற்றும் வாங்குபவர்களுடன் இணையுங்கள்.", visitFarmizen: "Farmizen தளத்தைப் பாருங்கள்", visitCommodity: "CommodityOnline தளத்தைப் பாருங்கள்", externalDisclaimer: "வெளிப்புற இணையதளம் திறக்கும். அங்குள்ள பட்டியல்கள் அல்லது பரிவர்த்தனைகளை FarmWise நிர்வகிக்காது." },
};
function useLanguage() {
  const context = useContext(LanguageContext);
  return {
    ...context,
    t: (key: string) =>
      marketplacePageTranslations[context.language]?.[key] ??
      translations[context.language]?.[key] ??
      context.dynamicTranslations[context.language]?.[key] ??
      translations.en?.[key] ??
      key,
  };
}
type Crop = {
  name: string;
  score: number;
  yield: string;
  cost: string;
  profit: string;
  risk: string;
  water: string;
  image: string;
  reason: string;
};

type Market = {
  name: string;
  type: string;
  distance: string;
  price: number;
  transport: number;
  charges: number;
  demand: string;
  arrivals: string;
};
const crops: Crop[] = [
  {
    name: "Groundnut",
    score: 92,
    yield: "950 kg / acre",
    cost: "INR 17,000",
    profit: "INR 18,500",
    risk: "Low",
    water: "Low",
    image:
      "https://images.unsplash.com/photo-1589923188900-85dae523342b?auto=format&fit=crop&w=700&q=80",
    reason:
      "Your loamy soil, medium water availability and Kharif timing create a strong fit. Nearby markets also show stable demand.",
  },
  {
    name: "Chilli",
    score: 84,
    yield: "700 kg / acre",
    cost: "INR 24,000",
    profit: "INR 16,200",
    risk: "Medium",
    water: "Medium",
    image:
      "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=700&q=80",
    reason:
      "A good seasonal fit with more upside, balanced by higher price volatility and input cost.",
  },
  {
    name: "Tomato",
    score: 76,
    yield: "2,800 kg / acre",
    cost: "INR 30,000",
    profit: "INR 15,400",
    risk: "Medium",
    water: "Medium",
    image:
      "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=700&q=80",
    reason:
      "High yield potential, but requires careful harvest timing and has a more variable selling window.",
  },
];
const markets: Market[] = [
  {
    name: "Guntur Central Market",
    type: "APMC market",
    distance: "32 km",
    price: 21,
    transport: 1.5,
    charges: 0.4,
    demand: "Very high",
    arrivals: "1,240 t",
  },
  {
    name: "Mangalagiri APMC",
    type: "Wholesale mandi",
    distance: "18 km",
    price: 18,
    transport: 1,
    charges: 0.4,
    demand: "High",
    arrivals: "680 t",
  },
  {
    name: "Vijayawada Wholesale",
    type: "Wholesale market",
    distance: "45 km",
    price: 22,
    transport: 4,
    charges: 0.5,
    demand: "Medium",
    arrivals: "910 t",
  },
];
const buyers = [
  {
    initials: "RT",
    name: "Rajesh Traders",
    type: "Wholesaler",
    location: "Guntur APMC",
    offer: "INR 17–19 / kg",
    quantity: "1–5 tonnes",
    match: 94,
    verification: "Phone · location · business",
  },
  {
    initials: "FC",
    name: "FreshKart Collective",
    type: "FPO / aggregator",
    location: "Vijayawada",
    offer: "INR 18–21 / kg",
    quantity: "2–8 tonnes",
    match: 88,
    verification: "Phone · location",
  },
  {
    initials: "SP",
    name: "Sri Padmavati Foods",
    type: "Processor",
    location: "Tenali",
    offer: "INR 18–20 / kg",
    quantity: "1–4 tonnes",
    match: 82,
    verification: "Location · business",
  },
];
const navItems: { label: Module; icon: string }[] = [
  { label: "Dashboard", icon: "⌂" },
  { label: "My Farm", icon: "⌁" },
  { label: "Crop Planner", icon: "✦" },
  { label: "Market Intelligence", icon: "↗" },
  { label: "Online Marketplaces", icon: "↗" },
  { label: "Buyers & Brokers", icon: "♧" },
  { label: "Crop Marketplace", icon: "▧" },
  { label: "Messages", icon: "✉" },
  { label: "My Harvest", icon: "◒" },
  { label: "Crop Guide", icon: "⌕" },
  { label: "Farm Budget & Profit", icon: "₹" },
  { label: "Analytics", icon: "▥" },
  { label: "Profile", icon: "◎" },
];
const navTranslationKeys: Record<string, string> = { Dashboard: "dashboard", "My Farm": "farm", "Crop Planner": "planner", "Market Intelligence": "markets", "Online Marketplaces": "onlineMarketplaces", "Buyers & Brokers": "buyers", "Crop Marketplace": "marketplace", Messages: "messages", "My Harvest": "harvest", "Crop Guide": "guide", "Farm Budget & Profit": "forecast", Analytics: "analytics", Profile: "profile" };

// Pre-translated languages that don't need backend translation.
const PRE_TRANSLATED_LANGUAGES: Set<Language> = new Set(["en", "hi", "kn", "te", "ta"]);

function App() {
  const [authenticated, setAuthenticated] = useState(false),
    [authMode, setAuthMode] = useState<"login" | "signup" | null>(null),
    [authLoading, setAuthLoading] = useState(true);
  const [language, setLanguage] = useState<Language>(() => {
    const savedLanguage = localStorage.getItem("farmwise_language");
    return supportedLanguages.find((option) => option.code === savedLanguage)?.code ?? "en";
  });
  const [dynamicTranslations, setDynamicTranslations] = useState<Partial<Record<Language, Record<string, string>>>>({});
  const [user, setUser] = useState<User | null>(null),
    [farm, setFarm] = useState<Farm | null>(null),
    [apiRecommendations, setApiRecommendations] = useState<ApiCrop[]>([]);
  const [active, setActive] = useState<Module>("Dashboard"),
    [demo, setDemo] = useState(false),
    [menuOpen, setMenuOpen] = useState(false);
  const [pendingContact, setPendingContact] = useState<{ listingId?: number; buyerUserId?: number } | null>(null);
  const [toast, setToast] = useState(""),
    [enquiryOpen, setEnquiryOpen] = useState(false),
    [enquirySent, setEnquirySent] = useState(false),
    [plannerLoading, setPlannerLoading] = useState(false),
    [searchOpen, setSearchOpen] = useState(false),
    [notificationsOpen, setNotificationsOpen] = useState(false),
    [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  const [selectedCrop, setSelectedCrop] = useState(crops[0]),
    [water, setWater] = useState("Medium"),
    [soil, setSoil] = useState("Loamy"),
    [quantity, setQuantity] = useState("2");
  const changeLanguage = (nextLanguage: Language) => {
    setLanguage(nextLanguage);
    localStorage.setItem("farmwise_language", nextLanguage);
    // Fetch translations from backend if language is not pre-translated
    if (!PRE_TRANSLATED_LANGUAGES.has(nextLanguage) && !dynamicTranslations[nextLanguage]) {
      void api.getInterfaceTranslations(nextLanguage)
        .then((translated) => {
          setDynamicTranslations((current) => ({ ...current, [nextLanguage]: translated }));
        })
        .catch((error) => {
          console.error(`Failed to load translations for ${nextLanguage}:`, error);
        });
    }
  };
  useEffect(() => {
    let cancelled = false;
    const checkBackend = () => {
      void api.health()
        .then(() => { if (!cancelled) setBackendConnected(true); })
        .catch(() => { if (!cancelled) setBackendConnected(false); });
    };
    checkBackend();
    const interval = window.setInterval(checkBackend, 30000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);
  const loadAccount = async (token: string) => {
    const currentUser = await api.me(token);
    const farms = await api.farms(token);
    setUser(currentUser);
    setFarm(farms[0] ?? null);
    setActive(currentUser.role === "buyer" ? "Crop Marketplace" : "Dashboard");
    setAuthenticated(true);
    if (farms[0]) {
      setSoil(farms[0].soil_type);
      setWater(farms[0].water_availability);
      const result = await api.recommendations(farms[0].id, token);
      setApiRecommendations(result.recommendations);
    }
  };
  const saveFarm = async (payload: Omit<Farm, "id">) => {
    const token = getToken();
    if (!token) throw new Error("Your session has expired. Please log in again.");
    const saved = farm ? await api.updateFarm(farm.id, payload, token) : await api.createFarm(payload, token);
    setFarm(saved);
    const result = await api.recommendations(saved.id, token);
    setApiRecommendations(result.recommendations);
    notify("Farm profile saved and recommendations refreshed.");
  };
  const publishHarvest = async (payload: HarvestPayload) => {
    const token = getToken();
    if (!token) throw new Error("Your session has expired. Please log in again.");
    await api.createHarvest(payload, token);
    notify("Crop media shared with buyers.");
    setActive(user?.role === "buyer" ? "Crop Marketplace" : "Buyers & Brokers");
  };
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setAuthLoading(false);
      return;
    }
    loadAccount(token)
      .catch(() => clearToken())
      .finally(() => setAuthLoading(false));
  }, []);
  const rankedCrops = useMemo(
    () =>
      apiRecommendations.length
        ? apiRecommendations.map((item, index) => ({
            name: item.crop,
            score: item.score,
            yield: "Profile-based estimate",
            cost: "Profile-based estimate",
            profit: `INR ${item.expected_profit_per_acre.toLocaleString("en-IN")}`,
            risk: item.risk,
            water: farm?.water_availability ?? "Unknown",
            image: crops[index % crops.length].image,
            reason: item.explanation,
          }))
        : [],
    [apiRecommendations, farm],
  );
  const rankedMarkets = useMemo(
    () =>
      markets
        .map((market) => ({
          ...market,
          net: market.price - market.transport - market.charges,
        }))
        .sort((a, b) => b.net - a.net),
    [],
  );
  const notify = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2800);
  };
  const startDemo = () => {
    setDemo(true);
    setAuthenticated(true);
    setActive("Dashboard");
    notify("Demo mode is for demonstration only. Log in to load your account.");
  };
  const startContact = (intent: { listingId?: number; buyerUserId?: number }) => {
    setPendingContact(intent);
    setActive("Messages");
  };
  const generatePlan = () => {
    setPlannerLoading(true);
    window.setTimeout(() => {
      setPlannerLoading(false);
      setActive("Crop Planner");
      notify("Your crop plan is ready.");
    }, 850);
  };
  const sendEnquiry = () => {
    setEnquirySent(true);
    setEnquiryOpen(false);
    notify("Enquiry sent successfully.");
  };
  if (authLoading)
    return (
      <LanguageContext.Provider value={{ language, setLanguage: changeLanguage, dynamicTranslations }}>
      <div className="loading-screen">
        <span className="spinner" /> Loading your FarmWise workspace...
      </div></LanguageContext.Provider>
    );
  if (!authenticated)
    return (
      <LanguageContext.Provider value={{ language, setLanguage: changeLanguage, dynamicTranslations }}>
      <Landing
        authMode={authMode}
        setAuthMode={setAuthMode}
        onLogin={async (identifier, password) => {
          const result = await api.login(identifier, password);
          saveToken(result.access_token);
          await loadAccount(result.access_token);
          setAuthMode(null);
        }}
        onSignup={async (payload) => {
          const result = await api.register(payload);
          saveToken(result.access_token);
          await loadAccount(result.access_token);
          setAuthMode(null);
        }}
        onGoogle={async (credential, phone) => {
          const result = await api.googleLogin(credential, phone);
          if ("phone_required" in result) return result;
          saveToken(result.access_token);
          await loadAccount(result.access_token);
          setAuthMode(null);
          return result;
        }}
        onDemo={startDemo}
      />
      </LanguageContext.Provider>
    );
  return (
    <LanguageContext.Provider value={{ language, setLanguage: changeLanguage, dynamicTranslations }}>
    <div className="product-shell">
      <aside className={menuOpen ? "app-sidebar open" : "app-sidebar"}>
        <div className="brand">
          <span className="brand-symbol">FW</span>
          <span>
            FarmWise <b>AI</b>
          </span>
        </div>
        <div className="sidebar-profile">
          <button className="profile-avatar profile-avatar-button" aria-label="Open farmer account" onClick={() => setActive("Profile")}>
            {user?.name?.slice(0, 2).toUpperCase()}
          </button>
          <button className="sidebar-profile-link" onClick={() => setActive("Profile")}>
            <strong>{user?.name}</strong>
            <small>
              {user?.role === "buyer" ? "Buyer account" : "Farmer account"}
            </small>
          </button>
          <span className="online-dot" />
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav>
          {navItems.filter((item) => user?.role === "buyer"
            ? ["Crop Marketplace", "Online Marketplaces", "Messages", "Profile"].includes(item.label)
            : item.label !== "Crop Marketplace").map((item) => (
            <button
              key={item.label}
              className={active === item.label ? "app-nav active" : "app-nav"}
              onClick={() => {
                setActive(item.label);
                setMenuOpen(false);
              }}
            >
              <span>{item.icon}</span>
              {marketplacePageTranslations[language]?.[navTranslationKeys[item.label]] ?? translations[language]?.[navTranslationKeys[item.label]] ?? translations.en?.[navTranslationKeys[item.label]] ?? item.label}
              {item.label === "Dashboard" && <i />}
            </button>
          ))}
        </nav>
        <p className="nav-caption lower">ACCOUNT</p>
        <nav>
          <button
            className="app-nav"
            onClick={() => setNotificationsOpen(true)}
          >
            <span>♢</span>Notifications
          </button>
          <button
            className="app-nav"
            onClick={() => setActive("Profile")}
          >
            <span>⚙</span>Account settings
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="season-card">
            <small>CURRENT SEASON</small>
            <strong>{user?.role === "buyer" ? "Buyer account" : farm?.current_season ?? "No farm season yet"}</strong>
            <span>{user?.role === "buyer" ? "Find produce and reply to farmers" : farm ? "Farm profile connected" : "Complete your farm profile"}</span>
            <div>
              <i />
            </div>
          </div>
          <button
            className="help-button"
            onClick={() => notify("FarmWise support is ready to help.")}
          >
            ? <span>Help & guidance</span>
          </button>
          <button
            className="logout-button"
            onClick={() => {
              clearToken();
              setUser(null);
              setFarm(null);
              setAuthenticated(false);
              setApiRecommendations([]);
            }}
          >
            <span>↪</span> Log out
          </button>
        </div>
      </aside>
      <main className="app-main">
        <header className="app-header">
          <button
            className="mobile-menu"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            ☰
          </button>
          <div className="breadcrumbs">
            <span>Workspace</span>
            <b>/</b>
            <strong>{active}</strong>
          </div>
          <div className="header-actions">
            <span className={`sync-status ${backendConnected === false ? "disconnected" : ""}`}>
              <i />
              {backendConnected === null ? "Checking backend…" : backendConnected ? "Backend connected" : "Backend offline"}
            </span>
            <button className="header-icon" onClick={() => setSearchOpen(true)} aria-label="Search FarmWise">
              ⌕
            </button>
            <button
              className="header-icon"
              onClick={() => setNotificationsOpen(true)}
              aria-label="Notifications"
            >
              ♢
            </button>
            <LanguageSelect />
            <button className="header-user header-user-button" onClick={() => setActive("Profile")} aria-label="Open farmer account">
              <div className="profile-avatar small">{user?.name?.slice(0, 2).toUpperCase()}</div>
              <span>{user?.name}⌄</span>
            </button>
          </div>
        </header>
        <div className="page-body">
          {active === "Dashboard" && (
            <Dashboard
              user={user}
              farm={farm}
              go={setActive}
              rankedCrops={rankedCrops}
              rankedMarkets={demo ? rankedMarkets : []}
              demo={demo}
              onEnquiry={() => setEnquiryOpen(true)}
              onDemo={startDemo}
            />
          )}
          {active === "My Farm" && (
            <FarmProfile
              user={user}
              farm={farm}
              soil={soil}
              water={water}
              setSoil={setSoil}
              setWater={setWater}
              notify={notify}
              saveFarm={saveFarm}
            />
          )}
          {active === "Crop Planner" && (
            <CropPlanner
              crops={rankedCrops}
              selectedCrop={selectedCrop}
              setSelectedCrop={setSelectedCrop}
              soil={soil}
              water={water}
              setSoil={setSoil}
              setWater={setWater}
              loading={plannerLoading}
              generatePlan={generatePlan}
            />
          )}
          {active === "Market Intelligence" && (
            <MarketView
              markets={demo ? rankedMarkets : []}
              quantity={quantity}
              setQuantity={setQuantity}
              notify={notify}
            />
          )}
          {active === "Online Marketplaces" && <OnlineMarketplaces />}
          {active === "Buyers & Brokers" && (
            <BuyerView
              token={getToken()}
              demo={demo}
              role="farmer"
              onContact={startContact}
            />
          )}
          {active === "Crop Marketplace" && (
            <BuyerView
              token={getToken()}
              demo={demo}
              role={user?.role === "buyer" ? "buyer" : "farmer"}
              currentUserId={user?.id}
              onContact={startContact}
            />
          )}
          {active === "Messages" && (
            <ConversationsView
              token={getToken()}
              role={user?.role === "buyer" ? "buyer" : "farmer"}
              currentUserId={user?.id}
              pendingContact={pendingContact}
              onContactStarted={() => setPendingContact(null)}
            />
          )}
          {active === "My Harvest" && (
            <HarvestView
              token={getToken()}
              onPublish={publishHarvest}
            />
          )}
          {active === "Crop Guide" && <AgricultureGuide />}
          {active === "Farm Budget & Profit" && <FinancialForecastView token={getToken()} farm={farm} />}
          {active === "Analytics" && <Analytics demo={demo} />}
          {active === "Profile" && <UserProfile user={user} onSaved={(updated) => { setUser(updated); notify("Profile changes saved."); }} />}
        </div>
      </main>
      {toast && (
        <div className="toast">
          <span>✓</span>
          {toast}
        </div>
      )}
      {enquiryOpen && (
        <EnquiryModal
          quantity={quantity}
          setQuantity={setQuantity}
          sent={enquirySent}
          onClose={() => setEnquiryOpen(false)}
          onSend={sendEnquiry}
        />
      )}
      {searchOpen && <SearchPanel token={getToken()} onClose={() => setSearchOpen(false)} onNavigate={(module) => { setActive(user?.role === "buyer" ? "Crop Marketplace" : module); setSearchOpen(false); }} />}
      {notificationsOpen && <NotificationsPanel token={getToken()} onClose={() => setNotificationsOpen(false)} onNavigate={(module) => { setActive(user?.role === "buyer" ? "Crop Marketplace" : module); setNotificationsOpen(false); }} />}
    </div></LanguageContext.Provider>
  );
}

function AgricultureGuide() {
  const [query, setQuery] = useState("");
  const filtered = agricultureGuide.filter((entry) =>
    `${entry.name} ${entry.summary}`.toLowerCase().includes(query.trim().toLowerCase()),
  );
  return (
    <>
      <PageHeading
        eyebrow="INDIA AGRICULTURE"
        title="A guide to crops and growing regions."
        text="Explore major Indian crops and the states where they are grown. Use search to find a crop, state, or region."
      />
      <label className="guide-search">
        SEARCH CROPS AND STATES
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try rice, Karnataka, tea…" />
      </label>
      {(["crop", "state"] as const).map((kind) => (
        <section className="guide-section" key={kind}>
          <div className="marketplace-section-heading">
            <div>
              <span className="eyebrow green">{kind === "crop" ? "CROP BY CROP" : "STATE BY STATE"}</span>
              <h2>{kind === "crop" ? "Who grows what" : "Agriculture across India"}</h2>
            </div>
            <span className="marketplace-count">{filtered.filter((entry) => entry.kind === kind).length}</span>
          </div>
          <div className="guide-grid">
            {filtered.filter((entry) => entry.kind === kind).map((entry) => (
              <article className="guide-card panel" key={entry.name}>
                <h3>{entry.name}</h3>
                <p>{entry.summary}</p>
                <a href={`https://www.google.com/search?q=${encodeURIComponent(`${entry.kind === "crop" ? "agriculture" : "agriculture in"} ${entry.name} India`)}`} target="_blank" rel="noreferrer">
                  Explore on Google ↗
                </a>
              </article>
            ))}
          </div>
        </section>
      ))}
    </>
  );
}

function SearchPanel({
  token,
  onClose,
  onNavigate,
}: {
  token: string | null;
  onClose: () => void;
  onNavigate: (module: Module) => void;
}) {
  const [query, setQuery] = useState("");
  const [buyersResults, setBuyersResults] = useState<BuyerProfile[]>([]);
  const [listingResults, setListingResults] = useState<CropListing[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.buyers(),
      token ? api.cropListings(token) : Promise.resolve([] as CropListing[]),
    ])
      .then(([buyerData, listingData]) => {
        if (cancelled) return;
        setBuyersResults(buyerData);
        setListingResults(listingData);
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Search could not load marketplace data.");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const normalized = query.trim().toLowerCase();
  const guideResults = normalized
    ? agricultureGuide.filter((entry) => `${entry.name} ${entry.summary}`.toLowerCase().includes(normalized)).slice(0, 8)
    : [];
  const buyerMatches = normalized
    ? buyersResults.filter((buyer) => `${buyer.name} ${buyer.business_type} ${buyer.location_name}`.toLowerCase().includes(normalized)).slice(0, 5)
    : [];
  const listingMatches = normalized
    ? listingResults.filter((listing) => `${listing.crop} ${listing.farmer.name} ${listing.farmer.state ?? ""} ${listing.farmer.district ?? ""}`.toLowerCase().includes(normalized)).slice(0, 5)
    : [];
  return (
    <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="search-panel panel" role="dialog" aria-modal="true" aria-label="Search FarmWise">
        <div className="search-panel-header">
          <div>
            <span className="eyebrow green">FARMWISE SEARCH</span>
            <h2>What are you looking for?</h2>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close search">×</button>
        </div>
        <input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search crops, states, farmers, buyers…" />
        {error && <p className="marketplace-error">{error}</p>}
        {!normalized && <p className="search-hint">Search crop and state guides, buyer contacts, and farmer crop listings.</p>}
        {normalized && guideResults.length === 0 && buyerMatches.length === 0 && listingMatches.length === 0 && !error && <p className="search-hint">No results found for “{query}”.</p>}
        {guideResults.length > 0 && <div className="search-result-group"><h3>Crop and state guide</h3>{guideResults.map((entry) => <button className="search-result" key={`${entry.kind}-${entry.name}`} onClick={() => onNavigate("Crop Guide")}><span>{entry.kind === "crop" ? "Crop" : "State"}</span><strong>{entry.name}</strong><small>{entry.summary}</small></button>)}</div>}
        {buyerMatches.length > 0 && <div className="search-result-group"><h3>Buyers</h3>{buyerMatches.map((buyer) => <button className="search-result" key={buyer.id} onClick={() => onNavigate("Buyers & Brokers")}><span>{buyer.business_type}</span><strong>{buyer.name}</strong><small>{buyer.location_name}</small></button>)}</div>}
        {listingMatches.length > 0 && <div className="search-result-group"><h3>Farmer listings</h3>{listingMatches.map((listing) => <button className="search-result" key={listing.id} onClick={() => onNavigate("Buyers & Brokers")}><span>{listing.crop}</span><strong>{listing.farmer.name}</strong><small>{listing.quantity_tonnes} tonnes · {[listing.farmer.district, listing.farmer.state].filter(Boolean).join(", ")}</small></button>)}</div>}
      </section>
    </div>
  );
}

function NotificationsPanel({
  token,
  onClose,
  onNavigate,
}: {
  token: string | null;
  onClose: () => void;
  onNavigate: (module: Module) => void;
}) {
  const [alerts, setAlerts] = useState<Awaited<ReturnType<typeof api.alerts>>>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(Boolean(token));
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    api.alerts(token)
      .then((results) => { if (!cancelled) setAlerts(results); })
      .catch((loadError) => { if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Notifications could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [token]);
  return (
    <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="notification-panel panel" role="dialog" aria-modal="true" aria-label="Notifications">
        <div className="search-panel-header">
          <div><span className="eyebrow green">ACCOUNT UPDATES</span><h2>Notifications</h2></div>
          <button className="modal-close" onClick={onClose} aria-label="Close notifications">×</button>
        </div>
        {!token && <p className="search-hint">Sign in to load account notifications.</p>}
        {loading && <p className="search-hint">Loading notifications…</p>}
        {error && <p className="marketplace-error">{error}</p>}
        {!loading && token && alerts.length === 0 && <p className="search-hint">You’re all caught up. No account alerts right now.</p>}
        {alerts.map((alert, index) => (
          <button className="notification-item" key={`${alert.type}-${index}`} onClick={() => onNavigate("Crop Planner")}>
            <span className={`notification-severity ${alert.severity}`}>●</span>
            <span><strong>{alert.type.replace("-", " ")}</strong><small>{alert.message}</small></span>
            <b>→</b>
          </button>
        ))}
      </section>
    </div>
  );
}

function Landing({
  authMode,
  setAuthMode,
  onLogin,
  onSignup,
  onGoogle,
  onDemo,
}: {
  authMode: "login" | "signup" | null;
  setAuthMode: (mode: "login" | "signup" | null) => void;
  onLogin: (identifier: string, password: string) => Promise<void>;
  onSignup: (payload: { name: string; phone: string; email: string; password: string; confirm_password: string; role: string; state: string; district: string }) => Promise<void>;
  onGoogle: (credential: string, phone?: string) => Promise<Awaited<ReturnType<typeof api.googleLogin>>>;
  onDemo: () => void;
}) {
  const { t } = useLanguage();
  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="brand dark">
          <span className="brand-symbol">FW</span>
          <span>
            FarmWise <b>AI</b>
          </span>
        </div>
        <div className="landing-links">
          <a href="#how">How it works</a>
          <a href="#impact">Impact</a>
          <a href="#trust">Trust & safety</a>
        </div>
        <div className="landing-actions">
          <LanguageSelect />
          <button onClick={() => setAuthMode("login")}>{t("login")}</button>
          <button className="nav-cta" onClick={() => setAuthMode("signup")}>
            {t("signup")} <span>→</span>
          </button>
        </div>
      </nav>
      <section className="landing-hero">
        <div className="hero-left">
          <div className="eyebrow-chip">
            <span>✦</span> Decision intelligence for Indian agriculture
          </div>
          <h1>
            From what to grow
            <br />
            <em>to where to sell.</em>
          </h1>
          <p>
            FarmWise helps farmers make better crop and market decisions with
            clear, explainable intelligence built for the real Indian
            agricultural ecosystem.
          </p>
          <div className="hero-actions">
            <button className="hero-cta" onClick={() => setAuthMode("signup")}>
              Build my farm plan <span>→</span>
            </button>
            <button className="demo-cta" onClick={onDemo}>
              <span>▷</span> Explore live demo
            </button>
          </div>
          <div className="hero-proof">
            <div className="proof-avatars">
              <span>AS</span>
              <span>RK</span>
              <span>MN</span>
            </div>
            <span>
              <strong>Built for everyday decisions</strong>
              <small>What · When · Where · Whom</small>
            </span>
          </div>
        </div>
        <div className="hero-photo">
          <img
            src="https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=1200&q=85"
            alt="Agricultural field at sunrise"
          />
          <div className="photo-overlay" />
          <div className="hero-photo-card">
            <span className="live-dot" /> <strong>Today&apos;s decision</strong>
            <small>Groundnut · 92% suitable</small>
            <b>+ INR 18,500 / acre</b>
          </div>
          <div className="photo-location">Karnataka · Kharif season</div>
        </div>
      </section>
      <section className="landing-strip">
        <span>One platform for the complete crop-to-market journey</span>
        <div>
          <b>01</b> Grow smarter <i /> <b>02</b> Sell with clarity <i />{" "}
          <b>03</b> Build resilience
        </div>
      </section>
      <section className="landing-how" id="how">
        <div>
          <p className="eyebrow green">THE FARM-TO-MARKET LOOP</p>
          <h2>
            Every decision is
            <br />
            <em>connected.</em>
          </h2>
        </div>
        <div className="how-grid">
          <InfoTile
            num="01"
            title="Know your farm"
            text="Translate soil, water, season and budget into a practical starting point."
          />
          <InfoTile
            num="02"
            title="See the trade-offs"
            text="Compare crops and markets on suitability, cost, risk and what you take home."
          />
          <InfoTile
            num="03"
            title="Act with confidence"
            text="Connect with real market participants already part of your local ecosystem."
          />
        </div>
      </section>
      <footer className="landing-footer">
        <div className="brand dark">
          <span className="brand-symbol">FW</span>
          <span>
            FarmWise <b>AI</b>
          </span>
        </div>
        <span>Better decisions. Stronger harvests.</span>
        <button onClick={() => setAuthMode("login")}>Open workspace →</button>
      </footer>
      {authMode && (
        <AuthModal
          mode={authMode}
          setMode={setAuthMode}
          onClose={() => setAuthMode(null)}
          onLogin={onLogin}
          onSignup={onSignup}
          onGoogle={onGoogle}
        />
      )}
    </div>
  );
}
function AuthModal({
  mode,
  setMode,
  onClose,
  onLogin,
  onSignup,
  onGoogle,
}: {
  mode: "login" | "signup";
  setMode: (mode: "login" | "signup" | null) => void;
  onClose: () => void;
  onLogin: (identifier: string, password: string) => Promise<void>;
  onSignup: (payload: { name: string; phone: string; email: string; password: string; confirm_password: string; role: string; state: string; district: string }) => Promise<void>;
  onGoogle: (credential: string, phone?: string) => Promise<Awaited<ReturnType<typeof api.googleLogin>>>;
}) {
  const { t } = useLanguage();
  const [name, setName] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [state, setState] = useState("");
  const [district, setDistrict] = useState("");
  const [role, setRole] = useState("farmer");
  const [error, setError] = useState("");
  const [googleCredential, setGoogleCredential] = useState("");
  const [googlePhone, setGooglePhone] = useState("");
  const [googlePhoneRequired, setGooglePhoneRequired] = useState(false);
  const [googleBusy, setGoogleBusy] = useState(false);
  const googleButtonRef = useRef<HTMLDivElement>(null);
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const onGoogleRef = useRef(onGoogle);
  onGoogleRef.current = onGoogle;

  useEffect(() => {
    if (!googleClientId || !googleButtonRef.current) return;
    let cancelled = false;
    const handleCredential: GoogleCredentialHandler = (response) => {
      setError("");
      setGoogleBusy(true);
      setGoogleCredential(response.credential);
      void onGoogleRef.current(response.credential)
        .then((result) => {
          if ("phone_required" in result) setGooglePhoneRequired(true);
        })
        .catch((googleError) => setError(googleError instanceof Error ? googleError.message : "Google sign-in failed."))
        .finally(() => setGoogleBusy(false));
    };
    activeGoogleCredentialHandler = handleCredential;
    const initializeGoogle = () => {
      if (cancelled || !window.google || !googleButtonRef.current) return;
      if (initializedGoogleClientId !== googleClientId) {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: (response) => activeGoogleCredentialHandler?.(response),
        });
        initializedGoogleClientId = googleClientId;
      }
      googleButtonRef.current.replaceChildren();
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        theme: "outline",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: Math.min(360, googleButtonRef.current.clientWidth || 320),
      });
    };
    const source = "https://accounts.google.com/gsi/client";
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${source}"]`);
    if (window.google) {
      initializeGoogle();
    } else if (existing) {
      existing.addEventListener("load", initializeGoogle);
    } else {
      const script = document.createElement("script");
      script.src = source;
      script.async = true;
      script.defer = true;
      script.addEventListener("load", initializeGoogle, { once: true });
      script.addEventListener("error", () => setError("Google sign-in could not load. Check your internet connection."), { once: true });
      document.head.appendChild(script);
    }
    return () => {
      cancelled = true;
      if (activeGoogleCredentialHandler === handleCredential) {
        activeGoogleCredentialHandler = null;
      }
      existing?.removeEventListener("load", initializeGoogle);
    };
  }, [googleClientId]);

  const finishGoogleSignup = async () => {
    setError("");
    setGoogleBusy(true);
    try {
      const result = await onGoogle(googleCredential, googlePhone);
      if ("phone_required" in result) setGooglePhoneRequired(true);
    } catch (googleError) {
      setError(googleError instanceof Error ? googleError.message : "Google sign-in failed.");
    } finally {
      setGoogleBusy(false);
    }
  };

  const submit = async () => {
    try {
      setError("");
      if (mode === "login") await onLogin(identifier, password);
      else await onSignup({ name, phone, email, password, confirm_password: confirmation, role, state, district });
    } catch (submitError) { setError(submitError instanceof Error ? submitError.message : "Unable to continue"); }
  };
  return (
    <div className="modal-backdrop">
      <div className="auth-modal">
        <button className="modal-close" onClick={onClose}>
          ×
        </button>
        <span className="modal-kicker">FARMWISE AI</span>
        <h2>{mode === "login" ? t("login") : "Start with your farm."}</h2>
        <p>
          {mode === "login"
            ? "Continue your crop-to-market plan."
            : "Create a profile built around your next decision."}
        </p>
        {mode === "signup" && (
          <label>
            FULL NAME
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Your full name" />
          </label>
        )}
        <label>
          {mode === "login" ? "MOBILE NUMBER OR EMAIL" : "MOBILE NUMBER"}
          <input value={mode === "login" ? identifier : phone} onChange={(event) => mode === "login" ? setIdentifier(event.target.value) : setPhone(event.target.value)} placeholder={mode === "login" ? "+91 98765 43210 or email" : "+91 98765 43210"} />
        </label>
        {mode === "signup" && <label>EMAIL<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="you@example.com" /></label>}
        <label>
          PASSWORD
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="••••••••" />
        </label>
        {mode === "signup" && (
          <>
          <label>CONFIRM PASSWORD<input value={confirmation} onChange={(event) => setConfirmation(event.target.value)} type="password" placeholder="Repeat password" /></label>
          <div className="two-fields"><label>STATE<input value={state} onChange={(event) => setState(event.target.value)} placeholder="Karnataka" /></label><label>DISTRICT<input value={district} onChange={(event) => setDistrict(event.target.value)} placeholder="Mandya" /></label></div>
          <label>
            ACCOUNT TYPE
            <select value={role} onChange={(event) => setRole(event.target.value)}>
              <option value="farmer">Farmer</option>
              <option value="buyer">Buyer / broker</option>
            </select>
          </label>
          </>
        )}
        {error && <div className="auth-error">{error}</div>}
        <button className="auth-submit" onClick={submit}>
          {mode === "login" ? "Log in to workspace" : "Create my account"}{" "}
          <span>→</span>
        </button>
        {googlePhoneRequired && (
          <div className="google-phone-step">
            <p>Google verified {googleCredential ? "your email" : "your account"}. Add a mobile number to finish your farmer profile.</p>
            <label>MOBILE NUMBER<input value={googlePhone} onChange={(event) => setGooglePhone(event.target.value)} placeholder="+91 98765 43210" /></label>
            <button className="auth-submit" disabled={googleBusy || googlePhone.trim().length < 10} onClick={() => void finishGoogleSignup()}>
              {googleBusy ? "Creating account…" : "Finish Google sign-in"} <span>→</span>
            </button>
          </div>
        )}
        {googleClientId
          ? <div className="google-signin-control" ref={googleButtonRef} />
          : <button className="google-button" disabled title="Google sign-in needs a configured OAuth client ID">G <span>Google sign-in needs setup</span></button>}
        {googleBusy && !googlePhoneRequired && <small className="google-status">Verifying your Google account…</small>}
        <div className="auth-switch">
          {mode === "login" ? "New to FarmWise?" : "Already have an account?"}{" "}
          <button
            onClick={() => setMode(mode === "login" ? "signup" : "login")}
          >
            {mode === "login" ? "Create account" : "Log in"}
          </button>
        </div>
        <small className="auth-note">
          By continuing, you agree to use recommendations as estimates and
          decision support.
        </small>
      </div>
    </div>
  );
}

function LanguageSelect() {
  const { language, setLanguage } = useLanguage();
  return <select className="lang-button" value={language} onChange={(event) => setLanguage(event.target.value as Language)} aria-label="Language" title="Choose app language">{supportedLanguages.map((option) => <option value={option.code} key={option.code}>{option.nativeName} · {option.englishName}</option>)}</select>;
}

function Dashboard({
  user,
  farm,
  go,
  rankedCrops,
  rankedMarkets,
  demo,
  onEnquiry,
  onDemo,
}: {
  user: User | null;
  farm: Farm | null;
  go: (module: Module) => void;
  rankedCrops: Crop[];
  rankedMarkets: (Market & { net: number })[];
  demo: boolean;
  onEnquiry: () => void;
  onDemo: () => void;
}) {
  const { t } = useLanguage();
  return (
    <>
      <div className="page-intro">
        <div>
          <p className="eyebrow green">YOUR FARMWISE WORKSPACE</p>
          <h1>
            {t("greeting")}, {user?.name ?? "there"} <span>✦</span>
          </h1>
          <p>
            {farm ? `${farm.land_size_acres} acres · ${farm.soil_type} soil · ${farm.water_availability} water` : "Complete your farm profile to unlock personal recommendations."}
          </p>
        </div>
        <div className="intro-actions">
          <span className="demo-badge">● DEMO DATA</span>
          <button className="primary-button" onClick={() => go("My Farm")}>
            + Update farm inputs
          </button>
        </div>
      </div>
      <section className="dashboard-hero">
        <div>
          <span className="hero-label">YOUR NEXT BEST DECISION</span>
          <h2>
            Net profit before
            <br />
            <em>you plant.</em>
          </h2>
          <p>
            FarmWise connects your farm profile, timing, markets and buyers into
            one clear plan.
          </p>
          <button className="cream-button" onClick={() => go("Crop Planner")}>
            Open crop planner <span>→</span>
          </button>
        </div>
        <div className="dashboard-hero-art">
          <div className="sun-art" />
          <div className="crop-row one" />
          <div className="crop-row two" />
          <div className="hero-seal">
            <strong>₹</strong>
            <span>
              Make every
              <br />
              acre count
            </span>
          </div>
        </div>
      </section>
      <div className="stat-row">
        <Stat
          label="Expected net realization"
          value={farm ? `INR ${Math.round((farm.budget || 0) * 1.08).toLocaleString("en-IN")}` : "—"}
          note="profile estimate"
          change={farm ? "Estimated" : "Add farm"}
        />
        <Stat
          label="Top crop fit"
          value={rankedCrops[0]?.name ?? "—"}
          note={rankedCrops[0] ? `${rankedCrops[0].score}% suitability` : "No recommendation yet"}
          change={rankedCrops[0] ? "Top pick" : "Add farm"}
        />
        <Stat
          label="Best market"
          value={rankedMarkets[0]?.name ?? "—"}
          note={rankedMarkets[0] ? `INR ${rankedMarkets[0].net.toFixed(2)} / kg net` : "No market data"}
          change={rankedMarkets[0] ? "Recommended" : "Unavailable"}
        />
        <Stat
          label="Water efficiency"
          value={farm ? "Profile-based" : "—"}
          note="resource estimate"
          change={farm ? "On track" : "Add farm"}
        />
      </div>
      <div className="section-title">
        <div>
          <span className="section-index">01</span>
          <div>
            <p className="eyebrow">THE FARM-TO-MARKET PLAN</p>
            <h2>Your decision path</h2>
          </div>
        </div>
        <button className="link-button" onClick={onDemo}>
          Reset demo ↻
        </button>
      </div>
      <div className="journey-card">
        <Journey
          label="Grow"
          value={rankedCrops[0]?.name ?? "No crop yet"}
          status="Recommended"
          icon="✦"
          active
        />
        <Journey
          label="Sow"
          value="18–25 Jun"
          status="Optimal window"
          icon="◷"
        />
        <Journey
          label="Harvest"
          value={demo ? "2.8 tonnes" : "No harvest yet"}
          status={demo ? "In 95 days" : "Add harvest"}
          icon="◒"
        />
        <Journey
          label="Sell"
          value={rankedMarkets[0]?.name ?? "No market yet"}
          status={rankedMarkets[0] ? `INR ${rankedMarkets[0].net.toFixed(2)} / kg` : "Add harvest"}
          icon="↗"
        />
        <Journey
          label="Connect"
          value={demo ? "2 buyers" : "No matches yet"}
          status={demo ? "94% top match" : "Add harvest"}
          icon="♧"
        />
      </div>
      <div className="section-title spaced">
        <div>
          <span className="section-index">02</span>
          <div>
            <p className="eyebrow">{t("cropPlan")}</p>
            <h2>{t("cropPlan")}</h2>
          </div>
        </div>
        <button className="link-button" onClick={() => go("Crop Planner")}>
          See full analysis →
        </button>
      </div>
      <div className="dashboard-grid">
        <div className="panel recommendation-panel">
          <div className="panel-head">
            <div>
              <h3>Best fit for your Kharif season</h3>
              <p>
                Weighted against your soil, water, budget and nearby demand.
              </p>
            </div>
            <span className="data-tag">ESTIMATED</span>
          </div>
          <div className="mini-crops">
            {rankedCrops.map((crop, i) => (
              <MiniCrop
                key={crop.name}
                crop={crop}
                index={i}
                onClick={() => go("Crop Planner")}
              />
            ))}
          </div>
          <div className="why-strip">
            <span>✦</span>
            <div>
              <strong>Why {rankedCrops[0]?.name ?? "this crop"}?</strong>
              <p>{rankedCrops[0]?.reason ?? "Create a farm profile to generate an explainable crop recommendation."}</p>
            </div>
            <button onClick={() => go("Crop Planner")}>Why? →</button>
          </div>
        </div>
        <div className="panel weather-panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">TODAY IN {user?.district?.toUpperCase() ?? "YOUR AREA"}</p>
              <h3>Monsoon watch</h3>
            </div>
            <span className="weather-symbol">◒</span>
          </div>
          <div className="weather-main">
            <strong>{demo ? "28°" : "—"}</strong>
            <span>
              {demo ? "Partly cloudy" : "Weather unavailable"}
              <br />
              <b>{demo ? "42% rain probability" : "Connect weather provider"}</b>
            </span>
          </div>
          <div className="weather-days">
            <span>
              WED <b>{demo ? "29°" : "—"}</b>
            </span>
            <span>
              THU <b>{demo ? "27°" : "—"}</b>
            </span>
            <span>
              FRI <b>{demo ? "30°" : "—"}</b>
            </span>
          </div>
          <div className="alert-note">
            <span>!</span> {demo ? "Rain may affect land preparation this week." : "Alerts will appear after farm data is available."}
          </div>
        </div>
      </div>
      <div className="section-title spaced">
        <div>
          <span className="section-index">03</span>
          <div>
            <p className="eyebrow">{t("marketPlan")}</p>
            <h2>{t("markets")}</h2>
          </div>
        </div>
        <button
          className="link-button"
          onClick={() => go("Market Intelligence")}
        >
          View all markets →
        </button>
      </div>
      <div className="bottom-grid">
        <div className="panel market-panel">
          <div className="market-map">
            <div className="map-grid" />
            <span className="map-label farmer">YOU</span>
            {rankedMarkets.map((market, i) => (
              <button
                key={market.name}
                className={`map-pin pin-${i + 1}`}
                onClick={() => go("Market Intelligence")}
              >
                ⌖<small>{market.name.split(" ")[0]}</small>
              </button>
            ))}
            <div className="map-legend">
              <span>
                <i className="you-dot" /> Your farm
              </span>
              <span>
                <i className="market-dot" /> Markets
              </span>
            </div>
          </div>
          <div className="market-summary">
            <div>
              <span className="eyebrow">RECOMMENDED MARKET</span>
              <h3>{rankedMarkets[0]?.name ?? "No market selected"}</h3>
              <p>{rankedMarkets[0] ? "Highest net realization after transport and charges." : "Add a harvest to compare selling options."}</p>
            </div>
            <strong>
              {rankedMarkets[0] ? `INR ${rankedMarkets[0].net.toFixed(2)}` : "—"}<small>/ kg net</small>
            </strong>
          </div>
        </div>
        <div className="panel buyers-preview">
          <div className="panel-head">
            <div>
              <p className="eyebrow">WHOM TO CONTACT</p>
              <h3>Buyer matches</h3>
            </div>
            <span className="match-pill">{demo ? "3 found" : "No harvest match"}</span>
          </div>
          {(demo ? buyers.slice(0, 2) : []).map((buyer) => (
            <BuyerRow key={buyer.name} buyer={buyer} onEnquiry={onEnquiry} />
          ))}
          {!demo && <p className="empty-state">Record a harvest to see buyer matches for your crop.</p>}
          <button
            className="full-width-link"
            onClick={() => go("Buyers & Brokers")}
          >
            Explore buyer network →
          </button>
        </div>
      </div>
      <div className="impact-callout">
        <div>
          <p className="eyebrow light">EXPECTED IMPACT</p>
          <h2>
            Small choices.
            <br />
            <em>Compounding gains.</em>
          </h2>
          <p>
            Estimates compared with a typical local crop-to-market decision.
          </p>
        </div>
        <ImpactStat value={demo ? "+12.4%" : "—"} label="Net realization" />
        <ImpactStat value={demo ? "−18%" : "—"} label="Transport cost" />
        <ImpactStat value={demo ? "74%" : "—"} label="Water efficiency" />
        <button className="cream-button" onClick={() => go("Analytics")}>
          Open analytics <span>→</span>
        </button>
      </div>
      <footer className="app-footer">
        <span>FarmWise AI</span>
        <span>Decision support for better farm outcomes</span>
        <span>All values are estimates · Demo data</span>
      </footer>
    </>
  );
}

function CropPlanner({
  crops,
  selectedCrop,
  setSelectedCrop,
  soil,
  water,
  setSoil,
  setWater,
  loading,
  generatePlan,
}: {
  crops: Crop[];
  selectedCrop: Crop;
  setSelectedCrop: (crop: Crop) => void;
  soil: string;
  water: string;
  setSoil: (value: string) => void;
  setWater: (value: string) => void;
  loading: boolean;
  generatePlan: () => void;
}) {
  return (
    <>
      <PageHeading
        eyebrow="CROP PLANNER"
        title="What should I grow?"
        text="Start with the conditions you can control. FarmWise will explain the trade-offs behind every recommendation."
      />
      <div className="planner-layout">
        <aside className="planner-form panel">
          <div className="panel-head">
            <div>
              <h3>Your farm inputs</h3>
              <p>Adjust any input to refresh your shortlist.</p>
            </div>
            <span className="step-pill">1 of 1</span>
          </div>
          <label>
            LOCATION
            <div className="input-with-icon">
              ⌖<input value="Guntur, Andhra Pradesh" readOnly />
            </div>
          </label>
          <div className="two-fields">
            <label>
              LAND SIZE
              <input value="2 acres" readOnly />
            </label>
            <label>
              SEASON
              <select>
                <option>Kharif 2025</option>
                <option>Rabi 2025</option>
              </select>
            </label>
          </div>
          <label>
            SOIL TYPE
            <select value={soil} onChange={(e) => setSoil(e.target.value)}>
              <option>Loamy</option>
              <option>Red loam</option>
              <option>Black soil</option>
              <option>Alluvial soil</option>
            </select>
          </label>
          <label>
            WATER AVAILABILITY
            <select value={water} onChange={(e) => setWater(e.target.value)}>
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
            </select>
          </label>
          <label>
            AVAILABLE BUDGET
            <input value="INR 50,000" readOnly />
          </label>
          <button className="primary-button full" onClick={generatePlan}>
            {loading ? (
              <>
                <span className="spinner" /> Analyzing your farm...
              </>
            ) : (
              <>
                Generate crop recommendations <span>→</span>
              </>
            )}
          </button>
          <span className="form-footnote">
            ✦ Deterministic scoring · Explainable estimates
          </span>
        </aside>
        <div className="planner-results">
          <div className="results-toolbar">
            <div>
              <span className="eyebrow green">YOUR TOP OPTIONS</span>
              <h2>Built around your farm</h2>
            </div>
            <span className="data-tag">SIMULATED MARKET DATA</span>
          </div>
          {crops.map((crop, i) => (
            <CropRecommendation
              key={crop.name}
              crop={crop}
              rank={i + 1}
              selected={selectedCrop.name === crop.name}
              onSelect={() => setSelectedCrop(crop)}
            />
          ))}
          <div className="planner-insight">
            <span>✦</span>
            <div>
              <strong>How FarmWise scores crops</strong>
              <p>
                25% soil · 20% climate · 15% water · 15% season · 15% profit ·
                10% market stability
              </p>
            </div>
            <button>View method →</button>
          </div>
        </div>
      </div>
      <section className="explain-section">
        <div>
          <p className="eyebrow green">EXPLAINABLE AI</p>
          <h2>
            Why FarmWise recommends
            <br />
            <em>{selectedCrop.name}.</em>
          </h2>
          <p>{selectedCrop.reason}</p>
        </div>
        <div className="score-breakdown">
          <ScoreBar label="Soil compatibility" value={95} />
          <ScoreBar label="Water fit" value={88} />
          <ScoreBar label="Season timing" value={92} />
          <ScoreBar label="Profit potential" value={85} />
        </div>
        <div className="explain-list">
          <span>✓ Fits your loamy soil profile</span>
          <span>✓ Works with medium water availability</span>
          <span>✓ Active demand in nearby markets</span>
          <span>✓ Production cost fits your budget</span>
        </div>
      </section>
    </>
  );
}

function MarketView({
  markets: rankedMarkets,
  quantity,
  setQuantity,
  notify,
}: {
  markets: (Market & { net: number })[];
  quantity: string;
  setQuantity: (value: string) => void;
  notify: (message: string) => void;
}) {
  const [selected, setSelected] = useState(rankedMarkets[0] ?? null);
  return (
    <>
      <PageHeading
        eyebrow="MARKET INTELLIGENCE"
        title="Where should you sell?"
        text="The highest quote is not always the highest take-home value. Compare the journey, costs and demand before you choose."
      />
      <div className="market-workspace">
        <div className="market-controls panel">
          <div className="panel-head">
            <div>
              <h3>Harvest details</h3>
              <p>Use your expected harvest to compare selling options.</p>
            </div>
            <span className="data-tag">DEMO DATA</span>
          </div>
          <label>
            CROP
            <select>
              <option>Groundnut</option>
              <option>Tomato</option>
              <option>Chilli</option>
            </select>
          </label>
          <div className="two-fields">
            <label>
              QUANTITY (TONNES)
              <input
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </label>
            <label>
              GRADE
              <select>
                <option>Grade A</option>
                <option>Grade B</option>
              </select>
            </label>
          </div>
          <label>
            EXPECTED HARVEST DATE
            <input value="18 September 2025" readOnly />
          </label>
          <button
            className="primary-button full"
            onClick={() => notify("Market options refreshed for your harvest.")}
          >
            Find best selling options →
          </button>
        </div>
        <div className="market-visual panel">
          <div className="market-map tall">
            <div className="map-grid" />
            <span className="map-label farmer">YOUR FARM</span>
            {rankedMarkets.map((market, i) => (
              <button
                key={market.name}
                className={`map-pin pin-${i + 1} ${selected?.name === market.name ? "selected" : ""}`}
                onClick={() => setSelected(market)}
              >
                ⌖<small>{market.name.split(" ")[0]}</small>
              </button>
            ))}
            <div className="route-line" />
          </div>
          <div className="map-footer">
            <span>
              <i className="you-dot" /> Your location
            </span>
            <span>
              <i className="market-dot" /> APMC / mandi
            </span>
            <button>Open map ↗</button>
          </div>
        </div>
      </div>
      <div className="market-heading">
        <div>
          <p className="eyebrow green">RANKED BY NET REALIZATION</p>
          <h2>Nearby markets</h2>
        </div>
        <span>Last updated · 16 Sep 2025</span>
      </div>
      <div className="market-cards">
        {rankedMarkets.map((market, i) => (
          <button
            className={
              selected?.name === market.name
                ? "market-card chosen"
                : "market-card"
            }
            key={market.name}
            onClick={() => setSelected(market)}
          >
            <div className="market-rank">0{i + 1}</div>
            <div className="market-card-main">
              <span className="eyebrow">{market.type}</span>
              <h3>{market.name}</h3>
              <p>
                {market.distance} · {market.demand} buyer demand
              </p>
              <div className="market-card-tags">
                <span>Arrivals {market.arrivals}</span>
                <span>Est. {market.charges.toFixed(2)} charges</span>
              </div>
            </div>
            <div className="market-card-values">
              <small>QUOTE</small>
              <strong>
                INR {market.price.toFixed(2)}
                <i>/kg</i>
              </strong>
              <small>NET REALIZATION</small>
              <b>
                INR {market.net.toFixed(2)}
                <i>/kg</i>
              </b>
            </div>
            {i === 0 && <span className="recommended-label">Recommended</span>}
          </button>
        ))}
      </div>
      <div className="tradeoff-banner">
        <span>↗</span>
        <div>
          <strong>Smart trade-off</strong>
          <p>
            {selected ? <>{selected.name} leaves you with{" "}<b>INR {selected.net.toFixed(2)} / kg</b> after estimated transport and market charges. FarmWise ranks what you take home, not just the quote.</> : "Add a harvest to compare markets using your crop, quantity and grade."}
          </p>
        </div>
      </div>
    </>
  );
}

function OnlineMarketplaces() {
  const { t } = useLanguage();
  const marketplaces = [
    {
      name: "Farmizen",
      category: t("farmizenCategory"),
      description: t("farmizenDescription"),
      url: "https://www.farmizen.com/farmers-markets",
      label: t("visitFarmizen"),
    },
    {
      name: "CommodityOnline",
      category: t("commodityCategory"),
      description: t("commodityDescription"),
      url: "https://www.commodityonline.com/",
      label: t("visitCommodity"),
    },
  ];

  return (
    <>
      <PageHeading
        eyebrow={t("externalEyebrow")}
        title={t("externalTitle")}
        text={t("externalText")}
      />
      <div className="external-marketplace-grid">
        {marketplaces.map((marketplace) => (
          <article className="external-marketplace-card panel" key={marketplace.name}>
            <span className="eyebrow green">{marketplace.category}</span>
            <h2>{marketplace.name}</h2>
            <p>{marketplace.description}</p>
            <a href={marketplace.url} target="_blank" rel="noopener noreferrer">
              {marketplace.label} <span aria-hidden="true">↗</span>
            </a>
            <small>{t("externalDisclaimer")}</small>
          </article>
        ))}
      </div>
    </>
  );
}

function BuyerView({
  token,
  demo,
  role,
  currentUserId,
  onContact,
}: {
  token: string | null;
  demo: boolean;
  role: "farmer" | "buyer";
  currentUserId?: number;
  onContact: (intent: { listingId?: number; buyerUserId?: number }) => void;
}) {
  const [directory, setDirectory] = useState<BuyerProfile[]>([]);
  const [listings, setListings] = useState<CropListing[]>([]);
  const [loading, setLoading] = useState(Boolean(token) && !demo);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || demo) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    Promise.all([api.buyers(), api.cropListings(token)])
      .then(([buyerResults, listingResults]) => {
        if (cancelled) return;
        setDirectory(buyerResults);
        setListings(listingResults);
        setError("");
      })
      .catch((loadError) => {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Could not load the marketplace.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token, demo]);

  const demoDirectory: BuyerProfile[] = buyers.map((buyer, index) => ({
    id: index + 1,
    name: buyer.name,
    business_type: buyer.type,
    location_name: buyer.location,
    verification_status: "verified",
    verification_fields: buyer.verification,
    rating: 4.4,
    phone: `+91900000000${index}`,
    email: `buyer${index + 1}@demo.farmwise`,
  }));
  const visibleBuyers = demo ? demoDirectory : directory.filter((buyer) => buyer.account_id);
  const visibleListings = listings.filter((listing) =>
    role === "farmer" || listing.farmer.account_id !== currentUserId,
  );

  return (
    <>
      <PageHeading
        eyebrow={role === "buyer" ? "BUYER WORKSPACE" : "FARMER MARKETPLACE"}
        title={role === "buyer" ? "Find fresh crops from farmers." : "Connect with registered buyers."}
        text={role === "buyer"
          ? "Browse crop photos and videos, then message a farmer. Their phone, email, and location are shared only with their permission."
          : "Browse local crops and message registered buyers. Contact details and precise location stay private unless you choose to share them in a conversation."}
      />
      {error && <div className="marketplace-error">{error}</div>}
      <div className={`marketplace-columns ${role === "buyer" ? "buyer-marketplace-only" : ""}`}>
        <section className="marketplace-column">
          <div className="marketplace-section-heading">
            <div>
              <span className="eyebrow green">FARMER HARVESTS</span>
              <h2>Fresh from the farm</h2>
            </div>
            <span className="marketplace-count">{demo ? "Demo" : visibleListings.length}</span>
          </div>
          {loading && <p className="empty-state">Loading farmer listings…</p>}
          {!loading && !visibleListings.length && (
            <div className="marketplace-empty panel">
              <strong>{role === "buyer" ? "No crops are listed yet" : "No crop photos shared yet"}</strong>
              <p>{role === "buyer" ? "Farmers' photo and video listings will appear here." : "Add a harvest photo or video in My Harvest to create a crop listing."}</p>
            </div>
          )}
          {visibleListings.map((listing) => (
            <article className="crop-listing-card panel" key={listing.id}>
              {listing.media_type.startsWith("video/")
                ? <video src={listing.photo_data_url} controls playsInline preload="metadata" aria-label={`${listing.crop} video from ${listing.farmer.name}`} />
                : <img src={listing.photo_data_url} alt={`${listing.crop} harvest from ${listing.farmer.name}`} />}
              <div className="crop-listing-body">
                <div className="crop-listing-title">
                  <h3>{listing.crop}</h3>
                  <span>{listing.grade}</span>
                </div>
                <p className="crop-listing-farmer">By {listing.farmer.name}</p>
                <div className="crop-listing-facts">
                  <span><small>QUANTITY</small><b>{listing.quantity_tonnes} tonnes</b></span>
                  <span><small>HARVEST DATE</small><b>{listing.harvest_date}</b></span>
                  <span><small>LOCATION</small><b>{[listing.farmer.district, listing.farmer.state].filter(Boolean).join(", ") || listing.farmer.location_name || "Location not provided"}</b></span>
                </div>
                {listing.notes && <p className="crop-listing-notes">{listing.notes}</p>}
                {role === "buyer" && <button className="primary-button" onClick={() => onContact({ listingId: listing.id })}>Message farmer</button>}
              </div>
            </article>
          ))}
        </section>
        {role === "farmer" && <section className="marketplace-column">
          <div className="marketplace-section-heading">
            <div>
              <span className="eyebrow green">BUYER DIRECTORY</span>
              <h2>Find a buyer</h2>
            </div>
            <span className="marketplace-count">{visibleBuyers.length}</span>
          </div>
          {!visibleBuyers.length && !loading && (
            <div className="marketplace-empty panel">
              <strong>No buyers listed yet</strong>
              <p>Buyer profiles will appear here when the backend buyer directory has been seeded.</p>
            </div>
          )}
          {visibleBuyers.map((buyer) => (
            <article className="directory-buyer-card panel" key={buyer.id}>
              <div className="buyer-directory-avatar">{buyer.name.slice(0, 2).toUpperCase()}</div>
              <div className="buyer-directory-info">
                <div className="buyer-name-line">
                  <h3>{buyer.name}</h3>
                  {buyer.verification_status === "verified" && <span className="verified-pill">✓ Verified</span>}
                </div>
                <p>{buyer.business_type} · {buyer.location_name}</p>
                <div className="buyer-directory-details">
                  <span>★ {buyer.rating.toFixed(1)} rating</span>
                  <span>Verified: {buyer.verification_fields || "Details pending"}</span>
                  {buyer.account_id
                    ? <button className="primary-button" onClick={() => onContact({ buyerUserId: buyer.account_id! })}>Message buyer</button>
                    : <span>Contact this buyer through the details they provide after signing in.</span>}
                </div>
              </div>
            </article>
          ))}
        </section>}
      </div>
    </>
  );
}

function ConversationsView({
  token,
  role,
  currentUserId,
  pendingContact,
  onContactStarted,
}: {
  token: string | null;
  role: "farmer" | "buyer";
  currentUserId?: number;
  pendingContact: { listingId?: number; buyerUserId?: number } | null;
  onContactStarted: () => void;
}) {
  const contactStartedRef = useRef(onContactStarted);
  contactStartedRef.current = onContactStarted;
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [listings, setListings] = useState<CropListing[]>([]);
  const [buyerAccounts, setBuyerAccounts] = useState<BuyerProfile[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [listingId, setListingId] = useState("");
  const [buyerId, setBuyerId] = useState("");
  const [message, setMessage] = useState("");
  const [shareContact, setShareContact] = useState(false);
  const [shareLocation, setShareLocation] = useState(false);
  const [loading, setLoading] = useState(Boolean(token));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    Promise.all([api.conversations(token), api.cropListings(token), api.buyers()])
      .then(([threads, cropListings, buyers]) => {
        if (cancelled) return;
        setConversations(threads);
        setListings(cropListings);
        setBuyerAccounts(buyers.filter((buyer) => buyer.account_id));
        const ownListings = role === "farmer"
          ? cropListings.filter((listing) => listing.farmer.account_id === currentUserId)
          : cropListings;
        if (pendingContact?.listingId) setListingId(String(pendingContact.listingId));
        else if (ownListings.length) setListingId(String(ownListings[0].id));
        if (pendingContact?.buyerUserId) setBuyerId(String(pendingContact.buyerUserId));
        if (pendingContact) contactStartedRef.current();
        setError("");
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Could not load conversations.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [token, role, currentUserId]);

  const selected = conversations.find((conversation) => conversation.id === selectedId) ?? null;
  const ownListings = role === "farmer"
    ? listings.filter((listing) => listing.farmer.account_id === currentUserId)
    : listings.filter((listing) => listing.farmer.account_id !== currentUserId);
  const otherParty = selected?.other_party;
  const directoryBuyerAccounts = buyerAccounts.filter((buyer) => buyer.account_id);

  useEffect(() => {
    if (!selected) return;
    setShareContact(selected.my_contact_shared);
    setShareLocation(selected.my_location_shared);
    setMessage("");
  }, [selectedId]);

  const sendMessage = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !message.trim()) return;
    setBusy(true);
    setError("");
    try {
      const updated = selected
        ? await api.replyConversation(selected.id, {
            message: message.trim(),
            share_my_contact: shareContact,
            share_my_location: shareLocation,
          }, token)
        : await api.startConversation({
            listing_id: Number(listingId),
            ...(role === "farmer" ? { buyer_user_id: Number(buyerId) } : {}),
            message: message.trim(),
            share_my_contact: shareContact,
            share_my_location: shareLocation,
          }, token);
      setConversations((current) => [updated, ...current.filter((conversation) => conversation.id !== updated.id)]);
      setSelectedId(updated.id);
      setMessage("");
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Could not send your message.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeading
        eyebrow="PRIVATE CONVERSATIONS"
        title="Talk before you trade."
        text="Messages stay in your account. Phone, email, and location are shared only when you explicitly choose to share them."
      />
      {error && <div className="marketplace-error" role="alert">{error}</div>}
      {!token ? <div className="panel empty-state">Log in with a farmer or buyer account to send private messages.</div> : (
        <div className="conversation-layout">
          <section className="conversation-list panel">
            <div className="marketplace-section-heading">
              <div><span className="eyebrow green">INBOX</span><h2>Your conversations</h2></div>
              <button className="secondary-button" onClick={() => { setSelectedId(null); setShareContact(false); setShareLocation(false); setMessage(""); }}>New message</button>
            </div>
            {loading && <p className="empty-state">Loading messages…</p>}
            {!loading && conversations.length === 0 && <p className="empty-state">No conversations yet. Start one from a crop listing or the buyer directory.</p>}
            {conversations.map((conversation) => (
              <button key={conversation.id} className={`conversation-item${selectedId === conversation.id ? " active" : ""}`} onClick={() => setSelectedId(conversation.id)}>
                <span><strong>{conversation.other_party.name}</strong><small>{conversation.crop} · {conversation.quantity_tonnes} tonnes</small></span>
                <small>{conversation.messages[conversation.messages.length - 1]?.body ?? "Conversation started"}</small>
              </button>
            ))}
          </section>
          <section className="conversation-detail panel">
            {selected ? (
              <>
                <div className="conversation-title">
                  <div><span className="eyebrow green">{selected.crop} · {selected.quantity_tonnes} TONNES</span><h2>{otherParty?.name}</h2></div>
                  <div className="conversation-sharing-status">
                    {otherParty?.phone && <a href={`tel:${otherParty.phone}`}>{otherParty.phone}</a>}
                    {otherParty?.email && <a href={`mailto:${otherParty.email}`}>{otherParty.email}</a>}
                    {[otherParty?.location_name, otherParty?.district, otherParty?.state].filter(Boolean).join(", ") && <span>{[otherParty?.location_name, otherParty?.district, otherParty?.state].filter(Boolean).join(", ")}</span>}
                    {otherParty?.latitude != null && otherParty?.longitude != null && <a href={`https://www.google.com/maps?q=${otherParty.latitude},${otherParty.longitude}`} target="_blank" rel="noreferrer">View shared map location</a>}
                  </div>
                </div>
                <div className="conversation-messages">
                  {selected.messages.map((item) => <article key={item.id} className={`conversation-message${item.is_mine ? " mine" : ""}`}><p>{item.body}</p><small>{item.is_mine ? "You" : otherParty?.name} · {new Date(item.created_at).toLocaleString()}</small></article>)}
                </div>
              </>
            ) : (
              <div className="conversation-title">
                <span className="eyebrow green">NEW MESSAGE</span>
                <h2>{role === "buyer" ? "Contact a farmer" : "Contact a buyer"}</h2>
                {pendingContact?.listingId && <p>Message the farmer about the selected crop listing.</p>}
              </div>
            )}
            <form className="conversation-compose" onSubmit={sendMessage}>
              {!selected && <div className="conversation-targets">
                {role === "farmer" && <>
                  <label>Your crop listing<select value={listingId} onChange={(event) => setListingId(event.target.value)} required>
                    <option value="">Choose a listing</option>
                    {ownListings.map((listing) => <option key={listing.id} value={listing.id}>{listing.crop} · {listing.quantity_tonnes} tonnes</option>)}
                  </select></label>
                  <label>Registered buyer<select value={buyerId} onChange={(event) => setBuyerId(event.target.value)} required>
                    <option value="">Choose a buyer</option>
                    {directoryBuyerAccounts.map((buyer) => <option key={buyer.id} value={String(buyer.account_id ?? "")}>{buyer.name} · {buyer.location_name}</option>)}
                  </select></label>
                </>}
                {role === "buyer" && <label>Crop listing<select value={listingId} onChange={(event) => setListingId(event.target.value)} required>
                  <option value="">Choose a farmer listing</option>
                  {ownListings.map((listing) => <option key={listing.id} value={listing.id}>{listing.crop} · {listing.farmer.name} · {listing.quantity_tonnes} tonnes</option>)}
                </select></label>}
              </div>}
              <label className="conversation-message-input">Message<textarea value={message} onChange={(event) => setMessage(event.target.value)} required maxLength={2000} placeholder="Ask about price, delivery, or availability" /></label>
              <fieldset className="sharing-consent">
                <legend>Share my details with this person (optional)</legend>
                <label><input type="checkbox" checked={shareContact} onChange={(event) => setShareContact(event.target.checked)} /> Share my phone and email</label>
                <label><input type="checkbox" checked={shareLocation} onChange={(event) => setShareLocation(event.target.checked)} /> Share my saved address and map location</label>
              </fieldset>
              <p className="privacy-note">Both boxes start unchecked. The other person's contact or location appears only if they have also opted in.</p>
              <button className="primary-button" type="submit" disabled={busy || loading || !message.trim() || (!selected && (!listingId || (role === "farmer" && !buyerId)))}>{busy ? "Sending…" : "Send message"}</button>
            </form>
          </section>
        </div>
      )}
    </>
  );
}

function FinancialForecastView({ token, farm }: { token: string | null; farm: Farm | null }) {
  const [cropOptions, setCropOptions] = useState<CropOption[]>([]);
  const [cropId, setCropId] = useState("");
  const [forecast, setForecast] = useState<FinancialForecast | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    api.crops(token).then((options) => {
      if (cancelled) return;
      setCropOptions(options);
      setCropId((current) => current || (options[0] ? String(options[0].id) : ""));
    }).catch((loadError) => {
      if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Could not load crops.");
    });
    return () => { cancelled = true; };
  }, [token]);

  const estimate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !cropId) return;
    setLoading(true);
    setError("");
    try {
      setForecast(await api.financialForecast(Number(cropId), token, farm?.id));
    } catch (forecastError) {
      setError(forecastError instanceof Error ? forecastError.message : "Could not calculate a farm forecast.");
      setForecast(null);
    } finally {
      setLoading(false);
    }
  };
  const rupees = (value: number) => `₹${Math.round(value).toLocaleString("en-IN")}`;
  const activeCrop = cropOptions.find((crop) => String(crop.id) === cropId);

  return (
    <>
      <PageHeading eyebrow="FARM FINANCIAL PLANNING" title="Plan the season before you spend." text="Compare estimated crop costs, revenue, and profit or loss against your farm's saved budget. These are scenarios, not guaranteed returns." />
      {!token && <div className="marketplace-error">Log in to calculate a forecast using your saved farm profile.</div>}
      <form className="forecast-form panel" onSubmit={estimate}>
        <div>
          <span className="eyebrow green">YOUR INPUTS</span>
          <h2>{farm ? `${farm.land_size_acres} acres · ${rupees(farm.budget)} available budget` : "A saved farm profile is required"}</h2>
          <p>Update your land size, season, and budget in My Farm before comparing crop scenarios.</p>
        </div>
        <label>Crop to estimate
          <select value={cropId} onChange={(event) => setCropId(event.target.value)} required disabled={!cropOptions.length}>
            {cropOptions.length === 0 && <option value="">Loading crops…</option>}
            {cropOptions.map((crop) => <option key={crop.id} value={crop.id}>{crop.name}</option>)}
          </select>
        </label>
        <button className="primary-button" type="submit" disabled={!token || !farm || !cropId || loading}>{loading ? "Estimating…" : "Estimate budget & returns"}</button>
      </form>
      {error && <div className="marketplace-error" role="alert">{error}</div>}
      {forecast && <section className="forecast-results">
        <div className="forecast-summary panel">
          <div><span className="eyebrow green">EXPECTED SCENARIO · {forecast.crop || activeCrop?.name}</span><h2>{rupees(forecast.scenarios.expected.profit_or_loss)} <small>estimated profit / loss</small></h2><p>{forecast.budget_status === "sufficient" ? "Your budget covers the estimated production cost." : `Estimated budget shortfall: ${rupees(Math.abs(forecast.budget_after_production))}`}</p></div>
          <div className="forecast-metrics"><span><small>PRODUCTION BUDGET</small><b>{rupees(forecast.production_budget_required)}</b></span><span><small>EXPECTED REVENUE</small><b>{rupees(forecast.scenarios.expected.gross_revenue)}</b></span><span><small>EXPECTED YIELD</small><b>{forecast.scenarios.expected.expected_yield_kg.toLocaleString("en-IN")} kg</b></span></div>
        </div>
        <div className="forecast-scenario-grid">
          {(["low", "expected", "high"] as const).map((scenario) => {
            const item = forecast.scenarios[scenario];
            return <article className={`forecast-scenario panel ${scenario}`} key={scenario}><span className="eyebrow green">{scenario.toUpperCase()} SCENARIO</span><h3>{rupees(item.profit_or_loss)} <small>net</small></h3><dl><div><dt>Gross revenue</dt><dd>{rupees(item.gross_revenue)}</dd></div><div><dt>Total costs</dt><dd>{rupees(item.total_cost)}</dd></div><div><dt>Yield</dt><dd>{item.expected_yield_kg.toLocaleString("en-IN")} kg</dd></div><div><dt>Market price</dt><dd>{rupees(item.price_per_kg)} / kg</dd></div></dl></article>;
          })}
        </div>
        <div className="forecast-notes panel"><strong>How to read this estimate</strong><p>Confidence: {forecast.confidence}. Price source: {forecast.price_source}. Actual yields, market prices, weather, and costs may differ.</p><ul>{Object.entries(forecast.assumptions).map(([key, value]) => <li key={key}>{key.replace(/_/g, " ")}: {String(value)}</li>)}</ul></div>
      </section>}
    </>
  );
}

function FarmProfile({
  user,
  farm,
  soil,
  water,
  setSoil,
  setWater,
  notify,
  saveFarm,
}: {
  user: User | null;
  farm: Farm | null;
  soil: string;
  water: string;
  setSoil: (value: string) => void;
  setWater: (value: string) => void;
  notify: (message: string) => void;
  saveFarm: (payload: Omit<Farm, "id">) => Promise<void>;
}) {
  return (
    <>
      <PageHeading
        eyebrow="MY FARM"
        title="A profile that learns with you."
        text="Keep your farm inputs current so every recommendation stays grounded in your reality."
        action={
          <button
            className="primary-button"
            onClick={() => saveFarm({ land_size_acres: farm?.land_size_acres ?? 2, soil_type: soil, water_availability: water, current_season: farm?.current_season ?? "Kharif", budget: farm?.budget ?? 0, previous_crop: farm?.previous_crop ?? null })}
          >
            Save changes
          </button>
        }
      />
      <div className="profile-layout">
        <div className="profile-main panel">
          <div className="profile-cover">
            <div className="farm-cover-image" />
            <div className="farm-identity">
              <div className="large-avatar">{user?.name?.slice(0, 2).toUpperCase()}</div>
              <div>
                <h2>{user?.name ?? "Your"}&apos;s farm</h2>
                <p>{user?.district ?? user?.location_name ?? "Add your location"} · {farm?.land_size_acres ?? "—"} acres</p>
              </div>
              <span className="complete-badge">92% complete</span>
            </div>
          </div>
          <div className="profile-form">
            <h3>Farm conditions</h3>
            <div className="form-grid">
              <label>
                STATE
                <input value={user?.state ?? ""} placeholder="Add state" readOnly />
              </label>
              <label>
                DISTRICT
                <input value={user?.district ?? ""} placeholder="Add district" readOnly />
              </label>
              <label>
                LAND SIZE
                <input value={farm ? `${farm.land_size_acres} acres` : "Not set"} readOnly />
              </label>
              <label>
                SOIL TYPE
                <select value={soil} onChange={(e) => setSoil(e.target.value)}>
                  <option>Loamy</option>
                  <option>Red loam</option>
                  <option>Black soil</option>
                </select>
              </label>
              <label>
                WATER AVAILABILITY
                <select
                  value={water}
                  onChange={(e) => setWater(e.target.value)}
                >
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                </select>
              </label>
              <label>
                IRRIGATION TYPE
                <select>
                  <option>Open well + rain</option>
                  <option>Drip irrigation</option>
                  <option>Canal</option>
                </select>
              </label>
              <label>
                AVAILABLE BUDGET
                <input value={`INR ${(farm?.budget ?? 0).toLocaleString("en-IN")}`} readOnly />
              </label>
              <label>
                CURRENT SEASON
                <select>
                    <option>{farm?.current_season ?? "Kharif"}</option>
                </select>
              </label>
            </div>
            <div className="profile-callout">
              <span>✦</span>
              <div>
                <strong>One more detail will sharpen your plan</strong>
                <p>
                  Add your soil test result when available. FarmWise keeps
                  recommendations useful even without it.
                </p>
              </div>
              <button
                onClick={() => notify("Soil test field added to your profile.")}
              >
                Add soil test →
              </button>
            </div>
          </div>
        </div>
        <aside className="profile-side">
          <div className="panel completion-card">
            <span className="ring">
              92<small>%</small>
            </span>
            <h3>Your farm profile</h3>
            <p>Complete profiles unlock more useful comparisons.</p>
            <div className="completion-line">
              <i />
            </div>
            <small>6 of 7 details added</small>
          </div>
          <div className="panel location-card">
            <p className="eyebrow">FARM LOCATION</p>
            <div className="mini-map">
              <span>⌖</span>
            </div>
            <strong>Guntur, Andhra Pradesh</strong>
            <small>15.8281° N · 80.0488° E</small>
          </div>
        </aside>
      </div>
    </>
  );
}
async function prepareCropMedia(file: File): Promise<string> {
  if (file.size > 10 * 1024 * 1024) {
    throw new Error("Crop photos and videos must be 10 MB or smaller.");
  }
  const extension = file.name.split(".").pop()?.toLowerCase();
  const videoType = extension === "mp4" ? "video/mp4"
    : extension === "webm" ? "video/webm"
      : extension === "mov" ? "video/quicktime"
        : null;
  if (videoType) {
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => typeof reader.result === "string"
        ? resolve(reader.result.replace(/^data:[^;]+;/, `data:${videoType};`))
        : reject(new Error("Could not read this video."));
      reader.onerror = () => reject(new Error("Could not read this video."));
      reader.readAsDataURL(file);
    });
  }
  if (!file.type.startsWith("image/")) {
    throw new Error("Choose a JPEG, PNG, WebP photo or MP4, WebM, MOV video.");
  }
  const bitmap = await createImageBitmap(file);
  try {
    const scale = Math.min(1, 1280 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Could not process this photo.");
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (result) => result ? resolve(result) : reject(new Error("Could not process this photo.")),
        "image/jpeg",
        0.82,
      );
    });
    if (blob.size > 1_400_000) {
      throw new Error("This photo is too large to upload. Choose a smaller image.");
    }
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => typeof reader.result === "string" ? resolve(reader.result) : reject(new Error("Could not read this photo."));
      reader.onerror = () => reject(new Error("Could not read this photo."));
      reader.readAsDataURL(blob);
    });
  } finally {
    bitmap.close();
  }
}

function HarvestView({
  token,
  onPublish,
}: {
  token: string | null;
  onPublish: (payload: HarvestPayload) => Promise<void>;
}) {
  const [cropOptions, setCropOptions] = useState<CropOption[]>([]);
  const [cropId, setCropId] = useState("");
  const [quantity, setQuantity] = useState("2");
  const [grade, setGrade] = useState("A");
  const [harvestDate, setHarvestDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState("");
  const [photo, setPhoto] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    api.crops(token)
      .then((options) => {
        if (cancelled) return;
        setCropOptions(options);
        if (options.length) setCropId(String(options[0].id));
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Could not load crops.");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const handlePhoto = async (file?: File) => {
    if (!file) return;
    try {
      setError("");
      setPhoto(await prepareCropMedia(file));
    } catch (photoError) {
      setError(photoError instanceof Error ? photoError.message : "Could not use this photo.");
    }
  };

  const submitHarvest = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    if (!cropId) {
      setError("No crops are available. Seed the backend crop catalog and try again.");
      return;
    }
    if (!photo) {
      setError("Take a photo or choose a crop photo before sharing with buyers.");
      return;
    }
    setBusy(true);
    try {
      await onPublish({
        crop_id: Number(cropId),
        quantity_tonnes: Number(quantity),
        grade,
        harvest_date: harvestDate,
        notes,
        photo_data_url: photo,
      });
      setPhoto("");
      setNotes("");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not share this harvest.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeading
        eyebrow="MY HARVEST"
        title="Show buyers what you have grown."
        text="Take a crop photo, add harvest details, and share your listing with the buyer directory."
      />
      {!token && (
        <p className="harvest-error">
          Demo mode is read-only. Log in to your farmer account with the backend running to publish harvests.
        </p>
      )}
      <div className="harvest-layout">
        <form className="harvest-form panel" onSubmit={submitHarvest}>
          <div className={`harvest-image${photo ? " has-photo" : ""}`}>
            {photo ? photo.startsWith("data:video/")
              ? <video src={photo} controls playsInline aria-label="Your crop video preview" />
              : <img src={photo} alt="Your crop photo preview" />
              : <div className="photo-placeholder"><span>▧</span><strong>Add a photo or video of your crop</strong><small>Photo or video up to 10 MB</small></div>}
          </div>
          <div className="harvest-fields">
            <label>
              CROP
              <select value={cropId} onChange={(event) => setCropId(event.target.value)} required>
                {cropOptions.length === 0 && <option value="">No crop choices available</option>}
                {cropOptions.map((crop) => <option value={crop.id} key={crop.id}>{crop.name}</option>)}
              </select>
            </label>
            <label>
              QUANTITY (TONNES)
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
                required
              />
            </label>
            <label>
              QUALITY / GRADE
              <select value={grade} onChange={(event) => setGrade(event.target.value)}>
                <option value="A">Grade A</option>
                <option value="B">Grade B</option>
                <option value="C">Grade C</option>
              </select>
            </label>
            <label>
              HARVEST DATE
              <input type="date" value={harvestDate} onChange={(event) => setHarvestDate(event.target.value)} required />
            </label>
            <label className="harvest-notes">
              NOTES FOR BUYERS
              <textarea value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={500} placeholder="Add variety, freshness, or delivery details" />
            </label>
            <label className="photo-upload-button">
              {photo ? "Choose another crop photo or video" : "Take a photo / choose photo or video"}
              <input type="file" accept="image/*,video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov" capture="environment" onChange={(event) => { void handlePhoto(event.target.files?.[0]); event.currentTarget.value = ""; }} />
            </label>
            {error && <p className="harvest-error" role="alert">{error}</p>}
            <button className="primary-button full" type="submit" disabled={busy || !token}>
              {busy ? "Sharing harvest…" : "Share crop with buyers →"}
            </button>
          </div>
        </form>
        <div className="harvest-next">
          <span className="eyebrow green">YOUR PHOTO, YOUR OFFER</span>
          <h2>Let buyers see your harvest.</h2>
          <p>
            Your listing includes the crop photo or video, quantity, quality, and harvest date. Your private phone, email, and precise address stay hidden until you opt in inside a conversation.
          </p>
          <div className="next-list">
            <span><b>01</b> Take or upload a crop photo or video (up to 10 MB)</span>
            <span><b>02</b> Add harvest details and location</span>
            <span><b>03</b> Share it in the buyer marketplace</span>
          </div>
        </div>
      </div>
    </>
  );
}
function UserProfile({ user, onSaved }: { user: User | null; onSaved: (user: User) => void }) {
  const [name, setName] = useState(user?.name ?? "");
  const [state, setState] = useState(user?.state ?? user?.location_name ?? "");
  const [district, setDistrict] = useState(user?.district ?? "");
  const [latitude, setLatitude] = useState<number | null>(user?.latitude ?? null);
  const [longitude, setLongitude] = useState<number | null>(user?.longitude ?? null);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [harvestHistory, setHarvestHistory] = useState<Array<{ id: number; crop: string; quantity_tonnes: number; grade: string; harvest_date: string; is_listed: boolean }>>([]);
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [error, setError] = useState("");
  const token = getToken();

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    Promise.all([api.farms(token), api.harvests(token)])
      .then(([accountFarms, accountHarvests]) => {
        if (!cancelled) {
          setFarms(accountFarms);
          setHarvestHistory(accountHarvests);
        }
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Could not load account details.");
      });
    return () => { cancelled = true; };
  }, [token]);

  const save = async () => {
    if (!token) return;
    setSaving(true);
    setError("");
    try {
      onSaved(await api.updateProfile({
        name,
        language: user?.language ?? "en",
        location_name: [district, state].filter(Boolean).join(", "),
        state,
        district,
        latitude,
        longitude,
      }, token));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save account details.");
    } finally {
      setSaving(false);
    }
  };

  const locate = () => {
    if (!navigator.geolocation) {
      setError("Location is not available in this browser.");
      return;
    }
    setLocating(true);
    setError("");
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLatitude(coords.latitude);
        setLongitude(coords.longitude);
        setLocating(false);
      },
      (locationError) => {
        setError(locationError.code === locationError.PERMISSION_DENIED
          ? "Location permission was denied. You can enter your state and district instead."
          : "Could not get your location. Check device location settings and try again.");
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 },
    );
  };

  const farm = farms[0];
  const mapLink = latitude !== null && longitude !== null
    ? `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`
    : "";
  return (
    <>
      {!token && <p className="marketplace-error">You’re viewing Demo Mode. Sign in with a real account to see and update your personal details.</p>}
      <PageHeading
        eyebrow="YOUR ACCOUNT"
        title={user?.role === "buyer" ? "Your complete account profile." : "Your complete farmer profile."}
        text={user?.role === "buyer"
          ? "Review your contact details and saved location. Your precise location is shared only when you opt in to a conversation."
          : "Review your contact details, growing location, farm setup and harvest history."}
        action={<button className="primary-button" onClick={() => void save()} disabled={saving || !token}>{saving ? "Saving…" : "Save changes"}</button>}
      />
      {error && <p className="marketplace-error" role="alert">{error}</p>}
      <div className="profile-layout">
        <div className="profile-main panel">
          <div className="profile-form">
            <div className="farm-identity">
              <div className="large-avatar">{user?.name?.slice(0, 2).toUpperCase()}</div>
              <div><h2>{user?.name}</h2><p>{user?.role === "buyer" ? "Buyer / broker account" : "Farmer account"}</p></div>
            </div>
            <div className="form-grid">
              <label>FULL NAME<input value={name} onChange={(event) => setName(event.target.value)} /></label>
              <label>EMAIL<input value={user?.email ?? "Not added"} readOnly /></label>
              <label>MOBILE NUMBER<input value={user?.phone ?? "Not added"} readOnly /></label>
              <label>STATE<input value={state} onChange={(event) => setState(event.target.value)} /></label>
              <label>DISTRICT<input value={district} onChange={(event) => setDistrict(event.target.value)} /></label>
              <label>ACCOUNT TYPE<input value={user?.role ?? "farmer"} readOnly /></label>
            </div>
            <div className="profile-location-details">
              <div><span className="eyebrow green">{user?.role === "buyer" ? "SAVED LOCATION" : "FARM LOCATION"}</span><strong>{[district, state].filter(Boolean).join(", ") || user?.location_name || "Add your district and state"}</strong>
                {latitude !== null && longitude !== null && <small>{latitude.toFixed(5)}°, {longitude.toFixed(5)}° · location shared with your account</small>}
              </div>
              <button className="outline-button" type="button" onClick={locate} disabled={locating || !token}>{locating ? "Getting location…" : "Use my current location"}</button>
              {mapLink && <a href={mapLink} target="_blank" rel="noreferrer">Open map ↗</a>}
              <small>Location is requested only when you press this button. FarmWise does not track your live location in the background.</small>
            </div>
            <div className="profile-callout"><span>✓</span><div><strong>Your account is protected</strong><p>Only you can update these account details. Your precise coordinates are not shown in public crop listings.</p></div></div>
          </div>
        </div>
        <aside className="profile-side">
          <div className="panel completion-card"><span className="ring">✓</span><h3>Member since</h3><p>{user?.created_at ? new Date(user.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "long" }) : "Recently"}</p><small>Role: {user?.role ?? "farmer"}</small></div>
          <div className="panel account-details-card">
            <span className="eyebrow green">MY FARM</span>
            {farm ? <>
              <h3>{farm.land_size_acres} acres</h3>
              <p>{farm.soil_type} soil · {farm.water_availability} water</p>
              <p>{farm.current_season} season · INR {farm.budget.toLocaleString("en-IN")} budget</p>
              {farm.previous_crop && <small>Previous crop: {farm.previous_crop}</small>}
            </> : <p>No farm saved yet. Add your farm details under My Farm.</p>}
          </div>
          <div className="panel account-details-card">
            <span className="eyebrow green">HARVEST HISTORY</span>
            <h3>{harvestHistory.length} harvest{harvestHistory.length === 1 ? "" : "s"}</h3>
            {harvestHistory.slice(0, 5).map((harvest) => <p key={harvest.id}><strong>{harvest.crop}</strong> · {harvest.quantity_tonnes} t · Grade {harvest.grade}{harvest.is_listed ? " · Shared with buyers" : ""}</p>)}
            {!harvestHistory.length && <p>Your harvest records will appear here.</p>}
          </div>
        </aside>
      </div>
    </>
  );
}
function Analytics({ demo }: { demo: boolean }) {
  if (!demo) return <><PageHeading eyebrow="ANALYTICS" title="Your analytics will grow with your data." text="Record a farm and harvest to calculate account-specific realization, profit and resource efficiency." /><div className="panel empty-state">No analytics are available yet for this account.</div></>;
  return (
    <>
      <PageHeading
        eyebrow="ANALYTICS"
        title="See the value of each decision."
        text="A transparent view of estimated costs, realization and resource efficiency. Nothing here is a guarantee."
      />
      <div className="analytics-stats">
        <Stat
          label="Expected revenue"
          value="INR 84,600"
          note="per acre"
          change="Estimated"
        />
        <Stat
          label="Expected profit"
          value="INR 18,500"
          note="per acre"
          change="+12.4%"
        />
        <Stat
          label="Net realization"
          value="INR 19.10"
          note="per kg"
          change="Best option"
        />
        <Stat
          label="Sustainability score"
          value="82 / 100"
          note="resource index"
          change="On track"
        />
      </div>
      <div className="analytics-grid">
        <div className="panel chart-panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">COST VS REVENUE</p>
              <h3>Estimated economics</h3>
            </div>
            <span className="data-tag">SIMULATED</span>
          </div>
          <div className="bar-chart">
            <div className="axis">
              <span>100k</span>
              <span>75k</span>
              <span>50k</span>
              <span>25k</span>
              <span>0</span>
            </div>
            <div className="bars">
              {["Inputs", "Transport", "Market", "Revenue"].map((item, i) => (
                <div className="bar-set" key={item}>
                  <div
                    className={`bar bar-${i}`}
                    style={{ height: `${[30, 14, 22, 90][i]}%` }}
                  />
                  <small>{item}</small>
                </div>
              ))}
            </div>
          </div>
          <div className="chart-legend">
            <span>
              <i className="legend-cost" /> Estimated cost
            </span>
            <span>
              <i className="legend-revenue" /> Expected revenue
            </span>
          </div>
        </div>
        <div className="panel efficiency-panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">RESOURCE EFFICIENCY</p>
              <h3>A lighter plan</h3>
            </div>
          </div>
          <ScoreBar label="Water efficiency" value={74} />
          <ScoreBar label="Input efficiency" value={81} />
          <ScoreBar label="Transport efficiency" value={68} />
          <ScoreBar label="Market optionality" value={86} />
          <div className="efficiency-note">
            Your recommended path favors a crop with low water demand and a
            nearby market with active buyers.
          </div>
        </div>
      </div>
    </>
  );
}

function PageHeading({
  eyebrow,
  title,
  text,
  action,
}: {
  eyebrow: string;
  title: string;
  text: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <p className="eyebrow green">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
      {action}
    </div>
  );
}
function InfoTile({
  num,
  title,
  text,
}: {
  num: string;
  title: string;
  text: string;
}) {
  return (
    <div className="info-tile">
      <span>{num}</span>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}
function Stat({
  label,
  value,
  note,
  change,
}: {
  label: string;
  value: string;
  note: string;
  change: string;
}) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <div>
        <small>{note}</small>
        <em>{change}</em>
      </div>
    </div>
  );
}
function ImpactStat({ value, label }: { value: string; label: string }) {
  return (
    <div className="impact-stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
function Journey({
  label,
  value,
  status,
  icon,
  active,
}: {
  label: string;
  value: string;
  status: string;
  icon: string;
  active?: boolean;
}) {
  return (
    <div className={active ? "journey active" : "journey"}>
      <span>{icon}</span>
      <small>{label}</small>
      <strong>{value}</strong>
      <em>{status}</em>
    </div>
  );
}
function MiniCrop({
  crop,
  index,
  onClick,
}: {
  crop: Crop;
  index: number;
  onClick: () => void;
}) {
  return (
    <button
      className={index === 0 ? "mini-crop selected" : "mini-crop"}
      onClick={onClick}
    >
      <img src={crop.image} alt="" />
      <div>
        <strong>{crop.name}</strong>
        <small>
          {crop.water} water · {crop.risk} risk
        </small>
        <div className="mini-score">
          <i style={{ width: `${crop.score}%` }} />
          <b>{crop.score}%</b>
        </div>
      </div>
      <span>
        INR {crop.profit.replace("INR ", "")}
        <small>/ acre est.</small>
      </span>
      <b className="mini-rank">0{index + 1}</b>
    </button>
  );
}
function CropRecommendation({
  crop,
  rank,
  selected,
  onSelect,
}: {
  crop: Crop;
  rank: number;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      className={
        selected ? "crop-recommendation selected" : "crop-recommendation"
      }
      onClick={onSelect}
    >
      <img src={crop.image} alt={`${crop.name} crop`} />
      <div className="crop-rec-content">
        <div className="crop-rec-top">
          <div>
            <span className="rec-rank">0{rank}</span>
            <h3>{crop.name}</h3>
            <p>
              {crop.risk} market risk · {crop.water} water
            </p>
          </div>
          <div className="suitability">
            <strong>{crop.score}%</strong>
            <span>farm suitability</span>
          </div>
        </div>
        <div className="rec-details">
          <span>
            <small>EXPECTED YIELD</small>
            <b>{crop.yield}</b>
          </span>
          <span>
            <small>EST. COST</small>
            <b>{crop.cost} / acre</b>
          </span>
          <span>
            <small>EST. RETURN</small>
            <b>{crop.profit} / acre</b>
          </span>
        </div>
        <div className="rec-reason">
          <span>✦</span>
          <p>{crop.reason}</p>
          <b>
            {selected ? "Selected" : "View recommendation"}{" "}
            {selected ? "✓" : "→"}
          </b>
        </div>
      </div>
    </button>
  );
}
function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-bar">
      <div>
        <span>{label}</span>
        <b>{value}</b>
      </div>
      <i>
        <em style={{ width: `${value}%` }} />
      </i>
    </div>
  );
}
function BuyerRow({
  buyer,
  onEnquiry,
}: {
  buyer: (typeof buyers)[number];
  onEnquiry: () => void;
}) {
  return (
    <div className="buyer-row">
      <div className="buyer-initials">{buyer.initials}</div>
      <div className="buyer-row-info">
        <div>
          <strong>{buyer.name}</strong>
          <span>✓ Verified fields</span>
        </div>
        <small>
          {buyer.location} · {buyer.quantity}
        </small>
      </div>
      <div className="match-score">
        <strong>{buyer.match}%</strong>
        <small>match</small>
      </div>
      <button onClick={onEnquiry}>Enquire</button>
    </div>
  );
}
function BuyerLarge({
  buyer,
  onEnquiry,
  sent,
}: {
  buyer: (typeof buyers)[number];
  onEnquiry: () => void;
  sent: boolean;
}) {
  return (
    <div className="buyer-large panel">
      <div className="buyer-big-avatar">{buyer.initials}</div>
      <div className="buyer-large-info">
        <div className="buyer-name-line">
          <h3>{buyer.name}</h3>
          <span className="verified-pill">✓ Verified fields</span>
        </div>
        <p>
          {buyer.type} · {buyer.location}
        </p>
        <div className="buyer-facts">
          <span>
            <small>INTERESTED IN</small>
            <b>Groundnut, Tomato</b>
          </span>
          <span>
            <small>REQUIRED QUANTITY</small>
            <b>{buyer.quantity}</b>
          </span>
          <span>
            <small>EXPECTED OFFER</small>
            <b>{buyer.offer}</b>
          </span>
          <span>
            <small>VERIFIED DATA</small>
            <b>{buyer.verification}</b>
          </span>
        </div>
      </div>
      <div className="buyer-match-ring">
        <strong>{buyer.match}%</strong>
        <span>AI match</span>
      </div>
      <div className="buyer-actions">
        <button className="primary-button" onClick={onEnquiry}>
          {sent ? "Enquiry sent ✓" : "Contact buyer"}
        </button>
        <button className="outline-button" onClick={onEnquiry}>
          View profile
        </button>
      </div>
    </div>
  );
}
function EnquiryModal({
  quantity,
  setQuantity,
  sent,
  onClose,
  onSend,
}: {
  quantity: string;
  setQuantity: (value: string) => void;
  sent: boolean;
  onClose: () => void;
  onSend: () => void;
}) {
  return (
    <div className="modal-backdrop">
      <div className="enquiry-modal">
        <button className="modal-close" onClick={onClose}>
          ×
        </button>
        <span className="modal-kicker">NEW ENQUIRY</span>
        <h2>Connect with Rajesh Traders.</h2>
        <p>Send a clear request so the buyer can respond faster.</p>
        <div className="enquiry-buyer">
          <div className="buyer-initials">RT</div>
          <div>
            <strong>Rajesh Traders</strong>
            <small>Wholesaler · Guntur APMC · 94% match</small>
          </div>
        </div>
        <div className="two-fields">
          <label>
            CROP
            <input value="Groundnut" readOnly />
          </label>
          <label>
            QUANTITY
            <input
              value={`${quantity} tonnes`}
              onChange={(e) =>
                setQuantity(e.target.value.replace(/[^0-9.]/g, ""))
              }
            />
          </label>
        </div>
        <div className="two-fields">
          <label>
            GRADE
            <select>
              <option>Grade A</option>
              <option>Grade B</option>
            </select>
          </label>
          <label>
            EXPECTED PRICE
            <input value="INR 18 / kg" readOnly />
          </label>
        </div>
        <label>
          MESSAGE
          <textarea defaultValue="I have 2 tonnes of Grade A groundnut available for sale." />
        </label>
        <button className="auth-submit" onClick={onSend}>
          {sent ? "Enquiry sent ✓" : "Send enquiry"} <span>→</span>
        </button>
        <small className="modal-disclaimer">
          Verified fields are shown exactly as provided by the buyer. FarmWise
          does not guarantee transactions.
        </small>
      </div>
    </div>
  );
}

export default App;
