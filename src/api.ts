const configuredApiBase = import.meta.env.VITE_API_URL?.trim();
const API_BASE = configuredApiBase || "http://127.0.0.1:8000/api/v1";
const API_URL_CONFIGURED = Boolean(configuredApiBase)
  || (typeof window !== "undefined" && ["localhost", "127.0.0.1"].includes(window.location.hostname));

function assertApiConfigured() {
  if (!API_URL_CONFIGURED) {
    throw new Error("FarmWise backend URL is not configured for this deployment. Set VITE_API_URL to your backend URL ending in /api/v1, then rebuild and redeploy the frontend.");
  }
}

export type User = {
  id: number;
  name: string;
  phone: string;
  email?: string | null;
  role: string;
  language?: string;
  location_name?: string | null;
  state?: string | null;
  district?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  created_at?: string | null;
};

export type Farm = {
  id: number;
  land_size_acres: number;
  soil_type: string;
  water_availability: string;
  current_season: string;
  budget: number;
  previous_crop?: string | null;
};

export type ApiCrop = {
  crop_id: number;
  crop: string;
  score: number;
  risk: string;
  expected_profit_per_acre: number;
  reasons: string[];
  explanation: string;
};

export type CropOption = { id: number; name: string };

export type HarvestPayload = {
  crop_id: number;
  quantity_tonnes: number;
  grade: string;
  harvest_date: string;
  notes: string;
  photo_data_url: string;
};

export type ConversationMessage = {
  id: number;
  sender_id: number;
  body: string;
  created_at: string;
  is_mine: boolean;
};

export type Conversation = {
  id: number;
  listing_id: number;
  crop: string;
  photo_data_url: string;
  quantity_tonnes: number;
  other_party: {
    name: string;
    role: string;
    phone?: string | null;
    email?: string | null;
    location_name?: string | null;
    state?: string | null;
    district?: string | null;
    latitude?: number | null;
    longitude?: number | null;
  };
  my_contact_shared: boolean;
  my_location_shared: boolean;
  created_at: string;
  messages: ConversationMessage[];
};

export type FinancialForecast = {
  crop: string;
  farm_acres: number;
  available_budget: number;
  production_budget_required: number;
  budget_after_production: number;
  budget_status: "sufficient" | "shortfall";
  expected_yield_per_acre_kg: number;
  expected_profit_or_loss_per_acre: number;
  confidence: "low" | "medium";
  price_source: string;
  scenarios: Record<"low" | "expected" | "high", {
    expected_yield_kg: number;
    price_per_kg: number;
    gross_revenue: number;
    production_cost: number;
    transport_cost: number;
    market_charges: number;
    total_cost: number;
    profit_or_loss: number;
  }>;
  assumptions: Record<string, string | number>;
};

export type CropListing = {
  id: number;
  harvest_id: number;
  crop: string;
  quantity_tonnes: number;
  grade: string;
  harvest_date: string;
  notes?: string | null;
  photo_data_url: string;
  media_type: string;
  farmer: {
    name: string;
    account_id: number;
    location_name?: string | null;
    state?: string | null;
    district?: string | null;
  };
  created_at: string;
};

export type BuyerProfile = {
  id: number;
  account_id?: number | null;
  name: string;
  business_type: string;
  location_name: string;
  verification_status: string;
  verification_fields: string;
  rating: number;
  phone?: string;
  email?: string | null;
};

export type AccountAlert = {
  type: string;
  severity: string;
  message: string;
};

export type GoogleLoginResult =
  | { phone_required: true; email: string; name: string }
  | { access_token: string; token_type: string; user: User };

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  assertApiConfigured();
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers ?? {}),
      },
    });
  } catch {
    throw new Error("FarmWise API is not reachable. Start the backend locally or configure VITE_API_URL for the deployed app.");
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok && response.status === 404) {
    throw new Error(`FarmWise API route was not found (${path}). Check that VITE_API_URL points to the backend and ends with /api/v1.`);
  }
  if (!response.ok)
    throw new Error(
      body?.detail?.message ??
        body?.detail ??
        body?.message ??
        "Request failed",
    );
  return body.data ?? body;
}

export const api = {
  health: async () => {
    assertApiConfigured();
    const backendBase = API_BASE.replace(/\/api\/v1\/?$/, "");
    let response: Response;
    try {
      response = await fetch(`${backendBase}/health`);
    } catch {
      throw new Error("FarmWise backend is not reachable");
    }
    if (!response.ok) throw new Error(`FarmWise backend health check failed (${response.status})`);
    const result: unknown = await response.json();
    if (!result || typeof result !== "object" || !("status" in result) || result.status !== "ok") {
      throw new Error("FarmWise backend is unhealthy");
    }
    return true;
  },
  login: (identifier: string, password: string) =>
    request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier, password }),
    }),
  googleLogin: (credential: string, phone?: string) =>
    request<GoogleLoginResult>("/auth/google", {
      method: "POST",
      body: JSON.stringify({ credential, phone }),
    }),
  register: (payload: {
    name: string;
    phone: string;
    email: string;
    password: string;
    confirm_password: string;
    role: string;
    state: string;
    district: string;
  }) =>
    request<{ access_token: string; user: User }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  me: (token: string) => request<User>("/auth/me", {}, token),
  updateProfile: (payload: { name: string; language: string; location_name?: string | null; state?: string | null; district?: string | null; latitude?: number | null; longitude?: number | null }, token: string) => request<User>("/farmers/profile", { method: "PUT", body: JSON.stringify(payload) }, token),
  farms: (token: string) => request<Farm[]>("/farms", {}, token),
  harvests: (token: string) => request<Array<{ id: number; crop_id: number; crop: string; quantity_tonnes: number; grade: string; harvest_date: string; notes?: string | null; is_listed: boolean }>>("/harvests", {}, token),
  alerts: (token: string) => request<AccountAlert[]>("/alerts", {}, token),
  createFarm: (payload: Omit<Farm, "id">, token: string) => request<Farm>("/farms", { method: "POST", body: JSON.stringify(payload) }, token),
  updateFarm: (id: number, payload: Omit<Farm, "id">, token: string) => request<Farm>(`/farms/${id}`, { method: "PUT", body: JSON.stringify(payload) }, token),
  recommendations: (farmId: number, token: string) =>
    request<{ recommendations: ApiCrop[] }>(
      `/recommendations/crops`,
      { method: "POST", body: JSON.stringify({ farm_id: farmId }) },
      token,
    ),
  financialForecast: (cropId: number, token: string, farmId?: number) =>
    request<FinancialForecast>(
      "/dashboard/financial-forecast",
      { method: "POST", body: JSON.stringify({ crop_id: cropId, farm_id: farmId }) },
      token,
    ),
  crops: (token: string) =>
    request<CropOption[]>("/crops", {}, token),
  createHarvest: (payload: HarvestPayload, token: string) =>
    request<{ id: number; crop_id: number; quantity_tonnes: number; grade: string; harvest_date: string; is_listed: boolean }>(
      "/harvests",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    ),
  cropListings: (token: string) =>
    request<CropListing[]>("/marketplace/listings", {}, token),
  conversations: (token: string) => request<Conversation[]>("/conversations", {}, token),
  startConversation: (payload: { listing_id: number; buyer_user_id?: number; message: string; share_my_contact: boolean; share_my_location: boolean }, token: string) =>
    request<Conversation>("/conversations", { method: "POST", body: JSON.stringify(payload) }, token),
  replyConversation: (id: number, payload: { message: string; share_my_contact: boolean; share_my_location: boolean }, token: string) =>
    request<Conversation>(`/conversations/${id}/messages`, { method: "POST", body: JSON.stringify(payload) }, token),
  markets: () =>
    request<Array<{ id: number; name: string; location_name: string }>>(
      "/markets",
    ),
  buyers: () => request<BuyerProfile[]>("/buyers"),
  getInterfaceTranslations: (language: string) =>
    request<Record<string, string>>(`/translate/interface-strings/${language}`),
};

export function saveToken(token: string) {
  localStorage.setItem("farmwise_access_token", token);
}
export function getToken() {
  return localStorage.getItem("farmwise_access_token");
}
export function clearToken() {
  localStorage.removeItem("farmwise_access_token");
}
