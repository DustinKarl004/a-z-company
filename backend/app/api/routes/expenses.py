from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.crud.branches import get_branch
from app.crud.expenses import create_expense, list_expenses
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseOut

router = APIRouter(prefix="/expenses", tags=["expenses"], dependencies=[Depends(require_admin)])


@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense_endpoint(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> ExpenseOut:
    if get_branch(db, payload.branch_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid branch_id")

    expense = create_expense(
        db,
        branch_id=payload.branch_id,
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
