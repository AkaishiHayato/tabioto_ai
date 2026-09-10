"""FE→BE API 認証。仕様: doc/auth_design.md

Supabase Auth が発行する JWT（ES256・JWKS方式）を検証し、
hosts.auth_user_id から host_id を解決する。
"""

from __future__ import annotations

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWKClient

from app.config import settings
from app.db.hosts import get_host_id_by_auth_user_id

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
  global _jwks_client
  if _jwks_client is None:
    _jwks_client = PyJWKClient(
      f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    )
  return _jwks_client


def _extract_bearer_token(authorization: str | None) -> str:
  if not authorization or not authorization.lower().startswith("bearer "):
    raise HTTPException(status_code=401, detail="認証トークンが必要です")
  return authorization.split(" ", 1)[1].strip()


async def get_current_host_id(authorization: str | None = Header(default=None)) -> str:
  """Authorization: Bearer <JWT> を検証し、対応する host_id を返す。"""
  token = _extract_bearer_token(authorization)

  try:
    signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
    claims = jwt.decode(
      token,
      signing_key.key,
      algorithms=["ES256"],
      audience="authenticated",
    )
  except jwt.PyJWTError as e:
    raise HTTPException(status_code=401, detail=f"認証トークンが無効です: {e}")

  auth_user_id = claims.get("sub")
  if not auth_user_id:
    raise HTTPException(status_code=401, detail="認証トークンが無効です")

  host_id = get_host_id_by_auth_user_id(auth_user_id)
  if not host_id:
    raise HTTPException(status_code=403, detail="このユーザーに紐づくホストが見つかりません")

  return host_id


async def verify_host_path_access(
  host_id: str,
  resolved_host_id: str = Depends(get_current_host_id),
) -> str:
  """URLパスの host_id が、認証済みユーザーの host_id と一致するか検証する。"""
  if host_id != resolved_host_id:
    raise HTTPException(status_code=403, detail="アクセス権がありません")
  return resolved_host_id
