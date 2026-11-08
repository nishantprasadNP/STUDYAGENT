/** Single entry point for every backend call. Components never build URLs themselves. */

const BASE_URL: string = import.meta.env.VITE_API_URL ?? "/api";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Field-level validation messages keyed by dotted path, e.g. "weekly_availability.mon". */
export type FieldErrors = Record<string, string>;

interface ErrorEnvelope {
  ok: false;
  error: { code: string; message: string; details?: unknown };
}

interface SuccessEnvelope<T> {
  ok: true;
  data: T;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  return isRecord(value) && value.ok === false && isRecord(value.error);
}

function isSuccessEnvelope<T>(value: unknown): value is SuccessEnvelope<T> {
  return isRecord(value) && value.ok === true && "data" in value;
}

/** FastAPI/Pydantic 422: {"detail": [{"loc": ["body", ...], "msg": "..."}]} */
function pydanticFieldErrors(body: unknown): FieldErrors | null {
  if (!isRecord(body) || !Array.isArray(body.detail)) return null;
  const fields: FieldErrors = {};
  for (const item of body.detail) {
    if (!isRecord(item)) continue;
    const loc = Array.isArray(item.loc) ? item.loc.map(String) : [];
    const path = (loc[0] === "body" ? loc.slice(1) : loc).join(".");
    const msg = typeof item.msg === "string" ? item.msg.replace(/^Value error, /, "") : "Invalid";
    if (!(path in fields)) fields[path] = msg;
  }
  return fields;
}

function envelopeError(status: number, body: ErrorEnvelope): ApiError {
  const { code, message } = body.error;
  const details: Record<string, unknown> = isRecord(body.error.details)
    ? { ...body.error.details }
    : {};
  const fields: FieldErrors = {};
  if (typeof details.field === "string") fields[details.field] = message;
  return new ApiError(status, code, message, { ...details, fields });
}

/** Field errors carried by an ApiError (empty object for anything else). */
export function fieldErrorsOf(error: unknown): FieldErrors {
  if (!(error instanceof ApiError) || !isRecord(error.details)) return {};
  const fields = error.details.fields;
  return isRecord(fields) ? (fields as FieldErrors) : {};
}

function parseJson(text: string): unknown {
  if (!text) return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return undefined;
  }
}

/**
 * Fetch JSON from the API. Handles both plain JSON (e.g. /health) and the
 * `{ok, data | error}` envelope used by agent tools in later phases.
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  if (init?.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  const body = parseJson(await response.text());

  if (isErrorEnvelope(body)) throw envelopeError(response.status, body);

  if (!response.ok) {
    const fields = response.status === 422 ? pydanticFieldErrors(body) : null;
    if (fields) {
      const first = Object.values(fields)[0] ?? "Validation failed";
      throw new ApiError(response.status, "VALIDATION_FAILED", first, { fields });
    }
    throw new ApiError(response.status, "HTTP_ERROR", response.statusText);
  }

  if (isSuccessEnvelope<T>(body)) return body.data;
  return body as T;
}
