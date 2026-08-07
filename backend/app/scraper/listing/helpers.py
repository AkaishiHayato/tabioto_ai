"""リスティング編集ツール scrape 用の Playwright ヘルパー。"""

from __future__ import annotations

import time

from playwright.async_api import Page

from app.config import settings
from app.scraper.listing.selectors import PAGE_LOAD_WAIT_MS

TITLE_INPUT_WAIT_MS = 10_000


def editor_url(listing_id: str, section: str, slug: str) -> str:
  return (
    f"{settings.airbnb_base_url}/hosting/listings/editor/"
    f"{listing_id}/{section}/{slug}"
  )


async def goto_editor_page(page: Page, listing_id: str, section: str, slug: str) -> None:
  await page.goto(
    editor_url(listing_id, section, slug),
    wait_until="domcontentloaded",
  )
  await page.wait_for_timeout(PAGE_LOAD_WAIT_MS)


async def input_value(page: Page, selector: str) -> str | None:
  locator = page.locator(selector).first
  try:
    if await locator.count() == 0:
      return None
    value = await locator.input_value()
    if value and value.strip():
      return value.strip()
    attr = await locator.get_attribute("value")
    return attr.strip() if attr else None
  except Exception:
    return None


async def wait_input_value(
  page: Page,
  selector: str,
  *,
  timeout_ms: int = TITLE_INPUT_WAIT_MS,
) -> str | None:
  """SPA の hydration 後に値が入る input/textarea を待って取得する。"""
  locator = page.locator(selector).first
  try:
    await locator.wait_for(state="attached", timeout=timeout_ms)
  except Exception:
    return await input_value(page, selector)

  deadline = time.monotonic() + timeout_ms / 1000
  while time.monotonic() < deadline:
    value = await input_value(page, selector)
    if value:
      return value
    await page.wait_for_timeout(250)

  return await input_value(page, selector)


async def select_value(page: Page, selector: str) -> str | None:
  locator = page.locator(selector).first
  try:
    if await locator.count() == 0:
      return None
    value = await locator.input_value()
    return value if value else None
  except Exception:
    return None


async def radio_yes_checked(page: Page, prefix: str) -> bool | None:
  yes = page.locator(f"#{prefix}-yes").first
  no = page.locator(f"#{prefix}-no").first
  try:
    if await yes.count() == 0 or await no.count() == 0:
      return None
    if await yes.is_checked():
      return True
    if await no.is_checked():
      return False
  except Exception:
    return None
  return None


async def switch_checked(page: Page, selector: str) -> bool | None:
  locator = page.locator(selector).first
  try:
    if await locator.count() == 0:
      return None
    checked = await locator.get_attribute("aria-checked")
    if checked is None:
      return None
    return checked.lower() == "true"
  except Exception:
    return None


def format_hour(value: str | None) -> str | None:
  """Airbnb の時刻 select 値（例: '16', '-1'）を表示用に変換する。"""
  if value is None or value == "":
    return None
  if value == "-1":
    return "flexible"
  if value.isdigit():
    return f"{int(value):02d}:00"
  return value
