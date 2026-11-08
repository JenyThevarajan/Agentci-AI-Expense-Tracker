"""Repository tests against SQLite, including a title that looks like SQL."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.repository import SqlAlchemyExpenseRepository


def repository() -> SqlAlchemyExpenseRepository:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    return SqlAlchemyExpenseRepository(session)


def test_repository_persists_lists_filters_and_summarizes():
    store = repository()
    store.add("Taxi", 4800, "Travel", "2026-11-01", "2026-11-07T00:00:00+00:00")
    store.add("Lunch", 2550, "Meals", "2026-11-03", "2026-11-07T00:00:00+00:00")
    store.add("O'Hare \"late\" taxi", 1000, "Travel", "2026-11-02", "2026-11-07T00:00:00+00:00")

    listed = store.list_expenses(None)
    assert [row.title for row in listed] == ["Lunch", "O'Hare \"late\" taxi", "Taxi"]

    travel = store.list_expenses("Travel")
    assert [row.expense_date for row in travel] == ["2026-11-02", "2026-11-01"]

    total, grouped = store.summarize()
    assert total == 8350
    assert grouped == [("Meals", 2550), ("Travel", 5800)]


def test_repository_filter_with_no_rows_is_empty():
    store = repository()
    assert store.list_expenses("Utilities") == []
    assert store.summarize() == (0, [])


def test_repository_date_range_is_inclusive_and_combines_with_category():
    store = repository()
    store.add("Before", 1000, "Travel", "2026-10-01", "2026-12-01T00:00:00+00:00")
    store.add("Start", 2000, "Travel", "2026-11-01", "2026-12-01T00:00:00+00:00")
    store.add("Middle meal", 500, "Meals", "2026-11-15", "2026-12-01T00:00:00+00:00")
    store.add("First same day", 100, "Travel", "2026-11-30", "2026-12-01T00:00:00+00:00")
    store.add("Second same day", 200, "Travel", "2026-11-30", "2026-12-01T00:00:00+00:00")
    store.add('O\'Hare "late" taxi', 800, "Travel", "2026-12-01", "2026-12-01T00:00:00+00:00")

    ranged = store.list_expenses(None, "2026-11-01", "2026-11-30")
    assert [row.title for row in ranged] == ["Second same day", "First same day", "Middle meal", "Start"]

    assert [row.title for row in store.list_expenses(None, "2026-11-15", None)] == [
        'O\'Hare "late" taxi',
        "Second same day",
        "First same day",
        "Middle meal",
    ]
    assert [row.expense_date for row in store.list_expenses(None, None, "2026-11-01")] == [
        "2026-11-01",
        "2026-10-01",
    ]
    assert [row.title for row in store.list_expenses("Travel", "2026-11-01", "2026-11-30")] == [
        "Second same day",
        "First same day",
        "Start",
    ]
    assert store.list_expenses(None, "2020-01-01", "2020-01-02") == []
    quoted = store.list_expenses(None, "2026-12-01", "2026-12-01")
    assert [row.title for row in quoted] == ['O\'Hare "late" taxi']
    total, grouped = store.summarize()
    assert total == 4600
    assert ("Travel", 4100) in grouped
    assert ("Meals", 500) in grouped
