from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, require_staff_or_admin
from app.crud.stock_items import (
    create_stock_item,
    get_stock_item,
    list_stock_items,
    update_stock_item,
)
from app.schemas.stock_item import StockItemCreate, StockItemOut, StockItemUpdate

router = APIRouter(prefix="/stock-items", tags=["stock-items"])


@router.post("", response_model=StockItemOut, status_code=201, dependencies=[Depends(require_admin)])
def create_stock_item_endpoint(payload: StockItemCreate, db: Session = Depends(get_db)) -> StockItemOut:
    item = create_stock_item(db, name=payload.name, unit=payload.unit, price=payload.price)
    return StockItemOut.model_validate(item)


@router.get("", response_model=list[StockItemOut], dependencies=[Depends(require_staff_or_admin)])
def list_stock_items_endpoint(db: Session = Depends(get_db)) -> list[StockItemOut]:
    return [StockItemOut.model_validate(i) for i in list_stock_items(db)]


@router.patch("/{item_id}", response_model=StockItemOut, dependencies=[Depends(require_admin)])
def update_stock_item_endpoint(
    item_id: str, payload: StockItemUpdate, db: Session = Depends(get_db)
) -> StockItemOut:
    item = get_stock_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock item not found")
    item = update_stock_item(db, item, unit=payload.unit, price=payload.price)
    return StockItemOut.model_validate(item)
