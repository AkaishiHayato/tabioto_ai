import json
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.config import settings
from app.scraper.auth.selectors import CHALLENGE_URL_FRAGMENTS, LOGIN_URL_FRAGMENTS

STEALTH_INIT_SCRIPT = (
  'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
)
USER_AGENT = (
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
LAUNCH_ARGS = ["--disable-blink-features=AutomationControlled"]


@asynccontextmanager
async def get_browser(*, headless: bool = True, slow_mo: int = 0):
  """Playwright ブラウザを起動する。"""
  async with async_playwright() as p:
    browser = await p.chromium.launch(
      headless=headless,
      slow_mo=slow_mo,
      args=LAUNCH_ARGS,
    )
    try:
      yield browser
    finally:
      await browser.close()


@asynccontextmanager
async def get_context(browser: Browser, storage_state: dict | None = None):
  """storageState 付きの BrowserContext を作成する。"""
  kwargs: dict = {
    "locale": "ja-JP",
    "timezone_id": "Asia/Tokyo",
    "viewport": {"width": 1280, "height": 720},
    "user_agent": USER_AGENT,
  }

  state_path: Path | None = None
  if storage_state:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
      json.dump(storage_state, f)
      state_path = Path(f.name)
      kwargs["storage_state"] = str(state_path)

  context = await browser.new_context(**kwargs)
  await context.add_init_script(STEALTH_INIT_SCRIPT)
  try:
    yield context
  finally:
    await context.close()
    if state_path:
      state_path.unlink(missing_ok=True)


async def get_page(context: BrowserContext) -> Page:
  return await context.new_page()


async def save_storage_state(context: BrowserContext) -> dict:
  """現在の storageState を dict として返す。"""
  with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    await context.storage_state(path=f.name)
    with open(f.name) as rf:
      state = json.load(rf)
    Path(f.name).unlink(missing_ok=True)
    return state


def is_login_url(url: str) -> bool:
  """URL がログイン系ページかどうか。"""
  lowered = url.lower()
  return any(fragment in lowered for fragment in LOGIN_URL_FRAGMENTS)


def is_challenge_url(url: str) -> bool:
  """URL が 2FA / 認証チャレンジ系かどうか。"""
  lowered = url.lower()
  return any(fragment in lowered for fragment in CHALLENGE_URL_FRAGMENTS)


async def is_hosting_accessible(page: Page) -> bool:
  """ホスティング画面にアクセスできるか確認する。"""
  await page.goto(
    f"{settings.airbnb_base_url}/hosting/listings",
    wait_until="domcontentloaded",
  )
  await page.wait_for_timeout(1500)

  if is_login_url(page.url) or is_challenge_url(page.url):
    return False

  hosting_markers = [
    '[data-testid="listing-card"]',
    '[href*="/hosting/listings/"]',
    'a[href*="/hosting/inbox"]',
    'nav a[href*="/hosting"]',
  ]
  for selector in hosting_markers:
    if await page.locator(selector).count() > 0:
      return True

  return "/hosting/" in page.url and not is_login_url(page.url)
