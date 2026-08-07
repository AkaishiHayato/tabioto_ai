"""arrival/ セクションの scrape。"""

from __future__ import annotations

from typing import Any

from playwright.async_api import Page

from app.scraper.listing.helpers import (
  format_hour,
  goto_editor_page,
  input_value,
  select_value,
)
from app.scraper.listing.selectors import (
  CHECK_IN_END,
  CHECK_IN_START,
  CHECK_OUT_TIME,
  DIRECTIONS_TEXTAREA,
  HOUSE_MANUAL_TEXTAREA,
  WIFI_NAME,
  WIFI_PASSWORD,
)

async def scrape_check_in_out(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "arrival", "check-in-out")
  check_in_start = await select_value(page, CHECK_IN_START)
  check_in_end = await select_value(page, CHECK_IN_END)
  check_out = await select_value(page, CHECK_OUT_TIME)
  return {
    "check_in_time": format_hour(check_in_start),
    "check_out_time": format_hour(check_out),
    "check_in_end": format_hour(check_in_end),
  }



async def scrape_directions(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "arrival", "directions")
  directions = await input_value(page, DIRECTIONS_TEXTAREA)
  return {"directions": directions}



async def scrape_wifi(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "arrival", "wifi-details")
  return {
    "wifi": {
      "ssid": await input_value(page, WIFI_NAME),
      "password": await input_value(page, WIFI_PASSWORD),
    },
  }



async def scrape_house_manual(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "arrival", "house-manual")
  manual = await input_value(page, HOUSE_MANUAL_TEXTAREA)
  return {"house_manual": manual}



async def scrape_check_in_method(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "arrival", "check-in-method")
  return await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
      const h3s = [...document.querySelectorAll("main h3")]
        .map((el) => clean(el.innerText))
        .filter(Boolean);

      const method = h3s[0] || null;
      const main = document.querySelector("main");
      const full = clean(main?.innerText || "");
      const preview = full.includes("プレビュー")
        ? full.slice(full.indexOf("プレビュー"))
        : full;

      const between = (text, start, ends) => {
        let s = text.indexOf(start);
        if (s < 0) return null;
        s += start.length;
        let e = text.length;
        for (const end of ends) {
          const i = text.indexOf(end, s);
          if (i >= 0 && i < e) e = i;
        }
        const val = clean(text.slice(s, e));
        return val || null;
      };

      const methodDescription = method
        ? between(preview, method, ["チェックイン手順", "手順を追加", "ヘルプ"])
        : null;

      return {
        check_in: {
          method,
          method_description: methodDescription,
          instructions: [],
        },
      };
    }
    """
  )



async def scrape_checkout_instructions(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "arrival", "checkout-instructions")
  return await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
      const checkoutInstructions = [...document.querySelectorAll("main h3")]
        .map((el) => clean(el.innerText))
        .filter(Boolean);

      return { checkout_instructions: checkoutInstructions };
    }
    """
  )


async def scrape_guidebooks(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "arrival", "guidebooks")
  return await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
      const headings = [...document.querySelectorAll("main h2")]
        .map((el) => clean(el.innerText))
        .filter(Boolean);

      const notCreated = headings.some((h) => h === "ガイドブックを作成する");
      if (notCreated) {
        return { guidebooks: { created: false, items: [] } };
      }

      const items = headings.filter((h) => h !== "ガイドブック");
      return { guidebooks: { created: items.length > 0, items } };
    }
    """
  )

