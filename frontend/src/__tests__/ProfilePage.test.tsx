import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ProfileOut } from "@/api/types";
import ProfilePage from "@/pages/ProfilePage";

import { json, mockFetch, renderWithClient } from "./utils";

const BASE: ProfileOut = {
  id: 1,
  name: "",
  timezone: "Asia/Kolkata",
  goal_text: null,
  target_date: null,
  skill_level: null,
  weekly_availability: { mon: 0, tue: 0, wed: 0, thu: 0, fri: 0, sat: 0, sun: 0 },
  preferred_session_minutes: null,
  checkin_time: "21:00",
  reminder_time: "22:30",
  preferences: {},
  is_complete: false,
  missing_fields: ["name", "target_date", "skill_level", "weekly_availability"],
  created_at: "2026-11-08T00:00:00Z",
  updated_at: "2026-11-08T00:00:00Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ProfilePage", () => {
  it("lists missing fields in the setup banner", async () => {
    mockFetch({ "GET /api/profile": () => json(BASE) });
    renderWithClient(<ProfilePage />);
    expect(
      await screen.findByText(
        "Finish your profile to create a study plan. Missing: name, target date, skill level, weekly availability",
      ),
    ).toBeInTheDocument();
  });

  it("shows no banner when the profile is complete", async () => {
    mockFetch({
      "GET /api/profile": () => json({ ...BASE, name: "N", is_complete: true, missing_fields: [] }),
    });
    renderWithClient(<ProfilePage />);
    await screen.findByLabelText("Name");
    expect(screen.queryByText(/Finish your profile/)).not.toBeInTheDocument();
  });

  it("shows a domain 422 message under the reminder input", async () => {
    mockFetch({
      "GET /api/profile": () => json(BASE),
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
    const user = userEvent.setup();
    renderWithClient(<ProfilePage />);
    const checkin = await screen.findByLabelText("Check-in time");
    await user.clear(checkin);
    await user.type(checkin, "23:00");
    await user.click(screen.getByRole("button", { name: "Save" }));

    const message = await screen.findByText(
      "reminder_time must be later than checkin_time on the same day",
    );
    expect(message).toHaveAttribute("id", "reminder_time-error");
  });

  it("sends only the changed fields", async () => {
    const fetchMock = mockFetch({
      "GET /api/profile": () => json(BASE),
      "PATCH /api/profile": (init) => {
        const patch = JSON.parse(String(init?.body)) as Record<string, unknown>;
        return json({
          profile: { ...BASE, ...patch, updated_at: "2026-11-08T01:00:00Z" },
          changed_fields: Object.keys(patch).sort(),
          plan_impact: {
            availability_or_deadline_changed: "weekly_availability" in patch,
            active_plan_now_invalid: false,
            violations: [],
          },
        });
      },
    });
    const user = userEvent.setup();
    renderWithClient(<ProfilePage />);

    const save = await screen.findByRole("button", { name: "Save" });
    expect(save).toBeDisabled();

    await user.type(screen.getByLabelText("Name"), "Niya");
    const sat = screen.getByLabelText("Sat");
    await user.clear(sat);
    await user.type(sat, "240");
    expect(screen.getByText("240 → 4 h")).toBeInTheDocument();
    await user.click(save);

    await waitFor(() => {
      expect(screen.getByText(/Saved/)).toBeInTheDocument();
    });
    const patchCall = fetchMock.mock.calls.find(([, init]) => init?.method === "PATCH");
    expect(JSON.parse(String(patchCall?.[1]?.body))).toEqual({
      name: "Niya",
      weekly_availability: { mon: 0, tue: 0, wed: 0, thu: 0, fri: 0, sat: 240, sun: 0 },
    });
    expect(screen.getByText(/Your study plan may need a revision/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("blocks save on invalid preferences JSON", async () => {
    mockFetch({ "GET /api/profile": () => json(BASE) });
    const user = userEvent.setup();
    renderWithClient(<ProfilePage />);
    const prefs = await screen.findByLabelText("Preferences (JSON)");
    await user.clear(prefs);
    await user.type(prefs, "not json");
    expect(screen.getByText("Invalid JSON")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });
});
