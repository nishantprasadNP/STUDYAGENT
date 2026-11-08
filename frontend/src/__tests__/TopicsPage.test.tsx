import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { TopicOut } from "@/api/types";
import TopicsPage from "@/pages/TopicsPage";

import { json, mockFetch, renderWithClient } from "./utils";

const TOPICS: TopicOut[] = [
  {
    slug: "arrays",
    name: "Arrays",
    category: "linear",
    order_index: 1,
    default_problem_count: 10,
    est_minutes_per_problem: 20,
    difficulty_tier: 1,
    prerequisites: [],
  },
  {
    slug: "sliding-window",
    name: "Sliding Window",
    category: "linear",
    order_index: 2,
    default_problem_count: 8,
    est_minutes_per_problem: 30,
    difficulty_tier: 2,
    prerequisites: ["arrays"],
  },
];

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("TopicsPage", () => {
  it("renders prerequisite names and estimated hours", async () => {
    mockFetch({ "GET /api/topics": () => json(TOPICS) });
    renderWithClient(<TopicsPage />);
    expect(await screen.findByText("Sliding Window")).toBeInTheDocument();
    // "Arrays" appears as a row name and as the prerequisite chip.
    expect(screen.getAllByText("Arrays")).toHaveLength(2);
    expect(screen.getByText("3.3")).toBeInTheDocument(); // 10 × 20 / 60
    expect(screen.getByText("4.0")).toBeInTheDocument(); // 8 × 30 / 60
  });

  it("shows the empty state", async () => {
    mockFetch({ "GET /api/topics": () => json([]) });
    renderWithClient(<TopicsPage />);
    expect(await screen.findByText(/No topics yet/)).toBeInTheDocument();
    expect(screen.getByText("make seed")).toBeInTheDocument();
  });
});
