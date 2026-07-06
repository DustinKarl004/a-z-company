from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sale import Sale


def create_sale(
    db: Session,
    *,
    branch_id: str,
    item_id: str,
    date_: date,
    quantity_sold: float,
    amount: float,
    created_by_id: str,
) -> Sale:
    sale = Sale(
        branch_id=branch_id,
        item_id=item_id,
        date=date_,
        quantity_sold=quantity_sold,
        amount=amount,
        created_by_id=created_by_id,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def list_sales(db: Session, *, branch_id: str | None = None, date_: date | None = None) -> list[Sale]:
    stmt = select(Sale)
    if branch_id:
        stmt = stmt.where(Sale.branch_id == branch_id)
    if date_:
        stmt = stmt.where(Sale.date == date_)
    return list(db.scalars(stmt.order_by(Sale.date.desc())))


def get_sale(db: Session, sale_id: str) -> Sale | None:
    return db.get(Sale, sale_id)


def update_sale(db: Session, sale: Sale, *, quantity_sold: float, amount: float) -> Sale:
    sale.quantity_sold = quantity_sold
    sale.amount = amount
    db.commit()
    db.refresh(sale)
    return sale
