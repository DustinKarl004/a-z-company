from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./za_company.db"
    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_expire_minutes: int = 480

    # The business operates in this timezone; staff edit/creation cutoffs ("today")
    # are computed against it, not the server host's (often UTC) system clock.
    app_timezone: str = "Asia/Manila"

    # Branches can stay open past midnight, so the "business day" rolls over at this
    # hour instead of 12am — e.g. 6 means anything before 6am still counts as yesterday.
    business_day_cutoff_hour: int = 6

    admin_email: str = "admin@za-company.com"
    admin_password: str = "change-me"

    superuser_email: str = "superuser@za-company.com"
    superuser_password: str = "change-me"

    # Local hour (in app_timezone) the daily backup job runs at. Must be AFTER
    # business_day_cutoff_hour, not before — branches can stay open past midnight,
    # so the business day (and staff's ability to edit "today") doesn't actually
    # close until the cutoff hour. Backing up too early (e.g. 11pm) would miss
    # edits made between then and the cutoff. Default is cutoff + 1 hour, giving
    # a small buffer once the day has genuinely closed.
    backup_hour_local: int = 7
    # Kill switch — set to false to pause the scheduled backup without a redeploy.
    backup_enabled: bool = True
    # OAuth credentials (as your own Google account, not a service account — service
    # accounts have no Drive storage quota of their own) used to upload backups to Drive.
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_refresh_token: str = ""
    google_drive_folder_id: str = ""

    # Comma-separated list of allowed frontend origins, e.g. "https://za-company.vercel.app".
    # Defaults to "*" for local dev; set explicitly in production.
    cors_origins: str = "*"

    # Enables /docs, /redoc, and /openapi.json. Off by default so the API schema
    # isn't publicly browsable in production; turn on for local dev only.
    debug: bool = False

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
