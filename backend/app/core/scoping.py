from datetime import date

from fastapi import HTTPException, status

from app.models.user import User


def resolve_branch_id(user: User, requested_branch_id: str | None) -> str:
    """Staff are always scoped to their own branch; admin must specify one."""
    if user.role == "staff":
        return user.branch_id

    if not requested_branch_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="branch_id is required"
        )
    return requested_branch_id


def ensure_editable(user: User, record_date: date) -> None:
    """Staff can only edit today's entries; admin can edit any date."""
    if user.role == "staff" and record_date != date.today():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This entry can no longer be edited",
        )


def ensure_creatable_date(user: User, record_date: date) -> None:
    """Staff can only log entries for today; admin can back/forward-date."""
    if user.role == "staff" and record_date != date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff can only log entries for today",
        )
