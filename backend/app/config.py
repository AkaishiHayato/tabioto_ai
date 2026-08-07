from pathlib import Path

from pydantic_settings import BaseSettings

# backend/app/config.py → リポジトリルートの .env
_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    session_encryption_key: str = ""
    gemini_api_key: str = ""
    line_general_channel_access_token: str = ""
    line_urgent_channel_access_token: str = ""
    airbnb_base_url: str = "https://www.airbnb.com"
    airbnb_login_email: str = ""
    airbnb_login_password: str = ""

    model_config = {
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
