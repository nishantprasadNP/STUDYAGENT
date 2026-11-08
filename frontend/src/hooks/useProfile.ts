import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import type { ProfileOut, ProfilePatch, ProfileResponse } from "@/api/types";

export const profileKey = ["profile"] as const;

export function useProfile() {
  return useQuery({ queryKey: profileKey, queryFn: () => apiFetch<ProfileOut>("/profile") });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (patch: ProfilePatch) =>
      apiFetch<ProfileResponse>("/profile", { method: "PATCH", body: JSON.stringify(patch) }),
    onSuccess: (data) => {
      queryClient.setQueryData(profileKey, data.profile);
    },
  });
}
