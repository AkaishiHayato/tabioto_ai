"""メッセージポーリング・送信オーケストレーション。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.db.listings import build_listing_info
from app.db.message_threads import (
  get_monitored_listing_ids,
  get_thread,
  resolve_listing_uuid,
  upsert_thread,
)
from app.db.messages import insert_message, update_message_status
from app.db.settings import build_host_policy_info, get_settings
from app.db.client import get_supabase
from app.db.session_store import mark_session_expired, save_session
from app.notifications.line import notify_auto_reply, notify_session_expired, notify_urgent_message
from app.scraper.auth import require_valid_session
from app.scraper.browser import (
  get_browser,
  get_context,
  get_page,
  is_challenge_url,
  is_login_url,
  save_storage_state,
)
from app.scraper.exceptions import ScraperError, SessionExpiredError
from app.scraper.messages.inbox import fetch_unread_threads
from app.scraper.messages.send import send_thread_message
from app.scraper.messages.thread_detail import fetch_thread_last_message, merge_inbox_summary
from app.services.reply_policy import ReplyAction, decide_reply_action

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


def _classify_urgency(message: str) -> bool:
  from app.config import settings

  if not settings.gemini_api_key:
    logger.warning("GEMINI_API_KEY 未設定のため緊急判定をスキップ（通常扱い）")
    return False
  from llm_core.client import classify_message

  return classify_message(message)


def _generate_reply(message: str, listing_record: dict, host_policy_info: str) -> str:
  from llm_core.client import generate_reply

  listing_info = build_listing_info(listing_record)
  return generate_reply(message, listing_info, host_policy_info)


async def poll_messages(host_id: str) -> dict[str, Any]:
  """未読スレッドを巡回し、返信要否判定 → 自動返信 or LINE 通知。"""
  state = await require_valid_session(host_id)
  monitored_ids = get_monitored_listing_ids(host_id)
  settings_row = get_settings(host_id)
  auto_reply_enabled = bool(settings_row.get("auto_reply_enabled", True)) if settings_row else True
  host_policy_info = build_host_policy_info(settings_row)
  results: list[dict[str, Any]] = []

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)

      if is_login_url(page.url) or is_challenge_url(page.url):
        if mark_session_expired(host_id):
          await notify_session_expired(host_id)
        raise SessionExpiredError("Airbnb セッションが切れています")

      summaries = await fetch_unread_threads(page)

      for summary in summaries:
        listing_id = summary.airbnb_listing_ids[0] if summary.airbnb_listing_ids else None
        is_monitored = bool(listing_id and listing_id in monitored_ids)

        detail = await fetch_thread_last_message(page, summary.airbnb_thread_id)
        detail = merge_inbox_summary(summary, detail)
        if not listing_id and detail.airbnb_listing_ids:
          listing_id = detail.airbnb_listing_ids[0]
          is_monitored = bool(listing_id in monitored_ids)

        existing = get_thread(host_id, summary.airbnb_thread_id)
        skip_auto_reply = bool(existing and existing.get("skip_auto_reply"))
        is_new = not existing or existing.get("last_message_hash") != detail.message_hash

        thread_record = upsert_thread(host_id, {
          "airbnb_thread_id": summary.airbnb_thread_id,
          "airbnb_listing_id": listing_id,
          "listing_id": resolve_listing_uuid(host_id, listing_id),
          "guest_name": detail.sender_name if detail.sender_role == "guest" else existing.get("guest_name") if existing else None,
          "thread_title": detail.thread_title,
          "reservation_status": (detail.reservation_status[0] if detail.reservation_status else None),
          "last_sender_role": detail.sender_role,
          "last_sender_name": detail.sender_name,
          "last_message_preview": detail.body[:500],
          "last_message_hash": detail.message_hash,
          "last_message_at": _utc_now_iso() if detail.body else None,
          "skip_auto_reply": skip_auto_reply,
        })

        item: dict[str, Any] = {
          "airbnb_thread_id": summary.airbnb_thread_id,
          "listing_id": listing_id,
          "is_monitored": is_monitored,
          "is_new_message": is_new,
          "sender_role": detail.sender_role,
          "action": "skip",
          "reason": "",
        }

        if not is_new:
          item["reason"] = "新規メッセージなし"
          results.append(item)
          continue

        message_row = insert_message({
          "host_id": host_id,
          "listing_id": thread_record.get("listing_id"),
          "airbnb_thread_id": summary.airbnb_thread_id,
          "airbnb_message_id": detail.message_hash,
          "guest_name": detail.sender_name,
          "guest_message": detail.body,
          "airbnb_thread_url": f"/hosting/messages/{summary.airbnb_thread_id}",
          "status": "new",
        })

        is_urgent: bool | None = None
        if detail.sender_role == "guest" and detail.body.strip():
          try:
            is_urgent = _classify_urgency(detail.body)
          except Exception as e:
            logger.warning("urgency classify failed: %s", e)
            is_urgent = False

        decision = decide_reply_action(
          last_message=detail,
          skip_auto_reply=skip_auto_reply,
          auto_reply_enabled=auto_reply_enabled,
          is_monitored_listing=is_monitored,
          is_new_message=True,
          is_urgent=is_urgent,
        )
        item["action"] = decision.action.value
        item["reason"] = decision.reason
        item["is_urgent"] = is_urgent

        if decision.action == ReplyAction.URGENT_NOTIFY and message_row:
          update_message_status(
            message_row["id"],
            is_urgent=True,
            status="manual_required",
            processed_at=_utc_now_iso(),
          )
          listing_title = None
          if thread_record.get("listing_id"):
            listing_rows = (
              get_supabase()
              .table("listings")
              .select("title")
              .eq("id", thread_record["listing_id"])
              .limit(1)
              .execute()
            )
            if listing_rows.data:
              listing_title = listing_rows.data[0].get("title")
          await notify_urgent_message(
            host_id=host_id,
            guest_name=detail.sender_name,
            listing_title=listing_title,
            message_preview=detail.body,
            thread_id=summary.airbnb_thread_id,
          )

        elif decision.action == ReplyAction.AUTO_REPLY and message_row:
          listing_record = None
          if thread_record.get("listing_id"):
            listing_rows = (
              get_supabase()
              .table("listings")
              .select("*")
              .eq("id", thread_record["listing_id"])
              .limit(1)
              .execute()
            )
            listing_record = listing_rows.data[0] if listing_rows.data else None

          if not listing_record:
            item["action"] = "skip"
            item["reason"] = "リスティング情報なし"
          else:
            reply_text = _generate_reply(detail.body, listing_record, host_policy_info)
            await send_thread_message(page, summary.airbnb_thread_id, reply_text)
            update_message_status(
              message_row["id"],
              is_urgent=False,
              reply_text=reply_text,
              status="auto_replied",
              processed_at=_utc_now_iso(),
            )
            item["reply_text"] = reply_text
            listing_title = listing_record.get("title")
            await notify_auto_reply(
              host_id=host_id,
              guest_name=detail.sender_name,
              listing_title=listing_title,
              guest_message=detail.body,
              reply_text=reply_text,
              thread_id=summary.airbnb_thread_id,
            )

        results.append(item)

      updated_state = await save_storage_state(context)
      save_session(host_id, updated_state)

  return {
    "status": "ok",
    "processed": len(results),
    "results": results,
  }


async def send_message_manual(host_id: str, airbnb_thread_id: str, text: str) -> dict[str, Any]:
  """FE 管理画面からの手動送信（補助ホストとして送信）。"""
  state = await require_valid_session(host_id)

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)
      await send_thread_message(page, airbnb_thread_id, text)
      updated_state = await save_storage_state(context)
      save_session(host_id, updated_state)

  insert_message({
    "host_id": host_id,
    "airbnb_thread_id": airbnb_thread_id,
    "airbnb_message_id": f"{airbnb_thread_id}:manual:{_utc_now_iso()}",
    "guest_name": None,
    "guest_message": "(補助ホスト手動送信)",
    "reply_text": text,
    "status": "manual_replied",
    "processed_at": _utc_now_iso(),
  })

  return {"status": "ok", "airbnb_thread_id": airbnb_thread_id, "sent_text": text}
