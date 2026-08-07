-- ⚠️ 開発環境専用: たびおとAI スキーマをすべて削除する
-- 本番では絶対に実行しないこと
--
-- 使い方:
--   1. Supabase SQL Editor でこのファイルを実行
--   2. 続けて 001_initial_schema.sql を実行
--   3. hosts / settings を再シード
--   4. login_cli で Airbnb セッションを再保存

-- トリガー
DROP TRIGGER IF EXISTS trg_settings_updated_at ON settings;
DROP TRIGGER IF EXISTS trg_messages_updated_at ON messages;
DROP TRIGGER IF EXISTS trg_listings_updated_at ON listings;
DROP TRIGGER IF EXISTS trg_airbnb_sessions_updated_at ON airbnb_sessions;
DROP TRIGGER IF EXISTS trg_hosts_updated_at ON hosts;

-- テーブル（依存関係の子 → 親）
DROP TABLE IF EXISTS scrape_logs CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS listings CASCADE;
DROP TABLE IF EXISTS settings CASCADE;
DROP TABLE IF EXISTS airbnb_sessions CASCADE;
DROP TABLE IF EXISTS hosts CASCADE;

-- ENUM 型
DROP TYPE IF EXISTS scrape_result CASCADE;
DROP TYPE IF EXISTS scrape_type CASCADE;
DROP TYPE IF EXISTS message_status CASCADE;
DROP TYPE IF EXISTS listing_status CASCADE;
DROP TYPE IF EXISTS session_status CASCADE;

-- トリガー関数（他プロジェクトと共有していなければ削除可）
DROP FUNCTION IF EXISTS update_updated_at() CASCADE;
