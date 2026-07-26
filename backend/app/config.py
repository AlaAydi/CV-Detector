from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Resume Optimizer"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "postgresql://iacv:iacv@localhost:5432/iacv"

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 5
    allowed_extensions: set[str] = {".pdf", ".docx"}

    cors_origins: list[str] = ["http://localhost:4200"]

    class Config:
        env_file = ".env"


settings = Settings()
