"""Data access for expenses. SQLAlchemy sends bound parameters, not concatenated SQL."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ExpenseRow


@dataclass(frozen=True)
class ExpenseRecord:
    id: int
    title: str
    amount_cents: int
    category: str
    expense_date: str


class ExpenseStore(Protocol):
    def add(
        self,
        title: str,
        amount_cents: int,
        category: str,
        expense_date: str,
        created_at: str,
    ) -> ExpenseRecord: ...

    def list_expenses(self, category: str | None) -> list[ExpenseRecord]: ...

    def summarize(self) -> tuple[int, list[tuple[str, int]]]: ...


class SqlAlchemyExpenseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        title: str,
        amount_cents: int,
        category: str,
        expense_date: str,
        created_at: str,
    ) -> ExpenseRecord:
        row = ExpenseRow(
            title=title,
            amount_cents=amount_cents,
            category=category,
            expense_date=expense_date,
            created_at=created_at,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_record(row)

    def list_expenses(self, category: str | None) -> list[ExpenseRecord]:
        statement = select(ExpenseRow).order_by(
            ExpenseRow.expense_date.desc(),
            ExpenseRow.id.desc(),
        )
        if category is not None:
            statement = statement.where(ExpenseRow.category == category)
        rows = self._session.scalars(statement).all()
        return [_to_record(row) for row in rows]

    def summarize(self) -> tuple[int, list[tuple[str, int]]]:
        total = self._session.scalar(select(func.coalesce(func.sum(ExpenseRow.amount_cents), 0)))
        grouped = self._session.execute(
            select(ExpenseRow.category, func.sum(ExpenseRow.amount_cents))
            .group_by(ExpenseRow.category)
            .having(func.sum(ExpenseRow.amount_cents) > 0)
            .order_by(ExpenseRow.category)
        ).all()
        return int(total or 0), [(category, int(cents)) for category, cents in grouped]


def _to_record(row: ExpenseRow) -> ExpenseRecord:
    return ExpenseRecord(
        id=row.id,
        title=row.title,
        amount_cents=row.amount_cents,
        category=row.category,
        expense_date=row.expense_date,
    )
