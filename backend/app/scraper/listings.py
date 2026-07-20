"""リスティング情報のスクレイピング。"""

from app.config import settings
from app.db.client import get_supabase
from app.db.session_store import mark_session_expired, save_session
from app.scraper.auth import require_valid_session
from app.scraper.exceptions import SessionExpiredError
from app.scraper.browser import (
  get_browser,
  get_context,
  get_page,
  is_challenge_url,
  is_login_url,
  save_storage_state,
)


async def scrape_listings(host_id: str) -> list[dict]:
  """
  ホストのリスティング一覧をスクレイピングし、DB に保存する。
  戻り値: スクレイピングしたリスティング情報のリスト
  """
  state = await require_valid_session(host_id)
  listings: list[dict] = []

  async with get_browser() as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)
      await page.goto(
        f"{settings.airbnb_base_url}/hosting/listings",
        wait_until="domcontentloaded",
      )
      await page.wait_for_timeout(2000)

      if is_login_url(page.url) or is_challenge_url(page.url):
        mark_session_expired(host_id)
        raise SessionExpiredError("Airbnb セッションが切れています")

      listing_elements = await page.query_selector_all('[data-testid="listing-card"]')

      for el in listing_elements:
        title_el = await el.query_selector("h2")
        link_el = await el.query_selector("a")

        title = await title_el.inner_text() if title_el else None
        href = await link_el.get_attribute("href") if link_el else None
        airbnb_id = href.split("/")[-1] if href else None

        if not airbnb_id:
          continue

        listings.append({
          "host_id": host_id,
          "airbnb_listing_id": airbnb_id,
          "title": title,
          "status": "active",
        })

      updated_state = await save_storage_state(context)
      save_session(host_id, updated_state)

  db = get_supabase()
  for listing in listings:
    db.table("listings").upsert(
      listing,
      on_conflict="airbnb_listing_id",
    ).execute()

  return listings
