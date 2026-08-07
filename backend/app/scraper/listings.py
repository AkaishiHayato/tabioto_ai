"""リスティング情報のスクレイピング。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.config import settings
from app.db.client import get_supabase
from app.db.listings import listing_record_from_scrape
from app.db.session_store import mark_session_expired, save_session
from app.scraper.auth import require_valid_session
from app.scraper.browser import (
  get_browser,
  get_context,
  get_page,
  is_challenge_url,
  is_login_url,
  save_storage_state,
)
from app.scraper.cohost import AcceptResult, accept_invite
from app.scraper.exceptions import ScraperError, SessionExpiredError
from app.scraper.listing import discover_listings, scrape_listing
from app.scraper.messages import discover_message_threads

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


def _match_listing_by_title(
  summaries: list[dict[str, str]],
  title: str | None,
) -> str | None:
  if not title:
    return None
  title_norm = title.strip().lower()
  for summary in summaries:
    preview = (summary.get("preview_title") or "").strip().lower()
    if not preview:
      continue
    if title_norm in preview or preview in title_norm:
      return summary["airbnb_listing_id"]
  return None


def _preview_title_for(
  summaries: list[dict[str, str]],
  airbnb_listing_id: str,
) -> str | None:
  for summary in summaries:
    if summary["airbnb_listing_id"] == airbnb_listing_id:
      return summary.get("preview_title") or None
  return None


async def scrape_listing_detail(host_id: str, listing_id: str) -> dict:
  """単一リスティングの詳細を scrape して DB に保存する。"""
  state = await require_valid_session(host_id)

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)
      summaries = await discover_listings(page)
      preview_title = _preview_title_for(summaries, listing_id)
      scraped = await scrape_listing(page, listing_id)

      updated_state = await save_storage_state(context)
      save_session(host_id, updated_state)

  record = listing_record_from_scrape(
    host_id,
    scraped,
    preview_title=preview_title,
    last_scraped_at=_utc_now_iso(),
  )
  db = get_supabase()
  db.table("listings").upsert(
    record,
    on_conflict="host_id,airbnb_listing_id",
  ).execute()
  return record


async def scrape_listings(host_id: str) -> list[dict]:
  """
  ホストのリスティング一覧を取得し、各リスティングの詳細を scrape して DB に保存する。
  """
  state = await require_valid_session(host_id)
  results: list[dict] = []

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)

      summaries = await discover_listings(page)
      if is_login_url(page.url) or is_challenge_url(page.url):
        mark_session_expired(host_id)
        raise SessionExpiredError("Airbnb セッションが切れています")

      if not summaries:
        logger.warning("listing_id が見つかりませんでした: %s/hosting/listings", settings.airbnb_base_url)
        return results

      scraped_at = _utc_now_iso()
      for summary in summaries:
        listing_id = summary["airbnb_listing_id"]
        logger.info("scraping listing %s", listing_id)
        scraped = await scrape_listing(page, listing_id)
        record = listing_record_from_scrape(
          host_id,
          scraped,
          summary.get("preview_title"),
          last_scraped_at=scraped_at,
        )
        results.append(record)

      updated_state = await save_storage_state(context)
      save_session(host_id, updated_state)

  db = get_supabase()
  for record in results:
    db.table("listings").upsert(
      record,
      on_conflict="host_id,airbnb_listing_id",
    ).execute()

  return results


async def sync_listing(
  host_id: str,
  *,
  invite_url: str | None = None,
  airbnb_listing_id: str | None = None,
) -> dict:
  """
  リスティング追加（FE 同期ボタン用）。

  1. 招待 URL があれば共同ホストとして参画
  2. リスティング詳細を scrape して DB に保存
  3. メッセージルーム一覧を取得（未実装の場合は空配列）
  """
  if not invite_url and not airbnb_listing_id:
    raise ValueError("invite_url または airbnb_listing_id が必要です")

  state = await require_valid_session(host_id)
  cohost_result: AcceptResult | None = None
  warnings: list[str] = []
  scraped_at = _utc_now_iso()

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)

      if invite_url:
        logger.info("共同ホスト招待を承認します: %s", invite_url)
        cohost_result = await accept_invite(page, invite_url)
        if not cohost_result.accepted:
          raise ScraperError(cohost_result.message)

      summaries = await discover_listings(page)
      if is_login_url(page.url) or is_challenge_url(page.url):
        mark_session_expired(host_id)
        raise SessionExpiredError("Airbnb セッションが切れています")

      if not airbnb_listing_id:
        listing_title = cohost_result.listing_title if cohost_result else None
        airbnb_listing_id = _match_listing_by_title(summaries, listing_title)
        if not airbnb_listing_id and len(summaries) == 1:
          airbnb_listing_id = summaries[0]["airbnb_listing_id"]
        if not airbnb_listing_id:
          raise ScraperError(
            "airbnb_listing_id を特定できませんでした。"
            "共同ホスト承認後、リクエストに airbnb_listing_id を指定してください。"
          )

      accessible_ids = {summary["airbnb_listing_id"] for summary in summaries}
      if airbnb_listing_id not in accessible_ids:
        raise ScraperError(
          f"リスティング {airbnb_listing_id} に共同ホストとしてアクセスできません。"
          "招待の承認を確認してください。"
        )

      preview_title = _preview_title_for(summaries, airbnb_listing_id)
      logger.info("scraping listing %s", airbnb_listing_id)
      scraped = await scrape_listing(page, airbnb_listing_id)
      record = listing_record_from_scrape(
        host_id,
        scraped,
        preview_title,
        last_scraped_at=scraped_at,
      )

      thread_result = await discover_message_threads(page, airbnb_listing_id)
      if not thread_result.get("implemented"):
        warning = thread_result.get("message")
        if warning:
          warnings.append(warning)

      updated_state = await save_storage_state(context)
      save_session(host_id, updated_state)

  db = get_supabase()
  db.table("listings").upsert(
    record,
    on_conflict="host_id,airbnb_listing_id",
  ).execute()

  return {
    "status": "ok",
    "cohost": cohost_result.__dict__ if cohost_result else None,
    "listing": record,
    "message_threads": thread_result,
    "warnings": warnings,
  }
