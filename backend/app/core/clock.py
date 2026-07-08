from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def local_today() -> date:
    """Current date in the configured business timezone, not the server host's."""
    return datetime.now(ZoneInfo(settings.app_timezone)).date()
