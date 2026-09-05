// 実API接続。仕様: doc/api_interface_settings_listings.md
import { apiFetch, HOST_ID } from "./api";
import type { AvaSettings } from "./types";

export async function getSettings(): Promise<AvaSettings> {
  const data = await apiFetch<{ status: string; settings: AvaSettings }>(
    `/api/settings/${HOST_ID}`,
  );
  return data.settings;
}

export async function updateSettings(
  patch: Partial<AvaSettings>,
): Promise<AvaSettings> {
  const data = await apiFetch<{ status: string; settings: AvaSettings }>(
    `/api/settings/${HOST_ID}`,
    {
      method: "PATCH",
      body: JSON.stringify(patch),
    },
  );
  return data.settings;
}
