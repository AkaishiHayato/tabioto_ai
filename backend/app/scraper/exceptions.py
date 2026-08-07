class ScraperError(Exception):
  """スクレイピング関連の基底例外。"""


class LoginError(ScraperError):
  """Airbnb ログイン失敗。"""


class ManualLoginRequiredError(LoginError):
  """CAPTCHA / 2FA 等により手動ログインが必要。"""


class SessionExpiredError(ScraperError):
  """保存済みセッションが無効。"""


class SessionNotFoundError(ScraperError):
  """有効なセッションが DB に存在しない。"""
