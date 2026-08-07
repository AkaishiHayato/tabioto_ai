"""返信要否判定。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.scraper.messages.thread_detail import ThreadLastMessage


class ReplyAction(str, Enum):
  SKIP = "skip"
  AUTO_REPLY = "auto_reply"
  URGENT_NOTIFY = "urgent_notify"


@dataclass
class ReplyDecision:
  action: ReplyAction
  reason: str


def decide_reply_action(
  *,
  last_message: ThreadLastMessage,
  skip_auto_reply: bool,
  auto_reply_enabled: bool,
  is_monitored_listing: bool,
  is_new_message: bool,
  is_urgent: bool | None = None,
) -> ReplyDecision:
  """doc/messages_scraping.md 5.1 / 5.2 + 緊急判定を反映する。"""

  if not is_monitored_listing:
    return ReplyDecision(ReplyAction.SKIP, "監視対象外リスティング")

  if not is_new_message:
    return ReplyDecision(ReplyAction.SKIP, "新規メッセージなし")

  if skip_auto_reply:
    return ReplyDecision(ReplyAction.SKIP, "FE で自動返信スキップ")

  if not auto_reply_enabled:
    return ReplyDecision(ReplyAction.SKIP, "設定で自動返信無効")

  if last_message.has_scheduled_reply:
    return ReplyDecision(ReplyAction.SKIP, "スケジュール済みクイック返信あり")

  role = last_message.sender_role
  if role in {"host", "cohost"}:
    return ReplyDecision(ReplyAction.SKIP, f"最新送信者が {role}")

  if role == "system":
    return ReplyDecision(ReplyAction.SKIP, "システム通知")

  if not last_message.body.strip():
    return ReplyDecision(ReplyAction.SKIP, "本文が空")

  if role != "guest":
    return ReplyDecision(ReplyAction.SKIP, f"ゲスト以外の送信 ({role})")

  if is_urgent is True:
    return ReplyDecision(ReplyAction.URGENT_NOTIFY, "緊急メッセージ（LINE 通知）")

  return ReplyDecision(ReplyAction.AUTO_REPLY, "ゲストメッセージ → 自動返信")
