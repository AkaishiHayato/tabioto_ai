"""hosts テーブル操作。"""

from __future__ import annotations

from typing import Literal

from app.db.client import get_supabase

LineChannel = Literal["general", "urgent"]


def get_host(host_id: str) -> dict | None:
  db = get_supabase()
  result = (
    db.table("hosts")
    .select("id, name, email, line_user_id_general, line_user_id_urgent")
    .eq("id", host_id)
    .maybe_single()
    .execute()
  )
  if not result or not result.data:
    return None
  return result.data


def get_line_user_id(host_id: str, channel: LineChannel) -> str | None:
  host = get_host(host_id)
  if not host:
    return None
  key = "line_user_id_general" if channel == "general" else "line_user_id_urgent"
  return host.get(key)


def update_line_user_id(host_id: str, channel: LineChannel, line_user_id: str) -> dict | None:
  column = "line_user_id_general" if channel == "general" else "line_user_id_urgent"
  db = get_supabase()
  result = (
    db.table("hosts")
    .update({column: line_user_id, "updated_at": "now()"})
    .eq("id", host_id)
    .execute()
  )
  if not result.data:
    return None
  return result.data[0]


def clear_line_user_id(host_id: str, channel: LineChannel) -> None:
  column = "line_user_id_general" if channel == "general" else "line_user_id_urgent"
  db = get_supabase()
  db.table("hosts").update({column: None, "updated_at": "now()"}).eq("id", host_id).execute()
