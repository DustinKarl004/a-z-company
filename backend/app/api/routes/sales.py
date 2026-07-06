from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_admin
from app.core.scoping import ensure_creatable_date, ensure_editable, resolve_branch_id
from app.crud.branches import get_branch
from app.crud.sales import create_sale, get_sale, list_sales, update_sale
from app.crud.stock_items import get_stock_item
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleOut, SaleUpdate

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleOut, status_code=201)
def create_sale_endpoint(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> SaleOut:
    branch_id = resolve_branch_id(user, payload.branch_id)
    if get_branch(db, branch_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid branch_id")
    if get_stock_item(db, payload.item_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item_id")
    ensure_creatable_date(user, payload.date)

    sale = create_sale(
        db,
        branch_id=branch_id,
        item_id=payload.item_id,
        date_=payload.date,
        quantity_sold=payload.quantity_sold,
        amount=payload.amount,
        created_by_id=user.id,
    )
    return SaleOut.model_validate(sale)


@router.get("", response_model=list[SaleOut])
def list_sales_endpoint(
    branch_id: str | None = None,
    date: date_type | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> list[SaleOut]:
    effective_branch_id = branch_id if user.role == "admin" else user.branch_id
    return [
        SaleOut.model_validate(s) for s in list_sales(db, branch_id=effective_branch_id, date_=date)
    ]


@router.patch("/{sale_id}", response_model=SaleOut)
def update_sale_endpoint(
    sale_id: str,
    payload: SaleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> SaleOut:
    sale = get_sale(db, sale_id)
    if sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
    if user.role == "staff" and sale.branch_id != user.branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your branch")
    ensure_editable(user, sale.date)

    updated = update_sale(db, sale, quantity_sold=payload.quantity_sold, amount=payload.amount)
    return SaleOut.model_validate(updated)
