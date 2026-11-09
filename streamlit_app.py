"""Optional Streamlit front end for deploying the expense portal on Streamlit Cloud."""

from contextlib import contextmanager
from datetime import date
from typing import Iterator

import streamlit as st

from app import database
from app.models import CATEGORIES
from app.repository import SqlAlchemyExpenseRepository
from app.service import ExpenseService
from app.validation import ValidationFailed


@st.cache_resource
def _initialize_database() -> bool:
    database.init_db()
    return True


@contextmanager
def _service() -> Iterator[ExpenseService]:
    _initialize_database()
    assert database.SessionLocal is not None
    session = database.SessionLocal()
    try:
        yield ExpenseService(SqlAlchemyExpenseRepository(session))
    finally:
        session.close()


def _clear_dates() -> None:
    st.session_state.start_filter = None
    st.session_state.end_filter = None
    st.session_state.filters_submitted = True


def _clear_category() -> None:
    st.session_state.category_filter = "All categories"
    st.session_state.filters_submitted = True


st.set_page_config(page_title="Smart Expense Management Portal", page_icon="💼", layout="wide")
st.title("Smart Expense Management Portal")
st.warning(
    "Shared demo ledger: there is no sign-in. Do not enter sensitive or confidential expense data."
)

page = st.sidebar.radio("Go to", ["Dashboard", "Expenses", "Add expense"])

if page == "Add expense":
    st.header("Add expense")
    with st.form("add_expense", clear_on_submit=False):
        title = st.text_input("Title", max_chars=100)
        amount = st.text_input("Amount", placeholder="e.g. 48.00")
        category = st.selectbox("Category", CATEGORIES)
        expense_date = st.date_input("Date", value=date.today(), max_value=date.today())
        submitted = st.form_submit_button("Save expense", type="primary")

    if submitted:
        try:
            with _service() as service:
                saved = service.create(
                    {
                        "title": title,
                        "amount": amount,
                        "category": category,
                        "date": expense_date.isoformat(),
                    }
                )
            st.success(f"Saved {saved.title} — {saved.amount}.")
            st.rerun()
        except ValidationFailed as exc:
            for error in exc.errors:
                st.error(f"{error.field.title()}: {error.message}")
        except Exception:
            st.error("Something went wrong. Try again.")

elif page == "Expenses":
    st.header("Expenses")

    st.session_state.setdefault("category_filter", "All categories")
    st.session_state.setdefault("start_filter", None)
    st.session_state.setdefault("end_filter", None)
    st.session_state.setdefault("filters_submitted", False)

    clear_dates, clear_category = st.columns(2)
    clear_dates.button("Clear dates", on_click=_clear_dates)
    clear_category.button("Clear category", on_click=_clear_category)

    with st.form("expense_filters"):
        st.selectbox("Category", ["All categories", *CATEGORIES], key="category_filter")
        st.date_input("Start date", value=None, key="start_filter", format="YYYY-MM-DD")
        st.date_input("End date", value=None, key="end_filter", format="YYYY-MM-DD")
        submitted = st.form_submit_button("Apply filters")

    if submitted:
        st.session_state.filters_submitted = True

    category_filter = st.session_state.category_filter
    active_category = None if category_filter == "All categories" else category_filter
    start_value = st.session_state.start_filter
    end_value = st.session_state.end_filter
    start_filter = start_value.isoformat() if isinstance(start_value, date) else None
    end_filter = end_value.isoformat() if isinstance(end_value, date) else None
    try:
        with _service() as service:
            expenses = service.list_expenses(
                active_category if st.session_state.filters_submitted else None,
                start_filter if st.session_state.filters_submitted else None,
                end_filter if st.session_state.filters_submitted else None,
            )
        if expenses:
            st.dataframe(
                [expense.as_dict() for expense in expenses],
                use_container_width=True,
                hide_index=True,
            )
        elif st.session_state.filters_submitted and (active_category or start_filter or end_filter):
            st.info("No expenses match these filters.")
        else:
            st.info("No expenses yet.")
    except ValidationFailed as exc:
        for error in exc.errors:
            st.error(f"{error.field.title()}: {error.message}")
    except Exception:
        st.error("Something went wrong. Try again.")

else:
    st.header("Dashboard")
    try:
        with _service() as service:
            dashboard = service.dashboard()
        st.metric("Total expenses", dashboard.total)
        if dashboard.by_category:
            columns = st.columns(len(dashboard.by_category))
            for column, item in zip(columns, dashboard.by_category):
                column.metric(item.category, item.total)
        else:
            st.info("No category totals yet.")
    except Exception:
        st.error("Something went wrong. Try again.")
