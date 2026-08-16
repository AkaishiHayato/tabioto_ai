// MOCK: BE実装後 GET /api/listings/{host_id} に差し替え。
// 仕様: doc/api_interface_settings_listings.md
import type { Listing } from "./types";

export const mockListings: Listing[] = [
  {
    id: "8f1c2b3a-0000-0000-0000-000000000001",
    airbnb_listing_id: "1564264295874414302",
    title:
      "【博多駅徒歩10分/最大6名】新幹線・地下鉄Wアクセス｜空港好アクセス｜移動ストレスゼロの快適拠点",
    address: "812-0011, Fukuoka, Hakata Ekimae, Japan",
    max_guests: 6,
    check_in_time: "16:00",
    check_out_time: "10:00",
    status: "active",
    last_scraped_at: "2026-08-10T03:20:00Z",
  },
  {
    id: "8f1c2b3a-0000-0000-0000-000000000002",
    airbnb_listing_id: "1598223391004512871",
    title: "【天神駅徒歩5分】都心の隠れ家スタジオ｜ワーケーション向け",
    address: "810-0001, Fukuoka, Tenjin, Japan",
    max_guests: 2,
    check_in_time: "15:00",
    check_out_time: "11:00",
    status: "active",
    last_scraped_at: "2026-08-09T21:05:00Z",
  },
  {
    id: "8f1c2b3a-0000-0000-0000-000000000003",
    airbnb_listing_id: "1612207743398821904",
    title: "【中洲川端】屋台街まで徒歩3分の夜景ビュールーム",
    address: "810-0002, Fukuoka, Nakasu, Japan",
    max_guests: 4,
    check_in_time: null,
    check_out_time: null,
    status: "pending_scrape",
    last_scraped_at: null,
  },
];
