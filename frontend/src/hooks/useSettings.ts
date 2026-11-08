import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import type { SettingsOut, SettingsPatch } from "@/api/types";

export const settingsKey = ["settings"] as const;

export function useSettings() {
  return useQuery({ queryKey: settingsKey, queryFn: () => apiFetch<SettingsOut>("/settings") });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (patch: SettingsPatch) =>
      apiFetch<SettingsOut>("/settings", { method: "PATCH", body: JSON.stringify(patch) }),
    onSuccess: (data) => {
      queryClient.setQueryData(settingsKey, data);
    },
  });
}
