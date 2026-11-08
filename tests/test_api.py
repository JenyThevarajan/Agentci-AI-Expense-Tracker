"""HTTP coverage for the pages and JSON API."""

import re
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "expenses.sqlite"))
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_health_and_home_redirect(client: TestClient):
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


def test_dashboard_starts_empty(client: TestClient):
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert "0.00" in page.text
    assert "No category totals yet." in page.text


def test_add_expense_appears_in_list_and_dashboard(client: TestClient):
    form = client.get("/expenses/new")
    token = re.search(r'name="csrf_token" value="([^"]+)"', form.text).group(1)
    saved = client.post(
        "/expenses",
        data={
            "csrf_token": token,
            "title": "Client visit",
            "amount": "48.00",
            "category": "Travel",
            "date": "2026-11-01",
        },
        follow_redirects=False,
    )
    assert saved.status_code == 303
    listing = client.get("/expenses")
    assert "Client visit" in listing.text
    assert "48.00" in listing.text
    filtered = client.get("/expenses", params={"category": "Meals"})
    assert "No expenses match these filters." in filtered.text
    cleared = client.get("/expenses")
    assert "Client visit" in cleared.text
    dashboard = client.get("/dashboard")
    assert "48.00" in dashboard.text
    assert "Travel" in dashboard.text


def test_invalid_form_keeps_entered_values(client: TestClient):
    form = client.get("/expenses/new")
    token = re.search(r'name="csrf_token" value="([^"]+)"', form.text).group(1)
    response = client.post(
        "/expenses",
        data={
            "csrf_token": token,
            "title": "",
            "amount": "0",
            "category": "Travel",
            "date": "2026-11-01",
        },
    )
    assert response.status_code == 422
    assert "Title is required." in response.text
    assert "Amount must be greater than 0." in response.text
    assert "2026-11-01" in response.text
    assert "No expenses yet." in client.get("/expenses").text


def test_api_create_list_filter_and_dashboard(client: TestClient):
    created = client.post(
        "/api/expenses",
        json={"title": "Lunch", "amount": "25.50", "category": "Meals", "date": "2026-11-01"},
    )
    assert created.status_code == 201
    assert created.json()["amount"] == "25.50"

    rejected = client.post("/api/expenses", json={"title": "Bad", "amount": "1.999", "category": "Meals", "date": "2026-11-01"})
    assert rejected.status_code == 422
    assert rejected.json()["errors"][0]["field"] == "amount"

    unknown = client.get("/api/expenses", params={"category": "Payroll"})
    assert unknown.status_code == 422
    listed = client.get("/api/expenses", params={"category": "Meals"})
    assert listed.status_code == 200
    assert listed.json()["expenses"][0]["title"] == "Lunch"

    dashboard = client.get("/api/dashboard")
    assert dashboard.json() == {
        "total": "25.50",
        "byCategory": [{"category": "Meals", "total": "25.50"}],
    }


def _iso(day: date) -> str:
    return day.isoformat()


def _create(client: TestClient, **overrides: str) -> None:
    payload = {
        "title": "Item",
        "amount": "10.00",
        "category": "Travel",
        "date": _iso(date.today()),
    }
    payload.update(overrides)
    created = client.post("/api/expenses", json=payload)
    assert created.status_code == 201


def test_api_date_range_filter_bounds_category_empty_and_dashboard(client: TestClient):
    today = date.today()
    before = today - timedelta(days=10)
    start = today - timedelta(days=5)
    middle = today - timedelta(days=3)
    end = today
    _create(client, title="Before", amount="10.00", category="Travel", date=_iso(before))
    _create(client, title="Start", amount="20.00", category="Travel", date=_iso(start))
    _create(client, title="Middle", amount="5.00", category="Meals", date=_iso(middle))
    _create(client, title="End", amount="7.00", category="Travel", date=_iso(end))

    both = client.get("/api/expenses", params={"start": _iso(start), "end": _iso(end)})
    assert both.status_code == 200
    assert [item["title"] for item in both.json()["expenses"]] == ["End", "Middle", "Start"]

    start_only = client.get("/api/expenses", params={"start": f"  {_iso(middle)}  "})
    assert start_only.status_code == 200
    assert [item["title"] for item in start_only.json()["expenses"]] == ["End", "Middle"]

    end_only = client.get("/api/expenses", params={"end": _iso(start)})
    assert end_only.status_code == 200
    assert [item["title"] for item in end_only.json()["expenses"]] == ["Start", "Before"]

    combined = client.get(
        "/api/expenses",
        params={"category": "Travel", "start": _iso(start), "end": _iso(end)},
    )
    assert combined.status_code == 200
    assert [item["title"] for item in combined.json()["expenses"]] == ["End", "Start"]

    cleared = client.get("/api/expenses", params={"category": "Travel"})
    assert cleared.status_code == 200
    assert [item["title"] for item in cleared.json()["expenses"]] == ["End", "Start", "Before"]

    empty = client.get(
        "/api/expenses",
        params={"start": _iso(today + timedelta(days=1)), "end": _iso(today + timedelta(days=2))},
    )
    assert empty.status_code == 200
    assert empty.json() == {"expenses": []}

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["total"] == "42.00"


def test_api_rejects_invalid_date_ranges_without_a_list(client: TestClient):
    _create(client, title="Kept", amount="10.00", date=_iso(date.today()))

    reversed_bounds = client.get("/api/expenses", params={"start": "2026-12-01", "end": "2026-01-01"})
    assert reversed_bounds.status_code == 422
    assert reversed_bounds.json() == {
        "errors": [{"field": "start", "message": "Start date must be on or before the end date."}]
    }
    assert "expenses" not in reversed_bounds.json()

    bad_start = client.get("/api/expenses", params={"start": "2026-11-1", "end": "2026-11-07"})
    assert bad_start.status_code == 422
    assert [error["field"] for error in bad_start.json()["errors"]] == ["start"]
    assert "expenses" not in bad_start.json()

    bad_end = client.get("/api/expenses", params={"end": "2026-02-31"})
    assert bad_end.status_code == 422
    assert [error["field"] for error in bad_end.json()["errors"]] == ["end"]

    both_bad = client.get("/api/expenses", params={"start": "11/01/2026", "end": "2026-13-01"})
    assert both_bad.status_code == 422
    assert [error["field"] for error in both_bad.json()["errors"]] == ["start", "end"]

    category_and_end = client.get("/api/expenses", params={"category": "Payroll", "end": "nope"})
    assert category_and_end.status_code == 422
    assert [error["field"] for error in category_and_end.json()["errors"]] == ["category", "end"]

    listed = client.get("/api/expenses")
    assert listed.status_code == 200
    assert [item["title"] for item in listed.json()["expenses"]] == ["Kept"]


def test_api_rejects_a_non_json_body(client: TestClient):
    response = client.post("/api/expenses", content="not-json", headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "body"
