from datetime import date as date_type, datetime

from pydantic import BaseModel, ConfigDict, Field


class StockDeliveryCreate(BaseModel):
    branch_id: str | None = None
    item_id: str
    date: date_type = Field(default_factory=date_type.today)
    quantity_delivered: float
    is_short: bool = False


class StockDeliveryUpdate(BaseModel):
    quantity_delivered: float | None = None
    is_short: bool | None = None


class StockDeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    branch_id: str
    item_id: str
    date: date_type
    quantity_delivered: float
    is_short: bool
    created_by_id: str
    created_at: datetime
