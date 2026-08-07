"""message_threads テーブル操作。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db.client import get_supabase


def _utc_now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


def get_monitored_listing_ids(host_id: str) -> set[str]:
  db = get_supabase()
  rows = (
    db.table("listings")
    .select("airbnb_listing_id")
    .eq("host_id", host_id)
    .eq("status", "active")
    .execute()
  )
  return {row["airbnb_listing_id"] for row in rows.data or []}


def resolve_listing_uuid(host_id: str, airbnb_listing_id: str | None) -> str | None:
  if not airbnb_listing_id:
    return None
  db = get_supabase()
  rows = (
    db.table("listings")
    .select("id")
    .eq("host_id", host_id)
    .eq("airbnb_listing_id", airbnb_listing_id)
    .limit(1)
    .execute()
  )
  if not rows.data:
    return None
  return rows.data[0]["id"]


def upsert_thread(host_id: str, record: dict[str, Any]) -> dict:
  db = get_supabase()
  payload = {
    "host_id": host_id,
    "last_polled_at": _utc_now_iso(),
    **record,
  }
  result = (
    db.table("message_threads")
    .upsert(payload, on_conflict="host_id,airbnb_thread_id")
    .execute()
  )
  return result.data[0]


def list_threads(host_id: str) -> list[dict]:
  db = get_supabase()
  rows = (
    db.table("message_threads")
    .select("*")
    .eq("host_id", host_id)
    .order("last_message_at", desc=True)
    .execute()
  )
  return rows.data or []


def get_thread(host_id: str, airbnb_thread_id: str) -> dict | None:
  db = get_supabase()
  rows = (
    db.table("message_threads")
    .select("*")
    .eq("host_id", host_id)
    .eq("airbnb_thread_id", airbnb_thread_id)
    .limit(1)
    .execute()
  )
  return rows.data[0] if rows.data else None


def update_skip_auto_reply(host_id: str, airbnb_thread_id: str, skip: bool) -> dict | None:
  db = get_supabase()
  rows = (
    db.table("message_threads")
    .update({"skip_auto_reply": skip})
    .eq("host_id", host_id)
    .eq("airbnb_thread_id", airbnb_thread_id)
    .execute()
  )
  return rows.data[0] if rows.data else None


def get_auto_reply_enabled(host_id: str) -> bool:
  db = get_supabase()
  rows = (
    db.table("settings")
    .select("auto_reply_enabled")
    .eq("host_id", host_id)
    .limit(1)
    .execute()
  )
  if not rows.data:
    return True
  return bool(rows.data[0].get("auto_reply_enabled", True))
