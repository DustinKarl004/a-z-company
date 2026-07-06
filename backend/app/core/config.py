from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./za_company.db"
    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_expire_minutes: int = 480

    admin_email: str = "admin@za-company.com"
    admin_password: str = "change-me"


settings = Settings()
