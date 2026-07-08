import { useAuthStore } from "../stores/auth";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function buildQuery(params = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      query.append(key, value);
    }
  }
  const str = query.toString();
  return str ? `?${str}` : "";
}

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === "string" ? detail : "Request failed");
    this.status = status;
    this.detail = detail;
  }
}

export async function apiFetch(path, { method = "GET", body, auth = true } = {}) {
  const authStore = useAuthStore();
  const headers = { "Content-Type": "application/json" };
  if (auth && authStore.token) {
    headers.Authorization = `Bearer ${authStore.token}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && auth) {
    authStore.logout();
    window.location.href = "/login";
    throw new ApiError(401, "Session expired");
  }

  const data = response.status === 204 ? null : await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(response.status, data?.detail);
  }

  return data;
}
