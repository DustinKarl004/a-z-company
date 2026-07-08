from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, require_admin_password
from app.crud.branches import get_branch
from app.crud.users import create_user, delete_user, get_user, get_user_by_email, list_staff, update_user
from app.schemas.user import StaffCreate, StaffOut, StaffUpdate

router = APIRouter(prefix="/staff", tags=["staff"], dependencies=[Depends(require_admin)])


def _get_staff_or_404(db: Session, staff_id: str):
    user = get_user(db, staff_id)
    if user is None or user.role != "staff":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    return user


@router.post("", response_model=StaffOut, status_code=201)
def create_staff_endpoint(payload: StaffCreate, db: Session = Depends(get_db)) -> StaffOut:
    is_all_branch_delivery = payload.roles == ["delivery"]
    branch_id = None if is_all_branch_delivery else payload.branch_id
    if not is_all_branch_delivery:
        if not branch_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="branch_id is required")
        if get_branch(db, branch_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid branch_id")
    if get_user_by_email(db, payload.email) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    staff = create_user(
        db,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role="staff",
        branch_id=branch_id,
        roles=payload.roles,
    )
    return StaffOut.model_validate(staff)


@router.get("", response_model=list[StaffOut])
def list_staff_endpoint(branch_id: str | None = None, db: Session = Depends(get_db)) -> list[StaffOut]:
    return [StaffOut.model_validate(s) for s in list_staff(db, branch_id=branch_id)]


@router.get("/{staff_id}", response_model=StaffOut)
def get_staff_endpoint(staff_id: str, db: Session = Depends(get_db)) -> StaffOut:
    return StaffOut.model_validate(_get_staff_or_404(db, staff_id))


@router.patch("/{staff_id}", response_model=StaffOut)
def update_staff_endpoint(
    staff_id: str, payload: StaffUpdate, db: Session = Depends(get_db)
) -> StaffOut:
    staff = _get_staff_or_404(db, staff_id)
    target_roles = payload.roles if payload.roles is not None else staff.roles
    is_all_branch_delivery = target_roles == ["delivery"]

    clear_branch = False
    if is_all_branch_delivery:
        clear_branch = True
    else:
        effective_branch_id = payload.branch_id if payload.branch_id is not None else staff.branch_id
        if not effective_branch_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="branch_id is required")
        if payload.branch_id is not None and get_branch(db, payload.branch_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid branch_id")

    updated = update_user(
        db,
        staff,
        name=payload.name,
        branch_id=payload.branch_id,
        clear_branch=clear_branch,
        is_active=payload.is_active,
        password=payload.password,
        roles=payload.roles,
    )
    return StaffOut.model_validate(updated)


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff_endpoint(
    staff_id: str, db: Session = Depends(get_db), _: object = Depends(require_admin_password)
) -> None:
    staff = _get_staff_or_404(db, staff_id)
    if staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deactivate this staff member before deleting them",
        )
    if not delete_user(db, staff):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This staff member has existing sales, delivery, or stock records and cannot be deleted.",
        )
