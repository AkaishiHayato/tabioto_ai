## Summary

たびおとAI の **Backend（FastAPI + Playwright）** を main にマージする PR です。  
Airbnb 共同ホストとしてのログイン・リスティング同期・メッセージ自動返信・LINE 通知まで、FE 開発に必要な API を一通り揃えています。

**FE 開発者向け**: API 仕様は Swagger UI → http://localhost:8000/docs （OpenAPI JSON → `/openapi.json`）

---

## 主な変更

| 領域 | 内容 |
|---|---|
| **Backend 基盤** | FastAPI、Docker Compose、Supabase 連携、`backend/llm_core` 統合 |
| **認証** | Airbnb ログイン → storageState 暗号化保存（`/api/sessions/*`） |
| **共同ホスト** | 招待承認（`/api/cohost/*`、通常は `/api/listings/sync` 内で処理） |
| **リスティング** | 編集ツール 19 ページ scrape → DB 保存（`/api/listings/*`） |
| **メッセージ** | 未読ポーリング・返信要否判定・自動返信・手動送信（`/api/messages/*`） |
| **LINE 通知** | 一般 / 緊急の 2 チャネル push + Webhook で User ID 自動登録 |
| **OpenAPI** | 全 17 エンドポイントに FE 向け Description・タグ説明を追加 |
| **DB** | `001_initial_schema.sql` + `002_message_threads.sql` |
| **Docs** | `architecture.md`, `listing_editor_fields.md`, `messages_scraping.md` 等 |

---

## FE が使う API 一覧

| Method | Path | 用途 |
|---|---|---|
| GET | `/health` | ヘルスチェック |
| GET | `/api/sessions/validate/{host_id}` | Airbnb セッション有効性 |
| POST | `/api/listings/sync/{host_id}` | **リスティング追加（メインフロー）** |
| GET | `/api/messages/threads/{host_id}` | メッセージスレッド一覧（DB） |
| GET | `/api/messages/threads/{host_id}/{thread_id}` | スレッド詳細 + 履歴 |
| PATCH | `/api/messages/threads/{host_id}/{thread_id}` | 自動返信スキップ |
| POST | `/api/messages/threads/{host_id}/{thread_id}/send` | 手動送信 |
| POST | `/api/messages/poll/{host_id}` | 未読同期（⚠️ 自動返信する場合あり） |
| GET | `/api/line/status/{host_id}` | LINE 連携状態 |

詳細・リクエスト形式・エラーコードは **Swagger UI** を参照してください。

---

## セットアップ（FE / BE 共通）

```bash
cp .env.example .env          # SUPABASE_*, SESSION_ENCRYPTION_KEY を設定
# Supabase SQL Editor で以下を実行:
#   supabase/migrations/001_initial_schema.sql
#   supabase/migrations/002_message_threads.sql
docker compose up -d --build
curl http://localhost:8000/health   # → {"status":"ok"}
```

- API ドキュメント: http://localhost:8000/docs
- Backend README: `backend/README.md`

---

## Test plan

- [ ] `docker compose up -d` → `/health` が `{"status":"ok"}`
- [ ] Supabase migration（001 + 002）適用済み
- [ ] `/docs` で全エンドポイントの Description が表示される
- [ ] `GET /api/sessions/validate/{host_id}` でセッション状態確認
- [ ] `POST /api/listings/sync/{host_id}` でリスティング同期（要 Airbnb セッション）
- [ ] `GET /api/messages/threads/{host_id}` でスレッド一覧取得
- [ ] `GET /api/line/status/{host_id}` で LINE 連携状態確認
- [ ] `.env` / `__pycache__` / `.venv` がコミットされていないこと

---

## 注意事項

- **認証**: MVP は単一ホスト想定。API 認証は未実装
- **`host_id`**: Supabase `hosts.id`（UUID）をパスに使用
- **セッション切れ**: 各 API が `401` を返す → `/api/sessions/login` または CLI 再ログイン
- **`POST /api/messages/poll`**: 本番ゲストへ自動送信される可能性あり。テスト時は注意
- **LINE**: token / Webhook 未設定でも API は動作（通知はスキップ）
