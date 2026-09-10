"""メッセージ画面のセレクタ。"""

INBOX_UNREAD_PATH = "/hosting/messages?unread="
THREAD_PATH = "/hosting/messages/{thread_id}"

INBOX_LIST_ITEM = '[data-testid^="inbox_list_"]'
# 2026-09 時点: thread_page_last_item は廃止され、メッセージ一覧内の
# 各アイテムが MessageOuterRegistryWrapperSpacingProps になった。
# 最新メッセージは .last で取得する。
THREAD_MESSAGE_ITEM = '[data-testid="MessageOuterRegistryWrapperSpacingProps"]'
THREAD_HEADER_TITLE = '[data-testid="thread-header-title"]'
COMPOSE_BAR = '[data-testid="messaging-composebar"]'
SEND_BUTTON = '[data-testid="messaging_compose_bar_send_button"]'

PAGE_LOAD_WAIT_MS = 6000
THREAD_LOAD_WAIT_MS = 5000

HOST_ROLE_MARKERS = ("ホスト", "Host")
COHOST_ROLE_MARKERS = ("補助ホスト", "Co-host", "Co‑host")
SCHEDULED_REPLY_MARKERS = ("クイック返信は", "scheduled", "予定されています")
