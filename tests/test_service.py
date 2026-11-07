"""Unit tests for add, view, filter, and dashboard rules."""

from datetime import date

import pytest

from app.repository import ExpenseRecord
from app.service import ExpenseService
from app.validation import ValidationFailed

TODAY = date(2026, 11, 7)


class MemoryStore:
    def __init__(self) -> None:
        self.rows: list[ExpenseRecord] = []

    def add(self, title, amount_cents, category, expense_date, created_at) -> ExpenseRecord:
        record = ExpenseRecord(
            id=len(self.rows) + 1,
            title=title,
            amount_cents=amount_cents,
            category=category,
            expense_date=expense_date,
        )
        self.rows.append(record)
        return record

    def list_expenses(self, category: str | None) -> list[ExpenseRecord]:
        selected = self.rows if category is None else [row for row in self.rows if row.category == category]
        return sorted(selected, key=lambda row: (row.expense_date, row.id), reverse=True)

    def summarize(self) -> tuple[int, list[tuple[str, int]]]:
        totals: dict[str, int] = {}
        for row in self.rows:
            totals[row.category] = totals.get(row.category, 0) + row.amount_cents
        grouped = sorted((name, cents) for name, cents in totals.items() if cents > 0)
        return sum(cents for _, cents in grouped), grouped


def service_with(store: MemoryStore | None = None) -> tuple[ExpenseService, MemoryStore]:
    memory = store or MemoryStore()
    return ExpenseService(memory, today=lambda: TODAY), memory


def valid_payload(**overrides) -> dict[str, str]:
    payload = {
        "title": "Client visit",
        "amount": "48.00",
        "category": "Travel",
        "date": "2026-11-01",
    }
    payload.update(overrides)
    return payload


def test_create_stores_a_valid_expense():
    service, store = service_with()
    created = service.create(valid_payload(title="  Client visit  ", amount="48"))
    assert created.title == "Client visit"
    assert created.amount == "48.00"
    assert created.category == "Travel"
    assert created.date == "2026-11-01"
    assert len(store.rows) == 1
    assert store.rows[0].amount_cents == 4800


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", ""),
        ("title", "   "),
        ("title", "x" * 101),
        ("amount", ""),
        ("amount", "0"),
        ("amount", "-5"),
        ("amount", "abc"),
        ("amount", "1.234"),
        ("category", "Payroll"),
        ("date", ""),
        ("date", "2026-02-31"),
        ("date", "2026-11-08"),
    ],
)
def test_create_rejects_each_invalid_field(field, value):
    service, store = service_with()
    with pytest.raises(ValidationFailed) as caught:
        service.create(valid_payload(**{field: value}))
    assert any(error.field == field for error in caught.value.errors)
    assert store.rows == []


def test_create_rejects_a_non_object_payload():
    service, store = service_with()
    with pytest.raises(ValidationFailed) as caught:
        service.create(["not", "an", "object"])
    assert caught.value.errors[0].field == "body"
    assert store.rows == []


def test_list_returns_every_expense_and_an_empty_store():
    service, _store = service_with()
    assert service.list_expenses(None) == []
    service.create(valid_payload(title="Train", date="2026-11-02"))
    service.create(valid_payload(title="Lunch", amount="12.50", category="Meals", date="2026-11-03"))
    listed = service.list_expenses(None)
    assert [item.title for item in listed] == ["Lunch", "Train"]
    assert [item.amount for item in listed] == ["12.50", "48.00"]


def test_filter_returns_one_category_and_rejects_unknown_values():
    service, _store = service_with()
    service.create(valid_payload(title="Train", category="Travel"))
    service.create(valid_payload(title="Lunch", amount="12.50", category="Meals"))
    assert [item.title for item in service.list_expenses("Meals")] == ["Lunch"]
    assert service.list_expenses("Supplies") == []
    with pytest.raises(ValidationFailed):
        service.list_expenses("Payroll")


def test_dashboard_sums_all_expenses_and_ignores_list_filters():
    service, _store = service_with()
    empty = service.dashboard()
    assert empty.total == "0.00"
    assert empty.by_category == []

    service.create(valid_payload(title="Train", amount="48.00", category="Travel"))
    service.create(valid_payload(title="Lunch", amount="25.50", category="Meals"))
    summary = service.dashboard()
    assert summary.total == "73.50"
    assert [(item.category, item.total) for item in summary.by_category] == [
        ("Meals", "25.50"),
        ("Travel", "48.00"),
    ]
    assert service.list_expenses("Meals")[0].title == "Lunch"
    assert service.dashboard().total == "73.50"
