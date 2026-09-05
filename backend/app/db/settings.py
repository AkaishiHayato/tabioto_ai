"""settings テーブル操作。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db.client import get_supabase


def _utc_now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


def get_settings(host_id: str) -> dict | None:
  db = get_supabase()
  result = (
    db.table("settings")
    .select("*")
    .eq("host_id", host_id)
    .maybe_single()
    .execute()
  )
  if not result or not result.data:
    return None
  return result.data


def update_settings(host_id: str, fields: dict[str, Any]) -> dict | None:
  db = get_supabase()
  payload = {**fields, "updated_at": _utc_now_iso()}
  result = (
    db.table("settings")
    .update(payload)
    .eq("host_id", host_id)
    .execute()
  )
  if not result.data:
    return None
  return result.data[0]


_POLICY_LABELS = {
  "flexible": "柔軟に対応する",
  "strict": "厳格に対応する",
  "decline": "常に丁重にお断りする",
  "defer_to_host": "即答せず、ホスト確認が必要である旨を伝える",
}


def build_host_policy_info(settings_row: dict | None) -> str:
  """settings 行から、返信生成 LLM に渡すホストポリシーの自然文を組み立てる。"""
  if not settings_row:
    return ""

  lines: list[str] = []

  early_checkin = settings_row.get("early_checkin_policy")
  if early_checkin:
    lines.append(f"アーリーチェックインの相談: {_POLICY_LABELS.get(early_checkin, early_checkin)}")

  late_checkout = settings_row.get("late_checkout_policy")
  if late_checkout:
    lines.append(f"レイトチェックアウトの相談: {_POLICY_LABELS.get(late_checkout, late_checkout)}")

  if settings_row.get("luggage_storage_enabled") and settings_row.get("luggage_storage_message"):
    lines.append(f"荷物預かりの案内: {settings_row['luggage_storage_message']}")

  price_negotiation = settings_row.get("price_negotiation_policy")
  if price_negotiation:
    lines.append(f"価格交渉への対応: {_POLICY_LABELS.get(price_negotiation, price_negotiation)}")

  custom_instructions = settings_row.get("custom_instructions")
  if custom_instructions:
    lines.append(f"追加の指示: {custom_instructions}")

  return "\n".join(lines)
