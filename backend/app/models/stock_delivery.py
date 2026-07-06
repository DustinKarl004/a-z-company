from datetime import date as date_type

from sqlalchemy import Boolean, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin


class StockDelivery(Base, IdMixin):
    __tablename__ = "stock_deliveries"

    branch_id: Mapped[str] = mapped_column(String(12), ForeignKey("branches.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(String(12), ForeignKey("stock_items.id"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    quantity_delivered: Mapped[float] = mapped_column(Float, nullable=False)
    is_short: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_id: Mapped[str] = mapped_column(String(12), ForeignKey("users.id"), nullable=False)
