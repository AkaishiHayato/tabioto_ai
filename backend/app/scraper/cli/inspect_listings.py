"""リスティング編集ツール各ページの DOM を調査する（一時スクリプト）。"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[4] / ".env")

from app.config import settings
from app.scraper.auth import require_valid_session
from app.scraper.browser import get_browser, get_context, get_page

HOST_ID = "907988a2-4fe4-4a50-88ed-da080d92986b"
LISTING_ID = "1564264295874414302"

PAGES = [
  ("details", "photo-tour", False),
  ("details", "title", True),
  ("details", "property-type", True),
  ("details", "sleeping-arrangements", True),
  ("details", "number-of-guests", True),
  ("details", "description", True),
  ("details", "amenities", True),
  ("details", "accessibility", True),
  ("details", "location", True),
  ("details", "host", False),
  ("details", "co-hosts", False),
  ("details", "instant-book", True),
  ("details", "house-rules", True),
  ("details", "guest-safety", True),
  ("details", "cancellation-policy", True),
  ("details", "custom-link", False),
  ("arrival", "check-in-out", True),
  ("arrival", "directions", True),
  ("arrival", "check-in-method", True),
  ("arrival", "wifi-details", True),
  ("arrival", "house-manual", True),
  ("arrival", "house-rules", True),
  ("arrival", "checkout-instructions", True),
  ("arrival", "guidebooks", True),
  ("arrival", "interaction-preferences", False),
]

EXTRACT_JS = """
() => {
  const visible = (el) => {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };

  const headings = [...document.querySelectorAll('h1,h2,h3,h4')]
    .filter(visible)
    .map(el => ({ tag: el.tagName.toLowerCase(), text: el.innerText.trim().slice(0, 120) }))
    .filter(h => h.text);

  const inputs = [...document.querySelectorAll('input, textarea, select')]
    .filter(visible)
    .map(el => ({
      tag: el.tagName.toLowerCase(),
      type: el.type || null,
      id: el.id || null,
      name: el.name || null,
      placeholder: el.placeholder || null,
      value: (el.value || '').slice(0, 200),
      ariaLabel: el.getAttribute('aria-label') || null,
      checked: el.type === 'checkbox' || el.type === 'radio' ? el.checked : null,
    }));

  const toggles = [...document.querySelectorAll('[role="switch"], [role="checkbox"]')]
    .filter(visible)
    .map(el => ({
      role: el.getAttribute('role'),
      ariaLabel: el.getAttribute('aria-label') || el.innerText.trim().slice(0, 80),
      ariaChecked: el.getAttribute('aria-checked'),
    }));

  const buttons = [...document.querySelectorAll('button')]
    .filter(visible)
    .map(el => el.innerText.trim())
    .filter(t => t && t.length < 80)
    .slice(0, 20);

  const listItems = [...document.querySelectorAll('li')]
    .filter(visible)
    .map(el => el.innerText.trim())
    .filter(t => t && t.length < 120)
    .slice(0, 30);

  const dataTestIds = [...document.querySelectorAll('[data-testid]')]
    .filter(visible)
    .map(el => ({
      testid: el.getAttribute('data-testid'),
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || '').trim().slice(0, 80),
    }))
    .slice(0, 40);

  return {
    url: location.href,
    pageTitle: document.title,
    headings,
    inputs,
    toggles,
    buttons,
    listItems,
    dataTestIds,
  };
}
"""


async def inspect_page(page, section: str, slug: str) -> dict:
  url = (
    f"{settings.airbnb_base_url}/hosting/listings/editor/"
    f"{LISTING_ID}/{section}/{slug}"
  )
  await page.goto(url, wait_until="domcontentloaded")
  await page.wait_for_timeout(3500)
  data = await page.evaluate(EXTRACT_JS)
  data["section"] = section
  data["slug"] = slug
  return data


async def main() -> None:
  state = await require_valid_session(HOST_ID)
  results: list[dict] = []

  async with get_browser(headless=True) as browser:
    async with get_context(browser, storage_state=state) as context:
      page = await get_page(context)
      for section, slug, _save in PAGES:
        print(f"inspecting {section}/{slug}...", file=sys.stderr)
        try:
          results.append(await inspect_page(page, section, slug))
        except Exception as e:
          results.append({
            "section": section,
            "slug": slug,
            "error": str(e),
          })

  out = Path(__file__).resolve().parents[1] / "listing_editor_inspect.json"
  out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
  print(out)


if __name__ == "__main__":
  asyncio.run(main())
