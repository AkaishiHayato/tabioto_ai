"""メッセージ inbox（未読一覧）の取得。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from playwright.async_api import Page

from app.config import settings
from app.scraper.messages.parsers import parse_tags, thread_id_from_graphql, thread_id_from_url
from app.scraper.messages.selectors import INBOX_UNREAD_PATH, PAGE_LOAD_WAIT_MS

logger = logging.getLogger(__name__)


@dataclass
class InboxThreadSummary:
  airbnb_thread_id: str
  airbnb_listing_ids: list[str] = field(default_factory=list)
  is_unread: bool = False
  reservation_status: list[str] = field(default_factory=list)
  thread_type: str | None = None
  title: str | None = None


async def fetch_unread_threads(page: Page) -> list[InboxThreadSummary]:
  """ViaductInboxData から未読スレッド一覧を取得する（読み取り専用）。"""
  inbox_payloads: list[dict] = []

  async def on_response(response):
    if "ViaductInboxData" not in response.url or response.status != 200:
      return
    try:
      inbox_payloads.append(await response.json())
    except Exception:
      pass

  page.on("response", on_response)
  await page.goto(
    f"{settings.airbnb_base_url}{INBOX_UNREAD_PATH}",
    wait_until="domcontentloaded",
  )
  await page.wait_for_timeout(PAGE_LOAD_WAIT_MS)

  summaries: list[InboxThreadSummary] = []
  seen: set[str] = set()

  for payload in inbox_payloads:
    edges = (
      payload.get("data", {})
      .get("node", {})
      .get("messagingInbox", {})
      .get("inboxItems", {})
      .get("edges", [])
    )
    for edge in edges:
      node = edge.get("node") or {}
      thread_id = thread_id_from_graphql(node.get("id", ""))
      if not thread_id or thread_id in seen:
        continue
      seen.add(thread_id)

      tags = parse_tags(node.get("userThreadTags") or [])
      summaries.append(InboxThreadSummary(
        airbnb_thread_id=thread_id,
        airbnb_listing_ids=tags.get("stay_listing_ids", []),
        is_unread="unread" in tags,
        reservation_status=tags.get("reservation_status", []),
        thread_type=node.get("messageThreadType"),
        title=(node.get("inboxTitle") or {}).get("accessibilityText"),
      ))

  if not summaries:
    summaries.extend(await _fetch_threads_from_dom(page))

  logger.info("unread threads found: %d", len(summaries))
  return summaries


async def _fetch_threads_from_dom(page: Page) -> list[InboxThreadSummary]:
  """GraphQL 傍受に失敗した場合の DOM フォールバック。"""
  items = await page.evaluate(
    """
    () => [...document.querySelectorAll('[data-testid^="inbox_list_"]')]
      .map(el => ({
        testid: el.getAttribute('data-testid'),
        href: el.getAttribute('href'),
        text: (el.innerText || '').slice(0, 120),
      }))
    """
  )
  results: list[InboxThreadSummary] = []
  for item in items:
    testid = item.get("testid") or ""
    if not testid.startswith("inbox_list_"):
      continue
    thread_id = testid.replace("inbox_list_", "")
    href = item.get("href") or ""
    url_id = thread_id_from_url(href) if href else None
    results.append(InboxThreadSummary(
      airbnb_thread_id=url_id or thread_id,
      is_unread=True,
    ))
  return results
