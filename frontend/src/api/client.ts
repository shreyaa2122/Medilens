// Typed API client. Every backend response uses the same envelope:
// { data, error }. These helpers unwrap it so pages only deal with data or an Error.

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: { field: string; issue: string }[] | null;
}

interface ApiEnvelope<T> {
  data: T | null;
  error: ApiErrorBody | null;
}

export class ApiError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

export function unwrapEnvelope<T>(ok: boolean, body: unknown): T {
  const envelope = body as ApiEnvelope<T> | null;
  if (!ok || !envelope || envelope.error || envelope.data === null || envelope.data === undefined) {
    throw new ApiError(
      envelope?.error?.code ?? "unknown_error",
      envelope?.error?.message ?? "The server returned an unexpected response.",
    );
  }
  return envelope.data;
}

async function send(method: string, path: string): Promise<Response> {
  try {
    return await fetch(`${API_BASE_URL}${path}`, { method });
  } catch {
    throw new ApiError("network_error", "Could not reach the MediLens server.");
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await send("GET", path);
  const body = await response.json().catch(() => null);
  return unwrapEnvelope<T>(response.ok, body);
}

export async function apiDelete(path: string): Promise<void> {
  const response = await send("DELETE", path);
  if (response.status === 204) return;
  const body = await response.json().catch(() => null);
  unwrapEnvelope<unknown>(false, body); // always throws with the server's message
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export const getHealth = () => apiGet<HealthStatus>("/health");
