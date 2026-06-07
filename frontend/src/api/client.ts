import { parseApiError } from "../lib/parse-api-error";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

type AuthTokenGetter = () => Promise<string | null>;

let authTokenGetter: AuthTokenGetter | null = null;

export function setAuthTokenGetter(getter: AuthTokenGetter): void {
  authTokenGetter = getter;
}

export async function apiClient<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);

  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }

  if (authTokenGetter) {
    const token = await authTokenGetter();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    signal: init?.signal,
  });
  if (!res.ok) {
    throw new Error(await parseApiError(res));
  }
  return res.json() as Promise<T>;
}
