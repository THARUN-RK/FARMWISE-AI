import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  api,
  clearToken,
  getToken,
  saveToken,
  type ApiCrop,
  type Farm,
  type User,
} from "./api";

type Module =
  | "Dashboard"
  | "My Farm"
  | "Crop Planner"
  | "Market Intelligence"
  | "Buyers & Brokers"
  | "My Harvest"
  | "Analytics"
  | "Profile";
type Language = "en" | "kn" | "te" | "ta";
const LanguageContext = createContext<{ language: Language; setLanguage: (language: Language) => void }>({ language: "en", setLanguage: () => undefined });
const translations: Record<Language, Record<string, string>> = {
  en: { dashboard: "Dashboard", farm: "My Farm", planner: "Crop Planner", markets: "Market Intelligence", buyers: "Buyers & Brokers", harvest: "My Harvest", analytics: "Analytics", profile: "Profile", login: "Log in", signup: "Get started", greeting: "Good morning", cropPlan: "What should I grow?", marketPlan: "Where should you sell?" },
  kn: { dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", farm: "ನನ್ನ ಜಮೀನು", planner: "ಬೆಳೆ ಯೋಜಕ", markets: "ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ", buyers: "ಖರೀದಿದಾರರು ಮತ್ತು ದಲ್ಲಾಳಿಗಳು", harvest: "ನನ್ನ ಕೊಯ್ಲು", analytics: "ವಿಶ್ಲೇಷಣೆ", profile: "ಪ್ರೊಫೈಲ್", login: "ಲಾಗಿನ್", signup: "ಪ್ರಾರಂಭಿಸಿ", greeting: "ಶುಭೋದಯ", cropPlan: "ನಾನು ಏನು ಬೆಳೆಯಬೇಕು?", marketPlan: "ನಾನು ಎಲ್ಲಿ ಮಾರಾಟ ಮಾಡಬೇಕು?" },
  te: { dashboard: "డాష్‌బోర్డ్", farm: "నా పొలం", planner: "పంట ప్రణాళిక", markets: "మార్కెట్ సమాచారం", buyers: "కొనుగోలుదారులు మరియు బ్రోకర్లు", harvest: "నా పంట", analytics: "విశ్లేషణ", profile: "ప్రొఫైల్", login: "లాగిన్", signup: "ప్రారంభించండి", greeting: "శుభోదయం", cropPlan: "నేను ఏమి పండించాలి?", marketPlan: "నేను ఎక్కడ అమ్మాలి?" },
  ta: { dashboard: "டாஷ்போர்டு", farm: "என் பண்ணை", planner: "பயிர் திட்டமிடல்", markets: "சந்தை தகவல்", buyers: "வாங்குபவர்கள் மற்றும் தரகர்கள்", harvest: "என் அறுவடை", analytics: "பகுப்பாய்வு", profile: "சுயவிவரம்", login: "உள்நுழை", signup: "தொடங்குங்கள்", greeting: "காலை வணக்கம்", cropPlan: "நான் என்ன பயிரிட வேண்டும்?", marketPlan: "நான் எங்கே விற்க வேண்டும்?" },
};
function useLanguage() { const context = useContext(LanguageContext); return { ...context, t: (key: string) => translations[context.language][key] ?? translations.en[key] ?? key }; }
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
  { label: "Buyers & Brokers", icon: "♧" },
  { label: "My Harvest", icon: "◒" },
  { label: "Analytics", icon: "▥" },
  { label: "Profile", icon: "◎" },
];
const navTranslationKeys: Record<string, string> = { Dashboard: "dashboard", "My Farm": "farm", "Crop Planner": "planner", "Market Intelligence": "markets", "Buyers & Brokers": "buyers", "My Harvest": "harvest", Analytics: "analytics", Profile: "profile" };

function App() {
  const [authenticated, setAuthenticated] = useState(false),
    [authMode, setAuthMode] = useState<"login" | "signup" | null>(null),
    [authLoading, setAuthLoading] = useState(true);
  const [language, setLanguage] = useState<Language>(() => (localStorage.getItem("farmwise_language") as Language) || "en");
  const [user, setUser] = useState<User | null>(null),
    [farm, setFarm] = useState<Farm | null>(null),
    [apiRecommendations, setApiRecommendations] = useState<ApiCrop[]>([]);
  const [active, setActive] = useState<Module>("Dashboard"),
    [demo, setDemo] = useState(false),
    [menuOpen, setMenuOpen] = useState(false);
  const [toast, setToast] = useState(""),
    [enquiryOpen, setEnquiryOpen] = useState(false),
    [enquirySent, setEnquirySent] = useState(false),
    [plannerLoading, setPlannerLoading] = useState(false);
  const [selectedCrop, setSelectedCrop] = useState(crops[0]),
    [water, setWater] = useState("Medium"),
    [soil, setSoil] = useState("Loamy"),
    [quantity, setQuantity] = useState("2");
  const changeLanguage = (nextLanguage: Language) => { setLanguage(nextLanguage); localStorage.setItem("farmwise_language", nextLanguage); };
  const loadAccount = async (token: string) => {
    const currentUser = await api.me(token);
    const farms = await api.farms(token);
    setUser(currentUser);
    setFarm(farms[0] ?? null);
    setActive(currentUser.role === "buyer" ? "Buyers & Brokers" : "Dashboard");
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
      <LanguageContext.Provider value={{ language, setLanguage: changeLanguage }}>
      <div className="loading-screen">
        <span className="spinner" /> Loading your FarmWise workspace...
      </div></LanguageContext.Provider>
    );
  if (!authenticated)
    return (
      <LanguageContext.Provider value={{ language, setLanguage: changeLanguage }}>
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
        onDemo={startDemo}
      />
      </LanguageContext.Provider>
    );
  return (
    <LanguageContext.Provider value={{ language, setLanguage: changeLanguage }}>
    <div className="product-shell">
      <aside className={menuOpen ? "app-sidebar open" : "app-sidebar"}>
        <div className="brand">
          <span className="brand-symbol">FW</span>
          <span>
            FarmWise <b>AI</b>
          </span>
        </div>
        <div className="sidebar-profile">
          <div className="profile-avatar">
            {user?.name?.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <strong>{user?.name}</strong>
            <small>
              {user?.role === "buyer" ? "Buyer account" : "Farmer account"}
            </small>
          </div>
          <span className="online-dot" />
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav>
          {navItems.map((item) => (
            <button
              key={item.label}
              className={active === item.label ? "app-nav active" : "app-nav"}
              onClick={() => {
                setActive(item.label);
                setMenuOpen(false);
              }}
            >
              <span>{item.icon}</span>
              {translations[language][navTranslationKeys[item.label]]}
              {item.label === "Dashboard" && <i />}
            </button>
          ))}
        </nav>
        <p className="nav-caption lower">ACCOUNT</p>
        <nav>
          <button
            className="app-nav"
            onClick={() => notify("You have 3 new notifications.")}
          >
            <span>♢</span>Notifications <b className="count">3</b>
          </button>
          <button
            className="app-nav"
            onClick={() =>
              notify("Settings are available in the next release.")
            }
          >
            <span>⚙</span>Settings
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="season-card">
            <small>CURRENT SEASON</small>
            <strong>{farm?.current_season ?? "No farm season yet"}</strong>
            <span>
              {farm ? "Farm profile connected" : "Complete your farm profile"}
            </span>
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
            <span className="sync-status">
              <i />
              Synced 2 min ago
            </span>
            <button
              className="header-icon"
              onClick={() => notify("You have 3 new notifications.")}
              aria-label="Notifications"
            >
              ♢<i />
            </button>
            <select className="lang-button" value={language} onChange={(event) => changeLanguage(event.target.value as Language)} aria-label="Language"><option value="en">EN</option><option value="kn">ಕನ್ನಡ</option><option value="te">తెలుగు</option><option value="ta">தமிழ்</option></select>
            <div className="header-user">
              <div className="profile-avatar small">{user?.name?.slice(0, 2).toUpperCase()}</div>
              <span>{user?.name}⌄</span>
            </div>
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
          {active === "Buyers & Brokers" && (
            <BuyerView
              onEnquiry={() => setEnquiryOpen(true)}
              sent={enquirySent}
              demo={demo}
            />
          )}
          {active === "My Harvest" && (
            <HarvestView
              quantity={quantity}
              setQuantity={setQuantity}
              notify={notify}
            />
          )}
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
    </div></LanguageContext.Provider>
  );
}

function Landing({
  authMode,
  setAuthMode,
  onLogin,
  onSignup,
  onDemo,
}: {
  authMode: "login" | "signup" | null;
  setAuthMode: (mode: "login" | "signup" | null) => void;
  onLogin: (identifier: string, password: string) => Promise<void>;
  onSignup: (payload: { name: string; phone: string; email: string; password: string; confirm_password: string; role: string; state: string; district: string }) => Promise<void>;
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
}: {
  mode: "login" | "signup";
  setMode: (mode: "login" | "signup" | null) => void;
  onClose: () => void;
  onLogin: (identifier: string, password: string) => Promise<void>;
  onSignup: (payload: { name: string; phone: string; email: string; password: string; confirm_password: string; role: string; state: string; district: string }) => Promise<void>;
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
        <button className="google-button">
          G <span>Continue with Google</span>
        </button>
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
  return <select className="lang-button" value={language} onChange={(event) => setLanguage(event.target.value as Language)} aria-label="Language"><option value="en">EN</option><option value="kn">ಕನ್ನಡ</option><option value="te">తెలుగు</option><option value="ta">தமிழ்</option></select>;
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

function BuyerView({
  onEnquiry,
  sent,
  demo,
}: {
  onEnquiry: () => void;
  sent: boolean;
  demo: boolean;
}) {
  return (
    <>
      <PageHeading
        eyebrow="BUYERS & BROKERS"
        title="Who should I contact?"
        text="Discover traders, commission agents, processors, FPOs and aggregators already looking for crops like yours."
        action={
          <button className="primary-button" onClick={onEnquiry}>
            + Send an enquiry
          </button>
        }
      />
      <div className="buyer-filters">
        <button className="filter-active">All buyers</button>
        <button>Tomato</button>
        <button>Groundnut</button>
        <button>Within 50 km</button>
        <button>Verified fields⌄</button>
        <span>{demo ? "3 matches · Demo data" : "No harvest match yet"}</span>
      </div>
      <div className="buyer-list">
        {(demo ? buyers : []).map((buyer) => (
          <BuyerLarge
            key={buyer.name}
            buyer={buyer}
            onEnquiry={onEnquiry}
            sent={sent}
          />
        ))}
        {!demo && <p className="empty-state">Add a harvest to receive buyer matches from the backend.</p>}
      </div>
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
function HarvestView({
  quantity,
  setQuantity,
  notify,
}: {
  quantity: string;
  setQuantity: (value: string) => void;
  notify: (message: string) => void;
}) {
  return (
    <>
      <PageHeading
        eyebrow="MY HARVEST"
        title="Turn harvest into a selling plan."
        text="Record what is ready, then compare markets and connect with relevant buyers."
        action={
          <button
            className="primary-button"
            onClick={() => notify("Harvest recorded as a draft.")}
          >
            Save harvest
          </button>
        }
      />
      <div className="harvest-layout">
        <div className="harvest-form panel">
          <div className="harvest-image">
            <img
              src="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=1000&q=80"
              alt="Freshly harvested tomatoes"
            />
            <div>
              <span>HARVEST PREVIEW</span>
              <strong>In 95 days</strong>
            </div>
          </div>
          <div className="harvest-fields">
            <label>
              CROP
              <select>
                <option>Groundnut</option>
                <option>Tomato</option>
                <option>Chilli</option>
              </select>
            </label>
            <label>
              QUANTITY
              <input
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </label>
            <label>
              QUALITY / GRADE
              <select>
                <option>Grade A</option>
                <option>Grade B</option>
              </select>
            </label>
            <label>
              HARVEST DATE
              <input value="18 September 2025" readOnly />
            </label>
            <button
              className="primary-button full"
              onClick={() =>
                notify("Harvest saved. Market comparisons are ready.")
              }
            >
              Find selling options →
            </button>
          </div>
        </div>
        <div className="harvest-next">
          <span className="eyebrow green">NEXT STEP</span>
          <h2>Your harvest is the bridge to better realization.</h2>
          <p>
            Once you record quantity and grade, FarmWise compares the costs of
            reaching each market and surfaces buyers whose requirements fit.
          </p>
          <div className="next-list">
            <span>
              <b>01</b> Compare net realization
            </span>
            <span>
              <b>02</b> Match buyer requirements
            </span>
            <span>
              <b>03</b> Send a clear enquiry
            </span>
          </div>
        </div>
      </div>
    </>
  );
}
function UserProfile({ user, onSaved }: { user: User | null; onSaved: (user: User) => void }) {
  const [name, setName] = useState(user?.name ?? "");
  const [state, setState] = useState(user?.state ?? "");
  const [district, setDistrict] = useState(user?.district ?? "");
  const [saving, setSaving] = useState(false);
  const save = async () => {
    const token = getToken();
    if (!token) return;
    setSaving(true);
    try { onSaved(await api.updateProfile({ name, language: user?.language ?? "en", location_name: district, state, district }, token)); }
    finally { setSaving(false); }
  };
  return <><PageHeading eyebrow="PROFILE" title="Your FarmWise identity." text="Keep your personal details current. They belong only to your authenticated account." action={<button className="primary-button" onClick={save}>{saving ? "Saving..." : "Save changes"}</button>} /><div className="profile-layout"><div className="profile-main panel"><div className="profile-form"><div className="farm-identity"><div className="large-avatar">{user?.name?.slice(0, 2).toUpperCase()}</div><div><h2>{user?.name}</h2><p>{user?.role === "buyer" ? "Buyer / broker account" : "Farmer account"}</p></div></div><div className="form-grid"><label>FULL NAME<input value={name} onChange={(event) => setName(event.target.value)} /></label><label>EMAIL<input value={user?.email ?? ""} readOnly /></label><label>MOBILE NUMBER<input value={user?.phone ?? ""} readOnly /></label><label>STATE<input value={state} onChange={(event) => setState(event.target.value)} /></label><label>DISTRICT<input value={district} onChange={(event) => setDistrict(event.target.value)} /></label><label>ACCOUNT TYPE<input value={user?.role ?? "farmer"} readOnly /></label></div><div className="profile-callout"><span>✓</span><div><strong>Your account is protected</strong><p>Authenticated FarmWise data is scoped to your account and is never loaded from a client-supplied user ID.</p></div></div></div></div><aside className="profile-side"><div className="panel completion-card"><span className="ring">✓</span><h3>Member since</h3><p>{user?.created_at ? new Date(user.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "long" }) : "Recently"}</p><small>Role: {user?.role ?? "farmer"}</small></div></aside></div></>;
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
