// TODO: BE実装後、apiFetch(`/api/settings/${HOST_ID}`) に差し替える。
// 仕様: doc/api_interface_settings_listings.md
import { mockAvaSettings } from "./mock-settings";
import type { AvaSettings } from "./types";

let current: AvaSettings = { ...mockAvaSettings };

export async function getSettings(): Promise<AvaSettings> {
  return current;
}

export async function updateSettings(
  patch: Partial<AvaSettings>,
): Promise<AvaSettings> {
  current = {
    ...current,
    ...patch,
    updated_at: new Date().toISOString(),
  };
  return current;
}
