from datetime import date, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.clock import local_today
from app.models.stock_delivery import StockDelivery

NEEDS_RETENTION_DAYS = 3


def clear_stale_short_flags(db: Session) -> None:
    """Needs older than NEEDS_RETENTION_DAYS no longer need action; drop the flag."""
    cutoff = local_today() - timedelta(days=NEEDS_RETENTION_DAYS)
    db.execute(
        update(StockDelivery)
        .where(StockDelivery.is_short.is_(True))
        .where(StockDelivery.date < cutoff)
        .values(is_short=False)
    )
    db.commit()


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


def get_delivery_for_day(
    db: Session, *, branch_id: str, item_id: str, date_: date
) -> StockDelivery | None:
    return db.scalar(
        select(StockDelivery).where(
            StockDelivery.branch_id == branch_id,
            StockDelivery.item_id == item_id,
            StockDelivery.date == date_,
        )
    )


def list_deliveries(
    db: Session,
    *,
    branch_id: str | None = None,
    date_: date | None = None,
    is_short: bool | None = None,
) -> list[StockDelivery]:
    stmt = select(StockDelivery)
    if branch_id:
        stmt = stmt.where(StockDelivery.branch_id == branch_id)
    if date_:
        stmt = stmt.where(StockDelivery.date == date_)
    if is_short is not None:
        stmt = stmt.where(StockDelivery.is_short.is_(is_short))
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
