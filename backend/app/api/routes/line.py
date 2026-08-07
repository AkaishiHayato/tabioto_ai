"""LINE Webhook API。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request

from app.config import settings
from app.db.hosts import get_host
from app.notifications.webhook import handle_webhook_events, verify_line_signature

logger = logging.getLogger(__name__)

router = APIRouter()


def _channel_secret(channel: str) -> str:
  if channel == "general":
    return settings.line_general_channel_secret
  if channel == "urgent":
    return settings.line_urgent_channel_secret
  raise HTTPException(status_code=404, detail="channel must be general or urgent")


@router.get("/status/{host_id}")
async def line_link_status(host_id: str):
  """ホストの LINE 連携状態（User ID 登録済みか）を返す。

  **用途**: FE 設定画面で「一般 LINE / 緊急 LINE の友だち追加済みか」を表示。

  **レスポンス**:
  ```json
  {
    "host_id": "...",
    "general_linked": true,
    "urgent_linked": false
  }
  ```

  **補足**: 友だち追加（follow イベント）で Webhook 経由自動登録される。
  """
  host = get_host(host_id)
  if not host:
    raise HTTPException(status_code=404, detail="host not found")

  return {
    "host_id": host_id,
    "line_user_id_general": bool(host.get("line_user_id_general")),
    "line_user_id_urgent": bool(host.get("line_user_id_urgent")),
    "general_linked": bool(host.get("line_user_id_general")),
    "urgent_linked": bool(host.get("line_user_id_urgent")),
  }


@router.post("/webhook/{channel}/{host_id}")
async def line_webhook(channel: str, host_id: str, request: Request):
  """LINE Messaging API Webhook 受信エンドポイント。

  **用途**: LINE Developers コンソール設定用。**FE からは呼ばない。**

  **パスパラメータ**:
  - `channel`: `general`（一般通知）または `urgent`（緊急通知）
  - `host_id`: Supabase `hosts.id`

  **Webhook URL 例**:
  - 一般: `https://<api>/api/line/webhook/general/<host_id>`
  - 緊急: `https://<api>/api/line/webhook/urgent/<host_id>`

  **処理**: `follow` → User ID を DB 保存 / `unfollow` → User ID クリア
  """
  if channel not in ("general", "urgent"):
    raise HTTPException(status_code=404, detail="channel must be general or urgent")

  secret = _channel_secret(channel)
  if not secret:
    raise HTTPException(
      status_code=503,
      detail=f"LINE_{channel.upper()}_CHANNEL_SECRET が未設定です",
    )

  body = await request.body()
  signature = request.headers.get("X-Line-Signature")
  if not verify_line_signature(body, signature, secret):
    raise HTTPException(status_code=403, detail="invalid LINE signature")

  payload = await request.json()
  try:
    result = handle_webhook_events(host_id, channel, payload)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e)) from e

  return {"status": "ok", **result}


@router.post("/test-push/{channel}/{host_id}")
async def line_test_push(
  channel: str,
  host_id: str,
  message: str = Query(default="たびおとAI テスト通知です", description="送信するテストメッセージ"),
):
  """開発用: 指定チャネルへテスト push 通知を送る。

  **用途**: LINE 連携確認。token 設定 + 友だち追加済みが必要。

  **パスパラメータ**: `channel` = `general` | `urgent`

  **クエリ**: `message`（任意、デフォルト: 「たびおとAI テスト通知です」）

  **注意**: 本番環境では無効化を推奨。
  """
  if channel not in ("general", "urgent"):
    raise HTTPException(status_code=404, detail="channel must be general or urgent")

  from app.notifications.line import send_test_push

  ok = await send_test_push(host_id, channel, message)
  if not ok:
    raise HTTPException(
      status_code=400,
      detail="push failed (token / user_id / API error). GET /api/line/status で連携状態を確認してください",
    )
  return {"status": "ok", "channel": channel, "host_id": host_id}
