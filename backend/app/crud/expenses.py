from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.expense import Expense


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
    return list(db.scalars(stmt.order_by(Expense.date.desc())))
