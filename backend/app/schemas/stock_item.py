from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StockItemCreate(BaseModel):
    name: str
    unit: str
    price: float
    category: str | None = None
    branch_ids: list[str] = []


class StockItemUpdate(BaseModel):
    name: str
    unit: str
    price: float
    category: str | None = None
    branch_ids: list[str] = []


class StockItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    unit: str
    price: float
    category: str | None = None
    branch_ids: list[str] = []
    created_at: datetime
