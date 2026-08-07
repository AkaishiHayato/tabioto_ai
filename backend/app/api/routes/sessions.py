from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
async def airbnb_login_automated(req: LoginRequest):
  """Airbnb にメール・パスワードで自動ログインし、storageState を DB に保存する。

  **用途**: 初回セットアップ、セッション切れ後の再ログイン。

  **成功時**: `{"status": "ok", "success": true, "method": "automated", ...}`

  **エラー**:
  - `401`: ログイン失敗
  - `428`: CAPTCHA 等で自動ログイン不可 → `/login/interactive` または CLI を使用
  """
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
async def airbnb_login_interactive(req: InteractiveLoginRequest):
  """ブラウザを起動して Airbnb ログインし、storageState を DB に保存する。

  **用途**: 自動ログインが `428` で失敗した場合の代替手段。

  **注意**: Docker 内では headless になるため、ローカル CLI ログインを推奨。

  **成功時**: `{"status": "ok", "success": true, "method": "interactive", ...}`
  """
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
async def import_session(req: ImportSessionRequest):
  """CLI で取得した Playwright storageState JSON を DB にインポートする。

  **用途**: ローカル CLI（`python -m app.scraper.cli.login`）でログイン後、
  その storageState を API 経由でサーバーに反映する場合。

  **成功時**: `{"status": "ok", "success": true, "method": "import", ...}`

  **エラー**:
  - `401`: インポートした storageState が無効
  """
  try:
    result = await import_session_state(req.host_id, req.storage_state)
    return {"status": "ok", **result.__dict__}
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))


@router.get("/validate/{host_id}")
async def check_session(host_id: str):
  """保存済み Airbnb セッションが有効かどうかを確認する。

  **用途**: FE 管理画面で「セッション状態」表示、API 呼び出し前の事前チェック。

  **レスポンス**: `{"valid": true}` または `{"valid": false}`

  **補足**: `false` の場合、DB 上のセッションは `expired` に更新される。
  """
  valid = await validate_session(host_id)
  return {"valid": valid}
