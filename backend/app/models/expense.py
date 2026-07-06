from datetime import date as date_type

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin


class Expense(Base, IdMixin):
    __tablename__ = "expenses"

    branch_id: Mapped[str] = mapped_column(String(12), ForeignKey("branches.id"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_by_id: Mapped[str] = mapped_column(String(12), ForeignKey("users.id"), nullable=False)
