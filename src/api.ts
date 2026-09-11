const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

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

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
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
  login: (identifier: string, password: string) =>
    request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier, password }),
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
  updateProfile: (payload: { name: string; language: string; location_name?: string | null; state?: string | null; district?: string | null }, token: string) => request<User>("/farmers/profile", { method: "PUT", body: JSON.stringify(payload) }, token),
  farms: (token: string) => request<Farm[]>("/farms", {}, token),
  createFarm: (payload: Omit<Farm, "id">, token: string) => request<Farm>("/farms", { method: "POST", body: JSON.stringify(payload) }, token),
  updateFarm: (id: number, payload: Omit<Farm, "id">, token: string) => request<Farm>(`/farms/${id}`, { method: "PUT", body: JSON.stringify(payload) }, token),
  recommendations: (farmId: number, token: string) =>
    request<{ recommendations: ApiCrop[] }>(
      `/recommendations/crops`,
      { method: "POST", body: JSON.stringify({ farm_id: farmId }) },
      token,
    ),
  markets: () =>
    request<Array<{ id: number; name: string; location_name: string }>>(
      "/markets",
    ),
  buyers: () =>
    request<
      Array<{
        id: number;
        name: string;
        business_type: string;
        location_name: string;
        verification_status: string;
      }>
    >("/buyers"),
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
