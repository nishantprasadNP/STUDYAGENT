import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import type { TopicOut } from "@/api/types";

export function useTopics() {
  return useQuery({ queryKey: ["topics"], queryFn: () => apiFetch<TopicOut[]>("/topics") });
}
