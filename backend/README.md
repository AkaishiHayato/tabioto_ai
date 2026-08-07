# Backend（たびおとAI）

FastAPI + Playwright による API サーバー。Airbnb スクレイピング、Supabase 連携、LLM 呼び出しを担う。

## 構成

```
backend/
├── app/
│   ├── main.py              # FastAPI エントリポイント
│   ├── config.py            # 環境変数
│   ├── api/routes/          # REST エンドポイント
│   ├── db/                  # Supabase クライアント・セッション暗号化
│   └── scraper/             # Playwright（認証・リスティング・メッセージ）
│       ├── auth/            # ログイン・セッション
│       ├── cohost/          # 共同ホスト招待
│       ├── listing/         # リスティング編集ツール scrape
│       │   ├── pages/       # details / arrival 各ページ
│       │   ├── scrape.py    # LISTING_SCRAPERS オーケストレーション
│       │   └── discovery.py
│       ├── cli/             # login, inspect 等の CLI
│       ├── browser.py
│       └── listings.py      # DB 保存オーケストレーション
├── llm_core/
│   ├── client.py            # classify_message / generate_reply
│   ├── prompts/
│   └── eval/                # LangSmith eval
├── Dockerfile
└── pyproject.toml
```

## 前提

- Docker / Docker Compose
- Supabase プロジェクト（スキーマ適用済み）

## 環境構築

### 1. ルートの `.env` を用意

Backend は **リポジトリルート** の `.env` を参照する（`docker-compose.yml` 経由）。

```bash
# リポジトリルートで
cp .env.example .env
```

| 変数 | 必須 | 説明 |
|---|---|---|
| `SUPABASE_URL` | ✅ | `https://<project-id>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Settings → API Keys → Secret keys |
| `SESSION_ENCRYPTION_KEY` | ✅ | `openssl rand -hex 32` で生成 |
| `GEMINI_API_KEY` | 後で | LLM 利用時 |
| `LINE_GENERAL_CHANNEL_ACCESS_TOKEN` | 後で | 一般通知用公式 LINE |
| `LINE_URGENT_CHANNEL_ACCESS_TOKEN` | 後で | 緊急通知用公式 LINE |

> `SUPABASE_URL` をブラウザで開くと `{"error":"requested path is invalid"}` が返るが、API ベース URL として正常。

### 2. Supabase スキーマ適用

Supabase Dashboard → SQL Editor で以下を実行:

```
supabase/migrations/001_initial_schema.sql
```

**`relation "hosts" already exists` と出た場合**（旧スキーマが残っている）:

```
supabase/reset_dev.sql              -- 開発環境のみ: 全テーブル削除
supabase/migrations/001_initial_schema.sql
```

削除されるデータ: hosts、Airbnb セッション、listings、messages 等 **すべて**。  
削除後は host シードの再投入と `app.scraper.cli.login` による再ログインが必要です。

`listings` テーブル設計の詳細: [doc/listing_editor_structure.md](../doc/listing_editor_structure.md#db-保存方針)

開発用シード（任意）:

```sql
INSERT INTO hosts (name, email) VALUES ('たくみ', 'takumi@example.com');
INSERT INTO settings (host_id) SELECT id FROM hosts LIMIT 1;
```

### 3. Docker で起動（推奨）

```bash
# リポジトリルートで
docker compose up -d --build
```

- API: [http://localhost:8000](http://localhost:8000)
- ヘルスチェック: `curl http://localhost:8000/health`

ログ確認・停止:

```bash
docker compose logs -f backend
docker compose down
```

`app/` と `llm_core/` は volume mount されているため、コード変更は自動リロードされる。  
`PYTHONDONTWRITEBYTECODE=1` を設定しているため、ホスト側に `__pycache__` は生成されない。

### 4. ローカル Python で起動（任意）

Docker を使わない場合:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium

# リポジトリルートの .env を読み込む
cd .. && uvicorn app.main:app --reload --app-dir backend
```

## システムアカウント準備（初回のみ・手動）

たびおとAI が Airbnb 上で動作するための **システム用 Airbnb アカウント**（共同ホスト）を用意する。  
以下は **初回セットアップ時に1回だけ手動で行う** 作業。自動化対象外。

### 必要な作業一覧

| # | 作業 | 方法 | 備考 |
|---|---|---|---|
| 1 | Airbnb アカウント作成 | 手動 | システム専用メールで作成 |
| 2 | ログイン | 自動化可 | `cli.login automated` |
| 3 | 補助ホスト招待の承認 | 半自動 | 通知 → accept-invite →「招待を承認」 |
| 4 | **本人確認（身分証明書 + 自撮り）** | **手動** | 「招待を承認」後に遷移 |

### 本人確認フロー（確認済み 2026-03）

「招待を承認」クリック後、本人確認未完了のアカウントは以下に遷移する:

```
https://www.airbnb.jp/account-fov?user_context=COHOST_INVITATION
```

画面: **「政府発行の身分証明書をご登録ください」**

1. 「身分証明書を登録」をクリック
2. 運転免許証（またはパスポート等）をアップロード
3. 自撮り写真を送信
4. Airbnb による本人確認完了を待つ

> 本人確認完了までは「招待を承認」ボタンが表示されても、承認処理が完了しない。

### 補助ホスト招待フロー（確認済み 2026-03）

```
1. ホストがシステムアカウントを補助ホスト（フル権限）として招待
2. https://www.airbnb.jp/notifications に通知が届く
3. 通知クリック → /co-hosting/accept-invite?code=XXX&listingType=STAY
4. 「招待を承認」をクリック
5. （初回）/account-fov?user_context=COHOST_INVITATION → 本人確認を完了
6. 共同ホストとしてリスティングにアクセス可能に
```

API（本人確認・ホスト初期設定完了後）:

```bash
# 通知から未承認招待をすべて承認
curl -X POST http://localhost:8000/api/cohost/accept/{host_id}

# URL 直接指定
curl -X POST http://localhost:8000/api/cohost/accept/{host_id}/url \
  -H "Content-Type: application/json" \
  -d '{"invite_url":"https://www.airbnb.jp/co-hosting/accept-invite?code=XXX&listingType=STAY"}'
```

---

## Airbnb 認証（storageState）

Airbnb ログインは CAPTCHA / 2FA があるため、**ブラウザ表示の interactive ログイン（推奨）** を用意している。

### 事前準備: host_id を取得

Supabase SQL Editor でシードしていない場合:

```sql
INSERT INTO hosts (name, email) VALUES ('たくみ', 'takumi@example.com');
INSERT INTO settings (host_id) SELECT id FROM hosts LIMIT 1;
```

Table Editor → `hosts` の `id`（UUID）をコピーする。

### 確認済み Airbnb ログインフロー（2026-03）

```
① /login → #phone-or-email にメール → 「続行」
② OTP 画面（#otp-code-input）→ 「別の方法を試す」  ⚠️「新しいコードを送信」は押さない
③ モーダル → 「パスワードを入力」
④ パスワード入力 → 「続行」
⑤ /hosting/listings でログイン確認
```

⑤ /hosting/listings でログイン確認
```

### 補助ホスト招待フロー（確認済み 2026-03）

```
1. https://www.airbnb.jp/notifications に招待通知が届く
2. 通知をクリック
3. /co-hosting/accept-invite?code=XXX&listingType=STAY に遷移
4. 「招待を承認」ボタンをクリック
5. （初回）本人確認 → /account-fov?user_context=COHOST_INVITATION
6. フル権限で共同ホストになる
```

### 方法 A: CLI interactive ログイン（推奨）

Docker コンテナ内では headless になるため、**ローカル Python** で実行する。

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
playwright install chromium

# .env に AIRBNB_LOGIN_EMAIL / AIRBNB_LOGIN_PASSWORD を設定（任意・自動入力用）
python -m app.scraper.cli.login --host-id <HOST_UUID> interactive
```

1. Chromium が起動し Airbnb ログイン画面が開く
2. CAPTCHA / 2FA があれば手動で完了
3. ホスティング画面に到達すると storageState を Supabase に自動保存

その他の CLI コマンド:

```bash
# 自動ログイン（CAPTCHA なしの場合のみ）
python -m app.scraper.cli.login --host-id <HOST_UUID> automated

# セッション検証
python -m app.scraper.cli.login --host-id <HOST_UUID> validate

# Playwright が保存した JSON をインポート
python -m app.scraper.cli.login --host-id <HOST_UUID> import ./state.json
```

### 方法 B: API

| Method | Path | 説明 |
|---|---|---|
| POST | `/api/sessions/login` | 自動ログイン（CAPTCHA 時は 428） |
| POST | `/api/sessions/login/interactive` | headless interactive（CLI 推奨） |
| POST | `/api/sessions/import` | storageState JSON インポート |
| GET | `/api/sessions/validate/{host_id}` | セッション有効性確認 |

```bash
curl -X POST http://localhost:8000/api/sessions/login \
  -H "Content-Type: application/json" \
  -d '{"host_id":"<HOST_UUID>","email":"...","password":"..."}'

curl http://localhost:8000/api/sessions/validate/<HOST_UUID>
```

### リスティング同期（FE 向け）

管理画面の「リスティング同期」ボタンから呼ぶ。共同ホスト参画 → scrape → メッセージルーム取得（未実装は空）を 1 リクエストで実行。

```bash
# 招待 URL から追加（初回）
curl -X POST http://localhost:8000/api/listings/sync/<HOST_UUID> \
  -H "Content-Type: application/json" \
  -d '{"invite_url":"https://www.airbnb.jp/co-hosting/accept-invite?code=XXX&listingType=STAY"}'

# 承認済み + listing ID 指定（再同期）
curl -X POST http://localhost:8000/api/listings/sync/<HOST_UUID> \
  -H "Content-Type: application/json" \
  -d '{"airbnb_listing_id":"1564264295874414302"}'
```

### リスティングスクレイピング（運用・一括）

編集ツールの保存対象 19 ページから、タイトル・説明文・アメニティ・チェックイン情報・Wi-Fi 等を取得して DB に保存する。

```bash
# 全リスティング
curl -X POST http://localhost:8000/api/listings/scrape/<HOST_UUID>

# 単一リスティング
curl -X POST http://localhost:8000/api/listings/scrape/<HOST_UUID>/1564264295874414302
```

取得フィールド詳細: [doc/listing_editor_fields.md](../doc/listing_editor_fields.md)

## API エンドポイント

| Method | Path | 説明 |
|---|---|---|
| GET | `/health` | ヘルスチェック |
| POST | `/api/sessions/login` | Airbnb 自動ログイン |
| POST | `/api/sessions/import` | storageState インポート |
| GET | `/api/sessions/validate/{host_id}` | セッション有効性確認 |
| POST | `/api/listings/sync/{host_id}` | リスティング追加・同期（FE 向け） |
| POST | `/api/listings/scrape/{host_id}` | リスティング一覧 + 詳細スクレイピング |
| POST | `/api/listings/scrape/{host_id}/{listing_id}` | 単一リスティングの詳細スクレイピング |

OpenAPI ドキュメント: [http://localhost:8000/docs](http://localhost:8000/docs)

## Supabase 接続確認

```bash
docker compose exec backend python -c "
from app.db.client import get_supabase
print(get_supabase().table('hosts').select('id').execute())
"
```

## LLM（llm_core）

### 使い方

```python
from llm_core.client import classify_message, generate_reply

is_urgent = classify_message("チェックインは何時ですか？")
reply = generate_reply("チェックインは何時ですか？", listing_info="チェックイン 15:00")
```

### eval（LangSmith）

```bash
cd backend
pip install -e ".[eval]"
python -m llm_core.eval.upload      # データセットアップロード
python -m llm_core.eval.evaluate    # eval 実行
```

詳細: [doc/llm_design.md](../doc/llm_design.md)

## 関連ドキュメント

- [アーキテクチャ設計](../doc/architecture.md) — 認証・スクレイピング・LINE 通知
- [LLM 設計](../doc/llm_design.md) — プロンプト・eval 方針
