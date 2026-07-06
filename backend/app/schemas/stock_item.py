from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StockItemCreate(BaseModel):
    name: str
    unit: str
    price: float


class StockItemUpdate(BaseModel):
    unit: str
    price: float


class StockItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    unit: str
    price: float
    created_at: datetime
