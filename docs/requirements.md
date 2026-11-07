# Requirements — Smart Expense Management Portal

**Role:** Business Analyst  
**Sources:** [prd.md](prd.md), [rules.md](../rules.md)  
**Status:** Draft for implementation  
**Scope of this document:** Project requirements, user stories, and acceptance criteria. No application code.

## 1. Purpose

Employees need a web application to record expenses and see how spending adds up. The portal lets an employee add an expense, view the full list, narrow the list by category, and read a dashboard of the total and the total per category.

## 2. Actors

| Actor | Description |
| --- | --- |
| Employee | The only user in this release. Records expenses and reviews totals. |

## 3. Assumptions

These items are not specified in the product requirements and are fixed here so design and acceptance stay consistent.

| ID | Assumption |
| --- | --- |
| A-1 | One shared expense list. There is no login, role, or per-employee ownership in this release. |
| A-2 | Categories are a fixed list: Travel, Meals, Supplies, Utilities, Other. |
| A-3 | Amount is a positive number in a single currency. No currency code is stored. |
| A-4 | Date is the date the expense occurred. It must be a real calendar date and cannot be in the future. |
| A-5 | Title is a short label, required, trimmed of leading and trailing spaces, between 1 and 100 characters. |
| A-6 | The dashboard always reflects every stored expense. The category filter applies only to the expense list. |
| A-7 | Deleting or editing an expense is out of scope. |
| A-8 | The application runs locally with SQLite and is packaged for deployment with Docker. |

## 4. In scope

1. Add an expense with title, amount, category, and date.
2. View all expenses.
3. Filter the expense list by category.
4. Dashboard showing total expenses and expenses per category.
5. Input validation, safe error handling, and secure coding aligned with OWASP practices.
6. Unit tests for every feature (Pytest).
7. Project documentation and a Docker deployment description.

## 5. Out of scope

- Authentication, authorization, and multi-user accounts
- Edit, delete, export, receipts, or approvals
- Budgets, reimbursements, and currency conversion
- Hosted databases other than local SQLite

## 6. Functional requirements

| ID | Requirement |
| --- | --- |
| FR-1 | The employee can submit a new expense with title, amount, category, and date. |
| FR-2 | The system stores a valid expense and shows it in the expense list. |
| FR-3 | The system rejects an expense that fails field rules and explains which field failed. |
| FR-4 | The employee can view every stored expense. |
| FR-5 | Each listed expense shows title, amount, category, and date. |
| FR-6 | The employee can filter the list to one category and can clear the filter to see all expenses. |
| FR-7 | An empty list, or a filter with no matches, shows a clear empty state. |
| FR-8 | The dashboard shows the sum of all expense amounts. |
| FR-9 | The dashboard shows the sum of amounts for each category that has at least one expense. |
| FR-10 | Totals use the same stored amounts as the expense list. |

## 7. Field rules

| Field | Required | Rule |
| --- | --- | --- |
| Title | Yes | Text after trim, length 1–100. |
| Amount | Yes | Number greater than 0. At most two decimal places. |
| Category | Yes | One of: Travel, Meals, Supplies, Utilities, Other. |
| Date | Yes | Valid calendar date on or before today (local application date). |

## 8. User stories and acceptance criteria

### US-01 — Add an expense

**As an** employee, **I want to** record an expense with a title, amount, category, and date, **so that** my spending is stored in one place.

**Acceptance criteria**

1. Given the add-expense form, when the employee submits a valid title, amount, category, and date, then the expense is saved and appears in the expense list.
2. Given a missing title, a blank title, or a title longer than 100 characters, when the employee submits, then the expense is not saved and the title error is shown.
3. Given an amount that is missing, not a number, zero, or negative, when the employee submits, then the expense is not saved and the amount error is shown.
4. Given an amount with more than two decimal places, when the employee submits, then the expense is not saved and the amount error is shown.
5. Given a category outside the allowed list, when the employee submits, then the expense is not saved and the category error is shown.
6. Given a missing date, an invalid date, or a date after today, when the employee submits, then the expense is not saved and the date error is shown.
7. Given a failed submission, when the error is shown, then previously entered values remain available for correction.

### US-02 — View expenses

**As an** employee, **I want to** see all of my expenses, **so that** I can review what I have recorded.

**Acceptance criteria**

1. Given one or more stored expenses, when the employee opens the expense list, then every expense is shown with title, amount, category, and date.
2. Given no stored expenses, when the employee opens the expense list, then an empty state is shown and no error is raised.
3. Given stored expenses, when the list is shown, then amounts and dates are displayed in a consistent, readable format.

### US-03 — Filter expenses by category

**As an** employee, **I want to** filter expenses by category, **so that** I can review one kind of spending.

**Acceptance criteria**

1. Given expenses in more than one category, when the employee selects a category, then only expenses in that category are shown.
2. Given a selected category with no expenses, when the filter is applied, then the empty state is shown.
3. Given an active category filter, when the employee clears it, then all expenses are shown again.
4. Given a category value that is not in the allowed list, when a filter is requested, then the system rejects the filter and does not return a partial or misleading list.

### US-04 — Read the dashboard

**As an** employee, **I want to** see total expenses and totals per category, **so that** I can understand overall spending.

**Acceptance criteria**

1. Given no expenses, when the employee opens the dashboard, then the total is 0 and no category totals are shown.
2. Given one or more expenses, when the employee opens the dashboard, then the total equals the sum of all stored amounts.
3. Given expenses in several categories, when the employee opens the dashboard, then each category with expenses shows the sum of amounts in that category.
4. Given a new valid expense is saved, when the employee opens the dashboard again, then both the overall total and the matching category total include that expense.
5. Given a category filter on the expense list, when the employee opens the dashboard, then the dashboard still shows totals for all expenses.

## 9. Non-functional requirements

| ID | Requirement | Source |
| --- | --- | --- |
| NFR-1 | Validate all inputs before they are stored or used in a query. | PRD Security; OWASP |
| NFR-2 | Return safe, specific errors for invalid input and a generic message for unexpected failures. Do not expose stack traces, file paths, or database details to the employee. | PRD Security |
| NFR-3 | Follow OWASP secure-coding practices for a small web app: parameterized data access, output encoding in the UI, and no secrets in source or images. | rules.md |
| NFR-4 | Persist data in SQLite for local use. | PRD; rules.md |
| NFR-5 | Provide unit tests for add, view, filter, and dashboard behavior, including invalid input. | rules.md |
| NFR-6 | Use FastAPI on the server and Bootstrap for the employee interface. | PRD |
| NFR-7 | Describe and later ship Docker artifacts so the app can run as a container. | PRD; rules.md |
| NFR-8 | Keep project documentation current for requirements, architecture, and decisions. | rules.md |
| NFR-9 | Do not commit secrets or change environment files without approval. Do not push directly to main. | rules.md |

## 10. Traceability

| User story | Requirements | PRD feature |
| --- | --- | --- |
| US-01 | FR-1, FR-2, FR-3 | Add Expense |
| US-02 | FR-4, FR-5, FR-7 | View Expenses |
| US-03 | FR-6, FR-7 | Filter Expenses |
| US-04 | FR-8, FR-9, FR-10 | Dashboard |
