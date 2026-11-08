"""Shared field rules for the HTML form and the JSON API."""

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.models import CATEGORIES

# Stay inside SQLite's signed integer range.
_MAX_CENTS = 2**62
_AMOUNT_PATTERN = re.compile(r"\d+(?:\.\d+)?")
_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
_FIELDS = ("title", "amount", "category", "date")


@dataclass(frozen=True)
class FieldError:
    field: str
    message: str


class ValidationFailed(Exception):
    """Raised when one or more fields fail the shared rules. Nothing is stored."""

    def __init__(self, errors: list[FieldError]) -> None:
        self.errors = errors
        super().__init__("validation failed")


@dataclass(frozen=True)
class ExpenseInput:
    title: str
    amount_cents: int
    category: str
    expense_date: str


@dataclass(frozen=True)
class ListFilters:
    category: str | None
    start: str | None
    end: str | None


_CATEGORY_FILTER_MESSAGE = "Category must be one of: Travel, Meals, Supplies, Utilities, Other."
_START_DATE_MESSAGE = "Start date must be a valid date (YYYY-MM-DD)."
_END_DATE_MESSAGE = "End date must be a valid date (YYYY-MM-DD)."
_DATE_ORDER_MESSAGE = "Start date must be on or before the end date."


def format_cents(cents: int) -> str:
    """Render integer cents as a two-decimal string."""
    sign = "-" if cents < 0 else ""
    whole, remainder = divmod(abs(cents), 100)
    return f"{sign}{whole}.{remainder:02d}"


def validate_new_expense(payload: object, today: date) -> ExpenseInput:
    """Validate a create payload and return the normalized values."""
    if not isinstance(payload, dict):
        raise ValidationFailed(
            [FieldError("body", "Request body must be a JSON object.")]
        )

    errors: list[FieldError] = []
    for key in payload:
        if key not in _FIELDS:
            errors.append(FieldError(key, "Unknown field."))

    title = _validate_title(payload.get("title"), "title" in payload, errors)
    amount_cents = _validate_amount(payload.get("amount"), "amount" in payload, errors)
    category = _validate_category(payload.get("category"), "category" in payload, errors)
    expense_date = _validate_date(payload.get("date"), "date" in payload, today, errors)

    if errors:
        raise ValidationFailed(errors)
    assert title is not None and amount_cents is not None
    assert category is not None and expense_date is not None
    return ExpenseInput(title, amount_cents, category, expense_date)


def validate_category_filter(category: str | None) -> str | None:
    """Accept a missing filter. Reject a category outside the allowed list."""
    errors: list[FieldError] = []
    selected = _optional_category(category, errors)
    if errors:
        raise ValidationFailed(errors)
    return selected


def validate_list_filters(category: object, start: object, end: object) -> ListFilters:
    """Accept a missing category or date bound. Reject invalid list filters together."""
    errors: list[FieldError] = []
    selected = _optional_category(category, errors)
    parsed_start = _optional_filter_date(start, "start", _START_DATE_MESSAGE, errors)
    parsed_end = _optional_filter_date(end, "end", _END_DATE_MESSAGE, errors)
    if parsed_start is not None and parsed_end is not None and parsed_start > parsed_end:
        errors.append(FieldError("start", _DATE_ORDER_MESSAGE))
    if errors:
        raise ValidationFailed(errors)
    return ListFilters(selected, parsed_start, parsed_end)


def _optional_category(value: object, errors: list[FieldError]) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or value not in CATEGORIES:
        errors.append(FieldError("category", _CATEGORY_FILTER_MESSAGE))
        return None
    return value


def _optional_filter_date(value: object, field: str, message: str, errors: list[FieldError]) -> str | None:
    """Parse an optional list bound. Blank means the bound is not applied."""
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(FieldError(field, message))
        return None
    text = value.strip()
    if not text:
        return None
    if not _DATE_PATTERN.fullmatch(text):
        errors.append(FieldError(field, message))
        return None
    try:
        datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        errors.append(FieldError(field, message))
        return None
    return text


def _validate_title(value: object, present: bool, errors: list[FieldError]) -> str | None:
    if not present or value is None:
        errors.append(FieldError("title", "Title is required."))
        return None
    if not isinstance(value, str):
        errors.append(FieldError("title", "Title must be text."))
        return None
    title = value.strip()
    if not title:
        errors.append(FieldError("title", "Title is required."))
        return None
    if len(title) > 100:
        errors.append(FieldError("title", "Title must be 100 characters or fewer."))
        return None
    return title


def _validate_amount(value: object, present: bool, errors: list[FieldError]) -> int | None:
    if not present or value is None:
        errors.append(FieldError("amount", "Amount is required."))
        return None
    if not isinstance(value, str):
        errors.append(FieldError("amount", "Amount must be a decimal string."))
        return None
    text = value.strip()
    if not text:
        errors.append(FieldError("amount", "Amount is required."))
        return None
    if text.startswith("-"):
        errors.append(FieldError("amount", "Amount must be greater than 0."))
        return None
    if not _AMOUNT_PATTERN.fullmatch(text):
        errors.append(FieldError("amount", "Amount must be a number."))
        return None
    fraction = text.split(".", 1)[1] if "." in text else ""
    if len(fraction) > 2:
        errors.append(FieldError("amount", "Amount must have at most two decimal places."))
        return None
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        errors.append(FieldError("amount", "Amount must be a number."))
        return None
    if parsed <= 0:
        errors.append(FieldError("amount", "Amount must be greater than 0."))
        return None
    cents = int(parsed * 100)
    if cents > _MAX_CENTS:
        errors.append(FieldError("amount", "Amount is too large."))
        return None
    return cents


def _validate_category(value: object, present: bool, errors: list[FieldError]) -> str | None:
    if not present or value is None or value == "":
        errors.append(FieldError("category", "Category is required."))
        return None
    if not isinstance(value, str) or value not in CATEGORIES:
        errors.append(
            FieldError(
                "category",
                "Category must be one of: Travel, Meals, Supplies, Utilities, Other.",
            )
        )
        return None
    return value


def _validate_date(value: object, present: bool, today: date, errors: list[FieldError]) -> str | None:
    if not present or value is None:
        errors.append(FieldError("date", "Date is required."))
        return None
    if not isinstance(value, str):
        errors.append(FieldError("date", "Date must be a valid date (YYYY-MM-DD)."))
        return None
    text = value.strip()
    if not text:
        errors.append(FieldError("date", "Date is required."))
        return None
    if not _DATE_PATTERN.fullmatch(text):
        errors.append(FieldError("date", "Date must be a valid date (YYYY-MM-DD)."))
        return None
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        errors.append(FieldError("date", "Date must be a valid date (YYYY-MM-DD)."))
        return None
    if parsed > today:
        errors.append(FieldError("date", "Date cannot be in the future."))
        return None
    return text
