"""メッセージ画面のセレクタ。"""

INBOX_UNREAD_PATH = "/hosting/messages?unread="
THREAD_PATH = "/hosting/messages/{thread_id}"

INBOX_LIST_ITEM = '[data-testid^="inbox_list_"]'
THREAD_LAST_MESSAGE = '[data-testid="thread_page_last_item"]'
THREAD_HEADER_TITLE = '[data-testid="thread-header-title"]'
COMPOSE_BAR = '[data-testid="messaging-composebar"]'
SEND_BUTTON = '[data-testid="messaging_compose_bar_send_button"]'

PAGE_LOAD_WAIT_MS = 6000
THREAD_LOAD_WAIT_MS = 5000

HOST_ROLE_MARKERS = ("ホスト", "Host")
COHOST_ROLE_MARKERS = ("補助ホスト", "Co-host", "Co‑host")
SCHEDULED_REPLY_MARKERS = ("クイック返信は", "scheduled", "予定されています")
