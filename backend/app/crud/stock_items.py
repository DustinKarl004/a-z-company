from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.sale import Sale
from app.models.stock_count import StockCount
from app.models.stock_delivery import StockDelivery
from app.models.stock_item import StockItem, stock_item_branches


def _resolve_branches(db: Session, branch_ids: list[str]) -> list[Branch]:
    if not branch_ids:
        return []
    return list(db.scalars(select(Branch).where(Branch.id.in_(branch_ids))))


def create_stock_item(
    db: Session,
    *,
    name: str,
    unit: str,
    price: float = 0.0,
    category: str | None = None,
    branch_ids: list[str] | None = None,
) -> StockItem:
    item = StockItem(name=name, unit=unit, price=price, category=category)
    item.branches = _resolve_branches(db, branch_ids or [])
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_stock_item(
    db: Session,
    item: StockItem,
    *,
    name: str,
    unit: str,
    price: float,
    category: str | None = None,
    branch_ids: list[str] | None = None,
) -> StockItem:
    item.name = name
    item.unit = unit
    item.price = price
    item.category = category
    item.branches = _resolve_branches(db, branch_ids or [])
    db.commit()
    db.refresh(item)
    return item


def list_stock_items(db: Session, *, branch_id: str | None = None) -> list[StockItem]:
    query = select(StockItem).order_by(StockItem.name)
    if branch_id is not None:
        unassigned = select(stock_item_branches.c.item_id)
        assigned_to_branch = select(stock_item_branches.c.item_id).where(
            stock_item_branches.c.branch_id == branch_id
        )
        query = query.where(
            StockItem.id.notin_(unassigned) | StockItem.id.in_(assigned_to_branch)
        )
    return list(db.scalars(query))


def get_stock_item(db: Session, item_id: str) -> StockItem | None:
    return db.get(StockItem, item_id)


def stock_item_has_related_records(db: Session, item_id: str) -> bool:
    for model in (Sale, StockCount, StockDelivery):
        if db.scalar(select(model.id).where(model.item_id == item_id).limit(1)) is not None:
            return True
    return False


def delete_stock_item(db: Session, item: StockItem) -> bool:
    if stock_item_has_related_records(db, item.id):
        return False
    db.delete(item)
    db.commit()
    return True


def delete_all_stock_items(db: Session) -> int:
    for model in (Sale, StockCount, StockDelivery):
        db.execute(delete(model))
    result = db.execute(delete(StockItem))
    db.commit()
    return result.rowcount or 0
