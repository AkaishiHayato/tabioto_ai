-- たびおとAI 初期スキーマ
-- Supabase SQL Editor で実行する

-- ============================================================
-- hosts: ホストユーザー (MVP: 1ユーザー)
-- ============================================================
CREATE TABLE hosts (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                    TEXT NOT NULL,
  email                   TEXT UNIQUE NOT NULL,
  line_user_id_general    TEXT,                -- 一般通知用公式LINE チャネル上のホスト User ID
  line_user_id_urgent     TEXT,                -- 緊急通知用公式LINE チャネル上のホスト User ID
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- airbnb_sessions: Playwright storageState (暗号化保存)
-- ============================================================
CREATE TYPE session_status AS ENUM ('active', 'expired', 'pending');

CREATE TABLE airbnb_sessions (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  host_id             UUID NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  encrypted_state     TEXT NOT NULL,           -- AES-256 暗号化された storageState JSON
  status              session_status NOT NULL DEFAULT 'pending',
  last_validated_at   TIMESTAMPTZ,
  expires_at          TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_airbnb_sessions_host_status ON airbnb_sessions(host_id, status);

-- ============================================================
-- listings: スクレイピングしたリスティング情報
-- ============================================================
CREATE TYPE listing_status AS ENUM ('active', 'inactive', 'pending_scrape');

CREATE TABLE listings (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  host_id                 UUID NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  airbnb_listing_id       TEXT NOT NULL,           -- Airbnb 側の listing ID

  -- AI 返信で頻出（トップレベルカラム）
  title                   TEXT,                    -- 日本語タイトル
  description             TEXT,                    -- 説明文（日本語・全セクション結合）
  address                 TEXT,                    -- 所在地（フルアドレス）
  max_guests              INT,                     -- 最大宿泊人数
  check_in_time           TEXT,                    -- 例: "16:00"
  check_out_time          TEXT,                    -- 例: "10:00"
  amenities               JSONB NOT NULL DEFAULT '[]',   -- アメニティ名リスト
  house_rules             JSONB NOT NULL DEFAULT '{}',   -- ペット/喫煙/静穏時間 等

  -- 到着・滞在（AI 返信で頻出）
  directions              TEXT,                    -- 道順（Maps URL 含む）
  check_in                JSONB,                   -- {method, method_description, instructions}
  wifi                    JSONB,                   -- {ssid, password} ※機密
  house_manual            TEXT,
  checkout_instructions   JSONB NOT NULL DEFAULT '[]',

  -- 補完データ（多言語タイトル、物件詳細、scrape エラー等）
  raw_data                JSONB NOT NULL DEFAULT '{}',

  status                  listing_status NOT NULL DEFAULT 'pending_scrape',
  last_scraped_at         TIMESTAMPTZ,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (host_id, airbnb_listing_id)
);

CREATE INDEX idx_listings_host ON listings(host_id);
CREATE INDEX idx_listings_host_status ON listings(host_id, status);

COMMENT ON TABLE listings IS 'Airbnb リスティング編集ツールから scrape した情報';
COMMENT ON COLUMN listings.amenities IS 'アメニティ名の配列。例: ["Wi-Fi", "キッチン"]';
COMMENT ON COLUMN listings.house_rules IS 'ハウスルール object。例: {pets_allowed, quiet_hours, ...}';
COMMENT ON COLUMN listings.check_in IS 'チェックイン方法。例: {method: "キーボックス", method_description: "..."}';
COMMENT ON COLUMN listings.wifi IS 'Wi-Fi 情報。例: {ssid, password}';
COMMENT ON COLUMN listings.checkout_instructions IS 'チェックアウト手順の配列';
COMMENT ON COLUMN listings.raw_data IS '補完 JSON。titles, property_type, location, guest_safety, cancellation, instant_book, guidebooks, amenities_detail, sleeping_arrangements, check_in_end, _errors';

-- ============================================================
-- messages: 受信メッセージ
-- ============================================================
CREATE TYPE message_status AS ENUM (
  'new',              -- 未処理
  'classified',       -- 緊急度判定済み
  'auto_replied',     -- 自動返信済み
  'manual_required',  -- 手動対応必要
  'manual_replied'    -- 手動返信済み
);

CREATE TABLE messages (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id          UUID REFERENCES listings(id) ON DELETE SET NULL,
  host_id             UUID NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  airbnb_thread_id    TEXT NOT NULL,
  airbnb_message_id   TEXT UNIQUE,
  guest_name          TEXT,
  guest_message       TEXT NOT NULL,
  is_urgent           BOOLEAN,
  reply_text          TEXT,
  airbnb_thread_url   TEXT,
  status              message_status NOT NULL DEFAULT 'new',
  received_at         TIMESTAMPTZ,
  processed_at        TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_messages_host_status ON messages(host_id, status);
CREATE INDEX idx_messages_thread ON messages(airbnb_thread_id);

-- ============================================================
-- settings: 自動返信設定
-- ============================================================
CREATE TABLE settings (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  host_id                     UUID UNIQUE NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  poll_interval_minutes       INT NOT NULL DEFAULT 10 CHECK (poll_interval_minutes IN (3, 10, 15)),
  early_checkin_policy        TEXT NOT NULL DEFAULT 'flexible'
                                CHECK (early_checkin_policy IN ('flexible', 'strict')),
  auto_reply_enabled          BOOLEAN NOT NULL DEFAULT true,
  custom_instructions         TEXT,            -- AI に渡す追加指示
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- scrape_logs: スクレイピング実行ログ
-- ============================================================
CREATE TYPE scrape_type AS ENUM ('listings', 'messages', 'auth_check');
CREATE TYPE scrape_result AS ENUM ('success', 'session_expired', 'error');

CREATE TABLE scrape_logs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  host_id         UUID NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  scrape_type     scrape_type NOT NULL,
  result          scrape_result NOT NULL,
  items_found     INT DEFAULT 0,
  error_message   TEXT,
  duration_ms     INT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_scrape_logs_host_created ON scrape_logs(host_id, created_at DESC);

-- ============================================================
-- updated_at 自動更新トリガー
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_hosts_updated_at
  BEFORE UPDATE ON hosts FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_airbnb_sessions_updated_at
  BEFORE UPDATE ON airbnb_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_listings_updated_at
  BEFORE UPDATE ON listings FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_messages_updated_at
  BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_settings_updated_at
  BEFORE UPDATE ON settings FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- MVP 用シードデータ (開発時のみ)
-- ============================================================
-- INSERT INTO hosts (name, email) VALUES ('たくみ', 'takumi@example.com');
-- INSERT INTO settings (host_id) SELECT id FROM hosts LIMIT 1;
