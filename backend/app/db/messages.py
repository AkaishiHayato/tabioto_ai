"""messages テーブル操作。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db.client import get_supabase


def _utc_now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


def insert_message(record: dict[str, Any]) -> dict | None:
  db = get_supabase()
  existing = (
    db.table("messages")
    .select("id")
    .eq("airbnb_message_id", record["airbnb_message_id"])
    .limit(1)
    .execute()
  )
  if existing.data:
    return existing.data[0]

  payload = {
    "received_at": _utc_now_iso(),
    **record,
  }
  rows = db.table("messages").insert(payload).execute()
  return rows.data[0] if rows.data else None


def list_thread_messages(host_id: str, airbnb_thread_id: str) -> list[dict]:
  db = get_supabase()
  rows = (
    db.table("messages")
    .select("*")
    .eq("host_id", host_id)
    .eq("airbnb_thread_id", airbnb_thread_id)
    .order("received_at", desc=True)
    .execute()
  )
  return rows.data or []


def update_message_status(message_id: str, **fields: Any) -> None:
  db = get_supabase()
  db.table("messages").update(fields).eq("id", message_id).execute()
