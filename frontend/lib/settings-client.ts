// 実API接続。仕様: doc/api_interface_settings_listings.md
// 初期表示（Server Component）用。保存(PATCH)は app/actions/settings.ts の Server Action を使う。
import { apiFetch } from "./api";
import { getAccessToken, getHostId } from "./dal";
import type { AvaSettings } from "./types";

export async function getSettings(): Promise<AvaSettings> {
  const [hostId, token] = await Promise.all([getHostId(), getAccessToken()]);
  const data = await apiFetch<{ status: string; settings: AvaSettings }>(
    `/api/settings/${hostId}`,
    token,
  );
  return data.settings;
}
