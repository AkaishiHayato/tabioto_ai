"""リスティング編集ツールのセレクタ（2026-03 調査済み）。"""

LISTING_ROW_BUTTON = "main button[data-testid]"

# details/title（id に textarea とあるが実体は input[type=text]）
LISTING_TITLE_JA = "#listing-title-ja-textarea"
LISTING_TITLE_EN = "#listing-title-en-textarea"
LISTING_TITLE_ZH_TW = "#listing-title-zh-tw-textarea"
LISTING_TITLE_KO = "#listing-title-ko-textarea"

# details/property-type
PROPERTY_TYPE_GROUP = 'select[name="propertyTypeGroup"]'
PROPERTY_TYPE = 'select[name="propertyType"]'
ROOM_TYPE = 'select[name="roomType"]'
YEAR_BUILT = 'input[name="yearBuilt"]'
PROPERTY_SIZE = 'input[name="propertySize"]'
PROPERTY_SIZE_UNITS = 'select[name="propertySizeUnits"]'

# details/house-rules
HOUSE_RULE_TOGGLES = {
  "pets_allowed": "pets-allowed-toggle-row-row-toggle-DLS-toggle",
  "events_allowed": "events-allowed-toggle-row-row-toggle-DLS-toggle",
  "smoking_allowed": "smoking-allowed-toggle-row-row-toggle-DLS-toggle",
  "quiet_hours_enabled": "quiet-hours-toggle-row-row-toggle-DLS-toggle",
  "commercial_photography_allowed": "commercial-photography-allowed-toggle-row-row-toggle-DLS-toggle",
}
QUIET_HOURS_START = 'select[name="quietHoursStartTime"]'
QUIET_HOURS_END = 'select[name="quietHoursEndTime"]'

# arrival/check-in-out
CHECK_IN_START = "#check-in-start-time"
CHECK_IN_END = "#check-in-end-time"
CHECK_OUT_TIME = "#check-out-time"

# arrival/directions, house-manual
DIRECTIONS_TEXTAREA = "#directionsForm-textarea"
HOUSE_MANUAL_TEXTAREA = "#houseManualForm-textarea"

# arrival/wifi-details
WIFI_NAME = "#wifi-name"
WIFI_PASSWORD = "#wifi-password"

# details/instant-book
INSTANT_BOOK_SWITCH = "#instant-book-switch-card"
GOOD_TRACK_RECORD_SWITCH = "#switch-good-track-record-switch-row"

# 保存対象ページ（section, slug）— listing.scrape.LISTING_SCRAPERS と対応
LISTING_EDITOR_PAGES = [
  # details
  ("details", "title"),
  ("details", "property-type"),
  ("details", "sleeping-arrangements"),
  ("details", "number-of-guests"),
  ("details", "description"),
  ("details", "amenities"),
  ("details", "accessibility"),
  ("details", "location"),
  ("details", "instant-book"),
  ("details", "house-rules"),
  ("details", "guest-safety"),
  ("details", "cancellation-policy"),
  # arrival
  ("arrival", "check-in-out"),
  ("arrival", "directions"),
  ("arrival", "check-in-method"),
  ("arrival", "wifi-details"),
  ("arrival", "house-manual"),
  ("arrival", "checkout-instructions"),
  ("arrival", "guidebooks"),
]

PAGE_LOAD_WAIT_MS = 3500
