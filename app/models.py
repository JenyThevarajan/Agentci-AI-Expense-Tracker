"""SQLite table for expenses. Amounts are integer cents to keep totals exact."""

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

CATEGORIES = ("Travel", "Meals", "Supplies", "Utilities", "Other")


class Base(DeclarativeBase):
    pass


class ExpenseRow(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("length(title) >= 1 AND length(title) <= 100", name="ck_expenses_title_len"),
        CheckConstraint("amount_cents > 0", name="ck_expenses_amount_positive"),
        CheckConstraint(
            "category IN ('Travel', 'Meals', 'Supplies', 'Utilities', 'Other')",
            name="ck_expenses_category",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    expense_date: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
