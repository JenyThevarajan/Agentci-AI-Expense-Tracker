"""Expense rules and totals. This layer does not talk to HTTP or SQL."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Callable

from app.repository import ExpenseRecord, ExpenseStore
from app.validation import (
    ExpenseInput,
    format_cents,
    validate_category_filter,
    validate_new_expense,
)


@dataclass(frozen=True)
class ExpenseView:
    id: int
    title: str
    amount: str
    category: str
    date: str

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "amount": self.amount,
            "category": self.category,
            "date": self.date,
        }


@dataclass(frozen=True)
class CategoryTotal:
    category: str
    total: str

    def as_dict(self) -> dict[str, str]:
        return {"category": self.category, "total": self.total}


@dataclass(frozen=True)
class DashboardView:
    total: str
    by_category: list[CategoryTotal]

    def as_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "byCategory": [item.as_dict() for item in self.by_category],
        }


class ExpenseService:
    def __init__(self, store: ExpenseStore, today: Callable[[], date] | None = None) -> None:
        self._store = store
        self._today = today or date.today

    def create(self, payload: object) -> ExpenseView:
        parsed: ExpenseInput = validate_new_expense(payload, self._today())
        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        record = self._store.add(
            title=parsed.title,
            amount_cents=parsed.amount_cents,
            category=parsed.category,
            expense_date=parsed.expense_date,
            created_at=created_at,
        )
        return _to_view(record)

    def list_expenses(self, category: str | None) -> list[ExpenseView]:
        selected = validate_category_filter(category)
        return [_to_view(record) for record in self._store.list_expenses(selected)]

    def dashboard(self) -> DashboardView:
        # Totals always cover every stored expense. The list filter is not applied here.
        total_cents, grouped = self._store.summarize()
        return DashboardView(
            total=format_cents(total_cents),
            by_category=[
                CategoryTotal(category=category, total=format_cents(cents))
                for category, cents in grouped
            ],
        )


def _to_view(record: ExpenseRecord) -> ExpenseView:
    return ExpenseView(
        id=record.id,
        title=record.title,
        amount=format_cents(record.amount_cents),
        category=record.category,
        date=record.expense_date,
    )
