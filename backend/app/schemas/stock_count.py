from datetime import date as date_type, datetime

from pydantic import BaseModel, ConfigDict, Field


class StockCountCreate(BaseModel):
    branch_id: str | None = None
    item_id: str
    date: date_type = Field(default_factory=date_type.today)
    quantity_remaining: float


class StockCountUpdate(BaseModel):
    quantity_remaining: float | None = None


class StockCountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    branch_id: str
    item_id: str
    date: date_type
    quantity_remaining: float
    created_by_id: str
    created_at: datetime
