-- hosts: Supabase Auth ユーザーとの紐付け（管理画面ログイン用）
-- 開発環境: Supabase SQL Editor で 001〜003 適用後に実行
-- 仕様: doc/auth_design.md

ALTER TABLE hosts
  ADD COLUMN auth_user_id UUID UNIQUE REFERENCES auth.users(id);

COMMENT ON COLUMN hosts.auth_user_id IS
  '管理画面ログイン用 Supabase Auth ユーザーID（auth.users.id）。JWTのsubクレームと照合してhost_idを解決する';
