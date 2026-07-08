from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./za_company.db"
    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_expire_minutes: int = 480

    # The business operates in this timezone; staff edit/creation cutoffs ("today")
    # are computed against it, not the server host's (often UTC) system clock.
    app_timezone: str = "Asia/Manila"

    admin_email: str = "admin@za-company.com"
    admin_password: str = "change-me"

    # Comma-separated list of allowed frontend origins, e.g. "https://za-company.vercel.app".
    # Defaults to "*" for local dev; set explicitly in production.
    cors_origins: str = "*"

    @property
    def sqlalchemy_database_url(self) -> str:
        # Some hosts (Railway, old Heroku) hand out "postgres://" — SQLAlchemy 2.x requires "postgresql://".
        if self.database_url.startswith("postgres://"):
            return "postgresql://" + self.database_url[len("postgres://") :]
        return self.database_url

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
