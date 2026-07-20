"""Airbnb ログイン CLI（手動 / 自動）。"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.scraper.auth import (
  import_session_state,
  login_automated,
  login_interactive,
  validate_session,
)
from app.scraper.exceptions import LoginError, ManualLoginRequiredError, ScraperError


def _build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description="Airbnb ログイン & storageState 保存")
  parser.add_argument("--host-id", required=True, help="hosts テーブルの UUID")

  sub = parser.add_subparsers(dest="command", required=True)

  interactive = sub.add_parser("interactive", help="ブラウザ表示で手動ログイン（推奨）")
  interactive.add_argument("--email", default=os.getenv("AIRBNB_LOGIN_EMAIL"))
  interactive.add_argument("--password", default=os.getenv("AIRBNB_LOGIN_PASSWORD"))
  interactive.add_argument("--timeout-ms", type=int, default=300_000)
  interactive.add_argument("--headless", action="store_true")

  automated = sub.add_parser("automated", help="メール/パスワード自動ログイン")
  automated.add_argument("--email", default=os.getenv("AIRBNB_LOGIN_EMAIL"), required=False)
  automated.add_argument("--password", default=os.getenv("AIRBNB_LOGIN_PASSWORD"), required=False)

  sub.add_parser("validate", help="保存済みセッションの検証")

  import_cmd = sub.add_parser("import", help="storageState JSON をインポート")
  import_cmd.add_argument("file", type=Path, help="Playwright storageState JSON パス")

  return parser


async def _run(args: argparse.Namespace) -> int:
  if args.command == "interactive":
    result = await login_interactive(
      args.host_id,
      email=args.email,
      password=args.password,
      timeout_ms=args.timeout_ms,
      headless=args.headless,
    )
    print(result.message)
    return 0

  if args.command == "automated":
    if not args.email or not args.password:
      print("email/password が必要です（引数 or AIRBNB_LOGIN_EMAIL/PASSWORD）", file=sys.stderr)
      return 1
    try:
      result = await login_automated(args.host_id, args.email, args.password)
      print(result.message)
      return 0
    except ManualLoginRequiredError as e:
      print(f"手動ログインが必要: {e}", file=sys.stderr)
      print("interactive コマンドを使用してください", file=sys.stderr)
      return 2

  if args.command == "validate":
    valid = await validate_session(args.host_id)
    print("valid" if valid else "invalid")
    return 0 if valid else 1

  if args.command == "import":
    state = json.loads(args.file.read_text())
    result = await import_session_state(args.host_id, state)
    print(result.message)
    return 0

  return 1


def main() -> None:
  root = Path(__file__).resolve().parents[3]
  load_dotenv(root / ".env")
  parser = _build_parser()
  args = parser.parse_args()

  try:
    raise SystemExit(asyncio.run(_run(args)))
  except ScraperError as e:
    print(f"error: {e}", file=sys.stderr)
    raise SystemExit(1) from e


if __name__ == "__main__":
  main()
