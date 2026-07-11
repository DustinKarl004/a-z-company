from datetime import date as date_type

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin


class BackupRun(Base, IdMixin):
    __tablename__ = "backup_runs"

    status: Mapped[str] = mapped_column(String(20), nullable=False)  # "success" | "failure"
    drive_file_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    drive_file_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(20), nullable=False)  # "scheduled" | "manual"
    # The date this run rebuilt the month "as of" (1st of that month through
    # this date) — nullable since rows created before this column existed
    # don't have it.
    as_of_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
