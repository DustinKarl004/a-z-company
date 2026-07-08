from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_admin
from app.core.scoping import ensure_creatable_date, ensure_editable, resolve_branch_id
from app.crud.branches import get_branch
from app.crud.stock_deliveries import (
    clear_stale_short_flags,
    create_delivery,
    get_delivery,
    get_delivery_for_day,
    list_deliveries,
    update_delivery,
)
from app.crud.stock_items import get_stock_item
from app.models.user import User
from app.schemas.stock_delivery import (
    StockDeliveryCreate,
    StockDeliveryOut,
    StockDeliveryUpdate,
)

router = APIRouter(prefix="/stock-deliveries", tags=["stock-deliveries"])


@router.post("", response_model=StockDeliveryOut, status_code=201)
def create_delivery_endpoint(
    payload: StockDeliveryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> StockDeliveryOut:
    branch_id = resolve_branch_id(user, payload.branch_id)
    if get_branch(db, branch_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid branch_id")
    if get_stock_item(db, payload.item_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item_id")
    ensure_creatable_date(user, payload.date)

    existing = get_delivery_for_day(db, branch_id=branch_id, item_id=payload.item_id, date_=payload.date)
    if existing is not None:
        updated = update_delivery(
            db, existing, quantity_delivered=payload.quantity_delivered, is_short=payload.is_short
        )
        return StockDeliveryOut.model_validate(updated)

    delivery = create_delivery(
        db,
        branch_id=branch_id,
        item_id=payload.item_id,
        date_=payload.date,
        quantity_delivered=payload.quantity_delivered,
        is_short=payload.is_short,
        created_by_id=user.id,
    )
    return StockDeliveryOut.model_validate(delivery)


@router.get("", response_model=list[StockDeliveryOut])
def list_deliveries_endpoint(
    branch_id: str | None = None,
    date: date_type | None = None,
    is_short: bool | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> list[StockDeliveryOut]:
    if is_short:
        clear_stale_short_flags(db)
    effective_branch_id = branch_id if (user.role == "admin" or not user.branch_id) else user.branch_id
    return [
        StockDeliveryOut.model_validate(d)
        for d in list_deliveries(db, branch_id=effective_branch_id, date_=date, is_short=is_short)
    ]


@router.patch("/{delivery_id}", response_model=StockDeliveryOut)
def update_delivery_endpoint(
    delivery_id: str,
    payload: StockDeliveryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> StockDeliveryOut:
    delivery = get_delivery(db, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
    if user.role == "staff" and user.branch_id and delivery.branch_id != user.branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your branch")
    if payload.quantity_delivered is not None or payload.is_short is not None:
        ensure_editable(user, delivery.date)

    updated = update_delivery(
        db,
        delivery,
        quantity_delivered=payload.quantity_delivered,
        is_short=payload.is_short,
        is_delivered=payload.is_delivered,
    )
    return StockDeliveryOut.model_validate(updated)
