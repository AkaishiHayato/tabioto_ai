"""メッセージ送信（FE 手動送信・自動返信のみ。ポーリングでは呼ばない）。"""

from __future__ import annotations

import logging

from playwright.async_api import Page

from app.config import settings
from app.scraper.exceptions import ScraperError
from app.scraper.messages.selectors import (
  COMPOSE_BAR,
  SEND_BUTTON,
  THREAD_LOAD_WAIT_MS,
)

logger = logging.getLogger(__name__)


async def send_thread_message(page: Page, thread_id: str, text: str) -> None:
  """
  スレッドにメッセージを送信する。

  ⚠️ 明示的に API / 自動返信判定後のみ呼び出すこと。
  """
  text = text.strip()
  if not text:
    raise ScraperError("送信テキストが空です")

  await page.goto(
    f"{settings.airbnb_base_url}/hosting/messages/{thread_id}",
    wait_until="domcontentloaded",
  )
  await page.wait_for_timeout(THREAD_LOAD_WAIT_MS)

  compose = page.locator(COMPOSE_BAR).first
  if await compose.count() == 0:
    raise ScraperError("メッセージ入力欄が見つかりません")

  await compose.click()
  await compose.fill(text)
  await page.wait_for_timeout(500)

  send_btn = page.locator(SEND_BUTTON).first
  if await send_btn.count() == 0:
    raise ScraperError("送信ボタンが見つかりません")
  if not await send_btn.is_enabled():
    raise ScraperError("送信ボタンが無効です")

  await send_btn.click()
  await page.wait_for_timeout(2000)
  logger.info("message sent thread=%s len=%d", thread_id, len(text))
