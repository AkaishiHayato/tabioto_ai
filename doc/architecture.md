# たびおとAI アーキテクチャ設計

> 更新: 2026-07-21  
> 対象フェーズ: 調査・プロトタイプ（1ユーザー / 認証突破〜リスティングスクレイピング）

---

## 1. システム概要

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Airbnb     │◄───►│  BE Worker   │────►│  Supabase (DB)  │
│  (Scrape)   │     │  Playwright  │     │                 │
└─────────────┘     └──────┬───────┘     └────────▲────────┘
                           │                       │
                    ┌──────▼───────┐               │
                    │  BE API      │───────────────┘
                    │  FastAPI     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──┐  ┌──────▼──────────┐  ┌─────▼─────┐
       │ llm_core│  │ LINE (2公式OA)  │  │ Frontend  │
       │ Gemini  │  │ 一般 / 緊急     │  │ Next.js   │
       └─────────┘  └────────┬────────┘  └───────────┘
                             │ push
                      ┌──────▼──────┐
                      │ ホスト個人LINE │
                      └─────────────┘
```

| コンポーネント | 技術 | 役割 |
|---|---|---|
| Frontend | Next.js 16 (App Router) / Vercel | 管理画面（メッセージ返信・設定・リスティング一覧） |
| BE API | Python 3.11 / FastAPI | REST API、管理画面向けエンドポイント |
| BE Worker | Python / Playwright | Airbnb スクレイピング、定期ポーリング、自動返信送信 |
| LLM | llm_core / Gemini 2.5 Flash | 緊急度判定・返信文生成 |
| DB | Supabase (PostgreSQL) | リスティング・メッセージ・設定・セッション保存 |
| 通知 | LINE Messaging API × 2 | 一般通知用 OA / 緊急通知用 OA → ホスト個人LINE へ push |
| Cron | APScheduler (MVP) → 本番は cron コンテナ | 3〜15分間隔のポーリング |

---

## 2. 技術選定の結論

### Frontend: Next.js ✅ 確定

- 既にセットアップ済み
- Vercel デプロイが容易
- Supabase Auth との連携が標準的

### Backend: FastAPI ✅ 推奨

| 観点 | FastAPI | 代替案 |
|---|---|---|
| Playwright 連携 | Python ネイティブ、相性◎ | Node + Puppeteer も可だが llm_core と分離 |
| llm_core 共有 | 同一言語で import 可能 | — |
| 型安全性 | Pydantic v2 | — |
| 非同期 | async/await 対応 | — |
| Docker | 公式イメージ豊富 | — |

**結論**: FastAPI + Playwright (Python) で BE API / Worker を統一言語にする。

### スクレイピング: Playwright ✅ 推奨

| 観点 | Playwright | Puppeteer | Selenium |
|---|---|---|---|
| ヘッドレス | ◎ | ◎ | △ |
| セッション永続化 (storageState) | ◎ 標準機能 | △ 自前実装 | △ |
| Airbnb SPA 対応 | ◎ | ◎ | △ |
| Docker 対応 | 公式イメージあり | あり | 重い |
| デバッグ | trace/screenshot 標準 | あり | あり |

**結論**: Playwright を採用。`storageState` によるセッション永続化が認証問題の核心。

### BE サーバー（本番）: 未決 → 推奨案

| 候補 | メリット | デメリット |
|---|---|---|
| **Railway** | Docker デプロイ簡単、Playwright 対応、低コスト | スケール上限 |
| **Fly.io** | グローバル、Docker | 設定やや複雑 |
| **AWS ECS Fargate** | スケール、80物件対応 | コスト・運用複雑 |
| **VPS (ConoHa等)** | 最安、フルコントrol | 運用負荷 |

**MVP 推奨**: Railway または VPS + Docker Compose  
**理由**: Playwright はブラウザバイナリが必要 → Docker 必須。Railway は `$5/月` 程度から。

---

## 3. ディレクトリ構成

```
tabioto_ai/
├── frontend/                 # Next.js 管理画面
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI エントリポイント
│   │   ├── config.py         # 環境変数
│   │   ├── api/              # REST エンドポイント
│   │   ├── db/               # Supabase クライアント
│   │   ├── scraper/          # Playwright スクレイピング
│   │   │   ├── browser.py    # ブラウザ起動・storageState 管理
│   │   │   ├── auth.py       # ログイン・セッション検証
│   │   │   ├── listings.py   # リスティング情報取得
│   │   │   └── messages.py   # メッセージ取得・送信
│   │   └── worker/           # 定期ジョブ
│   │       └── scheduler.py  # APScheduler
│   ├── llm_core/             # LLM モジュール（分類・返信生成・eval）
│   │   ├── client.py
│   │   ├── prompts/
│   │   └── eval/
│   ├── Dockerfile
│   └── pyproject.toml
├── supabase/
│   └── migrations/           # DB スキーマ
├── docker-compose.yml        # ローカル開発
└── doc/
    ├── architecture.md       # 本ドキュメント
    └── llm_design.md         # LLM 設計（既存）
```

---

## 4. 認証・セッション管理（最重要）

### 4.1 問題

Airbnb に API がないため、Playwright でブラウザ操作する。  
数分おきのポーリングで **毎回ログインし直すのは**:

- 2FA / CAPTCHA で自動化が止まる
- Airbnb の bot 検知リスクが上がる
- レスポンスが遅い

### 4.2 解決策: Playwright storageState 永続化

```
初回セットアップ:
  ホスト → 管理画面「Airbnb 連携」→ Playwright が headful/headless でログイン
  → storageState (cookies + localStorage) を暗号化して Supabase に保存

定期ポーリング:
  Worker → DB から storageState 復号 → Playwright に注入 → 既ログイン状態で操作
  → セッション切れ検知 → ②緊急通知用 LINE で push「再ログインが必要です」
```

### 4.3 storageState とは

Playwright が提供する JSON 形式のセッションスナップショット:

```json
{
  "cookies": [...],
  "origins": [{ "origin": "https://www.airbnb.com", "localStorage": [...] }]
}
```

- `context.storage_state(path="state.json")` で保存
- `browser.new_context(storage_state="state.json")` で復元
- Airbnb のセッション Cookie の有効期限は通常 **数週間〜数ヶ月**

### 4.4 認証情報の保存方針

| データ | 保存場所 | 暗号化 | 備考 |
|---|---|---|---|
| storageState (Cookie等) | Supabase `airbnb_sessions` テーブル | AES-256 (アプリ側) | メインの認証手段 |
| メール/パスワード | **原則保存しない** | — | 初回ログイン or セッション切れ時のみ使用 |
| 暗号化キー | 環境変数 `SESSION_ENCRYPTION_KEY` | — | BE サーバーのみ |
| Supabase service_role key | 環境変数 | — | BE のみ、FE には渡さない |

**MVP 方針**:

1. **初回**: 管理画面から Airbnb ログイン（Playwright が storageState を取得）
2. **運用中**: storageState のみ使用（パスワード不要）
3. **セッション切れ時**: LINE 通知 → 管理画面から再ログイン

> パスワードを DB に保存する案もあるが、セキュリティリスクが高く、2FA がある場合は使えない。storageState 方式を第一選択とする。

### 4.5 セッション切れ検知

```python
# ポーリング時のフロー
try:
    page.goto("https://www.airbnb.com/hosting/inbox")
    if is_login_page(page):
        mark_session_expired()
        notify_line("Airbnb セッションが切れました。管理画面から再ログインしてください。")
        return
    scrape_messages(page)
except SessionExpiredError:
    ...
finally:
    # 成功時は storageState を更新（Cookie リフレッシュ反映）
    context.storage_state(path=updated_state)
    save_encrypted_state(updated_state)
```

---

## 5. LINE 通知設計

### 5.1 構成

システム側で **2つの公式LINE アカウント（Messaging API チャネル）** を用意し、いずれもホストの個人LINE へ push 通知する。

```
[たびおとAI システム]
  ├── 公式LINE ① 一般通知用 ──push──► ホスト個人LINE
  └── 公式LINE ② 緊急通知用 ──push──► ホスト個人LINE（同一人物）
```

| 公式LINE | 用途 | 通知タイミング | 通知文例 |
|---|---|---|---|
| **① 一般通知用** | 自動返信の実行報告 | AI が自動返信した後 | `{リスティング名}で{ユーザー名}からの{問い合わせメッセージ}に{返信文}を自動送信しました。{実行時間} {メッセージリンク}` |
| **② 緊急通知用** | 手動対応が必要な案件 | 緊急度判定が true のとき | `緊急度の高いメッセージが届きました。確認してください。{リスティング名} {ユーザー名} {問い合わせメッセージ} {メッセージリンク}` |

> 通知文は LLM 不要。テンプレートへの変数埋め込みのみ（`llm_design.md` 参照）。

### 5.2 初回セットアップ

1. LINE Developers で Messaging API チャネルを **2つ** 作成（一般 / 緊急）
2. ホストが **両方の公式LINE を友だち追加**
3. 各チャネルの Webhook で `follow` イベントを受信 → ホストの User ID を取得
4. `hosts` テーブルに保存:
   - `line_user_id_general` ← ①一般通知用チャネル上の User ID
   - `line_user_id_urgent`  ← ②緊急通知用チャネル上の User ID

> **注意**: LINE Messaging API ではチャネル（公式アカウント）ごとに User ID が異なる。同一ホストでも 2 つの ID を別々に取得・保存する必要がある。

### 5.3 通知フロー

```
メッセージ受信
  → llm_core.classify_message()
  ├─ is_urgent = false
  │    → generate_reply() → Playwright で返信送信
  │    → ①一般通知用 OA から push（line_user_id_general 宛）
  └─ is_urgent = true
       → 自動返信しない
       → ②緊急通知用 OA から push（line_user_id_urgent 宛）
```

セッション切れ等のシステムアラートは **②緊急通知用** から送る（要確認が必要な事項のため）。

### 5.4 環境変数

| 変数 | 用途 |
|---|---|
| `LINE_GENERAL_CHANNEL_ACCESS_TOKEN` | ①一般通知用 OA のアクセストークン |
| `LINE_URGENT_CHANNEL_ACCESS_TOKEN` | ②緊急通知用 OA のアクセストークン |

ホストの User ID は環境変数ではなく DB (`hosts`) に保存する。

---

## 6. Supabase スキーマ設計

### 6.1 ER 図（MVP）

```
hosts (1) ──< airbnb_sessions (1)
  │
  ├──< listings (N)
  │      └──< messages (N)
  │             └──< message_actions (N)
  │
  └──< settings (1)
```

### 6.2 テーブル概要

| テーブル | 用途 |
|---|---|
| `hosts` | ホストユーザー（MVP: 1行）。LINE User ID は一般/緊急で2カラム |
| `airbnb_sessions` | 暗号化 storageState + セッション状態 |
| `listings` | スクレイピングしたリスティング情報 |
| `messages` | 受信メッセージ |
| `message_actions` | AI 判定結果・返信内容・通知ログ |
| `settings` | 自動返信設定（ポーリング間隔、アーリーチェックイン方針等） |
| `scrape_logs` | スクレイピング実行ログ |

詳細 DDL: `supabase/migrations/001_initial_schema.sql`

### 6.3 Supabase セットアップ手順

1. [supabase.com](https://supabase.com) で無料プロジェクト作成
2. Project Settings → API から `URL`, `anon key`, `service_role key` を取得
3. SQL Editor で `001_initial_schema.sql` を実行
4. `.env` にキーを設定

---

## 6.4 システムアカウント準備 & 補助ホスト招待（確認済み 2026-03）

### システムアカウント準備（初回のみ・手動）

| # | 作業 | 自動化 |
|---|---|---|
| 1 | Airbnb アカウント作成 | ❌ 手動 |
| 2 | ログイン | ✅ `login_cli automated` |
| 3 | 補助ホスト招待の承認 | △ API / CLI（前提条件あり） |
| 4 | **本人確認（身分証 + 自撮り）** | ❌ 手動 |

#### 本人確認（「招待を承認」後に遷移）

```
https://www.airbnb.jp/account-fov?user_context=COHOST_INVITATION
```

- 画面: 「政府発行の身分証明書をご登録ください」
- 運転免許証（またはパスポート等）+ 自撮りを送信
- Airbnb による確認完了まで待つ

### 補助ホスト招待フロー

```
1. ホストがシステムアカウントを補助ホスト（フル権限）として招待
2. https://www.airbnb.jp/notifications に通知が届く
3. 通知クリック → /co-hosting/accept-invite?code=XXX&listingType=STAY
4. 「招待を承認」をクリック
5. （初回）/account-fov → 本人確認を完了
6. 共同ホストとしてリスティングにアクセス可能に
```

実装: `backend/app/scraper/cohost.py`

| API | 用途 |
|---|---|
| `POST /api/cohost/accept/{host_id}` | 通知から未承認招待をすべて承認 |
| `POST /api/cohost/accept/{host_id}/url` | 招待 URL を直接指定して承認 |

---

## 7. スクレイピング設計

### 7.1 フェーズ1（今回）: リスティング情報取得

詳細 URL 構造: [doc/listing_editor_structure.md](./listing_editor_structure.md)

```
1. storageState 復元
2. /hosting/listings から listing_id 一覧を取得
3. /hosting/listings/editor/{listing_id}/{section}/{page} を巡回
4. 以下を抽出して DB 保存（写真・ホスト紹介等は除外）:
   - タイトル、説明文、ロケーション
   - チェックイン/アウト時間、チェックイン方法、道順
   - アメニティ、ハウスルール、Wi-Fi、ハウスマニュアル 等
   - Airbnb listing ID
```

### 7.2 フェーズ2: メッセージポーリング

```
1. /hosting/inbox に遷移
2. 未読スレッドを検出
3. 各スレッドの最新メッセージを取得
4. DB に保存（重複チェック: airbnb_message_id）
5. llm_core.classify_message() で緊急度判定
6. 通常 → generate_reply() → Playwright で返信送信 → ①一般通知用 LINE で push
7. 緊急 → 自動返信せず ②緊急通知用 LINE で push
```

### 7.3 bot 検知対策

- ランダムな wait (1〜3秒) を操作間に挿入
- User-Agent は Playwright デフォルト（Chromium）
- ポーリング間隔は最低 3 分（設定可能）
- 同一 IP からの過剰リクエストを避ける
- 将来的にプロキシ検討（80物件規模時）

---

## 8. 定期実行（Cron）設計

### MVP: APScheduler（backend 内蔵）

```python
# settings.poll_interval_minutes に基づきスケジュール
scheduler.add_job(poll_messages, "interval", minutes=settings.poll_interval_minutes)
```

### 本番: Docker cron コンテナ

```yaml
# docker-compose.yml
services:
  worker:
    command: python -m app.worker.scheduler
```

---

## 9. ローカル開発環境

```bash
# 1. Supabase プロジェクト作成 & migration 実行
# 2. 環境変数設定
cp .env.example .env

# 3. Docker Compose で起動
docker compose up -d

# 4. Frontend
cd frontend && pnpm dev

# 5. 手動でスクレイピングテスト
docker compose exec backend python -m app.scraper.listings

# 6. LLM eval（backend ディレクトリで実行）
cd backend && pip install -e ".[eval]" && python -m llm_core.eval.evaluate
```

---

## 10. 環境変数一覧

| 変数 | 用途 | 取得元 |
|---|---|---|
| `SUPABASE_URL` | DB 接続 | Supabase Dashboard |
| `SUPABASE_SERVICE_ROLE_KEY` | BE 用 DB アクセス | Supabase Dashboard |
| `SESSION_ENCRYPTION_KEY` | storageState 暗号化 | 自前生成 (`openssl rand -hex 32`) |
| `GEMINI_API_KEY` | LLM | Google AI Studio |
| `LINE_GENERAL_CHANNEL_ACCESS_TOKEN` | ①一般通知用 OA | LINE Developers |
| `LINE_URGENT_CHANNEL_ACCESS_TOKEN` | ②緊急通知用 OA | LINE Developers |

ホストの User ID（`line_user_id_general`, `line_user_id_urgent`）は DB に保存。Webhook の `follow` イベントで取得。

---

## 11. 進め方（2026-07-21〜）

### Step 1: 基盤構築 ✅ 本日

- [x] アーキテクチャ設計書
- [x] Supabase スキーマ DDL
- [x] Backend スキャフォールド (FastAPI + Playwright)
- [x] Docker Compose
- [ ] Supabase プロジェクト作成（たくみさん作業）
- [ ] `.env` 設定

### Step 2: 認証突破（1〜2日）

- [ ] Playwright で Airbnb ログインフロー実装
- [ ] storageState 保存・復元の動作確認
- [ ] セッション切れ検知

### Step 3: リスティングスクレイピング（2〜3日）

- [ ] リスティング一覧ページのパース
- [ ] リスティング詳細情報の抽出
- [ ] Supabase への保存

### Step 4: メッセージポーリング（3〜5日）

- [ ] inbox スクレイピング
- [ ] llm_core 連携
- [ ] 自動返信送信
- [x] LINE 通知（Webhook + push。FE 管理画面は未）

### Step 5: 管理画面（並行）

- [ ] リスティング一覧
- [ ] メッセージ画面
- [ ] 設定画面
- [ ] Airbnb 連携（再ログイン）画面

---

## 12. 未決事項・リスク

| 項目 | 内容 | 対策 |
|---|---|---|
| Airbnb UI 変更 | セレクタが変わる | スクレイピング部分をモジュール化、変更検知ログ |
| 2FA | システムアカウントに 2FA 設定時 | storageState 方式なら初回以降は不要 |
| アカウント BAN | 過剰アクセス | ポーリング間隔制限、ランダム wait |
| セッション寿命 | 不明（要調査） | scrape_logs でセッション有効性を記録 |
| 80物件スケール | 1ポーリングの処理時間 | バッチ処理、並列度調整 |
