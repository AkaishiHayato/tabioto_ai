"""メッセージ API（FE 向け）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import verify_host_path_access
from app.db.message_threads import (
  get_thread,
  list_threads,
  update_skip_auto_reply,
)
from app.db.messages import list_thread_messages
from app.scraper.exceptions import ScraperError, SessionExpiredError, SessionNotFoundError
from app.services.message_poll import poll_messages, send_message_manual

router = APIRouter(dependencies=[Depends(verify_host_path_access)])


class SkipAutoReplyRequest(BaseModel):
  skip_auto_reply: bool = Field(description="`true` でこのスレッドの AI 自動返信を無効化")


class SendMessageRequest(BaseModel):
  text: str = Field(min_length=1, max_length=4000, description="送信するメッセージ本文")


@router.get("/threads/{host_id}")
async def get_message_threads(host_id: str):
  """登録済みメッセージスレッド一覧を DB から返す。

  **用途**: FE メッセージ一覧画面。Airbnb へのリアルタイム取得は `POST /poll` で更新。

  **レスポンス**: `{"status": "ok", "threads": [...]}`

  **スレッド項目**: `airbnb_thread_id`, `guest_name`, `last_message_preview`,
  `last_sender_role`, `skip_auto_reply`, `listing_id` 等（`message_threads` テーブル）
  """
  return {"status": "ok", "threads": list_threads(host_id)}


@router.get("/threads/{host_id}/{airbnb_thread_id}")
async def get_message_thread(host_id: str, airbnb_thread_id: str):
  """単一スレッドの詳細とメッセージ履歴を DB から返す。

  **用途**: FE メッセージ詳細画面。

  **レスポンス**: `{"status": "ok", "thread": {...}, "messages": [...]}`

  **エラー**: `404` スレッド未登録（poll 未実行の場合あり）
  """
  thread = get_thread(host_id, airbnb_thread_id)
  if not thread:
    raise HTTPException(status_code=404, detail="スレッドが見つかりません")
  messages = list_thread_messages(host_id, airbnb_thread_id)
  return {"status": "ok", "thread": thread, "messages": messages}


@router.patch("/threads/{host_id}/{airbnb_thread_id}")
async def patch_message_thread(
  host_id: str,
  airbnb_thread_id: str,
  req: SkipAutoReplyRequest,
):
  """スレッドの自動返信スキップフラグを更新する。

  **用途**: FE で「このスレッドは自動返信しない」トグル。

  **リクエスト**: `{"skip_auto_reply": true}`

  **レスポンス**: `{"status": "ok", "thread": {...}}`（更新後レコード）
  """
  thread = update_skip_auto_reply(host_id, airbnb_thread_id, req.skip_auto_reply)
  if not thread:
    raise HTTPException(status_code=404, detail="スレッドが見つかりません")
  return {"status": "ok", "thread": thread}


@router.post("/poll/{host_id}")
async def trigger_message_poll(host_id: str):
  """Airbnb の未読メッセージをポーリングし、返信要否判定を実行する。

  **処理**:
  - 未読スレッド取得 → DB 更新
  - 通常メッセージ → AI 自動返信 + 一般 LINE 通知
  - 緊急メッセージ → 自動返信せず緊急 LINE 通知

  **注意**: 実ゲストへ自動送信される可能性あり。本番テスト時は注意。

  **レスポンス**: `{"status": "ok", "processed": N, "results": [...]}`
  各 result に `action`（`auto_reply` / `urgent_notify` / `skip` 等）が含まれる。

  **エラー**: `401` セッション切れ / `404` セッション未登録
  """
  try:
    result = await poll_messages(host_id)
    return result
  except SessionNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))
  except ScraperError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.post("/threads/{host_id}/{airbnb_thread_id}/send")
async def send_message_from_fe(
  host_id: str,
  airbnb_thread_id: str,
  req: SendMessageRequest,
):
  """FE 管理画面から補助ホストとして Airbnb メッセージを手動送信する。

  **用途**: 緊急案件の手動返信、自動返信スキップ中の対応。

  **リクエスト**: `{"text": "ご連絡ありがとうございます。"}`

  **成功時**: `{"status": "ok", "airbnb_thread_id": "...", "sent_text": "..."}`

  **エラー**: `401` セッション切れ / `404` セッション未登録 / `400` 送信失敗
  """
  try:
    return await send_message_manual(host_id, airbnb_thread_id, req.text)
  except SessionNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))
  except ScraperError as e:
    raise HTTPException(status_code=400, detail=str(e))
