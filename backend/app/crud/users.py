from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def any_admin_exists(db: Session) -> bool:
    return db.scalar(select(User).where(User.role == "admin")) is not None


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: str,
    branch_id: str | None,
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        branch_id=branch_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_staff(db: Session, *, branch_id: str | None = None) -> list[User]:
    stmt = select(User).where(User.role == "staff")
    if branch_id:
        stmt = stmt.where(User.branch_id == branch_id)
    return list(db.scalars(stmt.order_by(User.name)))


def update_user(
    db: Session,
    user: User,
    *,
    name: str | None = None,
    branch_id: str | None = None,
    is_active: bool | None = None,
    password: str | None = None,
) -> User:
    if name is not None:
        user.name = name
    if branch_id is not None:
        user.branch_id = branch_id
    if is_active is not None:
        user.is_active = is_active
    if password is not None:
        user.password_hash = hash_password(password)
    db.commit()
    db.refresh(user)
    return user
