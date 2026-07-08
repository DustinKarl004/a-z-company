from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock_count import StockCount


def create_count(
    db: Session,
    *,
    branch_id: str,
    item_id: str,
    date_: date,
    quantity_remaining: float,
    created_by_id: str,
) -> StockCount:
    count = StockCount(
        branch_id=branch_id,
        item_id=item_id,
        date=date_,
        quantity_remaining=quantity_remaining,
        created_by_id=created_by_id,
    )
    db.add(count)
    db.commit()
    db.refresh(count)
    return count


def get_count_for_day(
    db: Session, *, branch_id: str, item_id: str, date_: date
) -> StockCount | None:
    return db.scalar(
        select(StockCount).where(
            StockCount.branch_id == branch_id,
            StockCount.item_id == item_id,
            StockCount.date == date_,
        )
    )


def list_counts(
    db: Session, *, branch_id: str | None = None, date_: date | None = None
) -> list[StockCount]:
    stmt = select(StockCount)
    if branch_id:
        stmt = stmt.where(StockCount.branch_id == branch_id)
    if date_:
        stmt = stmt.where(StockCount.date == date_)
    return list(db.scalars(stmt.order_by(StockCount.date.desc())))


def get_count(db: Session, count_id: str) -> StockCount | None:
    return db.get(StockCount, count_id)


def update_count(db: Session, count: StockCount, *, quantity_remaining: float | None) -> StockCount:
    if quantity_remaining is not None:
        count.quantity_remaining = quantity_remaining
    db.commit()
    db.refresh(count)
    return count
