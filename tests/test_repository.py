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
