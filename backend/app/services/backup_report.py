"""Builds the same per-day branch report the Expenses page's "Export Excel"
button computes client-side (see fetchDayReport in AdminExpensesView.vue),
so the daily backup workbook matches that report exactly for a single day.
"""

from dataclasses import dataclass, field
from datetime import date as date_type, timedelta

from sqlalchemy.orm import Session

from app.crud.branches import list_branches
from app.crud.expenses import list_expenses
from app.crud.sales import list_sales
from app.crud.stock_counts import list_counts
from app.crud.stock_deliveries import list_deliveries
from app.crud.stock_items import list_stock_items


def round2(n: float) -> float:
    return round(n + 1e-9, 2)


@dataclass
class ItemRow:
    item_name: str
    unit: str
    opening: float
    delivery: float
    price: float
    closing: float | None
    has_closing: bool
    used: float | None
    expense: float | None


@dataclass
class BranchGroup:
    branch_id: str
    name: str
    rows: list[ItemRow]
    total: float


@dataclass
class BranchSummary:
    branch_name: str
    sales: float
    bills: float
    stock_expense: float
    total_expense: float
    profit: float


@dataclass
class DayReport:
    date: date_type
    groups: list[BranchGroup] = field(default_factory=list)
    summaries: list[BranchSummary] = field(default_factory=list)
    totals: dict = field(default_factory=dict)


def build_day_report(db: Session, date_: date_type) -> DayReport:
    branches = list_branches(db)
    items = list_stock_items(db)
    previous_date = date_ - timedelta(days=1)

    closing_yesterday = list_counts(db, date_=previous_date)
    closing_today = list_counts(db, date_=date_)
    deliveries_today = list_deliveries(db, date_=date_)
    expenses_today = list_expenses(db, date_=date_)
    sales_today = list_sales(db, date_=date_)

    opening_map = {(c.branch_id, c.item_id): c.quantity_remaining for c in closing_yesterday}
    closing_map = {(c.branch_id, c.item_id): c.quantity_remaining for c in closing_today}
    delivery_map: dict[tuple[str, str], float] = {}
    for d in deliveries_today:
        key = (d.branch_id, d.item_id)
        delivery_map[key] = delivery_map.get(key, 0) + d.quantity_delivered
    bills_map = {e.branch_id: e.amount for e in expenses_today}
    sales_map = {s.branch_id: s.amount for s in sales_today if s.item_id is None}

    groups: list[BranchGroup] = []
    for branch in branches:
        rows: list[ItemRow] = []
        for item in items:
            branch_ids = item.branch_ids
            if branch_ids and branch.id not in branch_ids:
                continue
            key = (branch.id, item.id)
            opening = opening_map.get(key) or 0
            delivery = delivery_map.get(key) or 0
            closing_raw = closing_map.get(key)
            has_closing = closing_raw is not None
            closing = closing_raw if has_closing else None
            used = round2(opening + delivery - closing) if has_closing else None
            expense = round2(used * (item.price or 0)) if has_closing else None
            rows.append(
                ItemRow(
                    item_name=item.name,
                    unit=item.unit or "",
                    opening=opening,
                    delivery=delivery,
                    price=item.price or 0,
                    closing=closing,
                    has_closing=has_closing,
                    used=used,
                    expense=expense,
                )
            )
        total = round2(sum(r.expense or 0 for r in rows))
        groups.append(BranchGroup(branch_id=branch.id, name=branch.name, rows=rows, total=total))

    totals_by_branch = {g.branch_id: g.total for g in groups}
    summaries: list[BranchSummary] = []
    for branch in branches:
        sales = sales_map.get(branch.id) or 0
        bills = bills_map.get(branch.id) or 0
        stock_expense = totals_by_branch.get(branch.id, 0)
        total_expense = round2(bills + stock_expense)
        summaries.append(
            BranchSummary(
                branch_name=branch.name,
                sales=sales,
                bills=bills,
                stock_expense=stock_expense,
                total_expense=total_expense,
                profit=round2(sales - total_expense),
            )
        )

    totals = {
        "sales": round2(sum(s.sales for s in summaries)),
        "bills": round2(sum(s.bills for s in summaries)),
        "stock_expense": round2(sum(s.stock_expense for s in summaries)),
        "total_expense": round2(sum(s.total_expense for s in summaries)),
        "profit": round2(sum(s.profit for s in summaries)),
    }

    return DayReport(date=date_, groups=groups, summaries=summaries, totals=totals)


def build_month_reports(db: Session, up_to: date_type) -> list[DayReport]:
    """One DayReport per day from the 1st of `up_to`'s month through `up_to`
    itself — the data behind a whole month's backup workbook."""
    start = up_to.replace(day=1)
    return [build_day_report(db, start + timedelta(days=i)) for i in range((up_to - start).days + 1)]
