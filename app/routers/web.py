"""Server-rendered pages for the employee portal."""

import secrets

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, Response

from app.dependencies import get_service
from app.models import CATEGORIES
from app.service import ExpenseService
from app.templating import templates
from app.validation import ValidationFailed, validate_list_filters

router = APIRouter()
_CSRF_COOKIE = "csrf_token"


def _token(request: Request) -> str:
    current = request.cookies.get(_CSRF_COOKIE)
    return current if current else secrets.token_urlsafe(32)


def _apply_csrf(response: Response, token: str) -> None:
    # Lax cookies are withheld on cross-site form posts, which blocks forged writes.
    response.set_cookie(_CSRF_COOKIE, token, httponly=True, samesite="lax")


@router.get("/")
def home() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/dashboard")
def dashboard(request: Request, service: ExpenseService = Depends(get_service)) -> Response:
    summary = service.dashboard()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "total": summary.total,
            "by_category": summary.by_category,
            "active": "dashboard",
        },
    )


@router.get("/expenses/new")
def new_expense(request: Request) -> Response:
    token = _token(request)
    response = templates.TemplateResponse(
        request,
        "expense_form.html",
        {
            "active": "new",
            "categories": CATEGORIES,
            "errors": {},
            "values": {"title": "", "amount": "", "category": "", "date": ""},
            "csrf_token": token,
        },
    )
    _apply_csrf(response, token)
    return response


@router.post("/expenses")
def create_expense(
    request: Request,
    title: str = Form(""),
    amount: str = Form(""),
    category: str = Form(""),
    date: str = Form(""),
    csrf_token: str = Form(""),
    service: ExpenseService = Depends(get_service),
) -> Response:
    token = _token(request)
    values = {"title": title, "amount": amount, "category": category, "date": date}
    cookie_token = request.cookies.get(_CSRF_COOKIE, "")
    if not _same_token(cookie_token, csrf_token):
        response = _form_response(
            request,
            values,
            {"form": "The form expired. Refresh the page and try again."},
            token,
            status_code=422,
        )
        _apply_csrf(response, token)
        return response
    try:
        service.create({"title": title, "amount": amount, "category": category, "date": date})
    except ValidationFailed as exc:
        response = _form_response(
            request,
            values,
            {error.field: error.message for error in exc.errors},
            token,
            status_code=422,
        )
        _apply_csrf(response, token)
        return response
    return RedirectResponse(url="/expenses", status_code=303)


@router.get("/expenses")
def list_expenses(
    request: Request,
    category: str | None = None,
    start: str | None = None,
    end: str | None = None,
    service: ExpenseService = Depends(get_service),
) -> Response:
    try:
        expenses = service.list_expenses(category, start, end)
    except ValidationFailed as exc:
        return templates.TemplateResponse(
            request,
            "expenses.html",
            {
                "active": "expenses",
                "categories": CATEGORIES,
                "selected": category if category in CATEGORIES else None,
                "start": start or "",
                "end": end or "",
                "expenses": [],
                "errors": [error.message for error in exc.errors],
            },
            status_code=422,
        )
    filters = validate_list_filters(category, start, end)
    return templates.TemplateResponse(
        request,
        "expenses.html",
        {
            "active": "expenses",
            "categories": CATEGORIES,
            "selected": filters.category,
            "start": filters.start or "",
            "end": filters.end or "",
            "expenses": expenses,
            "errors": [],
        },
    )


def _form_response(
    request: Request,
    values: dict[str, str],
    errors: dict[str, str],
    token: str,
    status_code: int,
) -> Response:
    return templates.TemplateResponse(
        request,
        "expense_form.html",
        {
            "active": "new",
            "categories": CATEGORIES,
            "errors": errors,
            "values": values,
            "csrf_token": token,
        },
        status_code=status_code,
    )


def _same_token(cookie_token: str, form_token: str) -> bool:
    if not cookie_token or len(cookie_token) != len(form_token):
        return False
    return secrets.compare_digest(cookie_token, form_token)