import calendar
from datetime import date as date_type, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.sale import Sale
from app.models.stock_delivery import StockDelivery
from app.models.user import User


def _branch_summary(db: Session, branch: Branch, start: date_type, end: date_type) -> dict:
    total_sales = db.scalar(
        select(func.coalesce(func.sum(Sale.amount), 0.0)).where(
            Sale.branch_id == branch.id, Sale.date >= start, Sale.date <= end
        )
    )
    has_shortfall = (
        db.scalar(
            select(StockDelivery.id).where(
                StockDelivery.branch_id == branch.id,
                StockDelivery.date >= start,
                StockDelivery.date <= end,
                StockDelivery.is_short.is_(True),
            )
        )
        is not None
    )

    return {
        "branch_id": branch.id,
        "branch_name": branch.name,
        "total_sales": total_sales,
        "has_shortfall": has_shortfall,
    }


def overview(db: Session) -> dict:
    today = date_type.today()
    branches = list(db.scalars(select(Branch).order_by(Branch.name)))
    branch_summaries = [_branch_summary(db, b, today, today) for b in branches]

    branch_count = len(branches)
    staff_count = db.scalar(select(func.count()).select_from(User).where(User.role == "staff"))

    return {
        "date": today.isoformat(),
        "branch_count": branch_count,
        "staff_count": staff_count,
        "branches": branch_summaries,
        "total_sales": sum(b["total_sales"] for b in branch_summaries),
    }


def _daily_breakdown(db: Session, branches: list[Branch], start: date_type, end: date_type) -> list[dict]:
    rows = db.execute(
        select(Sale.date, Sale.branch_id, func.sum(Sale.amount))
        .where(Sale.date >= start, Sale.date <= end)
        .group_by(Sale.date, Sale.branch_id)
    ).all()
    totals_by_date: dict[date_type, dict[str, float]] = {}
    for sale_date, branch_id, total in rows:
        totals_by_date.setdefault(sale_date, {})[branch_id] = total

    daily = []
    current = start
    while current <= end:
        by_branch = totals_by_date.get(current, {})
        daily.append(
            {
                "date": current.isoformat(),
                "branch_sales": {b.id: by_branch.get(b.id, 0.0) for b in branches},
                "total_sales": sum(by_branch.values()),
            }
        )
        current += timedelta(days=1)
    return daily


def monthly(db: Session, year: int, month: int) -> dict:
    start = date_type(year, month, 1)
    end = date_type(year, month, calendar.monthrange(year, month)[1])

    branches = list(db.scalars(select(Branch).order_by(Branch.name)))
    branch_summaries = [_branch_summary(db, b, start, end) for b in branches]

    return {
        "year": year,
        "month": month,
        "branches": branch_summaries,
        "total_sales": sum(b["total_sales"] for b in branch_summaries),
        "daily": _daily_breakdown(db, branches, start, end),
    }
