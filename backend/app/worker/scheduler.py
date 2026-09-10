"""メッセージポーリングの定期実行 Worker。

`docker compose exec backend python -m app.worker.scheduler` またはコンテナの
`command` から起動する。ホストごとに `settings.poll_interval_minutes` の間隔で
`poll_messages(host_id)` を実行する。

注意: 起動時に各ホストの間隔を読み込みジョブ登録する。実行中に設定を変更した場合は
反映のため Worker の再起動が必要(MVP範囲では十分。動的再スケジュールは対象外)。
"""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.client import get_supabase
from app.db.settings import get_settings
from app.scraper.exceptions import ScraperError, SessionExpiredError, SessionNotFoundError
from app.services.message_poll import poll_messages

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL_MINUTES = 10


def _list_host_ids() -> list[str]:
  db = get_supabase()
  rows = db.table("hosts").select("id").execute()
  return [row["id"] for row in rows.data or []]


def _poll_interval_minutes(host_id: str) -> int:
  settings_row = get_settings(host_id)
  if settings_row and settings_row.get("poll_interval_minutes"):
    return int(settings_row["poll_interval_minutes"])
  return DEFAULT_POLL_INTERVAL_MINUTES


async def _poll_host_job(host_id: str) -> None:
  try:
    result = await poll_messages(host_id)
    logger.info("poll_messages host=%s processed=%s", host_id, result.get("processed"))
  except SessionNotFoundError:
    logger.warning("host=%s: Airbnb セッション未登録のためスキップ", host_id)
  except SessionExpiredError:
    logger.warning("host=%s: Airbnb セッションが切れているためスキップ", host_id)
  except ScraperError as e:
    logger.error("host=%s: スクレイピングエラー: %s", host_id, e)
  except Exception:
    logger.exception("host=%s: ポーリング中に予期しないエラー", host_id)


def build_scheduler() -> AsyncIOScheduler:
  scheduler = AsyncIOScheduler()
  host_ids = _list_host_ids()
  if not host_ids:
    logger.warning("hosts テーブルが空です。ジョブは登録されません")

  for host_id in host_ids:
    interval = _poll_interval_minutes(host_id)
    scheduler.add_job(
      _poll_host_job,
      "interval",
      minutes=interval,
      args=[host_id],
      id=f"poll-messages-{host_id}",
      max_instances=1,
      coalesce=True,
    )
    logger.info("job registered: host=%s interval=%s分", host_id, interval)

  return scheduler


async def main() -> None:
  scheduler = build_scheduler()
  scheduler.start()
  logger.info("worker started")
  try:
    await asyncio.Event().wait()
  finally:
    scheduler.shutdown()


if __name__ == "__main__":
  asyncio.run(main())
