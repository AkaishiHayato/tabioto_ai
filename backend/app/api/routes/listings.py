from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, model_validator

from app.scraper.exceptions import ScraperError, SessionExpiredError, SessionNotFoundError
from app.scraper.listings import scrape_listing_detail, scrape_listings, sync_listing

router = APIRouter()


class SyncListingRequest(BaseModel):
  """リスティング同期リクエスト。

  - invite_url のみ: 招待承認 → listing_id 自動特定 → scrape
  - airbnb_listing_id のみ: 承認済み前提で scrape
  - 両方: 招待承認後、指定 ID を scrape
  """

  invite_url: HttpUrl | None = None
  airbnb_listing_id: str | None = None

  @model_validator(mode="after")
  def require_identifier(self) -> "SyncListingRequest":
    if not self.invite_url and not self.airbnb_listing_id:
      raise ValueError("invite_url または airbnb_listing_id のいずれかが必要です")
    return self


class AcceptResultResponse(BaseModel):
  invite_url: str
  accepted: bool
  listing_title: str | None
  message: str


class MessageThreadSummary(BaseModel):
  airbnb_thread_id: str | None = None
  guest_name: str | None = None
  preview: str | None = None
  thread_url: str | None = None


class MessageThreadsResponse(BaseModel):
  threads: list[MessageThreadSummary]
  implemented: bool
  message: str | None = None


class SyncListingResponse(BaseModel):
  status: str
  cohost: AcceptResultResponse | None
  listing: dict
  message_threads: MessageThreadsResponse
  warnings: list[str]


@router.post("/sync/{host_id}", response_model=SyncListingResponse)
async def sync_listing_for_host(host_id: str, req: SyncListingRequest):
  """
  リスティングを追加・同期する（FE 向け）。

  1. 共同ホスト招待の承認（invite_url 指定時）
  2. リスティング詳細の scrape → DB 保存
  3. メッセージルーム一覧の取得（未実装の場合は空）
  """
  try:
    result = await sync_listing(
      host_id,
      invite_url=str(req.invite_url) if req.invite_url else None,
      airbnb_listing_id=req.airbnb_listing_id,
    )
    return result
  except ValueError as e:
    raise HTTPException(status_code=422, detail=str(e))
  except SessionNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))
  except ScraperError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.post("/scrape/{host_id}")
async def trigger_listing_scrape(host_id: str):
  """リスティング一覧 + 詳細のスクレイピングを実行する。"""
  try:
    listings = await scrape_listings(host_id)
    return {"status": "ok", "count": len(listings), "listings": listings}
  except SessionNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))
  except ScraperError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.post("/scrape/{host_id}/{listing_id}")
async def trigger_single_listing_scrape(host_id: str, listing_id: str):
  """単一リスティングの詳細スクレイピングを実行する。"""
  try:
    listing = await scrape_listing_detail(host_id, listing_id)
    return {"status": "ok", "listing": listing}
  except SessionNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except SessionExpiredError as e:
    raise HTTPException(status_code=401, detail=str(e))
  except ScraperError as e:
    raise HTTPException(status_code=400, detail=str(e))
