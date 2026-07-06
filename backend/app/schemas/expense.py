from datetime import date as date_type, datetime

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCreate(BaseModel):
    branch_id: str
    date: date_type = Field(default_factory=date_type.today)
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
