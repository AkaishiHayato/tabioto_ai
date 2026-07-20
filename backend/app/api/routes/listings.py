from fastapi import APIRouter, HTTPException

from app.scraper.listings import scrape_listings

router = APIRouter()


@router.post("/scrape/{host_id}")
async def trigger_listing_scrape(host_id: str):
    """リスティング情報のスクレイピングを実行する。"""
    try:
        listings = await scrape_listings(host_id)
        return {"status": "ok", "count": len(listings), "listings": listings}
    except RuntimeError as e:
        raise HTTPException(status_code=401, detail=str(e))
