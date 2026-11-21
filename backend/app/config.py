from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    keitaro_url: str
    keitaro_api_key: str
    database_url: str = "sqlite:///./app.db"


settings = Settings()