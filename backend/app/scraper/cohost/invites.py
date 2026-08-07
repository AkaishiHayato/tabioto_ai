"""補助ホスト招待の検知・承認。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import urljoin

from playwright.async_api import Page

from app.config import settings
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
from app.scraper.exceptions import SessionExpiredError
from app.scraper.cohost.selectors import (
  COHOST_INVITE_URL_PATTERN,
  IDENTITY_VERIFICATION_PATH,
  NOTIFICATIONS_PATH,
)

logger = logging.getLogger(__name__)

INVITE_CODE_PATTERN = re.compile(r"code=([A-Z0-9]+)")
IDENTITY_VERIFICATION_TEXTS = (
  "本人確認の完了後",
  "政府発行の身分証明書",
  "身分証明書を登録",
  "Verify your identity",
  "identity verification",
)
ALREADY_ACCEPTED_TEXTS = (
  "すでに承認",
  "already accepted",
)


@dataclass
class CohostInvite:
  invite_url: str
  invite_code: str | None
  listing_title: str | None


@dataclass
class AcceptResult:
  invite_url: str
  accepted: bool
  listing_title: str | None
  message: str


async def _extract_listing_title(page: Page) -> str | None:
  for selector in ["h1", "h2", '[data-testid*="listing"]']:
    locator = page.locator(selector).first
    try:
      if await locator.is_visible(timeout=2000):
        text = (await locator.inner_text()).strip()
        if text and len(text) > 5:
          return text
    except Exception:
      continue
  return None


async def find_pending_invites(page: Page) -> list[CohostInvite]:
  """通知ページから未承認の補助ホスト招待 URL を収集する。"""
  await page.goto(
    f"{settings.airbnb_base_url}{NOTIFICATIONS_PATH}",
    wait_until="domcontentloaded",
  )
  await page.wait_for_timeout(2000)

  if is_login_url(page.url) or is_challenge_url(page.url):
    raise SessionExpiredError("セッションが切れています")

  invites: list[CohostInvite] = []
  seen_urls: set[str] = set()

  links = page.locator(f'a[href*="{COHOST_INVITE_URL_PATTERN}"]')
  count = await links.count()

  for i in range(count):
    href = await links.nth(i).get_attribute("href")
    if not href:
      continue

    invite_url = urljoin(settings.airbnb_base_url, href)
    if invite_url in seen_urls:
      continue
    seen_urls.add(invite_url)

    match = INVITE_CODE_PATTERN.search(invite_url)
    invites.append(CohostInvite(
      invite_url=invite_url,
      invite_code=match.group(1) if match else None,
      listing_title=None,
    ))

  return invites


async def _page_body(page: Page) -> str:
  return await page.locator("body").inner_text()


async def _needs_identity_verification(page: Page) -> bool:
  if IDENTITY_VERIFICATION_PATH in page.url:
    return True
  body = await _page_body(page)
  return any(text in body for text in IDENTITY_VERIFICATION_TEXTS)


async def _invite_accepted(page: Page, before_url: str) -> bool:
  if page.url != before_url:
    return True
  body = await _page_body(page)
  if any(text in body for text in ALREADY_ACCEPTED_TEXTS):
    return True
  if await page.locator('button:has-text("招待を承認")').count() == 0:
    return True
  return False


async def accept_invite(page: Page, invite_url: str) -> AcceptResult:
  """招待ページを開き「招待を承認」をクリックする。"""
  await page.goto(invite_url, wait_until="domcontentloaded")
  await page.wait_for_timeout(2000)

  if is_login_url(page.url):
    raise SessionExpiredError("セッションが切れています")

  listing_title = await _extract_listing_title(page)

  if await _needs_identity_verification(page):
    return AcceptResult(
      invite_url=invite_url,
      accepted=False,
      listing_title=listing_title,
      message="本人確認が未完了のため招待を承認できません。Airbnb で本人確認を完了してください。",
    )

  before_url = page.url
  btn = page.get_by_role("button", name="招待を承認")
  if await btn.count() == 0:
    return AcceptResult(
      invite_url=invite_url,
      accepted=False,
      listing_title=listing_title,
      message="「招待を承認」ボタンが見つかりませんでした（承認済みの可能性）",
    )

  await btn.click()
  await page.wait_for_timeout(5000)

  if IDENTITY_VERIFICATION_PATH in page.url or await _needs_identity_verification(page):
    return AcceptResult(
      invite_url=invite_url,
      accepted=False,
      listing_title=listing_title,
      message=(
        "「招待を承認」後に本人確認ページへ遷移しました。"
        "運転免許証と自撮りで本人確認を完了してください。"
        f" ({page.url})"
      ),
    )

  if await _invite_accepted(page, before_url):
    return AcceptResult(
      invite_url=invite_url,
      accepted=True,
      listing_title=listing_title,
      message="招待を承認しました",
    )

  return AcceptResult(
    invite_url=invite_url,
    accepted=False,
    listing_title=listing_title,
    message="「招待を承認」をクリックしましたが、承認が完了しませんでした",
  )


async def accept_invites_from_notifications(host_id: str) -> list[AcceptResult]:
  """
  通知ページから補助ホスト招待を検知し、すべて承認する。

  フロー:
  1. /notifications にアクセス
  2. accept-invite リンクを収集
  3. 各招待ページで「招待を承認」をクリック
  """
  state = await require_valid_session(host_id)
  results: list[AcceptResult] = []

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)

      invites = await find_pending_invites(page)
      if not invites:
        logger.info("未承認の補助ホスト招待はありません")
        return results

      for invite in invites:
        logger.info("招待を承認します: %s", invite.invite_url)
        result = await accept_invite(page, invite.invite_url)
        results.append(result)

      updated_state = await save_storage_state(context)
      save_session(host_id, updated_state)

  return results


async def accept_invite_by_url(host_id: str, invite_url: str) -> AcceptResult:
  """招待 URL を直接指定して承認する。"""
  state = await require_valid_session(host_id)

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)
      result = await accept_invite(page, invite_url)

      updated_state = await save_storage_state(context)
      save_session(host_id, updated_state)

  return result
