from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, require_admin_password, require_staff_or_admin
from app.crud.stock_items import (
    create_stock_item,
    delete_all_stock_items,
    delete_stock_item,
    get_stock_item,
    list_stock_items,
    update_stock_item,
)
from app.models.user import User
from app.schemas.stock_item import StockItemCreate, StockItemOut, StockItemUpdate

router = APIRouter(prefix="/stock-items", tags=["stock-items"])


def _get_stock_item_or_404(db: Session, item_id: str):
    item = get_stock_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock item not found")
    return item


@router.post("", response_model=StockItemOut, status_code=201, dependencies=[Depends(require_admin)])
def create_stock_item_endpoint(payload: StockItemCreate, db: Session = Depends(get_db)) -> StockItemOut:
    item = create_stock_item(
        db,
        name=payload.name,
        unit=payload.unit,
        price=payload.price,
        category=payload.category,
        branch_ids=payload.branch_ids,
    )
    return StockItemOut.model_validate(item)


@router.get("", response_model=list[StockItemOut])
def list_stock_items_endpoint(
    branch_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> list[StockItemOut]:
    effective_branch_id = branch_id if user.role == "admin" else user.branch_id
    return [StockItemOut.model_validate(i) for i in list_stock_items(db, branch_id=effective_branch_id)]


@router.patch("/{item_id}", response_model=StockItemOut, dependencies=[Depends(require_admin)])
def update_stock_item_endpoint(
    item_id: str, payload: StockItemUpdate, db: Session = Depends(get_db)
) -> StockItemOut:
    item = _get_stock_item_or_404(db, item_id)
    item = update_stock_item(
        db,
        item,
        name=payload.name,
        unit=payload.unit,
        price=payload.price,
        category=payload.category,
        branch_ids=payload.branch_ids,
    )
    return StockItemOut.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock_item_endpoint(
    item_id: str, db: Session = Depends(get_db), _: object = Depends(require_admin_password)
) -> None:
    item = _get_stock_item_or_404(db, item_id)
    if not delete_stock_item(db, item):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This item has existing sales, delivery, or stock records and cannot be deleted.",
        )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_stock_items_endpoint(
    db: Session = Depends(get_db), _: object = Depends(require_admin_password)
) -> None:
    delete_all_stock_items(db)
