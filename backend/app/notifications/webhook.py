"""LINE Webhook 署名検証・イベント処理。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from typing import Any

from app.db.hosts import LineChannel, clear_line_user_id, get_host, update_line_user_id

logger = logging.getLogger(__name__)


def verify_line_signature(body: bytes, signature: str | None, channel_secret: str) -> bool:
  if not channel_secret:
    return False
  if not signature:
    return False
  digest = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
  expected = base64.b64encode(digest).decode("utf-8")
  return hmac.compare_digest(expected, signature)


def handle_webhook_events(
  host_id: str,
  channel: LineChannel,
  payload: dict[str, Any],
) -> dict[str, Any]:
  host = get_host(host_id)
  if not host:
    raise ValueError(f"host not found: {host_id}")

  events = payload.get("events") or []
  handled: list[dict[str, Any]] = []

  for event in events:
    event_type = event.get("type")
    source = event.get("source") or {}
    user_id = source.get("userId")

    if event_type == "follow" and user_id:
      update_line_user_id(host_id, channel, user_id)
      handled.append({"type": event_type, "user_id": user_id, "action": "linked"})
      logger.info("LINE follow linked host=%s channel=%s user=%s", host_id, channel, user_id)
      continue

    if event_type == "unfollow":
      clear_line_user_id(host_id, channel)
      handled.append({"type": event_type, "action": "cleared"})
      logger.info("LINE unfollow cleared host=%s channel=%s", host_id, channel)
      continue

    handled.append({"type": event_type, "action": "ignored"})

  return {"host_id": host_id, "channel": channel, "events": handled}
