import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HealthBadge } from "@/components/HealthBadge";

function renderWithClient(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("HealthBadge", () => {
  it("shows 'API ok' when the backend is healthy", async () => {
    const body = { status: "ok", db: "ok", scheduler: "not_started", version: "0.1.0" };
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify(body), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
      ),
    );

    renderWithClient(<HealthBadge />);
    expect(await screen.findByText("API ok")).toBeInTheDocument();
  });

  it("shows 'API offline' when fetch rejects", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );

    renderWithClient(<HealthBadge />);
    expect(await screen.findByText("API offline")).toBeInTheDocument();
  });
});
