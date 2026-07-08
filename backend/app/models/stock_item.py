from sqlalchemy import Column, Float, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin

stock_item_branches = Table(
    "stock_item_branches",
    Base.metadata,
    Column("item_id", String(12), ForeignKey("stock_items.id"), primary_key=True),
    Column("branch_id", String(12), ForeignKey("branches.id"), primary_key=True),
)


class StockItem(Base, IdMixin):
    __tablename__ = "stock_items"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    branches: Mapped[list["Branch"]] = relationship(secondary=stock_item_branches)

    @property
    def branch_ids(self) -> list[str]:
        return [b.id for b in self.branches]
