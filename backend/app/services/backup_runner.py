"""Orchestrates a single backup run: rebuild a whole month's report (every day
from the 1st through the target date), render it to one Excel workbook,
upload it to Drive — overwriting that month's existing file if one's already
there — and record the outcome. Always records a backup_runs row rather than
raising, so a scheduled run failing overnight still shows up (as a failure)
in the superuser backup history instead of silently vanishing into a log no
one reads.
"""

import logging
from datetime import date as date_type

from app.core.clock import local_today
from app.core.database import SessionLocal
from app.crud.backup_runs import create_backup_run
from app.models.backup_run import BackupRun
from app.services.backup_excel import build_month_workbook
from app.services.backup_report import build_month_reports
from app.services.google_drive import upload_backup

logger = logging.getLogger(__name__)


def run_backup(triggered_by: str, target_date: date_type | None = None) -> BackupRun:
    """`target_date` defaults to today's business day (the normal nightly
    case). Passing an earlier date lets a manual run regenerate/backfill that
    date's month instead — the same month-rebuild logic just runs against a
    different "as of" day."""
    db = SessionLocal()
    as_of = target_date or local_today()
    try:
        try:
            reports = build_month_reports(db, as_of)
            month_label = as_of.strftime("%B %Y")
            filename = f"Backup_{as_of.strftime('%B_%Y')}.xlsx"
            buffer = build_month_workbook(reports, month_label)
            file_id, file_link = upload_backup(buffer, filename)
            return create_backup_run(
                db,
                status="success",
                triggered_by=triggered_by,
                as_of_date=as_of,
                drive_file_id=file_id,
                drive_file_link=file_link,
            )
        except Exception as e:
            logger.exception("Backup run failed")
            return create_backup_run(
                db,
                status="failure",
                triggered_by=triggered_by,
                as_of_date=as_of,
                error_message=str(e),
            )
    finally:
        db.close()
