"""Airbnb メッセージ（inbox）スクレイピング。"""

from app.scraper.messages.threads import discover_message_threads

__all__ = ["discover_message_threads"]
