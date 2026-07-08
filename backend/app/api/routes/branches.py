from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, require_admin_password, require_staff_or_admin
from app.crud.branches import create_branch, delete_branch, get_branch, list_branches, update_branch
from app.schemas.branch import BranchCreate, BranchOut, BranchUpdate

router = APIRouter(prefix="/branches", tags=["branches"])


def _get_branch_or_404(db: Session, branch_id: str):
    branch = get_branch(db, branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return branch


@router.post("", response_model=BranchOut, status_code=201, dependencies=[Depends(require_admin)])
def create_branch_endpoint(payload: BranchCreate, db: Session = Depends(get_db)) -> BranchOut:
    branch = create_branch(db, name=payload.name)
    return BranchOut.model_validate(branch)


@router.get("", response_model=list[BranchOut], dependencies=[Depends(require_staff_or_admin)])
def list_branches_endpoint(db: Session = Depends(get_db)) -> list[BranchOut]:
    return [BranchOut.model_validate(b) for b in list_branches(db)]


@router.patch("/{branch_id}", response_model=BranchOut, dependencies=[Depends(require_admin)])
def update_branch_endpoint(
    branch_id: str, payload: BranchUpdate, db: Session = Depends(get_db)
) -> BranchOut:
    branch = _get_branch_or_404(db, branch_id)
    branch = update_branch(db, branch, name=payload.name)
    return BranchOut.model_validate(branch)


@router.delete("/{branch_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_branch_endpoint(
    branch_id: str, db: Session = Depends(get_db), _: object = Depends(require_admin_password)
) -> None:
    branch = _get_branch_or_404(db, branch_id)
    if not delete_branch(db, branch):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This branch still has staff or records linked to it and cannot be deleted.",
        )
