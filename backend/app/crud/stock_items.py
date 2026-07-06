from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock_item import StockItem


def create_stock_item(db: Session, *, name: str, unit: str) -> StockItem:
    item = StockItem(name=name, unit=unit)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_stock_items(db: Session) -> list[StockItem]:
    return list(db.scalars(select(StockItem).order_by(StockItem.name)))


def get_stock_item(db: Session, item_id: str) -> StockItem | None:
    return db.get(StockItem, item_id)
