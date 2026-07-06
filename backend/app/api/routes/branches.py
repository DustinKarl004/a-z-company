from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.crud.branches import create_branch, list_branches
from app.schemas.branch import BranchCreate, BranchOut

router = APIRouter(prefix="/branches", tags=["branches"], dependencies=[Depends(require_admin)])


@router.post("", response_model=BranchOut, status_code=201)
def create_branch_endpoint(payload: BranchCreate, db: Session = Depends(get_db)) -> BranchOut:
    branch = create_branch(db, name=payload.name)
    return BranchOut.model_validate(branch)


@router.get("", response_model=list[BranchOut])
def list_branches_endpoint(db: Session = Depends(get_db)) -> list[BranchOut]:
    return [BranchOut.model_validate(b) for b in list_branches(db)]
