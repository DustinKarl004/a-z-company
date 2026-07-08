import json

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin

DEFAULT_STAFF_ROLES = ["staff"]


class User(Base, IdMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "admin" | "staff"
    roles_json: Mapped[str] = mapped_column(
        Text, nullable=False, default=lambda: json.dumps(DEFAULT_STAFF_ROLES)
    )  # sub-roles for "staff" users, e.g. ["staff", "delivery"]
    branch_id: Mapped[str | None] = mapped_column(
        String(12), ForeignKey("branches.id"), nullable=True
    )
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    backup_codes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    branch: Mapped["Branch | None"] = relationship(back_populates="users")

    @property
    def roles(self) -> list[str]:
        return json.loads(self.roles_json) if self.roles_json else list(DEFAULT_STAFF_ROLES)

    @roles.setter
    def roles(self, value: list[str]) -> None:
        self.roles_json = json.dumps(value)
