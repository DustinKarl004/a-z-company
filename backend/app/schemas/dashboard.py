from pydantic import BaseModel


class BranchSummary(BaseModel):
    branch_id: str
    branch_name: str
    total_sales: float
    total_expenses: float
    profit: float
    has_shortfall: bool


class OverviewResponse(BaseModel):
    date: str
    branch_count: int
    staff_count: int
    branches: list[BranchSummary]
    total_sales: float
    total_expenses: float
    total_profit: float


class DailyPoint(BaseModel):
    date: str
    branch_sales: dict[str, float]
    total_sales: float


class MonthlyResponse(BaseModel):
    year: int
    month: int
    branches: list[BranchSummary]
    total_sales: float
    total_expenses: float
    total_profit: float
    daily: list[DailyPoint]
