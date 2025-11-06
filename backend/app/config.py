from pathlib import Path
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "Badminton Count"
    secret_key: str = Field("super-secret-development-key", env="BADMINTON_SECRET_KEY")
    access_token_expire_minutes: int = Field(60 * 24, env="BADMINTON_ACCESS_TOKEN_EXPIRE")
    algorithm: str = "HS256"
    database_url: str = Field("sqlite:///" + str(Path(__file__).resolve().parent.parent / "badminton.db"), env="BADMINTON_DATABASE_URL")
    frontend_base_url: str = Field("/", env="BADMINTON_FRONTEND_BASE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
