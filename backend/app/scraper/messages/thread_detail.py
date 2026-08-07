"""スレッド詳細（最新メッセージ）の取得。"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from playwright.async_api import Page

from app.config import settings
from app.scraper.messages.inbox import InboxThreadSummary
from app.scraper.messages.parsers import (
  has_scheduled_quick_reply,
  message_fingerprint,
  parse_last_message_text,
  parse_tags,
)
from app.scraper.messages.selectors import (
  THREAD_HEADER_TITLE,
  THREAD_LAST_MESSAGE,
  THREAD_LOAD_WAIT_MS,
)

logger = logging.getLogger(__name__)


@dataclass
class ThreadLastMessage:
  airbnb_thread_id: str
  sender_name: str | None
  sender_role: str
  body: str
  message_hash: str
  thread_title: str | None
  airbnb_listing_ids: list[str]
  reservation_status: list[str]
  has_scheduled_reply: bool


async def fetch_thread_last_message(
  page: Page,
  thread_id: str,
) -> ThreadLastMessage:
  """スレッドを開き最新メッセージを取得する（読み取り専用）。"""
  thread_tags: dict[str, list[str]] = {}

  async def on_response(response):
    if "ViaductGetThreadAndDataQuery" not in response.url or response.status != 200:
      return
    try:
      payload = await response.json()
      td = payload.get("data", {}).get("threadData") or {}
      thread_tags.update(parse_tags(td.get("userThreadTags") or []))
    except Exception:
      pass

  page.on("response", on_response)
  await page.goto(
    f"{settings.airbnb_base_url}/hosting/messages/{thread_id}",
    wait_until="domcontentloaded",
  )
  await page.wait_for_timeout(THREAD_LOAD_WAIT_MS)

  raw_last = await page.locator(THREAD_LAST_MESSAGE).first.inner_text()
  parsed = parse_last_message_text(raw_last)
  page_text = await page.locator("body").inner_text()
  title_locator = page.locator(THREAD_HEADER_TITLE).first
  thread_title = None
  if await title_locator.count() > 0:
    thread_title = (await title_locator.inner_text()).strip() or None

  body = parsed.get("body") or ""
  return ThreadLastMessage(
    airbnb_thread_id=thread_id,
    sender_name=parsed.get("sender_name"),
    sender_role=parsed.get("sender_role") or "system",
    body=body,
    message_hash=message_fingerprint(thread_id, body),
    thread_title=thread_title,
    airbnb_listing_ids=thread_tags.get("stay_listing_ids", []),
    reservation_status=thread_tags.get("reservation_status", []),
    has_scheduled_reply=has_scheduled_quick_reply(page_text),
  )


def merge_inbox_summary(
  summary: InboxThreadSummary,
  detail: ThreadLastMessage,
) -> ThreadLastMessage:
  """inbox 側の listing 情報を detail にマージする。"""
  if summary.airbnb_listing_ids and not detail.airbnb_listing_ids:
    detail.airbnb_listing_ids = summary.airbnb_listing_ids
  if summary.reservation_status and not detail.reservation_status:
    detail.reservation_status = summary.reservation_status
  if summary.title and not detail.thread_title:
    detail.thread_title = summary.title
  return detail
