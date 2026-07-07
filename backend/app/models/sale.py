from datetime import date as date_type

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin


class Sale(Base, IdMixin):
    __tablename__ = "sales"

    branch_id: Mapped[str] = mapped_column(String(12), ForeignKey("branches.id"), nullable=False)
    item_id: Mapped[str | None] = mapped_column(String(12), ForeignKey("stock_items.id"), nullable=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    quantity_sold: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_by_id: Mapped[str] = mapped_column(String(12), ForeignKey("users.id"), nullable=False)
