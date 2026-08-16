// TODO: BE実装後、apiFetch(`/api/listings/${HOST_ID}`) に差し替える。
// 仕様: doc/api_interface_settings_listings.md
import { mockListings } from "./mock-listings";
import type { Listing } from "./types";

export async function getListings(): Promise<Listing[]> {
  return mockListings;
}
