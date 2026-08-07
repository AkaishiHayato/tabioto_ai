from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from app.scraper.cohost import accept_invite_by_url, accept_invites_from_notifications
from app.scraper.exceptions import ScraperError, SessionExpiredError, SessionNotFoundError

router = APIRouter()


class AcceptInviteRequest(BaseModel):
  invite_url: HttpUrl = Field(description="Airbnb 共同ホスト招待 URL")


@router.post("/accept/{host_id}")
async def accept_all_pending_invites(host_id: str):
  """Airbnb 通知ページから未承認の共同ホスト招待をすべて承認する。

  **用途**: デバッグ・運用。通常フローでは `POST /api/listings/sync` 内で処理。

  **成功時**: `{"status": "ok", "count": N, "results": [...]}`

  **エラー**: `401` セッション切れ / `404` セッション未登録
  """
  try:
    results = await accept_invites_from_notifications(host_id)
    return {
      "status": "ok",
      "count": len(results),
      "results": [r.__dict__ for r in results],
    }
  except SessionNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))


@router.post("/accept/{host_id}/url")
async def accept_invite_url(host_id: str, req: AcceptInviteRequest):
  """招待 URL を直接指定して共同ホスト招待を承認する。

  **用途**: デバッグ・運用。通常フローでは `POST /api/listings/sync` の `invite_url` を使用。

  **成功時**: `{"status": "ok", "accepted": true, "listing_title": "...", ...}`

  **エラー**: `401` セッション切れ / `400` 承認失敗
  """
  try:
    result = await accept_invite_by_url(host_id, str(req.invite_url))
    return {"status": "ok", **result.__dict__}
  except SessionNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))
  except ScraperError as e:
    raise HTTPException(status_code=400, detail=str(e))
