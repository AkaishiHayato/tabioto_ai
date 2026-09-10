"""Ava設定 API（FE 向け）。仕様: doc/api_interface_settings_listings.md"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import verify_host_path_access
from app.db.settings import get_settings, update_settings

router = APIRouter(dependencies=[Depends(verify_host_path_access)])

CheckinOutPolicy = Literal["flexible", "strict"]
PriceNegotiationPolicy = Literal["decline", "defer_to_host"]


class SettingsUpdateRequest(BaseModel):
  """設定更新リクエスト。送信したいフィールドのみでよい（部分更新）。"""

  auto_reply_enabled: bool | None = None
  poll_interval_minutes: Literal[3, 10, 15] | None = None
  reply_delay_minutes: int | None = Field(default=None, ge=0)
  early_checkin_policy: CheckinOutPolicy | None = None
  late_checkout_policy: CheckinOutPolicy | None = None
  luggage_storage_enabled: bool | None = None
  luggage_storage_message: str | None = None
  price_negotiation_policy: PriceNegotiationPolicy | None = None
  custom_instructions: str | None = None


@router.get("/{host_id}")
async def get_settings_for_host(host_id: str):
  """ホストの Ava設定 を返す。

  **用途**: FE Avaを設定画面の初期表示。

  **レスポンス**: `{"status": "ok", "settings": {...}}`

  **エラー**: `404` 該当ホストの設定行が存在しない場合。
  """
  settings_row = get_settings(host_id)
  if not settings_row:
    raise HTTPException(status_code=404, detail="設定が見つかりません")
  return {"status": "ok", "settings": settings_row}


@router.patch("/{host_id}")
async def patch_settings_for_host(host_id: str, req: SettingsUpdateRequest):
  """Ava設定 を部分更新する。

  **用途**: FE Avaを設定画面の保存ボタン。

  **リクエスト**: 更新したいフィールドのみ（例: `{"auto_reply_enabled": false}`）

  **レスポンス**: `{"status": "ok", "settings": {...}}`（更新後レコード）

  **エラー**: `404` 該当ホストなし
  """
  # exclude_unset: 「送られなかったフィールド」と「null が明示送信されたフィールド」を
  # 区別するため。exclude_none だと null 送信で null クリアができなくなる。
  fields = req.model_dump(exclude_unset=True)
  if not fields:
    settings_row = get_settings(host_id)
    if not settings_row:
      raise HTTPException(status_code=404, detail="設定が見つかりません")
    return {"status": "ok", "settings": settings_row}

  settings_row = update_settings(host_id, fields)
  if not settings_row:
    raise HTTPException(status_code=404, detail="設定が見つかりません")
  return {"status": "ok", "settings": settings_row}
