from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.branch import Branch


def create_branch(db: Session, *, name: str) -> Branch:
    branch = Branch(name=name)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def list_branches(db: Session) -> list[Branch]:
    return list(db.scalars(select(Branch).order_by(Branch.name)))


def get_branch(db: Session, branch_id: str) -> Branch | None:
    return db.get(Branch, branch_id)
