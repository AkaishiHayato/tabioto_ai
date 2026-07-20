# たびおとAI

Airbnb ホスト向けの自動返信システム。システムアカウントを共同ホストとして招待し、メッセージを定期監視して AI が返信またはホストへ LINE 通知する。

## システム概要

1. たびおとAI のシステムアカウントを、ホストのリスティングに共同ホスト（フル権限）として招待
2. Playwright でリスティング情報・メッセージをスクレイピングし Supabase に保存
3. 数分おきに新規メッセージを検知し、AI が緊急度を判定
   - **通常**: リスティング情報をもとに自動返信 → 一般通知用公式 LINE でホストに通知
   - **緊急**: 自動返信せず → 緊急通知用公式 LINE でホストに通知

## 技術スタック

| レイヤー | 技術 |
|---|---|
| Frontend | Next.js 16 (App Router) / Vercel |
| Backend | Python 3.11 / FastAPI / Playwright |
| LLM | Gemini 2.5 Flash（`backend/llm_core`） |
| DB | Supabase (PostgreSQL) |
| 通知 | LINE Messaging API（一般 / 緊急の2公式アカウント） |

## ディレクトリ構成

```
tabioto_ai/
├── frontend/                 # 管理画面 (Next.js)
├── backend/                  # API・スクレイピング・LLM
│   ├── app/                  # FastAPI
│   └── llm_core/             # 緊急度判定・返信文生成
├── supabase/
│   └── migrations/           # DB スキーマ
├── doc/
│   ├── architecture.md       # アーキテクチャ設計
│   └── llm_design.md         # LLM 設計
├── docker-compose.yml
└── .env.example
```

## クイックスタート

### 1. 環境変数

```bash
cp .env.example .env
# .env を編集（Supabase キー等）
openssl rand -hex 32   # SESSION_ENCRYPTION_KEY 用
```

### 2. Supabase

1. [Supabase](https://supabase.com) でプロジェクト作成
2. SQL Editor で `supabase/migrations/001_initial_schema.sql` を実行
3. `.env` に `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` を設定

### 3. Backend 起動

```bash
docker compose up -d
curl http://localhost:8000/health   # {"status":"ok"}
```

詳細は [backend/README.md](./backend/README.md) を参照。

### 4. Frontend 起動

```bash
cd frontend
pnpm install
pnpm dev
```

[http://localhost:3000](http://localhost:3000) で確認。

## ドキュメント

| ドキュメント | 内容 |
|---|---|
| [backend/README.md](./backend/README.md) | BE 環境構築・API・ローカル開発 |
| [doc/listing_editor_structure.md](./doc/listing_editor_structure.md) | リスティング編集ツール URL 構造・保存対象 |
| [doc/architecture.md](./doc/architecture.md) | アーキテクチャ・認証・スクレイピング設計 |
| [doc/llm_design.md](./doc/llm_design.md) | LLM 入出力・eval 方針 |

## 開発フェーズ（現状）

- [x] アーキテクチャ設計
- [x] Supabase スキーマ
- [x] Backend スキャフォールド（FastAPI + Playwright）
- [x] LLM コア（分類・返信生成）
- [x] Supabase 接続確認
- [x] Airbnb 自動ログイン
- [x] 補助ホスト招待フロー調査
- [ ] システムアカウント本人確認（手動・たくみ作業）
- [ ] リスティングスクレイピング
- [ ] メッセージポーリング・自動返信
- [ ] LINE 通知
- [ ] 管理画面（FE）
