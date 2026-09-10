"use server";

import { apiFetch } from "@/lib/api";
import { getAccessToken, getHostId } from "@/lib/dal";
import type { AvaSettings } from "@/lib/types";

export async function updateSettings(
  patch: Partial<AvaSettings>,
): Promise<AvaSettings> {
  const [hostId, token] = await Promise.all([getHostId(), getAccessToken()]);
  const data = await apiFetch<{ status: string; settings: AvaSettings }>(
    `/api/settings/${hostId}`,
    token,
    {
      method: "PATCH",
      body: JSON.stringify(patch),
    },
  );
  return data.settings;
}
