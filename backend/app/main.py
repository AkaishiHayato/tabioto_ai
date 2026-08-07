from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import cohost, health, line, listings, messages, sessions

OPENAPI_TAGS = [
  {
    "name": "health",
    "description": "サーバー稼働確認。",
  },
  {
    "name": "sessions",
    "description": "Airbnb ログインセッションの管理。storageState の保存・検証。初回セットアップ時に使用。",
  },
  {
    "name": "listings",
    "description": "リスティングの追加・同期・スクレイピング。FE の「リスティング追加」フローは `POST /sync` を使用。",
  },
  {
    "name": "messages",
    "description": "メッセージスレッドの参照・手動送信・未読ポーリング。スレッド一覧は DB キャッシュ、`POST /poll` で Airbnb から同期。",
  },
  {
    "name": "cohost",
    "description": "共同ホスト招待の承認。通常は `POST /listings/sync` 内で処理されるため、単体利用はデバッグ用途。",
  },
  {
    "name": "line",
    "description": "LINE 通知連携。`GET /status` で連携状態確認。Webhook は LINE Developers 側設定用（FE からは呼ばない）。",
  },
]

app = FastAPI(
  title="たびおとAI API",
  version="0.1.0",
  description=(
    "Airbnb 共同ホスト向け自動返信システムのバックエンド API。\n\n"
    "**FE 開発者向けメモ**\n"
    "- ベース URL: `http://localhost:8000`（ローカル）\n"
    "- 認証: 現時点では未実装（MVP は単一ホスト）\n"
    "- `host_id`: Supabase `hosts.id`（UUID）\n"
    "- セッション切れ時: `401` + `detail` に再ログイン案内\n"
    "- OpenAPI JSON: `/openapi.json` / Swagger UI: `/docs`"
  ),
  openapi_tags=OPENAPI_TAGS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(listings.router, prefix="/api/listings", tags=["listings"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(cohost.router, prefix="/api/cohost", tags=["cohost"])
app.include_router(line.router, prefix="/api/line", tags=["line"])
