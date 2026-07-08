import calendar
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.sale import Sale
from app.models.stock_count import StockCount
from app.models.stock_delivery import StockDelivery


def create_expense(
    db: Session,
    *,
    branch_id: str,
    date_: date,
    description: str,
    amount: float,
    created_by_id: str,
) -> Expense:
    expense = Expense(
        branch_id=branch_id,
        date=date_,
        description=description,
        amount=amount,
        created_by_id=created_by_id,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(db: Session, *, branch_id: str | None = None, date_: date | None = None) -> list[Expense]:
    stmt = select(Expense)
    if branch_id:
        stmt = stmt.where(Expense.branch_id == branch_id)
    if date_:
        stmt = stmt.where(Expense.date == date_)
    return list(db.scalars(stmt.order_by(Expense.date.desc(), Expense.created_at.desc())))


def get_expense(db: Session, expense_id: str) -> Expense | None:
    return db.get(Expense, expense_id)


def get_expense_for_day(db: Session, *, branch_id: str, date_: date) -> Expense | None:
    return db.scalar(
        select(Expense).where(Expense.branch_id == branch_id, Expense.date == date_)
    )


def update_expense(db: Session, expense: Expense, *, amount: float) -> Expense:
    expense.amount = amount
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense: Expense) -> None:
    db.delete(expense)
    db.commit()


def delete_month_data(db: Session, *, year: int, month: int) -> None:
    """Delete expenses, sales, stock counts, and stock deliveries for every branch
    in the given month (used to clear out old data once it's no longer needed).

    The stock count on the last day of the month is kept, since it's the
    "opening" figure for the 1st day of the following month."""
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    for model in (Expense, Sale, StockDelivery):
        db.execute(delete(model).where(model.date >= start, model.date <= end))
    db.execute(delete(StockCount).where(StockCount.date >= start, StockCount.date < end))
    db.commit()
