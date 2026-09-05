# 認証機構 調査・設計

> 作成: 2026-08-16
> 対象範囲: ① 管理画面(FE)へのホストログイン ② FE→BE APIの認証
> 対象外: Airbnbログイン([architecture.md](./architecture.md) 4章で設計・実装済み)、マルチテナント対応

---

## 1. 現状（コード確認済み）

- **FE**: ログイン画面・認証状態管理は一切存在しない。`frontend/lib/api.ts` の `HOST_ID` は `NEXT_PUBLIC_HOST_ID` 環境変数の固定値
- **BE**: `backend/app/main.py` の説明文に明記の通り「認証: 現時点では未実装（MVP は単一ホスト）」。CORSで `localhost:3000` からのオリジンは制限しているが、**リクエスト自体の認証チェックは一切ない**。`host_id` を知っていれば誰でも全APIを呼べる状態
- **DB**: `hosts` テーブル（`supabase/migrations/001_initial_schema.sql`）に `name`, `email` はあるが、パスワードや外部認証との紐付けカラムは無い

---

## 2. 要件・制約

- MVPは1ホストのみ。サインアップ画面や複雑な招待フローは不要（マルチテナントは明示的にスコープ外）
- 既にDBとしてSupabaseを採用済み（`backend/app/db/client.py` で `SUPABASE_SERVICE_ROLE_KEY` 使用）
- FE(Next.js 16 App Router) → BE(FastAPI) の構成を変えない

---

## 3. 選定: Supabase Auth ✅ 推奨

Next.js公式の認証ガイド（`node_modules/next/dist/docs/01-app/02-guides/authentication.md`）でも推奨ライブラリの1つとして名前が挙がっている。他の主要選択肢との比較:

| 選択肢 | メリット | デメリット |
|---|---|---|
| **Supabase Auth**（推奨） | 既存のSupabaseプロジェクトにそのまま同梱。パスワードハッシュ化・トークン発行・リフレッシュを自前実装しなくてよい。`@supabase/ssr` でNext.js App Router対応済み | Supabase側でEmail認証プロバイダの有効化が必要（ダッシュボード操作） |
| NextAuth.js (Auth.js) | プロバイダが豊富、汎用的 | 今回SNSログイン等は不要。DBセッション用に別途アダプタが要り、Supabaseと二重管理になる |
| 自前実装（bcrypt + jose） | 依存が最小 | パスワードリセット・トークン更新等を全部自前で作る必要があり、MVPの割に工数が重い。Next.js公式ガイドも「独自実装は複雑になりがちなのでライブラリ推奨」と明記 |
| 共有パスワード1つだけ（環境変数） | 実装コスト最小 | 「認証機構」と呼べる代物ではなく、退職・漏洩時の失効ができない。調査タスクの主旨に合わない |

**結論**: Supabase Auth（Email/Password）を採用する。

---

## 4. 設計

### 4.1 全体フロー

```
┌──────────────┐   1. ログイン(email/password)   ┌──────────────┐
│  ブラウザ     │ ───────────────────────────────► │ Supabase Auth │
│ (Next.js FE) │ ◄─────────────────────────────── │              │
└──────┬───────┘   2. access_token(JWT) + refresh  └──────────────┘
       │ 3. Cookieにセッション保存(@supabase/ssr)
       │
       │ 4. BEへのリクエストに Authorization: Bearer <access_token>
       ▼
┌──────────────┐   5. JWT検証(SUPABASE_JWT_SECRET)  
│ FastAPI (BE) │ ───────────────────────────────►  hosts.auth_user_id で該当ホストを特定
└──────────────┘
```

### 4.2 FE側

- **ログイン画面**: `app/login/page.tsx`（新規、`(dashboard)` 外）。email/password フォーム。Server Action で `supabase.auth.signInWithPassword()` を呼ぶ
- **サインアップ画面は作らない**: MVPは1ホストなので、ユーザーはSupabaseダッシュボードから手動作成する運用でよい
- **セッション管理**: `@supabase/ssr` パッケージを追加し、Server Component / Server Action / Route Handler 用のSupabaseクライアントを用意（Next.js公式ガイド通りのDALパターン: `lib/dal.ts` に `verifySession()` を作り、各ページの先頭で呼ぶ）
- **ルート保護**: Next.js 16では `middleware.ts` が `proxy.ts` に名称変更（機能は同じ）。`proxy.ts` でCookieの存在チェックのみ行う「楽観的チェック」を実装し、`(dashboard)` 配下を保護。**ただし公式ガイドが明言する通り、Proxyでの判定だけを唯一のセキュリティ境界にはしない**。実際のデータ取得箇所（各page.tsx）でも `verifySession()` を呼ぶ二重チェック構成にする
- **BEへのリクエスト**: `lib/api.ts` の `apiFetch()` に、Supabaseセッションの `access_token` を `Authorization: Bearer` ヘッダーとして付与する処理を追加。`HOST_ID` 固定値は撤廃し、以後は認証情報から解決する

### 4.3 BE側

- FastAPIに認証用の `Depends` を追加（例: `app/api/deps.py` に `get_current_host()`）
  1. `Authorization: Bearer <token>` ヘッダーを取得
  2. `SUPABASE_JWT_SECRET`（Supabaseダッシュボード → Project Settings → API から取得、新規環境変数）でJWTを検証（`PyJWT` or `python-jose`、アルゴリズムはSupabaseプロジェクトの設定に依存。レガシー共有シークレット方式ならHS256、新しい非対称鍵方式ならJWKS経由のRS256/ES256 — **どちらの方式かはSupabaseプロジェクト作成時の設定に依存するため、実プロジェクト作成後に要確認**）
  3. JWTの `sub`（Supabase Auth の `auth.users.id`）を取得
  4. `hosts` テーブルを `auth_user_id = sub` で検索し、`hosts.id` を解決
- 各エンドポイントの `host_id` パスパラメータは撤廃せず残すが、`get_current_host()` で解決した `host_id` と一致するかを検証する（他ホストのデータへのアクセスを防ぐ防御的チェック）。将来マルチテナント化する際もこの形のまま拡張できる

### 4.4 DBスキーマ変更

```sql
ALTER TABLE hosts ADD COLUMN auth_user_id UUID UNIQUE REFERENCES auth.users(id);
```

既存の唯一のホストレコードに対して、Supabaseダッシュボードで作成したユーザーの `auth.users.id` を手動で紐付ける（MVPなので1回きりのSQL実行でよい）。

### 4.5 新規環境変数

| 変数 | 用途 | 設定先 |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabaseクライアント初期化 | FE |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabaseクライアント初期化（RLS前提のanonキー） | FE |
| `SUPABASE_JWT_SECRET` | BEでのJWT検証 | BE |

---

## 5. 運用上の前提（人間が行う作業）

1. Supabaseダッシュボードで Authentication → Providers → Email を有効化
2. ホスト本人のアカウントをSupabaseダッシュボードから作成（またはSQL/Admin APIで作成）
3. `hosts.auth_user_id` にそのユーザーIDを設定
4. `SUPABASE_JWT_SECRET` を取得し `.env` に設定

---

## 6. 実装タスクの切り分け（案）

| # | タスク | 想定担当 |
|---|---|---|
| 1 | `hosts.auth_user_id` migration 追加 | BE |
| 2 | BE: `get_current_host()` 依存関数の実装、全ルーターへの適用 | BE |
| 3 | FE: `@supabase/ssr` 導入、ログイン画面、`proxy.ts`、DAL (`verifySession`) | FE |
| 4 | FE: `lib/api.ts` にBearerトークン付与を追加、`HOST_ID` 固定値を撤廃 | FE |
| 5 | Supabase Auth有効化・ホストアカウント作成（運用作業） | 人間（たくみさん等） |

---

## 7. 未決事項

- SupabaseプロジェクトのJWT署名方式（レガシー共有シークレット / 新方式JWKS）は、実際のSupabaseプロジェクト設定を見てから確定させる
- セッションの有効期限・自動リフレッシュ間隔はSupabaseのデフォルトのままでMVPは問題ないと考えるが、要合意
