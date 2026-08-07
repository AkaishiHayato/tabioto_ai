"""details/ セクションの scrape。"""

from __future__ import annotations

from typing import Any

from playwright.async_api import Page

from app.scraper.listing.helpers import (
  format_hour,
  goto_editor_page,
  input_value,
  radio_yes_checked,
  select_value,
  switch_checked,
  wait_input_value,
)
from app.scraper.listing.selectors import (
  HOUSE_RULE_TOGGLES,
  INSTANT_BOOK_SWITCH,
  GOOD_TRACK_RECORD_SWITCH,
  LISTING_TITLE_EN,
  LISTING_TITLE_JA,
  LISTING_TITLE_KO,
  LISTING_TITLE_ZH_TW,
  PROPERTY_SIZE,
  PROPERTY_SIZE_UNITS,
  PROPERTY_TYPE,
  PROPERTY_TYPE_GROUP,
  QUIET_HOURS_END,
  QUIET_HOURS_START,
  ROOM_TYPE,
  YEAR_BUILT,
)

async def scrape_title(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "title")

  titles = {
    "ja": await wait_input_value(page, LISTING_TITLE_JA),
    "en": await wait_input_value(page, LISTING_TITLE_EN),
    "zh_tw": await wait_input_value(page, LISTING_TITLE_ZH_TW),
    "ko": await wait_input_value(page, LISTING_TITLE_KO),
  }
  title = titles["ja"] or titles["zh_tw"] or titles["ko"] or titles["en"]

  return {"title": title, "titles": titles}



async def scrape_property_type(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "property-type")
  return {
    "property_type": {
      "property_type_group": await select_value(page, PROPERTY_TYPE_GROUP),
      "property_type": await select_value(page, PROPERTY_TYPE),
      "room_type": await select_value(page, ROOM_TYPE),
      "year_built": await input_value(page, YEAR_BUILT),
      "property_size": await input_value(page, PROPERTY_SIZE),
      "property_size_units": await select_value(page, PROPERTY_SIZE_UNITS),
    },
  }



async def scrape_max_guests(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "number-of-guests")
  locator = page.locator('main input[type="text"]').first
  value: str | None = None
  try:
    if await locator.count() > 0:
      value = (await locator.input_value()).strip() or None
  except Exception:
    value = None
  return {"max_guests": int(value) if value and value.isdigit() else value}



async def scrape_house_rules(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "house-rules")

  rules: dict[str, Any] = {}
  for key, prefix in HOUSE_RULE_TOGGLES.items():
    rules[key] = await radio_yes_checked(page, prefix)

  rules["quiet_hours"] = {
    "enabled": rules.pop("quiet_hours_enabled"),
    "start": format_hour(await select_value(page, QUIET_HOURS_START)),
    "end": format_hour(await select_value(page, QUIET_HOURS_END)),
  }
  return {"house_rules": rules}



async def scrape_description(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "description")
  return await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
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
        return clean(text.slice(s, e));
      };

      const sections = [
        ["listing", "リスティングの説明文", ["宿泊施設", "ゲストの立ち入り範囲"]],
        ["accommodations", "宿泊施設", ["ゲストの立ち入り範囲", "ゲストとの交流"]],
        ["guest_access", "ゲストの立ち入り範囲", ["ゲストとの交流", "その他の留意事項"]],
        ["interaction", "ゲストとの交流", ["その他の留意事項", "説明文に関する"]],
        ["other_notes", "その他の留意事項", ["説明文に関する"]],
      ];

      const descriptions = {};
      for (const [key, start, ends] of sections) {
        const val = between(preview, start, ends);
        if (val) descriptions[key] = val;
      }

      const parts = Object.values(descriptions).filter(Boolean);
      return {
        description: parts.length ? parts.join("\\n\\n") : null,
        descriptions,
      };
    }
    """
  )



async def scrape_amenities(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "amenities")
  return await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
      const main = document.querySelector("main");
      const full = clean(main?.innerText || "");
      const preview = full.includes("プレビュー")
        ? full.slice(full.indexOf("プレビュー"))
        : full;

      const marker = "以下のとおりです。";
      const start = preview.indexOf(marker);
      if (start < 0) return { amenities: [], amenities_detail: [] };

      const lines = preview
        .slice(start + marker.length)
        .split("\\n")
        .map(clean)
        .filter(Boolean);

      const looksLikeDescription = (line) =>
        line.length > 20 || /[。.]/.test(line) || /する$/.test(line);

      const amenities = [];
      let i = 0;
      while (i < lines.length) {
        const name = lines[i];
        i += 1;
        if (!name || name === "編集") continue;

        let description = null;
        if (i < lines.length && looksLikeDescription(lines[i])) {
          description = lines[i];
          i += 1;
        }
        amenities.push({ name, description });
      }

      return {
        amenities: amenities.map((a) => a.name),
        amenities_detail: amenities,
      };
    }
    """
  )



async def scrape_location(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "location")
  return await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
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
        if (!val || val === "詳細を追加してください") return null;
        return val;
      };

      const address = between(preview, "所在地", [
        "所在地の共有",
        "立地の特徴",
        "エリア情報",
        "ヘルプ",
      ]);

      const showExact = between(preview, "所在地の共有", [
        "立地の特徴",
        "エリア情報",
        "移動手段",
        "ヘルプ",
      ]);

      const features = between(preview, "立地の特徴", [
        "エリア情報",
        "移動手段",
        "宿泊施設から見える景色",
        "ヘルプ",
      ]);

      const areaInfo = between(preview, "エリア情報", [
        "移動手段",
        "宿泊施設から見える景色",
        "ヘルプ",
      ]);

      const transportation = between(preview, "移動手段", [
        "宿泊施設から見える景色",
        "ヘルプ",
      ]);

      const views = between(preview, "宿泊施設から見える景色", ["ヘルプ"]);

      return {
        address,
        location: {
          address,
          show_exact_location: showExact,
          features: features ? [features] : [],
          area_info: areaInfo,
          transportation,
          views,
        },
      };
    }
    """
  )



async def scrape_sleeping_arrangements(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "sleeping-arrangements")
  return await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
      const main = document.querySelector("main");
      const full = clean(main?.innerText || "");
      const preview = full.includes("プレビュー")
        ? full.slice(full.indexOf("プレビュー"))
        : full;

      const skip = new Set([
        "プレビュー",
        "寝具／ベッドの数と種類を追加する",
        "それぞれのお部屋にあるベッドの種類がゲストにはっきりとわかるようにしましょう。",
        "詳細を追加してください",
      ]);

      const lines = preview.split("\\n").map(clean).filter(Boolean);
      const rooms = [];

      for (let i = 0; i < lines.length; i += 1) {
        const line = lines[i];
        if (skip.has(line)) continue;

        const next = lines[i + 1];
        if (next === "詳細を追加してください") {
          rooms.push({ name: line, details: null });
          i += 1;
        } else if (next && !skip.has(next)) {
          rooms.push({ name: line, details: next });
          i += 1;
        }
      }

      return { sleeping_arrangements: { rooms } };
    }
    """
  )



async def scrape_accessibility(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "accessibility")
  return await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
      const main = document.querySelector("main");
      const full = clean(main?.innerText || "");
      const preview = full.includes("プレビュー")
        ? full.slice(full.indexOf("プレビュー"))
        : full;

      const lines = preview.split("\\n").map(clean).filter(Boolean);
      const start = lines.indexOf("アクセシビリティ機能・設備");
      const items = [];

      if (start >= 0) {
        for (let i = start + 1; i < lines.length; i += 1) {
          const line = lines[i];
          if (line.includes("ヘルプ")) break;
          items.push(line);
        }
      }

      return { accessibility: items };
    }
    """
  )



async def scrape_guest_safety(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "guest-safety")
  return await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
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
        if (!val || val === "詳細を追加してください") return null;
        return val;
      };

      return {
        guest_safety: {
          safety_notes: between(preview, "安全上の留意事項", ["防災設備", "ヘルプ"]),
          emergency_devices: between(preview, "防災設備", ["火災報知器", "ヘルプ"]),
          fire_alarm: between(preview, "火災報知器", ["宿泊施設情報", "ヘルプ"]),
          property_info: between(preview, "宿泊施設情報", ["ヘルプ"]),
        },
      };
    }
    """
  )



async def scrape_cancellation_policy(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "cancellation-policy")
  non_refundable = await switch_checked(page, '[role="switch"]')

  policy_data = await page.evaluate(
    """
    () => {
      const clean = (t) => (t || "").replace(/\\u2060/g, "").trim();
      const main = document.querySelector("main");
      const full = clean(main?.innerText || "");
      const preview = full.includes("プレビュー")
        ? full.slice(full.indexOf("プレビュー"))
        : full;

      const sectionLines = (text, heading, ends) => {
        let s = text.indexOf(heading);
        if (s < 0) return [];
        s += heading.length;
        let e = text.length;
        for (const end of ends) {
          const i = text.indexOf(end, s);
          if (i >= 0 && i < e) e = i;
        }
        return text
          .slice(s, e)
          .split("\\n")
          .map(clean)
          .filter(Boolean);
      };

      const shortLines = sectionLines(preview, "短期滞在", ["長期滞在"]);
      const longLines = sectionLines(preview, "長期滞在", ["返金不可オプション"]);

      return {
        short_term: {
          nights: shortLines[0] || null,
          policy: shortLines[1] || null,
        },
        long_term: {
          nights: longLines[0] || null,
          policy: longLines[1] || null,
        },
      };
    }
    """
  )

  return {
    "cancellation": {
      **policy_data,
      "non_refundable_option": non_refundable,
    },
  }



async def scrape_instant_book(page: Page, listing_id: str) -> dict[str, Any]:
  await goto_editor_page(page, listing_id, "details", "instant-book")
  return {
    "instant_book": {
      "enabled": await switch_checked(page, INSTANT_BOOK_SWITCH),
      "good_track_record": await switch_checked(page, GOOD_TRACK_RECORD_SWITCH),
    },
  }

