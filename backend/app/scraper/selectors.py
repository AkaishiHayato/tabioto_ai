"""Airbnb ログイン画面のセレクタ（2026-03 時点・手動確認済み）。"""

# Step 1: メール入力
EMAIL_INPUTS = [
  "#phone-or-email",
  'input[id="phone-or-email"]',
]

# Step 1 → 2: 続行（メール送信後）
CONTINUE_BUTTONS = [
  'button:has-text("続行")',
  'button:has-text("Continue")',
  'button[data-testid="signup-login-submit"]',
  'button[type="submit"]',
]

# Step 2: OTP 画面（#otp-code-input が表示される）
OTP_INPUT = "#otp-code-input"

# Step 2 → 3: 「別の方法を試す」（⚠️「新しいコードを送信」は押さない）
TRY_ANOTHER_METHOD_BUTTONS = [
  'button:has-text("別の方法を試す")',
  'button:has-text("Try another way")',
]

# Step 3: モーダル「別の方法をお試しください」→「パスワードを入力」
# ※テキストに Unicode 単語結合子 (U+2060) が含まれるため部分一致
PASSWORD_OPTION_BUTTONS = [
  'button:has-text("パスワード")',
  '[role="button"]:has-text("パスワード")',
]

# Step 4: パスワード入力
PASSWORD_INPUTS = [
  'input[type="password"]',
  'input[name="password"]',
  'input[autocomplete="current-password"]',
]

# Step 4 → 5: パスワード画面の「続行」（「ログイン」ではない）
PASSWORD_CONTINUE_BUTTONS = [
  'button:has-text("続行")',
  'button:has-text("Continue")',
]

# 旧互換
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

# 補助ホスト招待
NOTIFICATIONS_PATH = "/notifications"
COHOST_INVITE_URL_PATTERN = "/co-hosting/accept-invite"
IDENTITY_VERIFICATION_PATH = "/account-fov"
ACCEPT_INVITE_BUTTONS = [
  'button:has-text("招待を承認")',
  'button:has-text("Accept invitation")',
]
