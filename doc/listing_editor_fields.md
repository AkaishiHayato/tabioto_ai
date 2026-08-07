# リスティング編集ツール — 取得可能フィールド一覧

> 更新: 2026-03-23  
> 調査対象: `listing_id = 1564264295874414302`（博多）  
> 調査方法: システムアカウント（共同ホスト）で Playwright headless 巡回  
> 関連: [URL 構造](./listing_editor_structure.md)

---

## 概要

```
https://www.airbnb.jp/hosting/listings/editor/{listing_id}/{section}/{page}
```

| 項目 | 値 |
|---|---|
| ベース URL | `https://www.airbnb.jp/hosting/listings/editor/1564264295874414302` |
| セクション | `details`（基本情報）・`arrival`（到着ガイド） |
| 全ページ数 | 25（保存対象 19 / 除外 6） |

### 画面レイアウト（共通）

編集ツールは **左サイドバー + 右プレビューパネル** の2カラム構成。

| 領域 | 内容 |
|---|---|
| 左サイドバー | 全セクションの要約（タイトル・説明・アメニティ等の抜粋） |
| 右プレビュー | 選択中ページの詳細編集 UI |

> 多くのページは `<input>` / `<textarea>` が右パネルに遅延描画される。  
> 取得時は `wait_for_timeout(3000〜4000)` + 右パネル内の要素を対象にする。

### 凡例

| 記号 | 意味 |
|:---:|---|
| ✅ | DB 保存対象（AI 返信に使う） |
| ⬜ | 保存不要 |
| 🔍 | DOM 調査済（セレクタ確定 or 取得方針確定） |
| 🔜 | 取得方針は分かっているがセレクタ未確定 |

---

## 一覧サマリー

### details セクション

| 保存 | ページ | スラッグ | 主な取得項目 | 調査 |
|:---:|---|---|---|:---:|
| ⬜ | 写真 | `photo-tour` | 部屋カテゴリ名、写真枚数 | 🔍 |
| ✅ | タイトル | `title` | 多言語タイトル（ja/en/zh-tw/ko） | 🔍 |
| ✅ | 建物タイプ | `property-type` | 物件種別、部屋タイプ、面積 | 🔍 |
| ✅ | 寝具／ベッド | `sleeping-arrangements` | 部屋名、ベッド種類・数 | 🔜 |
| ✅ | 予約人数 | `number-of-guests` | 最大ゲスト数 | 🔍 |
| ✅ | 説明文 | `description` | 多言語説明文 | 🔜 |
| ✅ | アメニティ | `amenities` | アメニティ名リスト（+説明） | 🔜 |
| ✅ | アクセシビリティ | `accessibility` | バリアフリー設備リスト | 🔜 |
| ✅ | ロケーション | `location` | 住所、地図、立地特徴 | 🔜 |
| ⬜ | ホスト紹介 | `host` | ホスト名、レビュー数、評価 | 🔍 |
| ⬜ | 補助ホスト | `co-hosts` | 共同ホスト一覧 | 🔍 |
| ✅ | 今すぐ予約 | `instant-book` | 有効/無効、オプション設定 | 🔜 |
| ✅ | ハウスルール | `house-rules` | ペット/イベント/喫煙/静穏時間等 | 🔍 |
| ✅ | ゲストの安全 | `guest-safety` | 防災設備、安全上の留意事項 | 🔜 |
| ✅ | キャンセルポリシー | `cancellation-policy` | 短期/長期ポリシー名 | 🔜 |
| ⬜ | カスタム URL | `custom-link` | カスタム URL スラッグ | 🔍 |

### arrival セクション

| 保存 | ページ | スラッグ | 主な取得項目 | 調査 |
|:---:|---|---|---|:---:|
| ✅ | チェックイン・アウト | `check-in-out` | チェックイン開始/終了、チェックアウト時刻 | 🔍 |
| ✅ | 道順 | `directions` | 道順テキスト（Google Maps URL 含む） | 🔍 |
| ✅ | チェックイン方法 | `check-in-method` | 方式（キーボックス等）、入室手順 | 🔜 |
| ✅ | Wi-Fi 情報 | `wifi-details` | SSID、パスワード | 🔍 |
| ✅ | ハウスマニュアル | `house-manual` | マニュアル本文 | 🔍 |
| ✅ | ハウスルール | `house-rules` | details と同一フォーム | 🔍 |
| ✅ | チェックアウト手順 | `checkout-instructions` | 必須タスク一覧 | 🔜 |
| ✅ | ガイドブック | `guidebooks` | ガイドブック有無（未作成の場合は空） | 🔜 |
| ⬜ | ゲストとの交流 | `interaction-preferences` | 交流レベル設定 | 🔍 |

---

## ページ別詳細

### ⬜ details/photo-tour — 写真

**URL**: `.../details/photo-tour`

| フィールド | 内容 | 取得方法 |
|---|---|---|
| 部屋カテゴリ | リビング、フルキッチン、寝室、バスルーム等 | `h3` 見出し |
| 写真枚数 | 例: `写真74枚` | サイドバー要約テキスト |
| 寝室/ベッド/バスルーム数 | 例: `寝室1` `ベッド3` `バスルーム1` | サイドバー要約 |

**保存方針**: AI 返信には不要。写真 URL の取得も対象外。

---

### ✅ details/title — タイトル

**URL**: `.../details/title`

| フィールド | DB カラム | セレクタ | 例（博多） |
|---|---|---|---|
| タイトル（日本語） | `listings.title` | `#listing-title-ja-textarea` | 【博多駅徒歩10分/最大6名】… |
| タイトル（English） | `raw_data.titles.en` | `#listing-title-en-textarea` | （空） |
| タイトル（繁體中文） | `raw_data.titles.zh_tw` | `#listing-title-zh-tw-textarea` | 【博多站步行10分鐘…】 |
| タイトル（한국어） | `raw_data.titles.ko` | `#listing-title-ko-textarea` | 【하카타역 도보 10분…】 |

```python
title_ja = await page.input_value("#listing-title-ja-textarea")
```

> `id` に `textarea` とあるが実体は `<input type="text">`。

---

### ✅ details/property-type — 建物タイプ

**URL**: `.../details/property-type`

| フィールド | セレクタ (`name`) | 例（博多） | 備考 |
|---|---|---|---|
| 物件グループ | `select[name="propertyTypeGroup"]` | `APARTMENTS` | マンション・アパート等 |
| 物件タイプ | `select[name="propertyType"]` | `APARTMENT` | |
| 部屋タイプ | `select[name="roomType"]` | `ENTIRE_HOME` | 住宅全体 |
| 築年 | `input[name="yearBuilt"]` | （空） | |
| 面積 | `input[name="propertySize"]` | `45` | |
| 面積単位 | `select[name="propertySizeUnits"]` | `SQUARE_METERS` | |

**DB 保存案**: `raw_data.property_type` に enum 値 + 表示ラベルを格納。

サイドバー要約: `住宅全体 · マンション・アパート`

---

### ✅ details/sleeping-arrangements — 寝具／ベッド

**URL**: `.../details/sleeping-arrangements`

| フィールド | 内容 | 取得方法 |
|---|---|---|
| 部屋一覧 | リビング、寝室 等 | 右パネル `h3` + ベッド詳細 |
| ベッド種類・数 | 各部屋ごと | 🔜 カスタム UI。`input` なし |
| 合計ベッド数 | 例: `ベッド3` | サイドバー要約 |

**現状**: フォーム要素が headless では検出されず。右パネルのテキスト抽出 or 「編集」クリック後の DOM 調査が必要。

---

### ✅ details/number-of-guests — 予約人数

**URL**: `.../details/number-of-guests`

| フィールド | DB | 取得方法 | 例 |
|---|---|---|---|
| 最大ゲスト数 | `raw_data.max_guests` | 数値入力欄（`id` なし） | `6` |

サイドバー要約: `ゲスト6人`

---

### ✅ details/description — 説明文

**URL**: `.../details/description`

| フィールド | DB カラム | 取得方法 | 備考 |
|---|---|---|---|
| 説明文（日本語） | `listings.description` | 🔜 右パネルプレビューからテキスト抽出 | 多言語タブあり |
| 説明文（他言語） | `raw_data.descriptions.*` | 同上 | en / zh-tw / ko |

**確認済み内容（博多・抜粋）**:
- 博多駅徒歩10分、アクセス情報、最大6名、ベッド3台 等

**現状**: `<textarea>` が headless 初回ロードでは未検出。右パネル `main` 内の「リスティングの説明文」セクションから `inner_text` 取得が現実的。

---

### ✅ details/amenities — アメニティ・設備

**URL**: `.../details/amenities`

| フィールド | DB カラム | 取得方法 |
|---|---|---|
| アメニティ名リスト | `listings.amenities` | 右パネル内の項目名を列挙 |
| アメニティ説明 | `raw_data.amenities_detail` | 各項目のサブテキスト（任意） |

**確認済み例（博多）**:
Wi-Fi、アイロン、ウォシュレット（ビデ）、エアコン、キッチン、ケトル、ゲスト専用玄関、テレビ、洗濯機 等（計 32 件前後）

**現状**: チェックボックスリストはカスタム UI。「編集」ボタンクリック後の DOM か、プレビューパネルのテキストパースが必要。

---

### ✅ details/accessibility — アクセシビリティ

**URL**: `.../details/accessibility`

| フィールド | DB | 取得方法 |
|---|---|---|
| バリアフリー設備リスト | `raw_data.accessibility` | 右パネル項目名を列挙 |

**確認済み例（博多）**:
障害者用駐車スペース、段差のないアクセス、ゲスト用玄関幅 81cm 以上 等

---

### ✅ details/location — ロケーション

**URL**: `.../details/location`

| フィールド | DB カラム | 取得方法 | 例（博多） |
|---|---|---|---|
| 住所（フル） | `listings.address` | 「所在地」セクションのテキスト | `812-0011, Fukuoka, ... Hakata Ekimae, Japan` |
| 地図座標 | `raw_data.location.lat/lng` | Google Map 埋め込みから抽出（🔜） | |
| 所在地の共有設定 | `raw_data.location.show_exact` | トグル（🔜） | |
| 立地の特徴 | `raw_data.location.features` | テキスト（🔜） | ゲスト専用玄関 |
| エリア情報 | `raw_data.location.area_info` | テキスト（🔜） | |
| 移動手段 | `raw_data.location.transportation` | テキスト（🔜） | |
| 景色 | `raw_data.location.views` | テキスト（🔜） | |

---

### ⬜ details/host — ホストの紹介

**URL**: `.../details/host`

| フィールド | 内容 | 備考 |
|---|---|---|
| ホスト名 | 例: `Takumi` | 保存不要 |
| スーパーホスト | バッジ有無 | |
| レビュー数 | 例: `97` | `data-testid="レビュー-stat-heading"` |
| 評価 | 例: `4.9` | `data-testid="評価-stat-heading"` |
| ホスティング歴 | 例: `2` 年 | `data-testid="ホスティング歴-stat-heading"` |

---

### ⬜ details/co-hosts — 補助ホスト

**URL**: `.../details/co-hosts`

| フィールド | 内容 |
|---|---|
| 共同ホスト名 | 例: 花田拓実（Takumi）さん |
| 権限 | 完全なアクセス権 / リスティング所有者 |

**保存方針**: たびおとAI 自身の共同ホスト情報のため保存不要。

---

### ✅ details/instant-book — 今すぐ予約

**URL**: `.../details/instant-book`

| フィールド | DB | 取得方法 |
|---|---|---|
| 今すぐ予約 ON/OFF | `raw_data.instant_book.enabled` | `[role="switch"]` の `aria-checked` |
| 良好な利用実績要件 | `raw_data.instant_book.good_track_record` | トグル（🔜） |
| 予約前メッセージ | `raw_data.instant_book.pre_booking_message` | テキスト（🔜） |

**確認済み（博多）**: オン — `ゲストはその場で予約を確定できます`

---

### ✅ details/house-rules — ハウスルール

**URL**: `.../details/house-rules`  
**注意**: `arrival/house-rules` と **同一フォーム**（内容重複）

| フィールド | セレクタ | 例（博多） |
|---|---|---|
| ペット OK | `#pets-allowed-toggle-row-row-toggle-DLS-toggle-{yes\|no}` | OFF |
| イベント OK | `#events-allowed-toggle-row-row-toggle-DLS-toggle-{yes\|no}` | OFF |
| 喫煙 OK | `#smoking-allowed-toggle-row-row-toggle-DLS-toggle-{yes\|no}` | OFF |
| 静穏時間 | `#quiet-hours-toggle-row-row-toggle-DLS-toggle-{yes\|no}` | ON |
| 静穏時間 開始 | `select[name="quietHoursStartTime"]` | `20`（20:00） |
| 静穏時間 終了 | `select[name="quietHoursEndTime"]` | `7`（7:00） |
| 商業撮影 OK | `#commercial-photography-allowed-toggle-row-row-toggle-DLS-toggle-{yes\|no}` | OFF |

**DB 保存案**: `listings.house_rules` JSONB

```json
{
  "pets_allowed": false,
  "events_allowed": false,
  "smoking_allowed": false,
  "quiet_hours": { "enabled": true, "start": "20:00", "end": "07:00" },
  "commercial_photography_allowed": false
}
```

サイドバー要約にも `チェックイン時刻：16:00以降` `ゲスト定員6人` 等が表示される。

---

### ✅ details/guest-safety — ゲストの安全

**URL**: `.../details/guest-safety`

| フィールド | DB | 取得方法 |
|---|---|---|
| 安全上の留意事項 | `raw_data.guest_safety.notes` | テキスト（🔜） |
| 防災設備 | `raw_data.guest_safety.devices` | 項目リスト |

**確認済み例（博多）**:
- 一酸化炭素警報器なし
- 火災報知器を設置済み
- 屋外・共有部に防犯・監視カメラあり

---

### ✅ details/cancellation-policy — キャンセルポリシー

**URL**: `.../details/cancellation-policy`

| フィールド | DB | 取得方法 |
|---|---|---|
| 短期滞在ポリシー | `raw_data.cancellation.short_term` | 選択中ラジオ/カードのラベル |
| 長期滞在ポリシー | `raw_data.cancellation.long_term` | 同上 |
| 返金不可オプション | `raw_data.cancellation.non_refundable` | トグル `aria-checked` |

**確認済み例（博多）**:
- 短期: `限定`
- 長期: `やや厳格（長期滞在向け）`

---

### ⬜ details/custom-link — カスタム URL

**URL**: `.../details/custom-link`

| フィールド | セレクタ | 例 |
|---|---|---|
| カスタム URL スラッグ | `#custom-link-textarea` | `airbnb.jp/h/`（未完成） |

---

## arrival セクション詳細

### ✅ arrival/check-in-out — チェックイン・チェックアウト

**URL**: `.../arrival/check-in-out`

| フィールド | DB カラム | セレクタ | 例（博多） |
|---|---|---|---|
| チェックイン開始 | `listings.check_in_time` | `#check-in-start-time` | `16` → 16:00 |
| チェックイン終了 | `raw_data.check_in_end` | `#check-in-end-time` | `-1`（フレキシブル？） |
| チェックアウト | `listings.check_out_time` | `#check-out-time` | `10` → 10:00 |

```python
check_in = await page.input_value("#check-in-start-time")   # "16"
check_out = await page.input_value("#check-out-time")       # "10"
```

---

### ✅ arrival/directions — 道順

**URL**: `.../arrival/directions`

| フィールド | DB | セレクタ | 備考 |
|---|---|---|---|
| 道順テキスト | `raw_data.directions` | `#directionsForm-textarea` | Google Maps URL 含む |

**確認済み内容（博多）**:
- Airbnb への Maps リンク
- 博多駅からの Maps リンク

---

### ✅ arrival/check-in-method — チェックイン方法

**URL**: `.../arrival/check-in-method`

| フィールド | DB | 取得方法 | 例（博多） |
|---|---|---|---|
| チェックイン方式 | `raw_data.check_in.method` | 見出し/選択 UI | `キーボックス` |
| 方式の説明 | `raw_data.check_in.method_description` | テキスト | `入室日にキーボックスの番号をお伝えします！` |
| チェックイン手順 | `raw_data.check_in.instructions` | 手順リスト（🔜） | 未追加 |

**現状**: フォーム `input` なし。右パネルの構造化テキスト抽出が必要。

---

### ✅ arrival/wifi-details — Wi-Fi 情報

**URL**: `.../arrival/wifi-details`

| フィールド | DB | セレクタ |
|---|---|---|
| ネットワーク名（SSID） | `raw_data.wifi.ssid` | `#wifi-name` |
| パスワード | `raw_data.wifi.password` | `#wifi-password` |

```python
ssid = await page.input_value("#wifi-name")
password = await page.input_value("#wifi-password")
```

> **注意**: Wi-Fi 情報はゲストへの自動返信で頻出。DB 保存時は暗号化を検討。

---

### ✅ arrival/house-manual — ハウスマニュアル

**URL**: `.../arrival/house-manual`

| フィールド | DB | セレクタ |
|---|---|---|
| マニュアル本文 | `raw_data.house_manual` | `#houseManualForm-textarea` |

**確認済み（博多）**: 空（未入力）

---

### ✅ arrival/house-rules — ハウスルール

**URL**: `.../arrival/house-rules`

`details/house-rules` と **完全同一**。どちらか一方を scrape すればよい（推奨: `details/house-rules`）。

---

### ✅ arrival/checkout-instructions — チェックアウト手順

**URL**: `.../arrival/checkout-instructions`

| フィールド | DB | 取得方法 |
|---|---|---|
| 必須タスク一覧 | `raw_data.checkout_instructions` | 項目名リスト |

**確認済み例（博多）**:
1. 使用済みのタオルを集める
2. ごみを捨てる
3. 照明や家電をオフにする
4. 鍵をかける
5. 鍵を返す

**現状**: チェックボックス UI。`input` 未検出。テキスト列挙で取得可能。

---

### ✅ arrival/guidebooks — ガイドブック

**URL**: `.../arrival/guidebooks`

| フィールド | DB | 取得方法 |
|---|---|---|
| ガイドブック有無 | `raw_data.guidebooks` | 作成済みなら各ガイドのタイトル・内容 |

**確認済み（博多）**: 未作成（「ガイドブックを作成する」のみ表示）

---

### ⬜ arrival/interaction-preferences — ゲストとの交流

**URL**: `.../arrival/interaction-preferences`

| フィールド | セレクタ | 備考 |
|---|---|---|
| 交流レベル | `input[name="interaction-preferences-chip-group"]` | ラジオ 4 択 |

**保存方針**: AI 返信には優先度低。保存不要。

---

## DB マッピング（確定版）

### トップレベルカラム

| DB カラム | ソースページ |
|---|---|
| `title` | `details/title` |
| `description` | `details/description` |
| `address` | `details/location` |
| `max_guests` | `details/number-of-guests` |
| `check_in_time` / `check_out_time` | `arrival/check-in-out` |
| `amenities` | `details/amenities` |
| `house_rules` | `details/house-rules` |
| `directions` | `arrival/directions` |
| `check_in` | `arrival/check-in-method` |
| `wifi` | `arrival/wifi-details` |
| `house_manual` | `arrival/house-manual` |
| `checkout_instructions` | `arrival/checkout-instructions` |

### raw_data

| キー | ソースページ |
|---|---|
| `titles` | `details/title`（多言語） |
| `property_type` | `details/property-type` |
| `descriptions` | `details/description`（セクション別） |
| `amenities_detail` | `details/amenities` |
| `location` | `details/location`（立地特徴等） |
| `sleeping_arrangements` | `details/sleeping-arrangements` |
| `guest_safety` | `details/guest-safety` |
| `accessibility` | `details/accessibility` |
| `cancellation` | `details/cancellation-policy` |
| `instant_book` | `details/instant-book` |
| `guidebooks` | `arrival/guidebooks` |
| `check_in_end` | `arrival/check-in-out` |
| `_errors` | scrape エラー |

DDL: `supabase/migrations/001_initial_schema.sql`

---

## 実装状況

全 19 ページの scrape 実装済み（`backend/app/scraper/listing/scrape.py` の `LISTING_SCRAPERS`）。

| セクション | ページ数 |
|---|---|
| `details/` | 12 |
| `arrival/` | 7（`house-rules` は details と重複のため scrape 対象外） |

---

## 調査ログ

| 日付 | 内容 |
|---|---|
| 2026-03-23 | 全 25 ページ Playwright 巡回。19 保存対象ページの取得項目を整理。 |
| 2026-03-23 | セレクタ確定: title, property-type, house-rules, check-in-out, directions, wifi, house-manual |

### 再調査コマンド

```bash
docker compose exec backend python -m app.scraper.cli.inspect_listings
```

出力: `backend/app/scraper/listing_editor_inspect.json`（gitignore 済み・機密含む）
