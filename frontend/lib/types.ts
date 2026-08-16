// BE レスポンス形状。doc/api_interface_settings_listings.md と
// backend/app/api/routes/messages.py に対応。

export type MessageThread = {
  id: string;
  host_id: string;
  listing_id: string | null;
  airbnb_thread_id: string;
  airbnb_listing_id: string | null;
  guest_name: string | null;
  thread_title: string | null;
  reservation_status: string | null;
  last_message_at: string | null;
  last_sender_role: "guest" | "host" | "cohost" | "system" | "other" | null;
  last_sender_name: string | null;
  last_message_preview: string | null;
  skip_auto_reply: boolean;
  last_polled_at: string | null;
  created_at: string;
  updated_at: string;
};

export type MessageStatus =
  | "new"
  | "classified"
  | "auto_replied"
  | "manual_required"
  | "manual_replied";

export type Message = {
  id: string;
  listing_id: string | null;
  host_id: string;
  airbnb_thread_id: string;
  airbnb_message_id: string | null;
  guest_name: string | null;
  guest_message: string;
  is_urgent: boolean | null;
  reply_text: string | null;
  status: MessageStatus;
  received_at: string | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ListingStatus = "active" | "inactive" | "pending_scrape";

export type Listing = {
  id: string;
  airbnb_listing_id: string;
  title: string | null;
  address: string | null;
  max_guests: number | null;
  check_in_time: string | null;
  check_out_time: string | null;
  status: ListingStatus;
  last_scraped_at: string | null;
};

export type CheckinOutPolicy = "flexible" | "strict";
export type PriceNegotiationPolicy = "decline" | "defer_to_host";

export type AvaSettings = {
  host_id: string;
  auto_reply_enabled: boolean;
  poll_interval_minutes: 3 | 10 | 15;
  reply_delay_minutes: number;
  early_checkin_policy: CheckinOutPolicy;
  late_checkout_policy: CheckinOutPolicy;
  luggage_storage_enabled: boolean;
  luggage_storage_message: string;
  price_negotiation_policy: PriceNegotiationPolicy;
  custom_instructions: string | null;
  updated_at: string;
};
