# US-05 Test Plan — Filter Expenses by Date Range

## 1. Objective and scope

Verify that an employee can filter the expense list by an inclusive start date, an inclusive end date, or both; combine the date bounds with a category; recover from invalid filters; clear the date bounds independently; and continue to see unfiltered dashboard totals. This plan covers the nine US-05 acceptance criteria in `requirements.md` and the implementation contract in section 11 of `architecture.md`.

The feature affects list filters only. Creating expenses still rejects missing, invalid, or future expense dates. Filter dates are ISO `YYYY-MM-DD`, may be in the future, and a blank or whitespace-only bound is treated as absent. Invalid requests must not return a list. No schema changes are expected.

## 2. Test approach and fixtures

- Use pytest. Keep tests deterministic by injecting a fixed local application date for expense-creation fixtures; date-range filter values themselves must not depend on today's date.
- Use a fake `ExpenseStore` for service tests and an isolated SQLite database for repository and HTTP tests. Never use the developer's persistent database.
- Seed records around the exact bounds, including both boundary dates, dates just outside them, and multiple categories. Use distinct titles/IDs to make included and excluded records unambiguous.
- Include equal start/end dates, one-sided bounds, a future filter bound, no-match ranges, and blank/omitted bounds.
- For UI tests, submit filters through the rendered GET form and inspect both response status/content and preserved form values.
- Assert date ordering remains newest occurrence date first, then descending ID for tied dates. Assert `summarize` remains independent of list filters.

## 3. Acceptance-criteria coverage

| US-05 criterion | Required behavior | Coverage |
| --- | --- | --- |
| 1 | Both valid bounds, inclusive; only matching occurrence dates appear | Unit, service, repository, API, UI |
| 2 | Start only includes that date and later | Unit, service, repository, API, UI |
| 3 | End only includes that date and earlier | Unit, service, repository, API, UI |
| 4 | Start after end returns the specified error and no list | Unit, service, API, UI |
| 5 | Missing date parts / invalid calendar date names failing bound(s), no list | Unit, service, API, UI |
| 6 | Category and range combine using AND | Unit, service, repository, API, UI |
| 7 | Valid range with no matches is an empty state, not an error | Service, repository, API, UI |
| 8 | Dashboard totals include all expenses with a date range active on list | Service, repository, API, UI |
| 9 | Clearing dates removes only date constraints and preserves category | Service, API, UI |

## 4. Unit tests

Test `validate_list_filters(category, start, end)` and any date parsing/value normalization helpers without HTTP or database dependencies.

1. Normalize `None`, `""`, and whitespace-only `start` and `end` to absent independently and together; category omission remains valid.
2. Accept valid start-only, end-only, equal-bound, and ordered two-bound filters. Accept a valid filter date after today.
3. Reject malformed/partial values (for example `2026-11-1`, `11/01/2026`), impossible dates (for example `2026-02-31`), and non-string values. Verify exact field names (`start`, `end`) and messages.
4. If both bounds are invalid, return errors for both in `start`, then `end` order. If both parse but start is later, return only the `start` order error. Do not add the order error when either bound fails parsing.
5. Reject unknown categories with the documented category message; when category and a bound are invalid, return all applicable errors ordered `category`, `start`, `end`, then order error.
6. Preserve an allowed category value unchanged. Verify normalized bounds passed onward are canonical ISO strings.

## 5. Service tests

Use a spy/fake store to verify service behavior and calls.

1. Valid category, start, and end are forwarded as normalized arguments to `list_expenses`; test start-only and end-only calls as well.
2. Invalid category, invalid start, invalid end, both invalid bounds, and reversed bounds raise `ValidationFailed`; assert the store is not called.
3. With boundary fixture records, verify start-only, end-only, equal-bound, and inclusive two-bound results. Confirm category plus range returns only rows matching both predicates.
4. A valid range with no matching rows returns an empty list without raising.
5. Call a ranged list followed by `dashboard`; verify dashboard calls `summarize` without filter parameters and reports totals across all records, including rows outside the date range.
6. Retain regression coverage for unfiltered list, empty store, add, and unknown-category behavior with the updated `list_expenses(category, start, end)` signature.

## 6. Repository tests

Use a fresh SQLite database through the repository boundary.

1. Query rows before, on, between, on the end, and after both bounds; verify both comparisons are inclusive and only in-range rows are returned.
2. Verify start-only returns dates greater than or equal to start; end-only returns dates less than or equal to end. Include a future bound and verify it is accepted and yields matching rows or an empty result.
3. Combine category and date predicates; prove a row is excluded when it fails either predicate.
4. Verify ordering remains `expense_date` descending, then `id` descending for ties under all filter combinations.
5. Verify no-match ranges return an empty list and `summarize` on the same database still includes every stored record.
6. Confirm date bounds are supplied as bound values in repository queries (no string interpolation); include a title containing quotes to verify safe round-trip and guard parameterized data access.

## 7. API tests

Use FastAPI's test client with an isolated database and deterministic seeded expenses.

1. `GET /api/expenses` with both inclusive bounds, start only, end only, equal bounds, omitted bounds, and blank bounds returns `200` with the expected `expenses` array. Verify a future filter bound is accepted.
2. A valid no-match range returns `200` and `{"expenses": []}`.
3. Category plus range returns only matching rows; category-only and date-only behavior remain unchanged.
4. Reversed bounds return `422`, an error on `start` with the documented message, and no `expenses` key.
5. Test malformed/partial and impossible start and end values separately and together. Return `422`, name every failing field, and omit `expenses`. Confirm order error is not added for unparsable bounds.
6. Blank/omitted bounds do not cause validation errors. Unknown category with invalid date returns both field errors in contract order.
7. After listing with a date range, `GET /api/dashboard` returns unchanged overall and per-category totals for all seeded expenses.

## 8. UI tests

Use the HTTP test client against server-rendered pages; verify rendered form controls, text, status, and absence/presence of list content.

1. `GET /expenses` shows Start date and End date controls named `start` and `end`, alongside category selection. Valid filters appear in the controls and an allowed category remains selected.
2. Submit valid two-bound, start-only, end-only, and equal-bound filters. The table contains only matching rows, including boundary dates, and preserves the supplied filter values.
3. Submit category plus range and verify only rows satisfying both are displayed.
4. Submit a valid no-match range: status `200`, filtered empty copy “No expenses match these filters.” appears, and no error is shown. With no active filters and no rows, verify “No expenses yet.”
5. Submit reversed dates and each invalid bound form. Verify status `422`, the correct field error(s), and submitted date text remains in the form. Verify neither the table nor either empty-state message is rendered on validation error.
6. With an active date range and category, use Clear dates; verify the category remains selected and applies. With dates active, choose All categories and submit; verify dates remain and apply.
7. Verify the clear-dates link is present only when a date bound is active and preserves the allowed category in its URL.
8. While a range is active on `/expenses`, open `/dashboard`; verify overall and category totals still include out-of-range records.

## 9. Exit criteria

- Every US-05 acceptance criterion has passing coverage in its relevant layers as mapped above.
- Invalid filters never return a partial list; valid empty results remain distinguishable from validation errors.
- Dashboard totals and category/date filter independence are demonstrated by tests.
- Existing add, view, category filter, and dashboard regressions pass with the updated list-filter interface.
