import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch, fieldErrorsOf } from "@/api/client";

import { json, mockFetch } from "./utils";

afterEach(() => {
  vi.unstubAllGlobals();
});

async function catchError(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (e) {
    if (e instanceof ApiError) return e;
    throw e;
  }
  throw new Error("expected ApiError");
}

describe("apiFetch error mapping", () => {
  it("maps Pydantic 422 detail to details.fields by dotted path", async () => {
    mockFetch({
      "PATCH /api/profile": () =>
        json(
          {
            detail: [
              {
                loc: ["body", "weekly_availability", "mon"],
                msg: "Input should be less than or equal to 720",
                type: "less_than_equal",
              },
              { loc: ["body", "timezone"], msg: "Value error, invalid timezone", type: "x" },
            ],
          },
          422,
        ),
    });
    const err = await catchError(apiFetch("/profile", { method: "PATCH", body: "{}" }));
    expect(err.status).toBe(422);
    expect(err.code).toBe("VALIDATION_FAILED");
    expect(fieldErrorsOf(err)).toEqual({
      "weekly_availability.mon": "Input should be less than or equal to 720",
      timezone: "invalid timezone",
    });
  });

  it("maps the domain error envelope to details.fields", async () => {
    mockFetch({
      "PATCH /api/profile": () =>
        json(
          {
            ok: false,
            error: {
              code: "VALIDATION_FAILED",
              message: "reminder_time must be later than checkin_time on the same day",
              details: { field: "reminder_time" },
            },
          },
          422,
        ),
    });
    const err = await catchError(apiFetch("/profile", { method: "PATCH", body: "{}" }));
    expect(err.code).toBe("VALIDATION_FAILED");
    expect(err.message).toBe("reminder_time must be later than checkin_time on the same day");
    expect(err.details).toMatchObject({ field: "reminder_time" });
    expect(fieldErrorsOf(err)).toEqual({
      reminder_time: "reminder_time must be later than checkin_time on the same day",
    });
  });

  it("falls back to HTTP_ERROR for other failures", async () => {
    mockFetch({ "GET /api/x": () => new Response("boom", { status: 500, statusText: "Server" }) });
    const err = await catchError(apiFetch("/x"));
    expect(err.code).toBe("HTTP_ERROR");
    expect(fieldErrorsOf(err)).toEqual({});
  });
});
