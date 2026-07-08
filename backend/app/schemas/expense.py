from datetime import date as date_type, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.clock import local_today


class ExpenseCreate(BaseModel):
    branch_id: str | None = None
    date: date_type = Field(default_factory=local_today)
    description: str
    amount: float


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    branch_id: str
    date: date_type
    description: str
    amount: float
    created_by_id: str
    created_at: datetime
