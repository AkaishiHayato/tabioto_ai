"""リスティングに紐づくメッセージルーム一覧（同期 API 用）。"""

from __future__ import annotations

from typing import Any

from playwright.async_api import Page

from app.scraper.messages.inbox import fetch_unread_threads


async def discover_message_threads(
  page: Page,
  airbnb_listing_id: str,
) -> dict[str, Any]:
  """監視対象 listing に紐づく未読スレッド一覧を返す。"""
  summaries = await fetch_unread_threads(page)
  matched = [
    {
      "airbnb_thread_id": summary.airbnb_thread_id,
      "thread_title": summary.title,
      "is_unread": summary.is_unread,
      "reservation_status": summary.reservation_status,
    }
    for summary in summaries
    if airbnb_listing_id in summary.airbnb_listing_ids
  ]
  return {
    "threads": matched,
    "implemented": True,
    "message": None,
  }
