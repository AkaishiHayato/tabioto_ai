"""メッセージ DOM / GraphQL のパース。"""

from __future__ import annotations

import hashlib
import re

from app.scraper.messages.selectors import (
  COHOST_ROLE_MARKERS,
  HOST_ROLE_MARKERS,
  SCHEDULED_REPLY_MARKERS,
)

THREAD_ID_RE = re.compile(r"/hosting/messages/(\d+)")


def thread_id_from_graphql(gid: str) -> str:
  if ":" in gid:
    return gid.split(":", 1)[1]
  return gid


def thread_id_from_url(url: str) -> str | None:
  match = THREAD_ID_RE.search(url)
  return match.group(1) if match else None


def message_fingerprint(thread_id: str, body: str) -> str:
  digest = hashlib.sha256(body.strip().encode()).hexdigest()[:16]
  return f"{thread_id}:{digest}"


def parse_tags(user_thread_tags: list[dict]) -> dict[str, list[str]]:
  result: dict[str, list[str]] = {}
  for tag in user_thread_tags or []:
    name = tag.get("userThreadTagName")
    if name:
      result[name] = tag.get("additionalValues") or []
  return result


def parse_sender_role(header_line: str) -> tuple[str | None, str]:
  """送信者名と role（guest/host/cohost/system/other）を返す。"""
  line = header_line.strip()
  if not line:
    return None, "system"

  if "·" in line or "・" in line:
    separator = "·" if "·" in line else "・"
    name, role = line.split(separator, 1)
    name = name.strip()
    role = role.strip()
    if any(marker in role for marker in COHOST_ROLE_MARKERS):
      return name, "cohost"
    if any(marker in role for marker in HOST_ROLE_MARKERS):
      return name, "host"
    return name, "other"

  if line.startswith("予約") or "予約が確定" in line or "Reservation" in line:
    return None, "system"

  return line, "guest"


def parse_last_message_text(raw_text: str) -> dict[str, str | None]:
  """
  thread_page_last_item の innerText をパースする。

  形式例:
    Takumi · ホスト\\n23:37\\n本文\\n既読...
    다현\\n22:10\\nこんにちは
  """
  lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
  if not lines:
    return {
      "sender_name": None,
      "sender_role": "system",
      "body": "",
      "time_label": None,
    }

  sender_name, sender_role = parse_sender_role(lines[0])
  time_label = lines[1] if len(lines) > 1 and _looks_like_time(lines[1]) else None
  body_start = 2 if time_label else 1
  body_lines = [
    line for line in lines[body_start:]
    if not _looks_like_read_receipt(line)
  ]
  body = "\n".join(body_lines).strip()

  return {
    "sender_name": sender_name,
    "sender_role": sender_role,
    "body": body,
    "time_label": time_label,
  }


def has_scheduled_quick_reply(page_text: str) -> bool:
  return any(marker in page_text for marker in SCHEDULED_REPLY_MARKERS)


def _looks_like_time(value: str) -> bool:
  if re.match(r"^\d{1,2}:\d{2}$", value):
    return True
  if value in {"月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"}:
    return True
  if re.match(r"^\d{1,2}/\d{1,2}$", value):
    return True
  return False


def _looks_like_read_receipt(value: str) -> bool:
  return "既読" in value or "Read" in value
