"""List-filter rules shared by the form and the JSON API."""

import pytest

from app.validation import ListFilters, ValidationFailed, validate_list_filters


def test_omitted_blank_and_whitespace_bounds_are_not_applied():
    assert validate_list_filters(None, None, None) == ListFilters(None, None, None)
    assert validate_list_filters("", "", "") == ListFilters(None, None, None)
    assert validate_list_filters(None, " \t ", "  ") == ListFilters(None, None, None)


def test_valid_bounds_include_equal_dates_and_a_future_date():
    assert validate_list_filters(None, "2026-11-01", None) == ListFilters(None, "2026-11-01", None)
    assert validate_list_filters(None, None, " 2026-11-30 ") == ListFilters(None, None, "2026-11-30")
    assert validate_list_filters("Travel", "2026-11-01", "2026-11-01") == ListFilters(
        "Travel", "2026-11-01", "2026-11-01"
    )
    assert validate_list_filters("Meals", "2027-01-01", "2027-06-30") == ListFilters(
        "Meals", "2027-01-01", "2027-06-30"
    )


@pytest.mark.parametrize(
    ("start", "end", "fields"),
    [
        ("yesterday", "2026-11-01", ["start"]),
        ("2026-11-1", None, ["start"]),
        ("2026-02-31", None, ["start"]),
        (None, "11/30/2026", ["end"]),
        (None, "2026-11-31", ["end"]),
        ("nope", "2026-13-01", ["start", "end"]),
    ],
)
def test_invalid_filter_dates_name_each_failing_field(start, end, fields):
    with pytest.raises(ValidationFailed) as caught:
        validate_list_filters(None, start, end)
    assert [error.field for error in caught.value.errors] == fields
    messages = [error.message for error in caught.value.errors]
    assert all("on or before" not in message for message in messages)


def test_start_after_end_is_a_single_start_error():
    with pytest.raises(ValidationFailed) as caught:
        validate_list_filters(None, "2026-11-30", "2026-11-01")
    assert [(error.field, error.message) for error in caught.value.errors] == [
        ("start", "Start date must be on or before the end date.")
    ]


def test_unparsed_date_does_not_also_report_the_order_error():
    with pytest.raises(ValidationFailed) as caught:
        validate_list_filters(None, "2026-02-31", "2026-01-01")
    assert [error.field for error in caught.value.errors] == ["start"]


def test_unknown_category_and_invalid_date_are_both_reported():
    with pytest.raises(ValidationFailed) as caught:
        validate_list_filters("Payroll", "2026-11-40", None)
    assert [(error.field, error.message) for error in caught.value.errors] == [
        ("category", "Category must be one of: Travel, Meals, Supplies, Utilities, Other."),
        ("start", "Start date must be a valid date (YYYY-MM-DD)."),
    ]


def test_non_string_bound_is_rejected():
    with pytest.raises(ValidationFailed) as caught:
        validate_list_filters(None, 20261101, None)
    assert caught.value.errors[0].field == "start"
