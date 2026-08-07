"""LINE 通知。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings
from app.db.hosts import LineChannel, get_line_user_id

logger = logging.getLogger(__name__)

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
JST = timezone(timedelta(hours=9))
_PREVIEW_MAX = 200
_REPLY_MAX = 300


def _thread_url(thread_id: str) -> str:
  base = settings.airbnb_base_url.rstrip("/")
  return f"{base}/hosting/messages/{thread_id}"


def _now_jst_label() -> str:
  return datetime.now(JST).strftime("%Y/%m/%d %H:%M")


def _truncate(text: str, limit: int) -> str:
  text = text.strip()
  if len(text) <= limit:
    return text
  return text[: limit - 1] + "…"


def _channel_token(channel: LineChannel) -> str:
  if channel == "general":
    return settings.line_general_channel_access_token
  return settings.line_urgent_channel_access_token


def format_urgent_message(
  *,
  guest_name: str | None,
  listing_title: str | None,
  message_preview: str,
  thread_id: str,
) -> str:
  guest = guest_name or "ゲスト"
  listing = listing_title or "（リスティング不明）"
  preview = _truncate(message_preview, _PREVIEW_MAX)
  return (
    "緊急度の高いメッセージが届きました。確認してください。\n"
    f"{listing}\n"
    f"{guest}\n"
    f"{preview}\n"
    f"{_thread_url(thread_id)}"
  )


def format_auto_reply_message(
  *,
  guest_name: str | None,
  listing_title: str | None,
  guest_message: str,
  reply_text: str,
  thread_id: str,
  sent_at: datetime | None = None,
) -> str:
  guest = guest_name or "ゲスト"
  listing = listing_title or "（リスティング不明）"
  inquiry = _truncate(guest_message, _PREVIEW_MAX)
  reply = _truncate(reply_text, _REPLY_MAX)
  when = (sent_at or datetime.now(JST)).astimezone(JST).strftime("%Y/%m/%d %H:%M")
  return (
    f"{listing}で{guest}からの「{inquiry}」に"
    f"「{reply}」を自動送信しました。\n"
    f"{when}\n"
    f"{_thread_url(thread_id)}"
  )


def format_session_expired_message() -> str:
  return (
    "Airbnb セッションが切れました。\n"
    "管理画面から再ログインしてください。"
  )


async def _line_push(token: str, user_id: str, text: str) -> bool:
  headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
  }
  payload = {
    "to": user_id,
    "messages": [{"type": "text", "text": text}],
  }
  async with httpx.AsyncClient(timeout=15) as client:
    response = await client.post(LINE_PUSH_URL, headers=headers, json=payload)
    if response.status_code >= 400:
      logger.error("LINE push failed: %s %s", response.status_code, response.text)
      return False
  return True


async def _notify(
  *,
  host_id: str,
  channel: LineChannel,
  text: str,
  context: str,
) -> bool:
  token = _channel_token(channel)
  if not token:
    logger.warning("LINE token 未設定のため通知スキップ (%s)", context)
    return False

  user_id = get_line_user_id(host_id, channel)
  if not user_id:
    logger.warning(
      "LINE user_id 未登録のため通知スキップ host=%s channel=%s (%s)",
      host_id,
      channel,
      context,
    )
    return False

  ok = await _line_push(token, user_id, text)
  if ok:
    logger.info("LINE push sent host=%s channel=%s (%s)", host_id, channel, context)
  return ok


async def notify_urgent_message(
  *,
  host_id: str,
  guest_name: str | None,
  listing_title: str | None,
  message_preview: str,
  thread_id: str,
) -> bool:
  """緊急メッセージを②緊急通知用 OA から push する。"""
  text = format_urgent_message(
    guest_name=guest_name,
    listing_title=listing_title,
    message_preview=message_preview,
    thread_id=thread_id,
  )
  return await _notify(
    host_id=host_id,
    channel="urgent",
    text=text,
    context=f"urgent thread={thread_id}",
  )


async def notify_auto_reply(
  *,
  host_id: str,
  guest_name: str | None,
  listing_title: str | None,
  guest_message: str,
  reply_text: str,
  thread_id: str,
) -> bool:
  """自動返信完了を①一般通知用 OA から push する。"""
  text = format_auto_reply_message(
    guest_name=guest_name,
    listing_title=listing_title,
    guest_message=guest_message,
    reply_text=reply_text,
    thread_id=thread_id,
  )
  return await _notify(
    host_id=host_id,
    channel="general",
    text=text,
    context=f"auto_reply thread={thread_id}",
  )


async def notify_session_expired(host_id: str) -> bool:
  """セッション切れを②緊急通知用 OA から push する。"""
  return await _notify(
    host_id=host_id,
    channel="urgent",
    text=format_session_expired_message(),
    context="session_expired",
  )


async def send_test_push(host_id: str, channel: LineChannel, message: str) -> bool:
  """開発用テスト push。"""
  return await _notify(
    host_id=host_id,
    channel=channel,
    text=message,
    context="test_push",
  )
