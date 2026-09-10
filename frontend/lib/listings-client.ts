// 実API接続。仕様: doc/api_interface_settings_listings.md
import { apiFetch } from "./api";
import { getAccessToken, getHostId } from "./dal";
import type { Listing } from "./types";

export async function getListings(): Promise<Listing[]> {
  const [hostId, token] = await Promise.all([getHostId(), getAccessToken()]);
  const data = await apiFetch<{ status: string; listings: Listing[] }>(
    `/api/listings/${hostId}`,
    token,
  );
  return data.listings;
}
