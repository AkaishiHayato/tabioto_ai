-- message_threads: スレッド状態管理（ポーリング・FE 設定用）
-- 開発環境: Supabase SQL Editor で 001 適用後に実行

CREATE TABLE message_threads (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  host_id               UUID NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  listing_id            UUID REFERENCES listings(id) ON DELETE SET NULL,
  airbnb_thread_id      TEXT NOT NULL,
  airbnb_listing_id     TEXT,
  guest_name            TEXT,
  thread_title          TEXT,
  reservation_status    TEXT,
  last_message_at       TIMESTAMPTZ,
  last_sender_role      TEXT CHECK (last_sender_role IN ('guest', 'host', 'cohost', 'system', 'other')),
  last_sender_name      TEXT,
  last_message_preview  TEXT,
  last_message_hash     TEXT,
  skip_auto_reply       BOOLEAN NOT NULL DEFAULT false,
  last_polled_at        TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (host_id, airbnb_thread_id)
);

CREATE INDEX idx_message_threads_host ON message_threads(host_id);
CREATE INDEX idx_message_threads_listing ON message_threads(listing_id);
CREATE INDEX idx_message_threads_skip ON message_threads(host_id, skip_auto_reply);

COMMENT ON TABLE message_threads IS 'Airbnb メッセージスレッドのポーリング状態';
COMMENT ON COLUMN message_threads.skip_auto_reply IS 'true の場合、自動返信しない（FE 手動対応）';
COMMENT ON COLUMN message_threads.last_message_hash IS '最新メッセージ本文の fingerprint（重複検知）';

CREATE TRIGGER trg_message_threads_updated_at
  BEFORE UPDATE ON message_threads FOR EACH ROW EXECUTE FUNCTION update_updated_at();
