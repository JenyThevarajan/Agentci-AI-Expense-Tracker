"""HTTP coverage for the pages and JSON API."""

import re

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
    assert "No expenses in this category." in filtered.text
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


def test_api_rejects_a_non_json_body(client: TestClient):
    response = client.post("/api/expenses", content="not-json", headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "body"
