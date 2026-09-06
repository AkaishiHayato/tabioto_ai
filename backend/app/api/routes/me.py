"""ログイン中ホストの情報取得API。仕様: doc/auth_design.md"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_host_id
from app.db.hosts import get_host

router = APIRouter()


@router.get("/me")
async def get_me(host_id: str = Depends(get_current_host_id)):
  """認証済みトークンから解決した、ログイン中ホストの情報を返す。

  **用途**: FEがログイン後に自分の host_id を知るために呼ぶ。
  以後のAPI呼び出し（`/api/settings/{host_id}` 等）はこの host_id を使う。

  **レスポンス**: `{"status": "ok", "host": {...}}`
  """
  host = get_host(host_id)
  return {"status": "ok", "host": host}
