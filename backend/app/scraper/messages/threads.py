"""メッセージルーム一覧の取得。"""

from __future__ import annotations

from typing import Any

from playwright.async_api import Page


async def discover_message_threads(
  page: Page,
  airbnb_listing_id: str,
) -> dict[str, Any]:
  """
  リスティングに紐づくメッセージルーム一覧を取得する。

  TODO: /hosting/inbox の DOM 調査後に実装する。
  """
  _ = page
  _ = airbnb_listing_id
  return {
    "threads": [],
    "implemented": False,
    "message": "メッセージルーム取得は未実装です",
  }
