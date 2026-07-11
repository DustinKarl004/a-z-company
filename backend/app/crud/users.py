import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.sale import Sale
from app.models.stock_count import StockCount
from app.models.stock_delivery import StockDelivery
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def any_admin_exists(db: Session) -> bool:
    return db.scalar(select(User).where(User.role == "admin")) is not None


def any_superuser_exists(db: Session) -> bool:
    return db.scalar(select(User).where(User.role == "superuser")) is not None


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: str,
    branch_id: str | None,
    roles: list[str] | None = None,
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        branch_id=branch_id,
    )
    user.roles = roles or ["staff"]
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def user_has_related_records(db: Session, user_id: str) -> bool:
    for model in (Sale, StockCount, StockDelivery):
        if db.scalar(select(model.id).where(model.created_by_id == user_id).limit(1)) is not None:
            return True
    return False


def delete_user(db: Session, user: User) -> bool:
    if user_has_related_records(db, user.id):
        return False
    db.delete(user)
    db.commit()
    return True


def set_totp_secret(db: Session, user: User, secret: str | None) -> User:
    user.totp_secret = secret
    db.commit()
    db.refresh(user)
    return user


def set_backup_codes(db: Session, user: User, codes: list[str] | None) -> User:
    user.backup_codes = json.dumps([hash_password(code) for code in codes]) if codes else None
    db.commit()
    db.refresh(user)
    return user


def consume_backup_code(db: Session, user: User, code: str) -> bool:
    if not user.backup_codes:
        return False
    hashes = json.loads(user.backup_codes)
    for hashed in hashes:
        if verify_password(code, hashed):
            hashes.remove(hashed)
            user.backup_codes = json.dumps(hashes)
            db.commit()
            return True
    return False


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
    clear_branch: bool = False,
    is_active: bool | None = None,
    password: str | None = None,
    roles: list[str] | None = None,
) -> User:
    if name is not None:
        user.name = name
    if clear_branch:
        user.branch_id = None
    elif branch_id is not None:
        user.branch_id = branch_id
    if is_active is not None:
        user.is_active = is_active
    if password is not None:
        user.password_hash = hash_password(password)
    if roles is not None:
        user.roles = roles
    db.commit()
    db.refresh(user)
    return user
