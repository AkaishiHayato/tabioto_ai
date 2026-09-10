"""Airbnb ログイン・セッション管理。"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import Locator, Page

from app.config import settings
from app.db.session_store import load_session, mark_session_expired, save_session
from app.notifications.line import notify_session_expired
from app.scraper.browser import (
  get_browser,
  get_context,
  get_page,
  is_challenge_url,
  is_hosting_accessible,
  is_login_url,
  save_storage_state,
)
from app.scraper.exceptions import (
  LoginError,
  ManualLoginRequiredError,
  SessionExpiredError,
  SessionNotFoundError,
)
from app.scraper.auth.selectors import (
  CONTINUE_BUTTONS,
  EMAIL_INPUTS,
  OTP_INPUT,
  PASSWORD_CONTINUE_BUTTONS,
  PASSWORD_INPUTS,
  PASSWORD_OPTION_BUTTONS,
  TRY_ANOTHER_METHOD_BUTTONS,
)

logger = logging.getLogger(__name__)

LOGIN_PATH = "/login"
DEFAULT_LOGIN_TIMEOUT_MS = 300_000
POST_ACTION_WAIT_MS = 5000


@dataclass
class LoginResult:
  success: bool
  method: str
  message: str


async def _first_visible(page: Page, selectors: list[str]) -> Locator | None:
  for selector in selectors:
    locator = page.locator(selector).first
    try:
      if await locator.is_visible(timeout=1000):
        return locator
    except Exception:
      continue
  return None


async def _fill_first(page: Page, selectors: list[str], value: str) -> bool:
  locator = await _first_visible(page, selectors)
  if not locator:
    return False
  await locator.click()
  await locator.fill(value)
  return True


async def _click_first(page: Page, selectors: list[str]) -> bool:
  locator = await _first_visible(page, selectors)
  if not locator:
    return False
  await locator.click()
  return True


async def _goto_login(page: Page) -> None:
  await page.goto(f"{settings.airbnb_base_url}{LOGIN_PATH}", wait_until="domcontentloaded")
  await page.wait_for_timeout(1500)


async def _is_otp_screen(page: Page) -> bool:
  otp = page.locator(OTP_INPUT).first
  try:
    return await otp.is_visible(timeout=1000)
  except Exception:
    return False


async def _switch_to_password_screen(page: Page) -> None:
  """
  確認コード画面 → 「別の方法を試す」→「パスワードを入力」→ パスワード画面。

  ⚠️「新しいコードを送信」は絶対にクリックしない（OTP メールが再送される）。
  """
  if await _first_visible(page, PASSWORD_INPUTS):
    return

  if await _is_otp_screen(page):
    if not await _click_first(page, TRY_ANOTHER_METHOD_BUTTONS):
      raise LoginError("「別の方法を試す」ボタンが見つかりませんでした")
    await page.wait_for_timeout(1500)

  if not await _click_first(page, PASSWORD_OPTION_BUTTONS):
    raise LoginError("「パスワードを入力」オプションが見つかりませんでした")
  await page.wait_for_timeout(1500)

  if not await _first_visible(page, PASSWORD_INPUTS):
    raise LoginError("パスワード入力画面へ遷移できませんでした")


async def _detect_manual_step(page: Page) -> bool:
  """OTP コード入力待ち・CAPTCHA 等、自動化できない状態。"""
  if is_challenge_url(page.url):
    return True

  if await _is_otp_screen(page):
    return True

  challenge_texts = [
    "verification code",
    "confirm your identity",
    "ご本人確認が必要です",
    "captcha",
  ]
  body = (await page.locator("body").inner_text()).lower()
  return any(text.lower() in body for text in challenge_texts)


async def _automated_login_steps(page: Page, email: str, password: str) -> None:
  """
  確認済みフロー:
  1. メール入力 → 続行
  2. OTP 画面 → 別の方法を試す → パスワードを入力
  3. パスワード入力 → 続行
  """
  await _goto_login(page)

  if not await _fill_first(page, EMAIL_INPUTS, email):
    raise LoginError("メール入力欄が見つかりませんでした")
  if not await _click_first(page, CONTINUE_BUTTONS):
    raise LoginError("「続行」ボタンが見つかりませんでした")

  await page.wait_for_timeout(POST_ACTION_WAIT_MS)
  await _switch_to_password_screen(page)

  if not await _fill_first(page, PASSWORD_INPUTS, password):
    raise LoginError("パスワード入力欄が見つかりませんでした")
  if not await _click_first(page, PASSWORD_CONTINUE_BUTTONS):
    raise LoginError("パスワード画面の「続行」ボタンが見つかりませんでした")

  await page.wait_for_timeout(POST_ACTION_WAIT_MS)

  if await _detect_manual_step(page):
    raise ManualLoginRequiredError("追加認証が必要です。interactive ログインを使用してください")


async def wait_until_logged_in(page: Page, timeout_ms: int = DEFAULT_LOGIN_TIMEOUT_MS) -> bool:
  """手動ログイン完了まで待機する。"""
  deadline = time.monotonic() + timeout_ms / 1000

  while time.monotonic() < deadline:
    if await is_hosting_accessible(page):
      return True
    await page.wait_for_timeout(2000)

  return False


async def _persist_session(host_id: str, context) -> LoginResult:
  state = await save_storage_state(context)
  save_session(host_id, state)
  return LoginResult(
    success=True,
    method="saved",
    message="storageState を Supabase に保存しました",
  )


async def login_automated(host_id: str, email: str, password: str) -> LoginResult:
  """メール/パスワードで自動ログインを試行する。"""
  async with get_browser(headless=True) as browser:
    async with get_context(browser) as context:
      page = await get_page(context)
      await _automated_login_steps(page, email, password)

      if not await wait_until_logged_in(page, timeout_ms=30_000):
        if await _detect_manual_step(page):
          raise ManualLoginRequiredError("追加認証が必要です。interactive ログインを使用してください")
        raise LoginError("ログイン後にホスティング画面へアクセスできませんでした")

      return await _persist_session(host_id, context)


async def login_interactive(
  host_id: str,
  *,
  email: str | None = None,
  password: str | None = None,
  timeout_ms: int = DEFAULT_LOGIN_TIMEOUT_MS,
  headless: bool = False,
) -> LoginResult:
  """
  ブラウザを表示してログインを完了させる。
  メール/パスワードを事前入力し、OTP 画面以降は手動操作も可能。
  """
  async with get_browser(headless=headless) as browser:
    async with get_context(browser) as context:
      page = await get_page(context)
      await _goto_login(page)

      if email:
        await _fill_first(page, EMAIL_INPUTS, email)
        await _click_first(page, CONTINUE_BUTTONS)
        await page.wait_for_timeout(POST_ACTION_WAIT_MS)

        try:
          await _switch_to_password_screen(page)
        except LoginError:
          logger.info("パスワード画面への自動遷移をスキップ。手動操作を待ちます。")

      if password and await _first_visible(page, PASSWORD_INPUTS):
        await _fill_first(page, PASSWORD_INPUTS, password)
        await _click_first(page, PASSWORD_CONTINUE_BUTTONS)
        await page.wait_for_timeout(POST_ACTION_WAIT_MS)

      logger.info("ブラウザでログインを完了してください")

      if not await wait_until_logged_in(page, timeout_ms=timeout_ms):
        raise LoginError("ログイン待機がタイムアウトしました")

      return await _persist_session(host_id, context)


async def import_session_state(host_id: str, state: dict) -> LoginResult:
  """Playwright storageState JSON を直接インポートする。"""
  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)
      if not await is_hosting_accessible(page):
        raise SessionExpiredError("インポートした storageState は無効です")

      updated = await save_storage_state(context)
      save_session(host_id, updated)
      return LoginResult(
        success=True,
        method="import",
        message="storageState をインポートしました",
      )


async def import_session_via_cdp(
  host_id: str, cdp_url: str = "http://localhost:9222"
) -> LoginResult:
  """既にログイン済みの Chrome（--remote-debugging-port 起動）に接続し、
  そのセッションの storageState を取り込む。

  ログインフォームの送信を一切自動化しないため、Airbnb 側の自動操作検知
  （ログインが即座に差し戻される事象）を回避できる。ログイン自体は人間が
  普段通りの Chrome で行い、Playwright はログイン後の状態を読み取るだけ。
  """
  from playwright.async_api import async_playwright

  async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp(cdp_url)
    if not browser.contexts:
      raise LoginError(f"{cdp_url} に接続しましたが、アクティブなブラウザセッションが見つかりません")

    context = browser.contexts[0]
    page = context.pages[0] if context.pages else await context.new_page()

    if not await is_hosting_accessible(page):
      raise LoginError(
        "接続先のブラウザで Airbnb にログインし、"
        "/hosting/listings にアクセスできる状態にしてください"
      )

    updated = await save_storage_state(context)
    save_session(host_id, updated)
    return LoginResult(
      success=True,
      method="cdp_import",
      message="接続中のブラウザから Airbnb セッションを取り込みました",
    )


async def validate_session(host_id: str) -> bool:
  """保存済みセッションが有効かどうかを確認する。"""
  state = load_session(host_id)
  if not state:
    return False

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)
      valid = await is_hosting_accessible(page)

      if not valid:
        if mark_session_expired(host_id):
          await notify_session_expired(host_id)
        return False

      updated_state = await save_storage_state(context)
      save_session(host_id, updated_state)
      return True


async def require_valid_session(host_id: str) -> dict:
  """有効な storageState を返す。無効なら例外。"""
  state = load_session(host_id)
  if not state:
    raise SessionNotFoundError("Airbnb セッションがありません。先にログインしてください")

  if not await validate_session(host_id):
    raise SessionExpiredError("Airbnb セッションが切れています。再ログインしてください")

  reloaded = load_session(host_id)
  if not reloaded:
    raise SessionNotFoundError("セッションの読み込みに失敗しました")
  return reloaded


async def save_debug_screenshot(page: Page, path: Path) -> None:
  """デバッグ用スクリーンショットを保存する。"""
  path.parent.mkdir(parents=True, exist_ok=True)
  await page.screenshot(path=str(path), full_page=True)


async def login_and_save_session(host_id: str, email: str, password: str) -> bool:
  try:
    result = await login_automated(host_id, email, password)
    return result.success
  except ManualLoginRequiredError:
    return False
