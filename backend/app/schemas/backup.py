from datetime import date as date_type, datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator


class BackupRunRequest(BaseModel):
    date: date_type | None = None


class BackupRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    status: str
    as_of_date: date_type | None
    drive_file_id: str | None
    drive_file_link: str | None
    error_message: str | None
    triggered_by: str

    @field_validator("created_at")
    @classmethod
    def _assume_utc_if_naive(cls, value: datetime) -> datetime:
        # SQLite (local dev) drops tzinfo on round-trip even though IdMixin sets
        # it with datetime.now(timezone.utc) — without this, the JSON response
        # loses its UTC marker and browsers misinterpret it as local time.
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class BackupConfigOut(BaseModel):
    backup_hour_local: int
    app_timezone: str
    backup_enabled: bool
