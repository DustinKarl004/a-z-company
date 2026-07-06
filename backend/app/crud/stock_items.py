from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock_item import StockItem


def create_stock_item(db: Session, *, name: str, unit: str, price: float = 0.0) -> StockItem:
    item = StockItem(name=name, unit=unit, price=price)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_stock_item(db: Session, item: StockItem, *, unit: str, price: float) -> StockItem:
    item.unit = unit
    item.price = price
    db.commit()
    db.refresh(item)
    return item


def list_stock_items(db: Session) -> list[StockItem]:
    return list(db.scalars(select(StockItem).order_by(StockItem.name)))


def get_stock_item(db: Session, item_id: str) -> StockItem | None:
    return db.get(StockItem, item_id)
