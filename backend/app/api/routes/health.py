from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
  """API サーバーの稼働確認。

  **用途**: デプロイ・Docker 起動後のヘルスチェック。

  **レスポンス**: `{"status": "ok"}`
  """
  return {"status": "ok"}
