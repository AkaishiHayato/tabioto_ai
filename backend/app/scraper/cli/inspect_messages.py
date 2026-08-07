"""メッセージ画面の DOM を調査する（読み取り専用・送信しない）。"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[4] / ".env")

from app.config import settings
from app.scraper.auth import require_valid_session
from app.scraper.browser import get_browser, get_context, get_page

HOST_ID = "907988a2-4fe4-4a50-88ed-da080d92986b"

THREAD_ID_RE = re.compile(r"/hosting/messages/(\d+)")

EXTRACT_JS = """
() => {
  const visible = (el) => {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };

  const threadLinks = [...document.querySelectorAll('a[href*="/hosting/messages/"]')]
    .filter(visible)
    .map((el) => ({
      href: el.getAttribute('href'),
      text: (el.innerText || '').trim().slice(0, 120),
      ariaLabel: el.getAttribute('aria-label'),
      dataTestId: el.getAttribute('data-testid'),
    }))
    .slice(0, 30);

  const dataTestIds = [...document.querySelectorAll('[data-testid]')]
    .filter(visible)
    .map((el) => ({
      testid: el.getAttribute('data-testid'),
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || '').trim().slice(0, 100),
    }))
    .slice(0, 60);

  const listingLinks = [...document.querySelectorAll('a[href*="/hosting/listings"]')]
    .filter(visible)
    .map((el) => ({
      href: el.getAttribute('href'),
      text: (el.innerText || '').trim().slice(0, 80),
    }))
    .slice(0, 20);

  const reservationLinks = [...document.querySelectorAll('a[href*="reservation"], a[href*="Reservation"]')]
    .filter(visible)
    .map((el) => ({
      href: el.getAttribute('href'),
      text: (el.innerText || '').trim().slice(0, 80),
    }))
    .slice(0, 20);

  const messageItems = [...document.querySelectorAll(
    '[data-testid*="message"], [class*="message"], li[role="listitem"]'
  )]
    .filter(visible)
    .map((el) => ({
      testid: el.getAttribute('data-testid'),
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role'),
      text: (el.innerText || '').trim().slice(0, 200),
    }))
    .slice(0, 40);

  const headings = [...document.querySelectorAll('h1,h2,h3,h4')]
    .filter(visible)
    .map((el) => ({
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || '').trim().slice(0, 120),
    }));

  const sidePanelText = (() => {
    const candidates = [...document.querySelectorAll('aside, [role="complementary"], section')]
      .filter(visible);
    for (const el of candidates) {
      const t = (el.innerText || '').trim();
      if (t.includes('予約') || t.includes('チェックイン')) {
        return t.slice(0, 1500);
      }
    }
    return null;
  })();

  return {
    url: location.href,
    pageTitle: document.title,
    headings,
    threadLinks,
    listingLinks,
    reservationLinks,
    messageItems,
    dataTestIds,
    sidePanelText,
    bodyPreview: (document.body?.innerText || '').slice(0, 2000),
  };
}
"""

NETWORK_PATTERNS = (
  "message",
  "thread",
  "inbox",
  "reservation",
  "listing",
  "messaging",
)


def _thread_id_from_url(url: str) -> str | None:
  match = THREAD_ID_RE.search(url)
  return match.group(1) if match else None


async def inspect_messages_page(page, path: str, *, wait_ms: int = 6000) -> dict:
  url = f"{settings.airbnb_base_url}{path}"
  captured: list[dict] = []

  async def on_response(response):
    try:
      req_url = response.url.lower()
      if not any(p in req_url for p in NETWORK_PATTERNS):
        return
      entry = {
        "url": response.url,
        "status": response.status,
        "content_type": response.headers.get("content-type"),
      }
      if "json" in (entry["content_type"] or ""):
        body = await response.text()
        entry["body_preview"] = body[:2000]
      captured.append(entry)
    except Exception as e:
      captured.append({"url": response.url, "error": str(e)})

  page.on("response", on_response)
  await page.goto(url, wait_until="domcontentloaded")
  await page.wait_for_timeout(wait_ms)

  data = await page.evaluate(EXTRACT_JS)
  data["path"] = path
  data["thread_id_from_url"] = _thread_id_from_url(page.url)
  data["redirected_from"] = url if page.url != url else None
  data["network_responses"] = captured[:30]
  return data


async def main() -> None:
  state = await require_valid_session(HOST_ID)
  results: list[dict] = []

  paths = [
    "/hosting/messages?unread=",
    "/hosting/messages",
  ]

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)

      for path in paths:
        print(f"inspecting {path}...", file=sys.stderr)
        try:
          results.append(await inspect_messages_page(page, path))
        except Exception as e:
          results.append({"path": path, "error": str(e)})

      # 未読リダイレクト先のスレッド詳細を追加調査
      unread = next((r for r in results if r.get("path") == "/hosting/messages?unread="), None)
      thread_id = unread.get("thread_id_from_url") if unread else None
      if thread_id:
        detail_path = f"/hosting/messages/{thread_id}"
        print(f"inspecting thread detail {detail_path}...", file=sys.stderr)
        try:
          results.append(await inspect_messages_page(page, detail_path, wait_ms=5000))
        except Exception as e:
          results.append({"path": detail_path, "error": str(e)})

  out = Path(__file__).resolve().parents[1] / "messages_inspect.json"
  out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
  print(out)


if __name__ == "__main__":
  asyncio.run(main())
