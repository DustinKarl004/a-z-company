from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.clock import local_today
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_superuser, require_superuser_password
from app.crud.backup_runs import delete_backup_run, get_backup_run, list_backup_runs
from app.schemas.backup import BackupConfigOut, BackupRunOut, BackupRunRequest
from app.services.backup_runner import run_backup

router = APIRouter(prefix="/backup", tags=["backup"], dependencies=[Depends(require_superuser)])


@router.get("/config", response_model=BackupConfigOut)
def get_backup_config_endpoint() -> BackupConfigOut:
    return BackupConfigOut(
        backup_hour_local=settings.backup_hour_local,
        app_timezone=settings.app_timezone,
        backup_enabled=settings.backup_enabled,
    )


@router.get("/runs", response_model=list[BackupRunOut])
def list_backup_runs_endpoint(db: Session = Depends(get_db)) -> list[BackupRunOut]:
    return [BackupRunOut.model_validate(r) for r in list_backup_runs(db)]


@router.post("/run", response_model=BackupRunOut)
def trigger_backup_endpoint(payload: BackupRunRequest = BackupRunRequest()) -> BackupRunOut:
    if payload.date is not None and payload.date > local_today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Date cannot be in the future")
    run = run_backup(triggered_by="manual", target_date=payload.date)
    return BackupRunOut.model_validate(run)


@router.delete("/runs/{run_id}", status_code=204)
def delete_backup_run_endpoint(
    run_id: str, db: Session = Depends(get_db), _: object = Depends(require_superuser_password)
) -> None:
    run = get_backup_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup run not found")
    delete_backup_run(db, run)
