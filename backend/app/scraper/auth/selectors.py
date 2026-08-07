"""Airbnb ログイン画面のセレクタ（2026-03 時点・手動確認済み）。"""

EMAIL_INPUTS = [
  "#phone-or-email",
  'input[id="phone-or-email"]',
]

CONTINUE_BUTTONS = [
  'button:has-text("続行")',
  'button:has-text("Continue")',
  'button[data-testid="signup-login-submit"]',
  'button[type="submit"]',
]

OTP_INPUT = "#otp-code-input"

TRY_ANOTHER_METHOD_BUTTONS = [
  'button:has-text("別の方法を試す")',
  'button:has-text("Try another way")',
]

PASSWORD_OPTION_BUTTONS = [
  'button:has-text("パスワード")',
  '[role="button"]:has-text("パスワード")',
]

PASSWORD_INPUTS = [
  'input[type="password"]',
  'input[name="password"]',
  'input[autocomplete="current-password"]',
]

PASSWORD_CONTINUE_BUTTONS = [
  'button:has-text("続行")',
  'button:has-text("Continue")',
]

SUBMIT_BUTTONS = CONTINUE_BUTTONS
PASSWORD_LOGIN_LINKS = TRY_ANOTHER_METHOD_BUTTONS + PASSWORD_OPTION_BUTTONS

LOGIN_URL_FRAGMENTS = (
  "/login",
  "/authenticate",
  "/signup",
  "/forgot_password",
)

CHALLENGE_URL_FRAGMENTS = (
  "/verify",
  "/two-factor",
  "/challenge",
  "/account-activation",
  "/account-fov",
)
