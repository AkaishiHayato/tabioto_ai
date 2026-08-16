# API I/F仕様書: settings / listings 一覧

> 作成: 2026-08-16
> 依頼元: FE（管理画面）
> 目的: FE の「Avaを設定」「リスティング一覧」画面が必要とするエンドポイントを、実装をお願いするBE担当者に共有する
> 関連: [architecture.md](./architecture.md) 6章（Supabaseスキーマ）

---

## 1. 背景

管理画面に以下3画面を実装する:

1. **Avaを設定** — AIアシスタント（Ava）の返信挙動を設定
2. **リスティング一覧**
3. **メッセージ** — 既存の `/api/messages/*` で実装済み（本ドキュメントの対象外）

「メッセージ」は既存APIで完結するが、「Avaを設定」と「リスティング一覧」には対応するエンドポイントが無いため、以下2グループの新規実装をお願いしたい。FE側は本仕様のJSON形状を前提にモックデータで実装を進めている。

**レスポンス規約**: 既存の `messages.py` / `sessions.py` に合わせて `{"status": "ok", ...}` 形式、エラー時は `HTTPException(status_code, detail="...")` でお願いします。

---

## 2. Ava設定 API (`/api/settings`)

### 2.1 対象フィールドと現状

既存 `settings` テーブル（`supabase/migrations/001_initial_schema.sql`）:

```sql
CREATE TABLE settings (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  host_id                     UUID UNIQUE NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  poll_interval_minutes       INT NOT NULL DEFAULT 10 CHECK (poll_interval_minutes IN (3, 10, 15)),
  early_checkin_policy        TEXT NOT NULL DEFAULT 'flexible' CHECK (early_checkin_policy IN ('flexible', 'strict')),
  auto_reply_enabled          BOOLEAN NOT NULL DEFAULT true,
  custom_instructions         TEXT,
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

FE の「Avaを設定」画面には、上記に加えて以下5項目が必要（ユーザーヒアリングで確定した機能スコープの「A群」）。**カラム追加が必要**:

```sql
ALTER TABLE settings
  ADD COLUMN reply_delay_minutes INT NOT NULL DEFAULT 0,
  ADD COLUMN late_checkout_policy TEXT NOT NULL DEFAULT 'flexible'
    CHECK (late_checkout_policy IN ('flexible', 'strict')),
  ADD COLUMN luggage_storage_enabled BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN luggage_storage_message TEXT NOT NULL DEFAULT
    'お荷物はチェックイン当日の12:00以降からチェックアウト日の12:00までお預かり可能です。近くの駅のコインロッカーなども便利ですのでご活用ください。',
  ADD COLUMN price_negotiation_policy TEXT NOT NULL DEFAULT 'defer_to_host'
    CHECK (price_negotiation_policy IN ('decline', 'defer_to_host'));
```

> 上記DDLはFE側からの提案です。カラム名・型・デフォルト値の最終判断はBE担当にお任せします（変更する場合はFEの型定義 `lib/types.ts` の `AvaSettings` を追随させます）。

| フィールド | 型 | 説明 |
|---|---|---|
| `auto_reply_enabled` | boolean | 自動返信の有効/無効（既存） |
| `poll_interval_minutes` | 3 \| 10 \| 15 | ポーリング間隔（既存） |
| `reply_delay_minutes` | number | 応答遅延（分）。0=即時 |
| `early_checkin_policy` | `"flexible"` \| `"strict"` | アーリーチェックイン方針（既存） |
| `late_checkout_policy` | `"flexible"` \| `"strict"` | レイトチェックアウト方針 |
| `luggage_storage_enabled` | boolean | 荷物預かり案内の自動送信ON/OFF |
| `luggage_storage_message` | string | 荷物預かり案内の文面（ON時にAIが参照） |
| `price_negotiation_policy` | `"decline"` \| `"defer_to_host"` | 価格交渉が来た際の方針 |
| `custom_instructions` | string \| null | Avaへの追加指示（自由記述、既存） |

**MVPスコープ外**（今回は実装不要・将来別タスク）: アクセスコードの能動配布、ゲストレビュー自動投稿、予約メッセージ。これらは予約日を起点とした能動的な処理で、予約データ基盤自体が別途必要なため対象外としている。

### 2.2 `GET /api/settings/{host_id}`

**用途**: FE Avaを設定画面の初期表示。

**レスポンス 200**:
```json
{
  "status": "ok",
  "settings": {
    "host_id": "3b2f6e2e-...",
    "auto_reply_enabled": true,
    "poll_interval_minutes": 10,
    "reply_delay_minutes": 0,
    "early_checkin_policy": "flexible",
    "late_checkout_policy": "flexible",
    "luggage_storage_enabled": false,
    "luggage_storage_message": "お荷物はチェックイン当日の12:00以降から...",
    "price_negotiation_policy": "defer_to_host",
    "custom_instructions": null,
    "updated_at": "2026-08-16T09:00:00Z"
  }
}
```

**エラー**: `404` 該当ホストの設定行が存在しない場合。

### 2.3 `PATCH /api/settings/{host_id}`

**用途**: 設定保存（部分更新）。

**リクエスト**（送信したいフィールドのみでよい）:
```json
{
  "auto_reply_enabled": true,
  "reply_delay_minutes": 5,
  "luggage_storage_enabled": true,
  "luggage_storage_message": "..."
}
```

**レスポンス 200**: 更新後の `settings` オブジェクト全体（`2.2` と同じ形）。

**エラー**: `404` 該当ホストなし / `422` バリデーションエラー（policy系はenum外の値等）。

---

## 3. 【重要・追加対応】settingsをAvaの返信生成に反映させる

上記2章はあくまで「設定値の保存先（CRUD API）」であり、**保存しただけではAvaの返信は一切変わりません**。現在のコードを確認したところ、返信生成の入力は以下の2つだけで、`settings` テーブルの値は（既存の `early_checkin_policy` や `custom_instructions` も含めて）どこにも渡っていません。

- `backend/llm_core/client.py:31` — `generate_reply(message, listing_info)` … 引数は「ゲストメッセージ」と「リスティング情報」の2つのみ
- `backend/llm_core/prompts/reply.py` — `REPLY_USER_PROMPT` のプレースホルダーは `{message}` と `{listing_info}` のみ
- `backend/app/services/message_poll.py` — `settings` テーブルは `get_auto_reply_enabled()` で `auto_reply_enabled` の1カラムだけ読んでおり、それ以外は未使用

settings画面の項目（本ドキュメントの2章）を実際にAvaの言動に反映するには、CRUD APIとは別に、返信生成パイプラインへの配線が必要です。

### 3.1 プロンプトに渡す項目（早期チェックイン/レイトチェックアウト/荷物預かり/価格交渉/自由記述）

これらはすべて「ゲストへの返信文の言い回し・方針」に関わるものなので、**AI側にコンテキストとして渡すだけでよい**（Airbnb側の設定を書き換える処理は不要、というのがFE側との認識合わせ済みの前提）。

想定する変更:

1. `message_poll.py` の `_generate_reply()` 呼び出し前に、対象hostの `settings` 行を取得する
2. `early_checkin_policy`, `late_checkout_policy`, `luggage_storage_enabled`/`luggage_storage_message`, `price_negotiation_policy`, `custom_instructions` から「ホストポリシー」テキストを組み立てる（例: 「アーリーチェックイン: 柔軟に対応可、荷物預かり: 案内文を使う（文面: ...）、価格交渉: 常に丁重に断る」）
3. `generate_reply(message, listing_info, host_policy_info)` のように新しい引数を追加
4. `REPLY_USER_PROMPT`（`backend/llm_core/prompts/reply.py`）に `{host_policy_info}` のプレースホルダーを追加し、`REPLY_SYSTEM_PROMPT` にも「ホストポリシーがある場合はリスティング情報より優先して従うこと」等のルールを追記

### 3.2 応答遅延（`reply_delay_minutes`）は別種の対応

これはプロンプトの内容ではなく**送信タイミングの制御**。`message_poll.py` の自動返信送信箇所（`send_thread_message` 呼び出し）を、指定分数後に送るしくみ（遅延キュー、または次回ポーリング時まで保留 等）に変更する必要がある。3.1とは独立した対応として計画してほしい。

### 3.3 スコープの確認

「BEとのI/F決め」はAPIのCRUDだけでなく、この配線まで含めて完了とする想定です。認識が異なる場合はFE側まで連絡ください。

---

## 4. リスティング一覧 API (`/api/listings`)

既存の `listings.py` には `POST /sync/{host_id}`, `POST /scrape/{host_id}`, `POST /scrape/{host_id}/{listing_id}` はあるが、**一覧取得（GET）が存在しない**。FE一覧画面表示用に追加をお願いしたい。

### 3.1 `GET /api/listings/{host_id}`

**用途**: FE リスティング一覧画面。`listings` テーブル（`001_initial_schema.sql`）から host に紐づく行を返す。

**レスポンス 200**:
```json
{
  "status": "ok",
  "listings": [
    {
      "id": "8f1c2b3a-...",
      "airbnb_listing_id": "1564264295874414302",
      "title": "【博多駅徒歩10分/最大6名】新幹線・地下鉄Wアクセス｜空港好アクセス｜移動ストレスゼロの快適拠点",
      "address": "812-0011, Fukuoka, Hakata Ekimae, Japan",
      "max_guests": 6,
      "check_in_time": "16:00",
      "check_out_time": "10:00",
      "status": "active",
      "last_scraped_at": "2026-08-10T03:20:00Z"
    }
  ]
}
```

一覧表示に不要な `description`, `amenities`, `house_rules`, `raw_data` 等の重いフィールドは含めなくてよい（詳細ページ実装時に別途 `GET /{host_id}/{listing_id}` を検討）。

**該当リスティングなし**: `200` + `"listings": []`（404にしない）。

---

## 5. FE側の対応状況

- 上記2グループの実装が完了するまで、FE は本仕様と同じ形のモックデータ（`frontend/lib/mock-settings.ts`, `frontend/lib/mock-listings.ts`）で画面を組んでいる
- 実装後、`frontend/lib/settings-client.ts` / `frontend/lib/listings-client.ts` 内の呼び出し先をモックから `apiFetch()` 経由の実APIに差し替えるだけで接続できる構成にしてある
- スキーマ（カラム名・型）を変更する場合は事前にFE側へ共有をお願いします
