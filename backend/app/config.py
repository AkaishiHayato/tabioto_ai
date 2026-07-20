from pydantic_settings import BaseSettings


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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
