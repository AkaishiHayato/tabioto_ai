"""Airbnb リスティング一覧の取得。"""

from __future__ import annotations

import re

from playwright.async_api import Page

from app.config import settings

NUMERIC_LISTING_ID = re.compile(r"^\d+$")


async def discover_listings(page: Page) -> list[dict[str, str]]:
  """
  /hosting/listings から listing_id と概要テキストを取得する。

  listing 行は `main button[data-testid="{listing_id}"]` に格納される。
  """
  await page.goto(
    f"{settings.airbnb_base_url}/hosting/listings",
    wait_until="domcontentloaded",
  )
  await page.wait_for_timeout(4000)

  buttons = page.locator("main button[data-testid]")
  count = await buttons.count()
  listings: list[dict[str, str]] = []
  seen: set[str] = set()

  for i in range(count):
    testid = await buttons.nth(i).get_attribute("data-testid")
    if not testid or not NUMERIC_LISTING_ID.match(testid) or testid in seen:
      continue
    seen.add(testid)

    summary = (await buttons.nth(i).inner_text()).strip()
    lines = [line.strip() for line in summary.split("\n") if line.strip()]
    preview_title = next(
      (line for line in lines if line not in {"公開", "非公開", "下書き"}),
      None,
    )

    listings.append({
      "airbnb_listing_id": testid,
      "preview_title": preview_title or "",
      "summary_text": summary,
    })

  return listings
