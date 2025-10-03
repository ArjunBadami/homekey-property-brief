from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"  # or "sqlite:///:memory:" for quick tests

settings = Settings()
