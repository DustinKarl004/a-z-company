import calendar
from datetime import date as date_type

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.expense import Expense
from app.models.sale import Sale
from app.models.stock_delivery import StockDelivery
from app.models.user import User


def _branch_summary(db: Session, branch: Branch, start: date_type, end: date_type) -> dict:
    total_sales = db.scalar(
        select(func.coalesce(func.sum(Sale.amount), 0.0)).where(
            Sale.branch_id == branch.id, Sale.date >= start, Sale.date <= end
        )
    )
    total_expenses = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.branch_id == branch.id, Expense.date >= start, Expense.date <= end
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
        "total_expenses": total_expenses,
        "profit": total_sales - total_expenses,
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
        "total_expenses": sum(b["total_expenses"] for b in branch_summaries),
        "total_profit": sum(b["profit"] for b in branch_summaries),
    }


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
        "total_expenses": sum(b["total_expenses"] for b in branch_summaries),
        "total_profit": sum(b["profit"] for b in branch_summaries),
    }
