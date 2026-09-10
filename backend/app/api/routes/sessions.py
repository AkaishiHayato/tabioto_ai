from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_host_id, verify_host_path_access
from app.scraper.auth import (
  import_session_state,
  login_automated,
  login_interactive,
  validate_session,
)
from app.scraper.exceptions import (
  LoginError,
  ManualLoginRequiredError,
  SessionExpiredError,
  SessionNotFoundError,
)

router = APIRouter()


def _verify_body_host_id(req_host_id: str, authenticated_host_id: str) -> None:
  """リクエストボディの host_id が認証済みユーザーのものと一致するか検証する。"""
  if req_host_id != authenticated_host_id:
    raise HTTPException(status_code=403, detail="アクセス権がありません")


class LoginRequest(BaseModel):
  host_id: str = Field(description="Supabase `hosts.id`（UUID）")
  email: str = Field(description="Airbnb ログイン用メールアドレス")
  password: str = Field(description="Airbnb ログイン用パスワード")


class InteractiveLoginRequest(BaseModel):
  host_id: str = Field(description="Supabase `hosts.id`（UUID）")
  email: str | None = Field(default=None, description="事前入力するメール（任意）")
  password: str | None = Field(default=None, description="事前入力するパスワード（任意）")
  timeout_ms: int = Field(default=300_000, description="ログイン待機タイムアウト（ミリ秒）")


class ImportSessionRequest(BaseModel):
  host_id: str = Field(description="Supabase `hosts.id`（UUID）")
  storage_state: dict = Field(description="Playwright `storageState` JSON（CLI ログイン後に取得）")


@router.post("/login")
async def airbnb_login_automated(
  req: LoginRequest,
  authenticated_host_id: str = Depends(get_current_host_id),
):
  """Airbnb にメール・パスワードで自動ログインし、storageState を DB に保存する。

  **用途**: 初回セットアップ、セッション切れ後の再ログイン。

  **成功時**: `{"status": "ok", "success": true, "method": "automated", ...}`

  **エラー**:
  - `401`: ログイン失敗
  - `403`: リクエストの host_id が認証済みユーザーと一致しない
  - `428`: CAPTCHA 等で自動ログイン不可 → `/login/interactive` または CLI を使用
  """
  _verify_body_host_id(req.host_id, authenticated_host_id)
  try:
    result = await login_automated(req.host_id, req.email, req.password)
    return {"status": "ok", **result.__dict__}
  except ManualLoginRequiredError as e:
    raise HTTPException(
      status_code=428,
      detail=f"{e} POST /api/sessions/login/interactive または CLI を使用してください",
    )
  except LoginError as e:
    raise HTTPException(status_code=401, detail=str(e))


@router.post("/login/interactive")
async def airbnb_login_interactive(
  req: InteractiveLoginRequest,
  authenticated_host_id: str = Depends(get_current_host_id),
):
  """ブラウザを起動して Airbnb ログインし、storageState を DB に保存する。

  **用途**: 自動ログインが `428` で失敗した場合の代替手段。

  **注意**: Docker 内では headless になるため、ローカル CLI ログインを推奨。

  **成功時**: `{"status": "ok", "success": true, "method": "interactive", ...}`
  """
  _verify_body_host_id(req.host_id, authenticated_host_id)
  try:
    result = await login_interactive(
      req.host_id,
      email=req.email,
      password=req.password,
      timeout_ms=req.timeout_ms,
      headless=True,
    )
    return {"status": "ok", **result.__dict__}
  except LoginError as e:
    raise HTTPException(status_code=401, detail=str(e))


@router.post("/import")
async def import_session(
  req: ImportSessionRequest,
  authenticated_host_id: str = Depends(get_current_host_id),
):
  """CLI で取得した Playwright storageState JSON を DB にインポートする。

  **用途**: ローカル CLI（`python -m app.scraper.cli.login`）でログイン後、
  その storageState を API 経由でサーバーに反映する場合。

  **成功時**: `{"status": "ok", "success": true, "method": "import", ...}`

  **エラー**:
  - `401`: インポートした storageState が無効
  - `403`: リクエストの host_id が認証済みユーザーと一致しない
  """
  _verify_body_host_id(req.host_id, authenticated_host_id)
  try:
    result = await import_session_state(req.host_id, req.storage_state)
    return {"status": "ok", **result.__dict__}
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))


@router.get("/validate/{host_id}", dependencies=[Depends(verify_host_path_access)])
async def check_session(host_id: str):
  """保存済み Airbnb セッションが有効かどうかを確認する。

  **用途**: FE 管理画面で「セッション状態」表示、API 呼び出し前の事前チェック。

  **レスポンス**: `{"valid": true}` または `{"valid": false}`

  **補足**: `false` の場合、DB 上のセッションは `expired` に更新される。
  """
  valid = await validate_session(host_id)
  return {"valid": valid}
