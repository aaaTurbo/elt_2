from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://adrobot:adrobot@db:5432/adrobot"

    keitaro_api_url: str = "https://keitaro.example.com/admin_api/v1"
    keitaro_api_key: str = ""
    keitaro_mock: bool = True

    keitaro_domain_default: str = "track.example.com"
    keitaro_group_id_default: int = 1
    keitaro_source_id_default: int = 1
    google_redirect_url: str = "https://www.google.com"

    cors_origins: str = "*"


settings = Settings()
