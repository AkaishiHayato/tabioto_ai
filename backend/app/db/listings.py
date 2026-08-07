"""listings テーブル ↔ アプリケーション層の変換。"""

from __future__ import annotations

from typing import Any


_PROMOTED_RAW_KEYS = (
  "max_guests",
  "directions",
  "check_in",
  "wifi",
  "house_manual",
  "checkout_instructions",
)


def listing_record_from_scrape(
  host_id: str,
  scraped: dict[str, Any],
  preview_title: str | None,
  *,
  last_scraped_at: str,
) -> dict[str, Any]:
  """scrape 結果を listings テーブル行 dict に変換する。"""
  raw_data = dict(scraped.get("raw_data") or {})

  record: dict[str, Any] = {
    "host_id": host_id,
    "airbnb_listing_id": scraped["airbnb_listing_id"],
    "title": scraped.get("title") or preview_title,
    "description": scraped.get("description"),
    "address": scraped.get("address"),
    "max_guests": raw_data.get("max_guests"),
    "check_in_time": scraped.get("check_in_time"),
    "check_out_time": scraped.get("check_out_time"),
    "amenities": scraped.get("amenities") or [],
    "house_rules": scraped.get("house_rules") or {},
    "directions": raw_data.get("directions"),
    "check_in": raw_data.get("check_in"),
    "wifi": raw_data.get("wifi"),
    "house_manual": raw_data.get("house_manual"),
    "checkout_instructions": raw_data.get("checkout_instructions") or [],
    "status": "active",
    "last_scraped_at": last_scraped_at,
    "raw_data": {k: v for k, v in raw_data.items() if k not in _PROMOTED_RAW_KEYS},
  }

  if record["max_guests"] is not None and not isinstance(record["max_guests"], int):
    try:
      record["max_guests"] = int(record["max_guests"])
    except (TypeError, ValueError):
      record["max_guests"] = None

  return record


def build_listing_info(record: dict[str, Any]) -> str:
  """LLM 返信生成用のリスティング情報テキストを組み立てる。"""
  lines: list[str] = []

  if record.get("title"):
    lines.append(f"タイトル: {record['title']}")
  if record.get("address"):
    lines.append(f"住所: {record['address']}")
  if record.get("max_guests"):
    lines.append(f"最大宿泊人数: {record['max_guests']}人")
  if record.get("check_in_time"):
    lines.append(f"チェックイン: {record['check_in_time']}以降")
  if record.get("check_out_time"):
    lines.append(f"チェックアウト: {record['check_out_time']}まで")

  check_in = record.get("check_in") or {}
  if check_in.get("method"):
    lines.append(f"チェックイン方法: {check_in['method']}")
  if check_in.get("method_description"):
    lines.append(f"チェックイン詳細: {check_in['method_description']}")

  if record.get("directions"):
    lines.append(f"道順:\n{record['directions']}")

  wifi = record.get("wifi") or {}
  if wifi.get("ssid"):
    lines.append(f"Wi-Fi SSID: {wifi['ssid']}")
  if wifi.get("password"):
    lines.append(f"Wi-Fi パスワード: {wifi['password']}")

  amenities = record.get("amenities") or []
  if amenities:
    lines.append(f"アメニティ: {', '.join(amenities)}")

  if record.get("house_manual"):
    lines.append(f"ハウスマニュアル:\n{record['house_manual']}")

  checkout = record.get("checkout_instructions") or []
  if checkout:
    lines.append("チェックアウト手順: " + " / ".join(checkout))

  if record.get("description"):
    lines.append(f"説明:\n{record['description']}")

  return "\n".join(lines)
