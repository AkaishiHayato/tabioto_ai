# リスティング編集ツール URL 構造

> 更新: 2026-03-23  
> 確認方法: システムアカウントで共同ホスト承認後、`/hosting/listings` から編集画面へ遷移  
> **取得フィールド詳細**: [listing_editor_fields.md](./listing_editor_fields.md)

---

## 概要

```
/hosting/listings
  └─ リスティングをクリック
       └─ /hosting/listings/editor/{listing_id}/details/photo-tour  （デフォルト遷移先）
```

| 項目 | 値（例） |
|---|---|
| **ベース URL** | `https://www.airbnb.jp/hosting/listings/editor/{listing_id}` |
| **listing_id** | `1564264295874414302`（Airbnb 内部 ID） |
| **セクション** | `details/`（基本情報）・`arrival/`（到着・チェックイン関連） |

---

## URL パターン

```
https://www.airbnb.jp/hosting/listings/editor/{listing_id}/{section}/{page}
```

| プレースホルダ | 説明 |
|---|---|
| `{listing_id}` | リスティングごとの数値 ID |
| `{section}` | `details` または `arrival` |
| `{page}` | 各編集ページのスラッグ（下表参照） |

---

## 保存対象の整理

| 記号 | 意味 |
|---|---|
| ✅ | DB 保存対象（AI 返信に使う） |
| ⬜ | 保存不要（ユーザー判断） |
| 🔜 | 後日 DOM 調査予定 |

---

## details セクション（基本情報）

| 保存 | ページ | スラッグ | URL（例） |
|:---:|---|---|---|
| ⬜ | 写真 | `photo-tour` | `.../details/photo-tour` |
| ✅ 🔜 | タイトル | `title` | `.../details/title` |
| ✅ 🔜 | 建物タイプ | `property-type` | `.../details/property-type` |
| ✅ 🔜 | 寝具／ベッドの数と種類 | `sleeping-arrangements` | `.../details/sleeping-arrangements` |
| ✅ 🔜 | 予約人数 | `number-of-guests` | `.../details/number-of-guests` |
| ✅ 🔜 | 説明文 | `description` | `.../details/description` |
| ✅ 🔜 | アメニティ・設備 | `amenities` | `.../details/amenities` |
| ✅ 🔜 | アクセシビリティ機能・設備 | `accessibility` | `.../details/accessibility` |
| ✅ 🔜 | ロケーション | `location` | `.../details/location` |
| ⬜ | ホストの紹介 | `host` | `.../details/host` |
| ⬜ | 補助ホスト | `co-hosts` | `.../details/co-hosts` |
| ✅ 🔜 | 今すぐ予約 | `instant-book` | `.../details/instant-book` |
| ✅ 🔜 | ハウスルール | `house-rules` | `.../details/house-rules` |
| ✅ 🔜 | ゲストの安全 | `guest-safety` | `.../details/guest-safety` |
| ✅ 🔜 | キャンセルポリシー | `cancellation-policy` | `.../details/cancellation-policy` |
| ⬜ | カスタム URL | `custom-link` | `.../details/custom-link` |

---

## arrival セクション（到着・チェックイン関連）

| 保存 | ページ | スラッグ | URL（例） |
|:---:|---|---|---|
| ✅ 🔜 | チェックイン・チェックアウト | `check-in-out` | `.../arrival/check-in-out` |
| ✅ 🔜 | 道順 | `directions` | `.../arrival/directions` |
| ✅ 🔜 | チェックイン方法 | `check-in-method` | `.../arrival/check-in-method` |
| ✅ 🔜 | Wi-Fi 情報 | `wifi-details` | `.../arrival/wifi-details` |
| ✅ 🔜 | ハウスマニュアル | `house-manual` | `.../arrival/house-manual` |
| ✅ 🔜 | ハウスルール | `house-rules` | `.../arrival/house-rules` |
| ✅ 🔜 | チェックアウト手順 | `checkout-instructions` | `.../arrival/checkout-instructions` |
| ✅ 🔜 | ガイドブック | `guidebooks` | `.../arrival/guidebooks` |
| ⬜ | ゲストとの交流 | `interaction-preferences` | `.../arrival/interaction-preferences` |

> **注意**: `house-rules` が `details/` と `arrival/` の両方に存在する。内容の重複有無は DOM 調査時に確認する。

---

## DB 保存方針

### 設計方針

| レイヤー | 用途 | 例 |
|---|---|---|
| **トップレベルカラム** | AI 返信で頻出・検索したい | `title`, `wifi`, `directions` |
| **raw_data JSONB** | 補完情報・多言語・scrape エラー | `titles`, `property_type`, `_errors` |

詳細 DDL: `supabase/migrations/001_initial_schema.sql`

### カラムマッピング

| DB カラム | ソース | 型 |
|---|---|---|
| `airbnb_listing_id` | URL パス | TEXT |
| `title` | `details/title` | TEXT |
| `description` | `details/description` | TEXT |
| `address` | `details/location` | TEXT |
| `max_guests` | `details/number-of-guests` | INT |
| `check_in_time` | `arrival/check-in-out` | TEXT |
| `check_out_time` | `arrival/check-in-out` | TEXT |
| `amenities` | `details/amenities` | JSONB 配列 |
| `house_rules` | `details/house-rules` | JSONB object |
| `directions` | `arrival/directions` | TEXT |
| `check_in` | `arrival/check-in-method` | JSONB object |
| `wifi` | `arrival/wifi-details` | JSONB object |
| `house_manual` | `arrival/house-manual` | TEXT |
| `checkout_instructions` | `arrival/checkout-instructions` | JSONB 配列 |
| `raw_data` | 上記以外 | JSONB object |

### raw_data のキー

| キー | ソース |
|---|---|
| `titles` | 多言語タイトル |
| `property_type` | 建物タイプ |
| `descriptions` | 説明文セクション別 |
| `amenities_detail` | アメニティ詳細 |
| `location` | 立地特徴・エリア情報 等 |
| `sleeping_arrangements` | 寝具配置 |
| `guest_safety` | ゲストの安全 |
| `accessibility` | アクセシビリティ |
| `cancellation` | キャンセルポリシー |
| `instant_book` | 今すぐ予約 |
| `guidebooks` | ガイドブック |
| `check_in_end` | チェックイン終了時刻 |
| `_errors` | ページ別 scrape エラー |

---

## スクレイピング実装

```
1. /hosting/listings から listing_id 一覧を取得
2. 各 listing_id について LISTING_EDITOR_PAGES の URL を順に開く
3. 各ページの DOM からテキストを抽出
4. Supabase listings テーブルに upsert
```

実装: `backend/app/scraper/listing/`（`scrape.py` の `LISTING_SCRAPERS`）

---

## 調査ログ

| 日付 | 内容 |
|---|---|
| 2026-03-23 | 初回: listing_id `1564264295874414302` で全 URL パターン特定。保存要否を整理。 |
| 2026-03-23 | `details/title` DOM 調査完了。`#listing-title-ja-textarea` 等で言語別取得可能。 |

<!-- 以降、各ページの DOM 調査結果を追記していく -->

### details/title

- **調査日**: 2026-03-23
- **URL**: `https://www.airbnb.jp/hosting/listings/editor/{listing_id}/details/title`
- **ページ `<title>`**: `タイトル - リスティング編集ツール - Airbnb`

#### 画面構成

| 要素 | 内容 |
|---|---|
| `h2` | 「タイトル」（ページ見出し） |
| 言語タブ | 日本語 / English / 中文 (繁體) / 한국어 |
| 入力欄 | 言語ごとに 1 つの `<input type="text">` |

#### セレクタ（言語別）

| 言語 | `id` | `name` | 備考 |
|---|---|---|---|
| **日本語** | `#listing-title-ja-textarea` | `NAME.ja` | **メイン保存対象** |
| English | `#listing-title-en-textarea` | `NAME.en` | 空の場合あり |
| 中文 (繁體) | `#listing-title-zh-tw-textarea` | `NAME.zh-tw` | |
| 한국어 | `#listing-title-ko-textarea` | `NAME.ko` | |

> `id` に `textarea` とあるが、実際の要素は `<input type="text">`。

#### 取得例（listing_id: `1564264295874414302`）

| 言語 | 値 |
|---|---|
| 日本語 | `【博多駅徒歩10分/最大6名】新幹線・地下鉄Wアクセス｜空港好アクセス｜移動ストレスゼロの快適拠点` |
| English | （空） |
| 中文 (繁體) | `【博多站步行10分鐘/最多可容納6人】…` |
| 한국어 | `【하카타역 도보 10분/최대 6명】…` |

#### スクレイピング方針

```python
# 日本語タイトルを listings.title に保存
title_ja = await page.input_value("#listing-title-ja-textarea")

# 多言語は raw_data に格納（任意）
titles = {
  "ja": await page.input_value("#listing-title-ja-textarea"),
  "en": await page.input_value("#listing-title-en-textarea"),
  "zh_tw": await page.input_value("#listing-title-zh-tw-textarea"),
  "ko": await page.input_value("#listing-title-ko-textarea"),
}
```

- AI 返信には **日本語タイトル** を優先使用
- `data-testid` はタイトル入力欄には付与されていない → **`id` 属性で取得**

### details/description

- 調査日: —
- DOM / セレクタ: （未調査）

<!-- ... 他ページも同様に追記 ... -->
