from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.backup_run import BackupRun


def create_backup_run(
    db: Session,
    *,
    status: str,
    triggered_by: str,
    as_of_date: date_type | None = None,
    drive_file_id: str | None = None,
    drive_file_link: str | None = None,
    error_message: str | None = None,
) -> BackupRun:
    run = BackupRun(
        status=status,
        triggered_by=triggered_by,
        as_of_date=as_of_date,
        drive_file_id=drive_file_id,
        drive_file_link=drive_file_link,
        error_message=error_message,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_backup_runs(db: Session, *, limit: int = 100) -> list[BackupRun]:
    stmt = select(BackupRun).order_by(BackupRun.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))


def get_backup_run(db: Session, run_id: str) -> BackupRun | None:
    return db.get(BackupRun, run_id)


def delete_backup_run(db: Session, run: BackupRun) -> None:
    db.delete(run)
    db.commit()
