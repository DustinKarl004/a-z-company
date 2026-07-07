from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, require_admin_password
from app.core.scoping import resolve_branch_id
from app.crud.branches import get_branch
from app.crud.expenses import (
    create_expense,
    delete_expense,
    get_expense,
    get_expense_for_day,
    list_expenses,
    update_expense,
)
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseOut

router = APIRouter(prefix="/expenses", tags=["expenses"], dependencies=[Depends(require_admin)])


@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense_endpoint(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> ExpenseOut:
    branch_id = resolve_branch_id(user, payload.branch_id)
    if get_branch(db, branch_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid branch_id")

    existing = get_expense_for_day(db, branch_id=branch_id, date_=payload.date)
    if existing is not None:
        expense = update_expense(db, existing, amount=payload.amount)
    else:
        expense = create_expense(
            db,
            branch_id=branch_id,
            date_=payload.date,
            description=payload.description,
            amount=payload.amount,
            created_by_id=user.id,
        )
    return ExpenseOut.model_validate(expense)


@router.get("", response_model=list[ExpenseOut])
def list_expenses_endpoint(
    branch_id: str | None = None,
    date: date_type | None = None,
    db: Session = Depends(get_db),
) -> list[ExpenseOut]:
    return [ExpenseOut.model_validate(e) for e in list_expenses(db, branch_id=branch_id, date_=date)]


@router.delete("/{expense_id}", status_code=204)
def delete_expense_endpoint(
    expense_id: str, db: Session = Depends(get_db), _: object = Depends(require_admin_password)
) -> None:
    expense = get_expense(db, expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    delete_expense(db, expense)
