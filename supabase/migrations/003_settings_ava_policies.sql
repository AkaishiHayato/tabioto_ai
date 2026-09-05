-- settings: Avaを設定 画面で必要な項目を追加
-- 開発環境: Supabase SQL Editor で 001, 002 適用後に実行
-- 仕様: doc/api_interface_settings_listings.md

ALTER TABLE settings
  ADD COLUMN reply_delay_minutes INT NOT NULL DEFAULT 0,
  ADD COLUMN late_checkout_policy TEXT NOT NULL DEFAULT 'flexible'
    CHECK (late_checkout_policy IN ('flexible', 'strict')),
  ADD COLUMN luggage_storage_enabled BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN luggage_storage_message TEXT NOT NULL DEFAULT
    'お荷物はチェックイン当日の12:00以降からチェックアウト日の12:00までお預かり可能です。近くの駅のコインロッカーなども便利ですのでご活用ください。',
  ADD COLUMN price_negotiation_policy TEXT NOT NULL DEFAULT 'defer_to_host'
    CHECK (price_negotiation_policy IN ('decline', 'defer_to_host'));

COMMENT ON COLUMN settings.reply_delay_minutes IS '自動返信を送信するまでの遅延（分）。0=即時';
COMMENT ON COLUMN settings.late_checkout_policy IS 'レイトチェックアウトの問い合わせに対する返信方針';
COMMENT ON COLUMN settings.luggage_storage_enabled IS '荷物預かり案内の自動送信を有効にするか';
COMMENT ON COLUMN settings.luggage_storage_message IS '荷物預かり案内としてAIが参照する文面';
COMMENT ON COLUMN settings.price_negotiation_policy IS '価格交渉の問い合わせに対する返信方針';
