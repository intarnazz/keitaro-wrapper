from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    keitaro_url: str = ""
    keitaro_api_key: str = ""
    database_url: str = "sqlite:///./app.db"
    # Режим разработки без Keitaro: данные хранятся в памяти (см. app/keitaro/fake.py)
    keitaro_fake: bool = False
    # Откуда фронтенд может обращаться к API напрямую (через прокси Vite CORS не нужен)
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
