// MOCK: BE実装後 GET/PATCH /api/settings/{host_id} に差し替え。
// 仕様: doc/api_interface_settings_listings.md
import type { AvaSettings } from "./types";

export const mockAvaSettings: AvaSettings = {
  host_id: "mock-host-id",
  auto_reply_enabled: true,
  poll_interval_minutes: 10,
  reply_delay_minutes: 0,
  early_checkin_policy: "flexible",
  late_checkout_policy: "flexible",
  luggage_storage_enabled: false,
  luggage_storage_message:
    "お荷物はチェックイン当日の12:00以降からチェックアウト日の12:00までお預かり可能です。近くの駅のコインロッカーなども便利ですのでご活用ください。",
  price_negotiation_policy: "defer_to_host",
  custom_instructions: null,
  updated_at: "2026-08-01T00:00:00Z",
};
