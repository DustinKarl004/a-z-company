from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.services.backup_runner import run_backup


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.app_timezone)
    if settings.backup_enabled:
        scheduler.add_job(
            run_backup,
            trigger=CronTrigger(hour=settings.backup_hour_local, minute=0),
            kwargs={"triggered_by": "scheduled"},
            id="daily_backup",
        )
    return scheduler
