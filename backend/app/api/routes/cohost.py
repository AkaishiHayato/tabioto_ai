from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.scraper.cohost import accept_invite_by_url, accept_invites_from_notifications
from app.scraper.exceptions import ScraperError, SessionExpiredError, SessionNotFoundError

router = APIRouter()


class AcceptInviteRequest(BaseModel):
  invite_url: HttpUrl


@router.post("/accept/{host_id}")
async def accept_all_pending_invites(host_id: str):
  """通知ページから未承認の補助ホスト招待をすべて承認する。"""
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
  """招待 URL を直接指定して承認する。"""
  try:
    result = await accept_invite_by_url(host_id, str(req.invite_url))
    return {"status": "ok", **result.__dict__}
  except SessionNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))
  except ScraperError as e:
    raise HTTPException(status_code=400, detail=str(e))
