from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff
from app.core.security import create_access_token, verify_password
from app.crud.branches import get_branch
from app.crud.users import update_user
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.me import MeBranchUpdate, MeOut, MePasswordUpdate

router = APIRouter(prefix="/me", tags=["me"], dependencies=[Depends(require_staff)])


def _me_out(user: User) -> MeOut:
    return MeOut(
        id=user.id,
        name=user.name,
        email=user.email,
        roles=user.roles,
        branch_id=user.branch_id,
        branch_name=user.branch.name if user.branch else None,
    )


@router.get("", response_model=MeOut)
def get_me(user: User = Depends(require_staff)) -> MeOut:
    return _me_out(user)


@router.patch("/branch", response_model=TokenResponse)
def update_my_branch(
    payload: MeBranchUpdate, db: Session = Depends(get_db), user: User = Depends(require_staff)
) -> TokenResponse:
    if "staff" not in user.roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This account is not assigned to a branch")
    branch = get_branch(db, payload.branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid branch_id")

    updated = update_user(db, user, branch_id=payload.branch_id)
    token = create_access_token(
        user_id=updated.id,
        role=updated.role,
        roles=updated.roles,
        branch_id=updated.branch_id,
        branch_name=branch.name,
    )
    return TokenResponse(access_token=token)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    payload: MePasswordUpdate, db: Session = Depends(get_db), user: User = Depends(require_staff)
) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    update_user(db, user, password=payload.new_password)
