from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock_delivery import StockDelivery


def create_delivery(
    db: Session,
    *,
    branch_id: str,
    item_id: str,
    date_: date,
    quantity_delivered: float,
    is_short: bool,
    created_by_id: str,
) -> StockDelivery:
    delivery = StockDelivery(
        branch_id=branch_id,
        item_id=item_id,
        date=date_,
        quantity_delivered=quantity_delivered,
        is_short=is_short,
        created_by_id=created_by_id,
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


def list_deliveries(
    db: Session, *, branch_id: str | None = None, date_: date | None = None
) -> list[StockDelivery]:
    stmt = select(StockDelivery)
    if branch_id:
        stmt = stmt.where(StockDelivery.branch_id == branch_id)
    if date_:
        stmt = stmt.where(StockDelivery.date == date_)
    return list(db.scalars(stmt.order_by(StockDelivery.date.desc())))


def get_delivery(db: Session, delivery_id: str) -> StockDelivery | None:
    return db.get(StockDelivery, delivery_id)


def update_delivery(
    db: Session,
    delivery: StockDelivery,
    *,
    quantity_delivered: float | None,
    is_short: bool | None,
) -> StockDelivery:
    if quantity_delivered is not None:
        delivery.quantity_delivered = quantity_delivered
    if is_short is not None:
        delivery.is_short = is_short
    db.commit()
    db.refresh(delivery)
    return delivery
