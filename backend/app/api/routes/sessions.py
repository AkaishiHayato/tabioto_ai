from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
  host_id: str
  email: str
  password: str


class InteractiveLoginRequest(BaseModel):
  host_id: str
  email: str | None = None
  password: str | None = None
  timeout_ms: int = 300_000


class ImportSessionRequest(BaseModel):
  host_id: str
  storage_state: dict


@router.post("/login")
async def airbnb_login_automated(req: LoginRequest):
  """Airbnb に自動ログインし、storageState を保存する。"""
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
  """
  ブラウザを表示してログイン（Docker 内では headless になるため CLI 推奨）。
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
  """Playwright storageState JSON をインポートする。"""
  try:
    result = await import_session_state(req.host_id, req.storage_state)
    return {"status": "ok", **result.__dict__}
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))


@router.get("/validate/{host_id}")
async def check_session(host_id: str):
  """保存済みセッションの有効性を確認する。"""
  valid = await validate_session(host_id)
  return {"valid": valid}
