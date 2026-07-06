from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_admin
from app.core.scoping import ensure_creatable_date, ensure_editable, resolve_branch_id
from app.crud.branches import get_branch
from app.crud.stock_counts import create_count, get_count, list_counts, update_count
from app.crud.stock_items import get_stock_item
from app.models.user import User
from app.schemas.stock_count import StockCountCreate, StockCountOut, StockCountUpdate

router = APIRouter(prefix="/stock-counts", tags=["stock-counts"])


@router.post("", response_model=StockCountOut, status_code=201)
def create_count_endpoint(
    payload: StockCountCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> StockCountOut:
    branch_id = resolve_branch_id(user, payload.branch_id)
    if get_branch(db, branch_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid branch_id")
    if get_stock_item(db, payload.item_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item_id")
    ensure_creatable_date(user, payload.date)

    count = create_count(
        db,
        branch_id=branch_id,
        item_id=payload.item_id,
        date_=payload.date,
        quantity_remaining=payload.quantity_remaining,
        created_by_id=user.id,
    )
    return StockCountOut.model_validate(count)


@router.get("", response_model=list[StockCountOut])
def list_counts_endpoint(
    branch_id: str | None = None,
    date: date_type | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> list[StockCountOut]:
    effective_branch_id = branch_id if user.role == "admin" else user.branch_id
    return [
        StockCountOut.model_validate(c)
        for c in list_counts(db, branch_id=effective_branch_id, date_=date)
    ]


@router.patch("/{count_id}", response_model=StockCountOut)
def update_count_endpoint(
    count_id: str,
    payload: StockCountUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> StockCountOut:
    count = get_count(db, count_id)
    if count is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Count not found")
    if user.role == "staff" and count.branch_id != user.branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your branch")
    ensure_editable(user, count.date)

    updated = update_count(db, count, quantity_remaining=payload.quantity_remaining)
    return StockCountOut.model_validate(updated)
