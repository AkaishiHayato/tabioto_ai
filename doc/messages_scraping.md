# メッセージスクレイピング調査

> 更新: 2026-08-07  
> 対象: `/hosting/messages`（送信は調査中一度も行っていない）

関連: [architecture.md](./architecture.md)

---

## 1. URL 構造

| URL | 用途 |
|---|---|
| `/hosting/messages` | 全スレッド一覧 |
| `/hosting/messages?unread=` | 未読フィルタ → **数秒後に最新未読スレッドへクライアント遷移** |
| `/hosting/messages/{thread_id}` | スレッド詳細 |
| `/hosting/messages/{thread_id}?unread=` | 未読コンテキスト付き詳細 |

**スレッド ID**: URL パス中の数値（例: `2620916572`, `2553754926`）

GraphQL 上では `MessageThread:2620916572`（Base64: `TWVzc2FnZVRocmVhZDoyNjIwOTE2NTcy`）

---

## 2. リスティング ID との紐付け — ✅ 可能

`ViaductInboxData` GraphQL レスポンスの `userThreadTags` に **`stay_listing_ids`** タグがある。

```json
{
  "userThreadTagName": "stay_listing_ids",
  "additionalValues": ["1564264295874414302"]
}
```

| 項目 | 値（調査時） |
|---|---|
| thread_id | `2609311054`, `2620916572` 等 |
| listing_id | `1564264295874414302`（博多） |
| 取得元 API | `ViaductInboxData`, `ViaductGetThreadAndDataQuery` |

DOM 上はリスティング名（例: `スタイリッシュハウス博多`）がスレッド一覧プレビューに出るが、**数値 listing_id は API タグが確実**。

### DB マッピング案

```
message_threads.airbnb_thread_id  →  URL / GraphQL の thread_id
message_threads.airbnb_listing_id   →  stay_listing_ids[0]
message_threads.listing_id          →  listings.id (FK, host_id + airbnb_listing_id で解決)
```

---

## 3. 未読スレッドの取得フロー

### 3.1 ポーリング入口

```
1. GET /hosting/messages?unread=
2. ViaductInboxData が unread フィルタ付きでスレッド一覧を返す
3. クライアントが先頭未読スレッドへ redirect（例: /hosting/messages/2553754926?unread=）
```

### 3.2 DOM から thread_id 一覧

```html
[data-testid="inbox_list_{thread_id}"]
```

調査時に未読 8 件 → `inbox_list_2618536118` 等で取得可能。

### 3.3 未読数

`FetchInboxFiltersConfig` / `ViaductInboxData` の `unreadCount`（調査時: 8〜9 件）

---

## 4. メッセージ本文・送信者の取得

### 4.1 GraphQL API

| API | 用途 |
|---|---|
| `ViaductInboxData` | 一覧 + 各スレッド最新 1 件プレビュー + tags |
| `ViaductGetThreadAndDataQuery` | スレッド詳細（`messageData`, `userThreadTags`, 予約パネル） |

※ スレッド詳細の `messageData.messages` は初回レスポンスが空の場合あり。追加ロード API または DOM パースが必要。

### 4.2 DOM（実装しやすい）

| data-testid | 内容 |
|---|---|
| `message-thread-container` | スレッド全体 |
| `message-list` | メッセージ一覧 |
| `thread_page_last_item` | **最新メッセージ**（返信要否判定に最重要） |
| `thread-header-title` | 参加者名 |
| `hosting-details-reservation-info-section` | 右パネル予約情報 |
| `messaging-composebar` | 入力欄（**触らない**） |
| `messaging_compose_bar_send_button` | 送信ボタン（**触らない**） |

### 4.3 送信者ラベル（DOM テキスト）

```
Takumi · ホスト          → ホスト（返信済み扱い）
たびおと · 補助ホスト     → 共同ホスト（返信済み扱い）
다현                     → ゲスト（返信候補）
```

**重要**: `thread_page_last_item` の先頭行 `{名前} · {役割}` で判定可能。

---

## 5. 自動返信ロジック案

### 5.1 返信してよい条件（すべて AND）

1. スレッドが監視対象リスティング（`stay_listing_ids` が DB 登録済み listing と一致）
2. 最新メッセージの送信者が **ゲスト**（ホスト / 補助ホスト / システム通知ではない）
3. FE または DB で `skip_auto_reply = false`
4. `settings.auto_reply_enabled = true`
5. 予約ステータスが返信対象（例: 確定済み・進行中。レビュー依頼のみ等は除外検討）

### 5.2 返信しない条件

| 条件 | 理由 |
|---|---|
| 最新が `Takumi · ホスト` 等 | ホストが既に返信 |
| 最新が `たびおと · 補助ホスト` | システムアカウント自身の送信 |
| `skip_auto_reply = true` | FE で手動対応指定 |
| 予約確定通知のみ（システムメッセージ） | `contentType` がテキスト以外 |
| スケジュール済みクイック返信あり | 「クイック返信は ○月○日 に予定」表示 |

### 5.3 ⚠️ 未読 ≠ 要返信

調査時、未読 8 件の多くは **最後のメッセージがホスト（Takumi）** のスレッド。  
`?unread=` だけでは返信対象を絞れない。**必ずスレッドを開いて最新メッセージの送信者を確認**する。

---

## 6. DB 設計案（追加テーブル）

現行 `messages` はメッセージ 1 件単位。スレッド状態管理用に **`message_threads`** を追加推奨。

```sql
CREATE TABLE message_threads (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  host_id             UUID NOT NULL REFERENCES hosts(id),
  listing_id          UUID REFERENCES listings(id),
  airbnb_thread_id    TEXT NOT NULL,
  airbnb_listing_id   TEXT,
  guest_name          TEXT,
  reservation_status  TEXT,           -- UPCOMING_RESERVATIONS 等
  last_message_at     TIMESTAMPTZ,
  last_sender_role    TEXT,            -- guest | host | cohost | system
  last_message_preview TEXT,
  skip_auto_reply     BOOLEAN NOT NULL DEFAULT false,  -- FE から設定
  last_polled_at      TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (host_id, airbnb_thread_id)
);
```

`messages` テーブルは従来どおり個別メッセージ保存（`airbnb_message_id` で重複排除）。

---

## 7. ポーリング Worker フロー（案）

```
every N minutes:
  1. storageState 復元
  2. /hosting/messages?unread= を開く（送信操作は一切しない）
  3. ViaductInboxData または inbox_list_* から thread_id 一覧取得
  4. 各 thread_id について:
     a. listing_id を stay_listing_ids から解決
     b. DB 未登録なら message_threads に upsert
     c. /hosting/messages/{thread_id} を開く（read 状態が変わる点に注意）
     d. thread_page_last_item から最新メッセージ + 送信者取得
     e. ゲスト送信 かつ skip_auto_reply=false → classify + generate_reply
     f. （将来）送信 — MVP 前は LINE 通知のみでも可
  5. scrape_logs に結果記録
```

---

## 8. その他の考慮点

| 項目 | 内容 |
|---|---|
| **既読副作用** | スレッドを開くと既読になる。未読数が減る |
| **bot 検知** | ログイン時と同様、短間隔アクセスは制限リスク |
| **多言語** | ゲストメッセージは韓国語等。`localizationData.autoTranslateLocale` あり |
| **グループスレッド** | 「○○さんと、ほか4名」— 参加者複数 |
| **予約前スレッド** | `messageThreadType` = `HOME_BOOKING` 以外の可能性 |
| **contentType** | 予約確定通知・クイック返信スケジュール等はテキストと異なる型 |
| **network 傍受 vs DOM** | GraphQL 傍受は listing 紐付けに強い。本文は DOM の方が安定する可能性 |
| **airbnb_base_url** | `.com` 設定でも `.jp` にリダイレクト（セッション依存） |
| **送信ガード** | 実装時は compose bar への input/focus/click を禁止するテスト必須 |

---

## 9. 調査用 CLI

```bash
# 読み取り専用 DOM 調査（送信しない）
docker compose exec backend python -m app.scraper.cli.inspect_messages

# 出力（gitignore 済み・機密含む）
backend/app/scraper/messages_inspect.json
```

---

## 10. 実装状況

- [x] `message_threads` テーブル DDL（`002_message_threads.sql`）
- [x] `ViaductInboxData` 傍受による unread 一覧取得
- [x] スレッド詳細の最新メッセージ DOM パース
- [x] 返信要否判定ロジック（guest / host / cohost + 緊急）
- [x] FE API: `skip_auto_reply` / 手動送信 / ポーリング
- [x] 自動返信（通常）・緊急時 LINE 通知（token 設定時）

### FE / API

| Method | Path | 用途 |
|---|---|---|
| GET | `/api/messages/threads/{host_id}` | スレッド一覧 |
| GET | `/api/messages/threads/{host_id}/{thread_id}` | スレッド + メッセージ履歴 |
| PATCH | `/api/messages/threads/{host_id}/{thread_id}` | `skip_auto_reply` 更新 |
| POST | `/api/messages/poll/{host_id}` | ポーリング実行 |
| POST | `/api/messages/threads/{host_id}/{thread_id}/send` | FE 手動送信 |

---

## 11. 次のステップ

- [ ] Supabase に `002_message_threads.sql` 適用
- [x] LINE `hosts.line_user_id_*` Webhook 連携 + push 通知
- [ ] Worker 定期ポーリング（APScheduler）
- [ ] FE 管理画面 UI

---

## 調査ログ

| 日付 | 内容 |
|---|---|
| 2026-08-07 | 初回: `/hosting/messages?unread=` DOM + GraphQL 調査。listing 紐付け確認。未読≠要返信を確認 |
