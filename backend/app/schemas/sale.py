from datetime import date as date_type, datetime

from pydantic import BaseModel, ConfigDict, Field


class SaleCreate(BaseModel):
    branch_id: str | None = None
    item_id: str | None = None
    date: date_type = Field(default_factory=date_type.today)
    quantity_sold: float | None = None
    amount: float | None = None


class SaleUpdate(BaseModel):
    quantity_sold: float | None = None
    amount: float | None = None


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    branch_id: str
    item_id: str | None = None
    date: date_type
    quantity_sold: float
    amount: float
    created_by_id: str
    created_at: datetime
