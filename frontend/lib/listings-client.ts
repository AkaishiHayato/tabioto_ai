// 実API接続。仕様: doc/api_interface_settings_listings.md
import { apiFetch, HOST_ID } from "./api";
import type { Listing } from "./types";

export async function getListings(): Promise<Listing[]> {
  const data = await apiFetch<{ status: string; listings: Listing[] }>(
    `/api/listings/${HOST_ID}`,
  );
  return data.listings;
}
