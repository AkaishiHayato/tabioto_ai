"""リスティング編集ツール scrape のオーケストレーション。"""

from __future__ import annotations

import logging
from typing import Any

from playwright.async_api import Page

from app.scraper.listing.pages.arrival import (
  scrape_check_in_method,
  scrape_check_in_out,
  scrape_checkout_instructions,
  scrape_directions,
  scrape_guidebooks,
  scrape_house_manual,
  scrape_wifi,
)
from app.scraper.listing.pages.details import (
  scrape_accessibility,
  scrape_amenities,
  scrape_cancellation_policy,
  scrape_description,
  scrape_guest_safety,
  scrape_house_rules,
  scrape_instant_book,
  scrape_location,
  scrape_max_guests,
  scrape_property_type,
  scrape_sleeping_arrangements,
  scrape_title,
)

logger = logging.getLogger(__name__)

LISTING_SCRAPERS = [
  # details
  ("title", scrape_title),
  ("property_type", scrape_property_type),
  ("sleeping_arrangements", scrape_sleeping_arrangements),
  ("max_guests", scrape_max_guests),
  ("description", scrape_description),
  ("amenities", scrape_amenities),
  ("accessibility", scrape_accessibility),
  ("location", scrape_location),
  ("instant_book", scrape_instant_book),
  ("house_rules", scrape_house_rules),
  ("guest_safety", scrape_guest_safety),
  ("cancellation_policy", scrape_cancellation_policy),
  # arrival（house-rules は details と重複のため省略）
  ("check_in_out", scrape_check_in_out),
  ("directions", scrape_directions),
  ("check_in_method", scrape_check_in_method),
  ("wifi", scrape_wifi),
  ("house_manual", scrape_house_manual),
  ("checkout_instructions", scrape_checkout_instructions),
  ("guidebooks", scrape_guidebooks),
]

_TOP_LEVEL_KEYS = frozenset({
  "title",
  "description",
  "address",
  "check_in_time",
  "check_out_time",
  "house_rules",
  "amenities",
})


async def scrape_listing(page: Page, listing_id: str) -> dict[str, Any]:
  """編集ツールの保存対象ページを scrape して統合 dict を返す。"""
  result: dict[str, Any] = {
    "airbnb_listing_id": listing_id,
    "title": None,
    "description": None,
    "address": None,
    "check_in_time": None,
    "check_out_time": None,
    "house_rules": None,
    "amenities": None,
    "raw_data": {},
  }

  for name, scraper in LISTING_SCRAPERS:
    try:
      data = await scraper(page, listing_id)
    except Exception as e:
      logger.warning("scrape failed listing=%s step=%s: %s", listing_id, name, e)
      result["raw_data"].setdefault("_errors", {})[name] = str(e)
      continue

    for key, value in data.items():
      if key in _TOP_LEVEL_KEYS:
        if value is not None:
          result[key] = value
      else:
        result["raw_data"][key] = value

  return result
