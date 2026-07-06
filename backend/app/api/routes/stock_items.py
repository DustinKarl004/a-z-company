from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, require_staff_or_admin
from app.crud.stock_items import create_stock_item, list_stock_items
from app.schemas.stock_item import StockItemCreate, StockItemOut

router = APIRouter(prefix="/stock-items", tags=["stock-items"])


@router.post("", response_model=StockItemOut, status_code=201, dependencies=[Depends(require_admin)])
def create_stock_item_endpoint(payload: StockItemCreate, db: Session = Depends(get_db)) -> StockItemOut:
    item = create_stock_item(db, name=payload.name, unit=payload.unit)
    return StockItemOut.model_validate(item)


@router.get("", response_model=list[StockItemOut], dependencies=[Depends(require_staff_or_admin)])
def list_stock_items_endpoint(db: Session = Depends(get_db)) -> list[StockItemOut]:
    return [StockItemOut.model_validate(i) for i in list_stock_items(db)]
